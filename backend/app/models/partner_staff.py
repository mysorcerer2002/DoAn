from sqlalchemy import Boolean, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PartnerStaff(Base, TimestampMixin):
    """Staff thuộc 1 partner. Owner KHÔNG nằm trong bảng này (dùng partners.owner_user_id)."""

    __tablename__ = "partner_staff"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_partner_staff_user"),
        Index("ix_partner_staff_partner", "partner_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
