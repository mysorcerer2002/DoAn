from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PointRuleCreateRequest(BaseModel):
    points_per_unit: Decimal = Field(gt=0)
    unit_amount: int = Field(default=1000, gt=0)
    min_amount: int = Field(default=0, ge=0)


class PointRuleResponse(BaseModel):
    id: int
    partner_id: int
    points_per_unit: Decimal
    unit_amount: int
    min_amount: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
