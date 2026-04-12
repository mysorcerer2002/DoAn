"""Integration tests cho /merchant/staff API."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _make_active_tenant_with_owner(db_session):
    owner = User(email="owner@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="Test Shop",
        slug="test-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER)
    )
    await db_session.flush()
    return tenant, owner, create_access_token(user_id=owner.id)


async def test_add_staff_returns_201_with_verification_code(client: AsyncClient, db_session):
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)

    response = await client.post(
        "/merchant/staff",
        json={"email": "newstaff@example.com", "full_name": "New", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["staff"]["role"] == "staff"
    assert data["verification_code"] is not None
    assert len(data["verification_code"]) == 6


async def test_add_staff_non_owner_returns_403(client: AsyncClient, db_session):
    tenant, _owner, _ = await _make_active_tenant_with_owner(db_session)

    staff_user = User(email="s@example.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=staff_user.id, role=TenantStaffRole.STAFF)
    )
    await db_session.flush()
    staff_token = create_access_token(user_id=staff_user.id)

    response = await client.post(
        "/merchant/staff",
        json={"email": "x@example.com", "full_name": "X", "role": "staff"},
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 403


async def test_list_staff_owner_sees_all(client: AsyncClient, db_session):
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)
    await client.post(
        "/merchant/staff",
        json={"email": "s1@example.com", "full_name": "S1", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )

    response = await client.get(
        "/merchant/staff",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_remove_staff(client: AsyncClient, db_session):
    tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)
    add = await client.post(
        "/merchant/staff",
        json={"email": "s@example.com", "full_name": "S", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    staff_id = add.json()["staff"]["id"]

    response = await client.delete(
        f"/merchant/staff/{staff_id}",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-Id": str(tenant.id),
        },
    )
    assert response.status_code == 204


async def test_missing_tenant_header_returns_400(client: AsyncClient, db_session):
    _tenant, _owner, owner_token = await _make_active_tenant_with_owner(db_session)

    response = await client.get(
        "/merchant/staff",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 400
