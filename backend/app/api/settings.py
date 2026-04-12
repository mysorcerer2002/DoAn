from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_tenant_id,
    require_owner_in_tenant,
)
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.schemas.settings import (
    SettingsAuditEntry,
    SettingsUpdateRequest,
    TenantSettings,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/tenants/me/settings", tags=["tenants-settings"])


@router.get("", response_model=TenantSettings)
async def get_settings(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantSettings:
    service = SettingsService(db)
    return await service.get_settings(tenant_id=tenant_id)


@router.patch("", response_model=TenantSettings)
async def update_settings(
    request: SettingsUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantSettings:
    service = SettingsService(db)
    return await service.update_settings(
        tenant_id=tenant_id, user_id=user.id, request=request
    )


@router.get("/audit", response_model=list[SettingsAuditEntry])
async def list_audit(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[SettingsAuditEntry]:
    service = SettingsService(db)
    rows = await service.list_audit(tenant_id=tenant_id)
    return [
        SettingsAuditEntry(
            id=r.id,
            field_key=r.field_key,
            old_value=r.old_value.get("value") if r.old_value else None,
            new_value=r.new_value.get("value") if r.new_value else None,
            user_id=r.user_id,
            created_at=r.created_at,
        )
        for r in rows
    ]
