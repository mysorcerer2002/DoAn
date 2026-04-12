# Nền tảng Tích điểm Thành viên & Quản lý Chương trình Khuyến mãi

**Ngày:** 2026-04-12
**Loại:** Đề tài thực tập tốt nghiệp (8 tuần) — có khả năng scale lên luận văn tốt nghiệp
**Stack:** Next.js (frontend + PWA) + FastAPI (backend)

---

## 1. Tổng quan

### 1.1. Tên đề tài
**Nền tảng Tích điểm Thành viên và Quản lý Chương trình Khuyến mãi cho Doanh nghiệp vừa và nhỏ** (multi-tenant loyalty platform).

### 1.2. Mục tiêu
Xây dựng một platform **multi-tenant** cho phép nhiều doanh nghiệp vừa và nhỏ (quán cà phê, nhà hàng, shop bán lẻ) tự vận hành chương trình khách hàng thân thiết mà không cần tự phát triển hệ thống riêng. Hệ thống hỗ trợ quản lý thành viên, tích/đổi điểm, phát hành voucher khuyến mãi, và phân hạng thành viên.

### 1.2.1. Tiêu chí hoàn thành MVP (acceptance criteria)
Sau 8 tuần thực tập, sản phẩm phải đạt **tất cả** các tiêu chí sau:
1. **Demo end-to-end 1 kịch bản đầy đủ:** đăng ký tenant → Super Admin duyệt → cấu hình tier + point rule → nhân viên tạo giao dịch (3 cách: thủ công, QR shop, QR khách) → khách đổi quà nhận mã redemption → tạo campaign → khách claim voucher → dùng voucher → kích hoạt upgrade tier → nhận voucher sinh nhật.
2. **Multi-tenant isolation chứng minh được:** chạy 2 tenant song song, có test tự động đảm bảo dữ liệu không lẫn (`tests/integration/test_tenant_isolation.py` pass 100%).
3. **Point ledger reconcile khớp:** test invariant `SUM(point_ledger.delta) WHERE membership_id = X = memberships.points_balance` đúng với mọi membership trong seed data + sau mọi luồng test.
4. **Dashboard hiển thị 5 chỉ số:** số thành viên, giao dịch theo ngày, doanh thu, tỉ lệ đổi điểm, phân bố hạng. (ROI campaign là chỉ số nâng cao, ưu tiên thấp hơn.)
5. **PWA `/member` cài được trên Android Chrome thật:** mở offline vẫn xem được điểm + voucher đã có (dữ liệu cache).
6. **Có deploy demo chạy được:** Docker Compose local + ngrok ở mức tối thiểu, hoặc VPS nếu kịp.
7. **Báo cáo + slide demo:** file PDF báo cáo + 5–10 slide presentation cho buổi bảo vệ.

### 1.3. Người dùng mục tiêu
Hệ thống phục vụ **4 vai trò**:

| Vai trò | Mô tả | Giao diện |
|---|---|---|
| **Super Admin** | Quản lý platform, duyệt doanh nghiệp đăng ký | Web `/admin` — **MVP chỉ có 1 trang duy nhất:** danh sách tenant `pending` + nút Approve/Reject. Các thao tác khác (suspend, audit, edit) làm qua Swagger hoặc DB trực tiếp. |
| **Chủ doanh nghiệp** | Cấu hình chương trình tích điểm, tạo quà/khuyến mãi, xem thống kê | Web `/merchant` |
| **Nhân viên cửa hàng** | Nhập giao dịch, quét QR khách, xác nhận đổi quà | Web `/pos` (tối ưu cho tablet) |
| **Khách hàng cuối** | Xem điểm, hạng, lịch sử, đổi quà, xem voucher, hiển thị QR cá nhân | PWA `/member` |

### 1.4. Giả định phạm vi nghiệp vụ (MVP)
- **1 tenant = 1 cửa hàng đơn lẻ.** MVP không hỗ trợ nhiều chi nhánh cho 1 tenant — doanh nghiệp có nhiều chi nhánh sẽ đăng ký nhiều tenant riêng. Multi-store dành cho luận văn.
- **Tiếng Việt là ngôn ngữ duy nhất.** Không dùng i18n library trong MVP. Đa ngôn ngữ dành cho luận văn.
- **Đơn vị tiền tệ duy nhất là VND.**
- **MVP KHÔNG xử lý thanh toán.** Nhân viên tự nhận tiền (cash/chuyển khoản thủ công với khách), sau đó nhập số tiền vào `/pos` để hệ thống quy đổi điểm. Tích hợp cổng thanh toán (VNPay, Momo, ZaloPay) dành cho luận văn.
- **Múi giờ duy nhất: `Asia/Ho_Chi_Minh` (UTC+7).** Database lưu UTC (`TIMESTAMPTZ`), backend/frontend convert khi hiển thị. Mọi date-based logic (sinh nhật, voucher expire, campaign window, birthday job scheduler) BẮT BUỘC dùng `Asia/Ho_Chi_Minh` — không phụ thuộc vào timezone server. `users.birthday` là `DATE` không timezone, so sánh theo lịch VN.
- **Verification code (OTP) qua log console.** MVP không tích hợp SMS/email provider thật. Sinh viên đọc log backend → đọc cho khách demo. Luận văn mới upgrade sang SMS/email thật qua adapter pattern (đã chuẩn bị interface).

---

## 2. Phạm vi

### 2.1. Phạm vi MVP — **phải hoàn thành trong 8 tuần thực tập**

| # | Module | Nội dung chính |
|---|---|---|
| 1 | **Xác thực & phân quyền** | Đăng ký, đăng nhập, JWT (chỉ chứa `user_id` + `system_role`), refresh token. Phân quyền 4 vai trò qua header `X-Tenant-Id` + DB lookup với cache TTL 60s. (Rate limiting `slowapi` là cross-cutting concern, xem 3.1 và 6.7.) |
| 2 | **Quản lý doanh nghiệp (tenant)** | Đăng ký doanh nghiệp → Super Admin duyệt (MVP: minimal UI + Swagger). Chủ doanh nghiệp cấu hình thông tin, quy tắc tích điểm, quản lý nhân viên. |
| 3 | **Quản lý thành viên** | Đăng ký kết hợp: khách tự đăng ký trên PWA HOẶC nhân viên tạo shadow account bằng SĐT. Khách "nhận" tài khoản bằng verification code (bảng `verification_codes`). |
| 4 | **Giao dịch tích điểm** | 3 cách: (a) nhân viên nhập SĐT thủ công (default cho khách mới ở tenant — Luồng B), (b) khách đã có app quét QR cửa hàng, (c) nhân viên quét QR cá nhân khách đã là thành viên tenant. Cách (c) nếu khách chưa là thành viên → fall back về (a). Mỗi giao dịch ghi vào `point_ledger`. |
| 5 | **Hạng thành viên** | Cấu hình theo từng doanh nghiệp (vd Bronze/Silver/Gold). Tự động lên hạng theo `total_points_earned`. Sắp xếp theo `min_points ASC`. |
| 6 | **Đổi điểm lấy quà** | Catalog quà riêng mỗi doanh nghiệp. Khách đổi → sinh mã redemption → nhân viên xác nhận. Ghi ledger. |
| 7 | **Chiến dịch khuyến mãi (lazy claim)** | Chủ doanh nghiệp tạo campaign với điều kiện. Hệ thống KHÔNG sinh voucher hàng loạt. Khách vào `/member` → thấy campaign đủ điều kiện → bấm "Nhận" → sinh voucher cá nhân. |
| 8 | **Ưu đãi sinh nhật** | Background job hàng ngày (APScheduler) tạo voucher cá nhân cho khách có sinh nhật hôm nay, dùng "campaign sinh nhật" cấu hình trong `tenants.settings`. |
| 9 | **Point Ledger (audit trail)** | Bảng append-only ghi nhận mọi biến động điểm (tích, đổi, điều chỉnh). Cho phép reconcile balance bất cứ lúc nào. |
| 10 | **Dashboard & báo cáo cơ bản** | Thành viên, giao dịch theo ngày, doanh thu, tỉ lệ đổi điểm, phân bố hạng, **ROI campaign** (doanh thu từ transactions có voucher). |
| 11 | **Giao diện Web + PWA** | Next.js: `/admin`, `/merchant`, `/pos` + PWA `/member` (manifest, service worker, cài được trên điện thoại). |

### 2.2. Phạm vi để dành cho giai đoạn luận văn (KHÔNG làm trong 8 tuần)

- **ML cá nhân hóa:** gợi ý quà/voucher phù hợp từng khách (content-based + collaborative filtering)
- **Phân khúc khách hàng (RFM + K-means):** chạy chiến dịch trúng đối tượng
- **Dự báo churn:** cảnh báo khách sắp rời bỏ (classification model)
- **Gamification:** huy hiệu, challenges, streak bonus, thanh tiến độ
- **Referral program:** giới thiệu bạn bè nhận điểm
- **Mobile app native:** React Native / Flutter thay cho PWA
- **Real-time notifications:** WebSocket + Web Push
- **Tích hợp API với POS bên thứ ba:** webhook, REST API công khai
- **Báo cáo nâng cao:** custom report, funnel, cohort analysis
- **Multi-store cho 1 tenant** (nhiều chi nhánh, nhân viên theo chi nhánh)
- **OTP SMS thật** (brand name, tốn phí)
- **Super Admin UI đầy đủ** (audit logs, suspend tenant, billing...)
- **Đa ngôn ngữ & đa tiền tệ**

### 2.3. Vì sao phạm vi này vừa đủ cho 8 tuần
- Tập trung **nghiệp vụ cốt lõi** — không bị phân tán bởi ML/mobile/integration.
- **Multi-tenant + Point Ledger** có từ MVP → không phải refactor core khi mở rộng.
- **Lazy claim voucher** tránh sinh viên vướng vấn đề performance của bulk issue.
- Các tính năng giai đoạn luận văn chủ yếu là **thêm module mới**, không phải sửa cũ.

**Ví dụ cụ thể về việc không cần refactor core khi scale:**
- **Thêm RFM/K-means/churn:** chỉ cần 1 module `ml/` mới + 1 bảng `member_segments` + 1 background job offline. KHÔNG đổi `transactions`, `memberships`, `point_ledger`.
- **Thêm multi-store:** thêm bảng `stores` + cột `store_id` nullable trên `transactions` (default NULL = single-shop legacy). KHÔNG đổi ledger logic.
- **Thêm React Native app:** thêm endpoint FCM token registration (1 bảng + 2 endpoints). Business logic backend giữ nguyên 100%.
- **Thêm public REST API cho POS bên thứ ba:** thêm bảng `api_keys` + middleware HMAC signature. Reuse toàn bộ service layer hiện tại.
- **Audit log đầy đủ (tenant settings, staff actions):** đã có schema `security_audit_log` (xem 6.11) — chỉ việc insert thêm event types mới, không đổi pattern.

---

## 3. Kiến trúc & Stack công nghệ

### 3.1. Stack

| Lớp | Công nghệ |
|---|---|
| **Frontend** | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 15+ (multi-tenant theo cột `tenant_id`) |
| **Auth** | JWT (chỉ `user_id` + `system_role`), bcrypt cost ≥ 12, refresh token lưu DB |
| **Rate limiting** | `slowapi` middleware — bảo vệ auth, transaction, QR, claim-shadow. **Caveat:** mọi endpoint dùng `@limiter.limit` BẮT BUỘC phải có `request: Request` param (lỗi runtime chứ không phải compile time). Không rate limit theo body được vì decorator chạy trước khi parse — phải dùng `key_func` custom đọc từ header hoặc user_id sau auth. |
| **Background jobs** | APScheduler (in-process), bật/tắt theo biến môi trường `ENABLE_SCHEDULER`. **Bắt buộc chạy 1 worker duy nhất** khi bật scheduler — xem 3.2 và 6.9 |
| **QR code** | `qrcode` (Python, sinh QR tĩnh) + `html5-qrcode` (frontend quét) |
| **PWA** | `@serwist/next` (successor của `next-pwa` — package gốc đã không còn maintain, `@serwist/next` được khuyến nghị chính thức trong Next.js docs từ 2025, hỗ trợ App Router) + manifest + icons (192/512/maskable) + service worker (offline-first cho `/member`) |
| **Testing** | pytest + httpx + PostgreSQL testcontainers (backend), Vitest + RTL (frontend) |
| **Dev tools** | Docker Compose (postgres + backend + frontend), Alembic (migration), `.env.example` commit vào git |
| **Seed data** | Script `scripts/seed.py` — tạo sẵn 2 tenant, 5 tier, 20 khách, 100 giao dịch cho demo |

