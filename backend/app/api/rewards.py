"""Rewards API — CRUD cho merchant."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant, require_staff_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.reward import RewardCreateRequest, RewardResponse, RewardUpdateRequest
from app.services.reward_service import RewardNotFoundError, RewardService

router = APIRouter(prefix="/merchant/rewards", tags=["merchant-rewards"])


@router.get("", response_model=list[RewardResponse])
async def list_rewards(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    active_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[RewardResponse]:
    service = RewardService(db)
    rows = await service.list_rewards(
        tenant_id=tenant_id, active_only=active_only, limit=limit, offset=offset
    )
    return [RewardResponse.model_validate(r) for r in rows]


@router.post("", response_model=RewardResponse, status_code=201)
async def create_reward(
    body: RewardCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    reward = await service.create_reward(tenant_id=tenant_id, request=body)
    return RewardResponse.model_validate(reward)


@router.get("/{reward_id}", response_model=RewardResponse)
async def get_reward(
    reward_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    try:
        reward = await service.get_reward(tenant_id=tenant_id, reward_id=reward_id)
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RewardResponse.model_validate(reward)


@router.patch("/{reward_id}", response_model=RewardResponse)
async def update_reward(
    reward_id: int,
    body: RewardUpdateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    try:
        reward = await service.update_reward(
            tenant_id=tenant_id, reward_id=reward_id, request=body
        )
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RewardResponse.model_validate(reward)


@router.delete("/{reward_id}", response_model=RewardResponse)
async def delete_reward(
    reward_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    try:
        reward = await service.soft_delete_reward(
            tenant_id=tenant_id, reward_id=reward_id
        )
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RewardResponse.model_validate(reward)
