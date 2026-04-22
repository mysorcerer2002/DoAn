"""CampaignFeeSchedule — bảng giá phí dịch vụ.

M10 của plan voucher rebuild v2.2 (section 4.3). v1 seed-only, admin CRUD
defer phase sau. Mỗi `fee_type` 1 record base_amount hiện hành (
`is_active=TRUE`). `trigger_rule` JSONB reserved cho logic pricing phức tạp
ở phase sau (vd: áp phí multi_province khi campaign có >1 tỉnh).

Seed 5 row (plan line 371):
- so_ct_filing = 500.000 VND
- dossier_preparation = 1.000.000 VND
- multi_province = +2.000.000 VND
- express = +500.000 VND
- waiver = 0 (cho demo account)
"""

from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CampaignFeeSchedule(Base, TimestampMixin):
    __tablename__ = "campaign_fee_schedules"
    __table_args__ = (
        CheckConstraint(
            "fee_type IN ('so_ct_filing','dossier_preparation','multi_province',"
            "'express','waiver')",
            name="ck_campaign_fee_schedules_fee_type",
        ),
        CheckConstraint(
            "base_amount >= 0",
            name="ck_campaign_fee_schedules_base_amount_nonneg",
        ),
        CheckConstraint(
            "version > 0",
            name="ck_campaign_fee_schedules_version_positive",
        ),
        Index(
            "ux_campaign_fee_schedules_active_per_type",
            "fee_type",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
        UniqueConstraint(
            "fee_type", "version", name="uq_campaign_fee_schedules_type_version"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fee_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_rule: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    base_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("TRUE")
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
