"""Pytest E2E fixtures + helpers cho 34 kịch bản chức năng.

Chạy:
    python -m pytest tests_e2e -v --html=tests_e2e/results/report.html --self-contained-html

Yêu cầu môi trường:
- Backend + Frontend container đang chạy (docker compose -p loyalty-prod up -d)
- Postgres container reachable (mặc định loyalty-postgres-prod)
- Backend container reachable (mặc định loyalty-backend-prod) cho bcrypt_hash helper
- Demo data seeded (backend/seed_demo.py)
- Python 3.10+, pytest 8+, httpx 0.28+, pytest-html
"""

from __future__ import annotations

import os
import secrets
import subprocess
from collections.abc import Callable

import httpx
import pytest

# ============================================================
# Configuration
# ============================================================

BASE_URL = os.getenv("BASE_URL", "http://localhost:3199/api")
PG_CONTAINER = os.getenv("PG_CONTAINER", "loyalty-postgres-prod")
BE_CONTAINER = os.getenv("BE_CONTAINER", "loyalty-backend-prod")

# Demo accounts (seed_demo.py)
ADMIN_EMAIL = "admin@loyalty.vn"
ADMIN_PWD = "admin1234"
OWNER_CAFE_EMAIL = "owner@cafe.vn"
OWNER_CAFE_PWD = "owner1234"
OWNER_LALA_EMAIL = "owner@lala.vn"
OWNER_LALA_PWD = "owner1234"
CUSTOMER1_EMAIL = "khach1@gmail.com"
CUSTOMER2_EMAIL = "khach2@gmail.com"
CUSTOMER_PWD = "khach1234"


# ============================================================
# Random IP để bypass slowapi rate limit per-IP
# ============================================================

def random_ip() -> str:
    """IP ảo random mỗi request — bypass rate limit của slowapi (key theo X-Forwarded-For)."""
    return f"10.{secrets.randbelow(256)}.{secrets.randbelow(256)}.{secrets.randbelow(256)}"


# ============================================================
# DB + container helpers (full automation)
# ============================================================

