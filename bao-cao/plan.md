# Kế hoạch báo cáo luận văn — Loyalty Platform

**Đề tài (placeholder):** XÂY DỰNG HỆ THỐNG TÍCH ĐIỂM THÀNH VIÊN VÀ QUẢN LÝ KHUYẾN MẠI CHO DOANH NGHIỆP VỪA VÀ NHỎ

**Trường:** ĐH Công nghệ Sài Gòn — Khoa CNTT — Hệ Đại học (bìa xanh dương)

**Template gốc:** `C:\Users\Admin\Downloads\MAU_ThucTap_2025.docx`

---

## 1. Format (trích từ mẫu STU 2025)

| Mục | Quy định |
|---|---|
| Khổ giấy | A4 |
| Font nội dung | Times New Roman 13pt, line 1.3, paragraph spacing after 6pt |
| Tiêu đề cấp 1 (Chương) | 24pt, IN HOA, **bold**, canh phải, trang đầu chương KHÔNG header |
| Tiêu đề cấp 2 (1.1) | 15pt, IN HOA, **bold** |
| Tiêu đề cấp 3 (1.1.1) | 14pt, thường, **bold** |
| Tiêu đề cấp 4 (1.1.1.1) | 13pt, thường, <u>gạch dưới</u> |
| Tiêu đề mục lục | 18pt, IN HOA, **bold**, canh giữa |
| Header | Mỗi chương 1 header riêng "CHƯƠNG X: TÊN" IN HOA, *italic*, từ trang 2 trong chương |
| Footer | Chung cả quyển: tên đề tài IN HOA *italic* + số trang canh phải, chỉ từ nội dung LVTN |
| Hình ảnh | Canh giữa, In Line with Text; caption "Hình X-Y: …" (**bold italic** phần số, <u>gạch dưới</u>) |
| Tối thiểu | 60 trang (mẫu quy định) |

## 2. Thứ tự đóng quyển

1. Bìa cứng màu xanh dương
2. Giấy trắng
3. Tờ nhiệm vụ (GVHD ký)
4. Lời cảm ơn
5. Mục lục nội dung
6. Mục lục hình ảnh
7. Nội dung 5 chương
8. Phụ lục (HDSD 1 luồng — chọn **Campaign → Voucher**)
9. Tài liệu tham khảo
10. Giấy trắng
11. Bìa sau cùng màu

## 3. Outline nội dung

### Chương 1 — Giới thiệu

- **1.1. Đặt vấn đề, mục tiêu luận văn**
  - Bối cảnh: SME Việt Nam thiếu hạ tầng loyalty riêng, giải pháp có sẵn (Got It, Urbox, Loyverse) chi phí cao / không tuỳ biến / không hỗ trợ pháp lý khuyến mại VN
  - Vấn đề cụ thể: quản lý khách hàng đa cửa hàng, chương trình khuyến mãi theo Nghị định 81/2018/NĐ-CP (ngưỡng 500k/2M bắt buộc nộp hồ sơ Sở Công Thương)
  - Mục tiêu: xây hệ thống multi-tenant cho phép doanh nghiệp tự vận hành tích điểm + công ty vận hành thay cho phần pháp lý (managed service)
- **1.2. Thách thức cần giải quyết**
  - Multi-tenant scoping qua `X-Tenant-Id` + phân quyền 4 role (super admin / owner / staff / customer)
  - TOCTOU khi claim voucher concurrent — 3 lớp phòng thủ: `pg_advisory_xact_lock(hashtext('claim:' || campaign_id))` + atomic UPDATE `issued_count` với quota guard + partial unique index `(member_id, campaign_id) WHERE status != 'cancelled'`
  - Tuân thủ pháp lý NĐ 81/2018/NĐ-CP: `approval_tier` (none / notify_so_ct / dang_ky_so_ct / full_dossier), ngưỡng 500k (auto) / 2M (notify)
  - Nghĩa vụ hậu KM: nộp báo cáo kết thúc trong 45 ngày (NĐ 81 Điều 20) — cron `check_post_report_overdue` auto cảnh báo
  - Luật Kế toán 2015 Điều 41: lưu hồ sơ uỷ quyền + phí 10 năm (`auth_retention_years=10`)
  - VAT 10% trên phí dịch vụ (Luật Thuế GTGT) — đã mô hình hoá ở `campaign_service_fee` mặc dù `SERVICE_FEE_ENABLED=False` ở đồ án
  - PWA offline-ready (Serwist) cho khách hàng
  - Uỷ quyền giữa doanh nghiệp và công ty vận hành (`tenant_authorization` + OTP `authorization_sign` + `context_hash` bind form)
  - QR HMAC secret tách rời JWT secret trong production (`QR_HMAC_SECRET`)
