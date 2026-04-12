"""RedemptionService — atomic đổi quà + ledger (Luồng D)."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward
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
        tenant_id: int,
        membership_id: int,
        reward_id: int,
        ttl_days: int = 14,
    ) -> Redemption:
        """Đổi quà — atomic: lock membership → check balance → decrement stock → ledger."""
        # 1. SELECT FOR UPDATE membership
        membership = await self.db.scalar(
            select(Membership)
            .where(
                Membership.id == membership_id,
                Membership.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        if membership is None:
            raise ValueError(f"Membership {membership_id} not in tenant {tenant_id}")

        # 2. Get reward
        reward = await self.db.scalar(
            select(Reward).where(
                Reward.id == reward_id,
                Reward.tenant_id == tenant_id,
                Reward.is_active.is_(True),
                Reward.deleted_at.is_(None),
            )
        )
        if reward is None:
            raise ValueError(f"Reward {reward_id} not found")

        # 3. Check balance
        if membership.points_balance < reward.points_cost:
            raise InsufficientPointsError(
                f"Need {reward.points_cost}, have {membership.points_balance}"
            )

        # 4. Atomic decrement stock (nếu có)
        if reward.stock is not None:
            result = await self.db.execute(
                update(Reward)
                .where(Reward.id == reward_id, Reward.stock > 0)
                .values(stock=Reward.stock - 1)
            )
            if result.rowcount == 0:
                raise OutOfStockError(f"Reward {reward_id} out of stock")

        # 5. Decrement membership balance
        new_balance = membership.points_balance - reward.points_cost
        membership.points_balance = new_balance

        # 6. Generate unique redemption code
        code: str | None = None
        for _attempt in range(3):
            candidate = _generate_code()
            existing = await self.db.scalar(
                select(Redemption.id).where(
                    Redemption.tenant_id == tenant_id,
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
            tenant_id=tenant_id,
            membership_id=membership_id,
            reward_id=reward_id,
            points_spent=reward.points_cost,
            redemption_code=code,
            status=RedemptionStatus.PENDING,
            redeemed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days),
        )
        self.db.add(redemption)
        try:
            await self.db.flush()
        except IntegrityError as e:
            err_msg = str(e).lower()
            if "ck_memberships_balance_nonneg" in err_msg:
                raise InsufficientPointsError("Balance constraint violated") from e
            if "ck_rewards_stock_nonneg" in err_msg:
                raise OutOfStockError("Stock constraint violated") from e
            raise

        # 7. Insert ledger
        ledger_svc = LedgerService(self.db)
        await ledger_svc.log_entry(
            tenant_id=tenant_id,
            membership_id=membership_id,
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
        self, *, tenant_id: int, code: str, staff_id: int
    ) -> Redemption:
        """Nhân viên xác nhận sử dụng mã đổi quà."""
        redemption = await self.db.scalar(
            select(Redemption).where(
                Redemption.tenant_id == tenant_id,
                Redemption.redemption_code == code,
                Redemption.status == RedemptionStatus.PENDING,
            )
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
        self, *, tenant_id: int, membership_id: int
    ) -> list[Redemption]:
        rows = await self.db.scalars(
            select(Redemption)
            .where(
                Redemption.tenant_id == tenant_id,
                Redemption.membership_id == membership_id,
            )
            .order_by(Redemption.redeemed_at.desc())
        )
        return list(rows.all())

    async def list_tenant_redemptions(
        self, *, tenant_id: int, limit: int = 50, offset: int = 0
    ) -> list[Redemption]:
        rows = await self.db.scalars(
            select(Redemption)
            .where(Redemption.tenant_id == tenant_id)
            .order_by(Redemption.redeemed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())
