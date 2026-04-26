"""Pydantic schemas cho Redemption flow."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.redemption import RedemptionStatus


class RedeemRequest(BaseModel):
    reward_id: int = Field(gt=0)


class UseRedemptionRequest(BaseModel):
    code: str = Field(min_length=8, max_length=8)


class RedemptionResponse(BaseModel):
    id: int
    partner_id: int
    user_id: int
    reward_id: int
    points_spent: int
    redemption_code: str
    status: RedemptionStatus
    redeemed_at: datetime
    used_at: datetime | None
    used_by_staff_id: int | None
    expires_at: datetime
    snapshot_image_url: str | None

    model_config = {"from_attributes": True}


class MyRedemptionListItem(BaseModel):
    id: int
    redemption_code: str
    points_spent: int
    status: str
    redeemed_at: datetime
    expires_at: datetime
    used_at: datetime | None
    partner_id: int
    partner_name: str
    reward_id: int
    reward_name: str
    reward_image_url: str | None

    model_config = {"from_attributes": True}


class MyRedemptionListResponse(BaseModel):
    items: list[MyRedemptionListItem]
    total: int
    limit: int
    offset: int


class MyRedemptionDetailResponse(MyRedemptionListItem):
    snapshot_image_url: str | None
    reward_description: str | None
    reward_terms: str | None
