# Đồ án thực tập tốt nghiệp: Xây dựng hệ thống website cung cấp giải pháp chăm sóc khách hàng thân thiết cho doanh nghiệp SME

Hệ thống tích điểm thành viên đa đối tác cho SME (cà phê, nhà hàng, shop bán lẻ).
Sinh viên thực hiện: **Nguyễn Hải Đăng**.

**Stack:** FastAPI + SQLAlchemy 2.0 async + PostgreSQL 15 + Alembic · Next.js 14 App Router + Tailwind v4 + shadcn/ui · Docker Compose.

---

## 1. Chuẩn bị source code

```bash
git clone https://github.com/mysorcerer2002/DoAn.git
cd DoAn
```

Thư mục gốc đúng khi `ls` (hoặc `dir`) thấy `docker-compose.yml`, `backend/`, `frontend/`, `README.md`.

---

## 2. Cấu hình biến môi trường (.env)

Sao chép ba file `.env` từ các file mẫu:

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
```

**macOS / Linux:**

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Giá trị mặc định trong các file mẫu đủ để chạy thử ở môi trường local — không cần chỉnh sửa thêm để demo. `JWT_SECRET` mặc định trong `docker-compose.yml` chỉ phục vụ chạy thử, không dùng cho production.

*JWT_SECRET ngẫu nhiên (không bắt buộc khi chạy thử local) sinh bằng:*

```powershell
# Windows PowerShell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
```

```bash
# macOS / Linux
openssl rand -hex 32
```

Chuỗi kết quả thay vào biến `JWT_SECRET=` của `backend/.env`.

---

## 3. Quy trình khởi động

```bash
docker compose up -d --build
```

Lệnh này thực hiện 5 bước: pull image PostgreSQL 15, build image Backend (FastAPI, Python 3.11), build image Frontend (Next.js 14, Node 20), khởi động 3 container theo thứ tự `postgres → backend → frontend`, và Backend tự chạy Alembic migrations để tạo schema khi start.

Lần đầu build mất 5–10 phút tuỳ tốc độ mạng; các lần sau chỉ vài giây.

```bash
docker compose logs -f
```

Lệnh trên theo dõi tiến trình real-time; phím `Ctrl+C` thoát chế độ theo dõi mà không dừng container.

```bash
docker compose ps
```

Khi khởi động thành công, cột `STATUS` của ba container `loyalty-postgres`, `loyalty-backend`, `loyalty-frontend` đều ở trạng thái `Up ... (healthy)`.

---

## 4. Trạng thái sau khởi động

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

- Backend API docs (Swagger UI): http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 5. Dữ liệu seed cho demo

```bash
docker compose exec backend python seed_demo.py
```

Script `seed_demo.py` tạo dữ liệu mẫu trong container backend, gồm: 1 super admin; 2 đối tác (Cafe Cộng, Trà Sữa Lala) với đầy đủ tier, point rule, reward; 4 nhân viên; 10 khách hàng đã tham gia membership; ~65 giao dịch POS trong 14 ngày gần nhất; và bút toán point ledger + một số redemption mẫu.

Script kết thúc bằng dòng `✅ Seed completed`. Script là idempotent — chạy lặp không nhân đôi dữ liệu.

---

## 6. Tài khoản demo

Trang đăng nhập: http://localhost:3000/login

| Vai trò               | Email              | Mật khẩu  |
|-----------------------|--------------------|-----------|
| Super admin           | admin@loyalty.vn   | admin1234 |
| Chủ shop — Cafe Cộng  | owner@cafe.vn      | owner1234 |
| Chủ shop — Lala Food  | owner@lala.vn      | owner1234 |
| Nhân viên — Cafe Cộng | staff1@cafe.vn     | staff1234 |
| Nhân viên — Lala      | staff1@lala.vn     | staff1234 |
| Khách hàng (Cafe)     | khach1@gmail.com   | khach1234 |
| Khách hàng (Lala)     | lala1@gmail.com    | khach1234 |

Các email khách hàng còn lại: `khach2..khach5@gmail.com`, `lala2..lala5@gmail.com` (cùng mật khẩu `khach1234`).

Đường dẫn nhanh sau đăng nhập (hệ thống tự điều hướng theo vai trò):

- Super admin → `/admin`
- Chủ shop → `/merchant`
- Nhân viên → `/staff`
- Khách hàng → `/member`

---

## 7. Bộ kiểm thử tự động (Bảng 4-1 báo cáo, Chương 4)

Đồ án có sẵn 44 test function viết bằng Pytest, tương ứng 34 kịch bản kiểm thử trong Bảng 4-1. Test gọi API thật của backend đang chạy trong container, kèm thao tác DB qua psql để dựng các state đặc biệt (mật khẩu tạm, hạng Vàng, voucher quá hạn...).

| Nhóm | Phạm vi                                       | Số test            |
|------|-----------------------------------------------|--------------------|
| A    | Xác thực và phân quyền                        | 10 (TC-A01..A10)   |
| B    | Vòng đời đối tác (đăng ký, phê duyệt)         | 12 (TC-B01..B10)   |
| C    | Tích điểm POS và đổi quà                      | 17 (TC-C01..C16 + C13b) |
| D    | Quản trị hệ thống và kiểm toán                | 7 (TC-D01..D07)    |

Lần chạy gần nhất (commit `eb6d463`): 44/44 PASS.

### 7.1. Chuẩn bị (chỉ cần làm 1 lần)

Yêu cầu: Python 3.10+ trên máy host, 3 container đang chạy (mục 3), đã seed dữ liệu (mục 5).

```bash
python -m pip install --upgrade pip
python -m pip install pytest httpx pytest-html
```

### 7.2. Bộ lệnh chạy 44 test case + xuất báo cáo HTML

Test runner cần biết URL backend và tên container Postgres/Backend (mặc định trong code đang trỏ sang môi trường production của sinh viên, nên cần override).

**Windows PowerShell:**

```powershell
$env:BASE_URL      = "http://localhost:8000"
$env:PG_CONTAINER  = "loyalty-postgres"
$env:BE_CONTAINER  = "loyalty-backend"
python -m pytest tests_e2e `
    --html=tests_e2e/results/report.html `
    --self-contained-html `
    --junitxml=tests_e2e/results/junit.xml
```

