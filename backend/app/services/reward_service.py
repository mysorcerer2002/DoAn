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


class RewardValidationError(Exception):
    """Domain validation fail post-merge cho update — API map 422."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _validate_reward_state(
    offer_type: str | RewardOfferType,
    offer_value: int | None,
    min_purchase_amount: int | None,
) -> None:
    """Kiểm hypothetical state hợp lệ — gọi TRƯỚC setattr để tránh dirty session."""
    ot = RewardOfferType(offer_type) if isinstance(offer_type, str) else offer_type
    if ot == RewardOfferType.PERCENT_DISCOUNT:
        if offer_value is None or not (1 <= offer_value <= 100):
            raise RewardValidationError("Phần trăm giảm phải từ 1 đến 100")
    elif ot == RewardOfferType.FIXED_DISCOUNT:
        if offer_value is None or offer_value <= 0:
            raise RewardValidationError("Số tiền giảm phải lớn hơn 0")
    elif ot == RewardOfferType.ITEM_GIFT:
        if offer_value is not None:
            raise RewardValidationError(
                "Quà tặng hiện vật không được có giá trị giảm"
            )
        if min_purchase_amount is not None:
            raise RewardValidationError(
                "Quà tặng hiện vật không được đặt hoá đơn tối thiểu"
            )
    if min_purchase_amount is not None and min_purchase_amount <= 0:
        raise RewardValidationError("Hoá đơn tối thiểu phải lớn hơn 0")


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
            is_active=request.is_active,
            offer_type=request.offer_type.value,
            offer_value=request.offer_value,
            offer_label=request.offer_label,
            min_purchase_amount=request.min_purchase_amount,
            valid_until=request.valid_until,
            terms=request.terms,
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
        # offer_type immutable — schema đã reject, defensive pop phòng trường hợp lọt qua.
        update_data.pop("offer_type", None)

        # Build hypothetical state (merge update_data với reward hiện tại) → validate TRƯỚC setattr.
        new_offer_value = update_data.get("offer_value", reward.offer_value)
        new_min_purchase = update_data.get(
            "min_purchase_amount", reward.min_purchase_amount
        )
        _validate_reward_state(
            offer_type=reward.offer_type,
            offer_value=new_offer_value,
            min_purchase_amount=new_min_purchase,
        )

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