### 3.2. Kiến trúc tổng thể

```
┌──────────────────────────────────────────────────────────────┐
│                    Next.js (Frontend)                        │
│  ┌─────────┐  ┌──────────┐  ┌───────┐  ┌──────────────────┐  │
│  │ /admin  │  │/merchant │  │ /pos  │  │ /member (PWA)    │  │
│  │ super   │  │ owner    │  │ staff │  │ customer         │  │
│  └────┬────┘  └────┬─────┘  └───┬───┘  └────────┬─────────┘  │
│       └────────────┴────────────┴───────────────┘            │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTPS + JWT + X-Tenant-Id header
┌──────────────────────────▼───────────────────────────────────┐
│                    FastAPI (Backend)                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Middleware: CORS, RateLimit, Auth, TenantContext       │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌──────┬────────┬─────────┬──────┬──────────┬────────────┐  │
│  │ Auth │ Tenant │ Member  │ Txn  │ Reward   │ Campaign   │  │
│  └──────┴────────┴─────────┴──────┴──────────┴────────────┘  │
│  ┌──────┬────────┬─────────┬──────────────┬────────────────┐ │
│  │ Tier │ Ledger │ Voucher │ Notification │ Analytics      │ │
│  └──────┴────────┴─────────┴──────────────┴────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Background Jobs (APScheduler — ENABLE_SCHEDULER)    │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│             PostgreSQL (multi-tenant by tenant_id)           │
└──────────────────────────────────────────────────────────────┘
```

**Các component hạ tầng không vẽ trong diagram (cần quyết định trước khi code):**

| Component | MVP | Luận văn |
|---|---|---|
| **File upload** (ảnh rewards, logo shop, avatar) | Local filesystem `backend/uploads/`, mount volume Docker, serve tĩnh qua `/uploads/*` | S3/MinIO + pre-signed URL |
| **Email outbound** (notification, verification) | Mailtrap (SMTP fake) — không gửi email thật, chỉ xem inbox giả lập để test | Provider thật (SendGrid, Resend, AWS SES) |
| **SMS outbound** (verification code) | Log ra console backend (không dùng provider) | Twilio / eSMS VN |
| **DB migration runner** | Docker entrypoint backend chạy `alembic upgrade head` trước `uvicorn` | Tương tự, thêm script rollback manual |
| **Background scheduler** | APScheduler in-process (xem 6.9), chạy **1 worker duy nhất** khi bật | Celery + Redis nếu volume lớn |
| **File logs** | Ghi vào stdout + `backend/logs/` (app log, birthday job log) | Cloud logging (Grafana Loki / Datadog) |

### 3.3. Mô hình Multi-tenant

#### Isolation strategy
**Shared database, shared schema**, phân tách bằng cột `tenant_id` trong mọi bảng nghiệp vụ. Mọi query bắt buộc có `WHERE tenant_id = X`.

#### Xác định tenant context mỗi request
- **`/merchant`, `/pos`:** bắt buộc header `X-Tenant-Id`. Middleware `get_current_tenant()` thực hiện:
  1. Đọc `X-Tenant-Id` từ header
  2. Lookup `(user_id, tenant_id)` trong cache `cachetools.TTLCache(maxsize=1024, ttl=60)`
  3. Cache miss → query `SELECT role FROM tenant_staff WHERE user_id=? AND tenant_id=?`
  4. Cache value = `(role, checked_at)` — **cache `role` chứ không chỉ boolean** (để phân biệt `owner` vs `staff`, quan trọng cho dependency `require_owner_in_tenant()`)
  5. Inject `(tenant_id, role)` vào request state

- **`/admin`:** không cần header (Super Admin xuyên tenant, chỉ check `system_role`)
- **`/member`:** khách có nhiều membership. Frontend truyền tenant qua route param `/member/shops/{slug}/rewards`; backend verify `membership` tồn tại trong tenant đó.

#### Vì sao JWT không chứa tenant list
- Cấp quyền staff mới không cần bắt user re-login
- Nhân viên làm nhiều shop: không phải pass-around cả list trong mỗi request
- Revoke / đổi role có hiệu lực ngay (≤ 60s) mà không cần refresh token hay blacklist

#### Trade-off cache 60s & invalidation
- **Chấp nhận:** invalidation tối đa 60s. Owner revoke staff → staff vẫn thao tác được API tối đa 1 phút.
- **OK cho MVP** (đồ án thực tập, không dùng cho production finance-critical).
- **Dev / demo chạy 1 worker** → không có vấn đề stale giữa các worker.
- **Nếu chạy nhiều worker** (production-ish): mỗi worker có cache in-memory riêng → revoke mất tối đa N × 60s để hiệu lực trên toàn hệ thống. Giải pháp luận văn: chuyển cache sang Redis (single source of truth) hoặc giảm TTL xuống 5–10s.
- **KHÔNG dùng `functools.lru_cache`** — không có TTL thật (chỉ evict khi full). Bắt buộc dùng `cachetools.TTLCache`.
- **Endpoint admin invalidate cache** (optional cho MVP): `POST /internal/cache/invalidate` để force refresh khi cần — có sẵn cho giảng viên phản biện hỏi.

#### Scale lên luận văn
Kiến trúc hiện tại cho phép chuyển sang schema-per-tenant (mỗi tenant 1 PostgreSQL schema riêng) khi cần. Chỉ cần đổi DB connection logic + middleware set `search_path`, service layer không đổi.

### 3.4. Tổ chức mã nguồn (monorepo)

```
D:/DoAn/
├── backend/
│   ├── app/
│   │   ├── core/              # config, security, db, middleware, deps, cache
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # routers theo module
│   │   │   ├── auth.py
│   │   │   ├── tenants.py
│   │   │   ├── members.py
│   │   │   ├── transactions.py
│   │   │   ├── rewards.py
│   │   │   ├── campaigns.py
│   │   │   ├── vouchers.py
│   │   │   ├── tiers.py
│   │   │   ├── ledger.py
│   │   │   ├── notifications.py
│   │   │   └── analytics.py
│   │   ├── services/          # business logic
│   │   ├── jobs/              # APScheduler entrypoints + run_once CLI
│   │   └── main.py
│   ├── alembic/
│   ├── scripts/
│   │   ├── seed.py            # chạy: `cd backend && python -m scripts.seed`
│   │   └── backup.sh          # pg_dump thủ công trước demo
│   ├── tests/
│   │   ├── unit/              # business logic tests, không cần DB
│   │   └── integration/       # cần PostgreSQL testcontainer
│   │       ├── test_tenant_isolation.py
│   │       ├── test_ledger_invariant.py
│   │       └── ...
│   ├── uploads/               # file upload local (mount Docker volume, .gitignored)
│   ├── logs/                  # app log + birthday job log (.gitignored)
│   ├── .env.example
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/        # login, register
│   │   │   ├── admin/         # super admin
│   │   │   ├── merchant/      # business owner
│   │   │   ├── pos/           # staff
│   │   │   └── member/        # customer PWA (tên `member` để tránh trùng Next.js app router folder `src/app/`)
│   │   ├── components/
│   │   ├── lib/               # API client, hooks
│   │   └── types/
│   ├── public/
│   │   ├── manifest.json
│   │   ├── icons/             # PWA icons (192x192, 512x512, 192-maskable, 512-maskable)
│   │   └── sw.js              # service worker (do @serwist/next sinh ra)
│   ├── .env.example
│   └── package.json
├── Makefile                   # make dev | make test | make seed | make lint | make migrate | make up
├── README.md                  # hướng dẫn setup + chạy demo + troubleshoot
├── .pre-commit-config.yaml    # ruff, black, prettier — tránh commit messy code
├── docker-compose.yml         # postgres + backend + frontend + mailtrap (dev)
├── .gitignore
└── docs/
    └── superpowers/specs/2026-04-12-loyalty-platform-design.md
```

**Lệnh chính trong Makefile:**
```makefile
make up              # docker compose up -d
make migrate         # cd backend && alembic upgrade head
make seed            # cd backend && python -m scripts.seed
make dev-backend     # cd backend && uvicorn app.main:app --reload (ENABLE_SCHEDULER=false)
make dev-frontend    # cd frontend && npm run dev
make test            # cd backend && pytest && cd ../frontend && npm test
make lint            # ruff + black + prettier
make backup          # ./backend/scripts/backup.sh
```

---

## 4. Data Model

### 4.1. Các entity chính và quan hệ

```
users ──┬── tenant_staff ── tenants ── point_rules
        │                     │
        │                     ├── tiers
        │                     ├── rewards ─── redemptions ──┐
        │                     ├── campaigns ── vouchers ────┤
        │                     ├── notifications             │
        │                     │                             ▼
        ├── memberships ──────┴── transactions ─── point_ledger
        │
        └── verification_codes (claim shadow, reset password)
```

### 4.2. Các bảng chính

#### `users`
Tài khoản toàn hệ thống. Một user có thể là khách hàng ở nhiều tenant.
```
id, email (nullable, format chuẩn email), phone (nullable nhưng shadow bắt buộc có, format E.164 +84...),
password_hash (nullable cho shadow chưa claim),
full_name, birthday (DATE — không timezone, so sánh theo lịch Asia/Ho_Chi_Minh),
is_active (false = soft-deactivate, không hard delete để giữ FK integrity),
is_shadow (true = nhân viên tạo hộ, chưa claim),
system_role (super_admin | regular),
last_login_at (nullable TIMESTAMPTZ — cập nhật mỗi lần login, dùng cho dashboard "active users" và feature ML churn ở luận văn),
created_at
```
**Lưu ý:** users không hard delete. Để xóa, set `is_active=false`. Luận văn thêm `anonymize_user(user_id)` xóa PII (email, phone, full_name) nhưng giữ row cho FK.

#### `tenants`
Doanh nghiệp đăng ký platform.
```
id, name, slug (unique), owner_user_id, status (pending | active | suspended),
logo_url, description, settings (JSON — xem 4.4), created_at
```

#### `tenant_staff`
Liên kết user với tenant theo vai trò.
```
id, tenant_id, user_id, role (owner | staff), added_at
UNIQUE(tenant_id, user_id)
```

#### `memberships`
Mối quan hệ khách ↔ tenant. Mỗi khách ở mỗi tenant có 1 membership.
```
id, tenant_id, user_id, current_tier_id,
points_balance (cache, CHECK >= 0),
total_points_earned (cache, dùng cho upgrade tier — chỉ tăng, không giảm),
joined_at, last_activity_at,
archived_at (nullable TIMESTAMPTZ — MVP chưa dùng, luận văn dùng cho churn model phân biệt active vs churned)
UNIQUE(tenant_id, user_id)
```
**Lưu ý:** không có cột `membership_code`. QR cá nhân dùng trực tiếp `user_id` trong JWT signed payload (xem 6.2).

#### `tiers`
Cấu hình hạng thành viên của mỗi tenant.
```
id, tenant_id, name, min_points, perks (JSON — ví dụ hệ số nhân điểm, % giảm mặc định),
is_active, deleted_at (nullable, soft delete)
```
Sắp xếp bằng `ORDER BY min_points ASC` — không cần `sort_order`.

#### `point_rules`
Quy tắc tính điểm của mỗi tenant (MVP: mỗi tenant 1 rule).
```
id, tenant_id, points_per_unit (vd 1 điểm / 1000 VND),
min_amount, is_active
```

#### `transactions`
Ghi nhận mỗi giao dịch tích điểm.
```
id, tenant_id, membership_id, staff_id,
gross_amount (giá trước voucher),
voucher_id (nullable FK — voucher được áp dụng nếu có),
voucher_discount_amount (nullable, VND giảm thực tế từ voucher),
net_amount (sau voucher = gross - voucher_discount),
points_earned, method (manual | qr_shop | qr_customer),
note, created_at
```
- Điểm tính trên `net_amount` mặc định. Nếu `tenants.settings.points_on_gross = true` thì tính trên `gross_amount`.
- `voucher_discount_amount` lưu **VND giảm thực tế** áp dụng (sau khi cap `max_discount` từ campaign), khác với `campaigns.discount_value` (raw config). Cần thiết để tính ROI campaign chính xác.
- **Idempotency key:** MVP CHƯA có (sinh viên ghi vào note "đã biết, dành cho luận văn khi có mobile client"). Nếu staff retry transaction → có thể tạo duplicate. Workaround MVP: nhân viên kiểm tra trên màn hình trước khi bấm submit.
- **Transaction status (active | cancelled):** MVP KHÔNG có cột `status` — không hỗ trợ hủy giao dịch (xem Luồng I dành cho luận văn). Workaround: nếu staff nhập sai → admin dùng `POST /admin/adjust-points` để ghi ledger điều chỉnh manual.

