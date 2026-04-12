from starlette.requests import Request

from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_real_ip(request: Request) -> str:
    """Lấy IP thực từ X-Forwarded-For (nếu có) để rate-limit đúng behind proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_real_ip, default_limits=["100/minute"])
