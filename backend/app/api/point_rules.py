from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    get_tenant_id,
    require_owner_in_tenant,
    require_staff_in_tenant,
)
from app.models.tenant_staff import TenantStaffRole
from app.schemas.point_rule import PointRuleCreateRequest, PointRuleResponse
from app.services.point_rule_service import PointRuleService

router = APIRouter(prefix="/merchant/point-rules", tags=["merchant-point-rules"])


@router.get("/active", response_model=PointRuleResponse | None)
async def get_active_rule(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> PointRuleResponse | None:
    service = PointRuleService(db)
    rule = await service.get_active_rule(tenant_id=tenant_id)
    if rule is None:
        return None
    return PointRuleResponse.model_validate(rule)


@router.get("", response_model=list[PointRuleResponse])
async def list_rules(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[PointRuleResponse]:
    service = PointRuleService(db)
    return [PointRuleResponse.model_validate(r) for r in await service.list_rules(tenant_id=tenant_id)]


@router.post("", response_model=PointRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: PointRuleCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> PointRuleResponse:
    service = PointRuleService(db)
    rule = await service.create_rule(tenant_id=tenant_id, request=request)
    return PointRuleResponse.model_validate(rule)
