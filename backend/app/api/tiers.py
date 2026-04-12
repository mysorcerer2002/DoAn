from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_tenant_id,
    require_owner_in_tenant,
    require_staff_in_tenant,
)
from app.models.tenant_staff import TenantStaffRole
from app.schemas.tier import TierCreateRequest, TierResponse, TierUpdateRequest
from app.services.tier_service import TierNotFoundError, TierService

router = APIRouter(prefix="/merchant/tiers", tags=["merchant-tiers"])


@router.post("", response_model=TierResponse, status_code=status.HTTP_201_CREATED)
async def create_tier(
    request: TierCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    service = TierService(db)
    tier = await service.create_tier(tenant_id=tenant_id, request=request)
    return TierResponse.model_validate(tier)


@router.get("", response_model=list[TierResponse])
async def list_tiers(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[TierResponse]:
    service = TierService(db)
    tiers = await service.list_tiers(tenant_id=tenant_id)
    return [TierResponse.model_validate(t) for t in tiers]


@router.patch("/{tier_id}", response_model=TierResponse)
async def update_tier(
    tier_id: int,
    request: TierUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    service = TierService(db)
    try:
        tier = await service.update_tier(
            tenant_id=tenant_id, tier_id=tier_id, request=request
        )
    except TierNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TierResponse.model_validate(tier)


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tier(
    tier_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TierService(db)
    try:
        await service.delete_tier(tenant_id=tenant_id, tier_id=tier_id)
    except TierNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