**macOS / Linux:**

```bash
BASE_URL=http://localhost:8000 \
PG_CONTAINER=loyalty-postgres \
BE_CONTAINER=loyalty-backend \
python -m pytest tests_e2e \
    --html=tests_e2e/results/report.html \
    --self-contained-html \
    --junitxml=tests_e2e/results/junit.xml
```

Thời gian chạy: 2–3 phút. Kết quả mong đợi (dòng cuối terminal):

```
============== 44 passed in 145.xxs ==============
```

### 7.3. Cấu trúc báo cáo HTML

Báo cáo HTML nằm tại `tests_e2e/results/report.html`.

**Khối Summary (đầu trang)** — các con số tổng hợp toàn suite:

| Chỉ số      | Ý nghĩa                                                                 |
|-------------|-------------------------------------------------------------------------|
| `passed`    | Số test đạt — assertion + HTTP status đều khớp kỳ vọng.                 |
| `failed`    | Số test sai kết quả — request thành công nhưng response/DB không khớp.  |
| `error`     | Số test crash — exception trong fixture/setup, chưa tới được assert.    |
| `skipped`   | Số test bị bỏ qua bằng marker `@pytest.mark.skip`.                      |
| `duration`  | Tổng thời gian chạy toàn bộ suite (giây).                               |

**Khối Environment** — phiên bản Python, OS, các thư viện (httpx, pytest-html…). Dùng để đối chiếu khi reproduce.

**Khối Results (bảng chính)** — dòng/test:

| Cột        | Ý nghĩa                                                                  |
|------------|--------------------------------------------------------------------------|
| `Result`   | Trạng thái Passed / Failed / Error / Skipped (có nhãn màu).              |
| `Test`     | Đường dẫn module + tên test function, vd `test_group_a_auth.py::test_a01_dang_ky_hop_le`. |
| `Duration` | Thời gian chạy riêng test đó (giây).                                     |
| `Links`    | Click mũi tên để mở phần chi tiết phía dưới.                             |

**Phần chi tiết khi click một test:**

- `Captured stdout` — log `print()` trong test (request body, response status code…).
- `Captured stderr` — cảnh báo / error log từ thư viện.
- `Captured log` — log của Python `logging` (thường rỗng).
- Stack trace (nếu fail/error) — chỉ rõ dòng assertion vi phạm và giá trị thực tế vs kỳ vọng.

