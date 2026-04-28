# Kế hoạch báo cáo đồ án thực tập — Loyalty Platform (MVP)

**Đề tài chính thức:** XÂY DỰNG WEBSITE TÍCH ĐIỂM THÀNH VIÊN CHO DOANH NGHIỆP VỪA VÀ NHỎ

**Trường:** ĐH Công nghệ Sài Gòn — Khoa CNTT

**Sinh viên:** Nguyễn Hải Đăng — MSSV: `[ĐIỀN MSSV]`
**GVHD:** `[ĐIỀN GVHD]`
**Năm học:** 2025-2026

**Output:** `bao-cao/bao-cao-mvp.docx`

> **Lưu ý:** Bản plan này thay thế phiên bản cũ (đề tài có "quản lý khuyến mại"). Scope đã pivot sang MVP gọn — bỏ tier, campaign, voucher claim với pháp lý NĐ 81, service fee, PWA. Các phần đó được bảo lưu cho luận văn tốt nghiệp.

---

## 1. Format (trích mẫu STU 2025)

| Mục | Quy định |
|---|---|
| Khổ giấy | A4 |
| Font | Times New Roman 13pt, line 1.3, paragraph spacing after 6pt |
| H1 (Chương) | 24pt IN HOA bold, canh phải, trang đầu chương KHÔNG header |
| H2 (1.1) | 15pt IN HOA bold |
| H3 (1.1.1) | 14pt thường bold |
| H4 (1.1.1.1) | 13pt thường, gạch dưới |
| Header | "CHƯƠNG X: TÊN" IN HOA italic, từ trang 2 trong chương |
| Footer | Tên đề tài IN HOA italic + số trang canh phải |
| Hình | Canh giữa, caption "Hình X-Y: …" bold italic underline phần số |

## 2. Thứ tự đóng quyển

1. Bìa cứng xanh dương
2. Lời cảm ơn
3. Mục lục nội dung
4. Mục lục hình ảnh
5. Nội dung 5 chương
6. Phụ lục (HDSD luồng "Đăng ký → Đổi quà từ đối tác")
7. Tài liệu tham khảo

## 3. Outline nội dung

### Chương 1 — Giới thiệu (4-5 trang)

- **1.1. Đặt vấn đề, mục tiêu**
  - 1.1.1. Bối cảnh thị trường SME & loyalty Việt Nam
  - 1.1.2. Mục tiêu cụ thể của đề tài
- **1.2. Thách thức cần giải quyết**
  - 1.2.1. Cô lập dữ liệu đa tenant qua header `X-Partner-Id`
  - 1.2.2. Ví điểm toàn cục cross-shop với CHECK constraint không âm
  - 1.2.3. Append-only ledger (audit + chống mất lịch sử)
  - 1.2.4. Bảo mật JWT + bcrypt + rate limiting
  - 1.2.5. Cân bằng UX cho 4 vai trò (member/owner/staff/admin)
- **1.3. Phạm vi**
  - 1.3.1. In-scope: 5 module End-user + 5 module Đối tác + 3 module Admin
  - 1.3.2. Out-of-scope (bảo lưu cho luận văn): tier, campaign, voucher claim, NĐ 81, PWA, service fee
  - 1.3.3. Hướng phát triển mở rộng
- **1.4. Kết quả cần đạt** — bảng 8-10 mục tiêu × tiêu chí

### Chương 2 — Phương pháp thực hiện (5-7 trang)

- **2.1. Khảo sát hệ thống tương tự**
  - Smile.io / LoyaltyLion (SaaS quốc tế)
  - Got It / Urbox (voucher marketplace)
  - Loyverse (POS có loyalty, không multi-tenant)
  - Bảng so sánh
- **2.2. Công nghệ sử dụng**
  - Backend: FastAPI + SQLAlchemy 2.0 async + Pydantic v2 + Alembic + slowapi + python-jose + bcrypt + aiosmtplib
  - Frontend: Next.js 14 App Router + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query + Zustand
  - DB: PostgreSQL 15
  - Infra: Docker Compose + Cloudflare Tunnel
- **2.3. Phương pháp luận**
  - Layered architecture: thin-route / fat-service
  - Multi-tenant qua header + DI 4 role
  - Append-only ledger pattern (DB trigger)
  - TDD + smoke E2E (note: pytest infra gap trên Windows)
  - Git flow + code review tự động