#### `point_ledger` ★ QUAN TRỌNG
**Bảng append-only** ghi mọi biến động điểm. KHÔNG cho phép UPDATE/DELETE (trừ qua migration).
```
id, tenant_id, membership_id,
delta (integer — dương = cộng, âm = trừ),
reason (earn | redeem | adjust | expire | refund),
ref_type (transaction | redemption | manual | system),
ref_id (id của record nguồn),
balance_after (snapshot balance sau khi áp delta),
description, created_at
```
- Mỗi khi `points_balance` thay đổi → BẮT BUỘC insert 1 dòng ledger TRONG CÙNG DB transaction.
- **Reconcile rule:** `SUM(delta) WHERE membership_id = X` phải bằng `memberships.points_balance`.
- Có endpoint admin `POST /admin/reconcile/{membership_id}` để kiểm tra và báo lỗi nếu lệch.
- Là nền tảng cho các feature luận văn: audit, hoàn/hủy giao dịch, tính toán data cho ML.

#### `rewards`
Catalog quà tặng.
```
id, tenant_id, name, description, image_url,
points_cost, stock (INTEGER nullable — NULL = không giới hạn, CHECK stock IS NULL OR stock >= 0),
is_active, deleted_at (nullable, soft delete), created_at
```
- Query check còn hàng: `WHERE stock IS NULL OR stock > 0` (không dùng sentinel `-1`).

#### `redemptions`
Lịch sử khách đổi điểm lấy quà.
```
id, tenant_id, membership_id, reward_id, points_spent,
redemption_code (8 ký tự — xem 4.5),
status (pending | used | expired),
redeemed_at, used_at (nullable), used_by_staff_id (nullable), expires_at
```

#### `campaigns`
Chiến dịch khuyến mãi — **không bulk-issue voucher**.
```
id, tenant_id, name, description,
discount_type (percent | fixed), discount_value, min_order, max_discount (nullable),
target_tier_id (nullable — null = áp dụng mọi hạng),
max_issuances (nullable — tổng số voucher có thể phát),
issued_count (cache, số voucher đã phát),
starts_at, ends_at, is_active,
source (manual | birthday | signup),
deleted_at (nullable, soft delete), created_at
```

#### `vouchers`
Voucher cá nhân. Sinh theo 3 cách: (a) khách bấm "Nhận" trên `/member` (lazy claim), (b) background job sinh nhật, (c) chủ shop cấp thủ công.
```
id, tenant_id, campaign_id, membership_id (NOT NULL — luôn cá nhân hóa),
code (8 ký tự — xem 4.5),
status (issued | used | expired),
issued_at, used_at (nullable), expires_at
UNIQUE(tenant_id, code)
```
**Không có cột `used_in_transaction_id`** — tránh FK chu trình với `transactions.voucher_id`. Để tra "voucher này đã dùng ở giao dịch nào?", dùng query ngược: `SELECT id FROM transactions WHERE voucher_id = ?` (đã có index partial trong 4.3).

**Chống duplicate claim** dùng **partial unique index** (xem 4.3): `UNIQUE(campaign_id, membership_id) WHERE status NOT IN ('expired','used')`. Logic:
- **Luồng E (khách claim):** insert → nếu trùng (đã có voucher còn sống cùng campaign) → DB raise `IntegrityError` → backend trả `409 ALREADY_CLAIMED`. Atomic, không TOCTOU.
- **Luồng F (birthday job):** check idempotent ở app layer theo ngày: `WHERE campaign_id AND membership_id AND DATE(issued_at AT TIME ZONE 'Asia/Ho_Chi_Minh') = today`. Voucher năm trước đã `expired` nên partial unique cho phép insert mới.

#### `notifications`
Thông báo in-app cho người dùng.
```
id, tenant_id (nullable nếu system-wide), user_id,
type (tier_up | birthday | voucher_available | voucher_claimed | redemption_ready | shadow_claim | ...),
title, body, data (JSON — chứa id tham chiếu), is_read, created_at
```

#### `verification_codes` ★ MỚI
Cho claim shadow account và reset password.
```
id, user_id, code_hash (HMAC-SHA256 với server secret — không lưu plain, không bcrypt),
purpose (claim_shadow | reset_password),
expires_at (mặc định 10 phút), used_at (nullable), created_at
```
- **Dùng HMAC-SHA256, không bcrypt:** code 6 số chỉ có 10^6 = 1M tổ hợp, đã có rate limit chặn brute force. Bcrypt cost 12 mất ~250ms/lần verify (chậm) trong khi HMAC <1ms. HMAC an toàn vì attacker không lấy được server secret.
- MVP: sinh code 6 số, log ra console backend với mask phone (vd `[VERIFY] phone=091****5678 code=123456`). Dev đọc log đọc cho khách demo.
- Rate limit: 3 lần tạo code / 15 phút / user (xem 6.7).
- Khi tạo code mới, **invalidate** tất cả code cũ chưa dùng cùng `(user_id, purpose)` (tránh nhiều code valid song song).
- Cleanup job xoá code có `expires_at < NOW() - INTERVAL '1 day'` (giữ 1 ngày cho audit).
- Luận văn: đổi sang SMS/email thật qua adapter pattern.

### 4.3. Ràng buộc & Index quan trọng

#### Unique constraints
- `UNIQUE(tenant_id, user_id)` trên `memberships` — 1 user có 1 membership/tenant
- **`UNIQUE INDEX ... ON users(phone) WHERE phone IS NOT NULL`** — partial unique cho merge shadow → real (NULL phone không bị chặn)
- **`UNIQUE INDEX ... ON users(email) WHERE email IS NOT NULL`** — tương tự
- `UNIQUE(tenant_id, code)` trên `vouchers`
- **`UNIQUE(tenant_id, redemption_code)` trên `redemptions`** — staff scan mã không bị ambiguous (★ Critical fix)
- **Partial unique trên `vouchers`:** `UNIQUE INDEX ... ON vouchers(campaign_id, membership_id) WHERE status NOT IN ('expired','used')` — chống claim trùng cho voucher còn sống, nhưng cho phép sinh nhật năm sau (vì voucher năm trước đã `expired`)
- **Partial unique trên `point_rules`:** `UNIQUE INDEX ... ON point_rules(tenant_id) WHERE is_active = true` — đảm bảo mỗi tenant chỉ có 1 rule active tại 1 thời điểm

#### Check constraints
- `CHECK(memberships.points_balance >= 0)` — không cho balance âm
- `CHECK(rewards.stock IS NULL OR rewards.stock >= 0)` — `NULL = unlimited`, không dùng sentinel `-1`
- `CHECK(transactions.gross_amount >= transactions.net_amount)` — net không lớn hơn gross

#### Indexes (performance)
- **`point_ledger(membership_id, created_at DESC)`** — query lịch sử điểm khách
- **`point_ledger(tenant_id, created_at DESC)`** — admin reports
- **`transactions(tenant_id, created_at DESC)`** — dashboard analytics
- **`transactions(membership_id, created_at DESC)`** — lịch sử khách
- **`transactions(voucher_id) WHERE voucher_id IS NOT NULL`** — query ROI campaign
- **`notifications(user_id, tenant_id, created_at DESC)`** — list noti theo user/tenant
- **`vouchers(membership_id, status)`** — list voucher của khách
- **`memberships(tenant_id, current_tier_id)`** — phân bố hạng theo tenant

#### Append-only point_ledger (★ enforce ở DB level)
Dùng PostgreSQL trigger thay vì application guard:
```sql
CREATE OR REPLACE FUNCTION prevent_ledger_mutation() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'point_ledger is append-only — UPDATE/DELETE not allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_update_or_delete_ledger
  BEFORE UPDATE OR DELETE ON point_ledger
  FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
```
Migrated qua Alembic 1 lần. Là defense-in-depth — dev không thể vào psql gõ `UPDATE point_ledger` qua mặt.

#### Phone normalization
Số điện thoại lưu DB theo format **E.164** (`+84XXXXXXXXX`). Validate ở Pydantic model trước khi insert. Frontend chuẩn hóa input "0912345678" → "+84912345678" trước khi submit. Tránh duplicate kiểu "+84..." vs "0..." cùng 1 người.

#### Soft delete query rule
Soft delete áp trên `rewards`, `campaigns`, `tiers`. **Mọi query mặc định phải filter `WHERE deleted_at IS NULL`** — implement qua SQLAlchemy `with_loader_criteria` hoặc helper `active()` query. KHÔNG được dựa vào lập trình viên nhớ filter từng query.

#### Cascade behavior (FK)
| Parent | Child | ON DELETE | Lý do |
|---|---|---|---|
| `tenants` | mọi bảng con | `RESTRICT` | Xóa tenant là thao tác admin thủ công, cần manual cleanup |
| `users` | `tenant_staff` | `CASCADE` | Xóa user → clean staff link |
| `users` | `memberships` | `RESTRICT` | Giữ history giao dịch |
| `memberships` | `transactions`, `point_ledger`, `vouchers`, `redemptions` | `RESTRICT` | Append-only history |
| `campaigns` | `vouchers` | `RESTRICT` | + soft delete `campaigns` |
| `rewards` | `redemptions` | `RESTRICT` | + soft delete `rewards` |
| `tiers` | `memberships` | `RESTRICT` | + soft delete `tiers` |

**Quy tắc tổng quát:** Hầu hết dùng `RESTRICT` để bảo vệ data integrity. Hard delete chỉ áp cho bảng utility (`verification_codes`, `notifications` đã đọc lâu).

#### Reconcile rule (point_ledger)
- `SUM(point_ledger.delta) WHERE membership_id = X` **PHẢI bằng** `memberships.points_balance` của X.
- Endpoint `POST /admin/reconcile/{membership_id}` để kiểm tra; báo lỗi nếu lệch.
- Test invariant `tests/integration/test_ledger_invariant.py` chạy sau mọi kịch bản test.

### 4.4. `tenants.settings` — schema cố định
Validate bằng Pydantic model. Không cho phép key lạ.
```json
{
  "points_on_gross": false,
  "birthday_campaign_id": null,
  "signup_bonus_points": 0,
  "voucher_default_ttl_days": 30,
  "redemption_default_ttl_days": 14,
  "default_tier_id": null
}
```

### 4.5. Format mã code (redemption, voucher, verification)
- **Redemption/Voucher code:** 8 ký tự, alphanumeric uppercase, **loại bỏ** các ký tự dễ nhầm: `O 0 I 1 L` → còn lại 31 ký tự. Utility chung `generate_code()` ở `core/utils.py`.
- **Verification code:** 6 số (dễ đọc qua điện thoại / console).

---

## 5. Các module & Luồng nghiệp vụ chính

### 5.1. Backend modules (FastAPI)
1. **auth** — đăng ký, đăng nhập, refresh, verification code (claim shadow / reset password)
2. **tenants** — đăng ký doanh nghiệp, duyệt, **GET/PATCH `/tenants/me/settings`** (Pydantic-validated, ghi audit khi đổi `points_on_gross`)
3. **staff** — CRUD nhân viên của tenant (xem Luồng H)
4. **members** — tìm/tạo khách theo SĐT (Luồng B), shadow flow, xem lịch sử, **`POST /memberships` cho khách tự join shop (Luồng L)**, **`GET /shops/public` list shop để khách browse**
5. **transactions** — tạo giao dịch (3 cách), tính điểm, gọi ledger, gọi tiers
6. **rewards** — CRUD catalog, đổi quà, xác nhận sử dụng
7. **campaigns** — CRUD chiến dịch, list eligible campaigns cho khách
8. **vouchers** — claim voucher từ campaign, list voucher của khách, dùng voucher
9. **tiers** — cấu hình hạng, logic upgrade
10. **ledger** — insert entry (internal), query lịch sử, reconcile
11. **notifications** — list, mark-as-read; các service khác gọi vào để đẩy notification
12. **analytics** — tổng hợp số liệu dashboard, gồm ROI campaign. MVP: query trực tiếp DB với index trên `tenant_id` + `created_at`. Không cần materialized view (dành cho luận văn).
13. **jobs** — background: voucher sinh nhật (hằng ngày), đánh dấu voucher/redemption hết hạn