- **1.3. Nội dung, phạm vi thực hiện**
  - In-scope: backend FastAPI, frontend Next.js 14 (4 app shell), PostgreSQL schema, CI/CD docker compose, deploy Cloudflare Tunnel
  - Out-of-scope đồ án: thu phí thật (`SERVICE_FEE_ENABLED=False`), tích hợp ngân hàng, app native
  - Mở rộng khoá luận: fee collection, voucher NFT, ML tier recommendation
- **1.4. Kết quả cần đạt (bảng)**
  - Bảng 11 mục tiêu × tiêu chí đo lường: X mô-đun BE, Y endpoint, Z màn hình FE, test coverage, demo luồng E2E

### Chương 2 — Phương pháp thực hiện

- **2.1. Khảo sát hệ thống tương tự**
  - Got It Vietnam (voucher marketplace, không loyalty), Urbox (ví điểm B2B), Loyverse POS (loyalty kèm POS, không multi-tenant thật), Smile.io (SaaS Shopify, không hỗ trợ pháp lý VN)
  - Bảng so sánh feature × nền tảng
- **2.2. Công nghệ sử dụng**
  - Backend: FastAPI + SQLAlchemy 2.0 async + asyncpg + Pydantic v2 + slowapi (rate limit) + APScheduler + python-jose (JWT) + bcrypt
  - Frontend: Next.js 14 App Router + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query + Zustand + react-hook-form + zod + Serwist PWA + qrcode.react
  - DB: PostgreSQL 15 — partial unique index, trigger `voucher_validate_max_issuances`, view `v_campaign_stats`, advisory lock
  - Test: pytest + httpx + testcontainers-postgres + Playwright E2E
  - Infra: Docker Compose (dev + prod), Alembic 28 migrations, Cloudflare Tunnel → `loyalty.ecom-bill.com`
- **2.3. Phương pháp luận**
  - Kiến trúc layered thin-route / fat-service
  - Multi-tenant qua `X-Tenant-Id` header + dependency injection
  - TDD: unit + integration với testcontainers
  - Git flow + code review tự động
- **2.4. Phân tích nghiệp vụ**
  - **2.4.1 Các quy trình nghiệp vụ chính** (11 luồng):
    - Đăng ký merchant → duyệt → kích hoạt
    - POS tích điểm (earn) qua scan QR khách
    - Đổi quà (redemption)
    - Tạo chiến dịch → compute `approval_tier` theo cost → nộp hồ sơ Sở CT → duyệt → claim voucher
    - Uỷ quyền công ty vận hành (`tenant_authorization` + OTP `authorization_sign`)
    - Thăng hạng tự động theo `min_points` (trigger khi sửa cấu hình tier)
    - Cron `birthday_voucher_job` phát voucher sinh nhật
    - Cron `check_post_report_overdue` cảnh báo 45 ngày (NĐ 81 Điều 20)
    - Cron `expire_vouchers` đánh dấu voucher hết hạn
    - Cron `cleanup_codes` xoá OTP cũ
    - Cron `purge_retention` tôn trọng retention 10 năm uỷ quyền
  - **2.4.2 Sơ đồ chức năng** (functional decomposition tree)
  - **2.4.3 Use case tổng quát** + mô tả 5 Actor

### Chương 3 — Thiết kế

- **3.1. Mô hình dữ liệu (3 mức)**
  - Mức ý niệm: ERD 10 entity chính (User, Tenant, Membership, Tier, Transaction, PointLedger, Reward, Redemption, Campaign, Voucher) + 13 entity phụ trợ (VerificationCode, Notification, PointRule, TenantStaff, TenantSettingsAudit, TenantAuthorization, CampaignTemplate, CampaignApprovalEvent, CampaignRegulatorySubmission, CampaignIssuance, CampaignServiceFee, CampaignFeeSchedule + các enum helper)
  - Mức luận lý: chuyển thành relational schema với PK/FK/unique
  - Mức vật lý: DDL thật từ 28 migration Alembic (23 bảng), các partial unique index quan trọng (voucher claim dedupe exclude `cancelled`, campaign_service_fees, campaign_issuances), trigger `voucher_validate_max_issuances`, check constraint `approval_tier`, view `v_campaign_stats`
