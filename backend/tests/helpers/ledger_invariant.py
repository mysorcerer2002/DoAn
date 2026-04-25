from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point_ledger import PointLedger
from app.models.user import User


async def assert_ledger_invariant(db: AsyncSession, user_id: int) -> None:
    """Bất biến HYBRID: SUM(delta) toàn cục per user == users.points_balance."""
    expected = await db.scalar(
        select(func.coalesce(func.sum(PointLedger.delta), 0)).where(
            PointLedger.user_id == user_id
        )
    )
    user = await db.get(User, user_id)
    assert user is not None, f"User {user_id} không tồn tại"
    assert int(expected) == user.points_balance, (
        f"Ledger invariant FAILED: SUM(delta)={expected} != "
        f"user.points_balance={user.points_balance}"
    )
