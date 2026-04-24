from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_partner_id,
    require_owner_in_partner,
    require_staff_in_partner,
)
from app.models.partner_staff import PartnerStaffRole
from app.schemas.tier import TierCreateRequest, TierResponse, TierUpdateRequest
from app.services.tier_service import TierNotFoundError, TierService

router = APIRouter(prefix="/partner/tiers", tags=["partner-tiers"])


@router.post("", response_model=TierResponse, status_code=status.HTTP_201_CREATED)
async def create_tier(
    request: TierCreateRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    service = TierService(db)
    tier = await service.create_tier(partner_id=partner_id, request=request)
    return TierResponse.model_validate(tier)


@router.get("", response_model=list[TierResponse])
async def list_tiers(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[TierResponse]:
    service = TierService(db)
    tiers = await service.list_tiers(partner_id=partner_id)
    return [TierResponse.model_validate(t) for t in tiers]


@router.patch("/{tier_id}", response_model=TierResponse)
async def update_tier(
    tier_id: int,
    request: TierUpdateRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    service = TierService(db)
    try:
        tier = await service.update_tier(
            partner_id=partner_id, tier_id=tier_id, request=request
        )
    except TierNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TierResponse.model_validate(tier)


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tier(
    tier_id: int,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TierService(db)
    try:
        await service.delete_tier(partner_id=partner_id, tier_id=tier_id)
    except TierNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
