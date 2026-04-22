"""Pydantic DTO cho flow enroll campaign theo plan voucher rebuild v2.2.

Preview → request-otp → sign. `form_input` gửi nguyên vẹn ở cả 3 bước — FE
giữ state, không lưu server-side giữa các request (đỡ phải Redis).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollFormInput(BaseModel):
    """Phần shop fill instance-level từ template."""

    model_config = ConfigDict(extra="forbid")

    template_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    terms: str | None = Field(default=None, max_length=2000)
    usage_guide: str | None = Field(default=None, max_length=2000)
    support_contact: str | None = Field(default=None, max_length=500)
    discount_value: int = Field(..., gt=0)
    min_order: int = Field(default=0, ge=0)
    max_discount: int | None = Field(default=None, gt=0)
    target_tier_id: int | None = Field(default=None, gt=0)
    max_issuances: int | None = Field(default=None, gt=0)
    starts_at: datetime
    ends_at: datetime


class FeePreviewItem(BaseModel):
    fee_type: str
    description: str
    base_amount: int
    vat_amount: int
    total_with_vat: int


class CampaignEnrollPreviewResponse(BaseModel):
    template_id: int
    template_version: int
    program_form: str
    approval_tier: str
    estimated_cost: int
    service_fee_enabled: bool
    fees: list[FeePreviewItem]
    fee_total_pre_vat: int
    fee_vat_total: int
    fee_total_with_vat: int
    auth_doc_text: str
    auth_doc_hash: str
    consent_text_version: str


class AuthorizationOtpRequest(BaseModel):
    form: EnrollFormInput


class AuthorizationOtpResponse(BaseModel):
    email_masked: str
    ttl_minutes: int
    dev_code: str | None = None


class AuthorizationSignRequest(BaseModel):
    form: EnrollFormInput
    otp_code: str = Field(..., min_length=4, max_length=8)
    consent_checked: bool


class AuthorizationSignResponse(BaseModel):
    campaign_id: int
    authorization_id: int
    approval_status: str
    approval_tier: str
    service_fee_status: str


class CampaignTemplatePublicResponse(BaseModel):
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
