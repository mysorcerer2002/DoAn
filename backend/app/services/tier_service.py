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

    async def create_tier(self, *, tenant_id: int, request: TierCreateRequest) -> Tier:
        tier = Tier(
            tenant_id=tenant_id,
            name=request.name,
            min_points=request.min_points,
            perks=request.perks,
            is_active=True,
        )
        self.db.add(tier)
        await self.db.flush()
        await self.db.refresh(tier)
        return tier

    async def get_tier(self, *, tenant_id: int, tier_id: int) -> Tier:
        tier = await self.db.scalar(
            select(Tier).where(
                Tier.id == tier_id,
                Tier.tenant_id == tenant_id,
                Tier.deleted_at.is_(None),
            )
        )
        if tier is None:
            raise TierNotFoundError(
                f"Tier {tier_id} not found in tenant {tenant_id}"
            )
        return tier

    async def list_tiers(self, *, tenant_id: int) -> list[Tier]:
        rows = await self.db.scalars(
            select(Tier)
            .where(Tier.tenant_id == tenant_id, Tier.deleted_at.is_(None))
            .order_by(Tier.min_points.asc())
        )
        return list(rows.all())

    async def update_tier(
        self, *, tenant_id: int, tier_id: int, request: TierUpdateRequest
    ) -> Tier:
        tier = await self.get_tier(tenant_id=tenant_id, tier_id=tier_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(tier, field, value)
        await self.db.flush()
        return tier

    async def delete_tier(self, *, tenant_id: int, tier_id: int) -> None:
        """Soft delete: set deleted_at."""
        tier = await self.get_tier(tenant_id=tenant_id, tier_id=tier_id)
        tier.deleted_at = datetime.now(timezone.utc)
        tier.is_active = False
        await self.db.flush()
