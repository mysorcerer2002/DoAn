from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Tier(Base, TimestampMixin):
    __tablename__ = "tiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    perks: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    earn_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(precision=3, scale=2),
        server_default=text("1.00"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_tiers_partner_min_points", "partner_id", "min_points"),
        CheckConstraint(
            "earn_multiplier >= 0.50 AND earn_multiplier <= 5.00",
            name="ck_tiers_earn_multiplier_range",
        ),
    )
