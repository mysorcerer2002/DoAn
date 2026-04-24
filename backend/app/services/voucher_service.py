"""VoucherService — atomic claim chống TOCTOU + helper methods.

Phase 9 plan voucher rebuild v2.2:
- Filter `approval_status IN ('auto_approved','approved')` + `authorization.revoked_at IS NULL`.
- `pg_advisory_xact_lock('claim:' || campaign_id)` serialize claims trong campaign (section 3.2).
- Lazy-create `campaign_issuances` row bằng ON CONFLICT — mỗi voucher có `issuance_id` + `issue_source`.
- `discount_snapshot` = {discount_type, discount_value, max_discount, min_order, terms_hash} (section 3.3).
  `terms_hash = SHA-256(campaign.terms)` cô lập voucher khỏi edit campaign sau này (I1).
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.campaign import Campaign
from app.models.campaign_issuance import CampaignIssuance
from app.models.partner import Partner
from app.models.partner_authorization import PartnerAuthorization
from app.models.voucher import Voucher, VoucherStatus


class AlreadyClaimedError(Exception):
    pass


class CampaignFullError(Exception):
    pass


class CampaignNotEligibleError(Exception):
    pass


class VoucherNotFoundError(Exception):
    pass


class VoucherInvalidStatusError(Exception):
    """Voucher đã used hoặc expired."""


class VoucherExpiredError(Exception):
    pass


_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

_ELIGIBLE_APPROVAL_STATUSES = ("auto_approved", "approved")
_VALID_ISSUE_SOURCES = {
    "manual",
    "bulk_distribution",
    "signup_job",
    "birthday_job",
}


def generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))


class VoucherService:
    DEFAULT_TTL_DAYS = 30

    def __init__(self, db: AsyncSession):
        self.db = db

    async def claim(
        self,
        *,
        partner_id: int,
        membership_id: int,
        campaign_id: int,
        issue_source: str = "manual",
    ) -> Voucher:
        """Atomic claim voucher — Phase 9 v2.2.

        Guard chain (chặn cả TOCTOU):
        1. `pg_advisory_xact_lock('claim:' || campaign_id)` — serialize claim
           concurrent trong cùng campaign (plan section 3.2).
        2. Fetch campaign + validate: approval_status ∈ (auto_approved, approved),
           is_active, deleted_at IS NULL, window (starts_at ≤ now < ends_at),
           authorization.revoked_at IS NULL.
        3. Atomic UPDATE `issued_count` với quota guard (max_issuances) —
           belt-and-suspenders cùng advisory lock.
        4. Lazy-create `campaign_issuances` row (ON CONFLICT DO UPDATE RETURNING).
        5. Compute `discount_snapshot` với `terms_hash = SHA-256(terms)`.
        6. INSERT voucher (retry 3 lần nếu code collision).

        Raises:
            CampaignNotEligibleError: approval/authorization/window không hợp lệ.
            CampaignFullError: đã đạt max_issuances.
            AlreadyClaimedError: member đã có voucher active của campaign.
        """
        if issue_source not in _VALID_ISSUE_SOURCES:
            raise ValueError(
                f"issue_source không hợp lệ: {issue_source!r} "
                f"(hợp lệ: {sorted(_VALID_ISSUE_SOURCES)})"
            )

        now = datetime.now(timezone.utc)

        # Step 0: Advisory lock — auto-release end of transaction.
        await self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": f"claim:{campaign_id}"},
        )

        # Step 1: Fetch + validate eligibility.
        campaign = await self.db.scalar(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.partner_id == partner_id,
            )
        )
        if campaign is None:
            raise CampaignNotEligibleError("Campaign không tồn tại")
        if campaign.deleted_at is not None:
            raise CampaignNotEligibleError("Campaign đã bị xoá")
        if not campaign.is_active:
            raise CampaignNotEligibleError("Campaign tạm dừng")
        if campaign.approval_status not in _ELIGIBLE_APPROVAL_STATUSES:
            raise CampaignNotEligibleError(
                f"Campaign chưa duyệt (status={campaign.approval_status})"
            )
        starts_at = campaign.starts_at
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        ends_at = campaign.ends_at
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        if starts_at > now:
            raise CampaignNotEligibleError("Campaign chưa bắt đầu")
        if ends_at <= now:
            raise CampaignNotEligibleError("Campaign đã kết thúc")

        # Authorization revoked check (chỉ khi campaign link auth).
        if campaign.authorization_id is not None:
            auth = await self.db.get(PartnerAuthorization, campaign.authorization_id)
            if auth is None or auth.revoked_at is not None:
                raise CampaignNotEligibleError("Uỷ quyền shop đã thu hồi")

        # Step 2: Atomic UPDATE issued_count (quota guard).
        result = await self.db.execute(
            update(Campaign)
            .where(
                Campaign.id == campaign_id,
                Campaign.partner_id == partner_id,
                Campaign.approval_status.in_(_ELIGIBLE_APPROVAL_STATUSES),
                Campaign.is_active.is_(True),
                Campaign.deleted_at.is_(None),
                or_(
                    Campaign.max_issuances.is_(None),
                    Campaign.issued_count < Campaign.max_issuances,
                ),
            )
            .values(issued_count=Campaign.issued_count + 1)
        )
        if result.rowcount == 0:
            raise CampaignFullError("Campaign đã đạt giới hạn phát hành")

        # Step 3: Lazy-create issuance + RETURNING id.
        issuance_id = await self._get_or_create_lazy_issuance(
            partner_id=partner_id,
            campaign_id=campaign_id,
            issue_mode=issue_source,
        )

        # Step 4: discount_snapshot với terms_hash (SHA-256).
        terms_hash = hashlib.sha256(
            (campaign.terms or "").encode("utf-8")
        ).hexdigest()
        discount_type_val = (
            campaign.discount_type.value
            if hasattr(campaign.discount_type, "value")
            else str(campaign.discount_type)
        )
        discount_snapshot = {
            "discount_type": discount_type_val,
            "discount_value": campaign.discount_value,
            "max_discount": campaign.max_discount,
            "min_order": campaign.min_order,
            "terms_hash": terms_hash,
        }

        # Step 5: INSERT voucher (retry 3 lần nếu code collision).
        ttl = await self.get_voucher_ttl(partner_id)
        last_error: IntegrityError | None = None
        for _attempt in range(3):
            code = generate_code()
            try:
                async with self.db.begin_nested():
                    voucher = Voucher(
                        partner_id=partner_id,
                        campaign_id=campaign_id,
                        membership_id=membership_id,
                        code=code,
                        status=VoucherStatus.ISSUED,
                        issued_at=now,
                        expires_at=now + timedelta(days=ttl),
                        issuance_id=issuance_id,
                        issue_source=issue_source,
                        discount_snapshot=discount_snapshot,
                    )
                    self.db.add(voucher)
                    await self.db.flush()
                # Step 6: bump issuance counter sau khi voucher INSERT OK.
                await self.db.execute(
                    update(CampaignIssuance)
                    .where(CampaignIssuance.id == issuance_id)
                    .values(issued_count=CampaignIssuance.issued_count + 1)
                )
                await self.db.flush()
                return voucher
            except IntegrityError as e:
                last_error = e
                error_msg = str(e).lower()
                if (
                    "uq_vouchers_active_per_member_per_campaign" in error_msg
                    or "ix_vouchers_active_per_member_per_campaign" in error_msg
                ):
                    # Đã có voucher active → undo campaign.issued_count.
                    # (Issuance.issued_count chưa bump → không cần undo.)
                    await self.db.execute(
                        update(Campaign)
                        .where(Campaign.id == campaign_id)
                        .values(issued_count=Campaign.issued_count - 1)
                    )
                    await self.db.flush()
                    raise AlreadyClaimedError(
                        f"Membership {membership_id} đã có voucher từ campaign {campaign_id}"
                    ) from e
                continue

        # Hết retry → undo + raise.
        await self.db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(issued_count=Campaign.issued_count - 1)
        )
        await self.db.flush()
        raise RuntimeError(
            f"Failed to generate unique voucher code after 3 retries: {last_error}"
        )

    async def _get_or_create_lazy_issuance(
        self, *, partner_id: int, campaign_id: int, issue_mode: str
    ) -> int:
        """Lazy-create issuance row cho auto-batch (name IS NULL).

        Partial unique `uq_campaign_issuances_lazy_auto` trên
        `(campaign_id, issue_mode) WHERE name IS NULL AND deleted_at IS NULL`
        → batch shop tự đặt tên (name NOT NULL) không đụng.

        Dùng `ON CONFLICT DO UPDATE SET issued_count = issued_count`
        (no-op) để RETURNING id cho row có sẵn.
        """
        row = await self.db.execute(
            text(
                """
                INSERT INTO campaign_issuances
                    (partner_id, campaign_id, name, issued_count, issue_mode,
                     created_at, updated_at)
                VALUES
                    (:partner_id, :campaign_id, NULL, 0, :issue_mode,
                     NOW(), NOW())
                ON CONFLICT (campaign_id, issue_mode)
                    WHERE name IS NULL AND deleted_at IS NULL
                DO UPDATE SET issued_count = campaign_issuances.issued_count
                RETURNING id
                """
            ),
            {
                "partner_id": partner_id,
                "campaign_id": campaign_id,
                "issue_mode": issue_mode,
            },
        )
        issuance_id = row.scalar_one()
        return issuance_id

    async def get_voucher_ttl(self, partner_id: int) -> int:
        partner = await self.db.get(Partner, partner_id)
        if partner is None:
            return self.DEFAULT_TTL_DAYS
        return partner.settings.get("voucher_default_ttl_days", self.DEFAULT_TTL_DAYS)

    async def list_eligible_campaigns(
        self,
        *,
        partner_id: int,
        membership_id: int,
        current_tier_id: int | None = None,
    ) -> list[Campaign]:
        """List campaigns đủ điều kiện cho khách claim."""
        from sqlalchemy import not_

        now = datetime.now(timezone.utc)

        already_claimed = select(Voucher.campaign_id).where(
            Voucher.membership_id == membership_id,
            Voucher.status == VoucherStatus.ISSUED,
        )

        rows = await self.db.scalars(
            select(Campaign)
            .outerjoin(
                PartnerAuthorization,
                Campaign.authorization_id == PartnerAuthorization.id,
            )
            .where(
                Campaign.partner_id == partner_id,
                Campaign.approval_status.in_(_ELIGIBLE_APPROVAL_STATUSES),
                Campaign.is_active.is_(True),
                Campaign.deleted_at.is_(None),
                Campaign.starts_at <= now,
                Campaign.ends_at > now,
                or_(
                    Campaign.max_issuances.is_(None),
                    Campaign.issued_count < Campaign.max_issuances,
                ),
                or_(
                    Campaign.target_tier_id.is_(None),
                    Campaign.target_tier_id == current_tier_id,
                ),
                or_(
                    Campaign.authorization_id.is_(None),
                    PartnerAuthorization.revoked_at.is_(None),
                ),
                not_(Campaign.id.in_(already_claimed)),
            )
            .order_by(Campaign.ends_at.asc())
        )
        return list(rows.all())

    async def list_my_vouchers(
        self,
        *,
        partner_id: int,
        membership_id: int,
        status: VoucherStatus | None = None,
    ) -> list[Voucher]:
        stmt = (
            select(Voucher)
            .where(
                Voucher.partner_id == partner_id,
                Voucher.membership_id == membership_id,
            )
            .order_by(Voucher.issued_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Voucher.status == status)
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def find_by_code(self, *, partner_id: int, code: str) -> Voucher | None:
        return await self.db.scalar(
            select(Voucher).where(
                Voucher.partner_id == partner_id,
                Voucher.code == code,
            )
        )

    async def check_voucher_for_use(
        self,
        *,
        partner_id: int,
        code: str,
        gross_amount: int = 0,
    ) -> dict:
        """Kiểm tra voucher code + tính discount preview cho POS form.

        Raises:
            VoucherNotFoundError: code không tồn tại trong tenant
            VoucherInvalidStatusError: voucher đã used/expired
            VoucherExpiredError: voucher quá hạn

        Returns: dict với valid, code, campaign_name, discount_*, preview_*, meets_min_order
        """
        voucher = await self.db.scalar(
            select(Voucher)
            .options(joinedload(Voucher.campaign))
            .where(
                Voucher.partner_id == partner_id,
                Voucher.code == code.upper(),
            )
        )
        if voucher is None:
            raise VoucherNotFoundError(f"Voucher '{code}' không tồn tại")

        if voucher.status != VoucherStatus.ISSUED:
            status_label = (
                voucher.status.value
                if hasattr(voucher.status, "value")
                else str(voucher.status)
            )
            raise VoucherInvalidStatusError(f"Voucher đã {status_label}")

        now = datetime.now(timezone.utc)
        expires_at = voucher.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise VoucherExpiredError("Voucher đã hết hạn")

        campaign = voucher.campaign
        if campaign is None:
            raise VoucherInvalidStatusError("Voucher không có campaign")

        # Phase 9 I1 — đọc từ discount_snapshot trước, fallback sang live
        # campaign cho voucher cũ (pre-migration).
        snap = voucher.discount_snapshot or {}
        discount_type_str = snap.get("discount_type") or (
            campaign.discount_type.value
            if hasattr(campaign.discount_type, "value")
            else str(campaign.discount_type)
        )
        discount_value = snap.get("discount_value", campaign.discount_value)
        max_discount = snap.get("max_discount", campaign.max_discount)
        min_order = snap.get("min_order", campaign.min_order)

        # Tính discount preview (giống logic transaction_service apply voucher)
        discount = 0
        meets_min_order = gross_amount >= (min_order or 0)
        if meets_min_order:
            if discount_type_str == "percent":
                discount = gross_amount * discount_value // 100
            else:
                discount = discount_value
            if max_discount is not None:
                discount = min(discount, max_discount)
            discount = min(discount, gross_amount)

        return {
            "valid": True,
            "code": voucher.code,
            "campaign_name": campaign.name,
            "campaign_description": campaign.description,
            "campaign_terms": campaign.terms,
            "campaign_usage_guide": campaign.usage_guide,
            "campaign_support_contact": campaign.support_contact,
            "discount_type": discount_type_str,
            "discount_value": discount_value,
            "min_order": min_order,
            "max_discount": max_discount,
            "expires_at": voucher.expires_at,
            "preview_discount": discount,
            "preview_net": max(0, gross_amount - discount),
            "meets_min_order": meets_min_order,
        }

    async def mark_used(self, *, partner_id: int, voucher_id: int) -> Voucher:
        voucher = await self.db.scalar(
            select(Voucher).where(
                Voucher.id == voucher_id,
                Voucher.partner_id == partner_id,
            )
        )
        if voucher is None:
            raise ValueError(f"Voucher {voucher_id} not found in tenant {partner_id}")
        voucher.status = VoucherStatus.USED
        voucher.used_at = datetime.now(timezone.utc)
        await self.db.flush()
        return voucher
