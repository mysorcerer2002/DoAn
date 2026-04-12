from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.point_ledger import PointLedger


async def assert_ledger_invariant(db: AsyncSession, membership_id: int) -> None:
    """Kiểm tra bất biến: SUM(delta) == points_balance."""
    expected = await db.scalar(
        select(func.coalesce(func.sum(PointLedger.delta), 0)).where(
            PointLedger.membership_id == membership_id
        )
    )
    membership = await db.get(Membership, membership_id)
    assert membership is not None, f"Membership {membership_id} không tồn tại"
    assert int(expected) == membership.points_balance, (
        f"Ledger invariant FAILED: SUM(delta)={expected} != balance={membership.points_balance}"
    )
