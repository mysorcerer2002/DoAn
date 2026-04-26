"""Unit tests: QR shop token HMAC."""

from app.core.qr import (
    sign_shop_token,
    verify_shop_token,
)


class TestShopToken:
    """HMAC shop token."""

    def test_sign_and_verify(self):
        token = sign_shop_token(partner_id=5)
        assert len(token) == 16
        assert verify_shop_token(partner_id=5, token=token) is True

    def test_wrong_partner_fails(self):
        token = sign_shop_token(partner_id=5)
        assert verify_shop_token(partner_id=99, token=token) is False

    def test_wrong_token_fails(self):
        assert verify_shop_token(partner_id=5, token="0" * 16) is False
