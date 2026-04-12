from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "system_role IN ('regular', 'admin', 'super_admin')",
            name="ck_users_valid_role",
        ),
        CheckConstraint(
            "is_shadow = true OR email IS NOT NULL OR phone IS NOT NULL",
            name="ck_users_login_identifier",
        ),
        Index("ix_users_email_unique", "email", unique=True, postgresql_where="email IS NOT NULL"),
        Index("ix_users_phone_unique", "phone", unique=True, postgresql_where="phone IS NOT NULL"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_shadow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    system_role: Mapped[str] = mapped_column(String(20), default="regular", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
