from datetime import datetime

from pydantic import BaseModel, Field

from app.models.tenant import TenantStatus


class TenantCreateRequest(BaseModel):
    """Owner đăng ký doanh nghiệp."""

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)


class TenantUpdateRequest(BaseModel):
    """Owner cập nhật thông tin tenant (PATCH)."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)


class TenantResponse(BaseModel):
    """Trả cho owner/staff (đầy đủ thông tin)."""

    id: int
    name: str
    slug: str
    owner_user_id: int
    status: TenantStatus
    logo_url: str | None
    description: str | None
    settings: dict
    created_at: datetime
    activated_at: datetime | None

    model_config = {"from_attributes": True}


class TenantPublicResponse(BaseModel):
    """Trả cho khách hàng cuối browse danh sách shop public."""

    id: int
    name: str
    slug: str
    logo_url: str | None
    description: str | None

    model_config = {"from_attributes": True}


class TenantApprovalRequest(BaseModel):
    """Super Admin approve/reject."""

    approve: bool
    reason: str | None = Field(default=None, max_length=500)
