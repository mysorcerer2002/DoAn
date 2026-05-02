from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PointRuleCreateRequest(BaseModel):
    earn_percent: Decimal = Field(
        default=Decimal("1.00"),
        ge=Decimal("0.01"),
        le=Decimal("99.99"),
        description="Phần trăm giá trị hóa đơn quy đổi thành điểm (0.01% — 99.99%)",
    )
    use_tiers: bool = False


class PointRuleUpdate(BaseModel):
    earn_percent: Decimal | None = Field(default=None, ge=Decimal("0.01"), le=Decimal("99.99"))
    use_tiers: bool | None = None
    is_active: bool | None = None


class PointRuleResponse(BaseModel):
    id: int
    partner_id: int
    earn_percent: Decimal
    use_tiers: bool
    is_active: bool
    created_at: datetime  # GIỮ field cũ — không break consumer khác

    model_config = {"from_attributes": True}
