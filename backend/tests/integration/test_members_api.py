import pytest
from datetime import datetime, timezone

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.point_rule import PointRule
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup_with_member(db_session):
    """Tạo tenant + owner + point rule + 1 member (qua transaction API pattern)."""
    owner = User(email="shop-m@example.com", password_hash="x", is_active=True)
    member_user = User(
        phone="+84901234567", email=None, password_hash="x", is_active=True
    )
    db_session.add_all([owner, member_user])
    await db_session.flush()

    tenant = Tenant(
        name="ShopM",
        slug="shop-m",
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

    membership = Membership(
        tenant_id=tenant.id,
        user_id=member_user.id,
        points_balance=100,
        total_points_earned=100,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    # Tạo 1 ledger entry để test GET ledger
    ledger = PointLedger(
        tenant_id=tenant.id,
        membership_id=membership.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.TRANSACTION,
        ref_id=None,
        balance_after=100,
        description="Test earn",
    )
    db_session.add(ledger)
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": str(tenant.id),
    }
    return tenant, owner, membership, member_user, headers


@pytest.mark.asyncio
async def test_list_members(client, db_session):
    """List members trả về danh sách thành viên."""
    _tenant, _owner, _membership, _member, headers = await _setup_with_member(
        db_session
    )

    resp = await client.get("/merchant/members", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["points_balance"] == 100


@pytest.mark.asyncio
async def test_get_member_detail(client, db_session):
    """GET member chi tiết trả về đúng thông tin."""
    _tenant, _owner, membership, member_user, headers = await _setup_with_member(
        db_session
    )

    resp = await client.get(
        f"/merchant/members/{membership.id}", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["membership_id"] == membership.id
    assert data["user_phone"] == "+84901234567"
    assert data["points_balance"] == 100


@pytest.mark.asyncio
async def test_get_member_not_found(client, db_session):
    """GET member không tồn tại trả 404."""
    _tenant, _owner, _membership, _member, headers = await _setup_with_member(
        db_session
    )

    resp = await client.get("/merchant/members/99999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_member_ledger(client, db_session):
    """GET ledger trả về lịch sử điểm."""
    _tenant, _owner, membership, _member, headers = await _setup_with_member(
        db_session
    )

    resp = await client.get(
        f"/merchant/members/{membership.id}/ledger", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["delta"] == 100
    assert data[0]["reason"] == "earn"


@pytest.mark.asyncio
async def test_member_cross_tenant_isolation(client, db_session):
    """Tenant B không thấy member của tenant A."""
    _tenant_a, _owner_a, membership, _member, headers_a = await _setup_with_member(
        db_session
    )

    # Tạo tenant B
    owner_b = User(email="shopb-m@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="ShopBM",
        slug="shop-b-m",
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
    token_b = create_access_token(user_id=owner_b.id)
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Tenant-Id": str(tenant_b.id),
    }

    # Tenant B list members -> rỗng
    resp = await client.get("/merchant/members", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []

    # Tenant B xem member detail của tenant A -> 404
    resp = await client.get(
        f"/merchant/members/{membership.id}", headers=headers_b
    )
    assert resp.status_code == 404
