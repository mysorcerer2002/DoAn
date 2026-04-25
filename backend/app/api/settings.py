from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_partner_id,
    require_owner_in_partner,
)
from app.schemas.settings import (
    PartnerSettings,
    SettingsUpdateRequest,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/partners/me/settings", tags=["partners-settings"])


@router.get("", response_model=PartnerSettings)
async def get_settings(
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerSettings:
    """Đọc shop settings — owner only (MVP final 1 owner / shop)."""
    service = SettingsService(db)
    return await service.get_settings(partner_id=partner_id)


@router.patch("", response_model=PartnerSettings)
async def update_settings(
    request: SettingsUpdateRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerSettings:
    service = SettingsService(db)
    return await service.update_settings(partner_id=partner_id, request=request)
