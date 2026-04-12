from datetime import date

from pydantic import BaseModel, EmailStr, Field


class RequestClaimRequest(BaseModel):
    email: EmailStr


class ClaimShadowRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    birthday: date | None = None
