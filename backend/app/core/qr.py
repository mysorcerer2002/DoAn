"""QR JWT service — sign/verify QR cá nhân khách + fallback_code HMAC.

QR cá nhân khách = JWT ký bằng QR_SECRET (defense-in-depth: tách khỏi JWT_SECRET).
Payload {user_id, exp: now+120s}.
Fallback code = HMAC-SHA256(QR_SECRET, f"{user_id}|{bucket}") truncate 8 ký tự.

Bucket fallback dùng 5 phút (giảm window replay từ 1-2h xuống 5-10 phút).
"""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings


class InvalidQRError(Exception):
    """Lỗi khi QR token không hợp lệ hoặc hết hạn."""

    pass


_QR_TTL_SECONDS = 120
_QR_JWT_LEEWAY = 5  # Chấp nhận chênh lệch đồng hồ ±5s
_FALLBACK_CODE_LENGTH = 8
_FALLBACK_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # Loại 0/O/1/I/L
_FALLBACK_BUCKET_SECONDS = 300  # 5 phút (giảm replay window từ 1h xuống 5 phút)


def sign_qr_jwt(
    user_id: int, expires_delta: timedelta | None = None
) -> dict:
    """Sign JWT cho QR cá nhân khách.

    Returns:
        {
            "jwt": "<jwt_string>",
            "exp_at_server": <unix_timestamp>,
            "fallback_code": "<8 chars>",
        }

    Frontend dùng `exp_at_server` để countdown (KHÔNG dùng Date.now() client).
    """
    settings = get_settings()
    expires_delta = expires_delta or timedelta(seconds=_QR_TTL_SECONDS)
    expire_at = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(user_id),
        "type": "qr",
        "iat": datetime.now(timezone.utc),
        "exp": expire_at,
    }
    token = jwt.encode(
        payload, settings.qr_secret, algorithm=settings.jwt_algorithm
    )

    return {
        "jwt": token,
        "exp_at_server": int(expire_at.timestamp()),
        "fallback_code": generate_fallback_code(user_id=user_id),
    }


def decode_qr_jwt(token: str) -> int:
    """Decode QR JWT, return user_id. Raise InvalidQRError nếu invalid/expired."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.qr_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True, "leeway": _QR_JWT_LEEWAY},
        )
    except JWTError as e:
        raise InvalidQRError(f"Invalid QR token: {e}") from e

    if payload.get("type") != "qr":
        raise InvalidQRError("Token is not a QR token")

    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as e:
        raise InvalidQRError("Invalid sub claim") from e


def _hour_bucket(now: datetime | None = None) -> int:
    """Trả về bucket số (mỗi 5 phút) kể từ epoch — dùng cho fallback_code.

    Hàm giữ tên `_hour_bucket` để tương thích với code cũ, nhưng giờ đếm
    theo bucket 5 phút (`_FALLBACK_BUCKET_SECONDS`).
    """
    now = now or datetime.now(timezone.utc)
    return int(now.timestamp() // _FALLBACK_BUCKET_SECONDS)


def generate_fallback_code(user_id: int, hour_bucket: int | None = None) -> str:
    """Sinh fallback code 8 ký tự = HMAC(qr_secret, user_id|bucket).

    Đổi mỗi 5 phút (giảm replay window vs design 1h cũ).
    Khi mạng yếu/QR camera lỗi, nhân viên có thể nhập tay code này.
    """
    settings = get_settings()
    if hour_bucket is None:
        hour_bucket = _hour_bucket()

    msg = f"{user_id}|{hour_bucket}".encode()
    digest = hmac.new(settings.qr_secret.encode(), msg, hashlib.sha256).digest()
    chars = []
    for b in digest[:_FALLBACK_CODE_LENGTH]:
        chars.append(_FALLBACK_ALPHABET[b % len(_FALLBACK_ALPHABET)])
    return "".join(chars)


def verify_fallback_code_with_candidates(
    code: str, candidate_user_ids: list[int]
) -> int:
    """Verify fallback code bằng cách check với danh sách user_id ứng cử.

    Chấp nhận bucket hiện tại + 1 bucket trước (10 phút window) để tránh
    user nhập code cũ ngay khi sang bucket mới.

    Args:
        code: Code 8 ký tự khách đưa
        candidate_user_ids: List user_id để check

    Returns:
        user_id nếu match

    Raises:
        InvalidQRError nếu không match
    """
    if not code or len(code) != _FALLBACK_CODE_LENGTH:
        raise InvalidQRError("Invalid fallback code format")

    code_upper = code.upper()
    current_bucket = _hour_bucket()

    for user_id in candidate_user_ids:
        for bucket in [current_bucket, current_bucket - 1]:
            expected = generate_fallback_code(user_id, hour_bucket=bucket)
            if hmac.compare_digest(code_upper, expected):
                return user_id

    raise InvalidQRError("Fallback code does not match any known user")


def sign_shop_token(tenant_id: int) -> str:
    """Sinh shop_token = HMAC(secret, f"shop|{tenant_id}") truncate 16 chars.

    Static token (không có TTL) — chỉ verify QR shop thật trong hệ thống.
    """
    settings = get_settings()
    msg = f"shop|{tenant_id}".encode()
    digest = hmac.new(settings.qr_secret.encode(), msg, hashlib.sha256).digest()
    return digest.hex()[:16]


def verify_shop_token(tenant_id: int, token: str) -> bool:
    """Verify shop HMAC token."""
    expected = sign_shop_token(tenant_id)
    return hmac.compare_digest(expected, token)
