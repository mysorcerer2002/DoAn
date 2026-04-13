from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant
from app.core.tenant_cache import tenant_role_cache
from app.models.tenant_staff import TenantStaffRole
from app.schemas.tenant_staff import (
    StaffAddRequest,
    StaffAddResponse,
    StaffResponse,
    StaffUpdateRoleRequest,
)
from app.services.tenant_staff_service import (
    LastOwnerError,
    StaffAlreadyInTenantError,
    StaffNotFoundError,
    TenantStaffService,
)

router = APIRouter(prefix="/merchant/staff", tags=["merchant-staff"])


@router.post("", response_model=StaffAddResponse, status_code=status.HTTP_201_CREATED)
async def add_staff(
    request: StaffAddRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> StaffAddResponse:
    service = TenantStaffService(db)
    try:
        return await service.add_staff(tenant_id=tenant_id, request=request)
    except StaffAlreadyInTenantError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("", response_model=list[StaffResponse])
async def list_staff(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[StaffResponse]:
    service = TenantStaffService(db)
    return await service.list_staff(tenant_id=tenant_id, limit=limit, offset=offset)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff_role(
    staff_id: int,
    body: StaffUpdateRoleRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    service = TenantStaffService(db)
    try:
        result = await service.update_role(
            tenant_id=tenant_id, staff_id=staff_id, request=body
        )
    except StaffNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LastOwnerError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    tenant_role_cache.invalidate(user_id=result.user_id, tenant_id=tenant_id)
    return result


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_staff(
    staff_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TenantStaffService(db)
    try:
        removed_user_id = await service.remove_staff(
            tenant_id=tenant_id, staff_id=staff_id
        )
    except StaffNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LastOwnerError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    tenant_role_cache.invalidate(user_id=removed_user_id, tenant_id=tenant_id)
