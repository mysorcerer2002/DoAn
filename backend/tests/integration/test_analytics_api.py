"""Integration tests: Analytics + Admin API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus


async def _setup_analytics(db_session):
    """Tạo owner, tenant, member, transactions cho test analytics API."""
    now = datetime.now(timezone.utc)

    owner = User(email="analytics-api@test.com", password_hash="x", is_active=True)
    member_user = User(email="api-member@test.com", password_hash="x", is_active=True)
    db_session.add_all([owner, member_user])
    await db_session.flush()

    tenant = Tenant(
        name="AnalyticsAPIShop",
        slug="analytics-api-shop",
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

    membership = Membership(
        tenant_id=tenant.id,
        user_id=member_user.id,
        joined_at=now,
        points_balance=100,
        total_points_earned=100,
    )
    db_session.add(membership)
    await db_session.flush()

    # 2 transactions
    for i in range(2):
        db_session.add(
            Transaction(
                tenant_id=tenant.id,
                membership_id=membership.id,
                staff_id=owner.id,
                gross_amount=50000,
                net_amount=50000,
                points_earned=5,
                method=TransactionMethod.MANUAL,
                created_at=now - timedelta(days=i),
            )
        )
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": str(tenant.id),
    }
    return tenant, owner, headers


@pytest.mark.asyncio
async def test_dashboard_api(client, db_session):
    tenant, _, headers = await _setup_analytics(db_session)

    resp = await client.get(
        "/merchant/analytics/dashboard",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["member_count"] == 1
    assert data["transaction_count"] == 2
    assert data["total_revenue"] == 100000
    assert "daily_transactions" in data
    assert "tier_distribution" in data
    assert "campaign_roi" in data
    assert data["period_from"] is not None
    assert data["period_to"] is not None


@pytest.mark.asyncio
async def test_dashboard_api_with_date_range(client, db_session):
    _, _, headers = await _setup_analytics(db_session)

    resp = await client.get(
        "/merchant/analytics/dashboard",
        params={"from": "2020-01-01", "to": "2020-01-07"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["transaction_count"] == 0
    assert data["total_revenue"] == 0
    assert len(data["daily_transactions"]) == 7


@pytest.mark.asyncio
async def test_dashboard_api_requires_owner(client, db_session):
    """Staff (non-owner) không được xem analytics."""
    now = datetime.now(timezone.utc)

    owner = User(email="dash-owner@test.com", password_hash="x", is_active=True)
    staff_user = User(email="dash-staff@test.com", password_hash="x", is_active=True)
    db_session.add_all([owner, staff_user])
    await db_session.flush()

    tenant = Tenant(
        name="DashTestShop",
        slug="dash-test-shop",
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
    db_session.add(
        TenantStaff(
            tenant_id=tenant.id,
            user_id=staff_user.id,
            role=TenantStaffRole.STAFF,
        )
    )
    await db_session.flush()

    staff_token = create_access_token(user_id=staff_user.id)
    headers = {
        "Authorization": f"Bearer {staff_token}",
        "X-Tenant-Id": str(tenant.id),
    }
    resp = await client.get(
        "/merchant/analytics/dashboard",
        headers=headers,
    )
    assert resp.status_code == 403


# ── Admin Endpoints ──


async def _setup_admin(db_session):
    """Tạo super admin + tenant cho test admin endpoints."""
    now = datetime.now(timezone.utc)

    admin = User(
        email="superadmin-analytics@test.com",
        password_hash="x",
        is_active=True,
        system_role="super_admin",
    )
    db_session.add(admin)
    await db_session.flush()

    tenant = Tenant(
        name="AdminTestShop",
        slug="admin-test-shop",
        owner_user_id=admin.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    # Thêm 1 member + 1 transaction cho stats
    member_user = User(email="adm-member@test.com", password_hash="x", is_active=True)
    db_session.add(member_user)
    await db_session.flush()

    membership = Membership(
        tenant_id=tenant.id,
        user_id=member_user.id,
        joined_at=now,
        points_balance=50,
        total_points_earned=50,
    )
    db_session.add(membership)
    await db_session.flush()

    txn = Transaction(
        tenant_id=tenant.id,
        membership_id=membership.id,
        staff_id=admin.id,
        gross_amount=100000,
        net_amount=100000,
        points_earned=10,
        method=TransactionMethod.MANUAL,
    )
    db_session.add(txn)
    await db_session.flush()

    token = create_access_token(user_id=admin.id)
    headers = {"Authorization": f"Bearer {token}"}
    return tenant, admin, member_user, headers


@pytest.mark.asyncio
async def test_tenant_detail(client, db_session):
    tenant, _, _, headers = await _setup_admin(db_session)

    resp = await client.get(
        f"/admin/tenants/{tenant.id}/detail",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == tenant.id
    assert data["name"] == "AdminTestShop"
    assert data["member_count"] == 1
    assert data["transaction_count"] == 1
    assert data["total_revenue"] == 100000


@pytest.mark.asyncio
async def test_tenant_detail_not_found(client, db_session):
    _, _, _, headers = await _setup_admin(db_session)

    resp = await client.get(
        "/admin/tenants/99999/detail",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_suspend_tenant(client, db_session):
    tenant, _, _, headers = await _setup_admin(db_session)

    resp = await client.post(
        f"/admin/tenants/{tenant.id}/suspend",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "suspended"


@pytest.mark.asyncio
async def test_suspend_tenant_not_found(client, db_session):
    _, _, _, headers = await _setup_admin(db_session)

    resp = await client.post(
        "/admin/tenants/99999/suspend",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_platform_stats(client, db_session):
    _, _, _, headers = await _setup_admin(db_session)

    resp = await client.get("/admin/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tenants"] >= 1
    assert data["total_users"] >= 2
    assert data["total_transactions"] >= 1


@pytest.mark.asyncio
async def test_platform_stats_requires_admin(client, db_session):
    """Non-admin không được xem platform stats."""
    normal_user = User(
        email="nonadmin@test.com", password_hash="x", is_active=True
    )
    db_session.add(normal_user)
    await db_session.flush()

    token = create_access_token(user_id=normal_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin/stats", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_cross_tenant_detail(client, db_session):
    """Admin có thể xem detail của bất kỳ tenant nào."""
    tenant, _, _, headers = await _setup_admin(db_session)

    # Tạo thêm tenant B
    owner_b = User(email="otherowner@test.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()

    tenant_b = Tenant(
        name="OtherShopAdmin",
        slug="other-shop-admin",
        owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()

    resp = await client.get(
        f"/admin/tenants/{tenant_b.id}/detail",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "OtherShopAdmin"
    assert data["member_count"] == 0
    assert data["transaction_count"] == 0


@pytest.mark.asyncio
async def test_dashboard_api_max_range_rejected(client, db_session):
    """Date range > 366 ngày → 422 (anti-DoS)."""
    _, _, headers = await _setup_analytics(db_session)

    resp = await client.get(
        "/merchant/analytics/dashboard",
        params={"from": "2020-01-01", "to": "2026-12-31"},
        headers=headers,
    )
    assert resp.status_code == 422
    assert "too large" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_dashboard_api_cross_tenant_forbidden(client, db_session):
    """C2 fix: owner tenant A không xem được analytics tenant B."""
    tenant_a, owner_a, _ = await _setup_analytics(db_session)

    owner_b = User(
        email="owner-b-dash@test.com", password_hash="x", is_active=True
    )
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="ShopB",
        slug="shop-b-dash-cross",
        owner_user_id=owner_b.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        TenantStaff(
            tenant_id=tenant_b.id,
            user_id=owner_b.id,
            role=TenantStaffRole.OWNER,
        )
    )
    await db_session.flush()
    await db_session.commit()

    token_a = create_access_token(user_id=owner_a.id)
    resp = await client.get(
        "/merchant/analytics/dashboard",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-Id": str(tenant_b.id),
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_api_invalid_date_range_returns_422(client, db_session):
    """from_date > to_date phải trả 422."""
    _, _, headers = await _setup_analytics(db_session)

    resp = await client.get(
        "/merchant/analytics/dashboard",
        params={"from": "2025-02-01", "to": "2025-01-01"},
        headers=headers,
    )
    assert resp.status_code == 422
