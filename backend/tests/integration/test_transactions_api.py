import pytest

from app.core.security import create_access_token
from app.models.point_rule import PointRule
from app.models.partner import Partner, PartnerStatus
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.user import User


async def _setup_shop_with_rule(db_session):
    """Tạo tenant, owner, point rule để test transaction API."""
    owner = User(email="shop@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="ShopTx",
        slug="shop-tx",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    db_session.add(
        PartnerStaff(
            partner_id=partner.id,
            user_id=owner.id,
            role=PartnerStaffRole.OWNER,
        )
    )
    rule = PointRule(
        partner_id=partner.id,
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
        "X-Partner-Id": str(partner.id),
    }
    return partner, owner, headers


@pytest.mark.asyncio
async def test_create_transaction_success(client, db_session):
    """Tạo giao dịch thành công, trả về 201 với thông tin đầy đủ."""
    _tenant, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/partner/transactions",
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
        "/partner/transactions",
        json={"phone": "12345", "gross_amount": 10000},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_transactions(client, db_session):
    """Tạo 2 giao dịch rồi list ra đúng số lượng."""
    _tenant, _owner, headers = await _setup_shop_with_rule(db_session)

    await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 10000},
        headers=headers,
    )
    await client.post(
        "/partner/transactions",
        json={"phone": "0907654321", "gross_amount": 20000},
        headers=headers,
    )

    resp = await client.get("/partner/transactions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_create_transaction_no_rule_returns_409(client, db_session):
    """Partner không có point rule -> 409."""
    owner = User(email="norule@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="NoRule",
        slug="no-rule",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    db_session.add(
        PartnerStaff(
            partner_id=partner.id,
            user_id=owner.id,
            role=PartnerStaffRole.OWNER,
        )
    )
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Partner-Id": str(partner.id),
    }

    resp = await client.post(
        "/partner/transactions",
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
    tenant_b = Partner(
        name="ShopB",
        slug="shop-b",
        owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()
    db_session.add(
        PartnerStaff(
            partner_id=tenant_b.id,
            user_id=owner_b.id,
            role=PartnerStaffRole.OWNER,
        )
    )
    db_session.add(
        PointRule(
            partner_id=tenant_b.id,
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
        "X-Partner-Id": str(tenant_b.id),
    }

    # Partner A tạo 1 giao dịch
    await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 10000},
        headers=headers_a,
    )

    # Partner B list -> phải rỗng
    resp = await client.get("/partner/transactions", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []


# ── receipt_code tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_transaction_with_receipt_code(client, db_session):
    """receipt_code được lưu và trả về trong response."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "receipt_code": "HD-001"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction"]["receipt_code"] == "HD-001"


@pytest.mark.asyncio
async def test_create_transaction_receipt_code_whitespace_normalized(client, db_session):
    """receipt_code chỉ toàn whitespace được normalize về None."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "receipt_code": "   "},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["transaction"]["receipt_code"] is None


@pytest.mark.asyncio
async def test_create_transaction_receipt_code_null(client, db_session):
    """receipt_code omitted → None trong response."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["transaction"]["receipt_code"] is None


@pytest.mark.asyncio
async def test_create_transaction_duplicate_receipt_code_same_partner_returns_409(
    client, db_session
):
    """Hai giao dịch cùng receipt_code trong cùng partner → 409."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp1 = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "receipt_code": "HD-DUP"},
        headers=headers,
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 60000, "receipt_code": "HD-DUP"},
        headers=headers,
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_create_transaction_same_receipt_code_different_partners_ok(
    client, db_session
):
    """Hai partner khác nhau CÓ THỂ dùng cùng receipt_code — index partial per-partner."""
    _partner_a, _owner_a, headers_a = await _setup_shop_with_rule(db_session)

    owner_b = User(email="shopb2@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    partner_b = Partner(
        name="ShopB2",
        slug="shop-b2",
        owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner_b)
    await db_session.flush()
    db_session.add(
        PartnerStaff(partner_id=partner_b.id, user_id=owner_b.id, role=PartnerStaffRole.OWNER)
    )
    db_session.add(
        PointRule(
            partner_id=partner_b.id,
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
        "X-Partner-Id": str(partner_b.id),
    }

    resp_a = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "receipt_code": "HD-CROSS"},
        headers=headers_a,
    )
    assert resp_a.status_code == 201

    resp_b = await client.post(
        "/partner/transactions",
        json={"phone": "0901234568", "gross_amount": 60000, "receipt_code": "HD-CROSS"},
        headers=headers_b,
    )
    assert resp_b.status_code == 201


@pytest.mark.asyncio
async def test_create_transaction_receipt_code_too_long_returns_422(client, db_session):
    """receipt_code > 50 ký tự → 422 validation error."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "receipt_code": "X" * 51},
        headers=headers,
    )
    assert resp.status_code == 422
