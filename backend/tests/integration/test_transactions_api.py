import pytest

from app.core.security import create_access_token
from app.models.point_rule import PointRule
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup_shop_with_rule(db_session):
    """Tạo tenant, owner, point rule để test transaction API."""
    owner = User(email="shop@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="ShopTx",
        slug="shop-tx",
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
    rule = PointRule(
        tenant_id=tenant.id,
        points_per_unit=1,
        unit_amount=1000,
        min_amount=0,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": str(tenant.id),
    }
    return tenant, owner, headers


@pytest.mark.asyncio
async def test_create_transaction_success(client, db_session):
    """Tạo giao dịch thành công, trả về 201 với thông tin đầy đủ."""
    _tenant, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/merchant/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "note": "Mua hàng"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction"]["gross_amount"] == 50000
    assert data["transaction"]["net_amount"] == 50000
    assert data["transaction"]["points_earned"] == 50  # 50000/1000 * 1
    assert data["new_balance"] == 50
    assert data["new_total_earned"] == 50
    assert data["member_phone"] is not None


@pytest.mark.asyncio
async def test_create_transaction_invalid_phone(client, db_session):
    """SĐT không hợp lệ trả về 422."""
    _tenant, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/merchant/transactions",
        json={"phone": "12345", "gross_amount": 10000},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_transactions(client, db_session):
    """Tạo 2 giao dịch rồi list ra đúng số lượng."""
    _tenant, _owner, headers = await _setup_shop_with_rule(db_session)

    await client.post(
        "/merchant/transactions",
        json={"phone": "0901234567", "gross_amount": 10000},
        headers=headers,
    )
    await client.post(
        "/merchant/transactions",
        json={"phone": "0907654321", "gross_amount": 20000},
        headers=headers,
    )

    resp = await client.get("/merchant/transactions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_create_transaction_no_rule_returns_409(client, db_session):
    """Tenant không có point rule -> 409."""
    owner = User(email="norule@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="NoRule",
        slug="no-rule",
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

    resp = await client.post(
        "/merchant/transactions",
        json={"phone": "0901234567", "gross_amount": 10000},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_transaction_cross_tenant_isolation(client, db_session):
    """Giao dịch của tenant A không hiện khi tenant B list."""
    tenant_a, _owner_a, headers_a = await _setup_shop_with_rule(db_session)

    # Tạo tenant B
    owner_b = User(email="shopb@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="ShopB",
        slug="shop-b",
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
    db_session.add(
        PointRule(
            tenant_id=tenant_b.id,
            points_per_unit=1,
            unit_amount=1000,
            min_amount=0,
            is_active=True,
        )
    )
    await db_session.flush()
    token_b = create_access_token(user_id=owner_b.id)
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Tenant-Id": str(tenant_b.id),
    }

    # Tenant A tạo 1 giao dịch
    await client.post(
        "/merchant/transactions",
        json={"phone": "0901234567", "gross_amount": 10000},
        headers=headers_a,
    )

    # Tenant B list -> phải rỗng
    resp = await client.get("/merchant/transactions", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []
