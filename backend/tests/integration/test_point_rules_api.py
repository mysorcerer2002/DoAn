import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER))
    await db_session.flush()
    return tenant, create_access_token(user_id=owner.id)


@pytest.mark.asyncio
async def test_create_and_get_active_rule(client, db_session):
    tenant, token = await _setup(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    create = await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "1.00", "unit_amount": 1000, "min_amount": 10000},
        headers=headers,
    )
    assert create.status_code == 201

    get_active = await client.get("/merchant/point-rules/active", headers=headers)
    assert get_active.status_code == 200
    assert get_active.json()["points_per_unit"] == "1.00"


@pytest.mark.asyncio
async def test_create_rule_deactivates_old(client, db_session):
    tenant, token = await _setup(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "1.00"},
        headers=headers,
    )
    await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "2.00"},
        headers=headers,
    )

    list_resp = await client.get("/merchant/point-rules", headers=headers)
    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert len(rules) == 2
    active = [r for r in rules if r["is_active"]]
    assert len(active) == 1
    assert active[0]["points_per_unit"] == "2.00"


@pytest.mark.asyncio
async def test_point_rule_cross_tenant_isolation(client, db_session):
    tenant_a, token_a = await _setup(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="B", slug="b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    token_b = create_access_token(user_id=owner_b.id)

    await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "5.00"},
        headers={"Authorization": f"Bearer {token_b}", "X-Tenant-Id": str(tenant_b.id)},
    )

    response = await client.get(
        "/merchant/point-rules/active",
        headers={"Authorization": f"Bearer {token_a}", "X-Tenant-Id": str(tenant_a.id)},
    )
    assert response.status_code == 200
    assert response.json() is None
