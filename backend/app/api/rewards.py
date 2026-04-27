"""Rewards API — CRUD cho merchant."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_partner_id, require_owner_in_partner
from app.schemas.reward import (
    RewardCreateRequest,
    RewardResponse,
    RewardStatsResponse,
    RewardUpdateRequest,
)
from app.services.reward_service import RewardNotFoundError, RewardService, RewardValidationError

router = APIRouter(prefix="/partner/rewards", tags=["partner-rewards"])


@router.get("", response_model=list[RewardResponse])
async def list_rewards(
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    active_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[RewardResponse]:
    service = RewardService(db)
    rows = await service.list_rewards(
        partner_id=partner_id, active_only=active_only, limit=limit, offset=offset
    )
    return [RewardResponse.model_validate(r) for r in rows]


@router.post("", response_model=RewardResponse, status_code=201)
async def create_reward(
    body: RewardCreateRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    reward = await service.create_reward(partner_id=partner_id, request=body)
    return RewardResponse.model_validate(reward)


@router.get("/{reward_id}/stats", response_model=RewardStatsResponse)
async def get_reward_stats(
    reward_id: int,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> RewardStatsResponse:
    service = RewardService(db)
    try:
        return await service.get_stats(partner_id=partner_id, reward_id=reward_id)
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{reward_id}", response_model=RewardResponse)
async def get_reward(
    reward_id: int,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    try:
        reward = await service.get_reward(partner_id=partner_id, reward_id=reward_id)
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RewardResponse.model_validate(reward)


@router.patch("/{reward_id}", response_model=RewardResponse)
async def update_reward(
    reward_id: int,
    body: RewardUpdateRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    try:
        reward = await service.update_reward(
            partner_id=partner_id, reward_id=reward_id, request=body
        )
    except RewardValidationError as e:
        raise HTTPException(status_code=422, detail=e.message) from e
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RewardResponse.model_validate(reward)


@router.delete("/{reward_id}", response_model=RewardResponse)
async def delete_reward(
    reward_id: int,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    service = RewardService(db)
    try:
        reward = await service.soft_delete_reward(
            partner_id=partner_id, reward_id=reward_id
        )
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RewardResponse.model_validate(reward)
