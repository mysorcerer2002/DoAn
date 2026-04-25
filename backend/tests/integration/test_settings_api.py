import pytest

from app.core.security import create_access_token
from app.models.partner import Partner, PartnerStatus
from app.models.user import User


async def _setup_owner(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name="Shop", slug="shop", owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    return partner, owner, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_get_default_settings(client, db_session):
    partner, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    response = await client.get("/partners/me/settings", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["points_on_gross"] is False
    assert data["redemption_default_ttl_days"] == 14


@pytest.mark.asyncio
async def test_update_settings(client, db_session):
    partner, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    response = await client.patch(
        "/partners/me/settings",
        json={"points_on_gross": True, "redemption_default_ttl_days": 60},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["points_on_gross"] is True
    assert data["redemption_default_ttl_days"] == 60


@pytest.mark.asyncio
async def test_settings_cross_partner_isolation(client, db_session):
    """Owner A không thể access settings của partner B."""
    _partner_a, _, token_a = await _setup_owner(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    partner_b = Partner(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner_b)
    await db_session.flush()

    response = await client.patch(
        "/partners/me/settings",
        json={"points_on_gross": True},
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Partner-Id": str(partner_b.id),
        },
    )
    assert response.status_code == 403
