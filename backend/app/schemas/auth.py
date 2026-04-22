import re
from datetime import date, datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator


# VN mobile phone: 10 số, bắt đầu bằng 0 (09x, 08x, 07x, 05x, 03x).
# Không chấp nhận +84 để giữ validation đơn — user normalize "+84" về "0" khi cần.
_VN_PHONE_RE = re.compile(r"^0\d{9}$")


def _is_vn_phone(value: str) -> bool:
    return bool(_VN_PHONE_RE.match(value))


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
    """Đăng nhập bằng email hoặc số điện thoại VN.

    Chấp nhận `identifier` (tên mới, rõ nghĩa) hoặc `email` (alias cũ — giữ
    tương thích với client/test có sẵn). Service tự detect format → query cột
    tương ứng.
    """

    identifier: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("identifier", "email"),
    )
    password: str

    @field_validator("identifier")
    @classmethod
    def _normalize_identifier(cls, v: str) -> str:
        v = v.strip()
        if "@" in v:
            return _normalize_email(v)
        # Phone: bỏ khoảng trắng/dấu gạch/dấu cộng 84 → chuẩn 0xxxxxxxxx
        cleaned = re.sub(r"[\s\-\.]", "", v)
        if cleaned.startswith("+84"):
            cleaned = "0" + cleaned[3:]
        elif cleaned.startswith("84") and len(cleaned) == 11:
            cleaned = "0" + cleaned[2:]
        if _is_vn_phone(cleaned):
            return cleaned
        # Không match email/phone → để service raise 401 (không leak format info)
        return v


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
