"""CampaignIssuance model — lô phát voucher của 1 campaign."""

import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class IssueMode(str, enum.Enum):
    """Hình thức phát của lô."""

    MANUAL = "manual"
    BULK_DISTRIBUTION = "bulk_distribution"
    SIGNUP_JOB = "signup_job"
    BIRTHDAY_JOB = "birthday_job"


class CampaignIssuance(Base, TimestampMixin):
    """Lô phát voucher — tách từ campaign để audit + override TTL per-batch."""

    __tablename__ = "campaign_issuances"
    __table_args__ = (
        CheckConstraint(
            "issued_count >= 0",
            name="ck_campaign_issuances_issued_count_nonneg",
        ),
        CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_campaign_issuances_quantity_positive",
        ),
        CheckConstraint(
            "quantity IS NULL OR issued_count <= quantity",
            name="ck_campaign_issuances_issued_within_quantity",
        ),
        CheckConstraint(
            "starts_at IS NULL OR ends_at IS NULL OR ends_at > starts_at",
            name="ck_campaign_issuances_ends_after_starts",
        ),
        CheckConstraint(
            "voucher_ttl_days IS NULL OR voucher_ttl_days > 0",
            name="ck_campaign_issuances_voucher_ttl_positive",
        ),
        CheckConstraint(
            "issue_mode IN ('manual','bulk_distribution','signup_job','birthday_job')",
            name="ck_campaign_issuances_issue_mode",
        ),
        Index("ix_campaign_issuances_campaign", "campaign_id"),
        Index(
            "ix_campaign_issuances_tenant_active",
            "tenant_id",
            "created_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )

    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issued_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue_mode: Mapped[str] = mapped_column(String(30), nullable=False)

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    voucher_ttl_days: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
