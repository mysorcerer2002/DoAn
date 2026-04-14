"""Redemptions API — đổi quà + xác nhận sử dụng."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_tenant_id,
    require_owner_in_tenant,
    require_staff_in_tenant,
)
from app.core.limiter import limiter
from app.models.membership import Membership
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.schemas.redemption import RedeemRequest, RedemptionResponse, UseRedemptionRequest
from app.services.redemption_service import (
    InsufficientPointsError,
    OutOfStockError,
    RedemptionNotFoundError,
    RedemptionService,
)

router = APIRouter(prefix="/merchant/redemptions", tags=["merchant-redemptions"])


@router.post("", response_model=RedemptionResponse, status_code=201)
@limiter.limit("10/minute")
async def redeem_reward(
    request: Request,
    body: RedeemRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Đổi quà cho membership. Staff phải chỉ định membership_id qua query."""
    from sqlalchemy import select

    # Tìm membership của user hiện tại trong tenant
    membership = await db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user.id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    service = RedemptionService(db)
    try:
        redemption = await service.redeem(
            tenant_id=tenant_id,
            membership_id=membership.id,
            reward_id=body.reward_id,
        )
    except InsufficientPointsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OutOfStockError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)


@router.post("/for-member/{membership_id}", response_model=RedemptionResponse, status_code=201)
@limiter.limit("10/minute")
async def redeem_reward_for_member(
    request: Request,
    membership_id: int,
    body: RedeemRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Staff đổi quà thay cho member."""
    service = RedemptionService(db)
    try:
        redemption = await service.redeem(
            tenant_id=tenant_id,
            membership_id=membership_id,
            reward_id=body.reward_id,
        )
    except InsufficientPointsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OutOfStockError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)


@router.post("/use", response_model=RedemptionResponse)
async def use_redemption(
    body: UseRedemptionRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Nhân viên xác nhận sử dụng mã đổi quà."""
    service = RedemptionService(db)
    try:
        redemption = await service.use_redemption(
            tenant_id=tenant_id, code=body.code, staff_id=user.id
        )
    except RedemptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)


@router.get("", response_model=list[RedemptionResponse])
async def list_redemptions(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[RedemptionResponse]:
    service = RedemptionService(db)
    rows = await service.list_tenant_redemptions(
        tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [RedemptionResponse.model_validate(r) for r in rows]