File `junit.xml` cùng thư mục dùng để import vào CI/CD hoặc IDE — chứa cùng dữ liệu nhưng dạng XML chuẩn JUnit.

### 7.4. Chạy chọn lọc theo nhóm / test case

```bash
# 1 nhóm
python -m pytest tests_e2e/test_group_a_auth.py -v
python -m pytest tests_e2e/test_group_b_partner.py -v
python -m pytest tests_e2e/test_group_c_pos.py -v
python -m pytest tests_e2e/test_group_d_admin.py -v

# 1 test case
python -m pytest tests_e2e/test_group_a_auth.py::test_a01_dang_ky_hop_le -v
```

Bảng mapping đầy đủ TC ↔ tên test function ↔ kết quả mong đợi: file `tests_e2e/README.md`.

### 7.5. Bộ test backend (unit + integration) bên trong container

Backend container đã sẵn pytest, không cần cài Python trên host:

```bash
docker compose exec backend pytest -v                     # toàn bộ
docker compose exec backend pytest tests/unit -v          # unit only
docker compose exec backend pytest tests/integration -v   # integration
```

Phần integration dùng testcontainers (cần quyền điều khiển Docker từ trong container) nên phụ thuộc Docker socket — không phải môi trường nào cũng đáp ứng. Bộ E2E ở mục 7.2 đã bao phủ chức năng đầu-cuối nên không bắt buộc chạy thêm phần này khi thẩm định.

### 7.6. Kịch bản load test với Locust (Bảng 4-2 báo cáo)

5 kịch bản kiểm thử tải nằm ở `tmp/tests/load/locustfile.py`:

| Mã    | Class                    | Kịch bản                                              |
|-------|--------------------------|-------------------------------------------------------|
| LT-01 | `LoadTestRedeemRace`     | Race condition khi đổi quà (1 reward stock=5, 100 client) |
| LT-02 | `LoadTestFreeClaimRace`  | Race condition khi nhận voucher giới hạn (stock=10, 200 client) |
| LT-03 | `LoadTestPOSThroughput`  | Hiệu năng tích điểm POS (50 client × 5 phút, mục tiêu p95 < 200ms) |
| LT-04 | `LoadTestAutoEnroll`     | Auto-enroll khi tích điểm lần đầu (50 khách mới đồng thời) |
| LT-05 | `LoadTestBruteForce`     | Chống tấn công thử mật khẩu (100 lần login sai liên tiếp) |

**Chuẩn bị (1 lần):**

```bash
python -m pip install locust requests
cd tmp/tests/load

# 100 customer test + tích sẵn 5000 điểm cho mỗi
BASE_URL=http://localhost:3000/api python setup_data.py create_test_customers 100

# Cache JWT token (tránh login bottleneck khi đo race)
BASE_URL=http://localhost:3000/api python setup_data.py cache_tokens 100

# Tạo reward + voucher cho LT-01, LT-02; tạo victim cho LT-05
BASE_URL=http://localhost:3000/api python setup_data.py setup_lt01 5      # in REDEEM_REWARD_ID=<id>
BASE_URL=http://localhost:3000/api python setup_data.py setup_lt02 10     # in FREE_REWARD_ID=<id>
BASE_URL=http://localhost:3000/api python setup_data.py setup_lt05_victim
```

**Chạy 1 kịch bản (ví dụ LT-01) + xuất báo cáo HTML:**

```bash
# headless mode — toàn bộ kết quả lưu vào 1 file HTML self-contained
REDEEM_REWARD_ID=<id-từ-setup-lt01> \
locust -f locustfile.py LoadTestRedeemRace --host=http://localhost:3000 \
    --headless -u 100 -r 100 -t 20s --html=../results/lt01.html

# Hoặc UI mode (mở http://localhost:8089 để cấu hình + xem dashboard real-time;
# dừng test rồi bấm "Download Report" để lấy HTML)
locust -f locustfile.py LoadTestRedeemRace --host=http://localhost:3000
```

