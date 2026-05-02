"""Nhóm B — Vòng đời đối tác (TC-B01..B10) — QT2, QT3."""

import secrets

from .conftest import (
    OWNER_CAFE_EMAIL, OWNER_CAFE_PWD,
    db_exec, _login,
)


def _make_owner_token(http, http_client, random_email, random_phone) -> str:
    """Helper: tạo customer mới + login → token để đăng ký partner."""
    email = random_email()
    phone = random_phone()
    r = http("POST", "/auth/register", body={
        "email": email, "phone": phone,
        "password": "e2etest1234", "full_name": "E2E Owner",
    })
    assert r.status_code == 201
    return r.json()["access_token"]


def test_b01_dang_ky_partner_hop_le(http, http_client, random_email, random_phone):
    """TC-B01: Đăng ký đối tác hợp lệ → 201 pending, lưu terms_version + terms_accepted_at."""
    owner_tok = _make_owner_token(http, http_client, random_email, random_phone)
    body = {
        "name": f"E2E Shop {secrets.token_hex(3)}",
        "category": "cafe",
        "description": "E2E test shop",
        "contact_phone": "0900000001",
        "contact_email": "shop@e2e.vn",
        "address": "1 Street, HCM",
        "tax_code": "0123456789",
        "business_license_url": "/api/uploads/licenses/0/dummy.png",
        "accept_terms": True,
        "terms_version": "v1.0",
    }
    r = http("POST", "/partner/register", body=body, token=owner_tok)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["status"] == "pending", f"Status phải pending, got {data['status']}"
    # Verify side-effect: DB lưu terms_version + accepted_at
    pid = data["id"]
    row = db_exec(f"SELECT terms_version, terms_accepted_at FROM partners WHERE id={pid};")
    assert "v1.0" in row, f"DB không lưu terms_version='v1.0', got: {row}"


def test_b02_dang_ky_partner_thieu_giay_phep(http, http_client, random_email, random_phone):
    """TC-B02: Bỏ trống business_license_url → 422 Unprocessable Entity."""
    owner_tok = _make_owner_token(http, http_client, random_email, random_phone)
    r = http("POST", "/partner/register", body={
        "name": f"Bad Shop {secrets.token_hex(3)}",
        "category": "cafe",
        "accept_terms": True,
        "terms_version": "v1.0",
        # Thiếu business_license_url
    }, token=owner_tok)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"


def test_b03_admin_phe_duyet(http, admin_token, http_client, random_email, random_phone):
    """TC-B03: Admin approve → 200 active, last_status_reason lưu lý do."""
    owner_tok = _make_owner_token(http, http_client, random_email, random_phone)
    r = http("POST", "/partner/register", body={
        "name": f"Approve Shop {secrets.token_hex(3)}", "category": "cafe",
        "business_license_url": "/api/uploads/licenses/0/dummy.png",
        "accept_terms": True, "terms_version": "v1.0",
    }, token=owner_tok)
    pid = r.json()["id"]
    r2 = http("POST", f"/admin/partners/{pid}/approve",
              body={"approve": True, "reason": "Hồ sơ đầy đủ, duyệt"},
              token=admin_token)
    assert r2.status_code == 200, f"Approve expected 200, got {r2.status_code}"
    assert r2.json()["status"] == "active"
    # Verify DB lưu reason
    reason = db_exec(f"SELECT last_status_reason FROM partners WHERE id={pid};")
    assert reason == "Hồ sơ đầy đủ, duyệt", f"DB lưu reason '{reason}'"


def test_b04_admin_tu_choi(http, admin_token, http_client, random_email, random_phone):
    """TC-B04: Admin reject (approve=false) → 200 suspended, lưu lý do."""
    owner_tok = _make_owner_token(http, http_client, random_email, random_phone)
    r = http("POST", "/partner/register", body={
        "name": f"Reject Shop {secrets.token_hex(3)}", "category": "food",
        "business_license_url": "/api/uploads/licenses/0/dummy.png",
        "accept_terms": True, "terms_version": "v1.0",
    }, token=owner_tok)
    pid = r.json()["id"]
    r2 = http("POST", f"/admin/partners/{pid}/approve",
              body={"approve": False, "reason": "Giấy phép giả"},
              token=admin_token)
    assert r2.status_code == 200
    status = r2.json()["status"]
    assert status in ("suspended", "rejected"), f"Status sau reject: {status}"
    reason = db_exec(f"SELECT last_status_reason FROM partners WHERE id={pid};")
    assert reason == "Giấy phép giả"


def test_b05_partner_pending_truy_cap_endpoint_active(http, http_client, random_email, random_phone):
    """TC-B05: Partner trạng thái pending → /partners/me → 403."""
    owner_tok = _make_owner_token(http, http_client, random_email, random_phone)
    r = http("POST", "/partner/register", body={
        "name": f"Pending Shop {secrets.token_hex(3)}", "category": "cafe",
        "business_license_url": "/api/uploads/licenses/0/dummy.png",
        "accept_terms": True, "terms_version": "v1.0",
    }, token=owner_tok)
    pid = r.json()["id"]
    # Owner gọi /partners/me với X-Partner-Id của partner pending → 403
    r2 = http("GET", "/partners/me", token=owner_tok, partner_id=pid)
    assert r2.status_code == 403, f"Pending partner /partners/me expected 403, got {r2.status_code}"