### 5.2. Frontend apps (cùng một Next.js project, khác route)
1. **`/admin`** — Super Admin: duyệt doanh nghiệp (list + approve button), platform stats. **Minimal UI cho MVP.**
2. **`/merchant`** — Chủ doanh nghiệp: cấu hình shop, tiers, point_rules, rewards, campaigns, members, analytics
3. **`/pos`** — Nhân viên (tablet landscape): nhập giao dịch, quét QR khách, hiện QR shop, xác nhận đổi quà, nhập mã voucher
4. **`/member`** — PWA khách: điểm + hạng (theo từng shop), QR cá nhân (rolling), catalog quà, available campaigns + claim, voucher của mình, lịch sử, **`/member/shops` browse danh sách shop public + tự join (Luồng L)**

### 5.3. Các luồng nghiệp vụ then chốt

#### Luồng A — Đăng ký doanh nghiệp mới
1. User tạo tài khoản cá nhân → vào `/merchant/register` → điền thông tin doanh nghiệp (`name`, mô tả, logo)
2. Backend **auto-generate `slug`** từ `name` (slugify + random 4 ký tự suffix nếu trùng — vd `the-coffee-house-ab12`). User KHÔNG được chỉnh slug ở form này (tránh xung đột UX).
3. Hệ thống tạo `tenant` trạng thái `pending`, tạo `tenant_staff` role `owner`
4. Super Admin xem danh sách pending ở `/admin` → bấm duyệt → tenant chuyển `active`
5. Chủ doanh nghiệp nhận notification → vào `/merchant` cấu hình tiers, point_rules, rewards, nhân viên

#### Luồng B — Tạo thành viên mới qua SĐT (default cho khách mới ở tenant)

**Đây là luồng default cho mọi khách CHƯA có membership ở tenant hiện tại** — bao gồm cả 3 trường hợp:
- **Case 1:** Khách hoàn toàn mới (chưa đăng ký bất kỳ shop nào, chưa có user trong hệ thống)
- **Case 2:** Khách đã có shadow user (do tenant khác tạo trước) nhưng chưa claim
- **Case 3:** Khách đã có user thường (đã đăng ký, đã claim, đã có app PWA) nhưng chưa join tenant hiện tại

**Phần 1 — Tạo membership qua SĐT (lần đầu giao dịch ở shop này):**
1. Khách đến cửa hàng lần đầu, nhân viên mở `/pos` → form tạo giao dịch → nhập **SĐT khách** (frontend chuẩn hóa E.164: `0912345678` → `+84912345678`)
2. `members` service xử lý **3 case** trong cùng DB transaction:
   ```sql
   -- Bước 2a: Upsert user theo SĐT (atomic, tránh race)
   INSERT INTO users (phone, is_shadow, ...) VALUES ('+84912345678', true, ...)
   ON CONFLICT (phone) WHERE phone IS NOT NULL DO NOTHING
   RETURNING id;
   ```
   - Nếu RETURNING trả id mới → **Case 1** (khách hoàn toàn mới, vừa tạo shadow user)
   - Nếu RETURNING không trả id (CONFLICT) → SELECT lại lấy id của user cũ → **Case 2 hoặc Case 3** (user đã tồn tại, KHÔNG tạo lại)
3. Upsert `membership(tenant_id, user_id)`:
   ```sql
   INSERT INTO memberships (tenant_id, user_id, ...) VALUES (...)
   ON CONFLICT (tenant_id, user_id) DO NOTHING
   RETURNING id;
   ```
4. Tạo transaction tích điểm + ghi point_ledger trong **cùng DB transaction**
5. Nếu Case 3 (user đã có app), push notification vào `/member` của khách: *"Bạn đã trở thành thành viên shop [tên shop]"*

**Vì sao đơn giản hóa luồng này:**
- Nhân viên KHÔNG cần biết khách thuộc case nào — chỉ hỏi SĐT
- Backend tự upsert, không tạo duplicate user
- Bao quát cả 3 case mà không cần consent flow phức tạp
- SĐT khách + nhân viên hỏi miệng = consent rõ ràng

**Phần 2 — Claim (khách "nhận" tài khoản sau đó):**
1. Khách vào `/member/register` → nhập SĐT (chuẩn hóa E.164) + họ tên + email + password + birthday
2. Backend tìm `users.phone`:
   - **Không có** → tạo user thường + gửi verification_code (in console MVP, email luận văn)
   - **Có shadow user** → bước 3
3. **Invalidate code cũ** (★ fix race): `UPDATE verification_codes SET used_at = NOW() WHERE user_id = ? AND purpose = 'claim_shadow' AND used_at IS NULL` → tạo `verification_codes` mới với `code_hash = HMAC(secret, code)`
4. **Log code ra console backend** với mask phone (★ M1):
   ```
   [VERIFY CODE] user_id=42 phone=+84912****678 code=123456 expires=10min purpose=claim_shadow
   ```
5. Frontend chuyển sang màn hình nhập code
6. Khách nhập code → backend verify (`expires_at > NOW()`, `used_at IS NULL`, HMAC match) → set email + password + full_name + birthday → `is_shadow=false` → mark code `used_at=NOW()` → đăng nhập
7. Tất cả membership ở các tenant cũ của shadow user giờ thuộc về khách (không phải migrate, vì shadow user đã có membership rồi)

**Lưu ý bảo mật:**
- Không thể claim shadow chỉ bằng biết SĐT — phải qua verification_code
- Mỗi user/purpose chỉ có **1 code valid** tại 1 thời điểm (invalidate cũ khi tạo mới)
- Rate limit 3 lần tạo code / 15 phút / phone (xem 6.7)
- File log `backend/logs/` đã trong `.gitignore` — KHÔNG được commit
- **MVP chỉ chấp nhận** ở localhost demo. Staging/production cần SMS thật + cleanup log với rotation.

#### Luồng C — Tích điểm qua QR cá nhân (CHỈ cho khách đã có membership tenant)

**Tiền đề logic quan trọng:** QR cá nhân chỉ tồn tại khi khách đã có user account và đã mở `/member` PWA. Khách hoàn toàn mới (chưa đăng ký bất kỳ shop nào) **KHÔNG có user → KHÔNG có QR**. Vì vậy:
- **Khách hoàn toàn mới đến shop lần đầu** → BẮT BUỘC dùng **Luồng B** (nhân viên nhập SĐT, tạo shadow account + membership)
- **Khách đã là thành viên tenant hiện tại** → có thể quét QR (luồng dưới đây)
- **Khách đã có user (do tenant khác / đã claim shadow trước) nhưng CHƯA có membership ở tenant hiện tại** → vẫn dùng **Luồng B** (nhân viên nhập SĐT). Backend sẽ phát hiện user đã tồn tại → KHÔNG tạo user mới, chỉ tạo `membership` mới cho tenant hiện tại

→ **Luồng C chỉ áp dụng cho trường hợp khách đã có membership ở tenant hiện tại.** Mục đích: tích điểm nhanh, không phải nhập SĐT lại mỗi lần.

**Sinh QR (phía khách):**
1. Khách mở `/member` → frontend gọi `GET /member/qr` → backend ký JWT `{user_id, iat: now, exp: now + 120s}` bằng **server secret** → trả về `{jwt, exp_at_server: <unix_timestamp>}` (exp 120s để giảm risk mạng yếu)
2. Frontend KHÔNG dùng đồng hồ máy khách cho countdown — dùng `exp_at_server` từ response làm baseline, refresh QR khi `exp_at_server - now_local < 30s`. Tránh clock skew gây UX vỡ
3. Backend khi verify JWT set `leeway=5` (chấp nhận chênh lệch đồng hồ ±5s)
4. **Fallback offline:** trong response còn kèm `fallback_code` (8 ký tự alphanumeric, sinh từ HMAC `(user_id, hour)` — đổi mỗi giờ). Khi mạng yếu/QR camera lỗi, nhân viên có thể nhập tay code này

**Nhân viên quét QR khách:**
1. Nhân viên mở `/pos` → chọn "Quét QR khách" → quét → POST `/transactions` với payload QR (hoặc fallback_code) + header `X-Tenant-Id`
2. Backend decode QR (verify server secret + exp với leeway) → lấy `user_id`. Nếu là fallback_code → reverse-lookup HMAC → ra `user_id`
3. **`SELECT FOR UPDATE`** trên `membership(tenant_id=header, user_id)`:
   - **Thấy** → nhân viên nhập `gross_amount` (validate trong khoảng `[point_rules.min_amount, 100_000_000 VND]`) → tính `points_earned` theo `point_rules` → tạo `transaction` + insert `point_ledger(delta=+points, reason=earn, ref_type=transaction)` + cập nhật `memberships.points_balance` + `total_points_earned` + `last_activity_at` trong **1 DB transaction**
   - **Không thấy** → backend trả `404 NO_MEMBERSHIP`. `/pos` hiển thị message: *"Khách chưa phải thành viên shop này. Mời chuyển sang nhập SĐT (Luồng B) để đăng ký."* → nhân viên switch sang form nhập SĐT của Luồng B (nhập SĐT khách → backend upsert user theo SĐT → tạo membership mới + tích điểm)
4. Check upgrade tier (xem Luồng G) → nếu có, update `current_tier_id` + push notification
5. Trả kết quả về `/pos`, push notification vào `/member` của khách
6. **Bắt `IntegrityError`** (vd CHECK balance >= 0) → trả 409 thay vì 500

**Vì sao đơn giản hóa (không có consent flow phức tạp):**
- Nhân viên không phải nhớ 2 flow (Plan A/B) — chỉ cần biết: quét QR thất bại → fall back nhập SĐT (Luồng B)
- Luồng B đã handle cả 2 case: user hoàn toàn mới (tạo shadow) và user đã tồn tại (chỉ tạo membership mới qua upsert SĐT)
- SĐT là identity rõ ràng + nhân viên hỏi miệng khách = consent đầy đủ
- Không có vấn đề "khách hoàn toàn mới làm sao có QR" vì luồng C **không cố** xử lý case đó

#### Luồng D — Đổi điểm lấy quà (có ledger)
1. Khách vào `/member/rewards` → chọn quà đủ điểm → bấm đổi
2. Backend trong 1 DB transaction:
   - `SELECT ... FOR UPDATE` trên `memberships` → check `points_balance >= points_cost`
   - `UPDATE memberships SET points_balance = points_balance - cost`
   - `INSERT redemption(..., redemption_code, status=pending, expires_at=now+settings.redemption_default_ttl_days)`
   - `INSERT point_ledger(delta=-cost, reason=redeem, ref_type=redemption, ref_id=...)`
   - Nếu `stock IS NOT NULL` → `UPDATE rewards SET stock = stock - 1 WHERE id=? AND stock > 0` (atomic, kiểm rowcount=1)
   - **Bắt `IntegrityError`** (CHECK balance ≥ 0 hoặc stock < 0) → rollback → trả `409 INSUFFICIENT_POINTS` hoặc `409 OUT_OF_STOCK`
   - Commit
3. `/member` hiển thị mã redemption + QR
4. Khách đến cửa hàng → nhân viên nhập mã vào `/pos` → backend verify (status=pending, `NOW() < expires_at`, đúng tenant) → `UPDATE redemptions SET status=used, used_at, used_by_staff_id`

**Policy redemption hết hạn (MVP):**
- Job hằng ngày `expire_redemptions`: `UPDATE redemptions SET status=expired WHERE status=pending AND expires_at < NOW()`
- **KHÔNG hoàn điểm** khi redemption expired — đã ghi rõ trong UI lúc đổi quà: *"Quà đã đổi không hoàn điểm. Vui lòng đến cửa hàng lấy trong N ngày."*
- Luận văn: cân nhắc thêm option refund với ledger `delta=+cost, reason=expire`.

#### Luồng E — Chiến dịch khuyến mãi (LAZY CLAIM, atomic)

**Tạo campaign:**
1. Chủ shop vào `/merchant/campaigns` → tạo với điều kiện (target_tier, min_order, discount, max_issuances optional, start/end)
2. Backend lưu `campaigns` — **không sinh voucher nào**

**Khách claim voucher (atomic, không TOCTOU):**
1. Khách vào `/member/vouchers/available` → backend query campaigns đủ điều kiện (active, trong window, đúng tier, chưa max), filter ra danh sách
2. Khách bấm "Nhận" → backend thực hiện **2 atomic ops trong 1 transaction**:
   ```sql
   -- Op 1: atomic UPDATE check max_issuances
   UPDATE campaigns SET issued_count = issued_count + 1
     WHERE id = ?
       AND is_active = true
       AND NOW() BETWEEN starts_at AND ends_at
       AND (max_issuances IS NULL OR issued_count < max_issuances);
   -- Nếu rowcount = 0 → hết slot hoặc campaign đã đóng → rollback → trả 409 CAMPAIGN_FULL
   
   -- Op 2: insert voucher (partial unique sẽ raise nếu trùng)
   INSERT INTO vouchers (...) VALUES (...);
   -- Nếu raise IntegrityError → khách đã có voucher còn sống → rollback → trả 409 ALREADY_CLAIMED
   ```
