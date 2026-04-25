"""Integration tests: QR API."""

import pytest

from app.core.security import create_access_token
from app.core.qr import sign_shop_token
from app.models.partner import Partner, PartnerStatus
from app.models.user import User


async def _make_user_and_tenant(db_session):
    owner = User(email="qrapi@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="QRShop",
        slug="qr-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {"Authorization": f"Bearer {token}"}
    return partner, owner, headers


@pytest.mark.asyncio
async def test_get_qr_token(client, db_session):
    """Lấy QR JWT cho user đã đăng nhập."""
    _tenant, _owner, headers = await _make_user_and_tenant(db_session)

    resp = await client.get("/member/qr", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "jwt" in data
    assert "fallback_code" in data
    assert "exp_at_server" in data


@pytest.mark.asyncio
async def test_get_qr_unauthorized(client, db_session):
    """Không có token → 401."""
    resp = await client.get("/member/qr")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_checkin_qr_shop(client, db_session):
    """Quét QR shop (HMAC token) thành công."""
    partner, _owner, _headers = await _make_user_and_tenant(db_session)

    shop_token = sign_shop_token(partner.id)

    resp = await client.get(
        "/member/checkin",
        params={"partner": partner.slug, "shop_token": shop_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["partner_id"] == partner.id
    assert data["partner_slug"] == partner.slug


@pytest.mark.asyncio
async def test_checkin_invalid_token(client, db_session):
    """Token sai → 401."""
    partner, _owner, _headers = await _make_user_and_tenant(db_session)

    resp = await client.get(
        "/member/checkin",
        params={"partner": partner.slug, "shop_token": "0" * 16},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_checkin_invalid_tenant(client, db_session):
    """Partner không tồn tại → 404."""
    resp = await client.get(
        "/member/checkin",
        params={"partner": "nonexistent-slug", "shop_token": "0" * 16},
    )
    assert resp.status_code == 404