Tương tự cho `LoadTestFreeClaimRace` (LT-02), `LoadTestPOSThroughput` (LT-03), `LoadTestAutoEnroll` (LT-04), `LoadTestBruteForce` (LT-05). LT-01/LT-02 cần biến môi trường tương ứng (`REDEEM_REWARD_ID`, `FREE_REWARD_ID`).

**Báo cáo `lt01.html` gồm các khối chính:**

*Khối "Request statistics" (bảng chính, 1 dòng / endpoint):*

| Cột                    | Ý nghĩa                                                                |
|------------------------|------------------------------------------------------------------------|
| `Method` / `Name`      | HTTP method + endpoint (vd `POST /users/me/redemptions`).              |
| `# Requests`           | Tổng số request đã gửi tới endpoint trong suốt thời gian test.         |
| `# Fails`              | Số request thất bại (HTTP 4xx/5xx hoặc timeout). Với LT-01: mong đợi 95 fails (out_of_stock). |
| `Average (ms)`         | Thời gian phản hồi trung bình.                                         |
| `Min (ms)` / `Max (ms)`| Thời gian nhanh nhất / chậm nhất.                                      |
| `Average size (bytes)` | Kích thước response trung bình.                                        |
| `Current RPS`          | Số request/giây tại thời điểm cuối test.                               |
| `Current Failures/s`   | Số failure/giây tại thời điểm cuối test.                               |

*Khối "Response time statistics" (percentile latency, 1 dòng / endpoint):*

| Cột       | Ý nghĩa                                                                                |
|-----------|----------------------------------------------------------------------------------------|
| `50%ile`  | Median — 50% request có latency ≤ giá trị này.                                         |
| `66%/75%` | Đa số request hoàn tất trong khoảng này.                                               |
| `80%/90%` | Đuôi trên — đo độ ổn định khi tải cao.                                                 |
| `95%ile`  | Chỉ số quan trọng nhất với LT-03 (yêu cầu p95 < 200 ms theo Bảng 4-2 báo cáo).         |
| `98%/99%` | Phần đuôi rất xa — phản ánh worst-case dưới tải.                                       |
| `100%ile` | Latency request chậm nhất.                                                             |

*Khối "Charts":*

- **Total Requests per Second** — đường RPS theo thời gian (xanh = total, đỏ = fails). Xác định throughput thực tế.
- **Response Time (ms)** — 2 đường p50 (median) và p95 theo thời gian, xem độ ổn định.
- **Number of Users** — số virtual user đang hoạt động theo thời gian (ramp-up thấy rõ).

*Khối "Failures":* liệt kê các loại lỗi — exception/HTTP code + số lần xảy ra. Với LT-01 sẽ thấy `409 Conflict` × 95 (out_of_stock đúng kỳ vọng).

*Khối "Exceptions":* các exception phát sinh phía Locust client (không phải lỗi server) — thường rỗng.

Chi tiết tham số mỗi LT + cách verify DB state sau khi chạy (tồn kho cuối, số voucher phát thành công…): xem `tmp/tests/README.md`.

---

## 8. Kịch bản demo đề xuất

Năm kịch bản dưới đây bao quát các luồng nghiệp vụ chính của hệ thống ngoài bộ kiểm thử tự động:

1. **Đăng ký khách hàng mới** — Khách truy cập `/register` đăng ký bằng email mới, sau đó tham gia một đối tác tại `/member/partners`.
2. **Nhân viên ghi giao dịch tích điểm** — Nhân viên `staff1@cafe.vn` đăng nhập và mở `/staff/pos`, quét QR khách hoặc nhập số điện thoại kèm số tiền hoá đơn; hệ thống tự cộng điểm theo rule của shop.
3. **Khách hàng đổi quà** — Khách `khach3@gmail.com` (đã có sẵn ~2650 điểm) chọn đối tác Cafe Cộng tại `/member/partners/cafe-cong` và đổi một phần thưởng phù hợp; hệ thống cấp mã OTP. Nhân viên `staff1@cafe.vn` xác nhận tại `/staff/redeem` bằng OTP đó.
4. **Chủ shop xem báo cáo** — Chủ shop `owner@cafe.vn` đăng nhập vào `/merchant`; dashboard hiển thị tổng giao dịch, điểm phát/tiêu, top khách. Các trang chi tiết: `/merchant/customers`, `/merchant/transactions`, `/merchant/rewards`.
5. **Super admin giám sát** — Super admin `admin@loyalty.vn` truy cập `/admin` để xem tổng quan đa đối tác, quản lý điểm hệ thống và log audit.

