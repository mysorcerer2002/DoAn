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
    tenant_id: int
    membership_id: int
    reward_id: int
    points_spent: int
    redemption_code: str
    status: RedemptionStatus
    redeemed_at: datetime
    used_at: datetime | None
    used_by_staff_id: int | None
    expires_at: datetime

    model_config = {"from_attributes": True}
