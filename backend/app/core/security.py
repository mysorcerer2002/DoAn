from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class TokenPayload:
    """Kết quả decode JWT — typed thay vì raw dict."""

    sub: str
    type: str
    exp: int
    iat: int


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    """Decode JWT và trả về TokenPayload typed object."""
    settings = get_settings()
    raw = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return TokenPayload(
        sub=raw["sub"],
        type=raw.get("type", ""),
        exp=raw.get("exp", 0),
        iat=raw.get("iat", 0),
    )
