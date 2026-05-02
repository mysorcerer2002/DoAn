from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PointRule(Base, TimestampMixin):
    __tablename__ = "point_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    earn_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("1.00")
    )
    use_tiers: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index(
            "uq_point_rules_partner_active",
            "partner_id",
            unique=True,
            postgresql_where="is_active = true",
        ),
    )
