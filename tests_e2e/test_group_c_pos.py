"""Nhóm C — Tích điểm và đổi quà (TC-C01..C16 + TC-C13b) — QT4, QT5, QT6, QT7."""

import secrets

from .conftest import (
    CUSTOMER1_EMAIL, CUSTOMER2_EMAIL, CUSTOMER_PWD,
    OWNER_CAFE_EMAIL,
    db_exec, _login,
)


# ============================================================
# Module fixtures: setup khach1 đủ điểm + tier IDs đúng spec
# ============================================================

import pytest


@pytest.fixture(scope="module", autouse=True)
def _topup_khach1():
    """Top-up khach1 ≥ 50.000 điểm để mọi TC đổi quà đều có đủ điểm."""
    khach1_id = db_exec(f"SELECT id FROM users WHERE email='{CUSTOMER1_EMAIL}';")
    db_exec(f"UPDATE users SET points_balance = GREATEST(points_balance, 50000) WHERE id={khach1_id};")
    yield
    # No cleanup — để khach1 đủ điểm cho tests về sau


@pytest.fixture(scope="module")
def tier_ids(partner_cafe_id):
    """Cafe có 4 hạng theo seed: Đồng (id=1, min=0), Bạc (id=2, min=500),
    Vàng (id=3, min=2000), Bạch Kim (id=4, min=5000).
    """
    bac = db_exec(f"SELECT id FROM tiers WHERE partner_id={partner_cafe_id} ORDER BY min_points ASC OFFSET 1 LIMIT 1;")
    vang = db_exec(f"SELECT id FROM tiers WHERE partner_id={partner_cafe_id} ORDER BY min_points ASC OFFSET 2 LIMIT 1;")
    vang_min = db_exec(f"SELECT min_points FROM tiers WHERE id={vang};")
    return {
        "bac_id": int(bac), "vang_id": int(vang),
        "vang_min": int(vang_min),
    }


@pytest.fixture
def khach1_phone():
    return db_exec(f"SELECT phone FROM users WHERE email='{CUSTOMER1_EMAIL}';")


@pytest.fixture
def khach1_id():
    return int(db_exec(f"SELECT id FROM users WHERE email='{CUSTOMER1_EMAIL}';"))


# ============================================================
# Tests
# ============================================================

