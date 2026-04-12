from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.tenant_staff import TenantStaffRole


class StaffAddRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: TenantStaffRole = TenantStaffRole.STAFF


class StaffUpdateRoleRequest(BaseModel):
    role: TenantStaffRole


class StaffResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    role: TenantStaffRole
    user_email: str | None
    user_full_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StaffAddResponse(BaseModel):
    """Response khi thêm staff. Nếu user mới (shadow), kèm verification_code (MVP)."""

    staff: StaffResponse
    verification_code: str | None = None
