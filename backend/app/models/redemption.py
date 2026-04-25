"""Redemption model — đổi quà loyalty (HYBRID: scope user_id global)."""

import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RedemptionStatus(str, enum.Enum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"


class Redemption(Base, TimestampMixin):
    """Đổi quà — atomic stock decrement + ledger."""

    __tablename__ = "redemptions"
    __table_args__ = (
        # Suffix-only — convention prepend `ck_redemptions_` → final
        # `ck_redemptions_points_positive`.
        CheckConstraint("points_spent > 0", name="points_positive"),
        UniqueConstraint(
            "partner_id", "redemption_code", name="uq_redemptions_partner_code"
        ),
        Index("ix_redemptions_partner_status", "partner_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reward_id: Mapped[int] = mapped_column(
        ForeignKey("rewards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    redemption_code: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[RedemptionStatus] = mapped_column(
        String(20), nullable=False
    )
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    used_by_staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    snapshot_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
