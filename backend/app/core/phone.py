import phonenumbers
from phonenumbers import NumberParseException


class InvalidPhoneError(ValueError):
    pass


def normalize_phone(raw: str, default_region: str = "VN") -> str:
    """Chuẩn hóa số điện thoại sang E.164 format (vd +84912345678).

    Args:
        raw: Số điện thoại bất kỳ format
        default_region: Quốc gia mặc định nếu không có country code (default VN)

    Returns:
        E.164 string

    Raises:
        InvalidPhoneError: Nếu số không hợp lệ
    """
    if not raw or not raw.strip():
        raise InvalidPhoneError("Phone cannot be empty")

    try:
        parsed = phonenumbers.parse(raw, default_region)
    except NumberParseException as e:
        raise InvalidPhoneError(f"Invalid phone format: {e}") from e

    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneError("Phone number is not valid")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
