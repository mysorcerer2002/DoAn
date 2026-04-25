"""Reward model — quà đổi điểm trong chương trình loyalty (Hybrid template)."""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.voucher_template import VoucherTemplate


class RewardOfferType(str, enum.Enum):
    PERCENT_DISCOUNT = "PERCENT_DISCOUNT"
    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    ITEM_GIFT = "ITEM_GIFT"


class Reward(Base, TimestampMixin):
    """Quà đổi điểm — stock NULL = unlimited, soft delete qua deleted_at."""

    __tablename__ = "rewards"
    __table_args__ = (
        # Suffix-only — convention prepend `ck_rewards_`.
        CheckConstraint(
            "stock IS NULL OR stock >= 0", name="stock_nonneg_or_null"
        ),
        CheckConstraint("points_cost > 0", name="points_cost_positive"),
        CheckConstraint(
            "(offer_type = 'PERCENT_DISCOUNT' AND offer_value BETWEEN 1 AND 100) OR "
            "(offer_type = 'FIXED_DISCOUNT'   AND offer_value > 0) OR "
            "(offer_type = 'ITEM_GIFT'        AND offer_value IS NULL)",
            name="offer_value_matches_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("voucher_templates.id", ondelete="SET NULL"), nullable=True
    )
    offer_type: Mapped[RewardOfferType] = mapped_column(String(20), nullable=False)
    offer_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offer_label: Mapped[str] = mapped_column(String(120), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped["VoucherTemplate | None"] = relationship("VoucherTemplate")
