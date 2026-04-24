from datetime import datetime

from pydantic import BaseModel, Field


class TierCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    min_points: int = Field(ge=0)
    perks: dict = Field(default_factory=dict)


class TierUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    min_points: int | None = Field(default=None, ge=0)
    perks: dict | None = None
    is_active: bool | None = None


class TierResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    min_points: int
    perks: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