3. Push notification "Voucher đã sẵn sàng"

**Vì sao atomic:** Không có `SELECT COUNT` riêng → không có TOCTOU. Cả 2 invariant (`issued_count < max`) và `(campaign, member) chưa có voucher còn sống` đều được DB enforce.

**Dùng voucher khi tạo giao dịch:**
1. Khách đưa mã voucher cho nhân viên
2. Nhân viên nhập vào `/pos` khi tạo giao dịch → backend verify code (status=issued + chưa hết hạn + đúng tenant)
3. Tính `voucher_discount_amount` = min(discount_value × gross_amount / 100, max_discount) (nếu percent) hoặc min(discount_value, gross_amount) (nếu fixed)
4. `net_amount = gross_amount - voucher_discount_amount`
5. Tạo transaction với `voucher_id`, `voucher_discount_amount`, `gross_amount`, `net_amount`, `points_earned` (theo `points_on_gross` setting)
6. `UPDATE vouchers SET status=used, used_at`
7. **Voucher KHÔNG tạo entry ledger** (chỉ ảnh hưởng giảm giá, không phải điểm). Ledger entry vẫn ghi cho `points_earned` như giao dịch thường.

#### Luồng F — Voucher sinh nhật (background job, system-initiated)

**Cấu hình scheduler:**
- APScheduler khởi tạo với `timezone='Asia/Ho_Chi_Minh'` (KHÔNG dùng timezone server) — đảm bảo job chạy đúng 00:05 ICT bất kể server ở UTC hay nơi nào
- CHỈ bật nếu `ENABLE_SCHEDULER=true`

**Logic:**
1. Job chạy 00:05 ICT mỗi ngày
2. Query: `memberships` JOIN `users` JOIN `tenants`:
   ```sql
   WHERE users.is_active = true
     AND tenants.settings->>'birthday_campaign_id' IS NOT NULL
     AND (
       -- Match ngày-tháng theo lịch VN
       EXTRACT(MONTH FROM users.birthday) = EXTRACT(MONTH FROM (NOW() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date)
       AND EXTRACT(DAY FROM users.birthday) = EXTRACT(DAY FROM (NOW() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date)
     );
   ```
3. **Edge case 29/2:** khách sinh ngày 29/2 sẽ nhận voucher ngày 28/2 trong năm không nhuận (xử lý ở app layer trước query, hoặc hiểu là known limitation và ghi vào báo cáo).
4. Với mỗi `(membership, birthday_campaign_id)`:
   - **Check idempotent theo ngày VN:** `WHERE campaign_id AND membership_id AND DATE(issued_at AT TIME ZONE 'Asia/Ho_Chi_Minh') = today_vn`. Nếu có → skip (tránh job chạy 2 lần cùng ngày tạo duplicate).
   - Insert `vouchers(tenant_id, campaign_id, membership_id, code, expires_at=now+voucher_default_ttl_days, status=issued)` — system-initiated, không qua lazy claim
   - `UPDATE campaigns SET issued_count = issued_count + 1`
   - Insert `notifications(user_id, type=birthday, title="🎂 Chúc mừng sinh nhật!", ...)`
5. Log toàn bộ `(membership_id, voucher_id)` ra file `logs/birthday-YYYY-MM-DD.log` để audit
6. **Test:** unit test cho function `process_birthday_for_date(target_date)` — gọi trực tiếp không qua scheduler, assert tạo voucher đúng + không duplicate khi gọi 2 lần.

#### Luồng G — Tính lại hạng thành viên (chỉ upgrade hoặc silent re-bind)
1. Sau mỗi transaction thành công, `transactions` service gọi `tiers.recompute_tier(membership_id)`
2. Query: `SELECT * FROM tiers WHERE tenant_id = X AND min_points <= total_points_earned AND is_active AND deleted_at IS NULL ORDER BY min_points DESC LIMIT 1`
3. So sánh với `current_tier_id`:
   - **`new_tier.min_points > current_tier.min_points`** → upgrade thật → update + push notification "Chúc mừng bạn lên hạng **[X]**"
   - **`new_tier.min_points < current_tier.min_points`** → tier hiện tại đã bị xóa hoặc chủ shop tăng `min_points` cao hơn → **silent re-bind** (update `current_tier_id` không push notification "lên hạng" để tránh confuse khách). Ghi log audit.
   - **Bằng nhau hoặc cùng tier** → không làm gì
4. **Không ghi point_ledger** (vì không có biến động điểm), chỉ ghi `notifications` khi upgrade thật.

**Job recompute toàn bộ membership khi chủ shop sửa tier config:**
- Khi chủ shop PATCH `/tenants/me/tiers` (đổi `min_points` hoặc xóa tier có khách đang ở), backend trigger background task `recompute_all_memberships(tenant_id)` → loop tất cả membership của tenant + áp Luồng G ở chế độ silent.
- MVP: chạy đồng bộ trong request nếu < 100 membership, async nếu nhiều.

#### Luồng H — Quản lý nhân viên (★ MỚI)

**Chủ shop thêm nhân viên:**
1. Chủ shop vào `/merchant/staff` → bấm "Thêm nhân viên" → nhập `email + tên + role` (owner | staff)
2. Backend tìm `users.email`:
   - **Có user thường:** tạo `tenant_staff(tenant_id, user_id, role)` + insert notification "Bạn đã được thêm vào shop X"
   - **Không có user:** tạo `user(email, is_shadow=true, full_name)` + tạo `tenant_staff` + sinh `verification_codes(purpose=claim_shadow)` + log code ra console + email invite (MVP: log console)
3. Nhân viên vào `/login` → claim shadow flow như Luồng B → set password → login

**Chủ shop xóa nhân viên:**
1. Chủ shop vào `/merchant/staff` → chọn nhân viên → bấm "Xóa"
2. Backend `DELETE FROM tenant_staff WHERE id=?` → revoke tất cả refresh token của user trong tenant đó (xem 6.6)
3. Transactions cũ vẫn giữ nguyên `staff_id` (historical, không nullify)
4. Nhân viên không còn truy cập được `/pos` của shop (header `X-Tenant-Id` sẽ fail check)

**Chủ shop đổi role nhân viên:**
1. PATCH `/merchant/staff/{id}` với `role` mới
2. Invalidate cache `(user_id, tenant_id)` trong middleware (TTL 60s) — xem 3.3

#### Luồng I — Hủy/Hoàn giao dịch (refund) — DÀNH CHO LUẬN VĂN (★ MỚI)

**MVP cố ý KHÔNG implement** vì:
- Refund nghiệp vụ phức tạp (hoàn điểm, tier downgrade, voucher đã dùng, hoàn voucher, ...)
- Trong 8 tuần không kịp, dễ tạo bug
- Workaround MVP: nhân viên cẩn thận trước khi submit; nếu sai, dùng endpoint admin `POST /admin/adjust-points` (manual ghi ledger với `delta` âm + reason `manual_adjust`)

**Luận văn sẽ implement:**
1. Nhân viên vào transaction detail → bấm "Hủy" (chỉ cho phép trong 24h sau khi tạo)
2. Backend trong 1 DB transaction:
   - `SELECT FOR UPDATE` membership
   - `UPDATE memberships SET points_balance = points_balance - txn.points_earned, total_points_earned = total_points_earned - txn.points_earned`
   - Insert `point_ledger(delta=-txn.points_earned, reason=refund, ref_type=transaction, ref_id=txn.id)`
   - `UPDATE transactions SET status='cancelled', cancelled_at=NOW(), cancelled_by=staff_id`
3. Recompute tier (Luồng G) — có thể dẫn đến tier downgrade thật
4. Voucher đã dùng: policy "không hoàn voucher" (đã ghi ở UI). Nếu cần hoàn → tạo voucher mới với cùng campaign cho khách
5. Push notification "Giao dịch X đã được hủy"

Cần thêm cột `transactions.status` (active | cancelled) cho luận văn — MVP chưa có.

#### Luồng J — Reset password (★ MỚI, ngắn)

1. User vào `/login` → bấm "Quên mật khẩu" → nhập email
2. Backend tìm `users.email` → invalidate code cũ (như Luồng B) → tạo `verification_codes(purpose=reset_password)` → log code ra console (MVP) hoặc gửi email (luận văn)
3. User nhập code → nhập password mới → backend verify → set `password_hash` mới → mark code `used_at`
4. **Revoke tất cả refresh token** của user (xem 6.6) → buộc login lại trên mọi thiết bị

#### Luồng K — Chủ shop chỉnh tier có membership đang active (★ MỚI)

**Use case:** Chủ shop muốn đổi `min_points` của tier "Silver" từ 1000 → 1500 sau khi đã có khách đang ở Silver.

1. Chủ shop vào `/merchant/tiers` → sửa `min_points` → bấm Lưu
2. Backend update `tiers` row + trigger `recompute_all_memberships(tenant_id)` (Luồng G)
3. Khách có `total_points_earned = 1200` đang ở Silver → recompute → quay về Bronze (tier có `min_points = 0`) → silent re-bind, không push notification
4. Khách thấy tier mình "thấp xuống" trong app — UX cần thông báo: trong UI `/merchant/tiers` có warning *"Đổi `min_points` có thể khiến khách hiện tại bị tụt hạng. Đảm bảo bạn đã thông báo cho khách."*

**Trường hợp xóa tier:**
1. Chủ shop xóa tier → soft delete (`deleted_at = NOW()`)
2. Trigger `recompute_all_memberships` → khách đang ở tier bị xóa → re-bind sang tier thấp hơn còn sống
3. Nếu không còn tier nào → membership.current_tier_id = NULL (cho phép NULL trong DB)

#### Luồng L — Khách tự join shop từ app (★ MỚI)

**Điều kiện tiên quyết:** Khách đã có user account (đã đăng ký thường hoặc đã claim shadow ở tenant khác) → đã có thể đăng nhập `/member` PWA. Luồng này KHÔNG dành cho khách hoàn toàn mới (khách hoàn toàn mới vẫn dùng Luồng B tại quầy).

**Use case:** Khách biết shop từ trước (qua bạn bè giới thiệu, marketing, hoặc đã đến shop nhưng chưa kịp đăng ký), muốn join thành viên trước khi đến quầy để có sẵn QR cá nhân khi tới shop.

**Flow:**
1. Khách mở `/member` → vào tab `/member/shops` → backend trả về danh sách shop **public** (`tenants WHERE status='active'`) kèm thông tin: tên, logo, mô tả ngắn, vị trí (nếu có), số thành viên hiện tại
2. Khách filter/search shop → bấm "Xem chi tiết" → xem benefit của các tier
3. Khách bấm **"Tham gia [tên shop]"** → POST `/memberships` với body `{tenant_id}` (header chỉ cần JWT, không cần `X-Tenant-Id`)
4. Backend xử lý:
   - Verify user đang đăng nhập (JWT)
   - Upsert: `INSERT INTO memberships (tenant_id, user_id, joined_at, ...) VALUES (...) ON CONFLICT (tenant_id, user_id) DO NOTHING`
   - Nếu RETURNING trả id mới → tạo membership thành công + push notification cho khách "Đã tham gia thành viên [tên shop]"
   - Nếu CONFLICT (đã là thành viên) → trả `409 ALREADY_MEMBER`
5. Sau đó khách đến quầy → nhân viên quét QR → tích điểm như bình thường (Luồng C — đã có membership rồi)

**Vì sao không bỏ Luồng B:**
- Luồng B vẫn cần cho **khách hoàn toàn mới** (chưa có user → không thể đăng nhập app → không vào được `/member/shops`)
- Luồng L chỉ là **tùy chọn cho khách đã có app** muốn proactive join trước
- Hai luồng song song, không xung đột — chung cùng cơ chế upsert backend

**Bảo mật:**
- Khách phải đăng nhập (JWT verify)
- Không thể join hộ người khác (chỉ tự join cho `current_user`)
- Rate limit `POST /memberships` 10/phút/user (chống spam join hàng loạt)
- Không lộ `tenant_id` không tồn tại — backend trả 404 generic nếu tenant không `active`