def test_b06_admin_suspend_active_partner(http, admin_token, partner_cafe_id):
    """TC-B06: Admin suspend partner active → 200 + audit log có before/after + reason.

    Cleanup: bỏ qua restore active state vì có thể ảnh hưởng test khác.
    Test dùng partner mới tạo riêng (không động partner_cafe_id).
    """
    # Tạo partner mới + approve để đảm bảo state active sạch
    r = http("POST", "/auth/register", body={
        "email": f"e2e-b06+{secrets.token_hex(3)}@test.vn",
        "phone": f"09{secrets.randbelow(10**8):08d}",
        "password": "test1234", "full_name": "B06 Owner",
    })
    new_owner = r.json()["access_token"]
    r = http("POST", "/partner/register", body={
        "name": f"B06 Shop {secrets.token_hex(3)}", "category": "cafe",
        "business_license_url": "/api/uploads/licenses/0/dummy.png",
        "accept_terms": True, "terms_version": "v1.0",
    }, token=new_owner)
    pid = r.json()["id"]
    http("POST", f"/admin/partners/{pid}/approve",
         body={"approve": True, "reason": "OK"}, token=admin_token)
    # Suspend
    reason = "Vi phạm điều khoản dịch vụ E2E"
    r2 = http("POST", f"/admin/partners/{pid}/suspend",
              body={"reason": reason}, token=admin_token)
    assert r2.status_code == 200, f"Suspend expected 200, got {r2.status_code}"
    assert r2.json()["status"] == "suspended"
    # Verify audit log
    r3 = http("GET", f"/admin/audit-logs?action=partner_suspend&target_id={pid}",
              token=admin_token)
    items = r3.json().get("items", [])
    assert len(items) >= 1, "Audit log thiếu entry partner_suspend"
    entry = items[0]
    assert entry["reason"] == reason
    assert entry["before_snapshot"]["status"] == "active"
    assert entry["after_snapshot"]["status"] == "suspended"


def test_b07_cau_hinh_ty_le_tich_diem(http, owner_cafe_token, partner_cafe_id):
    """TC-B07: Cập nhật earn_percent của point_rule → 200 + giá trị lưu chính xác."""
    # Get current rule
    r = http("GET", "/partner/point-rules/active", token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r.status_code == 200
    rule = r.json()
    assert rule is not None, "Cafe phải có active point_rule (seeded)"
    # PATCH earn_percent = 1.00
    r2 = http("PATCH", f"/partner/point-rules/{rule['id']}",
              body={"earn_percent": 1.0},
              token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 200, r2.text
    updated = r2.json()
    # earn_percent có thể trả string "1.00" hoặc number 1.0 — chấp nhận cả 2
    ep = updated["earn_percent"]
    assert str(ep) in ("1.0", "1.00"), f"earn_percent = {ep}"


def test_b08_cau_hinh_hang_thanh_vien(http, owner_cafe_token, partner_cafe_id):
    """TC-B08: Cafe có ≥3 hạng thành viên với ngưỡng + hệ số khác nhau."""
    r = http("GET", "/partner/tiers", token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r.status_code == 200, r.text
    tiers = r.json()
    assert len(tiers) >= 3, f"Cần ≥3 hạng (Đồng/Bạc/Vàng), thấy {len(tiers)}"
    multipliers = {float(t["earn_multiplier"]) for t in tiers}
    assert len(multipliers) > 1, f"Các hạng phải có hệ số khác nhau, thấy {multipliers}"


def test_b09_bat_use_tiers(http, owner_cafe_token, partner_cafe_id):
    """TC-B09: PATCH use_tiers=True → response trả use_tiers=true."""
    r = http("GET", "/partner/point-rules/active", token=owner_cafe_token, partner_id=partner_cafe_id)
    rule_id = r.json()["id"]
    r2 = http("PATCH", f"/partner/point-rules/{rule_id}",
              body={"use_tiers": True}, token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 200
    assert r2.json()["use_tiers"] is True


def test_b10_tat_use_tiers(http, owner_cafe_token, partner_cafe_id):
    """TC-B10: PATCH use_tiers=False → response trả use_tiers=false."""
    r = http("GET", "/partner/point-rules/active", token=owner_cafe_token, partner_id=partner_cafe_id)
    rule_id = r.json()["id"]
    r2 = http("PATCH", f"/partner/point-rules/{rule_id}",
              body={"use_tiers": False}, token=owner_cafe_token, partner_id=partner_cafe_id)
    assert r2.status_code == 200
    assert r2.json()["use_tiers"] is False
