"""Integration tests cho Tenant API: register, admin approve, list my tenants, get tenant me."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _create_user(
    db,
    *,
    email: str = "owner@test.com",
    system_role: str = "regular",
) -> User:
    """Helper: tạo user trong DB, trả về User object."""
    user = User(
        email=email,
        password_hash=hash_password("Test1234!"),
        full_name="Test User",
        is_active=True,
        system_role=system_role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def _auth_headers(user_id: int) -> dict[str, str]:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ── POST /merchant/register ──


async def test_register_tenant_success(client: AsyncClient, db_session):
    user = await _create_user(db_session)
    resp = await client.post(
        "/merchant/register",
        json={"name": "Cà Phê Sài Gòn", "description": "Quán cà phê đặc biệt"},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Cà Phê Sài Gòn"
    assert data["status"] == "pending"
    assert data["owner_user_id"] == user.id
    assert "slug" in data


async def test_register_tenant_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/merchant/register",
        json={"name": "Test Shop"},
    )
    assert resp.status_code == 401


async def test_register_tenant_invalid_name(client: AsyncClient, db_session):
    user = await _create_user(db_session)
    resp = await client.post(
        "/merchant/register",
        json={"name": "x"},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 422


# ── GET /admin/tenants ──


async def test_admin_list_tenants(client: AsyncClient, db_session):
    admin = await _create_user(db_session, email="admin@test.com", system_role="super_admin")
    owner = await _create_user(db_session, email="owner@test.com", system_role="regular")

    # Tạo tenant trước
    await client.post(
        "/merchant/register",
        json={"name": "Shop A"},
        headers=_auth_headers(owner.id),
    )

    resp = await client.get(
        "/admin/tenants",
        params={"status": "pending"},
        headers=_auth_headers(admin.id),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"


async def test_admin_list_tenants_forbidden(client: AsyncClient, db_session):
    user = await _create_user(db_session, system_role="regular")
    resp = await client.get(
        "/admin/tenants",
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 403


# ── POST /admin/tenants/{id}/approve ──


async def test_admin_approve_tenant(client: AsyncClient, db_session):
    admin = await _create_user(db_session, email="admin@test.com", system_role="super_admin")
    owner = await _create_user(db_session, email="owner@test.com", system_role="regular")

    reg_resp = await client.post(
        "/merchant/register",
        json={"name": "Shop Approve"},
        headers=_auth_headers(owner.id),
    )
    tenant_id = reg_resp.json()["id"]

    resp = await client.post(
        f"/admin/tenants/{tenant_id}/approve",
        json={"approve": True},
        headers=_auth_headers(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


async def test_admin_reject_tenant(client: AsyncClient, db_session):
    admin = await _create_user(db_session, email="admin@test.com", system_role="super_admin")
    owner = await _create_user(db_session, email="owner@test.com", system_role="regular")

    reg_resp = await client.post(
        "/merchant/register",
        json={"name": "Shop Reject"},
        headers=_auth_headers(owner.id),
    )
    tenant_id = reg_resp.json()["id"]

    resp = await client.post(
        f"/admin/tenants/{tenant_id}/approve",
        json={"approve": False},
        headers=_auth_headers(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspended"


# ── GET /tenants/users/me/tenants ──


async def test_list_my_tenants(client: AsyncClient, db_session):
    owner = await _create_user(db_session)

    await client.post(
        "/merchant/register",
        json={"name": "My Shop 1"},
        headers=_auth_headers(owner.id),
    )
    await client.post(
        "/merchant/register",
        json={"name": "My Shop 2"},
        headers=_auth_headers(owner.id),
    )

    resp = await client.get(
        "/tenants/users/me/tenants",
        headers=_auth_headers(owner.id),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


# ── GET /tenants/me ──


async def test_get_tenant_me_active(client: AsyncClient, db_session):
    admin = await _create_user(db_session, email="admin@test.com", system_role="super_admin")
    owner = await _create_user(db_session, email="owner@test.com", system_role="regular")

    reg_resp = await client.post(
        "/merchant/register",
        json={"name": "Active Shop"},
        headers=_auth_headers(owner.id),
    )
    tenant_id = reg_resp.json()["id"]

    # Approve tenant trước
    await client.post(
        f"/admin/tenants/{tenant_id}/approve",
        json={"approve": True},
        headers=_auth_headers(admin.id),
    )

    resp = await client.get(
        "/tenants/me",
        headers={**_auth_headers(owner.id), "X-Tenant-Id": str(tenant_id)},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


async def test_get_tenant_me_pending_forbidden(client: AsyncClient, db_session):
    owner = await _create_user(db_session)

    reg_resp = await client.post(
        "/merchant/register",
        json={"name": "Pending Shop"},
        headers=_auth_headers(owner.id),
    )
    tenant_id = reg_resp.json()["id"]

    resp = await client.get(
        "/tenants/me",
        headers={**_auth_headers(owner.id), "X-Tenant-Id": str(tenant_id)},
    )
    assert resp.status_code == 403


async def test_get_tenant_me_not_found(client: AsyncClient, db_session):
    owner = await _create_user(db_session)
    resp = await client.get(
        "/tenants/me",
        headers={**_auth_headers(owner.id), "X-Tenant-Id": "9999"},
    )
    assert resp.status_code == 404
