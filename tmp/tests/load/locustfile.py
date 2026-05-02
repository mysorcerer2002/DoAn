"""Locust load tests cho 5 kịch bản LT-01..LT-05.

Chạy:
    locust -f locustfile.py --host=http://localhost:3199 --headless \
        -u <users> -r <spawn_rate> -t <duration> --csv=../results/load

Mỗi `LoadTest*` class tương ứng 1 kịch bản. Chỉ activate 1 class mỗi lần
chạy bằng cách comment các class còn lại HOẶC gọi:
    locust -f locustfile.py LoadTestRedeemRace
"""

import os
import random
import string
from datetime import datetime, timedelta

from locust import HttpUser, task, between, events


BASE_PATH = "/api"
ADMIN_EMAIL = "admin@loyalty.vn"
ADMIN_PWD = "admin1234"
OWNER_EMAIL = "owner@cafe.vn"
OWNER_PWD = "owner1234"
CUSTOMER_PWD = "khach1234"


# ============================================================
# LT-01 — Race condition khi đổi quà
# ============================================================
# Setup: tạo 1 reward stock=5 + 100 customer mới có 5000 điểm.
# Run: 100 client cùng đổi → 5 success, 95 out_of_stock.
# Locust:
#   locust -f locustfile.py LoadTestRedeemRace --host=http://localhost:3199 \
#       --headless -u 100 -r 100 -t 30s --csv=../results/lt01

class LoadTestRedeemRace(HttpUser):
    wait_time = between(0, 0.1)

    # Set qua env: REDEEM_REWARD_ID + customer pool token
    REWARD_ID = int(os.getenv("REDEEM_REWARD_ID", "1"))

    def on_start(self):
        # Mỗi user lấy 1 customer token từ pool seeded
        # (Test này giả định đã seed 100 customer test+0001..test+0100 với pwd test1234)
        idx = random.randint(1, 100)
        email = f"test+{idx:04d}@e2e.vn"
        r = self.client.post(f"{BASE_PATH}/auth/login",
                              json={"identifier": email, "password": "test1234"})
        if r.status_code == 200:
            self.token = r.json()["access_token"]
        else:
            self.token = None
            print(f"Login fail for {email}: {r.status_code}")

    @task
    def redeem(self):
        if not self.token:
            return
        r = self.client.post(
            f"{BASE_PATH}/users/me/redemptions",
            json={"reward_id": self.REWARD_ID},
            headers={"Authorization": f"Bearer {self.token}"},
            name="POST /users/me/redemptions"
        )
        # Kỳ vọng: 5 đầu trả 201, các sau trả 409 out_of_stock
        if r.status_code in (201, 409):
            pass  # OK
        else:
            print(f"Unexpected: {r.status_code} {r.text[:100]}")
        self.environment.runner.quit()  # Mỗi client chỉ chạy 1 lần


# ============================================================
# LT-02 — Race condition khi nhận voucher giới hạn
# ============================================================
# Setup: tạo 1 free reward (points_cost=0) stock=10.
# Run: 200 client cùng claim → 10 success, 190 out_of_stock OR already_claimed.

class LoadTestFreeClaimRace(HttpUser):
    wait_time = between(0, 0.1)
    REWARD_ID = int(os.getenv("FREE_REWARD_ID", "1"))

    def on_start(self):
        idx = random.randint(1, 200)
        email = f"test+{idx:04d}@e2e.vn"
        r = self.client.post(f"{BASE_PATH}/auth/login",
                              json={"identifier": email, "password": "test1234"})
        self.token = r.json().get("access_token") if r.status_code == 200 else None

    @task
    def claim_free(self):
        if not self.token:
            return
        r = self.client.post(
            f"{BASE_PATH}/users/me/rewards/{self.REWARD_ID}/claim",
            headers={"Authorization": f"Bearer {self.token}"},
            name="POST /users/me/rewards/{id}/claim"
        )
        if r.status_code in (201, 409):
            pass
        else:
            print(f"Unexpected: {r.status_code} {r.text[:100]}")
        self.environment.runner.quit()


