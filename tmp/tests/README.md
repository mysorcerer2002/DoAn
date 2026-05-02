# Bộ kịch bản kiểm thử cho Chương 4 báo cáo

## Cấu trúc

```
tmp/tests/
├── README.md                  ← tài liệu này
├── setup.sh                   ← env vars + helper functions (login, assert)
├── run_all_functional.sh      ← chạy toàn bộ 34 kịch bản chức năng
├── scenarios/
│   ├── group_a_auth.sh        ← TC-A01..A10  — Xác thực và phân quyền
│   ├── group_b_partner.sh     ← TC-B01..B10  — Vòng đời đối tác
│   ├── group_c_pos.sh         ← TC-C01..C16 + TC-C13b — Tích điểm và đổi quà
│   └── group_d_admin.sh       ← TC-D01..D07  — Quản trị và kiểm toán
├── load/
│   └── locustfile.py          ← LT-01..LT-05 — kiểm thử tải bằng Locust
└── results/                   ← log output mỗi lần chạy (gitignored)
```

## Yêu cầu

- `bash`, `curl`, `jq`, `python3` (cho Locust)
- Locust: `pip install locust`
- Backend + Frontend đã build/deploy: `docker compose -p loyalty-prod up -d`
- Tài khoản demo đã seed (`backend/seed_demo.py`)

## Chạy

### Functional (34 kịch bản)

```bash
# Mặc định BASE_URL=http://localhost:3199/api (qua Next.js proxy)
bash tmp/tests/run_all_functional.sh

# Hoặc chỉ định BASE_URL:
BASE_URL=https://loyalty.ecom-bill.com/api bash tmp/tests/run_all_functional.sh

# Chạy 1 group:
bash tmp/tests/scenarios/group_a_auth.sh

# Output lưu vào tmp/tests/results/<timestamp>.log
```

### Load test (5 kịch bản)

```bash
cd tmp/tests/load
locust -f locustfile.py --host=http://localhost:3199 --headless \
  -u 100 -r 100 -t 30s --csv=../results/load
# -u: số client ảo, -r: spawn rate (client/s), -t: thời gian
```

Hoặc chạy UI mode (mặc định http://localhost:8089):
```bash
locust -f locustfile.py --host=http://localhost:3199
```

## Tài khoản demo (seed sẵn)

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Super admin | `admin@loyalty.vn` | `admin1234` |
| Owner Cafe Cộng | `owner@cafe.vn` | `owner1234` |
| Owner Lala Food | `owner@lala.vn` | `owner1234` |
| Customer Cafe | `khach1@gmail.com` – `khach5@gmail.com` | `khach1234` |
| Customer Lala | `lala1@gmail.com` – `lala5@gmail.com` | `khach1234` |

## Capture screenshot cho Phụ lục B

1. Chạy `run_all_functional.sh` → kết quả console + log file ở `results/`.
2. Mở UI ở `http://localhost:3199` → manual test các flow chính (đăng ký, đổi quà, voucher) → screenshot.
3. Chạy Locust với UI mode → screenshot dashboard sau khi test xong.
4. Capture DB state bằng `docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT ..."` cho LT-01/LT-02 (verify tồn kho cuối, số voucher phát).
