from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class StaffCreateRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def _require_email_or_phone(self):
        if not self.email and not (self.phone and self.phone.strip()):
            raise ValueError("Cần ít nhất 1 trong 2: email hoặc số điện thoại")
        return self


class StaffPatchRequest(BaseModel):
    is_active: bool


class StaffResponse(BaseModel):
    id: int                # partner_staff.id
    user_id: int
    email: str | None
    phone: str | None
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StaffListResponse(BaseModel):
    items: list[StaffResponse]
    total: int


class StaffResetResponse(BaseModel):
    email_sent: bool
    temp_password: str
    message: str
