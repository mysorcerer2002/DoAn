# Đồ án thực tập tốt nghiệp: Xây dựng hệ thống website cung cấp giải pháp chăm sóc khách hàng thân thiết cho doanh nghiệp SME

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

*Tính năng "Quên mật khẩu" cần SMTP để gửi email đặt lại. Nếu để trống các biến `SMTP_*` trong `backend/.env`, hệ thống vẫn chạy bình thường — chỉ là email reset không được gửi. Để bật, cấu hình:*

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<địa chỉ Gmail>
SMTP_PASSWORD=<Gmail App Password 16 ký tự>
SMTP_FROM_EMAIL=<địa chỉ Gmail>
SMTP_FROM_NAME=Loyalty Platform
SMTP_USE_TLS=True
```

*Tạo Gmail App Password tại https://myaccount.google.com/apppasswords (yêu cầu đã bật 2-Step Verification trên tài khoản Google), sau đó dán chuỗi 16 ký tự vào `SMTP_PASSWORD`.*

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

## 7. Bộ kiểm thử tự động (unit + integration backend)

Backend container đã sẵn pytest, không cần cài Python trên host:

```bash
docker compose exec backend pytest -v                     # toàn bộ
docker compose exec backend pytest tests/unit -v          # unit only
docker compose exec backend pytest tests/integration -v   # integration
```

Phần integration dùng testcontainers (cần quyền điều khiển Docker từ trong container) nên phụ thuộc Docker socket — không phải môi trường nào cũng đáp ứng.

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
