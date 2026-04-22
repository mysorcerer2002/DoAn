"""Schemas cho tenant_authorization + campaign_service_fee ở merchant API.

Phase 7 plan voucher rebuild v2.2.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Whitelist field trong signature_payload được lộ ra owner — loại bỏ bất kỳ
# key future có dính OTP raw / hash nhạy cảm. Schema khoá các field hiện tại
# Phase 6 ghi; bổ sung sau phải update ở đây (regression guard).
_SIGNATURE_PAYLOAD_PUBLIC_KEYS = {
    "ip",
    "user_agent",
    "otp_purpose",
    "consent_text_version",
    "consent_text_hash",
    "doc_hash",
    "template_version",
    "signed_at_server",
    "signed_at_client",
    "session_id",
    "otp_delivery_address",
    "otp_attempts_count",
    "rendered_pdf_hash",
}


class SignaturePayloadPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ip: str | None = None
    user_agent: str | None = None
    otp_purpose: str | None = None
    consent_text_version: str | None = None
    consent_text_hash: str | None = None
    doc_hash: str | None = None
    template_version: int | None = None
    signed_at_server: str | None = None
    signed_at_client: str | None = None
    session_id: str | None = None
    otp_delivery_address: str | None = None
    otp_attempts_count: int | None = None
    rendered_pdf_hash: str | None = None


class TenantAuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    scope: str
    campaign_id: int | None
    document_content_hash: str
    document_url: str | None
    signed_by_user_id: int
    signed_at: datetime
    signature_method: str
    signature_payload: SignaturePayloadPublic
    valid_from: datetime
    valid_until: datetime
    revoked_at: datetime | None
    revoked_reason: str | None
    retention_until: datetime

    @field_validator("signature_payload", mode="before")
    @classmethod
    def _whitelist_payload(cls, v):
        if isinstance(v, dict):
            return {k: v[k] for k in _SIGNATURE_PAYLOAD_PUBLIC_KEYS if k in v}
        return v


class TenantAuthorizationSummaryResponse(BaseModel):
    """Bản rút gọn — không trả signature_payload (có OTP metadata)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    scope: str
    campaign_id: int | None
    document_content_hash: str
    signed_at: datetime
    signature_method: str
    valid_from: datetime
    valid_until: datetime
    revoked_at: datetime | None
    revoked_reason: str | None


class AuthorizationRevokeRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class CampaignServiceFeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    fee_type: str
    amount: int
    vat_rate: Decimal
    vat_amount: int
    total_with_vat: int
    description: str
    status: str
    invoiced_at: datetime | None
    paid_at: datetime | None
    invoice_reference: str | None
    e_invoice_provider: str
    refund_requested_at: datetime | None
    refunded_at: datetime | None
    refund_reason: str | None
