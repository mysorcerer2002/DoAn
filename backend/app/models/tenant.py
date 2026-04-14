import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class TenantStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class TenantCategory(str, enum.Enum):
    """Phân loại tenant để customer dễ khám phá + UI accent khác nhau."""

    CAFE = "cafe"  # Cafe/coffee shop
    FOOD = "food"  # Nhà hàng, fast-food, street food
    RETAIL = "retail"  # Cửa hàng bán lẻ, thời trang
    BEAUTY = "beauty"  # Mỹ phẩm, spa, salon
    OTHER = "other"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[TenantStatus] = mapped_column(
        String(20),
        default=TenantStatus.PENDING,
        nullable=False,
    )
    category: Mapped[TenantCategory] = mapped_column(
        String(20),
        default=TenantCategory.OTHER,
        nullable=False,
        server_default="other",
        index=True,
    )
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_user_id])