- **3.2. Mô hình xử lý**
  - **3.2.1 Use case chi tiết**: 8 use case quan trọng (kèm bảng mô tả Actor/Precondition/Main flow/Alt flow/Postcondition)
    - UC-01 Đăng ký merchant
    - UC-02 POS ghi giao dịch
    - UC-03 Đổi quà
    - UC-04 Tạo chiến dịch
    - UC-05 Duyệt chiến dịch (admin)
    - UC-06 Claim voucher
    - UC-07 Uỷ quyền OTP
    - UC-08 Thăng hạng
  - **3.2.2 Sơ đồ tuần tự** (sequence diagram) cho 4 luồng core: Login JWT, POS earn, Claim voucher concurrent, Campaign approval
  - **3.2.3 Sơ đồ hoạt động** (activity) cho 3 luồng: Campaign lifecycle, Redemption, Birthday cron
- **3.3. Hệ thống màn hình**
  - Tổng 5 app shell (admin / auth / member / merchant / staff) × 32 page.tsx: 8 member + 12 merchant + 10 admin + 2 staff (+ auth shell cho login/register/register-merchant)
  - Screenshot 12-16 màn hình chính (đã có sẵn trong repo: member-*.png, merchant-*.png, admin-*.png, landing-*.png)
  - Bảng liệt kê toàn bộ trang theo role
- **3.4. Hệ thống báo biểu**
  - Analytics dashboard (v_campaign_stats view)
  - Audit log (tenant_settings_audit)
  - Export CSV giao dịch

### Chương 4 — Thử nghiệm

- **4.1. Kịch bản thử nghiệm** (30+ scenario)
  - Auth (register, login, refresh, JWT expiry, rate limit)
  - Tenant (create, slug collision, approve, suspend)
  - POS (earn, refund, duplicate bill guard)
  - Redemption (happy path, stock hết, điểm không đủ)
  - Campaign (create, submit regulatory, approve, reject)
  - Voucher (claim happy, claim hết suất, claim 2 lần)
  - Cron (birthday voucher)
- **4.2. Kết quả thử nghiệm**
  - pytest output (unit + integration)
  - Playwright smoke E2E (từ Phase 15/16)
  - Performance: rate limit + P95 latency trên docker local
- **4.3. Xử lý ngoại lệ**
  - Concurrent claim voucher (TOCTOU) — 3 lớp: `pg_advisory_xact_lock` + atomic UPDATE quota guard + partial unique index exclude `cancelled`
  - Duplicate transaction bill — unique (tenant_id, pos_bill_id)
  - OTP hết hạn / đã dùng — `verification_code.expires_at` + `used_at`; anti-abuse ở tầng slowapi rate limiter (không có `attempt_count` ở model)
  - OTP `authorization_sign` bind context_hash chặn tamper form
  - Unique constraint phone/email/slug — global IntegrityError handler `app/main.py` map 409 + message VN
  - `SERVICE_FEE_ENABLED=False` — service skip tạo fee rows, UI ẩn tab phí

### Chương 5 — Kết luận

