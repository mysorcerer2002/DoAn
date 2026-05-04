# Loyalty Platform — Đồ án thực tập tốt nghiệp

Hệ thống tích điểm thành viên đa đối tác cho SME (cà phê, nhà hàng, shop bán lẻ).
Sinh viên thực hiện: **Nguyễn Hải Đăng**.

**Stack:** FastAPI + SQLAlchemy 2.0 async + PostgreSQL 15 + Alembic · Next.js 14 App Router + Tailwind v4 + shadcn/ui · Docker Compose.

---

## 1. Chuẩn bị source code

**Cách A — Giải nén từ file ZIP:**

1. Giải nén ZIP vào một thư mục, ví dụ `C:\DoAn` (Windows) hoặc `~/DoAn` (macOS/Linux).
2. Mở terminal và `cd` vào thư mục đó.

**Cách B — Clone từ Git:**

```bash
git clone <URL_REPOSITORY> DoAn
cd DoAn
```

Sau bước này, `ls` (hoặc `dir`) phải thấy `docker-compose.yml`, `backend/`, `frontend/`, `README.md`.

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

*(Tuỳ chọn — sinh ngẫu nhiên `JWT_SECRET` cho an toàn hơn)*

```powershell
# Windows PowerShell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
```

```bash
# macOS / Linux
openssl rand -hex 32
```

Sao chép chuỗi kết quả, mở `backend/.env`, gán vào biến `JWT_SECRET=`.

---

## 3. Khởi động toàn bộ hệ thống

```bash
docker compose up -d --build
```

Lệnh trên:

1. Pull image PostgreSQL 15.
2. Build image Backend (FastAPI, Python 3.11).
3. Build image Frontend (Next.js 14, Node 20).
4. Khởi động 3 container theo thứ tự: postgres → backend → frontend.
5. Backend tự động chạy Alembic migrations để tạo schema khi start.

Lần đầu build mất 5–10 phút tuỳ tốc độ mạng. Các lần sau chỉ vài giây.

Theo dõi tiến trình:

```bash
docker compose logs -f
```

Nhấn `Ctrl+C` để thoát theo dõi (container vẫn chạy nền).

Kiểm tra cả 3 container đã healthy:

```bash
docker compose ps
```

Cột `STATUS` phải hiển thị `Up ... (healthy)` cho `loyalty-postgres`, `loyalty-backend`, `loyalty-frontend`.

---

## 4. Kiểm tra hệ thống đã chạy

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

- Backend API docs (Swagger UI): http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 5. Nạp dữ liệu demo

```bash
docker compose exec backend python seed_demo.py
```

Script tạo:

- 1 super admin
- 2 đối tác (Cafe Cộng, Trà Sữa Lala) với đầy đủ tier, point rule, reward
- 4 nhân viên (staff)
- 10 khách hàng đã tham gia membership
- ~65 giao dịch POS trong 14 ngày gần nhất
- Bút toán point ledger + một số redemption mẫu

Khi script in dòng `✅ Seed completed` là hoàn tất. Có thể chạy lại nhiều lần — script idempotent, không nhân đôi dữ liệu.

---

## 6. Tài khoản demo

Truy cập: http://localhost:3000/login

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

## 7. Chạy test case tự động (Bảng 4-1 báo cáo, Chương 4)

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

### 7.2. Chạy toàn bộ 44 test case + xuất báo cáo HTML

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

### 7.3. Xem báo cáo HTML

Mở `tests_e2e/results/report.html` bằng trình duyệt. Báo cáo gồm:

- Dashboard tổng quan: số test PASS / FAIL / duration.
- Danh sách từng test theo nhóm A/B/C/D.
- Click vào tên test để xem chi tiết: request, response, DB state, assertion.

### 7.4. Chạy chọn lọc 1 nhóm hoặc 1 test case

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

### 7.5. Test backend (unit + integration) — chạy trong container

Không cần cài Python trên host:

```bash
docker compose exec backend pytest -v                     # toàn bộ
docker compose exec backend pytest tests/unit -v          # unit only
docker compose exec backend pytest tests/integration -v   # integration
```

Integration test dùng testcontainers (yêu cầu quyền điều khiển Docker từ trong container) — nếu báo lỗi liên quan đến Docker socket, có thể bỏ qua phần integration; bộ E2E ở mục 7.2 đã đủ để đánh giá chức năng đầu-cuối.

---

## 8. Kịch bản demo đề xuất

1. **Đăng ký khách hàng mới** — Vào http://localhost:3000/register, đăng ký bằng email mới. Đăng nhập, vào `/member/partners`, tham gia một đối tác.
2. **Nhân viên ghi giao dịch tích điểm** — Đăng nhập `staff1@cafe.vn / staff1234`. Vào `/staff/pos`, quét QR khách hoặc nhập số điện thoại, nhập số tiền hoá đơn, xác nhận → hệ thống cộng điểm tự động.
3. **Khách hàng đổi quà** — Đăng nhập `khach3@gmail.com / khach1234` (đã có ~2650 điểm). Vào `/member`, chọn đối tác Cafe Cộng → `/member/partners/cafe-cong`, bấm "Đổi quà". Mã OTP hiển thị, copy lại. Đăng nhập `staff1@cafe.vn`, vào `/staff/redeem`, nhập OTP → xác nhận.
4. **Chủ shop xem báo cáo** — Đăng nhập `owner@cafe.vn / owner1234`. Dashboard `/merchant` hiển thị tổng giao dịch, điểm phát/tiêu, top khách. Vào `/merchant/customers`, `/merchant/transactions`, `/merchant/rewards`.
5. **Super admin giám sát** — Đăng nhập `admin@loyalty.vn / admin1234`. Vào `/admin` để xem tổng quan đa đối tác, quản lý điểm hệ thống, log.

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
