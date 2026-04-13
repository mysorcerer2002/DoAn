import hashlib
import logging
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    get_dummy_password_hash,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.schemas.auth import RegisterRequest
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)

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

        now = datetime.now(UTC)
        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            birthday=request.birthday,
            is_active=True,
            is_shadow=False,
            system_role="regular",
            password_changed_at=now,
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

    async def authenticate(self, email: str, password: str) -> User:
        """Constant-time authenticate — luôn chạy bcrypt để chống timing attack."""
        user = await self.db.scalar(select(User).where(User.email == email))
        # Luôn verify (dummy hash nếu user/hash không tồn tại) để giữ thời gian nhất quán.
        hash_to_check = (
            user.password_hash if user and user.password_hash else get_dummy_password_hash()
        )
        password_valid = verify_password(password, hash_to_check)

        if user is None or user.password_hash is None or not password_valid:
            logger.warning(
                "auth.login.failed",
                extra={"email_hash": _hash_email_for_log(email)},
            )
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            logger.warning(
                "auth.login.disabled",
                extra={"user_id": user.id, "email_hash": _hash_email_for_log(email)},
            )
            raise InvalidCredentialsError("Account is disabled")

        user.last_login_at = datetime.now(UTC)
        # Không cần flush — get_db sẽ commit cuối request.
        logger.info("auth.login.success", extra={"user_id": user.id})
        return user

    async def request_claim(self, *, email: str) -> bool:
        """Gửi verification code cho shadow user. Trả False nếu không tồn tại hoặc không phải shadow."""
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None or not user.is_shadow:
            return False
        vcs = VerificationCodeService(self.db)
        await vcs.create_code(
            user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
        )
        logger.info(
            "auth.claim.code_sent",
            extra={"user_id": user.id, "email_hash": _hash_email_for_log(email)},
        )
        return True

    async def claim_shadow(
        self,
        *,
        email: str,
        code: str,
        password: str,
        full_name: str | None,
        birthday: date | None,
    ) -> User:
        """Xác nhận code và set password cho shadow user."""
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None or not user.is_shadow:
            raise InvalidCredentialsError("No claimable account for this email")

        vcs = VerificationCodeService(self.db)
        try:
            await vcs.verify_code(
                user_id=user.id,
                code=code,
                purpose=VerificationCodePurpose.CLAIM_SHADOW,
            )
        except InvalidCodeError as e:
            raise InvalidCredentialsError("Invalid or expired code") from e

        now = datetime.now(UTC)
        user.password_hash = hash_password(password)
        user.password_changed_at = now
        user.is_shadow = False
        if full_name is not None:
            user.full_name = full_name
        if birthday is not None:
            user.birthday = birthday
        await self.db.flush()
        logger.info(
            "auth.claim.success",
            extra={"user_id": user.id, "email_hash": _hash_email_for_log(email)},
        )
        return user
