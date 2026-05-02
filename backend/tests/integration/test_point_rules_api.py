import pytest

from app.core.security import create_access_token
from app.models.partner import Partner, PartnerStatus
from app.models.user import User


async def _setup(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=owner.id, status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    await db_session.flush()
    return partner, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_create_and_get_active_rule(client, db_session):
    partner, token = await _setup(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    create = await client.post(
        "/partner/point-rules",
        json={"earn_percent": "1.00"},
        headers=headers,
    )
    assert create.status_code == 201

    get_active = await client.get("/partner/point-rules/active", headers=headers)
    assert get_active.status_code == 200
    assert get_active.json()["earn_percent"] == "1.00"


@pytest.mark.asyncio
async def test_create_rule_deactivates_old(client, db_session):
    partner, token = await _setup(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    await client.post(
        "/partner/point-rules",
        json={"earn_percent": "1.00"},
        headers=headers,
    )
    await client.post(
        "/partner/point-rules",
        json={"earn_percent": "2.00"},
        headers=headers,
    )

    list_resp = await client.get("/partner/point-rules", headers=headers)
    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert len(rules) == 2
    active = [r for r in rules if r["is_active"]]
    assert len(active) == 1
    assert active[0]["earn_percent"] == "2.00"


@pytest.mark.asyncio
async def test_point_rule_cross_tenant_isolation(client, db_session):
    tenant_a, token_a = await _setup(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Partner(
        name="B", slug="b", owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(tenant_b)
    await db_session.flush()
    await db_session.flush()
    token_b = create_access_token(user_id=owner_b.id)

    await client.post(
        "/partner/point-rules",
        json={"earn_percent": "5.00"},
        headers={"Authorization": f"Bearer {token_b}", "X-Partner-Id": str(tenant_b.id)},
    )

    response = await client.get(
        "/partner/point-rules/active",
        headers={"Authorization": f"Bearer {token_a}", "X-Partner-Id": str(tenant_a.id)},
    )
    assert response.status_code == 200
    assert response.json() is None
