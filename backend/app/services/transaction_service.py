import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

logger = logging.getLogger(__name__)

# NĐ 81 Điều 7: mức giảm giá tối đa 50% (trừ đợt tập trung). Service
# layer warn log không CHECK cứng DB — đợt tập trung có thể vượt hợp lệ.
_LEGAL_DISCOUNT_WARN_THRESHOLD = Decimal("50")

from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.point_rule import PointRule
from app.models.partner import Partner
from app.models.tier import Tier
from app.models.transaction import Transaction, TransactionMethod
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    CreateQrCustomerTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
)
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService
from app.services.tier_service import TierService


class NoActivePointRuleError(Exception):
    pass


class NoMembershipError(Exception):
    pass


class InvalidVoucherError(Exception):
    pass


# LOCK ORDERING RULE (xem 6.1 trong spec):
# Mọi transaction cần lock nhiều bảng phải lock theo thứ tự cố định:
# 1. memberships (luôn đầu tiên, dùng SELECT FOR UPDATE)
# 2. tiers / point_rules (chỉ đọc, không cần lock)
# 3. vouchers (nếu có, từ tuần 5)
# 4. rewards (nếu có, từ tuần 4)


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_campaign_realized_cost_from_view(self, campaign_id: int) -> int:
        """Phase 10 — đọc realized_cost realtime từ `v_campaign_stats`.

        View COALESCE → 0 khi không có voucher nào dùng, trả BIGINT.
        Admin/partner API nên dùng helper này thay vì column cache
        `campaigns.realized_cost` (ngày cache sẽ drop ở phase sau).
        """
        row = await self.db.execute(
            text(
                "SELECT realized_cost FROM v_campaign_stats "
                "WHERE campaign_id = :cid"
            ),
            {"cid": campaign_id},
        )
        value = row.scalar()
        return int(value) if value is not None else 0

    async def _warn_if_high_discount_ratio(self, txn: Transaction) -> None:
        """NĐ 81 Điều 7 — giảm >50% chỉ hợp lệ trong đợt tập trung.

        Không raise — chỉ log WARNING để ops monitor. Column
        `legal_discount_ratio` do DB GENERATED STORED tính; sau flush,
        SQLAlchemy refresh giá trị.
        """
        ratio = txn.legal_discount_ratio
        if ratio is None:
            return
        if ratio > _LEGAL_DISCOUNT_WARN_THRESHOLD:
            logger.warning(
                "Transaction #%s legal_discount_ratio=%s%% vượt ngưỡng NĐ 81 Đ7 "
                "(gross=%s, voucher_discount=%s, campaign qua voucher #%s)",
                txn.id, ratio, txn.gross_amount,
                txn.voucher_discount_amount, txn.voucher_id,
            )

    async def create_manual(
        self,
        *,
        partner_id: int,
        staff_id: int,
        request: CreateManualTransactionRequest,
    ) -> TransactionWithMemberResponse:
        """Tạo giao dịch tích điểm method=manual."""
        member_svc = MemberService(self.db)
        ledger_svc = LedgerService(self.db)
        tier_svc = TierService(self.db)

        member = await member_svc.find_or_create_member(
            partner_id=partner_id, phone=request.phone
        )

        # SELECT FOR UPDATE membership (scope theo partner_id để defense-in-depth)
        # innerjoin=True vì user_id NOT NULL → tránh OUTER JOIN + FOR UPDATE conflict
        membership = await self.db.scalar(
            select(Membership)
            .options(
                joinedload(Membership.user, innerjoin=True),
                selectinload(Membership.current_tier),
            )
            .where(
                Membership.id == member.membership_id,
                Membership.partner_id == partner_id,
            )
            .with_for_update()
        )
        if membership is None:
            raise ValueError(f"Membership {member.membership_id} not found")

        # Giao dịch đầu tiên của khách tại shop này → phát voucher chào mừng
        is_first_transaction = membership.last_activity_at is None

        # Apply voucher nếu có
        voucher_id = None
        voucher_discount = None
        if request.voucher_code:
            voucher_id, voucher_discount = await self._apply_voucher_if_provided(
                partner_id=partner_id,
                membership_id=membership.id,
                voucher_code=request.voucher_code,
                gross_amount=request.gross_amount,
            )

        # Snapshot old_tier TRƯỚC khi recompute
        old_tier_id = membership.current_tier_id
        old_tier_min_points = 0
        if old_tier_id is not None:
            old_tier = await self.db.get(Tier, old_tier_id)
            old_tier_min_points = old_tier.min_points if old_tier else 0

        rule = await self.db.scalar(
            select(PointRule).where(
                PointRule.partner_id == partner_id, PointRule.is_active.is_(True)
            )
        )
        if rule is None:
            raise NoActivePointRuleError(
                f"Partner {partner_id} has no active point rule"
            )

        # Phase 10 I1 — clamp discount ≤ gross trước khi persist để
        # `legal_discount_ratio` (NUMERIC(5,2)) không overflow. NĐ 81 Đ7
        # về bản chất không cho ratio > 100% — data corruption nếu vượt.
        if voucher_discount is not None:
            voucher_discount = min(voucher_discount, request.gross_amount)
        # Clamp net_amount >= 0 (defense: voucher discount > gross_amount edge case)
        net_amount = max(0, request.gross_amount - (voucher_discount or 0))

        # Đọc settings của đối tác để biết tính điểm trên gross hay net
        partner = await self.db.get(Partner, partner_id)
        points_on_gross = bool(
            partner and partner.settings and partner.settings.get("points_on_gross")
        )
        amount_for_points = request.gross_amount if points_on_gross else net_amount
        points_earned = self._calculate_points(
            rule, amount_for_points, membership=membership
        )

        txn = Transaction(
            partner_id=partner_id,
            membership_id=membership.id,
            staff_id=staff_id,
            gross_amount=request.gross_amount,
            voucher_id=voucher_id,
            voucher_discount_amount=voucher_discount,
            net_amount=net_amount,
            points_earned=points_earned,
            method=TransactionMethod.MANUAL,
            note=request.note,
        )
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn, ["legal_discount_ratio"])
        await self._warn_if_high_discount_ratio(txn)

        new_balance = membership.points_balance + points_earned
        membership.points_balance = new_balance
        membership.total_points_earned += points_earned
        membership.last_activity_at = datetime.now(timezone.utc)

        if points_earned > 0:
            await ledger_svc.log_entry(
                partner_id=partner_id,
                membership_id=membership.id,
                delta=points_earned,
                reason=LedgerReason.EARN,
                ref_type=LedgerRefType.TRANSACTION,
                ref_id=txn.id,
                new_balance=new_balance,
                description=f"Manual transaction #{txn.id}",
            )

        new_tier = await tier_svc.recompute_tier(
            partner_id=partner_id, membership_id=membership.id
        )
        await self.db.flush()

        # tier_upgraded: True khi chuyển sang tier cao hơn (kể cả lần đầu có tier)
        tier_upgraded = False
        if new_tier is not None and new_tier.id != old_tier_id:
            # Lần đầu có tier (old_tier_id=None) cũng coi là thăng hạng
            tier_upgraded = (
                old_tier_id is None
                or new_tier.min_points > old_tier_min_points
            )

        welcome_voucher_code: str | None = None
        if is_first_transaction and points_earned > 0:
            welcome_voucher_code = await self._maybe_issue_welcome_voucher(
                partner_id=partner_id, membership_id=membership.id
            )

        return TransactionWithMemberResponse(
            transaction=TransactionResponse.model_validate(txn),
            member_phone=member.user_phone,
            member_full_name=member.user_full_name,
            new_balance=membership.points_balance,
            new_total_earned=membership.total_points_earned,
            new_tier_id=membership.current_tier_id,
            new_tier_name=new_tier.name if new_tier else None,
            tier_upgraded=tier_upgraded,
            welcome_voucher_code=welcome_voucher_code,
        )

    @staticmethod
    def _calculate_points(
        rule: PointRule,
        amount: int,
        *,
        membership: "Membership | None" = None,
    ) -> int:
        if amount < rule.min_amount:
            return 0
        units = Decimal(amount) / Decimal(rule.unit_amount)
        base_points = units * rule.points_per_unit

        multiplier = Decimal("1.00")
        if rule.use_tiers and membership is not None and membership.current_tier is not None:
            multiplier = membership.current_tier.earn_multiplier

        return int(base_points * multiplier)

    async def _apply_voucher_if_provided(
        self,
        *,
        partner_id: int,
        membership_id: int,
        voucher_code: str,
        gross_amount: int,
    ) -> tuple[int, int]:
        """Validate + atomic mark_used voucher. Trả về (voucher_id, discount_amount).

        FIX C1+C3: Lock chỉ hàng Voucher (of=Voucher), KHÔNG joinedload (load
        campaign sau qua db.get để tránh OUTER JOIN + FOR UPDATE conflict).
        Mark used bằng atomic UPDATE WHERE status=ISSUED + rowcount check
        thay vì Python-side assignment.
        """
        from sqlalchemy import update as sa_update

        voucher = await self.db.scalar(
            select(Voucher)
            .where(
                Voucher.partner_id == partner_id,
                Voucher.code == voucher_code,
            )
            .with_for_update(of=Voucher)
        )
        if voucher is None:
            raise InvalidVoucherError("Voucher not found")
        if voucher.membership_id != membership_id:
            raise InvalidVoucherError("Voucher does not belong to this member")
        if voucher.status != VoucherStatus.ISSUED:
            raise InvalidVoucherError(
                f"Voucher status is {voucher.status}, expected issued"
            )
        if voucher.expires_at and voucher.expires_at < datetime.now(timezone.utc):
            raise InvalidVoucherError("Voucher expired")

        campaign = await self.db.get(Campaign, voucher.campaign_id)
        if campaign is None:
            raise InvalidVoucherError("Campaign not found for voucher")

        # Phase 9 I1 — đọc từ discount_snapshot trước (cô lập voucher
        # khỏi edit campaign sau khi đã issue). Fallback sang live campaign
        # cho voucher cũ chưa có snapshot (pre-migration c7d8e9f0a1b2).
        snap = voucher.discount_snapshot or {}
        discount_type_str = snap.get("discount_type") or (
            campaign.discount_type.value
            if hasattr(campaign.discount_type, "value")
            else str(campaign.discount_type)
        )
        discount_value = snap.get("discount_value", campaign.discount_value)
        max_discount = snap.get("max_discount", campaign.max_discount)
        min_order = snap.get("min_order", campaign.min_order)

        if discount_type_str == "percent":
            discount = int(gross_amount * discount_value / 100)
            if max_discount:
                discount = min(discount, max_discount)
        else:
            discount = discount_value

        discount = min(discount, gross_amount)

        if min_order and gross_amount < min_order:
            raise InvalidVoucherError(
                f"Order amount {gross_amount} below minimum {min_order}"
            )

        # Atomic mark used: UPDATE WHERE status=ISSUED, fail nếu race
        result = await self.db.execute(
            sa_update(Voucher)
            .where(Voucher.id == voucher.id, Voucher.status == VoucherStatus.ISSUED)
            .values(status=VoucherStatus.USED, used_at=datetime.now(timezone.utc))
        )
        if result.rowcount == 0:
            raise InvalidVoucherError(
                "Voucher đã được sử dụng (race condition)"
            )

        return voucher.id, discount

    async def list_transactions(
        self, *, partner_id: int, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        rows = await self.db.scalars(
            select(Transaction)
            .where(Transaction.partner_id == partner_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())

    async def create_qr_customer(
        self,
        *,
        partner_id: int,
        staff_id: int,
        request: CreateQrCustomerTransactionRequest,
    ) -> TransactionWithMemberResponse:
        """Tạo giao dịch từ QR scan — staff quét QR khách."""
        from app.core.qr import InvalidQRError
        from app.services.qr_service import QrService

        qr_svc = QrService(self.db)
        try:
            user_id = await qr_svc.decode_qr_payload(
                payload=request.qr_payload, partner_id=partner_id
            )
        except InvalidQRError as e:
            raise ValueError(f"Invalid QR: {e}") from e

        # Tìm membership — nếu chưa có thì auto-enroll (1 lần đăng ký dùng mọi shop)
        membership = await self.db.scalar(
            select(Membership)
            .options(
                joinedload(Membership.user, innerjoin=True),
                selectinload(Membership.current_tier),
            )
            .where(
                Membership.partner_id == partner_id,
                Membership.user_id == user_id,
            )
            .with_for_update()
        )
        if membership is None:
            membership = await self._auto_enroll_membership(
                partner_id=partner_id, user_id=user_id
            )

        return await self._create_transaction_for_membership(
            partner_id=partner_id,
            staff_id=staff_id,
            membership=membership,
            gross_amount=request.gross_amount,
            note=request.note,
            method=TransactionMethod.QR_CUSTOMER,
        )

    async def _create_transaction_for_membership(
        self,
        *,
        partner_id: int,
        staff_id: int,
        membership: Membership,
        gross_amount: int,
        note: str | None,
        method: TransactionMethod,
        voucher_id: int | None = None,
        voucher_discount: int | None = None,
    ) -> TransactionWithMemberResponse:
        """Logic tạo transaction dùng chung cho manual và QR."""
        ledger_svc = LedgerService(self.db)
        tier_svc = TierService(self.db)

        is_first_transaction = membership.last_activity_at is None

        old_tier_id = membership.current_tier_id
        old_tier_min_points = 0
        if old_tier_id is not None:
            old_tier = await self.db.get(Tier, old_tier_id)
            old_tier_min_points = old_tier.min_points if old_tier else 0

        rule = await self.db.scalar(
            select(PointRule).where(
                PointRule.partner_id == partner_id, PointRule.is_active.is_(True)
            )
        )
        if rule is None:
            raise NoActivePointRuleError(
                f"Partner {partner_id} has no active point rule"
            )

        # Phase 10 I1 — clamp discount ≤ gross (xem create_manual comment).
        if voucher_discount is not None:
            voucher_discount = min(voucher_discount, gross_amount)
        net_amount = max(0, gross_amount - (voucher_discount or 0))
        points_earned = self._calculate_points(
            rule, net_amount, membership=membership
        )

        txn = Transaction(
            partner_id=partner_id,
            membership_id=membership.id,
            staff_id=staff_id,
            gross_amount=gross_amount,
            voucher_id=voucher_id,
            voucher_discount_amount=voucher_discount,
            net_amount=net_amount,
            points_earned=points_earned,
            method=method,
            note=note,
        )
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn, ["legal_discount_ratio"])
        await self._warn_if_high_discount_ratio(txn)

        new_balance = membership.points_balance + points_earned
        membership.points_balance = new_balance
        membership.total_points_earned += points_earned
        membership.last_activity_at = datetime.now(timezone.utc)

        if points_earned > 0:
            await ledger_svc.log_entry(
                partner_id=partner_id,
                membership_id=membership.id,
                delta=points_earned,
                reason=LedgerReason.EARN,
                ref_type=LedgerRefType.TRANSACTION,
                ref_id=txn.id,
                new_balance=new_balance,
                description=f"{method.value} transaction #{txn.id}",
            )

        new_tier = await tier_svc.recompute_tier(
            partner_id=partner_id, membership_id=membership.id
        )
        await self.db.flush()

        tier_upgraded = False
        if new_tier is not None and new_tier.id != old_tier_id:
            # Lần đầu có tier (old_tier_id=None) cũng coi là thăng hạng
            tier_upgraded = (
                old_tier_id is None
                or new_tier.min_points > old_tier_min_points
            )

        welcome_voucher_code: str | None = None
        if is_first_transaction and points_earned > 0:
            welcome_voucher_code = await self._maybe_issue_welcome_voucher(
                partner_id=partner_id, membership_id=membership.id
            )

        user = membership.user
        return TransactionWithMemberResponse(
            transaction=TransactionResponse.model_validate(txn),
            member_phone=user.phone if user else None,
            member_full_name=user.full_name if user else None,
            new_balance=membership.points_balance,
            new_total_earned=membership.total_points_earned,
            new_tier_id=membership.current_tier_id,
            new_tier_name=new_tier.name if new_tier else None,
            tier_upgraded=tier_upgraded,
            welcome_voucher_code=welcome_voucher_code,
        )

    async def _auto_enroll_membership(
        self, *, partner_id: int, user_id: int
    ) -> Membership:
        """Tạo membership mới cho user tại đối tác (auto-enroll lần đầu quét QR)."""
        from sqlalchemy.exc import IntegrityError as _SAIntegrityError

        try:
            async with self.db.begin_nested():
                membership = Membership(
                    partner_id=partner_id,
                    user_id=user_id,
                    current_tier_id=None,
                    points_balance=0,
                    total_points_earned=0,
                    joined_at=datetime.now(timezone.utc),
                )
                self.db.add(membership)
                await self.db.flush()
        except _SAIntegrityError:
            # Race: cùng lúc có request khác tạo cho (đối tác, user) này
            pass

        # Reload để có lock + eager load user + current_tier (dùng cho response và multiplier)
        membership = await self.db.scalar(
            select(Membership)
            .options(
                joinedload(Membership.user, innerjoin=True),
                selectinload(Membership.current_tier),
            )
            .where(
                Membership.partner_id == partner_id,
                Membership.user_id == user_id,
            )
            .with_for_update()
        )
        if membership is None:
            raise NoMembershipError(
                f"Không thể tạo membership cho user {user_id} tại đối tác {partner_id}"
            )
        return membership

    async def _maybe_issue_welcome_voucher(
        self, *, partner_id: int, membership_id: int
    ) -> str | None:
        """Phát voucher tích điểm lần đầu nếu shop có campaign source=SIGNUP đang mở.

        Không raise: mọi lỗi (không có campaign, campaign full, race duplicate)
        đều swallow để không làm fail giao dịch chính.
        """
        from app.services.voucher_service import (
            AlreadyClaimedError,
            CampaignFullError,
            CampaignNotEligibleError,
            VoucherService,
        )

        from sqlalchemy import or_

        from app.models.partner_authorization import PartnerAuthorization

        now = datetime.now(timezone.utc)
        campaign = await self.db.scalar(
            select(Campaign)
            .outerjoin(
                PartnerAuthorization,
                Campaign.authorization_id == PartnerAuthorization.id,
            )
            .where(
                Campaign.partner_id == partner_id,
                Campaign.source == CampaignSource.SIGNUP,
                Campaign.approval_status.in_(("auto_approved", "approved")),
                Campaign.is_active.is_(True),
                Campaign.deleted_at.is_(None),
                Campaign.starts_at <= now,
                Campaign.ends_at > now,
                or_(
                    Campaign.authorization_id.is_(None),
                    PartnerAuthorization.revoked_at.is_(None),
                ),
            )
            .order_by(Campaign.id.asc())
            .limit(1)
        )
        if campaign is None:
            return None

        voucher_svc = VoucherService(self.db)
        try:
            voucher = await voucher_svc.claim(
                partner_id=partner_id,
                membership_id=membership_id,
                campaign_id=campaign.id,
                issue_source="signup_job",
            )
        except (AlreadyClaimedError, CampaignFullError, CampaignNotEligibleError):
            return None
        return voucher.code
