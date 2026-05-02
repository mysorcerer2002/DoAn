"""Pydantic schemas cho Reward CRUD."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.reward import RewardOfferType


class RewardCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    points_cost: int = Field(ge=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool = True

    offer_type: RewardOfferType
    offer_value: int | None = None
    offer_label: str = Field(min_length=1, max_length=120)
    min_purchase_amount: int | None = Field(default=None, gt=0)
    valid_from: date | None = None
    valid_until: date | None = None
    terms: str | None = None

    @field_validator("offer_label")
    @classmethod
    def _label_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Nhãn quà bắt buộc")
        return v.strip()

    @model_validator(mode="after")
    def _validate_offer_consistency(self) -> "RewardCreateRequest":
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError("Ngày bắt đầu phải trước ngày kết thúc")
        return self

    @model_validator(mode="after")
    def _validate_offer_type(self) -> "RewardCreateRequest":
        ot = self.offer_type
        if ot == RewardOfferType.PERCENT_DISCOUNT:
            if self.offer_value is None or not (1 <= self.offer_value <= 100):
                raise ValueError("Phần trăm giảm phải từ 1 đến 100")
        elif ot == RewardOfferType.FIXED_DISCOUNT:
            if self.offer_value is None or self.offer_value <= 0:
                raise ValueError("Số tiền giảm phải lớn hơn 0")
        elif ot == RewardOfferType.ITEM_GIFT:
            if self.offer_value is not None:
                raise ValueError("Quà tặng hiện vật không được nhập giá trị giảm")
            if self.min_purchase_amount is not None:
                raise ValueError("Quà tặng hiện vật không được đặt hoá đơn tối thiểu")
        return self


class RewardUpdateRequest(BaseModel):
    """offer_type IMMUTABLE — schema reject explicit thay vì silent ignore (UX rõ hơn)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    points_cost: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    offer_value: int | None = None
    offer_label: str | None = Field(default=None, min_length=1, max_length=120)
    min_purchase_amount: int | None = Field(default=None, gt=0)
    valid_from: date | None = None
    valid_until: date | None = None
    terms: str | None = None

    # Cho phép field offer_type pass qua schema để raise 422 rõ ràng (không silent ignore).
    offer_type: RewardOfferType | None = None

    @model_validator(mode="after")
    def _reject_offer_type_change(self) -> "RewardUpdateRequest":
        if self.offer_type is not None:
            raise ValueError(
                "Loại quà không thể đổi sau khi tạo. Cần đổi → tạo quà mới."
            )
        return self


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

    offer_type: RewardOfferType
    offer_value: int | None
    offer_label: str
    min_purchase_amount: int | None
    valid_from: date | None
    valid_until: date | None
    terms: str | None

    model_config = {"from_attributes": True}


class RewardStatsResponse(BaseModel):
    reward_id: int
    offer_type: str
    issued: int
    redeemed: int
    used: int
    expired: int
    # null khi reward không phải kiểu giảm giá (ITEM_GIFT) → FE hiển thị note thay vì box chi phí.
    total_discount_cost: int | None = None
