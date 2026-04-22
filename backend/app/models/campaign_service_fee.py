"""CampaignServiceFee — phí dịch vụ công ty ops thu shop cho việc nộp hồ sơ.

M9 của plan voucher rebuild v2.2 (section 4.2). Scope đồ án KHÔNG thu phí
thật (`SERVICE_FEE_ENABLED=False`), nhưng data model tạo đủ để khoá luận
bật flag on.

VAT 10% default (Luật Thuế GTGT). `vat_amount` + `total_with_vat` là
GENERATED STORED — DB tự tính từ `amount` và `vat_rate`, không ai write
được (an toàn số liệu kế toán).

Status E1 refund flow: admin reject campaign đã `paid` → batch update
`refund_requested`; kế toán manual chuyển tiền rồi bấm `refunded`. Không
tự động gọi cổng thanh toán.

Retention 10 năm (Luật Kế toán 2015 Điều 41) — fee row không hard delete.
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FeeType(str, enum.Enum):
    SO_CT_FILING = "so_ct_filing"
    DOSSIER_PREPARATION = "dossier_preparation"
    MULTI_PROVINCE = "multi_province"
    EXPRESS = "express"
    WAIVER = "waiver"


class FeeStatus(str, enum.Enum):
    DRAFT = "draft"
    INVOICED = "invoiced"
    PAID = "paid"
    WAIVED = "waived"
    REFUND_REQUESTED = "refund_requested"
    REFUNDED = "refunded"


class EInvoiceProvider(str, enum.Enum):
    MANUAL = "manual"
    VNPT = "vnpt"
    VIETTEL = "viettel"
    MISA = "misa"


class CampaignServiceFee(Base, TimestampMixin):
    __tablename__ = "campaign_service_fees"
    __table_args__ = (
        CheckConstraint(
            "fee_type IN ('so_ct_filing','dossier_preparation','multi_province',"
            "'express','waiver')",
            name="ck_campaign_service_fees_fee_type",
        ),
        CheckConstraint(
            "status IN ('draft','invoiced','paid','waived',"
            "'refund_requested','refunded')",
            name="ck_campaign_service_fees_status",
        ),
        CheckConstraint(
            "e_invoice_provider IN ('manual','vnpt','viettel','misa')",
            name="ck_campaign_service_fees_e_invoice_provider",
        ),
        CheckConstraint(
            "amount >= 0",
            name="ck_campaign_service_fees_amount_nonneg",
        ),
        CheckConstraint(
            "vat_rate >= 0 AND vat_rate <= 99.99",
            name="ck_campaign_service_fees_vat_rate_range",
        ),
        CheckConstraint(
            "retention_until >= created_at + INTERVAL '10 years'",
            name="ck_campaign_service_fees_retention_10y",
        ),
        Index(
            "ux_campaign_service_fees_active_per_type",
            "campaign_id",
            "fee_type",
            unique=True,
            postgresql_where=text("status NOT IN ('waived','refunded')"),
        ),
        Index(
            "ix_campaign_service_fees_tenant_status",
            "tenant_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    fee_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, server_default=text("10.00")
    )
    vat_amount: Mapped[int] = mapped_column(
        BigInteger,
        Computed("(amount * vat_rate / 100)::BIGINT", persisted=True),
        nullable=False,
    )
    total_with_vat: Mapped[int] = mapped_column(
        BigInteger,
        Computed(
            "(amount + (amount * vat_rate / 100)::BIGINT)::BIGINT", persisted=True
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    invoiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invoice_reference: Mapped[str | None] = mapped_column(
        String(120), nullable=True
    )
    e_invoice_provider: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'manual'")
    )
    e_invoice_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    refund_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refund_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    retention_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
