from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PointRuleCreateRequest(BaseModel):
    points_per_unit: Decimal = Field(gt=0)
    unit_amount: int = Field(default=1000, gt=0)
    min_amount: int = Field(default=0, ge=0)
    use_tiers: bool = False


class PointRuleUpdate(BaseModel):
    points_per_unit: Decimal | None = Field(default=None, gt=0)
    unit_amount: int | None = Field(default=None, gt=0)
    min_amount: int | None = Field(default=None, ge=0)
    use_tiers: bool | None = None
    is_active: bool | None = None


class PointRuleResponse(BaseModel):
    id: int
    partner_id: int
    points_per_unit: Decimal
    unit_amount: int
    min_amount: int
    use_tiers: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
