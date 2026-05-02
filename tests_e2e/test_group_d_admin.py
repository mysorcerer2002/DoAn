"""Nhóm D — Quản trị và kiểm toán (TC-D01..D07) — QT8."""

import secrets

import pytest

from .conftest import db_exec


@pytest.fixture
def target_user(http):
    """Tạo customer mới làm victim test khoá."""
    email = f"target+{secrets.token_hex(4)}@e2e.vn"
    phone = f"09{secrets.randbelow(10**8):08d}"
    r = http("POST", "/auth/register", body={
        "email": email, "phone": phone,
        "password": "victim1234", "full_name": "Target",
    })
    token = r.json()["access_token"]
    r2 = http("GET", "/auth/me", token=token)
    return {
        "id": r2.json()["id"],
        "email": email,
        "phone": phone,
        "password": "victim1234",
    }


def test_d01_admin_lock_user(http, admin_token, target_user):
    """TC-D01: Admin lock user kèm reason → 200 + audit log có before/after + reason."""
    reason = "Khoá test E2E - vi phạm điều khoản"
    r = http("PATCH", f"/admin/users/{target_user['id']}",
             body={"is_active": False, "reason": reason},
             token=admin_token)
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is False
    # Verify audit log
    r2 = http("GET", f"/admin/audit-logs?action=user_lock&target_id={target_user['id']}",
              token=admin_token)
    items = r2.json()["items"]
    assert len(items) >= 1, "Audit log thiếu entry user_lock"
    entry = items[0]
    assert entry["reason"] == reason
    assert entry["before_snapshot"]["is_active"] is True
    assert entry["after_snapshot"]["is_active"] is False


def test_d02_user_khoa_dang_nhap(http, admin_token, target_user):
    """TC-D02: User đã khoá cố đăng nhập → 401."""
    # Lock user trước
    http("PATCH", f"/admin/users/{target_user['id']}",
         body={"is_active": False, "reason": "Test D02"},
         token=admin_token)
    # Login → 401
    r = http("POST", "/auth/login",
             body={"identifier": target_user["email"], "password": target_user["password"]})
    assert r.status_code == 401, f"User khoá login expected 401, got {r.status_code}"


def test_d03_admin_unlock_user(http, admin_token, target_user):
    """TC-D03: Admin unlock user kèm reason → 200 + audit log mới."""
    # Lock + unlock
    http("PATCH", f"/admin/users/{target_user['id']}",
         body={"is_active": False, "reason": "Khoá tạm"},
         token=admin_token)
    r = http("PATCH", f"/admin/users/{target_user['id']}",
             body={"is_active": True, "reason": "Mở khoá sau xác minh"},
             token=admin_token)
    assert r.status_code == 200
    assert r.json()["is_active"] is True
    # Verify audit log unlock
    r2 = http("GET", f"/admin/audit-logs?action=user_unlock&target_id={target_user['id']}",
              token=admin_token)
    items = r2.json()["items"]
    assert len(items) >= 1, "Audit log thiếu entry user_unlock"
    assert items[0]["reason"] == "Mở khoá sau xác minh"


def test_d04_tra_cuu_login_logs(http, admin_token, target_user):
    """TC-D04: GET /admin/login-logs filter theo identifier → 200 + list đúng."""
    # Trigger 1 login attempt cho target để có log
    http("POST", "/auth/login",
         body={"identifier": target_user["email"], "password": target_user["password"]})
    r = http("GET", f"/admin/login-logs?identifier={target_user['email']}&limit=20",
             token=admin_token)
    assert r.status_code == 200, r.text
    assert "items" in r.json()
    assert "total" in r.json()


def test_d05_tra_cuu_point_adjustments(http, admin_token):
    """TC-D05: GET /admin/point-adjustments → 200 + items list."""
    r = http("GET", "/admin/point-adjustments?limit=10", token=admin_token)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data


def test_d06_tra_cuu_audit_logs(http, admin_token):
    """TC-D06: GET /admin/audit-logs → 200 + entries có before/after snapshot."""
    r = http("GET", "/admin/audit-logs?limit=20", token=admin_token)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data["items"]
    assert len(items) >= 1, "Audit log có ít nhất 1 entry (test trước đã ghi)"
    has_snapshots = [it for it in items if it.get("before_snapshot") and it.get("after_snapshot")]
    assert len(has_snapshots) >= 1, "Có entry với cả before+after snapshot"


def test_d07_xem_audit_feed(http, admin_token):
    """TC-D07: GET /admin/audit-feed → 200 + list events gần đây."""
    r = http("GET", "/admin/audit-feed?limit=20", token=admin_token)
    assert r.status_code == 200, r.text
    events = r.json()
    assert isinstance(events, list)
    # Sample events có mặt (sau các test trước)
    assert len(events) >= 1, "Audit feed có ít nhất 1 sự kiện gần đây"
