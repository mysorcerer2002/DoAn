"""Redemptions API — staff-side đổi quà + xác nhận sử dụng.

Customer self-redeem ở `POST /users/me/redemptions` (partners.users_router).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_current_user,
    get_partner_id,
    require_owner_in_partner,
    require_staff_in_partner,
)
from app.core.limiter import limiter
from app.models.membership import Membership
from app.models.user import User
from app.schemas.redemption import RedeemRequest, RedemptionResponse, UseRedemptionRequest
from app.services.redemption_service import (
    InsufficientPointsError,
    OutOfStockError,
    RedemptionNotFoundError,
    RedemptionService,
)

router = APIRouter(prefix="/partner/redemptions", tags=["partner-redemptions"])


@router.post("/for-member/{membership_id}", response_model=RedemptionResponse, status_code=201)
@limiter.limit("10/minute")
async def redeem_reward_for_member(
    request: Request,
    membership_id: int,
    body: RedeemRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_staff_in_partner),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Owner đổi quà thay cho member."""
    from sqlalchemy import select

    member_user_id = await db.scalar(
        select(Membership.user_id).where(
            Membership.id == membership_id,
            Membership.partner_id == partner_id,
        )
    )
    if member_user_id is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    service = RedemptionService(db)
    try:
        redemption = await service.redeem(
            partner_id=partner_id,
            user_id=member_user_id,
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
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_staff_in_partner),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Owner xác nhận sử dụng mã đổi quà."""
    service = RedemptionService(db)
    try:
        redemption = await service.use_redemption(
            partner_id=partner_id, code=body.code, staff_id=user.id
        )
    except RedemptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)


@router.get("", response_model=list[RedemptionResponse])
async def list_redemptions(
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[RedemptionResponse]:
    service = RedemptionService(db)
    rows = await service.list_tenant_redemptions(
        partner_id=partner_id, limit=limit, offset=offset
    )
    return [RedemptionResponse.model_validate(r) for r in rows]
