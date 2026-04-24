from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.partner import PartnerCategory, PartnerStatus


class PartnerCreateRequest(BaseModel):
    """Owner đăng ký đối tác."""

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)
    category: PartnerCategory = Field(default=PartnerCategory.OTHER)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    tax_code: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=500)
    business_hours: str | None = Field(default=None, max_length=255)


class PartnerUpdateRequest(BaseModel):
    """Owner cập nhật thông tin đối tác (PATCH)."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)
    category: PartnerCategory | None = None
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    tax_code: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=500)
    business_hours: str | None = Field(default=None, max_length=255)


class PartnerResponse(BaseModel):
    """Trả cho owner/staff (đầy đủ thông tin)."""

    id: int
    name: str
    slug: str
    owner_user_id: int
    status: PartnerStatus
    category: PartnerCategory
    logo_url: str | None
    description: str | None
    contact_phone: str | None
    contact_email: str | None
    address: str | None
    tax_code: str | None
    website: str | None
    business_hours: str | None
    settings: dict
    created_at: datetime
    activated_at: datetime | None

    model_config = {"from_attributes": True}


class PartnerPublicResponse(BaseModel):
    """Trả cho khách hàng cuối browse danh sách shop public."""

    id: int
    name: str
    slug: str
    category: PartnerCategory
    logo_url: str | None
    description: str | None
    contact_phone: str | None
    contact_email: str | None
    address: str | None
    website: str | None
    business_hours: str | None

    model_config = {"from_attributes": True}


class PartnerApprovalRequest(BaseModel):
    """Super Admin approve/reject."""

    approve: bool
    reason: str | None = Field(default=None, max_length=500)


class PartnerStaffSummary(BaseModel):
    """Partner snapshot mà current user là staff. Frontend dùng để pick shop."""

    id: int
    name: str
    slug: str
    logo_url: str | None = None
    status: PartnerStatus
    role: str  # owner | staff (PartnerStaffRole.value)


class MyPartnerSummary(BaseModel):
    """Tóm tắt partner ACTIVE cho customer browse — không kèm membership info."""

    id: int
    name: str
    slug: str
    category: str
    description: str | None = None
    logo_url: str | None = None


class PartnerDetailForMember(BaseModel):
    """Chi tiết partner cho customer — kèm membership-conditional fields."""

    id: int
    name: str
    slug: str
    category: str
    description: str | None = None
    logo_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address: str | None = None
    website: str | None = None
    business_hours: str | None = None
    is_member: bool
    # Chỉ có giá trị khi is_member=True
    points_balance: int | None = None
    total_points_earned: int | None = None
    current_tier_name: str | None = None
    joined_at: datetime | None = None
    last_activity_at: datetime | None = None
