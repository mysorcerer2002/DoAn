from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_partner_id,
    require_owner_in_partner,
    require_staff_in_partner,
)
from app.models.partner_staff import PartnerStaffRole
from app.models.user import User
from app.schemas.settings import (
    PartnerSettings,
    SettingsAuditEntry,
    SettingsUpdateRequest,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/partners/me/settings", tags=["partners-settings"])


@router.get("", response_model=PartnerSettings)
async def get_settings(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerSettings:
    """Đọc shop settings — bất kỳ staff nào của partner đều có quyền."""
    service = SettingsService(db)
    return await service.get_settings(partner_id=partner_id)


@router.patch("", response_model=PartnerSettings)
async def update_settings(
    request: SettingsUpdateRequest,
    partner_id: int = Depends(get_partner_id),
    user: User = Depends(get_current_user),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerSettings:
    service = SettingsService(db)
    return await service.update_settings(
        partner_id=partner_id, user_id=user.id, request=request
    )


@router.get("/audit", response_model=list[SettingsAuditEntry])
async def list_audit(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[SettingsAuditEntry]:
    service = SettingsService(db)
    rows = await service.list_audit(partner_id=partner_id)
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
