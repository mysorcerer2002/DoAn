import phonenumbers
from phonenumbers import NumberParseException


class InvalidPhoneError(ValueError):
    pass


def normalize_phone(raw: str, default_region: str = "VN") -> str:
    """Chuẩn hóa SĐT VN về local 0-prefix format (vd 0912345678).

    Trả về `0xxxxxxxxx` (10 ký tự) — đồng nhất với:
    - `RegisterRequest._phone_check` (Pydantic validator) ở schemas/auth.py
    - Format khách hàng nhập trên FE
    - Format seed_demo

    Trước đây trả E.164 (`+84xxxxxxxxx`) gây mismatch với data đã seed/register
    → `find_or_create_member` không tìm được user existing → tạo trùng.

    Args:
        raw: SĐT bất kỳ format (`0xxx`, `+84xxx`, `84xxx`, có/không space)
        default_region: Quốc gia mặc định (VN)

    Returns:
        `0xxxxxxxxx` (10 ký tự, prefix `0`)

    Raises:
        InvalidPhoneError: SĐT không hợp lệ hoặc không thuộc VN
    """
    if not raw or not raw.strip():
        raise InvalidPhoneError("Phone cannot be empty")

    try:
        parsed = phonenumbers.parse(raw, default_region)
    except NumberParseException as e:
        raise InvalidPhoneError(f"Invalid phone format: {e}") from e

    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneError("Phone number is not valid")

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    if not e164.startswith("+84"):
        raise InvalidPhoneError(f"Only VN phones supported, got {e164}")
    return "0" + e164[3:]  # +84912345678 → 0912345678
