"""Schemas dành riêng cho admin endpoints (login logs, point adjustments, points summary)."""

from datetime import datetime

from pydantic import BaseModel


# ==================== Point Adjustments ====================

class PointAdjustmentResponse(BaseModel):
    id: int
    user_id: int
    user_email: str | None
    partner_id: int
    partner_name: str | None
    actor_user_id: int | None
    actor_email: str | None
    delta: int
    balance_after: int
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PointAdjustmentListResponse(BaseModel):
    items: list[PointAdjustmentResponse]
    total: int
    limit: int
    offset: int


# ==================== Points Summary ====================

class PartnerEarnedItem(BaseModel):
    partner_id: int
    name: str
    total_earned: int


class PointsSummaryResponse(BaseModel):
    total_circulating: int
    total_earned: int
    total_redeemed: int
    total_adjusted: int
    by_partner: list[PartnerEarnedItem]
