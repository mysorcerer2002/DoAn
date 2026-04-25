import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

logger = logging.getLogger(__name__)

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.point_rule import PointRule
from app.models.partner import Partner
from app.models.tier import Tier
from app.models.transaction import Transaction, TransactionMethod
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


# LOCK ORDERING RULE (xem 6.1 trong spec):
# Mọi transaction cần lock nhiều bảng phải lock theo thứ tự cố định:
# 1. memberships (luôn đầu tiên, dùng SELECT FOR UPDATE)
# 2. tiers / point_rules (chỉ đọc, không cần lock)


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

        net_amount = request.gross_amount

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
            net_amount=net_amount,
            points_earned=points_earned,
            method=TransactionMethod.MANUAL,
            note=request.note,
            receipt_code=request.receipt_code,
        )
        self.db.add(txn)
        await self.db.flush()

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

        tier_upgraded = False
        if new_tier is not None and new_tier.id != old_tier_id:
            tier_upgraded = (
                old_tier_id is None
                or new_tier.min_points > old_tier_min_points
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
        if rule.use_tiers and membership is not None:
            tier = getattr(membership, "current_tier", None)
            if tier is not None:
                multiplier = tier.earn_multiplier

        return int(base_points * multiplier)

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
    ) -> TransactionWithMemberResponse:
        """Logic tạo transaction dùng chung cho manual và QR."""
        ledger_svc = LedgerService(self.db)
        tier_svc = TierService(self.db)

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

        net_amount = gross_amount
        points_earned = self._calculate_points(
            rule, net_amount, membership=membership
        )

        txn = Transaction(
            partner_id=partner_id,
            membership_id=membership.id,
            staff_id=staff_id,
            gross_amount=gross_amount,
            net_amount=net_amount,
            points_earned=points_earned,
            method=method,
            note=note,
        )
        self.db.add(txn)
        await self.db.flush()

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
            tier_upgraded = (
                old_tier_id is None
                or new_tier.min_points > old_tier_min_points
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
            pass

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
