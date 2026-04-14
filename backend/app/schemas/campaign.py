"""Schemas cho Campaign CRUD."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.campaign import CampaignSource, DiscountType


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    terms: str | None = Field(default=None, max_length=2000)
    usage_guide: str | None = Field(default=None, max_length=2000)
    support_contact: str | None = Field(default=None, max_length=500)
    discount_type: DiscountType
    discount_value: int = Field(gt=0)
    min_order: int = Field(default=0, ge=0)
    max_discount: int | None = Field(default=None, gt=0)
    target_tier_id: int | None = None
    max_issuances: int | None = Field(default=None, gt=0)
    starts_at: datetime
    ends_at: datetime
    source: CampaignSource = CampaignSource.MANUAL

    @model_validator(mode="after")
    def validate_dates_and_percent(self) -> "CampaignCreateRequest":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be > starts_at")
        if self.discount_type == DiscountType.PERCENT and self.discount_value > 100:
            raise ValueError("percent discount must be <= 100")
        return self


class CampaignUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    terms: str | None = Field(default=None, max_length=2000)
    usage_guide: str | None = Field(default=None, max_length=2000)
    support_contact: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    ends_at: datetime | None = None
    max_issuances: int | None = Field(default=None, gt=0)


class CampaignResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str | None
    terms: str | None = None
    usage_guide: str | None = None
    support_contact: str | None = None
    discount_type: DiscountType
    discount_value: int
    min_order: int
    max_discount: int | None
    target_tier_id: int | None
    max_issuances: int | None
    issued_count: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    source: CampaignSource
    deleted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignRoiResponse(BaseModel):
    campaign_id: int
    name: str
    vouchers_issued: int
    vouchers_used: int
    total_discount_amount: int
    total_revenue_from_voucher_txns: int
