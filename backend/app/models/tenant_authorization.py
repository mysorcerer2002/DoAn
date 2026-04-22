"""TenantAuthorization — giấy uỷ quyền điện tử shop uỷ cho công ty ops.

M8 của plan voucher rebuild v2.2 (section 4.1). Shop ký văn bản uỷ quyền
công ty nộp hồ sơ Sở CT thay mình. v1 scope cố định `per_campaign`
(mỗi campaign 1 uỷ quyền riêng); framework scope tenant-wide defer sau.

Signature method v1: `click_to_sign` (dev/demo) hoặc `otp_email` (prod —
OTP gửi qua email owner). `digital_cert` + `otp_sms` defer khoá luận.

`signature_payload` JSONB lưu đủ dấu vết pháp lý (I2 plan): ip, user_agent,
session_id, OTP metadata, consent_text_hash + version, rendered_pdf_hash,
server/client clock. Không mutate sau khi ký.

`retention_until = signed_at + 10 năm` (Luật Kế toán 2015 Điều 41) — hard
delete chỉ sau mốc này.

Revoke rule (C4): chỉ cho phép khi
`campaigns.ops_filing_started_at IS NULL AND approval_status != 'approved'`
— enforce ở service layer (phase 7).
"""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AuthorizationScope(str, enum.Enum):
    """Phạm vi uỷ quyền. v1 chỉ per_campaign."""

    PER_CAMPAIGN = "per_campaign"


class SignatureMethod(str, enum.Enum):
    """Phương thức ký điện tử v1."""

    CLICK_TO_SIGN = "click_to_sign"
    OTP_EMAIL = "otp_email"


class TenantAuthorization(Base, TimestampMixin):
    __tablename__ = "tenant_authorizations"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('per_campaign')",
            name="ck_tenant_authorizations_scope",
        ),
        CheckConstraint(
            "signature_method IN ('click_to_sign','otp_email')",
            name="ck_tenant_authorizations_signature_method",
        ),
        CheckConstraint(
            "scope <> 'per_campaign' OR campaign_id IS NOT NULL",
            name="ck_tenant_authorizations_per_campaign_requires_campaign",
        ),
        CheckConstraint(
            "valid_until > valid_from",
            name="ck_tenant_authorizations_valid_window",
        ),
        CheckConstraint(
            "retention_until >= signed_at + INTERVAL '10 years'",
            name="ck_tenant_authorizations_retention_10y",
        ),
        Index(
            "ux_tenant_authorizations_active_per_campaign",
            "tenant_id",
            "campaign_id",
            unique=True,
            postgresql_where=text(
                "scope = 'per_campaign' AND revoked_at IS NULL"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(30), nullable=False)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=True
    )

    document_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    signed_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    signature_method: Mapped[str] = mapped_column(String(30), nullable=False)
    signature_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    retention_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
