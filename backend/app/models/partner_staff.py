import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.partner import Partner
    from app.models.user import User


class PartnerStaffRole(str, enum.Enum):
    OWNER = "owner"
    STAFF = "staff"


class PartnerStaff(Base):
    __tablename__ = "partner_staff"
    __table_args__ = (
        UniqueConstraint("partner_id", "user_id", name="uq_partner_staff_partner_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[PartnerStaffRole] = mapped_column(
        String(20), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    partner: Mapped["Partner"] = relationship("Partner")
    user: Mapped["User"] = relationship("User")