- **5.1. Đối chiếu kết quả vs mục tiêu (1.4)** — bảng đạt/chưa đạt
- **5.2. Vấn đề còn tồn đọng**
  - `Campaign.discount_type` / `Voucher.status` khai báo `Mapped[Enum]` nhưng lưu `String(20)` — caller phải xử lý cả str lẫn Enum (task #183)
  - Rate limit keyed bằng `X-Forwarded-For` — phụ thuộc reverse proxy (Cloudflare Tunnel)
  - Chưa có real payment integration (`SERVICE_FEE_ENABLED=False` scope đồ án)
  - Chưa có OTP attempt counter ở DB — tất cả phụ thuộc slowapi
  - Frontend chưa optimize bundle size, staff shell chỉ 2 trang (có thể gộp vào merchant)
- **5.3. Mở rộng** (hướng phát triển)
  - Mở SERVICE_FEE_ENABLED → thu phí thật, tích hợp bank API
  - App mobile native (React Native / Flutter)
  - Voucher NFT onchain
  - ML tier recommendation + churn prediction

### Phụ lục — HDSD luồng Campaign → Voucher

HDSD từng bước cho 1 quy trình đầy đủ:
1. Owner đăng nhập
2. Tạo campaign (loại %, điều kiện, thời gian, max_issuances)
3. Chọn template pháp lý (auto compute `approval_tier`)
4. Nộp hồ sơ Sở Công Thương (nếu tier ≥ notify_so_ct)
5. Công ty vận hành duyệt (hoặc Sở CT duyệt)
6. Campaign active
7. Khách hàng claim voucher qua PWA
8. Staff verify voucher tại POS, mark used
9. Owner xem thống kê claim/redeem

Mỗi bước 1-2 screenshot + mô tả ngắn.

## 4. Phương pháp sản xuất file .docx

**Phương án chọn:** Script Python dùng `python-docx` (đã cài, v1.2.0)

- `bao-cao/build_docx.py` — script build
- `bao-cao/content/` — thư mục chứa nội dung từng chương dạng Python module hoặc markdown
- `bao-cao/assets/` — hình ảnh screenshot + diagram
- Output: `bao-cao/bao-cao-final.docx`

Lý do:
- Pandoc không cài sẵn
- python-docx cho phép control cực chi tiết: styles từng cấp, header/footer per section, caption hình, bìa màu, mục lục tự động
- Reproducible: chỉnh nội dung → rebuild

## 5. Sơ đồ diagram (user confirmed: Mermaid)

Dùng Mermaid CLI (`@mermaid-js/mermaid-cli` / `mmdc`) render → PNG rồi chèn vào docx qua python-docx `add_picture`. Các diagram cần:
- ERD 9 entity chính + 13 phụ trợ
- Sơ đồ chức năng (functional decomposition)
- Use case diagram tổng quát (5 Actor: Super Admin, Owner, Staff, Customer, System/Cron)
- 4 sequence diagram: Login JWT, POS earn, Claim voucher concurrent, Campaign approval
- 3 activity diagram: Campaign lifecycle, Redemption, Birthday cron
- Sơ đồ kiến trúc hệ thống (C4 context + container)

**Pipeline:** `bao-cao/diagrams/*.mmd` → `mmdc -i file.mmd -o file.png -t default -b transparent` → `bao-cao/assets/*.png` → chèn docx.

**Kiểm tra mmdc:** nếu chưa cài, `npm i -g @mermaid-js/mermaid-cli` (global).

## 6. Thứ tự execute

1. ✅ Plan (file này)
2. Build `build_docx.py` với styles + bìa + header/footer (test với nội dung giả)
3. Viết Chương 1 (text thuần)
4. Viết Chương 2 (text + use case diagram + bảng công nghệ)
5. Viết Chương 3 (text + ERD + sequence + activity + screenshot hệ thống màn hình)
6. Viết Chương 4 (text + bảng kết quả test + log output)
7. Viết Chương 5 + Phụ lục
8. Compile final docx
9. Review cuối + điền thông tin bìa (tên, MSSV, GVHD)

## 7. Ước lượng trang (user-defined: 30-50 trang, đủ nội dung thì dừng)

| Chương | Ước lượng trang |
|---|---|
| Lời cảm ơn | 1 |
| Mục lục nội dung | 2 |
| Mục lục hình ảnh | 1 |
| Chương 1 | 4-5 |
| Chương 2 | 6-8 |
| Chương 3 | 12-18 (nặng nhất: ERD + sequence + activity + screenshot) |
| Chương 4 | 4-6 |
| Chương 5 | 2-3 |
| Phụ lục HDSD | 4-6 |
| TLTK | 1 |
| **Tổng** | **~37-51 trang** |

Lưu ý: mẫu STU quy định tối thiểu 60 trang, nhưng user chấp nhận dừng ở 30-50 khi nội dung đủ. Nếu GVHD yêu cầu đủ 60, có thể bổ sung: khảo sát chi tiết hơn các hệ thống tương tự, phân tích sâu pháp lý NĐ 81, screenshot đầy đủ hơn.

## 8. Bìa (điền sau)

- [ ] Tên đề tài chính thức
- [ ] Họ tên sinh viên
- [ ] MSSV
- [ ] Họ tên GVHD
- [ ] Năm học
