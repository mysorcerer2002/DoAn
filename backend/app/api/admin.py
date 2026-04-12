from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_super_admin
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.analytics import PlatformStatsResponse, TenantDetailResponse
from app.schemas.ledger import ReconcileResponse
from app.schemas.tenant import TenantApprovalRequest, TenantResponse
from app.services.ledger_service import LedgerService
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


@router.post(
    "/reconcile/{membership_id}",
    response_model=ReconcileResponse,
    status_code=status.HTTP_200_OK,
)
async def reconcile_member_balance(
    membership_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ReconcileResponse:
    """Super Admin kiểm tra tính nhất quán giữa points_balance và ledger."""
    service = LedgerService(db)
    result = await service.reconcile(membership_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Membership không tồn tại")
    return result


@router.get("/tenants/{tenant_id}/detail", response_model=TenantDetailResponse)
async def get_tenant_detail(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantDetailResponse:
    """Super Admin xem chi tiết tenant kèm thống kê."""
    service = TenantService(db)
    try:
        tenant = await service.get_tenant_by_id(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    member_count = int(
        await db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.tenant_id == tenant_id,
                Membership.archived_at.is_(None),
            )
        )
        or 0
    )
    txn_result = await db.execute(
        select(
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.net_amount), 0),
        ).where(Transaction.tenant_id == tenant_id)
    )
    txn_count, total_revenue = txn_result.one()

    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        member_count=member_count,
        transaction_count=int(txn_count),
        total_revenue=int(total_revenue),
    )


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Super Admin suspend một tenant."""
    service = TenantService(db)
    try:
        tenant = await service.suspend_tenant(tenant_id=tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TenantResponse.model_validate(tenant)


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformStatsResponse:
    """Thống kê toàn platform cho super admin."""
    tenants_count = await db.scalar(
        select(func.count()).select_from(Tenant)
    )
    users_count = await db.scalar(
        select(func.count()).select_from(User)
    )
    txn_count = await db.scalar(
        select(func.count()).select_from(Transaction)
    )
    return PlatformStatsResponse(
        total_tenants=int(tenants_count or 0),
        total_users=int(users_count or 0),
        total_transactions=int(txn_count or 0),
    )
