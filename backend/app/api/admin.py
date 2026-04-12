from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_super_admin
from app.models.tenant import TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantApprovalRequest, TenantResponse
from app.services.tenant_service import TenantNotFoundError, TenantService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(
    tenant_status: TenantStatus | None = Query(default=None, alias="status"),
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[TenantResponse]:
    """Super Admin xem danh sách tenant (filter theo status)."""
    service = TenantService(db)
    tenants = await service.list_tenants(status=tenant_status)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.post("/tenants/{tenant_id}/approve", response_model=TenantResponse)
async def approve_tenant(
    tenant_id: int,
    body: TenantApprovalRequest,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Super Admin approve/reject tenant."""
    service = TenantService(db)
    try:
        if body.approve:
            tenant = await service.approve_tenant(tenant_id=tenant_id)
        else:
            tenant = await service.suspend_tenant(tenant_id=tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TenantResponse.model_validate(tenant)