# ============================================================
# LT-03 — Hiệu năng tích điểm POS
# ============================================================
# Setup: owner Cafe + 50 customer. Mỗi user đảm nhận tích điểm cho 1 customer.
# Run: 50 user, 5 phút, throughput target > 100 req/s.

class LoadTestPOSThroughput(HttpUser):
    wait_time = between(0.05, 0.2)  # ~5-20 req/s/user

    def on_start(self):
        # Login owner
        r = self.client.post(f"{BASE_PATH}/auth/login",
                              json={"identifier": OWNER_EMAIL, "password": OWNER_PWD})
        self.owner_token = r.json()["access_token"]
        # Get partner_id
        r = self.client.get(f"{BASE_PATH}/users/me/partners-as-staff",
                             headers={"Authorization": f"Bearer {self.owner_token}"})
        self.partner_id = r.json()[0]["id"]
        # Mỗi user gắn 1 customer phone
        idx = random.randint(1, 50)
        self.customer_phone = f"091{idx:07d}"

    @task
    def pos_earn(self):
        amount = random.choice([50000, 100000, 150000, 200000])
        self.client.post(
            f"{BASE_PATH}/partner/transactions",
            json={"phone": self.customer_phone, "gross_amount": amount},
            headers={
                "Authorization": f"Bearer {self.owner_token}",
                "X-Partner-Id": str(self.partner_id),
            },
            name="POST /partner/transactions"
        )


# ============================================================
# LT-04 — Auto-enroll khi tích điểm lần đầu
# ============================================================
# Setup: owner Cafe + 50 SĐT mới (chưa từng giao dịch).
# Run: 50 user cùng tích điểm cho 50 SĐT mới → mỗi SĐT 1 membership.

class LoadTestAutoEnroll(HttpUser):
    wait_time = between(0, 0.1)

    def on_start(self):
        r = self.client.post(f"{BASE_PATH}/auth/login",
                              json={"identifier": OWNER_EMAIL, "password": OWNER_PWD})
        self.owner_token = r.json()["access_token"]
        r = self.client.get(f"{BASE_PATH}/users/me/partners-as-staff",
                             headers={"Authorization": f"Bearer {self.owner_token}"})
        self.partner_id = r.json()[0]["id"]
        # Tạo phone duy nhất cho user này (UUID-ish)
        self.unique_phone = f"098{random.randint(0, 99999999):08d}"

    @task
    def enroll_and_earn(self):
        self.client.post(
            f"{BASE_PATH}/partner/transactions",
            json={"phone": self.unique_phone, "gross_amount": 50000},
            headers={
                "Authorization": f"Bearer {self.owner_token}",
                "X-Partner-Id": str(self.partner_id),
            },
            name="POST /partner/transactions (auto-enroll)"
        )
        self.environment.runner.quit()


# ============================================================
# LT-05 — Chống tấn công thử mật khẩu
# ============================================================
# Setup: 1 customer email bất kỳ (vd khach1@gmail.com).
# Run: 1 user gửi 100 yêu cầu login sai liên tiếp.

class LoadTestBruteForce(HttpUser):
    wait_time = between(0, 0.1)

    def on_start(self):
        self.attempts = 0
        self.victim_email = "khach1@gmail.com"

    @task
    def wrong_login(self):
        self.attempts += 1
        wrong_pwd = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        r = self.client.post(
            f"{BASE_PATH}/auth/login",
            json={"identifier": self.victim_email, "password": wrong_pwd},
            name="POST /auth/login (wrong)"
        )
        # Trước threshold: 401. Sau threshold: 423/429.
        if self.attempts >= 100:
            self.environment.runner.quit()


# ============================================================
# Helper: setup test data trước khi chạy LT-01/LT-02
# ============================================================
# Chạy bằng: python locustfile.py setup_lt01 (hoặc setup_lt02)
# Sẽ in REWARD_ID/FREE_REWARD_ID + tạo 100 customer test+XXXX.

