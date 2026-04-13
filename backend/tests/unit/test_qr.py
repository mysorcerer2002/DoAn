"""Unit tests: QR JWT sign/verify + fallback code."""

import time
from unittest.mock import patch

import pytest

from app.core.qr import (
    InvalidQRError,
    _FALLBACK_ALPHABET,
    decode_qr_jwt,
    generate_fallback_code,
    sign_qr_jwt,
    sign_shop_token,
    verify_fallback_code_with_candidates,
    verify_shop_token,
)


class TestQrJwt:
    """QR JWT sign/verify."""

    def test_sign_and_decode_success(self):
        result = sign_qr_jwt(user_id=42)
        assert "jwt" in result
        assert "exp_at_server" in result
        assert "fallback_code" in result

        decoded_user_id = decode_qr_jwt(result["jwt"])
        assert decoded_user_id == 42

    def test_expired_token_raises(self):
        from datetime import timedelta

        result = sign_qr_jwt(user_id=42, expires_delta=timedelta(seconds=-10))
        with pytest.raises(InvalidQRError, match="expired"):
            decode_qr_jwt(result["jwt"])

    def test_invalid_token_raises(self):
        with pytest.raises(InvalidQRError):
            decode_qr_jwt("invalid.jwt.token")

    def test_fallback_code_format(self):
        result = sign_qr_jwt(user_id=100)
        code = result["fallback_code"]
        assert len(code) == 8
        assert all(c in _FALLBACK_ALPHABET for c in code)


class TestFallbackCode:
    """HMAC fallback code."""

    def test_same_input_same_code(self):
        # Bucket được tự generate inside generate_fallback_code → 2 calls cùng giây cùng kết quả
        code1 = generate_fallback_code(user_id=1)
        code2 = generate_fallback_code(user_id=1)
        assert code1 == code2

    def test_different_user_different_code(self):
        code1 = generate_fallback_code(user_id=1)
        code2 = generate_fallback_code(user_id=2)
        assert code1 != code2

    def test_verify_with_candidates(self):
        code = generate_fallback_code(user_id=42)
        result = verify_fallback_code_with_candidates(code, [10, 20, 42, 50])
        assert result == 42

    def test_verify_no_match_raises(self):
        with pytest.raises(InvalidQRError):
            verify_fallback_code_with_candidates("XXXXXXXX", [1, 2, 3])


class TestShopToken:
    """HMAC shop token."""

    def test_sign_and_verify(self):
        token = sign_shop_token(tenant_id=5)
        assert len(token) == 16
        assert verify_shop_token(tenant_id=5, token=token) is True

    def test_wrong_tenant_fails(self):
        token = sign_shop_token(tenant_id=5)
        assert verify_shop_token(tenant_id=99, token=token) is False

    def test_wrong_token_fails(self):
        assert verify_shop_token(tenant_id=5, token="0" * 16) is False
