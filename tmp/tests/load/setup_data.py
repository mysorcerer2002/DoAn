"""Setup test data cho Locust LT-01..LT-05. Chạy trước Locust.

KHÔNG import locust ở đây — gevent monkey-patch xung đột với requests.

    python setup_data.py create_test_customers 100
    python setup_data.py setup_lt01 5            # in REDEEM_REWARD_ID
    python setup_data.py setup_lt02 10           # in FREE_REWARD_ID
    python setup_data.py setup_lt05_victim       # tạo victim throwaway
"""

from __future__ import annotations

import os
import random
import secrets
import sys
from datetime import datetime

import requests

OWNER_EMAIL = "owner@cafe.vn"
OWNER_PWD = "owner1234"
TEST_CUSTOMER_PWD = "test1234"
LT05_VICTIM_EMAIL = "lt05victim@e2e.vn"


def random_ip() -> str:
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Forwarded-For": random_ip()}


def login(base_url: str, email: str, pwd: str) -> str:
    r = requests.post(
        f"{base_url}/auth/login",
        json={"identifier": email, "password": pwd},
        headers={"X-Forwarded-For": random_ip()}, timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def create_test_customers(base_url: str, n: int) -> None:
    """Tạo n customer test+0001..n + tích sẵn 5000 điểm cho mỗi."""
    owner_tok = login(base_url, OWNER_EMAIL, OWNER_PWD)
    partner_id = requests.get(
        f"{base_url}/users/me/partners-as-staff",
        headers=auth_headers(owner_tok), timeout=10,
    ).json()[0]["id"]
    for i in range(1, n + 1):
        email = f"test+{i:04d}@e2e.vn"
        phone = f"099{i:07d}"
        r = requests.post(
            f"{base_url}/auth/register",
            json={"email": email, "phone": phone,
                  "password": TEST_CUSTOMER_PWD, "full_name": f"Test {i}"},
            headers={"X-Forwarded-For": random_ip()}, timeout=10,
        )
        if r.status_code not in (201, 409):
            print(f"[skip] register {email}: {r.status_code} {r.text[:80]}")
            continue
        # Tích 500k @ 1% = 5000 điểm để đủ đổi quà giá 1000đ (LT-01)
        r = requests.post(
            f"{base_url}/partner/transactions",
            json={"phone": phone, "gross_amount": 500000},
            headers={**auth_headers(owner_tok), "X-Partner-Id": str(partner_id)},
            timeout=10,
        )
        if r.status_code != 201:
            print(f"[skip] POS earn {phone}: {r.status_code} {r.text[:80]}")
        if i % 25 == 0:
            print(f"  progress: {i}/{n}")
    print(f"DONE: {n} customers ready (test+0001..test+{n:04d}@e2e.vn / pwd={TEST_CUSTOMER_PWD})")


def setup_lt01(base_url: str, stock: int = 5) -> int:
    """Tạo 1 reward stock=N, points_cost=1000."""
    owner_tok = login(base_url, OWNER_EMAIL, OWNER_PWD)
    partner_id = requests.get(
        f"{base_url}/users/me/partners-as-staff",
        headers=auth_headers(owner_tok), timeout=10,
    ).json()[0]["id"]
    body = {
        "name": f"LT01 reward {datetime.now().isoformat(timespec='seconds')}",
        "points_cost": 1000, "stock": stock,
        "offer_type": "ITEM_GIFT",
        "offer_label": f"Reward stock={stock} (LT-01)",
    }
    r = requests.post(
        f"{base_url}/partner/rewards", json=body,
        headers={**auth_headers(owner_tok), "X-Partner-Id": str(partner_id)},
        timeout=10,
    )
    r.raise_for_status()
    rid = r.json()["id"]
    print(f"REDEEM_REWARD_ID={rid}")
    return rid


def setup_lt02(base_url: str, stock: int = 10) -> int:
    """Tạo 1 free voucher stock=N, points_cost=0."""
    owner_tok = login(base_url, OWNER_EMAIL, OWNER_PWD)
    partner_id = requests.get(
        f"{base_url}/users/me/partners-as-staff",
        headers=auth_headers(owner_tok), timeout=10,
    ).json()[0]["id"]
    body = {
        "name": f"LT02 free voucher {datetime.now().isoformat(timespec='seconds')}",
        "points_cost": 0, "stock": stock,
        "offer_type": "ITEM_GIFT",
        "offer_label": f"Free voucher stock={stock} (LT-02)",
    }
    r = requests.post(
        f"{base_url}/partner/rewards", json=body,
        headers={**auth_headers(owner_tok), "X-Partner-Id": str(partner_id)},
        timeout=10,
    )
    r.raise_for_status()
    rid = r.json()["id"]
    print(f"FREE_REWARD_ID={rid}")
    return rid


def cache_tokens(base_url: str, n: int) -> None:
    """Login n test customers + owner, lưu tokens.json để Locust dùng (tránh bcrypt bottleneck)."""
    import json
    tokens = {"customers": [], "owner_token": "", "partner_id": 0}
    print(f"Login owner...")
    owner_tok = login(base_url, OWNER_EMAIL, OWNER_PWD)
    tokens["owner_token"] = owner_tok
    tokens["partner_id"] = requests.get(
        f"{base_url}/users/me/partners-as-staff",
        headers=auth_headers(owner_tok), timeout=10,
    ).json()[0]["id"]
    print(f"Login {n} customers...")
    for i in range(1, n + 1):
        email = f"test+{i:04d}@e2e.vn"
        try:
            tok = login(base_url, email, TEST_CUSTOMER_PWD)
            tokens["customers"].append(tok)
        except Exception as e:
            print(f"[skip] login {email}: {e}")
        if i % 25 == 0:
            print(f"  progress: {i}/{n}")
    with open("tokens.json", "w") as f:
        json.dump(tokens, f)
    print(f"DONE: cached {len(tokens['customers'])} customer tokens + owner → tokens.json")


def setup_lt05_victim(base_url: str) -> None:
    """Tạo victim throwaway cho LT-05 (KHÔNG đụng khach1..5 thật)."""
    phone = f"097{random.randint(0, 9999999):07d}"  # 10 ký tự đúng định dạng VN
    r = requests.post(
        f"{base_url}/auth/register",
        json={"email": LT05_VICTIM_EMAIL, "phone": phone,
              "password": secrets.token_urlsafe(16),
              "full_name": "LT-05 Victim"},
        headers={"X-Forwarded-For": random_ip()}, timeout=10,
    )
    if r.status_code in (201, 409):
        print(f"VICTIM ready: {LT05_VICTIM_EMAIL}")
    else:
        print(f"Register victim FAIL: {r.status_code} {r.text[:80]}")


if __name__ == "__main__":
    base = os.getenv("BASE_URL", "http://localhost:3199/api")
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "create_test_customers":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        create_test_customers(base, n)
    elif cmd == "setup_lt01":
        setup_lt01(base, int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    elif cmd == "setup_lt02":
        setup_lt02(base, int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    elif cmd == "setup_lt05_victim":
        setup_lt05_victim(base)
    elif cmd == "cache_tokens":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        cache_tokens(base, n)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
