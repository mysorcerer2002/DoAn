"""Rate limiter setup.

⚠️ PRODUCTION WARNING: `_get_real_ip` đọc `X-Forwarded-For` trực tiếp từ header.
Nếu app expose trực tiếp (không qua trusted reverse proxy), attacker có thể tự
set `X-Forwarded-For: <random>` để bypass rate limit hoàn toàn.

Khi deploy production:
1. ALWAYS đặt sau reverse proxy (nginx/cloudflare).
2. Run uvicorn với `--forwarded-allow-ips=<proxy-ip>` để chỉ trust proxy IP.
3. Hoặc enforce ở proxy: drop incoming `X-Forwarded-For` header trước khi proxy.
"""

from starlette.requests import Request

from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_real_ip(request: Request) -> str:
    """Lấy IP thực từ X-Forwarded-For (nếu có) để rate-limit đúng behind proxy.

    ⚠️ Chỉ trust XFF khi production có reverse proxy strip/set lại header này.
    Xem module docstring.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_real_ip, default_limits=["100/minute"])
