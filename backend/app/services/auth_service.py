from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.schemas.auth import RegisterRequest
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


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
            is_shadow=False,
            system_role="regular",
        )
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError:
            raise EmailAlreadyExistsError(f"Email {request.email} already registered")
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.email == email))
        if user is None or user.password_hash is None:
            raise InvalidCredentialsError("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InvalidCredentialsError("Account is disabled")

        user.last_login_at = datetime.now(UTC)
        await self.db.flush()
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

        user.password_hash = hash_password(password)
        user.is_shadow = False
        if full_name is not None:
            user.full_name = full_name
        if birthday is not None:
            user.birthday = birthday
        await self.db.flush()
        return user
