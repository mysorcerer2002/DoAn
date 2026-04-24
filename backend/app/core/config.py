from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "loyalty-platform"
    environment: str = "development"
    debug: bool = False

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    qr_hmac_secret: str = ""

    @property
    def qr_secret(self) -> str:
        """Secret riêng cho QR/HMAC. Bắt buộc cấu hình riêng trong production."""
        return self.qr_hmac_secret or self.jwt_secret

    enable_scheduler: bool = False
    frontend_origins: str = "http://localhost:3000"

    # NĐ 81/2018 Điều 17/19 — threshold tier phê duyệt (VND).
    # estimated_cost <= auto → auto_approved;
    # < notify → notify_so_ct; >= notify → dang_ky_so_ct.
    campaign_auto_threshold: int = 500_000
    campaign_notify_threshold: int = 2_000_000

    # Voucher rebuild v2.2 — post-report và retention.
    # 45 ngày nộp báo cáo kết thúc (Điều 20 NĐ 81). 10 năm lưu uỷ quyền
    # (Luật Kế toán 2015 Điều 41).
    campaign_default_post_report_days: int = 45
    auth_retention_years: int = 10
    consent_text_version: str = "v1.0-2026-04"

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        """Kiểm tra secrets đủ mạnh trong production."""
        if self.environment not in ("development", "test", "testing"):
            if len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET phải >= 32 ký tự trong production"
                )
            if not self.qr_hmac_secret:
                raise ValueError(
                    "QR_HMAC_SECRET phải được cấu hình riêng trong production"
                )
            if self.qr_hmac_secret == self.jwt_secret:
                raise ValueError(
                    "QR_HMAC_SECRET phải khác JWT_SECRET"
                )
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