**Tính năng phụ trợ trong `/member/shops`:**
- Xem trước benefit các tier mà chưa cần join
- Search/filter theo tên, vị trí
- Đánh dấu shop đã/chưa là thành viên

**Lưu ý:** MVP KHÔNG có tính năng "rời thành viên" — khách đã join rồi không có cách tự rút khỏi shop. Nếu cần (vd khách yêu cầu xóa data), chủ shop dùng admin endpoint để soft archive. Tính năng tự rời dành cho luận văn nếu cần.

---

## 6. Xử lý lỗi & Bảo mật

### 6.1. Race condition khi tích/đổi điểm

**Quy tắc cố định:**
- `SELECT ... FOR UPDATE` trên `memberships` **đầu tiên** trong mọi transaction thay đổi balance
- Update balance + insert ledger + insert transaction/redemption TRONG CÙNG DB transaction
- `CHECK(points_balance >= 0)` ở DB constraint + check ở service layer (defense-in-depth)
- Test tự động cho 2 request đổi quà đồng thời

**Lock ordering rule (★ tránh deadlock):**
Khi 1 transaction phải khoá nhiều bảng, **luôn lock theo thứ tự cố định**:
1. `memberships` (luôn đầu tiên)
2. `tiers` / `point_rules` (chỉ đọc — không cần FOR UPDATE)
3. `vouchers` (nếu liên quan)
4. `rewards` (nếu liên quan)
5. `campaigns` (chỉ dùng atomic UPDATE, không lock riêng)

Mọi service code phải tuân thủ thứ tự này. Comment trong code nhắc rõ.

**Xử lý `IntegrityError` (★ tránh leak stack trace):**
- Bọc transaction đổi điểm bằng `try/except IntegrityError as e`
- Map sang HTTP exception:
  - `CHECK points_balance >= 0` → `409 INSUFFICIENT_POINTS`
  - `CHECK rewards.stock >= 0` → `409 OUT_OF_STOCK`
  - `UNIQUE vouchers (campaign, member) WHERE active` → `409 ALREADY_CLAIMED`
  - `UNIQUE redemptions (tenant, code)` → retry với code mới
- KHÔNG để FastAPI default trả 500 với stack trace

**Retry deadlock:**
- Nếu bắt `psycopg2.errors.DeadlockDetected` → retry tối đa 1 lần với backoff 100ms
- Sau 1 lần retry vẫn fail → trả 503 SERVICE_BUSY

### 6.2. QR chống lạm dụng

**QR cá nhân khách:**
- JWT ký bằng **server secret**, `exp = now + 120s` (★ tăng từ 60s để chịu được mạng yếu)
- Backend trả `{jwt, exp_at_server, fallback_code}`. Frontend dùng `exp_at_server` (KHÔNG dùng `Date.now()` của client để tính countdown — tránh clock skew)
- Verify JWT với `leeway=5` (chấp nhận chênh đồng hồ ±5s)
- Refresh QR khi `exp_at_server - now < 30s`
- Không có secret ở client → client không tự sinh được QR

**Fallback offline:**
- Trong response `/member/qr` có thêm `fallback_code` 8 ký tự = HMAC(`server_secret`, `user_id || hour_bucket`) — đổi mỗi giờ
- Khi mạng yếu/QR camera hỏng, nhân viên gõ tay code này vào `/pos`
- Backend reverse-lookup HMAC → ra `user_id` → dùng cho luồng tích điểm như JWT

**QR cửa hàng (luồng b — khách quét):**
- Deeplink dạng `/member/checkin?tenant={slug}&shop_token=<HMAC>` — token ký bằng server secret để xác minh đây là QR thật của shop (không phải ai tạo deeplink fake cũng được)
- Khách quét → mở `/member` → backend verify `shop_token` → tạo session check-in tạm (TTL 5 phút) → chuyển sang nhập amount bởi nhân viên
- **Khách KHÔNG tự nhập amount để tích điểm** — mọi giao dịch phải do nhân viên xác nhận trên `/pos` (chống self-credit fraud)

**Rate limit:** xem 6.7

### 6.3. Multi-tenant isolation
- **Mọi query nghiệp vụ BẮT BUỘC có `tenant_id` trong WHERE** — không dựa ORM scoping mặc định.
- Dependency `get_current_tenant()`: đọc `X-Tenant-Id` header → query `tenant_staff` → verify → cache 60s.
- **Test `test_tenant_isolation.py`** cho mỗi module: tạo 2 tenant, đảm bảo user tenant A không thao tác được dữ liệu tenant B ở mọi endpoint.

### 6.4. Phân quyền (đơn giản hóa)
- **JWT chứa CHỈ `{user_id, system_role, exp}`** — không chứa tenant list.
- Dependency:
  - `require_super_admin()` — chỉ check `system_role`
  - `require_staff_in_tenant()` — đọc `X-Tenant-Id` → verify user có role trong `tenant_staff`
  - `require_owner_in_tenant()` — như trên, chỉ chấp nhận `role=owner`
  - `require_customer_in_tenant()` — verify user có `membership` trong tenant đó
- Frontend ẩn UI theo role, nhưng **backend là lớp enforce thật sự**.

### 6.5. Shadow account claim
- Bảng `verification_codes` là cơ chế duy nhất để claim
- Code 6 số, hash bcrypt lưu DB, TTL 10 phút, dùng 1 lần
- Rate limit: 3 lần tạo code / 15 phút / phone
- **MVP:** log code ra console backend (+ lưu DB hash) — dev đọc cho khách demo
- **Luận văn:** tích hợp SMS provider thật (Twilio, eSMS, ...) qua adapter pattern — đã chuẩn bị interface

### 6.6. Mật khẩu & token

**Hash:**
- Password: bcrypt cost ≥ 12, min length 8 ký tự
- Verification code 6 số: HMAC-SHA256 (xem 4.2)

**Token lifecycle:**
- Access token JWT 15 phút, **stateless** — không revoke được trước hạn (trade-off chấp nhận cho MVP)
- Refresh token 7 ngày, lưu DB, có thể revoke

**Revoke triggers (refresh token):**
- User logout → revoke refresh token hiện tại
- User đổi mật khẩu → revoke TẤT CẢ refresh token của user (logout all devices)
- Owner remove staff khỏi tenant → revoke refresh token của staff đó
- Admin suspend tenant → revoke refresh token của tất cả staff thuộc tenant đó

**Frontend xử lý 401:**
- Axios interceptor bắt 401 → gọi `POST /auth/refresh` → retry request gốc
- Nếu refresh fail → redirect `/login`

**Lưu trữ token ở client:**
- Access token: trong memory (Zustand store), KHÔNG localStorage (XSS-resistant)
- Refresh token: HttpOnly cookie SameSite=Strict (xem 6.11 về CSRF)

### 6.7. Rate limiting (`slowapi`)

| Endpoint | Giới hạn | Ghi chú |
|---|---|---|
| `POST /auth/login` | 5/phút/IP **+** 10/phút/email | Hybrid: chống brute force IP và account-based; khi 10 nhân viên dùng chung WiFi café không bị chặn nhầm |
| `POST /auth/register` | 3/phút/IP + 5/phút/phone | Tương tự |
| `POST /auth/refresh` | 20/phút/IP | Chống brute force refresh token |
| `POST /auth/verify-code` (claim shadow, reset password) | 3/15phút/phone | Chống enumerate SĐT |
| `POST /transactions` | 30/phút/staff | Cap spam tích điểm |
| `POST /redemptions` | 10/phút/user | Cap spam đổi quà tìm race |
| `GET /member/qr` | 20/phút/user | Cap spam refresh QR |
| `POST /vouchers/claim` | 10/phút/user | Cap spam claim |
| `POST /memberships` (khách tự join shop, Luồng L) | 10/phút/user | Cap spam join hàng loạt shop |
| `PATCH /tenants/me/settings` | 10/phút/owner | Tránh owner bị compromise đổi liên tục |
| Default còn lại | 100/phút/IP | — |

**Caveat slowapi (đã ghi ở 3.1):** mọi endpoint dùng `@limiter.limit` BẮT BUỘC có `request: Request` param. Không rate limit theo body; phải dùng `key_func` custom đọc từ header hoặc user_id sau auth.

### 6.8. Cách tính điểm (net vs gross)
- **Mặc định:** tính trên `net_amount` (sau voucher) — an toàn cho shop, không double-benefit
- Chủ shop có thể bật `tenants.settings.points_on_gross = true` → điểm tính trên `gross_amount`
- UI setting có **tooltip giải thích** rõ ràng + **confirm dialog 2 bước** khi đổi giá trị (vì ảnh hưởng kinh tế trực tiếp)
- **Audit:** mỗi lần đổi `tenants.settings` ghi vào bảng `tenant_settings_audit (tenant_id, user_id, key, old_value, new_value, changed_at)` — đặc biệt `points_on_gross` để có evidence khi tranh chấp

### 6.9. Background job safety (in-process scheduler)

**APScheduler chạy trong cùng process FastAPI**, KHÔNG phải process riêng. Có 3 cấu hình:

| Mode | Cấu hình | Tại sao |
|---|---|---|
| **Dev (Windows + uvicorn --reload)** | `ENABLE_SCHEDULER=false` | Hot reload sẽ chạy job 2+ lần. Job test thủ công bằng `python -m app.jobs.run_once <name>` |
| **Demo / Single worker production-ish** | `ENABLE_SCHEDULER=true`, chạy `uvicorn` (không reload) với **1 worker** | Đơn giản, đủ cho MVP |
| **Multi-worker (KHÔNG khuyến nghị cho MVP)** | API workers: `ENABLE_SCHEDULER=false`. Tách scheduler thành process riêng: `python -m app.jobs.runner` | Nếu chạy `uvicorn --workers 4` mà bật scheduler, mỗi worker sẽ chạy job 4 lần (vd birthday voucher gửi 4 notification) |

**Quy tắc cho đồ án:**
- MVP demo dùng **1 worker** + `ENABLE_SCHEDULER=true` — đơn giản nhất, không có vấn đề
- Trong báo cáo, ghi rõ giới hạn này để tránh phản biện hỏi về scale horizontal

**CLI trigger thủ công** (debug, test):
```bash
cd backend && python -m app.jobs.run_once birthday
cd backend && python -m app.jobs.run_once expire_vouchers
```

### 6.10. Backup & demo reliability
- MVP: `pg_dump` thủ công trước mỗi lần demo hoặc migration lớn
- Script: `scripts/backup.sh` chạy `docker compose exec postgres pg_dump -U ... > backup.sql`
- **Pre-demo checklist:** (1) chạy `scripts/backup.sh` ngay trước demo, (2) kiểm `ls -lh` file backup, (3) test restore script trên local lần đầu setup
- **CẢNH BÁO:** KHÔNG dùng `docker compose down -v` (mất volume = mất DB). Chỉ dùng `docker compose down`
- Không cần automated backup cho MVP (luận văn mới cần cron + retention policy)

### 6.11. Web Security Basics (★ MỚI)

Các concern OWASP Top 10 cơ bản — sinh viên CẦN đọc và quyết định trước khi code, vì giảng viên phản biện chắc chắn sẽ hỏi.

#### CSRF (Cross-Site Request Forgery)
- **Quyết định:** Refresh token lưu **HttpOnly cookie** với `SameSite=Strict` + check `Origin`/`Referer` header server-side. Access token trong memory dùng `Authorization: Bearer` header (không phải cookie → không bị CSRF).
- KHÔNG cần CSRF token riêng vì SameSite=Strict đủ cho MVP.

#### XSS (Cross-Site Scripting)
- React mặc định escape mọi user content trong JSX
- **TUYỆT ĐỐI KHÔNG** dùng `dangerouslySetInnerHTML` cho user input (rewards.name, tenant.name, voucher description, ...)
- Validate URL của ảnh user upload trước khi render `<img src={...}>`
- Set `Content-Security-Policy` header (Next.js middleware): `default-src 'self'; img-src 'self' data: https:; script-src 'self'`

#### SQL Injection
- Mọi query qua **SQLAlchemy ORM** (parameterized) — mặc định safe
- Nếu phải dùng raw SQL (vd reporting): BẮT BUỘC dùng `text()` với `bindparam`. Code review enforce
- KHÔNG nối chuỗi SQL với input

#### IDOR (Insecure Direct Object Reference) — intra-tenant
- Cross-tenant đã được cover bởi `tenant_id` filter (6.3)
- **Intra-tenant cần check riêng:** vd `GET /members/{id}` ở `/member` route — backend phải verify `member.user_id == current_user.id` (khách chỉ xem được data của mình), không chỉ check tenant
- Dependency `require_owner_resource()` enforce: `WHERE tenant_id = X AND user_id = current_user.id`

