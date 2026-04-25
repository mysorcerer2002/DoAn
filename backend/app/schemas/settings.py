from pydantic import BaseModel, Field


class PartnerSettings(BaseModel):
    """Schema fixed cho tenants.settings JSONB. Validate chặt chẽ."""

    points_on_gross: bool = False
    signup_bonus_points: int = Field(default=0, ge=0)
    redemption_default_ttl_days: int = Field(default=14, ge=1, le=365)
    default_tier_id: int | None = None

    model_config = {"extra": "forbid"}


class SettingsUpdateRequest(BaseModel):
    """PATCH — chỉ các field muốn đổi."""

    points_on_gross: bool | None = None
    signup_bonus_points: int | None = Field(default=None, ge=0)
    redemption_default_ttl_days: int | None = Field(default=None, ge=1, le=365)
    default_tier_id: int | None = None

    model_config = {"extra": "forbid"}
