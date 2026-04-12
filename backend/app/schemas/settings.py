from typing import Any

from datetime import datetime

from pydantic import BaseModel, Field


class TenantSettings(BaseModel):
    """Schema fixed cho tenants.settings JSONB. Validate chặt chẽ."""

    points_on_gross: bool = False
    birthday_campaign_id: int | None = None
    signup_bonus_points: int = Field(default=0, ge=0)
    voucher_default_ttl_days: int = Field(default=30, ge=1, le=365)
    redemption_default_ttl_days: int = Field(default=14, ge=1, le=365)
    default_tier_id: int | None = None

    model_config = {"extra": "forbid"}


class SettingsUpdateRequest(BaseModel):
    """PATCH — chỉ các field muốn đổi."""

    points_on_gross: bool | None = None
    birthday_campaign_id: int | None = None
    signup_bonus_points: int | None = Field(default=None, ge=0)
    voucher_default_ttl_days: int | None = Field(default=None, ge=1, le=365)
    redemption_default_ttl_days: int | None = Field(default=None, ge=1, le=365)
    default_tier_id: int | None = None

    model_config = {"extra": "forbid"}


class SettingsAuditEntry(BaseModel):
    id: int
    field_key: str
    old_value: Any
    new_value: Any
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