def db_exec(sql: str) -> str:
    """Execute SQL trong loyalty-postgres-prod, trả output (single value cho SELECT đơn giản)."""
    result = subprocess.run(
        ["docker", "exec", PG_CONTAINER, "psql", "-U", "loyalty", "-d", "loyalty", "-tAc", sql],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip()


def bcrypt_hash(plain: str) -> str:
    """Hash mật khẩu dùng app.core.security.hash_password (bcrypt)."""
    result = subprocess.run(
        ["docker", "exec", BE_CONTAINER, "python", "-c",
         f"from app.core.security import hash_password; print(hash_password({plain!r}))"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip()


def set_temp_password(email: str, pwd: str, *, must_change: bool = True) -> None:
    """Set known temp password + must_change_password flag (skip super_admin tránh lock-out)."""
    h = bcrypt_hash(pwd)
    flag = "TRUE" if must_change else "FALSE"
    db_exec(f"UPDATE users SET password_hash='{h}', must_change_password={flag} WHERE email='{email}';")


def restore_user_password(email: str, pwd: str) -> None:
    """Restore mật khẩu + clear must_change_password (idempotent)."""
    set_temp_password(email, pwd, must_change=False)


# ============================================================
# HTTP client helper với random IP
# ============================================================

def _http_request(
    client: httpx.Client, method: str, path: str,
    body: dict | None = None, token: str | None = None, partner_id: int | None = None,
) -> httpx.Response:
    """HTTP request với random X-Forwarded-For (bypass rate limit) + auth headers."""
    headers: dict[str, str] = {"X-Forwarded-For": random_ip()}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if partner_id is not None:
        headers["X-Partner-Id"] = str(partner_id)
    return client.request(method, path, json=body, headers=headers)


def _login(client: httpx.Client, email: str, pwd: str) -> str | None:
    """Login → JWT token (None nếu fail)."""
    r = _http_request(client, "POST", "/auth/login", body={"identifier": email, "password": pwd})
    if r.status_code != 200:
        return None
    return r.json().get("access_token")


# ============================================================
# Pytest fixtures
# ============================================================

HttpFn = Callable[..., httpx.Response]


@pytest.fixture(scope="session", autouse=True)
def _reset_login_lock():
    """Xoá failed login attempts trong 20 phút gần nhất cho các tài khoản test.

    Tránh `LOCK_THRESHOLD=5 fails / 15 phút` block fixture login đầu suite.
    Áp dụng cho mọi seed account (khach1..5 + admin + owners).
    """
    db_exec(
        "DELETE FROM login_log WHERE success=FALSE AND created_at > NOW() - INTERVAL '20 minutes' "
        "AND identifier IN ('admin@loyalty.vn','owner@cafe.vn','owner@lala.vn',"
        "'khach1@gmail.com','khach2@gmail.com','khach3@gmail.com','khach4@gmail.com','khach5@gmail.com');"
    )
    yield


@pytest.fixture(scope="session")
def http_client():
    """Persistent httpx.Client cho toàn session test."""
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        yield client


@pytest.fixture
def http(http_client) -> HttpFn:
    """Per-test http helper. Use: http('POST', '/auth/login', body={...}, token=tok)."""
    def _do(method: str, path: str, body: dict | None = None,
            token: str | None = None, partner_id: int | None = None) -> httpx.Response:
        return _http_request(http_client, method, path, body, token, partner_id)
    return _do


@pytest.fixture(scope="session")
def admin_token(http_client) -> str:
    tok = _login(http_client, ADMIN_EMAIL, ADMIN_PWD)
    assert tok, f"Không login được admin {ADMIN_EMAIL}"
    return tok


@pytest.fixture(scope="session")
def owner_cafe_token(http_client) -> str:
    tok = _login(http_client, OWNER_CAFE_EMAIL, OWNER_CAFE_PWD)
    assert tok, f"Không login được {OWNER_CAFE_EMAIL}"
    return tok


@pytest.fixture(scope="session")
def owner_lala_token(http_client) -> str:
    tok = _login(http_client, OWNER_LALA_EMAIL, OWNER_LALA_PWD)
    assert tok, f"Không login được {OWNER_LALA_EMAIL}"
    return tok


@pytest.fixture
def customer1_token(http_client) -> str:
    """Per-test (function scope) re-login khach1 để tránh stale token."""
    tok = _login(http_client, CUSTOMER1_EMAIL, CUSTOMER_PWD)
    assert tok, f"Không login được {CUSTOMER1_EMAIL}"
    return tok


@pytest.fixture
def customer2_token(http_client) -> str:
    """Per-test re-login khach2."""
    tok = _login(http_client, CUSTOMER2_EMAIL, CUSTOMER_PWD)
    assert tok, f"Không login được {CUSTOMER2_EMAIL} — restore_user_password bằng fixture cleanup"
    return tok


@pytest.fixture(scope="session")
def partner_cafe_id(http_client, owner_cafe_token) -> int:
    r = _http_request(http_client, "GET", "/users/me/partners-as-staff", token=owner_cafe_token)
    assert r.status_code == 200, r.text
    return r.json()[0]["id"]


@pytest.fixture(scope="session")
def partner_lala_id(http_client, owner_lala_token) -> int:
    r = _http_request(http_client, "GET", "/users/me/partners-as-staff", token=owner_lala_token)
    assert r.status_code == 200, r.text
    return r.json()[0]["id"]


# ============================================================
# Helpers exposed cho test files
# ============================================================

@pytest.fixture
def random_email() -> Callable[[], str]:
    """Tạo email unique cho mỗi test."""
    def _gen():
        return f"e2e+{secrets.token_hex(4)}@test.vn"
    return _gen


@pytest.fixture
def random_phone() -> Callable[[], str]:
    """Tạo SĐT VN unique 0xxxxxxxxx."""
    def _gen():
        return f"09{secrets.randbelow(10**8):08d}"
    return _gen
