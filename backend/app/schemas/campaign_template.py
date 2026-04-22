"""Pydantic DTOs cho admin CRUD campaign templates.

Template là khung khuyến mãi do admin/công ty định nghĩa. Shop chọn template
khi enroll campaign, fill các trường instance-level (name cụ thể, discount_value
trong cap, ngày bắt đầu/kết thúc, max_issuances trong cap…).

`approval_tier_hint` không lưu DB — tính động ở
`CampaignTemplateService.compute_tier_hint(program_form, estimated_cost)`.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.campaign import CampaignSource, DiscountType
from app.models.campaign_template import ProgramForm


class CampaignTemplateBase(BaseModel):
    """Field chung giữa create/update — validate cap/percent/ttl ở đây."""

    code: str = Field(min_length=3, max_length=60)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    source: CampaignSource
    program_form: ProgramForm
    discount_type: DiscountType

    default_usage_guide: str | None = Field(default=None, max_length=2000)
    default_support_contact: str | None = Field(default=None, max_length=200)
    default_terms: str | None = Field(default=None, max_length=2000)

    max_discount_percent_cap: int | None = Field(default=None, ge=1, le=50)
    max_discount_value_cap: int | None = Field(default=None, ge=1)
    max_discount_fixed_cap: int | None = Field(default=None, ge=1)

    min_order_floor: int = Field(default=0, ge=0)
    max_issuances_cap: int | None = Field(default=None, ge=1)
    max_duration_days: int | None = Field(default=None, ge=1, le=365)
    min_voucher_ttl_days: int = Field(default=7, ge=1, le=365)
    max_voucher_ttl_days: int = Field(default=30, ge=1, le=365)

    is_active: bool = True


class CampaignTemplateCreateRequest(CampaignTemplateBase):
    """Create payload — version mặc định = 1, service set."""

    @model_validator(mode="after")
    def _validate_caps_match_type(self) -> "CampaignTemplateCreateRequest":
        if self.discount_type == DiscountType.PERCENT:
            if self.max_discount_percent_cap is None or self.max_discount_value_cap is None:
                raise ValueError(
                    "discount_type=percent cần max_discount_percent_cap "
                    "(<= 50) và max_discount_value_cap (> 0)"
                )
        elif self.discount_type == DiscountType.FIXED:
            if self.max_discount_fixed_cap is None:
                raise ValueError(
                    "discount_type=fixed cần max_discount_fixed_cap (> 0)"
                )
        if self.max_voucher_ttl_days < self.min_voucher_ttl_days:
            raise ValueError(
                "max_voucher_ttl_days phải >= min_voucher_ttl_days"
            )
        return self


class CampaignTemplateUpdateRequest(BaseModel):
    """Partial update — chỉ các field không phá contract đã enroll.

    Đổi rule (caps, program_form, discount_type) → service bump `version`
    để campaign tương lai dùng version mới; campaign cũ giữ snapshot cũ.
    """

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    program_form: ProgramForm | None = None
    discount_type: DiscountType | None = None

    default_usage_guide: str | None = Field(default=None, max_length=2000)
    default_support_contact: str | None = Field(default=None, max_length=200)
    default_terms: str | None = Field(default=None, max_length=2000)

    max_discount_percent_cap: int | None = Field(default=None, ge=1, le=50)
    max_discount_value_cap: int | None = Field(default=None, ge=1)
    max_discount_fixed_cap: int | None = Field(default=None, ge=1)

    min_order_floor: int | None = Field(default=None, ge=0)
    max_issuances_cap: int | None = Field(default=None, ge=1)
    max_duration_days: int | None = Field(default=None, ge=1, le=365)
    min_voucher_ttl_days: int | None = Field(default=None, ge=1, le=365)
    max_voucher_ttl_days: int | None = Field(default=None, ge=1, le=365)

    is_active: bool | None = None


class CampaignTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    source: str
    program_form: str
    discount_type: str

    default_usage_guide: str | None
    default_support_contact: str | None
    default_terms: str | None

    max_discount_percent_cap: int | None
    max_discount_value_cap: int | None
    max_discount_fixed_cap: int | None

    min_order_floor: int
    max_issuances_cap: int | None
    max_duration_days: int | None
    min_voucher_ttl_days: int
    max_voucher_ttl_days: int

    version: int
    is_active: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
