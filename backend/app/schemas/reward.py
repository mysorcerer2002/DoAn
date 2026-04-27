"""Pydantic schemas cho Reward CRUD."""

from datetime import datetime

from pydantic import BaseModel, Field


class RewardCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    points_cost: int = Field(gt=0)
    stock: int | None = Field(default=None, ge=0)


class RewardUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    points_cost: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class RewardResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    description: str | None
    image_url: str | None
    points_cost: int
    stock: int | None
    is_active: bool
    deleted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RewardStatsResponse(BaseModel):
    reward_id: int
    issued: int
    redeemed: int
    used: int
    expired: int
    # null khi reward không phải kiểu giảm giá (ITEM_GIFT) → FE ẩn dòng "Tổng chi phí".
    total_discount_cost: int | None = None
