from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_partner_id,
    require_owner_in_partner,
    require_staff_in_partner,
)
from app.models.partner_staff import PartnerStaffRole
from app.schemas.point_rule import PointRuleCreateRequest, PointRuleResponse
from app.services.point_rule_service import PointRuleService

router = APIRouter(prefix="/partner/point-rules", tags=["partner-point-rules"])


@router.get("/active", response_model=PointRuleResponse | None)
async def get_active_rule(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
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
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[PointRuleResponse]:
    service = PointRuleService(db)
    return [PointRuleResponse.model_validate(r) for r in await service.list_rules(partner_id=partner_id)]


@router.post("", response_model=PointRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: PointRuleCreateRequest,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
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
