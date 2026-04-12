"""Integration tests: Campaigns API CRUD + ROI."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup_shop(db_session):
    owner = User(email="campapi@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="CampAPIShop",
        slug="camp-api-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    db_session.add(
        TenantStaff(
            tenant_id=tenant.id,
            user_id=owner.id,
            role=TenantStaffRole.OWNER,
        )
    )
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": str(tenant.id),
    }
    return tenant, owner, headers


def _campaign_payload(**overrides):
    now = datetime.now(timezone.utc)
    base = {
        "name": "Test Campaign",
        "discount_type": "percent",
        "discount_value": 10,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=30)).isoformat(),
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_create_campaign_api(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    resp = await client.post(
        "/merchant/campaigns",
        json=_campaign_payload(name="Summer Sale", discount_value=15),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Summer Sale"
    assert data["discount_value"] == 15
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_campaigns_api(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    await client.post("/merchant/campaigns", json=_campaign_payload(name="A"), headers=headers)
    await client.post("/merchant/campaigns", json=_campaign_payload(name="B"), headers=headers)

    resp = await client.get("/merchant/campaigns", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_campaign_api(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/campaigns",
        json=_campaign_payload(name="Single"),
        headers=headers,
    )
    campaign_id = create_resp.json()["id"]

    resp = await client.get(f"/merchant/campaigns/{campaign_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Single"


@pytest.mark.asyncio
async def test_update_campaign_api(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/campaigns",
        json=_campaign_payload(name="Original"),
        headers=headers,
    )
    campaign_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/merchant/campaigns/{campaign_id}",
        json={"name": "Updated", "is_active": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_campaign_api(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/campaigns",
        json=_campaign_payload(name="ToDelete"),
        headers=headers,
    )
    campaign_id = create_resp.json()["id"]

    resp = await client.delete(f"/merchant/campaigns/{campaign_id}", headers=headers)
    assert resp.status_code == 204

    # Verify not returned
    resp = await client.get(f"/merchant/campaigns/{campaign_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_campaign_roi_api(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/campaigns",
        json=_campaign_payload(name="ROI Campaign"),
        headers=headers,
    )
    campaign_id = create_resp.json()["id"]

    resp = await client.get(
        f"/merchant/campaigns/{campaign_id}/roi",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["vouchers_issued"] == 0
    assert data["vouchers_used"] == 0


@pytest.mark.asyncio
async def test_campaign_404(client, db_session):
    _, _, headers = await _setup_shop(db_session)

    resp = await client.get("/merchant/campaigns/99999", headers=headers)
    assert resp.status_code == 404
