import hashlib
import logging
import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    get_dummy_password_hash,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import RegisterRequest

logger = logging.getLogger(__name__)


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def _hash_email_for_log(email: str) -> str:
    """SHA256 truncated — log email mà không leak PII."""
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> User:
        existing = await self.db.scalar(select(User).where(User.email == request.email))
        if existing is not None:
            raise EmailAlreadyExistsError(f"Email {request.email} already registered")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            birthday=request.birthday,
            is_active=True,
            system_role="regular",
        )
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError:
            raise EmailAlreadyExistsError(f"Email {request.email} already registered")
        await self.db.refresh(user)
        logger.info(
            "auth.register.success",
            extra={"user_id": user.id, "email_hash": _hash_email_for_log(request.email)},
        )
        return user

    async def authenticate(self, identifier: str, password: str) -> User:
        """Constant-time authenticate — luôn chạy bcrypt để chống timing attack.

        `identifier` có thể là email (chứa '@') hoặc SĐT VN (đã normalize về
        dạng 0xxxxxxxxx bởi schema). Nếu không match format nào → user sẽ None,
        dummy hash verify vẫn chạy để giữ thời gian nhất quán.
        """
        if "@" in identifier:
            user = await self.db.scalar(select(User).where(User.email == identifier))
        else:
            user = await self.db.scalar(select(User).where(User.phone == identifier))
        # Luôn verify (dummy hash nếu user/hash không tồn tại) để giữ thời gian nhất quán.
        hash_to_check = (
            user.password_hash if user and user.password_hash else get_dummy_password_hash()
        )
        password_valid = verify_password(password, hash_to_check)

        if user is None or user.password_hash is None or not password_valid:
            logger.warning(
                "auth.login.failed",
                extra={"identifier_hash": _hash_email_for_log(identifier)},
            )
            raise InvalidCredentialsError("Invalid email/phone or password")
        if not user.is_active:
            logger.warning(
                "auth.login.disabled",
                extra={"user_id": user.id},
            )
            raise InvalidCredentialsError("Account is disabled")

        user.last_login_at = datetime.now(UTC)
        # Không cần flush — get_db sẽ commit cuối request.
        logger.info("auth.login.success", extra={"user_id": user.id})
        return user

    async def reset_password_send_temp(self, *, email: str) -> str | None:
        """Forgot-password: gen temp password, set bcrypt, log/email plain.

        Trả temp password (caller log/email). Trả None nếu user không tồn tại
        — caller vẫn return generic 200 để tránh enumeration.
        """
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None:
            # Equalize timing — chạy bcrypt cost dù user không tồn tại,
            # tránh enumeration qua phản hồi nhanh/chậm.
            hash_password(secrets.token_urlsafe(8))
            return None
        temp_password = secrets.token_urlsafe(8)
        user.password_hash = hash_password(temp_password)
        await self.db.flush()
        logger.info(
            "auth.forgot_password.reset",
            extra={"user_id": user.id, "email_hash": _hash_email_for_log(email)},
        )
        return temp_password

    async def change_password(
        self, *, user: User, current_password: str, new_password: str
    ) -> None:
        if user.password_hash is None or not verify_password(
            current_password, user.password_hash
        ):
            raise InvalidCredentialsError("Mật khẩu hiện tại không đúng")
        user.password_hash = hash_password(new_password)
        await self.db.flush()
        logger.info("auth.change_password.success", extra={"user_id": user.id})
