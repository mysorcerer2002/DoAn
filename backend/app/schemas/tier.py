from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TierCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    min_points: int = Field(ge=0)
    earn_multiplier: Decimal = Field(
        default=Decimal("1.00"),
        ge=Decimal("0.50"),
        le=Decimal("5.00"),
        decimal_places=2,
    )
    perks: dict = Field(default_factory=dict)


class TierUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    min_points: int | None = Field(default=None, ge=0)
    earn_multiplier: Decimal | None = Field(
        default=None,
        ge=Decimal("0.50"),
        le=Decimal("5.00"),
        decimal_places=2,
    )
    perks: dict | None = None
    is_active: bool | None = None


class TierResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    min_points: int
    earn_multiplier: Decimal
    perks: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
