from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Partner
from app.schemas.settings import SettingsUpdateRequest, PartnerSettings


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, *, partner_id: int) -> PartnerSettings:
        partner = await self.db.get(Partner, partner_id)
        if partner is None:
            raise ValueError(f"Partner {partner_id} not found")
        return PartnerSettings(**partner.settings)

    async def update_settings(
        self,
        *,
        partner_id: int,
        request: SettingsUpdateRequest,
    ) -> PartnerSettings:
        partner = await self.db.scalar(
            select(Partner).where(Partner.id == partner_id).with_for_update()
        )
        if partner is None:
            raise ValueError(f"Partner {partner_id} not found")

        current = PartnerSettings(**partner.settings)
        changes = request.model_dump(exclude_unset=True)

        for field_key, new_value in changes.items():
            if getattr(current, field_key) != new_value:
                setattr(current, field_key, new_value)

        partner.settings = current.model_dump()
        await self.db.flush()
        return current
