"""QR HMAC service — shop token cho QR shop check-in.

Personal QR của khách = raw user_id (string số), render local tại FE.
Shop QR = HMAC(qr_secret, f"shop|{partner_id}") truncate 16 chars.
"""

import hashlib
import hmac

from app.core.config import get_settings


def sign_shop_token(partner_id: int) -> str:
    """Sinh shop_token = HMAC(secret, f"shop|{partner_id}") truncate 16 chars.

    Static token (không có TTL) — chỉ verify QR shop thật trong hệ thống.
    """
    settings = get_settings()
    msg = f"shop|{partner_id}".encode()
    digest = hmac.new(settings.qr_secret.encode(), msg, hashlib.sha256).digest()
    return digest.hex()[:16]


def verify_shop_token(partner_id: int, token: str) -> bool:
    """Verify shop HMAC token."""
    expected = sign_shop_token(partner_id)
    return hmac.compare_digest(expected, token)
