import pytest
from app.core.phone import InvalidPhoneError, normalize_phone


def test_normalize_vn_local_to_e164():
    assert normalize_phone("0912345678") == "+84912345678"


def test_normalize_vn_with_country_code():
    assert normalize_phone("84912345678") == "+84912345678"


def test_normalize_already_e164():
    assert normalize_phone("+84912345678") == "+84912345678"


def test_normalize_strips_spaces_and_dashes():
    assert normalize_phone("091 234 5678") == "+84912345678"
    assert normalize_phone("091-234-5678") == "+84912345678"


def test_normalize_invalid_raises():
    with pytest.raises(InvalidPhoneError):
        normalize_phone("not-a-phone")


def test_normalize_too_short_raises():
    with pytest.raises(InvalidPhoneError):
        normalize_phone("123")


def test_normalize_empty_raises():
    with pytest.raises(InvalidPhoneError):
        normalize_phone("")
