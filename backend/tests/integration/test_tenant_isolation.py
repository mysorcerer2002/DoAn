"""Cross-tenant isolation tests.

Mục đích: đảm bảo user của tenant A không thao tác được dữ liệu của tenant B,
KHÔNG dựa vào ORM scoping mặc định mà phải qua tenant_id filter ở mọi query.
"""
import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


@pytest.fixture
async def two_tenants_with_owners(db_session):
    owner_a = User(email="a@example.com", password_hash="x", is_active=True)
    owner_b = User(email="b@example.com", password_hash="x", is_active=True)
    db_session.add_all([owner_a, owner_b])
    await db_session.flush()

    tenant_a = Tenant(
        name="Shop A", slug="shop-a", owner_user_id=owner_a.id,
        status=TenantStatus.ACTIVE, settings={},
    )
    tenant_b = Tenant(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    db_session.add_all([
        TenantStaff(tenant_id=tenant_a.id, user_id=owner_a.id, role=TenantStaffRole.OWNER),
        TenantStaff(tenant_id=tenant_b.id, user_id=owner_b.id, role=TenantStaffRole.OWNER),
    ])
    await db_session.flush()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "owner_a": owner_a,
        "owner_b": owner_b,
        "token_a": create_access_token(user_id=owner_a.id),
        "token_b": create_access_token(user_id=owner_b.id),
    }


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_tiers(client, two_tenants_with_owners):
    """Owner A gửi X-Tenant-Id của tenant B → 403."""
    ctx = two_tenants_with_owners
    response = await client.post(
        "/merchant/tiers",
        json={"name": "Hacked", "min_points": 0},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_staff(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.get(
        "/merchant/staff",
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_settings(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.patch(
        "/tenants/me/settings",
        json={"points_on_gross": True},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_point_rules(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.post(
        "/merchant/point-rules",
        json={"points_per_unit": "100.00"},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tiers_listed_for_a_not_visible_to_b(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Tenant-Id": str(ctx["tenant_a"].id),
    }
    headers_b = {
        "Authorization": f"Bearer {ctx['token_b']}",
        "X-Tenant-Id": str(ctx["tenant_b"].id),
    }
    await client.post(
        "/merchant/tiers", json={"name": "A-Bronze", "min_points": 0}, headers=headers_a
    )
    await client.post(
        "/merchant/tiers", json={"name": "B-Bronze", "min_points": 0}, headers=headers_b
    )

    list_a = await client.get("/merchant/tiers", headers=headers_a)
    list_b = await client.get("/merchant/tiers", headers=headers_b)
    names_a = {t["name"] for t in list_a.json()}
    names_b = {t["name"] for t in list_b.json()}

    assert "A-Bronze" in names_a
    assert "B-Bronze" not in names_a
    assert "B-Bronze" in names_b
    assert "A-Bronze" not in names_b