if __name__ == "__main__":
    import sys
    import requests

    BASE_URL = os.getenv("BASE_URL", "http://localhost:3199/api")

    def login(email, pwd):
        r = requests.post(f"{BASE_URL}/auth/login",
                          json={"identifier": email, "password": pwd})
        r.raise_for_status()
        return r.json()["access_token"]

    def create_test_customers(n):
        """Tạo n customer mới với email test+XXXX@e2e.vn, pwd test1234, mỗi customer cộng 5000 điểm."""
        admin_tok = login(ADMIN_EMAIL, ADMIN_PWD)
        owner_tok = login(OWNER_EMAIL, OWNER_PWD)
        partner_id = requests.get(f"{BASE_URL}/users/me/partners-as-staff",
                                   headers={"Authorization": f"Bearer {owner_tok}"}).json()[0]["id"]
        for i in range(1, n + 1):
            email = f"test+{i:04d}@e2e.vn"
            phone = f"099{i:07d}"
            r = requests.post(f"{BASE_URL}/auth/register",
                              json={"email": email, "phone": phone,
                                    "password": "test1234", "full_name": f"Test {i}"})
            if r.status_code not in (201, 409):
                print(f"Register {email}: {r.status_code}")
            # Tích điểm 500k @ 1% = 5000 điểm
            r = requests.post(f"{BASE_URL}/partner/transactions",
                              json={"phone": phone, "gross_amount": 500000},
                              headers={"Authorization": f"Bearer {owner_tok}",
                                       "X-Partner-Id": str(partner_id)})
            if r.status_code != 201:
                print(f"POS earn {phone}: {r.status_code} {r.text[:100]}")
            if i % 20 == 0:
                print(f"Created {i}/{n}")

    def setup_lt01(stock=5):
        """Tạo 1 reward stock=5 cho LT-01."""
        owner_tok = login(OWNER_EMAIL, OWNER_PWD)
        partner_id = requests.get(f"{BASE_URL}/users/me/partners-as-staff",
                                   headers={"Authorization": f"Bearer {owner_tok}"}).json()[0]["id"]
        body = {
            "name": f"LT01 reward {datetime.now().isoformat()}",
            "points_cost": 1000,
            "stock": stock,
            "offer_type": "ITEM_GIFT",
            "offer_label": "1 Cafe miễn phí (LT-01)"
        }
        r = requests.post(f"{BASE_URL}/partner/rewards", json=body,
                          headers={"Authorization": f"Bearer {owner_tok}",
                                   "X-Partner-Id": str(partner_id)})
        r.raise_for_status()
        rid = r.json()["id"]
        print(f"export REDEEM_REWARD_ID={rid}")

    def setup_lt02(stock=10):
        """Tạo 1 free reward stock=10 cho LT-02."""
        owner_tok = login(OWNER_EMAIL, OWNER_PWD)
        partner_id = requests.get(f"{BASE_URL}/users/me/partners-as-staff",
                                   headers={"Authorization": f"Bearer {owner_tok}"}).json()[0]["id"]
        body = {
            "name": f"LT02 free voucher {datetime.now().isoformat()}",
            "points_cost": 0,
            "stock": stock,
            "offer_type": "ITEM_GIFT",
            "offer_label": "Free voucher (LT-02)"
        }
        r = requests.post(f"{BASE_URL}/partner/rewards", json=body,
                          headers={"Authorization": f"Bearer {owner_tok}",
                                   "X-Partner-Id": str(partner_id)})
        r.raise_for_status()
        rid = r.json()["id"]
        print(f"export FREE_REWARD_ID={rid}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "create_test_customers":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            create_test_customers(n)
        elif cmd == "setup_lt01":
            setup_lt01(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
        elif cmd == "setup_lt02":
            setup_lt02(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
        else:
            print("Usage: python locustfile.py {create_test_customers|setup_lt01|setup_lt02} [n]")
