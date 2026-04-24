"""Voucher model — mã khuyến mãi phát cho khách."""

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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class VoucherStatus(str, enum.Enum):
    ISSUED = "issued"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class IssueSource(str, enum.Enum):
    """Nguồn phát voucher — `legacy` cho voucher trước M4."""

    LEGACY = "legacy"
    MANUAL = "manual"
    BULK_DISTRIBUTION = "bulk_distribution"
    SIGNUP_JOB = "signup_job"
    BIRTHDAY_JOB = "birthday_job"


class Voucher(Base, TimestampMixin):
    """Voucher — code UNIQUE per partner, partial unique index chống claim trùng."""

    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("partner_id", "code", name="uq_vouchers_partner_code"),
        CheckConstraint(
            "status IN ('issued','used','expired','cancelled')",
            name="ck_vouchers_status",
        ),
        CheckConstraint(
            "status <> 'cancelled' OR ("
            "cancelled_at IS NOT NULL AND cancelled_reason IS NOT NULL)",
            name="ck_vouchers_cancelled_needs_meta",
        ),
        CheckConstraint(
            "issue_source IN ("
            "'legacy','manual','bulk_distribution','signup_job','birthday_job')",
            name="ck_vouchers_issue_source",
        ),
        Index("ix_vouchers_membership_status", "membership_id", "status"),
        Index(
            "uq_vouchers_active_per_member_per_campaign",
            "campaign_id",
            "membership_id",
            unique=True,
            postgresql_where=text("status NOT IN ('used','expired','cancelled')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    issuance_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_issuances.id", ondelete="RESTRICT"), nullable=True
    )
    issued_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    code: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[VoucherStatus] = mapped_column(String(20), nullable=False)
    issue_source: Mapped[str] = mapped_column(String(30), nullable=False)

    # Snapshot discount rule tại thời điểm phát — immutable, engine redeem đọc
    # từ đây thay vì JOIN campaigns để tránh campaign sửa sau ảnh hưởng voucher cũ.
    discount_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign = relationship("Campaign", lazy="select")
