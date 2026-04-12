from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


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
        await self.db.flush()
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
