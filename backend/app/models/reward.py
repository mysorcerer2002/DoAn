"""Reward model — quà đổi điểm trong chương trình loyalty."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Reward(Base, TimestampMixin):
    """Quà đổi điểm — stock NULL = unlimited, soft delete qua deleted_at."""

    __tablename__ = "rewards"
    __table_args__ = (
        CheckConstraint(
            "stock IS NULL OR stock >= 0", name="ck_rewards_stock_nonneg_or_null"
        ),
        CheckConstraint("points_cost > 0", name="ck_rewards_points_cost_positive"),
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
