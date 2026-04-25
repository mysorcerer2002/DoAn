import pytest

from app.core.security import create_access_token
from app.models.point_rule import PointRule
from app.models.partner import Partner, PartnerStatus
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
    """Tạo 2 giao dịch rồi list ra đúng số lượng — response shape mới paginated."""
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
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1


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
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


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


@pytest.mark.asyncio
async def test_create_transaction_null_receipt_code_allows_duplicates_same_partner(
    client, db_session
):
    """Partial index WHERE receipt_code IS NOT NULL — hai transaction cùng partner
    không gửi receipt_code đều 201, không bị 409."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp1 = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 10000},
        headers=headers,
    )
    assert resp1.status_code == 201
    assert resp1.json()["transaction"]["receipt_code"] is None

    resp2 = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 20000},
        headers=headers,
    )
    assert resp2.status_code == 201
    assert resp2.json()["transaction"]["receipt_code"] is None


@pytest.mark.asyncio
async def test_create_transaction_concurrent_same_receipt_code_one_409(
    client, db_session
):
    """TOCTOU-safety: hai POST đồng thời cùng receipt_code → đúng 1×201 + 1×409.
    Partial unique index + IntegrityError handler đảm bảo không cả hai đều insert."""
    import asyncio

    _partner, _owner, headers = await _setup_shop_with_rule(db_session)
    payload = {
        "phone": "0901234567",
        "gross_amount": 30000,
        "receipt_code": "HD-RACE",
    }

    r1, r2 = await asyncio.gather(
        client.post("/partner/transactions", json=payload, headers=headers),
        client.post("/partner/transactions", json=payload, headers=headers),
        return_exceptions=True,
    )
    statuses = sorted(
        getattr(r, "status_code", 500) for r in (r1, r2)
    )
    assert statuses == [201, 409]


# ── C2: GET list paginated / detail / PATCH ───────────────────────────────────


async def _create_txn(client, headers, phone="0901234567", amount=10000, receipt_code=None):
    """Helper nhỏ: tạo 1 giao dịch, trả về response JSON."""
    payload = {"phone": phone, "gross_amount": amount}
    if receipt_code is not None:
        payload["receipt_code"] = receipt_code
    resp = await client.post("/partner/transactions", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_list_transactions_pagination(client, db_session):
    """50 giao dịch, GET ?page=1&page_size=20 → total=50, items=20."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    for i in range(50):
        # Dùng phone khác nhau để tránh cùng membership, nhưng format VN hợp lệ
        # 10 số bắt đầu 09
        phone = f"090{i:07d}"
        await _create_txn(client, headers, phone=phone, amount=10000)

    resp = await client.get("/partner/transactions?page=1&page_size=20", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 50
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 20


@pytest.mark.asyncio
async def test_list_filter_by_staff(client, db_session):
    """Filter ?staff_id= trả đúng giao dịch của staff đó."""
    partner, owner, headers_owner = await _setup_shop_with_rule(db_session)

    # Tạo staff user B
    staff_b = User(email="staffb@example.com", password_hash="x", is_active=True)
    db_session.add(staff_b)
    await db_session.flush()
    await db_session.flush()

    from app.core.security import create_access_token
    token_b = create_access_token(user_id=staff_b.id)
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Partner-Id": str(partner.id),
    }

    # Owner tạo 1 txn, staff_b tạo 1 txn
    await _create_txn(client, headers_owner, phone="0901111111", amount=10000)
    await _create_txn(client, headers_b, phone="0902222222", amount=20000)

    resp = await client.get(
        f"/partner/transactions?staff_id={staff_b.id}", headers=headers_owner
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_list_cross_partner_isolation(client, db_session):
    """Partner A tạo txn, Partner B GET list → items=[], total=0."""
    _partner_a, _owner_a, headers_a = await _setup_shop_with_rule(db_session)

    owner_b = User(email="partnerb@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    partner_b = Partner(
        name="PartnerB-C2",
        slug="partner-b-c2",
        owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner_b)
    await db_session.flush()
    from app.models.point_rule import PointRule
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

    from app.core.security import create_access_token
    token_b = create_access_token(user_id=owner_b.id)
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Partner-Id": str(partner_b.id),
    }

    await _create_txn(client, headers_a, phone="0901234567", amount=10000)

    resp = await client.get("/partner/transactions", headers=headers_b)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_detail_includes_note(client, db_session):
    """GET /{id} trả về note trong response detail."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    resp_create = await client.post(
        "/partner/transactions",
        json={"phone": "0901234567", "gross_amount": 50000, "note": "xin chào"},
        headers=headers,
    )
    assert resp_create.status_code == 201
    txn_id = resp_create.json()["transaction"]["id"]

    resp = await client.get(f"/partner/transactions/{txn_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["note"] == "xin chào"
    assert data["id"] == txn_id


@pytest.mark.asyncio
async def test_get_detail_404_other_partner(client, db_session):
    """Partner B GET /{id} của Partner A → 404."""
    partner_a, _owner_a, headers_a = await _setup_shop_with_rule(db_session)

    owner_b = User(email="detail404b@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    partner_b = Partner(
        name="DetailB-404",
        slug="detail-b-404",
        owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner_b)
    await db_session.flush()
    await db_session.flush()

    from app.core.security import create_access_token
    token_b = create_access_token(user_id=owner_b.id)
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Partner-Id": str(partner_b.id),
    }

    txn_data = await _create_txn(client, headers_a, phone="0901234567", amount=10000)
    txn_id = txn_data["transaction"]["id"]

    resp = await client.get(f"/partner/transactions/{txn_id}", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_as_owner_updates_receipt_code(client, db_session):
    """Owner PATCH {receipt_code} → 200, response echo receipt_code."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    txn_data = await _create_txn(client, headers, phone="0901234567", amount=10000)
    txn_id = txn_data["transaction"]["id"]

    resp = await client.patch(
        f"/partner/transactions/{txn_id}",
        json={"receipt_code": "FIXED-001"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["receipt_code"] == "FIXED-001"


@pytest.mark.asyncio
async def test_patch_as_staff_forbidden(client, db_session):
    """Staff (không phải owner) PATCH → 403."""
    partner, owner, headers_owner = await _setup_shop_with_rule(db_session)

    staff_user = User(email="staff403@example.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    await db_session.flush()

    from app.core.security import create_access_token
    token_staff = create_access_token(user_id=staff_user.id)
    headers_staff = {
        "Authorization": f"Bearer {token_staff}",
        "X-Partner-Id": str(partner.id),
    }

    txn_data = await _create_txn(client, headers_owner, phone="0901234567", amount=10000)
    txn_id = txn_data["transaction"]["id"]

    resp = await client.patch(
        f"/partner/transactions/{txn_id}",
        json={"receipt_code": "STAFF-TRY"},
        headers=headers_staff,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_patch_receipt_code_to_null(client, db_session):
    """Owner PATCH {receipt_code: null} → 200, null echo."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    txn_data = await _create_txn(client, headers, phone="0901234567", amount=10000, receipt_code="OLD-CODE")
    txn_id = txn_data["transaction"]["id"]

    resp = await client.patch(
        f"/partner/transactions/{txn_id}",
        json={"receipt_code": None},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["receipt_code"] is None


@pytest.mark.asyncio
async def test_patch_duplicate_receipt_code_409(client, db_session):
    """PATCH txn B để dùng receipt_code của txn A → 409."""
    _partner, _owner, headers = await _setup_shop_with_rule(db_session)

    txn_a = await _create_txn(client, headers, phone="0901111111", amount=10000, receipt_code="AAA")
    txn_b = await _create_txn(client, headers, phone="0902222222", amount=20000, receipt_code="BBB")

    txn_b_id = txn_b["transaction"]["id"]

    resp = await client.patch(
        f"/partner/transactions/{txn_b_id}",
        json={"receipt_code": "AAA"},
        headers=headers,
    )
    assert resp.status_code == 409
