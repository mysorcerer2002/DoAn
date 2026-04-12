# DANH SÁCH TÍNH NĂNG

**Đề tài:** Nền tảng Tích điểm Thành viên và Quản lý Chương trình Khuyến mãi cho Doanh nghiệp vừa và nhỏ

**Loại đề tài:** Đồ án thực tập tốt nghiệp (8 tuần) — có khả năng mở rộng thành luận văn tốt nghiệp

**Công nghệ sử dụng:**
- Frontend: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, PWA (`@serwist/next`)
- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async)
- Database: PostgreSQL 15+ (multi-tenant)
- Auth: JWT + bcrypt
- Background jobs: APScheduler
- Testing: pytest, httpx, PostgreSQL testcontainers, Vitest, React Testing Library
- DevOps: Docker Compose, Alembic, GitHub Actions CI

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Phần I — Tính năng MVP (8 tuần thực tập)](#phần-i--tính-năng-mvp-8-tuần-thực-tập)
   - 2.1. [Tính năng theo vai trò người dùng](#21-tính-năng-theo-vai-trò-người-dùng)
   - 2.2. [Tính năng kỹ thuật (cross-cutting)](#22-tính-năng-kỹ-thuật-cross-cutting)
   - 2.3. [Tính năng bảo mật](#23-tính-năng-bảo-mật)
   - 2.4. [Tính năng kiểm thử và DevOps](#24-tính-năng-kiểm-thử-và-devops)
3. [Phần II — Tính năng mở rộng cho luận văn tốt nghiệp](#phần-ii--tính-năng-mở-rộng-cho-luận-văn-tốt-nghiệp)
4. [Phần III — Số liệu tổng quan](#phần-iii--số-liệu-tổng-quan)
5. [Phụ lục — Các luồng nghiệp vụ chính](#phụ-lục--các-luồng-nghiệp-vụ-chính)

---

## 1. Tổng quan

Hệ thống là một **nền tảng đa người thuê (multi-tenant)** cho phép nhiều doanh nghiệp vừa và nhỏ (quán cà phê, nhà hàng, shop bán lẻ) tự vận hành chương trình khách hàng thân thiết mà không cần tự phát triển hệ thống riêng.

Hệ thống phục vụ **4 vai trò người dùng** với 4 giao diện riêng biệt:

| Vai trò | Mô tả | Giao diện |
|---|---|---|
| Super Admin | Quản lý nền tảng, duyệt doanh nghiệp đăng ký | Web `/admin` |
| Chủ doanh nghiệp | Cấu hình chương trình tích điểm, tạo quà/khuyến mãi, xem thống kê | Web `/merchant` |
| Nhân viên cửa hàng | Nhập giao dịch, quét QR khách, xác nhận đổi quà | Web `/pos` (tablet) |
| Khách hàng cuối | Xem điểm, hạng, lịch sử, đổi quà, xem voucher | PWA `/member` |

---

## Phần I — Tính năng MVP (8 tuần thực tập)

### 2.1. Tính năng theo vai trò người dùng

#### 2.1.1. Super Admin (`/admin`)

| STT | Tính năng | Mô tả |
|---|---|---|
| 1.1 | Đăng nhập | Xác thực qua JWT, refresh token 7 ngày |
| 1.2 | Duyệt doanh nghiệp đăng ký | Hiển thị danh sách tenant trạng thái `pending`, cho phép phê duyệt hoặc từ chối |
| 1.3 | Xem thống kê nền tảng cơ bản | Tổng số tenant, tổng số người dùng, tổng số giao dịch toàn hệ thống |

> Ghi chú: Giao diện `/admin` chỉ gồm 1 trang minimal cho phạm vi MVP. Các thao tác nâng cao (suspend tenant, audit log đầy đủ) thực hiện qua Swagger hoặc dành cho giai đoạn luận văn.

#### 2.1.2. Chủ doanh nghiệp (`/merchant`)

**A. Quản lý doanh nghiệp**

| STT | Tính năng | Mô tả |
|---|---|---|
| 2.1 | Đăng ký tài khoản doanh nghiệp | Form đăng ký với tên, mô tả, logo. Hệ thống tự động sinh slug duy nhất |
| 2.2 | Cấu hình thông tin shop | Cập nhật tên, mô tả, logo, thông tin liên hệ |
| 2.3 | Cấu hình settings shop | `points_on_gross`, `voucher_default_ttl_days`, `redemption_default_ttl_days`, `birthday_campaign_id`, `signup_bonus_points`. Có audit log khi thay đổi |

**B. Quản lý nhân viên**

| STT | Tính năng | Mô tả |
|---|---|---|
| 2.4 | Thêm nhân viên mới | Nhập email, hệ thống tự tạo shadow account và sinh verification code |
| 2.5 | Đổi role nhân viên | Chuyển đổi giữa role `owner` và `staff` |
| 2.6 | Xóa nhân viên | Xóa quyền truy cập của nhân viên, revoke refresh token, transactions cũ vẫn được giữ historical |

**C. Quản lý hạng thành viên**

| STT | Tính năng | Mô tả |
|---|---|---|
| 2.7 | CRUD hạng thành viên | Tạo, sửa, xóa các hạng (Bronze, Silver, Gold...) với `min_points` và quyền lợi |
| 2.8 | Cấu hình quy tắc tích điểm | Quy đổi VND sang điểm (vd: 1 điểm / 1.000 VND), điều kiện tối thiểu |
| 2.9 | Tự động cập nhật hạng khi đổi cấu hình | Khi sửa `min_points`, hệ thống tự động tính lại hạng cho khách hiện tại |

**D. Quản lý quà tặng**

| STT | Tính năng | Mô tả |
|---|---|---|
| 2.10 | CRUD catalog quà | Tên, mô tả, ảnh, số điểm cần đổi, số lượng tồn kho |
| 2.11 | Stock có thể không giới hạn | Cho phép đặt stock = NULL nếu quà không giới hạn (vd voucher) |
| 2.12 | Soft delete quà | Xóa mềm để bảo vệ FK với redemption history |

**E. Quản lý chiến dịch khuyến mãi**

| STT | Tính năng | Mô tả |
|---|---|---|
| 2.13 | CRUD chiến dịch | Loại giảm giá (%, cố định), điều kiện đơn tối thiểu, giảm tối đa, áp dụng cho hạng nào, thời gian, số lượng tối đa |
| 2.14 | Lazy claim model | Hệ thống KHÔNG tự động phát voucher hàng loạt — khách phải tự bấm nhận |
| 2.15 | Xem voucher đã phát của chiến dịch | Danh sách voucher đã phát, đã dùng, ROI doanh thu từ voucher |

**F. Dashboard và báo cáo**

| STT | Tính năng | Mô tả |
|---|---|---|
| 2.16 | Số lượng thành viên | Hiển thị tổng số khách của shop |
| 2.17 | Giao dịch theo ngày | Biểu đồ đường giao dịch trong 30 ngày gần nhất |
| 2.18 | Tổng doanh thu | Doanh thu gross, net theo ngày/tuần/tháng |
| 2.19 | Tỉ lệ đổi điểm | Tỉ lệ khách đổi quà / tổng số khách có điểm |
| 2.20 | Phân bố hạng thành viên | Biểu đồ tròn phân bố khách theo hạng |
| 2.21 | ROI campaign | Doanh thu từ giao dịch có sử dụng voucher của từng chiến dịch (ưu tiên P1) |

#### 2.1.3. Nhân viên cửa hàng (`/pos`)

Giao diện tối ưu cho tablet ngang.

| STT | Tính năng | Mô tả |
|---|---|---|
| 3.1 | Đăng nhập và chọn shop làm việc | Xác thực qua JWT, header `X-Tenant-Id` xác định shop hiện tại |
| 3.2 | Tích điểm qua SĐT (default cho khách mới) | Nhập số điện thoại khách + số tiền. Backend tự upsert: tạo shadow account nếu khách hoàn toàn mới, hoặc tạo membership mới nếu khách đã có user (do tenant khác). KHÔNG cần consent flow phức tạp |
| 3.3 | Tích điểm qua QR cửa hàng | Khách (đã có app) quét QR cửa hàng, deeplink có HMAC token |
| 3.4 | Tích điểm qua QR cá nhân khách | Nhân viên quét QR cá nhân của khách đã là thành viên tenant (JWT server-signed, exp 120s, kèm fallback code 8 ký tự). Nếu khách chưa là thành viên → fall back về tích điểm qua SĐT (3.2) |
| 3.5 | Hiển thị QR cửa hàng | QR tĩnh có HMAC token để khách quét |
| 3.6 | Xác nhận đổi quà | Quét hoặc nhập mã redemption từ khách, xác nhận đã sử dụng |
| 3.7 | Áp voucher khi tạo giao dịch | Nhập mã voucher, hệ thống tính giảm giá (gross → net) |
| 3.8 | Xem lịch sử giao dịch | Danh sách giao dịch nhân viên đã tạo trong shop |

#### 2.1.4. Khách hàng cuối (`/member` PWA)

**A. Xác thực và hồ sơ**

| STT | Tính năng | Mô tả |
|---|---|---|
| 4.1 | Đăng ký tài khoản | Số điện thoại chuẩn hóa E.164, mật khẩu, họ tên, sinh nhật |
| 4.2 | Claim shadow account | Nhận tài khoản đã được nhân viên tạo trước qua verification code 6 số |
| 4.3 | Đăng nhập | Email/SĐT + mật khẩu |
| 4.4 | Reset mật khẩu | Qua verification code, revoke tất cả token cũ |
| 4.5 | Cập nhật hồ sơ cá nhân | Họ tên, email, sinh nhật |

**B. Tích điểm và hạng**

| STT | Tính năng | Mô tả |
|---|---|---|
| 4.6 | Xem điểm hiện tại | Số dư điểm và tổng điểm tích lũy ở từng shop |
| 4.7 | Xem hạng và quyền lợi | Hạng hiện tại với danh sách quyền lợi |
| 4.8 | Hiển thị QR cá nhân | QR rolling tự refresh, kèm fallback code dùng khi mạng yếu |
| 4.9 | Xem lịch sử giao dịch | Lịch sử tích/đổi điểm với entries từ point ledger |
| 4.10 | Nhận thông báo lên hạng | Push notification khi đủ điều kiện lên hạng cao hơn |

**C. Đổi quà**

| STT | Tính năng | Mô tả |
|---|---|---|
| 4.11 | Xem catalog quà | Danh sách quà của shop với điểm cần đổi |
| 4.12 | Đổi điểm lấy quà | Bấm đổi → nhận mã redemption |
| 4.13 | Xem danh sách quà đã đổi | Lịch sử redemption với trạng thái pending, used, expired |

**D. Voucher và khuyến mãi**

| STT | Tính năng | Mô tả |
|---|---|---|
| 4.14 | Xem chiến dịch đủ điều kiện claim | Danh sách campaign khách có thể nhận voucher |
| 4.15 | Nhận voucher (lazy claim) | Bấm nhận → hệ thống sinh voucher cá nhân |
| 4.16 | Xem voucher của mình | Danh sách voucher với trạng thái issued, used, expired |
| 4.17 | Tự động nhận voucher sinh nhật | Background job tự động phát voucher vào ngày sinh nhật |

**E. Đa shop và browse**

| STT | Tính năng | Mô tả |
|---|---|---|
| 4.18 | Xem danh sách shop đang là thành viên | Liệt kê các shop khách đã tham gia, xem điểm/hạng của từng shop |
| 4.19 | Browse danh sách shop public | `/member/shops` hiển thị danh sách tất cả shop đang `active` trên nền tảng, có search/filter, xem chi tiết tier benefits trước khi join |
| 4.20 | Tự join shop từ app (Luồng L) | Khách bấm "Tham gia [tên shop]" → backend tạo membership mới qua upsert. Yêu cầu: khách phải đã có user account (đã đăng ký hoặc đã claim shadow trước đó) |
| 4.21 | Tham gia shop qua SĐT tại quầy (Luồng B) | Đối với khách hoàn toàn mới chưa có app: nhân viên đăng ký giúp qua SĐT tại cửa hàng — backend tự động tạo shadow account và membership |

**F. Tính năng PWA**

| STT | Tính năng | Mô tả |
|---|---|---|
| 4.20 | Cài đặt như app trên điện thoại | Manifest + service worker `@serwist/next`, hỗ trợ Android và iOS |
| 4.21 | Hoạt động offline cơ bản | Cache dữ liệu để xem điểm và voucher đã có khi không có mạng |
| 4.22 | Notification in-app | Hiển thị thông báo trong ứng dụng (chưa hỗ trợ Web Push, dành cho luận văn) |

---

### 2.2. Tính năng kỹ thuật (cross-cutting)

| STT | Tính năng | Mô tả |
|---|---|---|
| K.1 | Multi-tenant isolation | Shared database, shared schema, phân tách qua cột `tenant_id`. Header `X-Tenant-Id` xác định context, cache `cachetools.TTLCache` 60 giây |
| K.2 | Point Ledger append-only | Bảng audit cho mọi biến động điểm. PostgreSQL trigger enforce immutability. Reconcile invariant `SUM(delta) = balance` |
| K.3 | JWT đơn giản | Token chỉ chứa `user_id` và `system_role`. Tenant context lấy từ header, không hard-code trong JWT |
| K.4 | Phân quyền 4 cấp | `require_super_admin`, `require_owner_in_tenant`, `require_staff_in_tenant`, `require_customer_in_tenant` |
| K.5 | Verification code HMAC-SHA256 | Mã 6 số, TTL 10 phút, dùng 1 lần. Dùng cho claim shadow account và reset mật khẩu |
| K.6 | Xử lý race condition | `SELECT FOR UPDATE` trên membership, lock ordering rule, retry deadlock với backoff |
| K.7 | Atomic UPDATE chống TOCTOU | `UPDATE campaigns SET issued_count = issued_count + 1 WHERE issued_count < max_issuances` |
| K.8 | Partial unique index | `UNIQUE(campaign_id, membership_id) WHERE status NOT IN ('expired','used')` để chống claim trùng nhưng cho phép voucher sinh nhật năm sau |
| K.9 | Background jobs | APScheduler với timezone `Asia/Ho_Chi_Minh` cho voucher sinh nhật và expire voucher/redemption |
| K.10 | Rate limiting | `slowapi` middleware với hybrid IP + identifier (chống brute force và chống chặn nhầm khi shared WiFi) |
| K.11 | Notification module | Lưu, list, mark-as-read thông báo in-app. Các service khác gọi để đẩy notification |
| K.12 | Settings audit log | Ghi lại mọi thay đổi `tenants.settings` với who, when, old_value, new_value |
| K.13 | Dashboard analytics | Query trực tiếp PostgreSQL với index trên `tenant_id` + `created_at`. Không cần materialized view trong MVP |
| K.14 | Seed data script | `scripts/seed.py` tạo 2 tenant, 5 tier, 20 khách, 100 giao dịch để demo |

---

### 2.3. Tính năng bảo mật

Tham chiếu OWASP Top 10:

| STT | Tính năng | Mô tả |
|---|---|---|
| S.1 | CSRF protection | HttpOnly cookie với SameSite=Strict + Origin/Referer check |
| S.2 | XSS prevention | React mặc định escape, Content-Security-Policy header, không dùng dangerouslySetInnerHTML cho user input |
| S.3 | SQL injection prevention | SQLAlchemy ORM parameterized queries, raw SQL bắt buộc dùng bindparam |
| S.4 | IDOR intra-tenant | `require_owner_resource()` check `resource.user_id == current_user.id` ngoài check tenant_id |
| S.5 | Mass assignment prevention | DTO Pydantic riêng cho PATCH, không tái dùng model SQLAlchemy |
| S.6 | HTTPS enforcement | Production bắt buộc HTTPS với Let's Encrypt + Caddy/Nginx, HSTS header |
| S.7 | CORS whitelist | `FRONTEND_ORIGINS` env, không dùng wildcard `*` |
| S.8 | Secrets management | `.env.example` commit với placeholder, `.env` trong `.gitignore` |
| S.9 | Error response không leak | Production `DEBUG=False`, custom exception handler, không trả stack trace |
| S.10 | Password policy | Min 8 ký tự, bcrypt cost ≥ 12 |
| S.11 | Token revoke | Tự động revoke refresh token khi logout, đổi mật khẩu, staff bị xóa, tenant bị suspend |
| S.12 | Rate limiting toàn diện | Login, register, refresh, verify-code, transaction, QR, voucher claim, settings |

---

### 2.4. Tính năng kiểm thử và DevOps

| STT | Tính năng | Mô tả |
|---|---|---|
| T.1 | Unit tests | pytest với coverage target 60-70% cho services layer |
| T.2 | Integration tests | pytest + httpx + PostgreSQL testcontainers (session-scoped fixture) |
| T.3 | Cross-tenant isolation tests | File test riêng cho mỗi module, đảm bảo dữ liệu không lẫn giữa tenant |
| T.4 | Race condition tests | Test 2 request đổi quà đồng thời, claim voucher song song |
| T.5 | Ledger invariant tests | Verify `SUM(delta) = balance` sau mọi kịch bản test |
| T.6 | Background job tests | Test birthday job với edge case 29/2, đảm bảo idempotent khi chạy 2 lần |
| T.7 | Authorization horizontal tests | Đảm bảo member không gọi được merchant API, staff không xem được dashboard owner |
| T.8 | Frontend component tests | Vitest + React Testing Library cho form giao dịch, QR display, voucher list |
| T.9 | Manual QA checklist | Test 3 cách tích điểm trên Android Chrome + iOS Safari, PWA offline, 3 breakpoint responsive |
| T.10 | Lighthouse PWA score | Mục tiêu ≥ 85 cho Performance, Accessibility, Best Practices, PWA |
| T.11 | Smoke benchmark | `ab -n 500 -c 10` trên 3 endpoint quan trọng, mục tiêu p95 < 500ms |
| T.12 | GitHub Actions CI | Chạy pytest, vitest, lint mỗi push và pull request |
| T.13 | Docker Compose dev | Postgres + backend + frontend + Mailtrap (SMTP fake) |
| T.14 | Alembic migration | Entrypoint Docker chạy `alembic upgrade head` trước `uvicorn` |
| T.15 | Backup script | `scripts/backup.sh` chạy `pg_dump` thủ công trước demo |

---

## Phần II — Tính năng mở rộng cho luận văn tốt nghiệp

### 3.1. Hướng nghiên cứu (research)

| STT | Tính năng | Mô tả |
|---|---|---|
| R.1 | Phân khúc khách hàng RFM + K-means | Phân cụm khách hàng theo Recency, Frequency, Monetary. Dashboard cho chủ shop xem phân bố cluster |
| R.2 | Hệ gợi ý quà cá nhân hóa | Content-based hoặc item-based collaborative filtering, gợi ý quà phù hợp từng khách |
| R.3 | Dự báo churn | Logistic regression / random forest / XGBoost để cảnh báo khách sắp rời bỏ |
| R.4 | Báo cáo nâng cao | Cohort analysis, funnel, retention rate |

### 3.2. Hướng kỹ thuật (engineering)

| STT | Tính năng | Mô tả |
|---|---|---|
| E.1 | Mobile app React Native | Thay thế PWA, hỗ trợ FCM push notification |
| E.2 | Public REST API + webhook | Cho phép POS bên thứ ba tích hợp, webhook ký HMAC signature |
| E.3 | Real-time notification | WebSocket + Web Push API |
| E.4 | Multi-store cho 1 tenant | Hỗ trợ nhiều chi nhánh, nhân viên theo chi nhánh |
| E.5 | OTP SMS thật | Tích hợp Twilio hoặc eSMS VN qua adapter pattern đã chuẩn bị sẵn |
| E.6 | Super Admin UI đầy đủ | Audit logs, suspend tenant, billing |
| E.7 | Đa ngôn ngữ và đa tiền tệ | i18n library, multi-currency support |
| E.8 | Refund / hủy giao dịch | Thêm `transactions.status`, voucher restore policy |
| E.9 | Idempotency key | Cho transactions và redemptions khi có mobile client |
| E.10 | Distributed lock | Redis lock cho multi-worker scheduler |
| E.11 | Observability | OpenTelemetry distributed tracing, security audit log đầy đủ |
| E.12 | Tích hợp cổng thanh toán | VNPay, Momo, ZaloPay |
| E.13 | Gamification | Badges, streak bonus, challenges |
| E.14 | Referral program | Giới thiệu bạn bè nhận điểm, cây giới thiệu |

---

## Phần III — Số liệu tổng quan

| Tiêu chí | Phạm vi MVP (8 tuần) | Phạm vi Luận văn |
|---|---|---|
| Số module backend | 13 modules | + 3 (ml, audit, public_api) |
| Số route frontend | 4 (`/admin`, `/merchant`, `/pos`, `/member`) | + 1 (mobile native) |
| Số bảng database | 14 bảng | + 5 (member_segments, api_keys, security_audit_log, fcm_tokens, stores) |
| Số luồng nghiệp vụ chính | 12 luồng (A → L, trừ I refund) | + 1 (Luồng I refund) |
| Số vai trò người dùng | 4 | Không thay đổi |
| Số tính năng MVP | 80+ tính năng | — |

### 3.1. Danh sách 13 module backend (MVP)

| STT | Module | Trách nhiệm |
|---|---|---|
| 1 | auth | Đăng ký, đăng nhập, refresh token, verification code |
| 2 | tenants | Đăng ký doanh nghiệp, duyệt, cấu hình settings |
| 3 | staff | CRUD nhân viên của tenant |
| 4 | members | Tìm/tạo khách, shadow flow, lịch sử |
| 5 | transactions | Tạo giao dịch (3 cách), tính điểm, gọi ledger |
| 6 | rewards | CRUD catalog quà, đổi quà, xác nhận sử dụng |
| 7 | campaigns | CRUD chiến dịch, list eligible cho khách |
| 8 | vouchers | Claim voucher, list, dùng voucher |
| 9 | tiers | Cấu hình hạng, logic upgrade |
| 10 | ledger | Insert entry (internal), query lịch sử, reconcile |
| 11 | notifications | List, mark-as-read, đẩy notification |
| 12 | analytics | Tổng hợp số liệu dashboard |
| 13 | jobs | Background jobs (birthday, expire) |

### 3.2. Danh sách 14 bảng database (MVP)

| STT | Bảng | Mục đích |
|---|---|---|
| 1 | users | Tài khoản toàn hệ thống |
| 2 | tenants | Doanh nghiệp đăng ký nền tảng |
| 3 | tenant_staff | Liên kết user với tenant theo vai trò |
| 4 | memberships | Quan hệ khách hàng ↔ tenant |
| 5 | tiers | Cấu hình hạng thành viên |
| 6 | point_rules | Quy tắc tính điểm |
| 7 | transactions | Giao dịch tích điểm |
| 8 | point_ledger | Audit log biến động điểm (append-only) |
| 9 | rewards | Catalog quà tặng |
| 10 | redemptions | Lịch sử đổi điểm lấy quà |
| 11 | campaigns | Chiến dịch khuyến mãi |
| 12 | vouchers | Voucher cá nhân |
| 13 | notifications | Thông báo in-app |
| 14 | verification_codes | Mã xác thực cho claim shadow / reset password |

---

## Phụ lục — Các luồng nghiệp vụ chính

| Mã | Tên luồng | Mô tả ngắn |
|---|---|---|
| Luồng A | Đăng ký doanh nghiệp mới | Chủ shop đăng ký → Super Admin duyệt → cấu hình tier, point rule, rewards |
| Luồng B | Tạo thành viên qua SĐT (default cho khách mới) | Nhân viên nhập SĐT khách → backend upsert: tạo shadow user nếu chưa có, hoặc tạo membership mới nếu user đã tồn tại (do tenant khác). Áp dụng cho mọi khách chưa có membership ở tenant hiện tại. Khách "claim" tài khoản sau qua verification code 6 số |
| Luồng C | Tích điểm qua QR cá nhân | CHỈ áp dụng cho khách đã là thành viên tenant. Khách hiển thị QR (JWT server-signed exp 120s + fallback code), nhân viên quét. Nếu khách chưa là thành viên tenant → fall back về Luồng B (nhập SĐT) |
| Luồng D | Đổi điểm lấy quà | Khách chọn quà, hệ thống trừ điểm, sinh mã redemption, nhân viên xác nhận |
| Luồng E | Chiến dịch khuyến mãi (lazy claim) | Khách tự bấm nhận voucher từ campaign đủ điều kiện |
| Luồng F | Voucher sinh nhật (background job) | Job chạy 00:05 ICT mỗi ngày, tự động phát voucher cho khách có sinh nhật hôm nay |
| Luồng G | Tính lại hạng thành viên | Tự động upgrade hạng sau mỗi giao dịch, silent re-bind nếu chủ shop đổi cấu hình tier |
| Luồng H | Quản lý nhân viên | Chủ shop thêm/xóa/đổi role nhân viên, tự động revoke token |
| Luồng I | Hủy/Hoàn giao dịch | Dành cho luận văn (MVP cố ý không implement) |
| Luồng J | Reset mật khẩu | Dùng cùng pattern với verification code |
| Luồng K | Chỉnh tier có membership active | Recompute toàn bộ membership khi chủ shop sửa tier config |
| Luồng L | Khách tự join shop từ app | Khách đã có account → vào `/member/shops` browse → bấm "Tham gia [tên shop]" → backend tạo membership mới qua upsert. Bổ sung cho Luồng B (dành cho khách chưa có app) |

---

## Tiêu chí hoàn thành MVP (Acceptance Criteria)

Sau 8 tuần thực tập, sản phẩm phải đạt **tất cả** các tiêu chí sau:

1. **Demo end-to-end 1 kịch bản đầy đủ:** đăng ký tenant → Super Admin duyệt → cấu hình tier + point rule → nhân viên tạo giao dịch (3 cách: thủ công, QR shop, QR khách) → khách đổi quà nhận mã redemption → tạo campaign → khách claim voucher → dùng voucher → kích hoạt upgrade tier → nhận voucher sinh nhật.

2. **Multi-tenant isolation chứng minh được:** chạy 2 tenant song song, có test tự động đảm bảo dữ liệu không lẫn (`tests/integration/test_tenant_isolation.py` pass 100%).

3. **Point ledger reconcile khớp:** test invariant `SUM(point_ledger.delta) WHERE membership_id = X = memberships.points_balance` đúng với mọi membership trong seed data và sau mọi luồng test.

4. **Dashboard hiển thị 5 chỉ số:** số thành viên, giao dịch theo ngày, doanh thu, tỉ lệ đổi điểm, phân bố hạng. (ROI campaign là chỉ số nâng cao, ưu tiên thấp hơn.)

5. **PWA `/member` cài được trên Android Chrome thật:** mở offline vẫn xem được điểm và voucher đã có (dữ liệu cache).

6. **Có deploy demo chạy được:** Docker Compose local + ngrok ở mức tối thiểu, hoặc VPS nếu kịp.

7. **Báo cáo và slide demo:** file PDF báo cáo + 5–10 slide presentation cho buổi bảo vệ.

---

*Tài liệu này là phụ lục danh sách tính năng được trích từ design spec đầy đủ tại `docs/superpowers/specs/2026-04-12-loyalty-platform-design.md`*
