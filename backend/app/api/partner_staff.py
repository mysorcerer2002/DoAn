from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_partner_id, require_owner_in_partner
from app.core.partner_cache import partner_role_cache
from app.models.partner_staff import PartnerStaffRole
from app.schemas.partner_staff import (
    StaffAddRequest,
    StaffAddResponse,
    StaffResponse,
    StaffUpdateRoleRequest,
)
from app.services.partner_staff_service import (
    LastOwnerError,
    StaffAlreadyInPartnerError,
    StaffNotFoundError,
    PartnerStaffService,
)

router = APIRouter(prefix="/partner/staff", tags=["partner-staff"])


@router.post("", response_model=StaffAddResponse, status_code=status.HTTP_201_CREATED)
async def add_staff(
    request: StaffAddRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> StaffAddResponse:
    service = PartnerStaffService(db)
    try:
        return await service.add_staff(partner_id=partner_id, request=request)
    except StaffAlreadyInPartnerError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("", response_model=list[StaffResponse])
async def list_staff(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[StaffResponse]:
    service = PartnerStaffService(db)
    return await service.list_staff(partner_id=partner_id, limit=limit, offset=offset)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff_role(
    staff_id: int,
    body: StaffUpdateRoleRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    service = PartnerStaffService(db)
    try:
        result = await service.update_role(
            partner_id=partner_id, staff_id=staff_id, request=body
        )
    except StaffNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LastOwnerError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    partner_role_cache.invalidate(user_id=result.user_id, partner_id=partner_id)
    return result


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_staff(
    staff_id: int,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = PartnerStaffService(db)
    try:
        removed_user_id = await service.remove_staff(
            partner_id=partner_id, staff_id=staff_id
        )
    except StaffNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LastOwnerError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    partner_role_cache.invalidate(user_id=removed_user_id, partner_id=partner_id)
