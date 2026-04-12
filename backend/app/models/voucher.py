"""Voucher model — mã khuyến mãi phát cho khách."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class VoucherStatus(str, enum.Enum):
    ISSUED = "issued"
    USED = "used"
    EXPIRED = "expired"


class Voucher(Base, TimestampMixin):
    """Voucher — code UNIQUE per tenant, partial unique index chống claim trùng."""

    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_vouchers_tenant_code"),
        Index("ix_vouchers_membership_status", "membership_id", "status"),
        Index(
            "uq_vouchers_active_per_member_per_campaign",
            "campaign_id",
            "membership_id",
            unique=True,
            postgresql_where=text("status NOT IN ('used', 'expired')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[VoucherStatus] = mapped_column(
        String(20), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    campaign = relationship("Campaign", lazy="select")
