import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup_owner(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="Shop", slug="shop", owner_user_id=owner.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    return tenant, owner, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_create_tier(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    response = await client.post(
        "/merchant/tiers",
        json={"name": "Bronze", "min_points": 0},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Bronze"


@pytest.mark.asyncio
async def test_list_tiers(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}
    await client.post("/merchant/tiers", json={"name": "Silver", "min_points": 500}, headers=headers)
    await client.post("/merchant/tiers", json={"name": "Bronze", "min_points": 0}, headers=headers)

    response = await client.get("/merchant/tiers", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert [t["name"] for t in data] == ["Bronze", "Silver"]


@pytest.mark.asyncio
async def test_update_tier(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}
    create = await client.post(
        "/merchant/tiers", json={"name": "Bronze", "min_points": 0}, headers=headers
    )
    tier_id = create.json()["id"]

    response = await client.patch(
        f"/merchant/tiers/{tier_id}",
        json={"min_points": 100},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["min_points"] == 100


@pytest.mark.asyncio
async def test_delete_tier_soft_deletes(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}
    create = await client.post(
        "/merchant/tiers", json={"name": "Bronze", "min_points": 0}, headers=headers
    )
    tier_id = create.json()["id"]

    response = await client.delete(f"/merchant/tiers/{tier_id}", headers=headers)
    assert response.status_code == 204

    list_resp = await client.get("/merchant/tiers", headers=headers)
    assert all(t["id"] != tier_id for t in list_resp.json())


@pytest.mark.asyncio
async def test_create_tier_non_owner_returns_403(client, db_session):
    tenant, _owner, _ = await _setup_owner(db_session)
    staff_user = User(email="s@example.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=staff_user.id, role=TenantStaffRole.STAFF)
    )
    await db_session.flush()
    staff_token = create_access_token(user_id=staff_user.id)

    response = await client.post(
        "/merchant/tiers",
        json={"name": "X", "min_points": 0},
        headers={"Authorization": f"Bearer {staff_token}", "X-Tenant-Id": str(tenant.id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_cannot_access_other_tenant_tiers(client, db_session):
    """Owner của tenant A không được CRUD tier của tenant B."""
    tenant_a, _, token_a = await _setup_owner(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    token_b = create_access_token(user_id=owner_b.id)

    create = await client.post(
        "/merchant/tiers",
        json={"name": "B-Bronze", "min_points": 0},
        headers={"Authorization": f"Bearer {token_b}", "X-Tenant-Id": str(tenant_b.id)},
    )
    tier_b_id = create.json()["id"]

    response = await client.patch(
        f"/merchant/tiers/{tier_b_id}",
        json={"name": "hacked"},
        headers={"Authorization": f"Bearer {token_a}", "X-Tenant-Id": str(tenant_a.id)},
    )
    assert response.status_code == 404
