"""CampaignTemplate model — template admin-managed cho shop enroll campaign."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.campaign import CampaignSource, DiscountType


class ProgramForm(str, enum.Enum):
    """Hình thức khuyến mãi theo NĐ 81/2018 Điều 8, 13 — driver chính cho approval tier."""

    GIAM_GIA = "giam_gia"
    TANG_KEM = "tang_kem"
    MAY_RUI_QUAY_SO = "may_rui_quay_so"
    MAY_RUI_TRUC_TIEP = "may_rui_truc_tiep"
    KHACH_HANG_THUONG_XUYEN = "khach_hang_thuong_xuyen"


class CampaignTemplate(Base, TimestampMixin):
    """Template khung khuyến mãi do admin/công ty định nghĩa — shop enroll + fill instance."""

    __tablename__ = "campaign_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_campaign_templates_code"),
        CheckConstraint(
            "source IN ('manual','birthday','signup')",
            name="ck_campaign_templates_source",
        ),
        CheckConstraint(
            "program_form IN ('giam_gia','tang_kem','may_rui_quay_so',"
            "'may_rui_truc_tiep','khach_hang_thuong_xuyen')",
            name="ck_campaign_templates_program_form",
        ),
        CheckConstraint(
            "discount_type IN ('percent','fixed')",
            name="ck_campaign_templates_discount_type",
        ),
        CheckConstraint(
            "discount_type <> 'percent' OR ("
            "max_discount_percent_cap IS NOT NULL "
            "AND max_discount_percent_cap > 0 "
            "AND max_discount_percent_cap <= 50 "
            "AND max_discount_value_cap IS NOT NULL "
            "AND max_discount_value_cap > 0)",
            name="ck_campaign_templates_percent_caps_valid",
        ),
        CheckConstraint(
            "discount_type <> 'fixed' OR ("
            "max_discount_fixed_cap IS NOT NULL AND max_discount_fixed_cap > 0)",
            name="ck_campaign_templates_fixed_caps_valid",
        ),
        CheckConstraint(
            "max_issuances_cap IS NULL OR max_issuances_cap > 0",
            name="ck_campaign_templates_max_issuances_positive",
        ),
        CheckConstraint(
            "min_voucher_ttl_days > 0 AND max_voucher_ttl_days >= min_voucher_ttl_days",
            name="ck_campaign_templates_voucher_ttl_range",
        ),
        Index("ix_campaign_templates_source", "source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[CampaignSource] = mapped_column(String(20), nullable=False)
    program_form: Mapped[ProgramForm] = mapped_column(String(32), nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(String(20), nullable=False)

    default_usage_guide: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_support_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    default_terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    max_discount_percent_cap: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    max_discount_value_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_discount_fixed_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)

    min_order_floor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_issuances_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_duration_days: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    min_voucher_ttl_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=7)
    max_voucher_ttl_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=30)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
