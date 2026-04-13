from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
from jose import JWTError, jwt

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


@lru_cache(maxsize=1)
def get_dummy_password_hash() -> str:
    """Hash dummy dùng cho constant-time auth (chống user enumeration timing attack)."""
    return hash_password("dummy-password-for-constant-time-auth")


def _encode_jwt(*, user_id: int, token_type: str, expire: datetime, now: datetime) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    return _encode_jwt(user_id=user_id, token_type="access", expire=expire, now=now)


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    return _encode_jwt(user_id=user_id, token_type="refresh", expire=expire, now=now)


def decode_token(token: str) -> TokenPayload:
    """Decode JWT và trả về TokenPayload typed object.

    Raises JWTError nếu token invalid, expired, hoặc thiếu sub claim.
    """
    settings = get_settings()
    raw = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    sub = raw.get("sub")
    if sub is None:
        raise JWTError("Missing sub claim")
    return TokenPayload(
        sub=str(sub),
        type=raw.get("type", ""),
        exp=raw.get("exp", 0),
        iat=raw.get("iat", 0),
    )
