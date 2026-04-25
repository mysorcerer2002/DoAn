"""Cross-tenant isolation tests.

Mục đích: đảm bảo user của tenant A không thao tác được dữ liệu của tenant B,
KHÔNG dựa vào ORM scoping mặc định mà phải qua partner_id filter ở mọi query.
"""
import pytest

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.partner import Partner, PartnerStatus
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User


@pytest.fixture
async def two_tenants_with_owners(db_session):
    owner_a = User(email="a@example.com", password_hash="x", is_active=True)
    owner_b = User(email="b@example.com", password_hash="x", is_active=True)
    db_session.add_all([owner_a, owner_b])
    await db_session.flush()

    tenant_a = Partner(
        name="Shop A", slug="shop-a", owner_user_id=owner_a.id,
        status=PartnerStatus.ACTIVE, settings={},
    )
    tenant_b = Partner(
        name="Shop B", slug="shop-b", owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE, settings={},
    )
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    db_session.add_all([
        PartnerStaff(partner_id=tenant_a.id, user_id=owner_a.id, role=PartnerStaffRole.OWNER),
        PartnerStaff(partner_id=tenant_b.id, user_id=owner_b.id, role=PartnerStaffRole.OWNER),
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
    """Owner A gửi X-Partner-Id của tenant B → 403."""
    ctx = two_tenants_with_owners
    response = await client.post(
        "/partner/tiers",
        json={"name": "Hacked", "min_points": 0},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Partner-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_staff(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.get(
        "/partner/staff",
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Partner-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_settings(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.patch(
        "/partners/me/settings",
        json={"points_on_gross": True},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Partner-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_use_tenant_b_header_for_point_rules(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.post(
        "/partner/point-rules",
        json={"points_per_unit": "100.00"},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Partner-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tiers_listed_for_a_not_visible_to_b(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Partner-Id": str(ctx["tenant_a"].id),
    }
    headers_b = {
        "Authorization": f"Bearer {ctx['token_b']}",
        "X-Partner-Id": str(ctx["tenant_b"].id),
    }
    await client.post(
        "/partner/tiers", json={"name": "A-Bronze", "min_points": 0}, headers=headers_a
    )
    await client.post(
        "/partner/tiers", json={"name": "B-Bronze", "min_points": 0}, headers=headers_b
    )

    list_a = await client.get("/partner/tiers", headers=headers_a)
    list_b = await client.get("/partner/tiers", headers=headers_b)
    names_a = {t["name"] for t in list_a.json()}
    names_b = {t["name"] for t in list_b.json()}

    assert "A-Bronze" in names_a
    assert "B-Bronze" not in names_a
    assert "B-Bronze" in names_b
    assert "A-Bronze" not in names_b


# ─────────────────────────────────────────────────────────────────────
# Fixture mở rộng: 2 tenant với members + transactions
# Dùng để test cross-tenant query không bị rò rỉ data giữa members/txn.
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
async def two_tenants_full_data(db_session):
    """Setup: 2 tenant, mỗi tenant 2 customer + 2 transaction."""
    # Owners
    owner_a = User(email="a-owner@x.com", password_hash="x", is_active=True)
    owner_b = User(email="b-owner@x.com", password_hash="x", is_active=True)
    db_session.add_all([owner_a, owner_b])
    await db_session.flush()

    # Tenants
    tenant_a = Partner(
        name="Shop A", slug="shop-a-iso", owner_user_id=owner_a.id,
        status=PartnerStatus.ACTIVE, settings={},
    )
    tenant_b = Partner(
        name="Shop B", slug="shop-b-iso", owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE, settings={},
    )
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    # Staff
    db_session.add_all([
        PartnerStaff(partner_id=tenant_a.id, user_id=owner_a.id, role=PartnerStaffRole.OWNER),
        PartnerStaff(partner_id=tenant_b.id, user_id=owner_b.id, role=PartnerStaffRole.OWNER),
    ])
    await db_session.flush()

    # Customers (mỗi tenant 2 khách)
    cust_a1 = User(email="a-c1@x.com", password_hash="x", is_active=True, full_name="A Customer 1")
    cust_a2 = User(email="a-c2@x.com", password_hash="x", is_active=True, full_name="A Customer 2")
    cust_b1 = User(email="b-c1@x.com", password_hash="x", is_active=True, full_name="B Customer 1")
    cust_b2 = User(email="b-c2@x.com", password_hash="x", is_active=True, full_name="B Customer 2")
    db_session.add_all([cust_a1, cust_a2, cust_b1, cust_b2])
    await db_session.flush()

    # Memberships
    mem_a1 = Membership(partner_id=tenant_a.id, user_id=cust_a1.id, points_balance=100, total_points_earned=100)
    mem_a2 = Membership(partner_id=tenant_a.id, user_id=cust_a2.id, points_balance=200, total_points_earned=200)
    mem_b1 = Membership(partner_id=tenant_b.id, user_id=cust_b1.id, points_balance=300, total_points_earned=300)
    mem_b2 = Membership(partner_id=tenant_b.id, user_id=cust_b2.id, points_balance=400, total_points_earned=400)
    db_session.add_all([mem_a1, mem_a2, mem_b1, mem_b2])
    await db_session.flush()

    # Transactions
    db_session.add_all([
        Transaction(
            partner_id=tenant_a.id, membership_id=mem_a1.id, staff_id=owner_a.id,
            gross_amount=50000, net_amount=50000, points_earned=5,
            method=TransactionMethod.MANUAL, note="A txn 1",
        ),
        Transaction(
            partner_id=tenant_b.id, membership_id=mem_b1.id, staff_id=owner_b.id,
            gross_amount=70000, net_amount=70000, points_earned=7,
            method=TransactionMethod.MANUAL, note="B txn 1",
        ),
    ])
    await db_session.flush()

    return {
        "tenant_a": tenant_a, "tenant_b": tenant_b,
        "owner_a": owner_a, "owner_b": owner_b,
        "cust_a1": cust_a1, "cust_b1": cust_b1,
        "mem_a1": mem_a1, "mem_b1": mem_b1,
        "token_a": create_access_token(user_id=owner_a.id),
        "token_b": create_access_token(user_id=owner_b.id),
        "token_cust_a1": create_access_token(user_id=cust_a1.id),
        "token_cust_b1": create_access_token(user_id=cust_b1.id),
    }


# ─── Merchant-side isolation: members, transactions ───


@pytest.mark.asyncio
async def test_isolation_members_list(client, two_tenants_full_data):
    """Owner A list /partner/members → chỉ thấy membership của tenant A."""
    ctx = two_tenants_full_data
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Partner-Id": str(ctx["tenant_a"].id),
    }
    resp = await client.get("/partner/members", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()
    # Chỉ chứa A customers, không có B
    ids = {m["membership_id"] for m in data}
    assert ctx["mem_a1"].id in ids
    assert ctx["mem_b1"].id not in ids


@pytest.mark.asyncio
async def test_isolation_members_detail_403(client, two_tenants_full_data):
    """Owner A truy cập member detail của tenant B → 403/404, không leak data."""
    ctx = two_tenants_full_data
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Partner-Id": str(ctx["tenant_a"].id),
    }
    resp = await client.get(
        f"/partner/members/{ctx['mem_b1'].id}", headers=headers_a
    )
    # Không được phép đọc — 404 (not found trong tenant A) hoặc 403
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_isolation_transactions_list(client, two_tenants_full_data):
    """Owner A list /partner/transactions → chỉ thấy txn của tenant A."""
    ctx = two_tenants_full_data
    headers_a = {
        "Authorization": f"Bearer {ctx['token_a']}",
        "X-Partner-Id": str(ctx["tenant_a"].id),
    }
    resp = await client.get("/partner/transactions", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()
    notes = {t["note"] for t in data}
    assert "A txn 1" in notes
    assert "B txn 1" not in notes


@pytest.mark.asyncio
async def test_isolation_owner_a_spoofs_tenant_b_for_members(
    client, two_tenants_full_data
):
    """Owner A gửi X-Partner-Id của tenant B cho /partner/members → 403."""
    ctx = two_tenants_full_data
    resp = await client.get(
        "/partner/members",
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Partner-Id": str(ctx["tenant_b"].id),
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_isolation_owner_a_spoofs_tenant_b_for_transactions(
    client, two_tenants_full_data
):
    ctx = two_tenants_full_data
    resp = await client.get(
        "/partner/transactions",
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Partner-Id": str(ctx["tenant_b"].id),
        },
    )
    assert resp.status_code == 403


# ─── Customer-side isolation: /users/me/* ───


@pytest.mark.asyncio
async def test_isolation_user_me_memberships(client, two_tenants_full_data):
    """Customer A gọi /users/me/partners-as-staff → chỉ thấy tenant A (từ staff), không thấy B."""
    ctx = two_tenants_full_data
    # Customer A không phải staff của tenant nào → list empty
    resp = await client.get(
        "/users/me/partners-as-staff",
        headers={"Authorization": f"Bearer {ctx['token_cust_a1']}"},
    )
    assert resp.status_code == 200
    # Customer không có staff role ở tenant nào
    assert resp.json() == []


@pytest.mark.asyncio
async def test_isolation_user_me_ledger_own_only(
    client, db_session, two_tenants_full_data
):
    """Customer A gọi /users/me/ledger → chỉ thấy ledger entry của chính A qua membership A.

    Endpoint này trả ledger cho TẤT CẢ membership của current user, không phải tenant header.
    Vì vậy customer B gọi endpoint này KHÔNG được thấy entry của A.
    """
    ctx = two_tenants_full_data
    from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger

    entry = PointLedger(
        partner_id=ctx["tenant_a"].id,
        membership_id=ctx["mem_a1"].id,
        delta=50,
        reason=LedgerReason.ADJUST,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        balance_after=150,
        description="Test entry cho customer A",
    )
    db_session.add(entry)
    await db_session.flush()

    # Customer A → thấy entry
    resp_a = await client.get(
        "/users/me/ledger",
        headers={"Authorization": f"Bearer {ctx['token_cust_a1']}"},
    )
    assert resp_a.status_code == 200
    descriptions_a = {e.get("description") for e in resp_a.json()}
    assert "Test entry cho customer A" in descriptions_a

    # Customer B → KHÔNG thấy entry của A
    resp_b = await client.get(
        "/users/me/ledger",
        headers={"Authorization": f"Bearer {ctx['token_cust_b1']}"},
    )
    assert resp_b.status_code == 200
    descriptions_b = {e.get("description") for e in resp_b.json()}
    assert "Test entry cho customer A" not in descriptions_b


@pytest.mark.asyncio
async def test_isolation_customer_cannot_access_merchant_endpoints(
    client, two_tenants_full_data
):
    """Customer A gọi /partner/members với bất kỳ X-Partner-Id nào → 403."""
    ctx = two_tenants_full_data
    resp = await client.get(
        "/partner/members",
        headers={
            "Authorization": f"Bearer {ctx['token_cust_a1']}",
            "X-Partner-Id": str(ctx["tenant_a"].id),
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_isolation_customer_cannot_access_admin_endpoints(
    client, two_tenants_full_data
):
    """Customer A (không phải super_admin) gọi /admin/users → 403."""
    ctx = two_tenants_full_data
    resp = await client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {ctx['token_cust_a1']}"},
    )
    assert resp.status_code == 403
