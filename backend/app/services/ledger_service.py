from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.user import User
from app.schemas.ledger import ReconcileResponse


class LedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_entry(
        self,
        *,
        partner_id: int,
        user_id: int,
        delta: int,
        reason: LedgerReason,
        ref_type: LedgerRefType,
        ref_id: int | None,
        new_balance: int,
        description: str | None = None,
    ) -> PointLedger:
        entry = PointLedger(
            partner_id=partner_id,
            user_id=user_id,
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
        self,
        *,
        user_id: int,
        partner_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PointLedger]:
        """Lịch sử điểm. partner_id=None → global cross-shop; có partner_id → lọc theo shop."""
        stmt = select(PointLedger).where(PointLedger.user_id == user_id)
        if partner_id is not None:
            stmt = stmt.where(PointLedger.partner_id == partner_id)
        stmt = (
            stmt.order_by(PointLedger.created_at.desc(), PointLedger.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def reconcile(self, *, user_id: int) -> ReconcileResponse:
        """So khớp tổng ledger global vs users.points_balance."""
        expected_sum = await self.db.scalar(
            select(func.coalesce(func.sum(PointLedger.delta), 0)).where(
                PointLedger.user_id == user_id,
            )
        )
        user = await self.db.get(User, user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")

        actual = user.points_balance
        return ReconcileResponse(
            user_id=user_id,
            expected_balance=int(expected_sum),
            actual_balance=actual,
            is_consistent=int(expected_sum) == actual,
            diff=int(expected_sum) - actual,
        )
