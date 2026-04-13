from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_password_bytes(value: str) -> str:
    """bcrypt giới hạn 72 BYTES (không phải 72 ký tự).

    UTF-8 char đặc biệt (vd emoji) chiếm 4 byte → string 50 ký tự có thể >72 byte
    → bcrypt silently truncate hoặc raise. Validate explicit để fail-fast.
    """
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password too long (>72 bytes after UTF-8 encoding)")
    return value


def _normalize_email(value: str) -> str:
    """Lowercase email — chống duplicate kiểu Alice@X.com vs alice@x.com bypass unique constraint."""
    return value.lower()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    birthday: date | None = None

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return _normalize_email(v)

    @field_validator("password")
    @classmethod
    def _password_bytes(cls, v: str) -> str:
        return _validate_password_bytes(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return _normalize_email(v)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str | None
    phone: str | None = None
    full_name: str | None
    birthday: date | None
    system_role: Literal["regular", "admin", "super_admin"]
    created_at: datetime

    model_config = {"from_attributes": True}
