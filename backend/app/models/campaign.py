"""Campaign model — chiến dịch khuyến mãi voucher."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class CampaignSource(str, enum.Enum):
    MANUAL = "manual"
    BIRTHDAY = "birthday"
    SIGNUP = "signup"


class Campaign(Base, TimestampMixin):
    """Chiến dịch khuyến mãi — max_issuances NULL = unlimited, soft delete qua deleted_at."""

    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(
            "discount_value > 0", name="ck_campaigns_discount_positive"
        ),
        CheckConstraint(
            "max_issuances IS NULL OR max_issuances > 0",
            name="ck_campaigns_max_issuances_positive",
        ),
        CheckConstraint("issued_count >= 0", name="ck_campaigns_issued_nonneg"),
        Index("ix_campaigns_tenant_active", "tenant_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type"), nullable=False
    )
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    min_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_discount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_tier_id: Mapped[int | None] = mapped_column(
        ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True
    )
    max_issuances: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issued_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[CampaignSource] = mapped_column(
        Enum(CampaignSource, name="campaign_source"),
        default=CampaignSource.MANUAL,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