---

## 9. Lệnh hữu ích

```bash
# Xem log một service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Khởi động lại 1 service
docker compose restart backend

# Truy cập database
docker compose exec postgres psql -U loyalty -d loyalty
# (\dt xem bảng, \q thoát)

# Tạm dừng / khởi động lại (giữ dữ liệu)
docker compose stop
docker compose start

# Xoá container, GIỮ database
docker compose down

# Xoá container VÀ database (reset hoàn toàn)
docker compose down -v
```

---

## 10. Xử lý sự cố thường gặp

**`port is already allocated`** — Cổng 3000/8000/5433 đang bị chiếm. Kiểm tra `netstat -ano | findstr :3000` (Windows) hoặc `lsof -i :3000` (Linux). Đóng app chiếm cổng, hoặc đổi cổng trong `docker-compose.yml` (vd `"3000:3000"` → `"3001:3000"`).

**Backend không healthy, log có `could not connect to postgres`** — Postgres chưa sẵn sàng. Đợi 30s rồi `docker compose restart backend`.

**Frontend `Network Error` khi đăng nhập** — Kiểm tra `NEXT_PUBLIC_API_URL` trong `frontend/.env.local` (mặc định `http://localhost:8000`). Rebuild: `docker compose up -d --build frontend`.

**Test E2E `connection refused` đến container Postgres** — Container đang dùng tên khác. `docker compose ps` để xem tên thực tế, set lại biến `PG_CONTAINER` và `BE_CONTAINER`.

**Test E2E `python: command not found` hoặc `pytest: command not found`** — Chưa cài Python hoặc Python không có trong PATH. Cài Python 3.10+ từ python.org (Windows nhớ tick "Add to PATH"), sau đó chạy lại `python -m pip install pytest httpx pytest-html`.

**Trang trắng / lỗi 500** — Xem log: `docker compose logs --tail 50 backend` và `docker compose logs --tail 50 frontend`.

**Reset toàn bộ dữ liệu để demo lại từ đầu:**

```bash
docker compose down -v
docker compose up -d --build
docker compose exec backend python seed_demo.py
```

**Build lại sau khi sửa code:**

```bash
docker compose up -d --build backend     # chỉ backend
docker compose up -d --build frontend    # chỉ frontend
```

---

## 11. Cấu trúc thư mục dự án

```
DoAn/
├── backend/                  Mã nguồn FastAPI + SQLAlchemy + Alembic
│   ├── app/                    - Source chính (api, services, models, schemas)
│   ├── alembic/                - Migration database
│   ├── tests/                  - Test (unit + integration)
│   └── seed_demo.py            - Script seed dữ liệu demo
├── frontend/                 Mã nguồn Next.js 14 + Tailwind + shadcn/ui
│   └── src/app/                - Route theo App Router (admin, merchant, staff, member, auth)
├── tests_e2e/                Pytest E2E — 44 test theo Bảng 4-1 báo cáo
│   ├── test_group_a_auth.py    - Nhóm A (Xác thực)
│   ├── test_group_b_partner.py - Nhóm B (Đối tác)
│   ├── test_group_c_pos.py     - Nhóm C (POS + đổi quà)
│   ├── test_group_d_admin.py   - Nhóm D (Quản trị)
│   └── README.md               - Mapping TC ↔ test function
├── tmp/tests/                Locust load test — 5 kịch bản theo Bảng 4-2 báo cáo
│   ├── load/locustfile.py      - 5 LT class (LT-01..LT-05)
│   ├── load/setup_data.py      - Tạo customer + cache token + setup reward
│   └── README.md               - Chi tiết tham số + cách verify
├── docs/                     Spec + plan + thiết kế
├── bao-cao/                  File báo cáo + ảnh minh hoạ
├── docker-compose.yml        Cấu hình môi trường chạy thử (dev)
├── docker-compose.prod.yml   Cấu hình môi trường production
└── README.md                 File đang đọc
```

---

## 12. Thông tin liên hệ

- Sinh viên thực hiện: **Nguyễn Hải Đăng**
- Email: dang.nguyenhai2k2@gmail.com
- URL bản demo online: https://loyalty.ecom-bill.com