- **2.4. Phân tích nghiệp vụ**
  - 2.4.1. 8 quy trình nghiệp vụ chính
  - 2.4.2. Sơ đồ chức năng
  - 2.4.3. Use case tổng quát + 4 actor

### Chương 3 — Thiết kế (10-15 trang — nặng nhất)

- **3.1. Mô hình dữ liệu (3 mức)**
  - Mức ý niệm: ERD ~11 entity (User, Partner, PartnerStaff, Membership, Reward, Redemption, Transaction, PointLedger, PointAdjustment, Notification, VerificationCode)
  - Mức luận lý: relational schema PK/FK/unique
  - Mức vật lý: DDL, CHECK `points_balance >= 0`, partial unique index, trigger `prevent_point_ledger_mutation`
- **3.2. Mô hình xử lý**
  - 3.2.1. 5 Use case chi tiết: UC-01 Login, UC-02 Đăng ký merchant, UC-03 POS tích điểm, UC-04 Đổi quà, UC-05 Quản lý điểm hệ thống
  - 3.2.2. Sequence diagram: Login JWT, POS tích điểm, Đổi quà
  - 3.2.3. Activity diagram: Đăng ký merchant, Quên mật khẩu
- **3.3. Hệ thống màn hình**
  - 5 app shell × danh sách page
  - Screenshot 8-12 màn chính
  - Bảng tổng hợp page theo role
- **3.4. Hệ thống báo biểu**
  - Dashboard analytics (KPI 6 cột + chart doanh thu + chart redemption + Top 5 quà)
  - Log đăng nhập
  - Log điều chỉnh điểm
  - Tổng điểm hệ thống

### Chương 4 — Thử nghiệm (4-6 trang)

- **4.1. Kịch bản thử nghiệm** (~25 scenario)
  - Auth, Partner, Member, POS, Reward CRUD, Admin
- **4.2. Kết quả thử nghiệm**
  - Smoke E2E qua curl + Playwright (note: pytest infra gap docker-exec Windows)
  - Bảng pass/fail
  - Performance: rate limit slowapi + P95 latency demo
- **4.3. Xử lý ngoại lệ**
  - `points_balance >= 0` enforce 3 layer (Pydantic / service / DB CHECK)
  - Append-only ledger (trigger block UPDATE/DELETE)
  - Reward `offer_type` immutable (schema reject 422)
  - Email SMTP fail-silent
  - Unique phone/email — IntegrityError handler 409 + message VN

### Chương 5 — Kết luận (2-3 trang)

- **5.1. Đối chiếu kết quả vs mục tiêu** — bảng đạt/chưa đạt
- **5.2. Vấn đề còn tồn đọng**
  - pytest infra gap trên Windows
  - FE chưa optimize bundle size
  - Chưa có 2FA cho admin
  - Audit log chưa phủ mọi action
- **5.3. Mở rộng (luận văn tốt nghiệp)**
  - Campaign + voucher hệ thống có pháp lý NĐ 81
  - Tier hạng thành viên
  - Service fee thật + cổng thanh toán
  - PWA offline-ready
  - Mobile native + ML

### Phụ lục — HDSD "Đăng ký → Đổi quà từ đối tác" (3-5 trang)

1. Khách hàng đăng ký tài khoản
2. Đăng nhập vào /member
3. Mở danh sách đối tác → chọn 1 đối tác
4. Xem chi tiết đối tác + danh sách quà
5. Bấm "Đổi quà"
6. Hệ thống trừ điểm + ghi ledger + tạo redemption
7. Voucher xuất hiện ở /member/vouchers
8. Mang voucher + QR cá nhân ra POS
9. Staff scan QR → verify reward → mark used

### TLTK (~1 trang) — ~10 nguồn

## 4. Mục tiêu trang

| Phần | Trang |
|---|---|
| Lời cảm ơn | 1 |
| Mục lục | 2-3 |
| Chương 1 | 4-5 |
| Chương 2 | 5-7 |
| Chương 3 | 10-15 |
| Chương 4 | 4-6 |
| Chương 5 | 2-3 |
| Phụ lục | 3-5 |
| TLTK | 1 |
| **Tổng** | **32-46 trang** |

## 5. Bìa (cần điền)

- [x] Tên đề tài: "XÂY DỰNG WEBSITE TÍCH ĐIỂM THÀNH VIÊN CHO DOANH NGHIỆP VỪA VÀ NHỎ"
- [x] Sinh viên: Nguyễn Hải Đăng
- [ ] MSSV
- [ ] GVHD
- [x] Năm học: 2025-2026
