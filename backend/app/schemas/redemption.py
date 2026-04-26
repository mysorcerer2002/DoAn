"""Pydantic schemas cho Redemption flow."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.redemption import RedemptionStatus
from app.models.reward import RewardOfferType


class RedeemRequest(BaseModel):
    reward_id: int = Field(gt=0)


class UseRedemptionRequest(BaseModel):
    code: str = Field(min_length=8, max_length=8)
    # original_amount: tổng bill (VND) khi voucher PERCENT/FIXED discount.
    # gt=0 để tránh gửi 0 cho discount voucher; ITEM_GIFT bỏ trống.
    original_amount: int | None = Field(default=None, gt=0)
    # expected_user_id: backend bắt buộc match chủ voucher để tránh bypass UI gate.
    expected_user_id: int | None = Field(default=None, gt=0)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, v: str) -> str:
        return v.strip().upper()


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
    original_amount: int | None
    discount_amount: int | None

    model_config = {"from_attributes": True}


class RedemptionInspectRewardInfo(BaseModel):
    id: int
    name: str
    image_url: str | None
    offer_type: RewardOfferType
    offer_value: int | None
    offer_label: str


class RedemptionInspectCustomerInfo(BaseModel):
    user_id: int
    full_name: str | None
    phone: str | None


class RedemptionInspectResponse(BaseModel):
    """Preview voucher cho staff TRƯỚC khi xác nhận dùng. Không thay đổi state."""

    redemption_code: str
    status: RedemptionStatus
    points_spent: int
    redeemed_at: datetime
    expires_at: datetime
    reward: RedemptionInspectRewardInfo
    customer: RedemptionInspectCustomerInfo


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
