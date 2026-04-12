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
async def test_get_default_settings(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    response = await client.get("/tenants/me/settings", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["points_on_gross"] is False
    assert data["voucher_default_ttl_days"] == 30


@pytest.mark.asyncio
async def test_update_settings(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    response = await client.patch(
        "/tenants/me/settings",
        json={"points_on_gross": True, "voucher_default_ttl_days": 60},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["points_on_gross"] is True
    assert data["voucher_default_ttl_days"] == 60


@pytest.mark.asyncio
async def test_list_audit_after_update(client, db_session):
    tenant, _owner, token = await _setup_owner(db_session)
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": str(tenant.id)}

    await client.patch(
        "/tenants/me/settings",
        json={"points_on_gross": True},
        headers=headers,
    )

    response = await client.get("/tenants/me/settings/audit", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["field_key"] == "points_on_gross"


@pytest.mark.asyncio
async def test_settings_cross_tenant_isolation(client, db_session):
    """Owner A không thể access settings của tenant B."""
    tenant_a, _, token_a = await _setup_owner(db_session)

    owner_b = User(email="ob@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()

    response = await client.patch(
        "/tenants/me/settings",
        json={"points_on_gross": True},
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-Id": str(tenant_b.id),
        },
    )
    assert response.status_code == 403
