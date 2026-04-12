from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id
from app.models.tenant import TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreateRequest, TenantResponse
from app.services.tenant_service import TenantNotFoundError, TenantService

merchant_router = APIRouter(prefix="/merchant", tags=["merchant"])
tenants_router = APIRouter(prefix="/tenants", tags=["tenants"])


@merchant_router.post(
    "/register",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_tenant(
    request: TenantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Owner đăng ký doanh nghiệp mới (status=pending, chờ Super Admin duyệt)."""
    service = TenantService(db)
    tenant = await service.create_tenant(owner=current_user, request=request)
    return TenantResponse.model_validate(tenant)


@tenants_router.get("/users/me/tenants")
async def list_my_tenants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List tenant mà user là staff/owner. Frontend dùng để chọn tenant sau login."""
    service = TenantService(db)
    return await service.list_tenants_for_user(user_id=user.id)


@tenants_router.get("/me", response_model=TenantResponse)
async def get_my_tenant(
    tenant_id: int = Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Lấy thông tin tenant theo header X-Tenant-Id. Yêu cầu status=active."""
    service = TenantService(db)
    try:
        tenant = await service.get_tenant_by_id(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant is {tenant.status.value}, not active",
        )

    return TenantResponse.model_validate(tenant)
