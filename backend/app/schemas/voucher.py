"""Schemas cho Voucher claim / list."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.voucher import VoucherStatus


class VoucherClaimRequest(BaseModel):
    campaign_id: int = Field(gt=0)


class VoucherResponse(BaseModel):
    id: int
    partner_id: int
    campaign_id: int
    membership_id: int
    code: str
    status: VoucherStatus
    issued_at: datetime
    used_at: datetime | None
    expires_at: datetime
    campaign_name: str | None = None
    campaign_description: str | None = None
    campaign_terms: str | None = None
    campaign_usage_guide: str | None = None
    campaign_support_contact: str | None = None
    discount_type: str | None = None
    discount_value: int | None = None
    min_order: int | None = None
    max_discount: int | None = None

    model_config = {"from_attributes": True}


class CampaignEligibleResponse(BaseModel):
    campaign_id: int
    name: str
    description: str | None
    discount_type: str
    discount_value: int
    min_order: int
    max_discount: int | None
    ends_at: datetime
    issued_count: int
    max_issuances: int | None
