"""Email sender stub.

v1 đồ án không có SMTP thật — chỉ log OTP ra console để dev/demo test. Khi
chuyển khoá luận/prod, swap `send_otp_email` sang provider thực (SendGrid
/ SES / SMTP) mà không đổi caller signature.

`dev_code_leaking` = True khi `environment == 'development'` — API có thể
trả code trực tiếp cho client test nhanh. Prod phải set False cứng.
"""

import logging

from app.core.config import get_settings


logger = logging.getLogger(__name__)


async def send_otp_email(*, to_email: str, code: str, purpose: str) -> None:
    """Gửi OTP qua email. v1: log console."""
    logger.info(
        "[email stub] OTP sent to=%s purpose=%s code=%s",
        to_email,
        purpose,
        code,
    )


def dev_code_leak_enabled() -> bool:
    """Có cho phép trả OTP code trong response để dev test?"""
    s = get_settings()
    return s.environment in {"development", "test", "testing"}


def mask_email(email: str) -> str:
    """`user@example.com` → `u***@example.com`."""
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"
