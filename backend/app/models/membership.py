from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.partner import Partner
    from app.models.tier import Tier
    from app.models.user import User


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("partner_id", "user_id", name="uq_memberships_partner_user"),
        CheckConstraint("points_balance >= 0", name="ck_memberships_balance_nonneg"),
        CheckConstraint("total_points_earned >= 0", name="ck_memberships_total_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_tier_id: Mapped[int | None] = mapped_column(
        ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    partner: Mapped["Partner"] = relationship("Partner")
    user: Mapped["User"] = relationship("User")
    current_tier: Mapped["Tier | None"] = relationship("Tier", foreign_keys=[current_tier_id])
