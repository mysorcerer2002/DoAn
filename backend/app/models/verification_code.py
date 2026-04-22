import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class VerificationCodePurpose(str, enum.Enum):
    CLAIM_SHADOW = "claim_shadow"
    RESET_PASSWORD = "reset_password"
    AUTHORIZATION_SIGN = "authorization_sign"


class VerificationCode(Base, TimestampMixin):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[VerificationCodePurpose] = mapped_column(
        String(20), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # sha256 hex của payload liên quan — dùng ở flow authorization_sign để
    # bind OTP với form enroll (chặn tamper). Null cho purpose khác.
    context_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
