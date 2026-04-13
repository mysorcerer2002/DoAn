"""VoucherService — atomic claim chống TOCTOU + helper methods."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.campaign import Campaign
from app.models.tenant import Tenant
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


def generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))


class VoucherService:
    DEFAULT_TTL_DAYS = 30

    def __init__(self, db: AsyncSession):
        self.db = db

    async def claim(
        self, *, tenant_id: int, membership_id: int, campaign_id: int
    ) -> Voucher:
        """Atomic claim voucher (chống TOCTOU).

        1. UPDATE campaigns SET issued_count += 1 WHERE ... AND (max NULL OR < max)
           → rowcount=0 → CampaignFullError hoặc CampaignNotEligibleError
        2. INSERT voucher → IntegrityError (partial unique) → AlreadyClaimedError
        """
        now = datetime.now(timezone.utc)

        # Step 1: Atomic UPDATE check + increment
        result = await self.db.execute(
            update(Campaign)
            .where(
                Campaign.id == campaign_id,
                Campaign.tenant_id == tenant_id,
                Campaign.is_active.is_(True),
                Campaign.deleted_at.is_(None),
                Campaign.starts_at <= now,
                Campaign.ends_at > now,
                or_(
                    Campaign.max_issuances.is_(None),
                    Campaign.issued_count < Campaign.max_issuances,
                ),
            )
            .values(issued_count=Campaign.issued_count + 1)
        )

        if result.rowcount == 0:
            campaign = await self.db.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id, Campaign.tenant_id == tenant_id
                )
            )
            if campaign is None:
                raise CampaignNotEligibleError("Campaign not found")
            if (
                campaign.max_issuances is not None
                and campaign.issued_count >= campaign.max_issuances
            ):
                raise CampaignFullError("Campaign reached max issuances")
            raise CampaignNotEligibleError("Campaign not active or out of window")

        # Step 2: INSERT voucher với savepoint retry on code collision
        ttl = await self.get_voucher_ttl(tenant_id)
        last_error: IntegrityError | None = None
        for _attempt in range(3):
            code = generate_code()
            try:
                async with self.db.begin_nested():
                    voucher = Voucher(
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        membership_id=membership_id,
                        code=code,
                        status=VoucherStatus.ISSUED,
                        issued_at=now,
                        expires_at=now + timedelta(days=ttl),
                    )
                    self.db.add(voucher)
                    await self.db.flush()
                return voucher
            except IntegrityError as e:
                last_error = e
                error_msg = str(e).lower()
                if (
                    "uq_vouchers_active_per_member_per_campaign" in error_msg
                    or "ix_vouchers_active_per_member_per_campaign" in error_msg
                ):
                    # Đã có voucher active → undo issued_count
                    await self.db.execute(
                        update(Campaign)
                        .where(Campaign.id == campaign_id)
                        .values(issued_count=Campaign.issued_count - 1)
                    )
                    await self.db.flush()
                    raise AlreadyClaimedError(
                        f"Membership {membership_id} đã có voucher từ campaign {campaign_id}"
                    ) from e
                # Code collision → retry
                continue

        # Hết retry → undo và raise
        await self.db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(issued_count=Campaign.issued_count - 1)
        )
        await self.db.flush()
        raise RuntimeError(
            f"Failed to generate unique voucher code after 3 retries: {last_error}"
        )

    async def get_voucher_ttl(self, tenant_id: int) -> int:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            return self.DEFAULT_TTL_DAYS
        return tenant.settings.get("voucher_default_ttl_days", self.DEFAULT_TTL_DAYS)

    async def list_eligible_campaigns(
        self,
        *,
        tenant_id: int,
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
            .where(
                Campaign.tenant_id == tenant_id,
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
                not_(Campaign.id.in_(already_claimed)),
            )
            .order_by(Campaign.ends_at.asc())
        )
        return list(rows.all())

    async def list_my_vouchers(
        self,
        *,
        tenant_id: int,
        membership_id: int,
        status: VoucherStatus | None = None,
    ) -> list[Voucher]:
        stmt = (
            select(Voucher)
            .where(
                Voucher.tenant_id == tenant_id,
                Voucher.membership_id == membership_id,
            )
            .order_by(Voucher.issued_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Voucher.status == status)
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def find_by_code(self, *, tenant_id: int, code: str) -> Voucher | None:
        return await self.db.scalar(
            select(Voucher).where(
                Voucher.tenant_id == tenant_id,
                Voucher.code == code,
            )
        )

    async def check_voucher_for_use(
        self,
        *,
        tenant_id: int,
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
                Voucher.tenant_id == tenant_id,
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

        # Tính discount preview (giống logic transaction_service apply voucher)
        discount = 0
        meets_min_order = gross_amount >= campaign.min_order
        if meets_min_order:
            discount_type_str = (
                campaign.discount_type.value
                if hasattr(campaign.discount_type, "value")
                else str(campaign.discount_type)
            )
            if discount_type_str == "percent":
                discount = gross_amount * campaign.discount_value // 100
            else:
                discount = campaign.discount_value
            if campaign.max_discount is not None:
                discount = min(discount, campaign.max_discount)
            discount = min(discount, gross_amount)

        return {
            "valid": True,
            "code": voucher.code,
            "campaign_name": campaign.name,
            "discount_type": (
                campaign.discount_type.value
                if hasattr(campaign.discount_type, "value")
                else str(campaign.discount_type)
            ),
            "discount_value": campaign.discount_value,
            "min_order": campaign.min_order,
            "max_discount": campaign.max_discount,
            "expires_at": voucher.expires_at,
            "preview_discount": discount,
            "preview_net": max(0, gross_amount - discount),
            "meets_min_order": meets_min_order,
        }

    async def mark_used(self, *, tenant_id: int, voucher_id: int) -> Voucher:
        voucher = await self.db.scalar(
            select(Voucher).where(
                Voucher.id == voucher_id,
                Voucher.tenant_id == tenant_id,
            )
        )
        if voucher is None:
            raise ValueError(f"Voucher {voucher_id} not found in tenant {tenant_id}")
        voucher.status = VoucherStatus.USED
        voucher.used_at = datetime.now(timezone.utc)
        await self.db.flush()
        return voucher
