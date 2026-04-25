from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tier import Tier
from app.schemas.tier import TierCreateRequest, TierUpdateRequest


class TierNotFoundError(Exception):
    pass


class TierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tier(self, *, partner_id: int, request: TierCreateRequest) -> Tier:
        tier = Tier(
            partner_id=partner_id,
            name=request.name,
            min_points=request.min_points,
            earn_multiplier=request.earn_multiplier,
            perks=request.perks,
            is_active=True,
        )
        self.db.add(tier)
        await self.db.flush()
        await self.db.refresh(tier)
        return tier

    async def get_tier(self, *, partner_id: int, tier_id: int) -> Tier:
        tier = await self.db.scalar(
            select(Tier).where(
                Tier.id == tier_id,
                Tier.partner_id == partner_id,
                Tier.deleted_at.is_(None),
            )
        )
        if tier is None:
            raise TierNotFoundError(
                f"Tier {tier_id} not found in partner {partner_id}"
            )
        return tier

    async def list_tiers(self, *, partner_id: int) -> list[Tier]:
        rows = await self.db.scalars(
            select(Tier)
            .where(Tier.partner_id == partner_id, Tier.deleted_at.is_(None))
            .order_by(Tier.min_points.asc())
        )
        return list(rows.all())

    async def update_tier(
        self, *, partner_id: int, tier_id: int, request: TierUpdateRequest
    ) -> Tier:
        tier = await self.get_tier(partner_id=partner_id, tier_id=tier_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(tier, field, value)
        await self.db.flush()
        return tier

    async def delete_tier(self, *, partner_id: int, tier_id: int) -> None:
        """Soft delete: set deleted_at."""
        tier = await self.get_tier(partner_id=partner_id, tier_id=tier_id)
        tier.deleted_at = datetime.now(timezone.utc)
        tier.is_active = False
        await self.db.flush()

    async def recompute_tier(
        self, *, partner_id: int, membership_id: int
    ) -> Tier | None:
        """Luồng G — tính lại tier theo lifetime_earned per-shop."""
        from app.models.membership import Membership

        membership = await self.db.get(Membership, membership_id)
        if membership is None or membership.partner_id != partner_id:
            raise ValueError(
                f"Membership {membership_id} not found in partner {partner_id}"
            )

        new_tier = await self.db.scalar(
            select(Tier)
            .where(
                Tier.partner_id == partner_id,
                Tier.is_active.is_(True),
                Tier.deleted_at.is_(None),
                Tier.min_points <= membership.lifetime_earned,
            )
            .order_by(Tier.min_points.desc())
            .limit(1)
        )

        if new_tier is None:
            membership.current_tier_id = None
            await self.db.flush()
            return None

        if membership.current_tier_id != new_tier.id:
            membership.current_tier_id = new_tier.id
            await self.db.flush()

        return new_tier
