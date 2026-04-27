"""RewardService — CRUD + soft delete cho rewards."""

from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward, RewardOfferType
from app.schemas.reward import (
    RewardCreateRequest,
    RewardStatsResponse,
    RewardUpdateRequest,
)


class RewardNotFoundError(Exception):
    pass


class RewardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reward(
        self, *, partner_id: int, request: RewardCreateRequest
    ) -> Reward:
        reward = Reward(
            partner_id=partner_id,
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            points_cost=request.points_cost,
            stock=request.stock,
            is_active=True,
        )
        self.db.add(reward)
        await self.db.flush()
        return reward

    async def get_reward(self, *, partner_id: int, reward_id: int) -> Reward:
        reward = await self.db.scalar(
            select(Reward).where(
                Reward.id == reward_id,
                Reward.partner_id == partner_id,
                Reward.deleted_at.is_(None),
            )
        )
        if reward is None:
            raise RewardNotFoundError(f"Reward {reward_id} not found")
        return reward

    async def list_rewards(
        self,
        *,
        partner_id: int,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Reward]:
        stmt = (
            select(Reward)
            .where(Reward.partner_id == partner_id, Reward.deleted_at.is_(None))
            .order_by(Reward.points_cost.asc())
            .limit(limit)
            .offset(offset)
        )
        if active_only:
            stmt = stmt.where(Reward.is_active.is_(True))
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def update_reward(
        self, *, partner_id: int, reward_id: int, request: RewardUpdateRequest
    ) -> Reward:
        reward = await self.get_reward(partner_id=partner_id, reward_id=reward_id)
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(reward, field, value)
        await self.db.flush()
        return reward

    async def soft_delete_reward(self, *, partner_id: int, reward_id: int) -> Reward:
        reward = await self.get_reward(partner_id=partner_id, reward_id=reward_id)
        reward.deleted_at = datetime.now(timezone.utc)
        reward.is_active = False
        await self.db.flush()
        return reward

    async def get_stats(
        self, *, partner_id: int, reward_id: int
    ) -> RewardStatsResponse:
        reward = await self.get_reward(partner_id=partner_id, reward_id=reward_id)

        # offer_type cột String(20) → ORM trả str, coerce về Enum để so sánh chuẩn.
        offer_type = RewardOfferType(reward.offer_type)
        is_discount = offer_type in (
            RewardOfferType.PERCENT_DISCOUNT,
            RewardOfferType.FIXED_DISCOUNT,
        )

        row = (
            await self.db.execute(
                select(
                    func.count(Redemption.id).label("issued"),
                    func.coalesce(
                        func.sum(
                            case(
                                (Redemption.status == RedemptionStatus.PENDING, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("redeemed"),
                    func.coalesce(
                        func.sum(
                            case(
                                (Redemption.status == RedemptionStatus.USED, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("used"),
                    func.coalesce(
                        func.sum(
                            case(
                                (Redemption.status == RedemptionStatus.EXPIRED, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("expired"),
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    Redemption.status == RedemptionStatus.USED,
                                    func.coalesce(Redemption.discount_amount, 0),
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("discount_cost"),
                ).where(
                    Redemption.reward_id == reward_id,
                    Redemption.partner_id == partner_id,
                )
            )
        ).one()

        return RewardStatsResponse(
            reward_id=reward_id,
            offer_type=offer_type.value,
            issued=int(row.issued or 0),
            redeemed=int(row.redeemed or 0),
            used=int(row.used or 0),
            expired=int(row.expired or 0),
            total_discount_cost=int(row.discount_cost or 0) if is_discount else None,
        )