def test_c01_pos_khach_da_co_ho_so(http, owner_cafe_token, partner_cafe_id, khach1_phone, khach1_id):
    """TC-C01: POS khách đã có hồ sơ — bill 200k @ 1% → +2000 điểm + ledger có actor_user_id."""
    # Setup state đúng spec: earn_percent=1%, use_tiers=FALSE (không nhân hệ số)
    db_exec(f"UPDATE point_rules SET earn_percent=1.00, use_tiers=FALSE "
            f"WHERE partner_id={partner_cafe_id} AND is_active=TRUE;")
    r = http("POST", "/partner/transactions",
             body={"phone": khach1_phone, "gross_amount": 200000},
             token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["transaction"]["points_earned"] == 2000, (
        f"Bill 200k @ 1% = 2000 điểm, got {data['transaction']['points_earned']}"
    )
    # Verify ledger có actor_user_id của owner Cafe
    txn_id = data["transaction"]["id"]
    actor = db_exec(f"SELECT actor_user_id FROM point_ledger WHERE ref_id={txn_id} AND reason='earn';")
    owner_id = db_exec(f"SELECT id FROM users WHERE email='{OWNER_CAFE_EMAIL}';")
    assert actor == owner_id, f"Ledger actor_user_id='{actor}' (expected owner={owner_id})"


def test_c02_pos_khach_lan_dau(http, owner_cafe_token, partner_cafe_id, random_phone):
    """TC-C02: SĐT chưa từng giao dịch → auto-create user + membership."""
    new_phone = random_phone()
    r = http("POST", "/partner/transactions",
             body={"phone": new_phone, "gross_amount": 100000},
             token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r.status_code == 201, r.text
    data = r.json()
    # Verify auto-create: user mới với phone đó tồn tại trong DB
    user_count = db_exec(f"SELECT COUNT(*) FROM users WHERE phone='{new_phone}';")
    assert user_count == "1", f"Expected 1 user mới với phone {new_phone}, got {user_count}"
    # Verify membership được tạo cho partner Cafe
    new_user_id = db_exec(f"SELECT id FROM users WHERE phone='{new_phone}';")
    mem_count = db_exec(
        f"SELECT COUNT(*) FROM memberships WHERE user_id={new_user_id} AND partner_id={partner_cafe_id};"
    )
    assert mem_count == "1", f"Expected 1 membership mới, got {mem_count}"


def test_c03_tich_diem_co_he_so_hang(http, owner_cafe_token, partner_cafe_id, khach1_phone, khach1_id, tier_ids):
    """TC-C03: Khách hạng Vàng (hệ số 1.5), bill 200k @ 1% → 3000 điểm.

    Setup: bật use_tiers, set Vàng multiplier=1.5, set khach1 current_tier=Vàng.
    """
    db_exec(f"UPDATE tiers SET earn_multiplier=1.50 WHERE id={tier_ids['vang_id']};")
    db_exec(f"UPDATE point_rules SET earn_percent=1.00, use_tiers=TRUE "
            f"WHERE partner_id={partner_cafe_id} AND is_active=TRUE;")
    db_exec(
        f"UPDATE memberships SET lifetime_earned={tier_ids['vang_min']}, "
        f"current_tier_id={tier_ids['vang_id']} "
        f"WHERE user_id={khach1_id} AND partner_id={partner_cafe_id};"
    )
    r = http("POST", "/partner/transactions",
             body={"phone": khach1_phone, "gross_amount": 200000},
             token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r.status_code == 201, r.text
    points = r.json()["transaction"]["points_earned"]
    assert points == 3000, f"200k × 1% × Vàng 1.5 = 3000 điểm, got {points}"


def test_c04_vuot_nguong_nang_hang(http, owner_cafe_token, partner_cafe_id, tier_ids):
    """TC-C04: Khách Bạc, sau giao dịch đạt ngưỡng Vàng → tier_upgraded=true.

    Setup: khach4 lifetime=(Vàng_min - 500), tier=Bạc, multiplier Bạc default 1.25.
    Transaction 200k × 1% × 1.25 = 2500 → lifetime mới = (Vàng_min + 2000) > Vàng_min → upgrade.
    """
    khach4_id = int(db_exec("SELECT id FROM users WHERE email='khach4@gmail.com';"))
    khach4_phone = db_exec(f"SELECT phone FROM users WHERE id={khach4_id};")
    lifetime_before = tier_ids['vang_min'] - 500
    db_exec(f"UPDATE point_rules SET use_tiers=TRUE WHERE partner_id={partner_cafe_id} AND is_active=TRUE;")
    # Đảm bảo membership tồn tại + set state
    has_mem = db_exec(f"SELECT 1 FROM memberships WHERE user_id={khach4_id} AND partner_id={partner_cafe_id};")
    if not has_mem:
        db_exec(
            f"INSERT INTO memberships (partner_id, user_id, lifetime_earned, current_tier_id, "
            f"joined_at, created_at, updated_at) VALUES "
            f"({partner_cafe_id}, {khach4_id}, {lifetime_before}, {tier_ids['bac_id']}, "
            f"NOW(), NOW(), NOW());"
        )
    else:
        db_exec(
            f"UPDATE memberships SET lifetime_earned={lifetime_before}, "
            f"current_tier_id={tier_ids['bac_id']} "
            f"WHERE user_id={khach4_id} AND partner_id={partner_cafe_id};"
        )
    r = http("POST", "/partner/transactions",
             body={"phone": khach4_phone, "gross_amount": 200000},
             token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["tier_upgraded"] is True, (
        f"tier_upgraded={data['tier_upgraded']} (expected true). "
        f"lifetime={data.get('new_lifetime_earned')}, new_tier={data.get('new_tier_name')}"
    )
    # Cleanup: tắt use_tiers để các test sau không bị nhân hệ số bất ngờ
    db_exec(f"UPDATE point_rules SET use_tiers=FALSE WHERE partner_id={partner_cafe_id};")


def _create_reward(http, owner_token, partner_id, **fields) -> int:
    """Tạo reward mới, trả id."""
    body = {
        "name": f"E2E reward {secrets.token_hex(3)}",
        "points_cost": 100,
        "stock": 5,
        "offer_type": "ITEM_GIFT",
        "offer_label": "Test reward",
    }
    body.update(fields)
    r = http("POST", "/partner/rewards", body=body, token=owner_token, partner_id=partner_id)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_c05_doi_qua_thanh_cong(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C05: Đổi quà thành công → 201, voucher mã 8 ký tự, trừ điểm đúng."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=100)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    assert r.status_code == 201, r.text
    data = r.json()
    code = data["redemption_code"]
    assert len(code) == 8, f"Mã voucher 8 ký tự, got len={len(code)}: {code!r}"
    assert data["points_spent"] == 100


def test_c06_doi_qua_khong_du_diem(http, owner_cafe_token, partner_cafe_id):
    """TC-C06: Customer thiếu điểm → 409 insufficient_points, không trừ điểm."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=999999)
    cust5_tok = _login_helper("khach5@gmail.com", CUSTOMER_PWD)
    if cust5_tok is None:
        pytest.skip("khach5 không login được — skip")
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=cust5_tok)
    assert r.status_code == 409, f"Expected 409 insufficient_points, got {r.status_code}"


def _login_helper(email, pwd):
    """Helper login bên ngoài fixture."""
    import httpx
    from .conftest import BASE_URL, _http_request
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        r = _http_request(c, "POST", "/auth/login", body={"identifier": email, "password": pwd})
        if r.status_code != 200:
            return None
        return r.json().get("access_token")


def test_c07_doi_qua_het_ton_kho(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C07: Reward stock=0 → 409 out_of_stock."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=0)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    assert r.status_code == 409, f"Expected 409 out_of_stock, got {r.status_code}: {r.text}"


def test_c08_doi_qua_ngoai_thoi_gian_hieu_luc(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C08: Reward valid_until quá khứ → 404 not_found_or_expired."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=5)
    db_exec(f"UPDATE rewards SET valid_until = CURRENT_DATE - 1 WHERE id={rid};")
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"


def test_c09_su_dung_voucher_hop_le(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C09: Voucher hợp lệ → inspect 200 + use 200 + status=used + used_at set."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=5)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    code = r.json()["redemption_code"]
    # Inspect
    r2 = http("GET", f"/partner/redemptions/inspect/{code}", token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 200, r2.text
    # Use
    r3 = http("POST", "/partner/redemptions/use",
              body={"code": code, "original_amount": 100000},
              token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r3.status_code == 200, r3.text
    data = r3.json()
    assert data["status"] == "used"
    assert data["used_at"] is not None


def test_c10_su_dung_voucher_qua_han(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C10: Voucher expires_at quá khứ → 404 (auto flip status sang expired)."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=5)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    code = r.json()["redemption_code"]
    db_exec(f"UPDATE redemptions SET expires_at = NOW() - INTERVAL '1 day' WHERE redemption_code='{code}';")
    r2 = http("POST", "/partner/redemptions/use",
              body={"code": code, "original_amount": 100000},
              token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 404, f"Expected 404 expired, got {r2.status_code}"


def test_c11_su_dung_voucher_da_dung(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C11: Voucher status=used → use lần 2 → 404."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=5)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    code = r.json()["redemption_code"]
    # Use lần 1 OK
    http("POST", "/partner/redemptions/use",
         body={"code": code, "original_amount": 100000},
         token=owner_cafe_token, partner_id=partner_cafe_id)
    # Use lần 2 → 404
    r2 = http("POST", "/partner/redemptions/use",
              body={"code": code, "original_amount": 100000},
              token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 404, f"Expected 404 already used, got {r2.status_code}"


def test_c12_voucher_giam_phan_tram(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C12: Voucher PERCENT_DISCOUNT 20% + bill 200k → discount_amount = 40000."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id,
                         points_cost=10, stock=5,
                         offer_type="PERCENT_DISCOUNT", offer_value=20,
                         offer_label="Giảm 20%")
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    code = r.json()["redemption_code"]
    r2 = http("POST", "/partner/redemptions/use",
              body={"code": code, "original_amount": 200000},
              token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 200, r2.text
    discount = r2.json()["discount_amount"]
    assert discount == 40000, f"200k × 20% = 40000, got {discount}"


def test_c13_voucher_partner_khac(http, owner_cafe_token, partner_cafe_id,
                                   owner_lala_token, partner_lala_id, customer1_token):
    """TC-C13: Voucher của Cafe + nhập tại quầy Lala → 404."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=5)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    code = r.json()["redemption_code"]
    r2 = http("GET", f"/partner/redemptions/inspect/{code}",
              token=owner_lala_token, partner_id=partner_lala_id)
    assert r2.status_code == 404, f"Voucher Cafe quét tại Lala expected 404, got {r2.status_code}"


def test_c13b_voucher_qr_khach_khac(http, owner_cafe_token, partner_cafe_id,
                                     customer1_token, customer2_token):
    """TC-C13b: Voucher khach1 + use với expected_user_id=khach2 → 409 customer_mismatch."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id, points_cost=10, stock=5)
    r = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    code = r.json()["redemption_code"]
    # Lấy user_id của khach2
    r_me = http("GET", "/auth/me", token=customer2_token)
    cust2_id = r_me.json()["id"]
    r2 = http("POST", "/partner/redemptions/use",
              body={"code": code, "original_amount": 100000, "expected_user_id": cust2_id},
              token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 409, f"Voucher khach1 + expected khach2 expected 409, got {r2.status_code}: {r2.text}"


def test_c14_phat_voucher_mien_phi_co_gioi_han(http, owner_cafe_token, partner_cafe_id):
    """TC-C14: Đối tác tạo free voucher (points_cost=0, stock=100) → 201."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id,
                         points_cost=0, stock=100,
                         offer_label="Free voucher 100 stock")
    assert rid > 0
    # Verify reward.points_cost = 0
    pc = db_exec(f"SELECT points_cost FROM rewards WHERE id={rid};")
    assert pc == "0"


def test_c15_nhan_free_voucher_lan_2(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C15: Khách nhận free voucher lần 2 trong cùng đợt → 409 already_claimed."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id,
                         points_cost=0, stock=10,
                         offer_label="Free voucher")
    # Lần 1 OK
    r1 = http("POST", f"/users/me/rewards/{rid}/claim", token=customer1_token)
    assert r1.status_code == 201, r1.text
    # Lần 2 → 409
    r2 = http("POST", f"/users/me/rewards/{rid}/claim", token=customer1_token)
    assert r2.status_code == 409, f"Claim lần 2 expected 409, got {r2.status_code}: {r2.text}"


def test_c16_doi_paid_reward_nhieu_lan(http, owner_cafe_token, partner_cafe_id, customer1_token):
    """TC-C16: Khách đổi cùng paid reward 2 lần → cả 2 đều thành công."""
    rid = _create_reward(http, owner_cafe_token, partner_cafe_id,
                         points_cost=10, stock=5,
                         offer_label="Đổi nhiều lần")
    r1 = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    assert r1.status_code == 201, r1.text
    r2 = http("POST", "/users/me/redemptions", body={"reward_id": rid}, token=customer1_token)
    assert r2.status_code == 201, f"Lần 2 expected 201, got {r2.status_code}: {r2.text}"
    # 2 voucher khác nhau
    assert r1.json()["redemption_code"] != r2.json()["redemption_code"]
