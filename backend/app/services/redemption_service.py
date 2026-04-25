"""RedemptionService — atomic đổi quà + ledger (HYBRID: scope user_id global)."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward
from app.models.user import User
from app.services.ledger_service import LedgerService


class InsufficientPointsError(Exception):
    pass


class OutOfStockError(Exception):
    pass


class RedemptionNotFoundError(Exception):
    pass


_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))


class RedemptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def redeem(
        self,
        *,
        partner_id: int,
        user_id: int,
        reward_id: int,
        ttl_days: int = 14,
    ) -> Redemption:
        """Đổi quà — atomic: lock reward → atomic-decrement user.points_balance → ledger.

        HYBRID: ví điểm global trên users.points_balance. Dùng atomic UPDATE
        với WHERE points_balance >= cost để tránh lost-update mà không cần
        SELECT FOR UPDATE trên users (giảm contention khi user đổi quà cùng
        lúc earn ở shop khác).
        """
        # 1. Get reward — FOR UPDATE để khoá points_cost/is_active/deleted_at
        # khỏi admin edit concurrent.
        reward = await self.db.scalar(
            select(Reward)
            .where(
                Reward.id == reward_id,
                Reward.partner_id == partner_id,
                Reward.is_active.is_(True),
                Reward.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if reward is None:
            raise ValueError(f"Reward {reward_id} not found")

        # 2. Atomic decrement stock (nếu có)
        if reward.stock is not None:
            result = await self.db.execute(
                update(Reward)
                .where(Reward.id == reward_id, Reward.stock > 0)
                .values(stock=Reward.stock - 1)
            )
            if result.rowcount == 0:
                raise OutOfStockError(f"Reward {reward_id} out of stock")

        # 3. Atomic decrement user wallet (race-safe vs concurrent earn cross-shop)
        try:
            result = await self.db.execute(
                update(User)
                .where(User.id == user_id, User.points_balance >= reward.points_cost)
                .values(points_balance=User.points_balance - reward.points_cost)
                .returning(User.points_balance)
            )
            new_balance = result.scalar_one_or_none()
        except IntegrityError as e:
            raise InsufficientPointsError("Balance constraint violated") from e

        if new_balance is None:
            # Stock đã trừ rồi → cần rollback. Chỉ revert nếu reward có stock.
            if reward.stock is not None:
                await self.db.execute(
                    update(Reward)
                    .where(Reward.id == reward_id)
                    .values(stock=Reward.stock + 1)
                )
            raise InsufficientPointsError(
                f"User {user_id} insufficient points (need {reward.points_cost})"
            )

        # 4. Generate unique redemption code (per partner)
        code: str | None = None
        for _attempt in range(3):
            candidate = _generate_code()
            existing = await self.db.scalar(
                select(Redemption.id).where(
                    Redemption.partner_id == partner_id,
                    Redemption.redemption_code == candidate,
                )
            )
            if existing is None:
                code = candidate
                break
        if code is None:
            raise RuntimeError(
                "Failed to generate unique redemption code after 3 attempts"
            )

        redemption = Redemption(
            partner_id=partner_id,
            user_id=user_id,
            reward_id=reward_id,
            points_spent=reward.points_cost,
            redemption_code=code,
            status=RedemptionStatus.PENDING,
            redeemed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days),
        )
        self.db.add(redemption)
        await self.db.flush()

        # 5. Insert ledger
        ledger_svc = LedgerService(self.db)
        await ledger_svc.log_entry(
            partner_id=partner_id,
            user_id=user_id,
            delta=-reward.points_cost,
            reason=LedgerReason.REDEEM,
            ref_type=LedgerRefType.REDEMPTION,
            ref_id=redemption.id,
            new_balance=new_balance,
            description=f"Đổi quà: {reward.name}",
        )
        await self.db.flush()

        return redemption

    async def use_redemption(
        self, *, partner_id: int, code: str, staff_id: int
    ) -> Redemption:
        """Nhân viên xác nhận sử dụng mã đổi quà."""
        redemption = await self.db.scalar(
            select(Redemption).where(
                Redemption.partner_id == partner_id,
                Redemption.redemption_code == code,
                Redemption.status == RedemptionStatus.PENDING,
            ).with_for_update()
        )
        if redemption is None:
            raise RedemptionNotFoundError(f"Code {code} not found or already used")

        if redemption.expires_at < datetime.now(timezone.utc):
            redemption.status = RedemptionStatus.EXPIRED
            await self.db.flush()
            raise RedemptionNotFoundError(f"Code {code} expired")

        redemption.status = RedemptionStatus.USED
        redemption.used_at = datetime.now(timezone.utc)
        redemption.used_by_staff_id = staff_id
        await self.db.flush()
        return redemption

    async def list_my_redemptions(
        self, *, user_id: int, partner_id: int | None = None
    ) -> list[Redemption]:
        """Lịch sử đổi quà của user. partner_id=None → cross-shop."""
        stmt = select(Redemption).where(Redemption.user_id == user_id)
        if partner_id is not None:
            stmt = stmt.where(Redemption.partner_id == partner_id)
        rows = await self.db.scalars(stmt.order_by(Redemption.redeemed_at.desc()))
        return list(rows.all())

    async def list_tenant_redemptions(
        self, *, partner_id: int, limit: int = 50, offset: int = 0
    ) -> list[Redemption]:
        rows = await self.db.scalars(
            select(Redemption)
            .where(Redemption.partner_id == partner_id)
            .order_by(Redemption.redeemed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())
