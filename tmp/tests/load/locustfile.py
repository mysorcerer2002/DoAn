"""Locust load tests cho 5 kịch bản LT-01..LT-05 — Bảng 4-2 báo cáo Chương 4.

Mỗi class tương ứng 1 kịch bản. Chạy 1 lúc 1 class qua tham số class name:

    locust -f locustfile.py LoadTestRedeemRace --host=http://localhost:3199 \\
        --headless -u 100 -r 100 -t 20s --csv=../results/lt01

Setup helpers (chạy trước Locust):

    python locustfile.py create_test_customers 100   # tạo 100 user test+0001..0100
    python locustfile.py setup_lt01 5                # tạo 1 reward stock=5 → in REWARD_ID
    python locustfile.py setup_lt02 10               # tạo 1 free voucher stock=10
"""

from __future__ import annotations

import json
import os
import random
import string
from datetime import datetime
from pathlib import Path

from locust import HttpUser, between, task
from locust.exception import StopUser

BASE_PATH = "/api"

ADMIN_EMAIL = "admin@loyalty.vn"
ADMIN_PWD = "admin1234"
OWNER_EMAIL = "owner@cafe.vn"
OWNER_PWD = "owner1234"
TEST_CUSTOMER_PWD = "test1234"

# Pre-cached tokens (chạy `python setup_data.py cache_tokens 200` trước Locust)
_TOKENS_FILE = Path(__file__).parent / "tokens.json"
if _TOKENS_FILE.exists():
    _CACHED = json.loads(_TOKENS_FILE.read_text())
    CUSTOMER_TOKENS: list[str] = _CACHED.get("customers", [])
    CACHED_OWNER_TOKEN: str = _CACHED.get("owner_token", "")
    CACHED_PARTNER_ID: int = _CACHED.get("partner_id", 0)
else:
    CUSTOMER_TOKENS, CACHED_OWNER_TOKEN, CACHED_PARTNER_ID = [], "", 0


def random_ip() -> str:
    """X-Forwarded-For random IP để bypass rate limit per-IP của slowapi."""
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Forwarded-For": random_ip()}


# ============================================================
# LT-01 — Race condition khi đổi quà
# ============================================================
# Spec: 1 reward stock=5, 100 client ảo cùng đổi đồng thời.
# Expected: đúng 5 success (201), 95 out_of_stock (409).
# Run:
#   export REDEEM_REWARD_ID=<id từ setup_lt01>
#   locust -f locustfile.py LoadTestRedeemRace --host=http://localhost:3199 \
#       --headless -u 100 -r 100 -t 20s --csv=../results/lt01

class LoadTestRedeemRace(HttpUser):
    wait_time = between(0, 0.05)
    REWARD_ID = int(os.getenv("REDEEM_REWARD_ID", "1"))

    def on_start(self):
        # Pre-cached token (tránh bcrypt bottleneck — race test phải đo race trên redeem, không đo login)
        if not CUSTOMER_TOKENS:
            raise StopUser()
        self.token = random.choice(CUSTOMER_TOKENS)

    @task
    def redeem(self):
        self.client.post(
            f"{BASE_PATH}/users/me/redemptions",
            json={"reward_id": self.REWARD_ID},
            headers=auth_headers(self.token),
            name="POST /users/me/redemptions",
        )
        raise StopUser()  # 1 client = 1 yêu cầu duy nhất


# ============================================================
# LT-02 — Race condition khi nhận voucher giới hạn
# ============================================================
# Spec: 1 free voucher stock=10, 200 client cùng claim.
# Expected: đúng 10 success, 190 từ chối; mỗi client max 1 voucher.

