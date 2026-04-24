from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Partner
from app.models.partner_settings_audit import PartnerSettingsAudit
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
        user_id: int,
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
            old_value = getattr(current, field_key)
            if old_value != new_value:
                self.db.add(
                    PartnerSettingsAudit(
                        partner_id=partner_id,
                        user_id=user_id,
                        field_key=field_key,
                        old_value={"value": old_value},
                        new_value={"value": new_value},
                    )
                )
                setattr(current, field_key, new_value)

        partner.settings = current.model_dump()
        await self.db.flush()
        return current

    async def list_audit(self, *, partner_id: int, limit: int = 50) -> list[PartnerSettingsAudit]:
        rows = await self.db.scalars(
            select(PartnerSettingsAudit)
            .where(PartnerSettingsAudit.partner_id == partner_id)
            .order_by(PartnerSettingsAudit.created_at.desc())
            .limit(limit)
        )
        return list(rows.all())
