from datetime import datetime

from pydantic import BaseModel, Field


class MemberLookupRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


class MemberResponse(BaseModel):
    membership_id: int
    tenant_id: int
    user_id: int
    user_phone: str | None
    user_full_name: str | None
    user_email: str | None
    points_balance: int
    total_points_earned: int
    current_tier_id: int | None
    current_tier_name: str | None
    joined_at: datetime
    last_activity_at: datetime | None
    is_new: bool

    model_config = {"from_attributes": True}
