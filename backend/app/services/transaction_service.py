from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.point_rule import PointRule
from app.models.tier import Tier
from app.models.transaction import Transaction, TransactionMethod
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
)
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService
from app.services.tier_service import TierService


class NoActivePointRuleError(Exception):
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

    async def create_manual(
        self,
        *,
        tenant_id: int,
        staff_id: int,
        request: CreateManualTransactionRequest,
    ) -> TransactionWithMemberResponse:
        """Tạo giao dịch tích điểm method=manual."""
        member_svc = MemberService(self.db)
        ledger_svc = LedgerService(self.db)
        tier_svc = TierService(self.db)

        member = await member_svc.find_or_create_member(
            tenant_id=tenant_id, phone=request.phone
        )

        # SELECT FOR UPDATE membership
        # innerjoin=True vì user_id NOT NULL → tránh OUTER JOIN + FOR UPDATE conflict
        membership = await self.db.scalar(
            select(Membership)
            .options(joinedload(Membership.user, innerjoin=True))
            .where(Membership.id == member.membership_id)
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
                PointRule.tenant_id == tenant_id, PointRule.is_active.is_(True)
            )
        )
        if rule is None:
            raise NoActivePointRuleError(
                f"Tenant {tenant_id} has no active point rule"
            )

        net_amount = request.gross_amount
        points_earned = self._calculate_points(rule, net_amount)

        txn = Transaction(
            tenant_id=tenant_id,
            membership_id=membership.id,
            staff_id=staff_id,
            gross_amount=request.gross_amount,
            voucher_id=None,
            voucher_discount_amount=None,
            net_amount=net_amount,
            points_earned=points_earned,
            method=TransactionMethod.MANUAL,
            note=request.note,
        )
        self.db.add(txn)
        await self.db.flush()

        new_balance = membership.points_balance + points_earned
        membership.points_balance = new_balance
        membership.total_points_earned += points_earned
        membership.last_activity_at = datetime.now(timezone.utc)

        if points_earned > 0:
            await ledger_svc.log_entry(
                tenant_id=tenant_id,
                membership_id=membership.id,
                delta=points_earned,
                reason=LedgerReason.EARN,
                ref_type=LedgerRefType.TRANSACTION,
                ref_id=txn.id,
                new_balance=new_balance,
                description=f"Manual transaction #{txn.id}",
            )

        new_tier = await tier_svc.recompute_tier(
            tenant_id=tenant_id, membership_id=membership.id
        )
        await self.db.flush()

        tier_upgraded = False
        if new_tier is not None and old_tier_id is not None and new_tier.id != old_tier_id:
            tier_upgraded = new_tier.min_points > old_tier_min_points

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
    def _calculate_points(rule: PointRule, net_amount: int) -> int:
        if net_amount < rule.min_amount:
            return 0
        units = Decimal(net_amount) / Decimal(rule.unit_amount)
        return int(units * rule.points_per_unit)

    async def list_transactions(
        self, *, tenant_id: int, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        rows = await self.db.scalars(
            select(Transaction)
            .where(Transaction.tenant_id == tenant_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())