#### Mass assignment
- Schema PATCH phải là **DTO riêng**, KHÔNG tái dùng model SQLAlchemy
- Whitelist field được phép update, vd `MemberUpdateSchema` chỉ có `full_name`, `birthday` — không có `is_shadow`, `system_role`, `password_hash`
- Pydantic + `model_dump(exclude_unset=True)` an toàn nếu schema được thiết kế đúng

#### HTTPS
- Production / demo bắt buộc HTTPS (Let's Encrypt + Caddy hoặc Nginx reverse proxy)
- Dev local chấp nhận HTTP (localhost)
- HSTS header `Strict-Transport-Security: max-age=31536000; includeSubDomains` cho production

#### Secrets management
- `.env` KHÔNG commit (đã trong `.gitignore`)
- `.env.example` commit với value placeholder, không commit secret thật
- Rotate `JWT_SECRET`, `DB_PASSWORD` khi cần — generate bằng `openssl rand -hex 32`
- Khi demo, KHÔNG hard-code credentials trong source code (giảng viên có thể xem repo)

#### CORS
- `allow_origins` = `os.environ.get("FRONTEND_ORIGINS", "").split(",")` — chỉ whitelist domain frontend cụ thể
- **KHÔNG dùng `allow_origins=["*"]`** kể cả dev (dùng `["http://localhost:3000"]` thay)
- `allow_credentials=True` để cookie hoạt động

#### Error response không leak
- Production `DEBUG=False`, custom exception handler trong FastAPI
- KHÔNG return stack trace ra response
- Log đầy đủ ở backend (file `backend/logs/app.log`), trả response generic cho client

#### Security event logging (audit)
Bảng `security_audit_log` (hoặc reuse `notifications` với type=security_event) ghi:
- Login fail (> 3 lần liên tiếp / 10 phút)
- Rate limit triggered
- Cross-tenant access attempt bị reject
- Change password / reset password
- Toggle `tenants.settings.points_on_gross`
- Owner remove staff
- Super Admin approve/suspend tenant

Không cần cho MVP nhưng nên có schema sẵn — giảng viên hỏi trả lời được.

#### Dependency vulnerability
- Pin versions trong `requirements.txt` / `package-lock.json`
- Chạy `pip-audit` + `npm audit` trước mỗi tuần (1 phút check)
- CI tự động chạy audit, fail nếu có HIGH severity

#### Password policy
- Min 8 ký tự
- Không cần complexity rule (NIST 2024 nói complexity rules thực ra giảm security)
- Bcrypt cost ≥ 12 đủ để chống offline attack
- KHÔNG check against common password list trong MVP (dành cho luận văn nếu cần)

---

## 7. Testing

### 7.1. Backend

**Stack test:**
- **Unit tests:** services — tính điểm, upgrade tier, lazy claim voucher, đổi quà, ledger reconcile, verification code flow, birthday job
- **Integration tests:** pytest + httpx + **PostgreSQL testcontainer** (KHÔNG dùng SQLite — tránh sai khác SQL dialect; testcontainer dùng session-scoped fixture để reuse container giữa test, giảm overhead trên Windows)
- **Coverage target:** ~60–70% backend services layer (business logic). KHÔNG cố 100% — chỉ tập trung services. Dùng `pytest-cov` report.

**Fixtures (conftest.py):**
Pytest fixtures dùng chung để tránh viết lại setup mỗi test:
```python
# Backbone
client, db_session

# Tenant fixtures
tenant_a, tenant_b  # 2 tenant riêng biệt cho isolation test

# Token fixtures (đã include X-Tenant-Id phù hợp)
super_admin_token
owner_token_a, owner_token_b
staff_token_a, staff_token_b
member_token_a, member_token_b

# Seed fixtures
seeded_tier_bronze_a, seeded_tier_silver_a
seeded_reward_a, seeded_campaign_a, seeded_membership_a

# Helpers
make_transaction(tenant, member, amount)
make_voucher(campaign, member)
```
KHÔNG cần `factory_boy` cho 8 tuần — pytest fixture đủ.

**Test case critical:**
- Cross-tenant isolation (mỗi module riêng 1 file test trong `tests/integration/`)
- Race condition đổi quà đồng thời (2 request song song qua `asyncio.gather`)
- Shadow → real account merge đầy đủ với verification code, gồm cả case 2 khách cùng SĐT
- Upgrade hạng đúng điều kiện (nhiều tier, sort đúng `min_points`)
- Tier downgrade do config thay đổi → silent re-bind, không push notification "lên hạng"
- **Ledger invariant:** `SUM(delta) = balance` sau mọi kịch bản (`tests/integration/test_ledger_invariant.py`)
- Lazy claim voucher không duplicate (partial unique index test)
- QR fallback flow: khi quét QR khách chưa là thành viên tenant → response 404 NO_MEMBERSHIP → `/pos` chuyển sang form nhập SĐT (Luồng B) → backend upsert user → tạo membership → tích điểm
- **Background job birthday:** gọi function trực tiếp, assert tạo voucher đúng + idempotent (chạy 2 lần cùng ngày không duplicate) + edge case 29/2
- **Authorization horizontal:** role `member` không gọi được API `/merchant/*`; role `staff` không thấy dashboard owner; JWT hết hạn trả 401
- **Lock ordering:** test cố tạo deadlock bằng 2 transaction lock theo thứ tự ngược → service phải retry đúng

### 7.2. Frontend

**Component tests (Vitest + RTL):**
- Form giao dịch (POS), form claim voucher, card thành viên, QR display, voucher list, redemption code dialog

**E2E (Playwright):**
- **Điều kiện làm:** chỉ làm nếu tuần 7 còn ≥ 1.5 ngày rảnh sau manual QA
- 2 flow tối thiểu: (a) staff login + nhập giao dịch, (b) khách đổi quà → nhận mã redemption
- **KHÔNG làm E2E cho PWA offline / iOS** — manual test trên device thật hiệu quả hơn

### 7.3. Manual QA checklist

**Device:**
- 3 cách tích điểm trên: desktop + Android Chrome + iOS Safari
- Cài PWA trên Android + iOS, test offline (mở lại không có mạng)
- 3 breakpoint responsive: mobile (360–400px), tablet (768px), desktop (1280px+). `/pos` ưu tiên tablet, `/member` ưu tiên mobile, `/merchant` ưu tiên desktop

**Multi-tenant:**
- 2 tenant song song để confirm isolation (đã có test tự động, manual để double-check)

**Demo scenario đầy đủ:**
- Tạo shop → cấu hình tier → staff login → giao dịch (3 cách) → khách đổi quà → tạo campaign → khách claim voucher → dùng voucher → upgrade tier → voucher sinh nhật

**Lighthouse PWA (≥85):**
- Chạy Lighthouse trên `/member` PWA — kỳ vọng ≥ 85 cho Performance, Accessibility, Best Practices, PWA
- Fix lỗi dễ: alt text, contrast, label form. KHÔNG cố tối ưu hết.

**Smoke benchmark (tuần 7):**
- `ab -n 500 -c 10` hoặc `locust` 5 phút trên 3 API quan trọng nhất: `POST /transactions`, `GET /member/me`, `GET /merchant/dashboard`
- Mục tiêu p95 < 500ms ở local
- KHÔNG phải load test thật — chỉ baseline để có số báo cáo

### 7.4. CI/CD

**GitHub Actions workflow** (`.github/workflows/ci.yml`):
- Trigger: mỗi push + pull request
- Job: setup PostgreSQL service container → `pip install` → `pytest` + `pytest-cov` → frontend `npm test` + `npm run lint` + `eslint` + `ruff` + `black --check`
- **Quy tắc:** đỏ CI = không merge dù 1 dev. Chấp nhận đỏ ở tuần 1–2 khi setup.

---

## 8. Hướng scale lên luận văn tốt nghiệp

### 8.1. Các tính năng nâng cao có thể thêm sau MVP

| Tính năng | Độ khó | Giá trị luận văn |
|---|---|---|
| **ML cá nhân hóa gợi ý quà** (collaborative filtering) | Trung bình–Cao | Cao — điểm nghiên cứu |
| **Phân khúc khách hàng RFM + K-means** | Trung bình | Cao — data mining |
| **Dự báo churn** (logistic regression / random forest) | Trung bình | Cao — bài toán thực tế |
| **Gamification** (badges, streak, challenges) | Thấp–Trung bình | Trung bình |
| **Referral program** | Thấp | Trung bình |
| **React Native app** | Cao | Cao — kỹ năng cross-platform |
| **Real-time notification (WebSocket + Web Push)** | Trung bình | Trung bình |
| **Public REST API + webhook cho POS tích hợp** | Trung bình | Cao — tư duy platform |
| **Báo cáo nâng cao** (cohort, funnel, retention) | Trung bình | Cao — data analytics |
| **Multi-store cho 1 tenant** | Trung bình | Trung bình |
| **OTP SMS/Email thật** | Thấp | Thấp (chỉ integration) |

### 8.2. Đề xuất chọn 2–3 hướng cho luận văn

Phần MVP tập trung hệ thống. Luận văn nên chọn **1–2 hướng research** (ML/data) + **1 hướng engineering** để cân bằng. Sinh viên chọn theo sở thích:

1. **Phân khúc khách hàng RFM + K-means** — output là cluster label (Champions, Loyal, At Risk, ...). Dashboard cho chủ shop xem phân bố cluster + run chiến dịch nhắm cluster cụ thể. Đơn giản, engineering rõ ràng. (research nhẹ)
2. **Hệ gợi ý quà cá nhân hóa** — content-based (reward category × member preferences) hoặc item-based collaborative filtering. **KHÔNG phải kết quả của K-means** — đây là 2 bài toán khác. Có thể dùng cluster từ (1) làm feature input. (research nặng hơn)
3. **Dự báo churn** (logistic regression / random forest / XGBoost) — cảnh báo chủ shop khách sắp rời bỏ. Cần feature từ ledger + last_login_at + last_activity_at. (research)
4. **Mobile app React Native** thay PWA — thêm endpoint FCM token registration + push notification. UI layer viết lại; business logic backend ~90% giữ nguyên. (engineering)
5. **Backup option (cho sinh viên backend-first không muốn ML/mobile):** Observability + Multi-store + Public REST API + webhook ký HMAC cho tích hợp POS bên thứ ba + audit log đầy đủ + distributed tracing (OpenTelemetry). (engineering nặng)

**Khuyến nghị:** chọn (1) + (3) + (4) — cân bằng research/engineering, có sản phẩm demo trực quan.

### 8.3. Vì sao MVP không cần viết lại ở giai đoạn luận văn
- **Dữ liệu đã có sẵn** (transactions, point_ledger, campaigns, vouchers) → ML có nguồn data huấn luyện
- **Kiến trúc modular** → thêm module `ml/` không ảnh hưởng core
- **Point ledger** từ MVP → là feature store cơ bản cho ML (event sourcing pattern)
- **PWA → native:** business logic backend giữ nguyên ~90%, chỉ thêm endpoints FCM token registration + gửi push notification. UI layer viết lại với React Native (chia sẻ type definitions qua OpenAPI codegen).

### 8.4. Rủi ro khi scale lên luận văn (★ MỚI)

**Data sparsity — rủi ro #1:**
- MVP chỉ có seed data demo (~20 khách, ~100 giao dịch). Train ML model trên dataset như vậy sẽ cho **kết quả vô nghĩa** (overfit hoặc cold start 100%).
- **Giải pháp khi vào luận văn:**
  - **(a) Sinh dữ liệu synthetic** có phân phối thực: 500 khách × 6 tháng giao dịch theo Poisson + Pareto, ngày sinh theo random uniform. Có thể viết script `scripts/generate_synthetic_data.py`.
  - **(b) Xin dataset loyalty public** từ Kaggle (vd "Online Retail II", "Brazilian E-Commerce"). Map schema sang loyalty platform.
  - **(c) Triển khai thật cho 1–2 quán café** (lý tưởng nhưng khó coordinate).
- **KHÔNG giả định** dataset tự động đủ.

**Compute cho ML training:**
- Laptop sinh viên có thể không đủ RAM/GPU cho model phức tạp. Cân nhắc Google Colab free tier hoặc giảm complexity.

**Privacy của data thật (nếu chọn option c):**
- Cần ẩn danh PII trước khi phân tích. Dùng `anonymize_user()` (đã design ở 4.2).

---

## 9. Rủi ro & cân nhắc

| Rủi ro | Mức độ | Cách giảm thiểu |
|---|---|---|
| **Multi-tenant phức tạp hơn dự kiến** | Trung bình | Test cross-tenant từ tuần 2, dùng dependency thống nhất |
| **PWA không ổn định trên iOS Safari** | Trung bình | Ưu tiên Android, iOS fallback responsive web |
| **Quét QR camera web trên iOS** | Trung bình | Fallback nhập mã `fallback_code` thủ công (xem 6.2) |
| **Race condition tích/đổi điểm** | Trung bình | DB transaction + row lock + lock ordering + point_ledger + test |
| **Scope creep** | Cao | Checklist MVP rõ. **Tuần 8 KHÔNG code feature mới.** Mỗi đầu tuần review checklist với giảng viên. Mọi đề xuất feature mới từ tuần 4+ chuyển sang luận văn. |
| **4 UI quá tải** | Trung bình | Chung component library. `/admin` minimal, ưu tiên `/pos` và `/member` |
| **Deploy/demo không kịp tuần 8** | Cao | Dockerfile + docker-compose từ tuần 1. Fallback: local + ngrok cho demo nếu không kịp VPS |
| **Seed data thiếu → demo trống** | Trung bình | Viết `scripts/seed.py` từ tuần 2, chạy sau migration |
| **Alembic migration conflict** | Thấp | 1 dev, 1 migration / feature, commit ngay. Backup DB trước migration lớn |
| **Verification code (OTP) "sao không SMS thật?"** | Trung bình | Adapter pattern interface có sẵn, MVP log console + luận văn SMS thật |
| **Lỗ hổng QR cross-tenant** | Đã xử lý | Consent flow Luồng C + JWT server secret + rate limit |
| **Point ledger bị skip trong code** | Trung bình | Trigger DB append-only + `test_ledger_invariant.py` |
| **Performance test phản biện hỏi** | Trung bình | Smoke benchmark tuần 7 (`ab` 500 req trên 3 endpoint), có số báo cáo. Load test thật cho luận văn |
| **APScheduler chạy nhiều lần do hot reload** | Đã xử lý | `ENABLE_SCHEDULER=false` mặc định dev |
| **Sinh viên ốm / cách ly / trùng thi cuối kỳ** | Trung bình | Đẩy việc khó lên tuần 1–5. Tuần 7 là buffer chủ động. Mất tuần nào → cắt theo danh sách P2 (xem 10) |
| **Sinh viên thiếu kinh nghiệm Docker / Alembic / SQLAlchemy async** | Trung bình | Tuần 1 có buffer học. Dùng Alembic autogenerate giảm viết tay. Bí thì fallback SQLAlchemy sync tạm |
| **PostgreSQL testcontainers chậm/flaky trên Windows** | Trung bình | Session-scoped fixture reuse container. Fallback profile `test` với Postgres compose riêng |
| **Service worker debug khó (cache cũ, iOS hạn chế)** | Trung bình | Dev mode disable SW (`disable: NODE_ENV === 'development'`). DevTools "Update on reload". Test build production từ tuần 4 |
| **Không có iPhone test iOS Safari** | Trung bình | BrowserStack free trial hoặc mượn bạn từ tuần 4 (không đợi tuần 7). Fallback: ghi rõ "test trên Android + iOS simulator" trong báo cáo |
| **Next.js 14 App Router gotchas (Server vs Client Components, hydration, middleware)** | Thấp–Trung bình | Tuần 1 có buffer. Đọc Next.js docs App Router kỹ. Bí thì fallback Pages Router |
| **Không có ai review code (sinh viên 1 mình)** | Trung bình | Self-review checklist + nhờ giảng viên review 1 lần ở milestone tuần 4 |
| **Mất dữ liệu Git / hỏng máy** | Thấp–Trung bình | `git push` hàng ngày lên GitHub. Backup `.env` cá nhân (không commit) lên password manager |
| **Giảng viên hướng dẫn không phản hồi kịp** | Trung bình | Hẹn lịch milestone định kỳ ngay đầu kỳ (cuối tuần 2/4/6/8). Liên lạc backup qua email + Zalo |
| **Data sparsity khi chuyển sang luận văn ML** | Trung bình | Đã có plan ở 8.4 (synthetic data hoặc dataset Kaggle) |

---

## 10. Kế hoạch 8 tuần (sơ bộ, chi tiết ra ở writing-plans)

### Giả định thời gian
- **~25 giờ/tuần × 8 tuần ≈ 200 giờ tổng** (sinh viên thực tập có môn học song song, không phải full-time)
- **Tuần 7 = buffer chủ động:** nếu các tuần trước chậm thì dùng tuần 7 bù; nếu đúng tiến độ thì tuần 7 dùng cho polish và QA đầy đủ
- **Tuần 8 = không feature mới**, chỉ bug fix + deploy + báo cáo

### Bảng phân bổ tuần

| Tuần | Backend | Frontend | Khác | Cuối tuần phải có |
|---|---|---|---|---|
| **1** | Setup Docker Compose, PostgreSQL, Alembic, schema base, auth (register/login/refresh), JWT middleware, slowapi rate limit | Setup Next.js, TypeScript, Tailwind, shadcn/ui, layout chung, login/register pages, **PWA skeleton** (manifest, service worker disable trong dev) | `.env.example`, README, Dockerfile, GitHub Actions CI cơ bản | Đăng nhập được + Docker chạy được + CI xanh |
| **2** | Module tenants (đăng ký + Super Admin minimal approve), tenant_staff, tiers, point_rules, verification_codes, **claim shadow flow đầy đủ**, settings module | `/merchant` onboarding (tenant register, cấu hình tier + point rule), `/admin` minimal, **`/merchant/staff` quản lý nhân viên** | **Seed v1** (2 tenant, 5 tier, 3 point_rule, 5 staff), test cross-tenant đầu tiên, **Milestone review #1 với giảng viên** | Tenant + tier + staff CRUD chạy được |
| **3** | Module members (shadow upsert atomic), transactions method (a) nhập thủ công, **point_ledger (append + reconcile + trigger DB)**, upgrade tier logic | `/pos` UI skeleton + form nhập giao dịch thủ công + lịch sử khách | Test ledger invariant + reconcile endpoint | Tích điểm thủ công + ledger reconcile pass |
| **4** | Transactions method (b) QR shop + (c) QR khách (chỉ khi đã là thành viên tenant) + **fallback về Luồng B nếu khách chưa là thành viên**, rewards CRUD, redemption flow (Luồng D), **birthday job (APScheduler timezone Asia/Ho_Chi_Minh)** | `/pos` scan QR (html5-qrcode), `/member` PWA QR cá nhân rolling, catalog rewards + đổi quà | **Test trên Android device thật**, **Milestone review #2 với giảng viên** | 3 cách tích điểm chạy + đổi quà chạy + birthday job test |
| **5** | Campaigns CRUD, vouchers (lazy claim atomic), notifications module, audit settings | `/merchant` quản lý campaigns, `/member` list available campaigns + claim voucher + voucher của mình | **Seed v2** (thêm transactions, rewards, campaigns, vouchers) | Toàn bộ business logic backend xong |
| **6** | Analytics API (dashboard queries + ROI campaign), finalize `/admin` minimal, bug fix backend sớm | `/merchant` dashboard, `/member` lịch sử + voucher đã có + voucher đã dùng, polish PWA | **Milestone review #3 với giảng viên** | Feature-complete (mọi module MVP done) |
| **7** | **Buffer + bug fix** + integration tests còn thiếu + performance check (index, N+1 query, smoke benchmark `ab`) | `/pos` + `/member` + `/merchant` polish, **test iOS Safari**, manual QA checklist đầy đủ, Lighthouse PWA | Deploy dry-run, viết demo scenario, mượn iPhone test | QA pass, ready to demo |
| **8** | **KHÔNG code feature mới.** Chỉ bug fix critical, deploy demo, security smoke test | Smoke test toàn hệ thống, polish UI lần cuối | **Deploy VPS / Docker + ngrok**, viết báo cáo PDF, chuẩn bị slide demo, **Milestone review #4 (bảo vệ nháp)** | Báo cáo + slide + demo URL chạy được |

### Ưu tiên cắt khi chậm tiến độ (P0 / P1 / P2)

Nếu đến tuần 6 thấy không kịp, **cắt theo thứ tự dưới đây** (P2 cắt trước):

**P2 — Cắt trước nếu chậm:**
1. Dashboard charts đẹp → bảng số thô là đủ
2. ROI campaign analytics → để cho luận văn
3. iOS Safari polish → chỉ cần chạy được, không polish
4. Lighthouse PWA target ≥85 → bỏ qua
5. E2E Playwright (vốn đã optional)
6. Smoke benchmark `ab` → bỏ qua, chỉ test functional

**P1 — Cắt nếu vẫn chậm:**
7. `/admin` UI → chỉ cần Swagger-based, không UI riêng
8. Birthday job APScheduler → chạy script `python -m app.jobs.run_once birthday` thủ công khi demo
9. `/merchant` Audit settings → bỏ qua, chỉ cần endpoint update
10. Notifications module → chỉ cần INSERT bảng, không cần list/mark-read API
11. (đã đơn giản hóa — Luồng C giờ chỉ fall back về Luồng B nếu khách chưa là thành viên, không cần Plan A/B nữa)

**P0 — TUYỆT ĐỐI KHÔNG CẮT (đây là core MVP):**
- Multi-tenant + isolation
- Auth + JWT + phân quyền
- Point ledger + reconcile invariant
- 3 cách tích điểm (đặc biệt Luồng B nhập SĐT — default cho khách mới ở tenant)
- Đổi quà + redemption flow
- Lazy claim voucher
- Verification code (claim shadow)
- PWA `/member` cài được trên Android

### Milestone review với giảng viên hướng dẫn

| Cuối tuần | Mục tiêu review | Demo |
|---|---|---|
| **2** | Confirm hướng đúng, xác nhận scope, bắt lỗi định hướng sớm | Auth + tenant + tier + staff CRUD |
| **4** | Check technical risk (QR, consent, ledger), bắt lỗi kỹ thuật giữa kỳ | 3 cách tích điểm + đổi quà + ledger reconcile |
| **6** | Thống nhất scope đóng (feature-complete), không thêm gì mới | Toàn bộ MVP, dashboard, claim voucher |
| **8** | Bảo vệ nháp, chuẩn bị bảo vệ chính thức | Demo end-to-end + báo cáo PDF + slide |

**Hẹn lịch milestone ngay đầu kỳ** với giảng viên — không đợi đến lúc cần. Backup contact qua email + Zalo.

### Nguyên tắc kỷ luật

- Cross-tenant test từ tuần 2 — phát hiện lỗi sớm
- Seed script từ tuần 2 — luôn có data để demo
- Docker + CI từ tuần 1 — không bất ngờ tuần cuối
- **Tuần 8 không code feature mới** — chống scope creep
- **Mỗi đầu tuần** review checklist với giảng viên (qua email cũng được nếu không gặp được)
- **`git push` hàng ngày** lên GitHub — chống mất việc do hỏng máy

---

## 11. Kết luận

Đề tài đáp ứng đúng yêu cầu:
- **Đủ nhỏ cho 8 tuần (~200 giờ):** 11 module MVP có scope rõ ràng, timeline có **buffer tuần 7** và 4 milestone review với giảng viên, có ưu tiên cắt **P0/P1/P2** khi chậm tiến độ
- **Đủ khả năng scale lên luận văn:** 5 hướng (RFM, recommendation, churn, mobile native, observability/public API) — đều có path triển khai rõ và có warning về data sparsity
- **Phù hợp stack Next.js + FastAPI** — cả MVP và phần nâng cao
- **Ứng dụng thực tế cao:** loyalty program đang là nhu cầu phổ biến của các SME tại Việt Nam
- **Point ledger append-only từ MVP:** nền tảng audit, hoàn hủy giao dịch, và là feature store cho ML ở luận văn
- **Bảo mật được cân nhắc từ đầu:** SĐT-based onboarding qua Luồng B (đơn giản, không edge case), QR server-signed + fallback offline, verification code HMAC, rate limiting hybrid IP+identifier, multi-tenant isolation, lock ordering, web security basics (CSRF/XSS/IDOR) — đều ở mức phù hợp cho đồ án thực tập
- **Có acceptance criteria đo được** (1.2.1) để biết khi nào MVP hoàn thành
- **Có plan rủi ro thực tế** (ốm, kinh nghiệm thiếu, device test, timezone, ...) — không lạc quan
