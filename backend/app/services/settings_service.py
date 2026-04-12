from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.tenant_settings_audit import TenantSettingsAudit
from app.schemas.settings import SettingsUpdateRequest, TenantSettings


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, *, tenant_id: int) -> TenantSettings:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        return TenantSettings(**tenant.settings)

    async def update_settings(
        self,
        *,
        tenant_id: int,
        user_id: int,
        request: SettingsUpdateRequest,
    ) -> TenantSettings:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")

        current = TenantSettings(**tenant.settings)
        changes = request.model_dump(exclude_unset=True)

        for field_key, new_value in changes.items():
            old_value = getattr(current, field_key)
            if old_value != new_value:
                self.db.add(
                    TenantSettingsAudit(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        field_key=field_key,
                        old_value={"value": old_value},
                        new_value={"value": new_value},
                    )
                )
                setattr(current, field_key, new_value)

        tenant.settings = current.model_dump()
        await self.db.flush()
        return current

    async def list_audit(self, *, tenant_id: int, limit: int = 50) -> list[TenantSettingsAudit]:
        rows = await self.db.scalars(
            select(TenantSettingsAudit)
            .where(TenantSettingsAudit.tenant_id == tenant_id)
            .order_by(TenantSettingsAudit.created_at.desc())
            .limit(limit)
        )
        return list(rows.all())
