from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.schemas.ledger import ReconcileResponse


class LedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_entry(
        self,
        *,
        partner_id: int,
        membership_id: int,
        delta: int,
        reason: LedgerReason,
        ref_type: LedgerRefType,
        ref_id: int | None,
        new_balance: int,
        description: str | None = None,
    ) -> PointLedger:
        entry = PointLedger(
            partner_id=partner_id,
            membership_id=membership_id,
            delta=delta,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
            balance_after=new_balance,
            description=description,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_history(
        self, *, partner_id: int, membership_id: int, limit: int = 50, offset: int = 0
    ) -> list[PointLedger]:
        rows = await self.db.scalars(
            select(PointLedger)
            .where(
                PointLedger.partner_id == partner_id,
                PointLedger.membership_id == membership_id,
            )
            .order_by(PointLedger.created_at.desc(), PointLedger.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())

    async def reconcile(
        self, *, partner_id: int, membership_id: int
    ) -> ReconcileResponse:
        expected_sum = await self.db.scalar(
            select(func.coalesce(func.sum(PointLedger.delta), 0)).where(
                PointLedger.partner_id == partner_id,
                PointLedger.membership_id == membership_id,
            )
        )
        membership = await self.db.get(Membership, membership_id)
        if membership is None or membership.partner_id != partner_id:
            raise ValueError(f"Membership {membership_id} not found in tenant {partner_id}")

        actual = membership.points_balance
        return ReconcileResponse(
            membership_id=membership_id,
            expected_balance=int(expected_sum),
            actual_balance=actual,
            is_consistent=int(expected_sum) == actual,
            diff=int(expected_sum) - actual,
        )
