"""Nhóm A — Xác thực và phân quyền (TC-A01..A10) — QT1."""

import secrets

from .conftest import (
    ADMIN_EMAIL, ADMIN_PWD,
    CUSTOMER1_EMAIL, CUSTOMER2_EMAIL, CUSTOMER_PWD,
    db_exec, restore_user_password, set_temp_password,
    _login,
)


def test_a01_dang_ky_hop_le(http, random_email, random_phone):
    """TC-A01: Đăng ký tài khoản hợp lệ → 201, status active."""
    r = http("POST", "/auth/register", body={
        "email": random_email(),
        "phone": random_phone(),
        "password": "e2etest1234",
        "full_name": "Test User",
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert "access_token" in data, "Response thiếu access_token"
    assert data.get("token_type") == "bearer"


def test_a02_dang_ky_email_trung(http, random_email, random_phone):
    """TC-A02: Email đã tồn tại → 409 Conflict, không tạo bản ghi."""
    email = random_email()
    # Đăng ký lần 1
    r1 = http("POST", "/auth/register", body={
        "email": email, "phone": random_phone(),
        "password": "test1234", "full_name": "First",
    })
    assert r1.status_code == 201
    # Đăng ký lần 2 cùng email
    r2 = http("POST", "/auth/register", body={
        "email": email, "phone": random_phone(),
        "password": "another1234", "full_name": "Second",
    })
    assert r2.status_code == 409, f"Expected 409, got {r2.status_code}: {r2.text}"


def test_a03a_dang_nhap_bang_email(http_client):
    """TC-A03a: Đăng nhập bằng email + mật khẩu đúng → cấp JWT access_token."""
    tok = _login(http_client, CUSTOMER1_EMAIL, CUSTOMER_PWD)
    assert tok is not None, "Login đúng pwd nhưng không trả token"
    assert len(tok) > 50, f"Token nghi vấn ngắn bất thường: len={len(tok)}"


def test_a03b_dang_nhap_bang_phone(http_client):
    """TC-A03b: Đăng nhập bằng SĐT + mật khẩu đúng → cấp JWT access_token.

    Backend dispatcher: identifier chứa '@' → tìm theo email; ngược lại → tìm
    theo phone (auth_service.AuthService.authenticate).
    """
    phone = db_exec(f"SELECT phone FROM users WHERE email='{CUSTOMER1_EMAIL}';")
    assert phone, f"Không lấy được phone của {CUSTOMER1_EMAIL}"
    tok = _login(http_client, phone, CUSTOMER_PWD)
    assert tok is not None, f"Login bằng SĐT {phone} không trả token"
    assert len(tok) > 50


def test_a04_dang_nhap_sai_pwd(http):
    """TC-A04: Email/SĐT đúng + mật khẩu sai → 401, không cấp token."""
    r = http("POST", "/auth/login", body={
        "identifier": CUSTOMER1_EMAIL, "password": "wrong-password-123",
    })
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    assert "access_token" not in r.text


def test_a05_quen_mat_khau(http):
    """TC-A05: Quên mật khẩu → 200 idempotent + must_change_password=TRUE.

    Cleanup: restore khach2 password để các TC sau dùng được.
    """
    r = http("POST", "/auth/forgot-password", body={"email": CUSTOMER2_EMAIL})
    assert r.status_code == 200, f"Forgot password phải idempotent 200, got {r.status_code}"
    # Verify side-effect: must_change_password=TRUE
    flag = db_exec(f"SELECT must_change_password FROM users WHERE email='{CUSTOMER2_EMAIL}';")
    assert flag == "t", f"Expected must_change_password=TRUE, got '{flag}'"
    # Cleanup
    restore_user_password(CUSTOMER2_EMAIL, CUSTOMER_PWD)


def test_a06_truy_cap_khi_buoc_doi_pwd(http, http_client):
    """TC-A06: Login với temp pwd → call API tích điểm → 423 password_change_required."""
    target = "khach3@gmail.com"
    temp_pwd = "tempABC123!"
    set_temp_password(target, temp_pwd)
    try:
        token = _login(http_client, target, temp_pwd)
        assert token is not None, "Login với temp pwd phải thành công"
        r = http("GET", "/users/me/memberships", token=token)
        assert r.status_code == 423, f"Expected 423 LOCKED, got {r.status_code}"
        assert r.json().get("detail") == "password_change_required"
    finally:
        restore_user_password(target, CUSTOMER_PWD)


def test_a07_doi_mat_khau_va_truy_cap_lai(http, http_client):
    """TC-A07: Đổi mật khẩu → 204 → API tích điểm trả 200."""
    target = "khach3@gmail.com"
    temp_pwd = "tempABC123!"
    new_pwd = "newpass4567!"
    set_temp_password(target, temp_pwd)
    try:
        token = _login(http_client, target, temp_pwd)
        # Đổi mật khẩu
        r1 = http("PATCH", "/auth/me/password",
                  body={"current_password": temp_pwd, "new_password": new_pwd},
                  token=token)
        assert r1.status_code == 204, f"Đổi pwd expected 204, got {r1.status_code}: {r1.text}"
        # Sau đó gọi API khác → 200 (flag đã clear)
        r2 = http("GET", "/users/me/memberships", token=token)
        assert r2.status_code == 200, f"Sau đổi pwd expected 200, got {r2.status_code}"
        # Verify flag đã clear
        flag = db_exec(f"SELECT must_change_password FROM users WHERE email='{target}';")
        assert flag == "f", f"Sau đổi pwd, flag phải FALSE, got '{flag}'"
    finally:
        restore_user_password(target, CUSTOMER_PWD)


def test_a08_super_admin_skip_buoc_doi(http, http_client):
    """TC-A08: Super admin loại trừ khỏi cơ chế must_change_password.

    Verify 2 việc:
    1. Forgot password cho admin → KHÔNG set must_change_password (super_admin SKIP)
    2. Admin login với pwd hiện tại → API admin trả 200, không bị 423
    """
    # Force flag=FALSE rồi gọi forgot-password
    db_exec(f"UPDATE users SET must_change_password=FALSE WHERE email='{ADMIN_EMAIL}';")
    http("POST", "/auth/forgot-password", body={"email": ADMIN_EMAIL})
    flag = db_exec(f"SELECT must_change_password FROM users WHERE email='{ADMIN_EMAIL}';")
    assert flag == "f", f"super_admin SKIP — flag phải FALSE, got '{flag}'"
    # Restore admin pwd (vì forgot-password đã đổi pwd)
    restore_user_password(ADMIN_EMAIL, ADMIN_PWD)
    # Admin login + call /admin/stats → 200
    tok = _login(http_client, ADMIN_EMAIL, ADMIN_PWD)
    assert tok is not None, "Admin login fail sau restore pwd"
    r = http("GET", "/admin/stats", token=tok)
    assert r.status_code == 200, f"Admin /admin/stats expected 200, got {r.status_code}"


def test_a09_khach_truy_cap_admin_api(http, customer1_token):
    """TC-A09: Customer token → endpoint admin → 403 Forbidden."""
    r = http("GET", "/admin/stats", token=customer1_token)
    assert r.status_code == 403, f"Customer → /admin/stats expected 403, got {r.status_code}"


def test_a10_owner_a_truy_cap_pos_b(http, owner_cafe_token, partner_lala_id):
    """TC-A10: Owner Cafe → POS endpoint của Lala (X-Partner-Id=Lala) → 403."""
    r = http("POST", "/partner/transactions",
             body={"phone": "0901234567", "gross_amount": 50000},
             token=owner_cafe_token, partner_id=partner_lala_id)
    assert r.status_code == 403, (
        f"Owner Cafe → POS Lala expected 403, got {r.status_code}: {r.text[:200]}"
    )