class LoadTestFreeClaimRace(HttpUser):
    wait_time = between(0, 0.05)
    REWARD_ID = int(os.getenv("FREE_REWARD_ID", "1"))
    _idx_counter = [0]  # class-level counter — mỗi user lấy 1 token unique (test 1-per-user)

    def on_start(self):
        if not CUSTOMER_TOKENS:
            raise StopUser()
        # Round-robin token để mỗi virtual user là 1 customer khác
        self.token = CUSTOMER_TOKENS[self._idx_counter[0] % len(CUSTOMER_TOKENS)]
        self._idx_counter[0] += 1

    @task
    def claim_free(self):
        self.client.post(
            f"{BASE_PATH}/users/me/rewards/{self.REWARD_ID}/claim",
            headers=auth_headers(self.token),
            name="POST /users/me/rewards/{id}/claim",
        )
        raise StopUser()


# ============================================================
# LT-03 — Hiệu năng tích điểm POS
# ============================================================
# Spec: 50 client × 5 phút, throughput >100 req/s, p95 <200ms.
# Mỗi client tích điểm liên tục cho 50 khách khác nhau.

class LoadTestPOSThroughput(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        # Pre-cached owner token + partner_id (tránh login bottleneck)
        if not CACHED_OWNER_TOKEN:
            raise StopUser()
        self.owner_token = CACHED_OWNER_TOKEN
        self.partner_id = CACHED_PARTNER_ID
        # Mỗi user gắn 1 customer phone (50 user → 50 phone khác nhau)
        idx = random.randint(1, 50)
        self.customer_phone = f"099{idx:07d}"

    @task
    def pos_earn(self):
        amount = random.choice([50000, 100000, 150000, 200000])
        self.client.post(
            f"{BASE_PATH}/partner/transactions",
            json={"phone": self.customer_phone, "gross_amount": amount},
            headers={
                "Authorization": f"Bearer {self.owner_token}",
                "X-Partner-Id": str(self.partner_id),
                "X-Forwarded-For": random_ip(),
            },
            name="POST /partner/transactions",
        )


# ============================================================
# LT-04 — Auto-enroll khi tích điểm lần đầu
# ============================================================
# Spec: 50 khách mới cùng được tích điểm tại cùng cửa hàng → mỗi khách
# có đúng 1 membership, không trùng.

class LoadTestAutoEnroll(HttpUser):
    wait_time = between(0, 0.1)

    def on_start(self):
        if not CACHED_OWNER_TOKEN:
            raise StopUser()
        self.owner_token = CACHED_OWNER_TOKEN
        self.partner_id = CACHED_PARTNER_ID
        # Phone duy nhất cho user này — 10 ký tự đúng định dạng VN (098 + 7 số)
        self.unique_phone = f"098{random.randint(0, 9999999):07d}"

    @task
    def enroll_and_earn(self):
        self.client.post(
            f"{BASE_PATH}/partner/transactions",
            json={"phone": self.unique_phone, "gross_amount": 50000},
            headers={
                "Authorization": f"Bearer {self.owner_token}",
                "X-Partner-Id": str(self.partner_id),
                "X-Forwarded-For": random_ip(),
            },
            name="POST /partner/transactions (auto-enroll)",
        )
        raise StopUser()


# ============================================================
# LT-05 — Chống tấn công thử mật khẩu
# ============================================================
# Spec: 1 client × 100 yêu cầu sai mật khẩu liên tiếp → sau N lần →
# 423/429 + tài khoản tạm khóa.
# Victim = email throwaway (KHÔNG đụng khach1..5 — sẽ block khách thật)

VICTIM_EMAIL = os.getenv("LT05_VICTIM_EMAIL", "lt05victim@e2e.vn")


class LoadTestBruteForce(HttpUser):
    wait_time = between(0, 0.05)
    fixed_ip = "10.99.99.99"  # cùng IP → trigger lock theo IP/identifier

    def on_start(self):
        self.attempts = 0

    @task
    def wrong_login(self):
        self.attempts += 1
        wrong_pwd = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        self.client.post(
            f"{BASE_PATH}/auth/login",
            json={"identifier": VICTIM_EMAIL, "password": wrong_pwd},
            headers={"X-Forwarded-For": self.fixed_ip},
            name="POST /auth/login (wrong)",
        )
        if self.attempts >= 100:
            raise StopUser()


# Setup helpers tách sang setup_data.py (tránh xung đột gevent monkey-patch).
