from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_partner_id,
    require_owner_in_partner,
)
from app.models.point_rule import PointRule
from app.schemas.point_rule import PointRuleCreateRequest, PointRuleResponse, PointRuleUpdate
from app.services.point_rule_service import PointRuleService

router = APIRouter(prefix="/partner/point-rules", tags=["partner-point-rules"])


@router.get("/active", response_model=PointRuleResponse | None)
async def get_active_rule(
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PointRuleResponse | None:
    service = PointRuleService(db)
    rule = await service.get_active_rule(partner_id=partner_id)
    if rule is None:
        return None
    return PointRuleResponse.model_validate(rule)


@router.get("", response_model=list[PointRuleResponse])
async def list_rules(
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[PointRuleResponse]:
    service = PointRuleService(db)
    return [PointRuleResponse.model_validate(r) for r in await service.list_rules(partner_id=partner_id)]


@router.post("", response_model=PointRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: PointRuleCreateRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PointRuleResponse:
    service = PointRuleService(db)
    try:
        rule = await service.create_rule(partner_id=partner_id, request=request)
    except IntegrityError as e:
        # Race window: 2 owner cùng tạo rule → partial unique index reject 1
        raise HTTPException(
            status_code=409,
            detail="Another active rule was created concurrently, please retry",
        ) from e
    return PointRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=PointRuleResponse)
async def update_point_rule(
    rule_id: int,
    request: PointRuleUpdate,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
) -> PointRuleResponse:
    rule = await db.get(PointRule, rule_id)
    if rule is None or rule.partner_id != partner_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy công thức tích điểm.")
    payload = request.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(rule, key, value)
    await db.flush()
    await db.refresh(rule)
    return PointRuleResponse.model_validate(rule)
