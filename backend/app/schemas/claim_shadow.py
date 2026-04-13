from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.auth import _normalize_email, _validate_password_bytes


class RequestClaimRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return _normalize_email(v)


class ClaimShadowRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    birthday: date | None = None

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return _normalize_email(v)

    @field_validator("password")
    @classmethod
    def _password_bytes(cls, v: str) -> str:
        return _validate_password_bytes(v)
