# Partner rename + Discovery UX

**Ngày:** 2026-04-24
**Trạng thái:** Draft — chờ review
**Loại:** Refactor rộng + UX tinh chỉnh. Không tính năng mới ngoài 1 trang partner detail cho end-user.
**Scope:** 1 spec gộp — rename toàn cục `Tenant`+`Merchant` → `Partner`, đồng thời dẹp UX "join partner" không dùng.
**Migration style:** M1 **one-shot clean-break**. Không dual-name, không backwards compat, không alias.

---

## 1. Bối cảnh & động cơ

### 1.1. User pain (trích nguyên văn)

> "cơ chế đối tác chưa được tốt. Chức năng chính của người dùng cuối (End-user) Đối tác — Xem danh sách đối tác, đăng ký tham gia thành viên thực ra chỉ cần xem danh sách đối tác và thông tin đối tác, lịch sử tích điểm ở đối tác đó thôi. vì khi tạo account trên hệ thống thì toàn bộ các đối tác đều có thể tích điểm, không cần đăng ký riêng từng đối tác nữa"

> "dùng từ Partners cho tôi, vì đang là dự án nên có thể đổi tên toàn bộ. … Hiển thị là Đối tác"

### 1.2. Hai root cause

**R1 — Dead UX "join partner":**
Trang `/member/shops` có nút **"Tham gia"** và pill **"Đã là thành viên / Chưa tham gia"**, hàm ý end-user phải đăng ký riêng từng đối tác trước khi tích điểm. Thực tế:

- Không có API backend `POST /users/me/memberships` (không có endpoint join).
- `MemberService.find_or_create_member()` (xem `backend/app/services/member_service.py`) tự động tạo `Membership` **lần đầu** user giao dịch POS tại đối tác đó (lazy membership creation qua SAVEPOINT atomic upsert).
- Do đó nút "Tham gia" trên UI là no-op (disabled về mặt logic, không gọi API nào) → user bối rối, UX mismatch mental model.

**R2 — Thuật ngữ lộn xộn 3 lớp:**

| Lớp | Từ đang dùng | Vấn đề |
|---|---|---|
| Backend kỹ thuật | `Tenant`, `tenants`, `tenant_id`, `X-Tenant-Id` | Nhấn mạnh đặc tính multi-tenant SaaS, không phản ánh domain (đây là SME/shop chứ không phải "tenant" kiểu cloud platform). |
| Backend vai trò | `Merchant`, `/merchant`, `(merchant)` | Trùng khái niệm với `Tenant` — 2 tên cho 1 thực thể. Một số route là `/merchant/*` (owner dashboard), một số là `/tenants/*` (CRUD public), lẫn lộn. |
| UI hiển thị | "Cửa hàng", "Shop", "Đối tác", "Merchant" | Inconsistent. Báo cáo STU đã dùng "đối tác" nhưng UI + code chưa theo. |

Hệ quả:
- Developer mới vào dự án phải học ngay 3 tên cho cùng 1 thứ.
- Grader/reviewer báo cáo STU thấy báo cáo và code không khớp thuật ngữ.
- Copy UI cho end-user không thống nhất (thấy "Cửa hàng" trên 1 trang, "Merchant" trên trang khác).

### 1.3. Tại sao fix bây giờ + one-shot

- Đang là **đồ án thực tập** → chưa có user production ngoài demo → cost đổi tên gần như 0.
- GitNexus index hiện tại: 3152 occurrences của `Tenant`/`tenant` trên 183 file, 757 occurrences của `merchant` trên ~92 file. Chưa có `partner` nào (verified via Glob `(partner)/` = 0 file) → zero conflict.
- Một lần đau bằng 10 lần nhức. Dual-name (Tenant + Partner cùng tồn tại) tạo debt vĩnh viễn; clean-break xong trong 1 cutover sạch.
- User explicit approve: "đang là dự án nên có thể đổi tên toàn bộ" và "oke" sau khi present 12-section outline + M1 recommendation.

---

## 2. Goals / Non-goals

### 2.1. Goals

1. **Xoá toàn bộ UX "join partner"** trên customer app (`/member/*`): không còn nút tham gia, không còn pill "Đã là thành viên / Chưa tham gia", không còn stats "Đang là thành viên / Tổng shop".
2. **Thêm 1 trang partner detail** `/member/partners/[slug]` hiển thị: thông tin đối tác (name, category, description, address, contact, business hours) + lịch sử tích/tiêu điểm của user **chỉ tại đối tác đó**.
3. **Thống nhất thuật ngữ backend** về `Partner`:
   - Không dùng `Tenant` ở bất kỳ đâu trong code mới.
   - Không dùng `Merchant` như tên role — vai trò "chủ đối tác" dùng `PartnerOwner` / `PartnerStaff`.
4. **Thống nhất thuật ngữ frontend** về `Partner` (tên kỹ thuật) / `"Đối tác"` (tên hiển thị tiếng Việt).
5. **Clean-break migration:** 1 Alembic revision đổi tên bảng + FK + index + sequence trong 1 deploy; không có cờ compat, không có alias route.
6. **Zero behavior change** cho luồng tích/đổi điểm, voucher, campaign. Lazy membership creation qua POS giữ nguyên.

### 2.2. Non-goals (explicit để tránh scope creep)

- ❌ Không redesign cơ chế point earning / redemption / tier progression.
- ❌ Không build "partner onboarding" cho end-user (vì theo design mới, user không cần onboard vào từng partner).
- ❌ Không touch campaign/voucher logic beyond rename field + route.
- ❌ Không tách `seed_demo.py` thành seed riêng partner — cứ seed như cũ với tên mới.
- ❌ Không refactor thiết kế multi-tenant isolation — chỉ rename, logic isolation giữ nguyên qua header + deps.
- ❌ Không đụng `super_admin` role / admin portal ngoài rename references.
- ❌ Không viết lại báo cáo STU từ đầu — chỉ patch các chỗ dùng "tenant"/"merchant" trong `bao-cao/content/*.py`.

---

## 3. Glossary — mapping từ cũ sang mới

Glossary này là **nguồn sự thật duy nhất** cho implementation plan + code review. Mọi từ bên cột "Cũ" phải bị thay khi merge. Mọi từ bên cột "Mới" phải là duy nhất trong codebase sau merge.

### 3.1. Python / Backend

| Cũ | Mới | Loại |
|---|---|---|
| `Tenant` | `Partner` | Class |
| `TenantStatus` (enum PENDING/ACTIVE/SUSPENDED) | `PartnerStatus` | Enum |
| `TenantCategory` (enum cafe/food/retail/beauty/other) | `PartnerCategory` | Enum |
| `TenantStaff` | `PartnerStaff` | Class |
| `TenantStaffRole` (enum OWNER/MANAGER/STAFF) | `PartnerStaffRole` | Enum |
| `TenantAuthorization` | `PartnerAuthorization` | Class |
| `TenantSettingsAudit` | `PartnerSettingsAudit` | Class |
| `TenantService` | `PartnerService` | Service class |
| `TenantNotFoundError` | `PartnerNotFoundError` | Domain exception |
| `tenant_id` (column/param) | `partner_id` | Column + param |
| `tenant_role_cache` | `partner_role_cache` | Cache singleton ở `app/core/tenant_cache.py` (không phải `deps.py`); `deps.py` chỉ import |
| `TenantRoleCache` | `PartnerRoleCache` | Class định nghĩa trong `tenant_cache.py` |
| `tenant_cache.py` | `partner_cache.py` | File rename |
| `tenants` (table name) | `partners` | DB table |
| `tenant_staff` (table) | `partner_staff` | DB table |
| `tenant_authorizations` (table) | `partner_authorizations` | DB table |
| `tenant_settings_audit` (table) | `partner_settings_audit` | DB table |
| `get_tenant_id` | `get_partner_id` | FastAPI dep |
| `get_verified_tenant_id` | `get_verified_partner_id` | FastAPI dep |
| `get_current_tenant_role` | `get_current_partner_role` | FastAPI dep |
| `require_staff_in_tenant` | `require_staff_in_partner` | FastAPI dep |
| `require_owner_in_tenant` | `require_owner_in_partner` | FastAPI dep |
| `require_customer_in_tenant` | `require_customer_in_partner` | FastAPI dep |
| `extract_tenant_id_from_header` | `extract_partner_id_from_header` | Helper |
| `merchant_router` | `partner_router` | APIRouter |
| `tenants_router` | `partners_router` | APIRouter |
| `X-Tenant-Id` | `X-Partner-Id` | HTTP header |
| `/merchant/*` | `/partner/*` | URL prefix (owner/staff) |
| `/tenants/*` | `/partners/*` | URL prefix (public + admin) |
| `/users/me/shops` | `/users/me/partners` | URL (customer view) |

### 3.2. TypeScript / Frontend

| Cũ | Mới | Loại |
|---|---|---|
| `useTenantStore` | `usePartnerStore` | Zustand hook |
| `getActiveTenantId()` | `getActivePartnerId()` | Helper |
| `tenant-store.ts` | `partner-store.ts` | File |
| `api-merchant.ts` | `api-partner.ts` | File (axios group client) |
| `(merchant)` | `(partner)` | Next.js route group folder |
| `/merchant/*` | `/partner/*` | URL (tất cả owner dashboard pages) |
| `/member/shops` | `/member/partners` | URL (customer) |
| storage key `"active_tenant"` | `"active_partner"` | localStorage key |
| interface/type `Tenant`, `TenantItem`, `TenantStaffRole` | `Partner`, `PartnerItem`, `PartnerStaffRole` | TS types |
| `useMerchant*` hooks | `usePartner*` hooks | TanStack Query hooks |

### 3.3. UI copy tiếng Việt

| Copy cũ | Copy mới | Ghi chú |
|---|---|---|
| "Cửa hàng" / "Shop" | "Đối tác" | Chuẩn hoá 100% |
| "Cửa hàng của tôi" (dashboard member) | "Đối tác của tôi" | |
| "Shop đối tác" | "Đối tác" | Không double |
| "Đăng ký tham gia đối tác" | **XOÁ** | Luồng không tồn tại |
| "Đã là thành viên" / "Đã tham gia" | **XOÁ pill** | Không còn khái niệm join |
| "Chưa tham gia" | **XOÁ pill** | |
| "Đang là thành viên X / Tổng shop Y" (stats header `/member/shops`) | **XOÁ section** hoặc thay "X đối tác" đơn giản | |
| "Tham gia" (button) | **XOÁ button** | |
| "Chủ shop" / "Merchant" | "Chủ đối tác" | Dùng khi UI muốn emphasize role |
| "Đăng ký doanh nghiệp" (đăng ký partner mới trên `/register/merchant`) | "Đăng ký đối tác" + URL đổi sang `/register/partner` | Luồng đăng ký B2B giữ nguyên logic |

### 3.4. Không đụng tới

- `Member`, `Membership`, `User`, `TierName`, `Campaign`, `Voucher`, `Transaction`, `Reward`, `Redemption`, `PointLedger`, `PointRule`, `Notification`, `VerificationCode` — giữ nguyên. Chỉ field `tenant_id` trong các bảng này đổi thành `partner_id`.
- `super_admin` system role, `/admin/*` route — giữ nguyên. `/admin/tenants` sẽ đổi prefix thành `/admin/partners` nhưng concept role không đổi.

---

## 4. Data model changes

### 4.1. Bảng đổi tên (`ALTER TABLE ... RENAME TO`)

| Cũ | Mới |
|---|---|
| `tenants` | `partners` |
| `tenant_staff` | `partner_staff` |
| `tenant_authorizations` | `partner_authorizations` |
| `tenant_settings_audit` | `partner_settings_audit` |

### 4.2. Cột FK đổi tên (`ALTER TABLE <t> RENAME COLUMN tenant_id TO partner_id`)

15 bảng sở hữu cột `tenant_id` (verified bằng grep `tenant_id` trong `backend/app/models/`):

1. `memberships`
2. `transactions`
3. `point_ledger` (table name singular)
4. `point_rules`
5. `tiers`
6. `rewards`
7. `redemptions`
8. `vouchers`
9. `campaigns`
10. `campaign_issuances`
11. `campaign_service_fees`
12. `notifications`
13. `partner_staff` (đã rename từ `tenant_staff`)
14. `partner_authorizations` (đã rename)
15. `partner_settings_audit` (đã rename)

**Bảng KHÔNG có `tenant_id` (nên không rename column) — chỉ để rõ ràng tránh nghi bỏ sót:**
- `campaign_approval_events`, `campaign_regulatory_submissions`, `campaign_fee_schedules`, `campaign_templates` — FK xuống `campaigns.id`, tenant-scope gián tiếp qua parent campaign.
- `users`, `verification_codes` — scope theo user, không theo partner.

### 4.3. Index / Constraint / Sequence đổi tên

Alembic không tự rename khi `RENAME TABLE`, nên cần rename thủ công:

- **Sequence:** `tenants_id_seq` → `partners_id_seq`, tương tự cho 3 bảng còn lại.
- **Primary key:** `tenants_pkey` → `partners_pkey`.
- **Unique constraints:** VD `uq_memberships_tenant_user` → `uq_memberships_partner_user`, tìm hết bằng `SELECT conname FROM pg_constraint WHERE conname LIKE '%tenant%'` tại thời điểm migration.
- **Indexes:** VD `ix_memberships_tenant_id` → `ix_memberships_partner_id`. Convention naming: `ix_<table>_<column>`.
- **Foreign key constraints:** VD `fk_memberships_tenant_id_tenants` → `fk_memberships_partner_id_partners`.

**Strategy:** Alembic migration chủ động issue `ALTER INDEX ... RENAME TO` + `ALTER TABLE ... RENAME CONSTRAINT ... TO` cho từng object. Không dựa vào autogenerate vì autogenerate không hiểu rename vs drop+recreate.

**Discovery query** (chạy trên dev DB để enumerate list cần rename — phải cover cả 2 nguồn vì **partial index** như voucher-uniqueness không phải constraint):
```sql
SELECT indexname FROM pg_indexes WHERE indexname LIKE '%tenant%';
SELECT conname  FROM pg_constraint WHERE conname LIKE '%tenant%';
-- Bắt cả 2 naming style: custom SA convention (fk_<t>_<col>_<reft>)
-- lẫn PG default (<t>_<col>_fkey).
```

### 4.4. Enum values

Không đụng values. Chỉ đổi **tên class Python**:
- `TenantStatus` → `PartnerStatus`: values vẫn là `"pending"`, `"active"`, `"suspended"`.
- `TenantCategory` → `PartnerCategory`: values vẫn `"cafe"`, `"food"`, `"retail"`, `"beauty"`, `"other"`.
- `TenantStaffRole` → `PartnerStaffRole`: values vẫn `"owner"`, `"manager"`, `"staff"`.

Cột PostgreSQL stored as `String(20)` (xem `backend/app/models/tenant.py` line 39–50 và task #183 note) → không có enum type ở DB → không cần `ALTER TYPE ... RENAME`.

### 4.5. Data migration

Không cần. Chỉ rename schema; data rows giữ nguyên.

---

## 5. API changes

### 5.1. HTTP header

```
Trước:  X-Tenant-Id: <id>
Sau:    X-Partner-Id: <id>
```

Không support alias. Client cũ sẽ bị `400 Missing X-Partner-Id`.

### 5.2. Route prefix rename

| Cũ | Mới | Ai dùng |
|---|---|---|
| `/merchant/dashboard` | `/partner/dashboard` | Owner + staff |
| `/merchant/campaigns` | `/partner/campaigns` | Owner + staff |
| `/merchant/campaigns/{id}` | `/partner/campaigns/{id}` | |
| `/merchant/members` | `/partner/members` | |
| `/merchant/point-rules` | `/partner/point-rules` | |
| `/merchant/tiers` | `/partner/tiers` | |
| `/merchant/rewards` | `/partner/rewards` | |
| `/merchant/staff` | `/partner/staff` | Owner only |
| `/merchant/redemptions` | `/partner/redemptions` | |
| `/merchant/transactions` | `/partner/transactions` | Owner + staff POS |
| `/merchant/vouchers` | `/partner/vouchers` | |
| `/merchant/settings` | `/partner/settings` | Owner |
| `/merchant/authorizations` | `/partner/authorizations` | Owner |
| `/merchant/analytics` | `/partner/analytics` | Owner |
| `/tenants` | `/partners` | Public listing (member) |
| `/tenants/me` | `/partners/me` | Owner — get partner đang active |
| `/tenants/{id}` | `/partners/{id}` | |
| `/tenants/{id}/approve` | `/partners/{id}/approve` | Admin |
| `/tenants/{id}/suspend` | `/partners/{id}/suspend` | Admin |
| `/admin/tenants` | `/admin/partners` | Admin list |
| `/users/me/shops` | `/users/me/partners` | Customer — list all partners (đã bỏ is_member) |
| `/users/me/tenants` | `/users/me/partners-as-staff` | **Staff** — list partner-của-mình với role staff/owner. Đổi tên tránh collision với customer `/users/me/partners`. |
| `/tenants/me/settings` | `/partners/me/settings` | Owner edit partner settings |

### 5.3. Response schema changes

- **`/users/me/partners`** (tên mới của `/users/me/shops`):
  - **Bỏ** fields: `is_member`, `points_balance`, `tier_name` khỏi default response của list endpoint. Các field này vẫn dùng trong `/users/me/memberships` hoặc `/users/me/partners/{slug}` detail.
  - **Giữ:** `id`, `slug`, `name`, `category`, `description`, `logo_url`.
  - Rationale: end-user không cần biết "đã tham gia chưa" khi đang duyệt danh sách → UX mới là "tất cả đối tác đều có thể tích điểm khi giao dịch".

- **`/users/me/partners/{slug}`** (endpoint mới):
  - Thông tin partner (name, category, description, logo_url, contact_phone, contact_email, address, business_hours, website, tax_code).
  - User-specific state tại partner này: `points_balance`, `total_points_earned`, `current_tier_name`, `joined_at`, `last_activity_at` — lấy từ `memberships` nếu row tồn tại, `null` nếu chưa có giao dịch lần nào.
  - Không trả về history inline — history lấy qua `/users/me/ledger?partner_slug=<slug>`.

- **`/users/me/ledger`** (có sẵn):
  - **Thêm query param:** `partner_slug: str | None`. Nếu provided → filter ledger entries chỉ tại partner đó.

### 5.4. Request schema changes

- **Auth dep** kiểm header: `get_partner_id()` đọc header `X-Partner-Id` thay vì `X-Tenant-Id`. Trả `400 Missing X-Partner-Id header` (nguyên văn) nếu thiếu — chuẩn hoá message tiếng Anh ở HTTP layer.
- Không đổi body schema ngoài rename field `tenant_id` → `partner_id` trong các schema Pydantic (nếu schema có expose field này).

### 5.5. Deprecation

**Không có deprecation window.** Cutover deploy mới → URL cũ trả 404. Tương tự header cũ bị ignore, dep raise 400. Chủ đích: clean-break, không tolerance cho client cũ vì không có client production nào ngoài demo.

---

## 6. Backend code changes

### 6.1. File rename

```
backend/app/models/tenant.py                   → backend/app/models/partner.py
backend/app/models/tenant_staff.py             → backend/app/models/partner_staff.py
backend/app/models/tenant_authorization.py     → backend/app/models/partner_authorization.py
backend/app/models/tenant_settings_audit.py    → backend/app/models/partner_settings_audit.py

backend/app/services/tenant_service.py         → backend/app/services/partner_service.py
backend/app/services/tenant_staff_service.py   → backend/app/services/partner_staff_service.py  (nếu tồn tại)
backend/app/services/tenant_authorization_service.py → backend/app/services/partner_authorization_service.py  (nếu tồn tại)

backend/app/schemas/tenant.py                  → backend/app/schemas/partner.py
backend/app/schemas/tenant_staff.py            → backend/app/schemas/partner_staff.py
backend/app/schemas/tenant_authorization.py    → backend/app/schemas/partner_authorization.py

backend/app/api/tenants.py                     → backend/app/api/partners.py
backend/app/api/tenant_staff.py                → backend/app/api/partner_staff.py
backend/app/api/tenant_authorization.py        → backend/app/api/partner_authorization.py

backend/app/core/tenant_cache.py               → backend/app/core/partner_cache.py

backend/tests/unit/test_tenant_service.py      → backend/tests/unit/test_partner_service.py
backend/tests/unit/test_tenant_cache.py        → backend/tests/unit/test_partner_cache.py
backend/tests/integration/test_tenant_*.py     → backend/tests/integration/test_partner_*.py
```

### 6.2. Symbol rename (trong toàn bộ backend)

Áp dụng glossary section 3.1. Không được còn identifier nào chứa `tenant`/`Tenant` trong backend source sau khi merge (trừ comment migration lịch sử).

**Kiểm chứng:** `rtk grep -r "tenant" backend/app/ backend/tests/ --glob='*.py' | grep -v alembic/versions/ | wc -l` = 0.

### 6.3. File đặc biệt

**`backend/app/main.py`:**
- Import router `tenants_router`, `merchant_router` → `partners_router`, `partner_router`.
- **CORSMiddleware `allow_headers`** (verified dòng 66): `["Authorization", "Content-Type", "X-Tenant-Id"]` → `["Authorization", "Content-Type", "X-Partner-Id"]`. Nếu miss, browser preflight block request — 100% UI vỡ.
- **Global exception handler `IntegrityError`** (verified dòng 99–118): handler dùng **substring match trên text lowercase** (`"tenant_user" in msg_low or "tenant_staff" in msg_low`), KHÔNG query tên constraint. Cần update 2 chỗ:
  - String literal: `"tenant_user"` → `"partner_user"`, `"tenant_staff"` → `"partner_staff"`. Sau rename DB, PG error text sẽ chứa `partner_user`/`partner_staff` nên substring phải match.
  - Message tiếng Việt: `"User đã thuộc tenant này"` → `"User đã thuộc đối tác này"`.
- `"slug"` branch (dòng 107) giữ nguyên vì substring generic, không đụng rename.

**`backend/app/core/deps.py`** (228 lines):
- Header alias `"X-Tenant-Id"` → `"X-Partner-Id"` trong `Header(default=None, alias=...)`.
- Error message `"Missing X-Tenant-Id header"` → `"Missing X-Partner-Id header"`.
- Symbol rename: `tenant_role_cache`, `get_tenant_id`, `get_verified_tenant_id`, `get_current_tenant_role`, `require_staff_in_tenant`, `require_owner_in_tenant`, `require_customer_in_tenant`, `extract_tenant_id_from_header`.

**`backend/app/core/limiter.py`:**
- Verified: không có reference `tenant_id` — không đụng code. Chỉ sweep comment nếu có.

**`backend/app/core/config.py`:**
- Verified: không có `TENANT_*` env var — không đụng.

**`backend/app/jobs/*.py`:**
- Birthday voucher job + bất kỳ job nào query `Tenant`/`Membership.tenant_id` → rename.

**`backend/seed_demo.py`:**
- `Tenant(...)` → `Partner(...)`, `tenant_id=` → `partner_id=`. Copy demo text "Cafe Cộng" etc giữ nguyên, chỉ đổi key Python.

### 6.4. Service layer behavior

**Zero behavior change.** Chỉ rename. Cụ thể:

- `PartnerService.create_partner()` = cũ `TenantService.create_tenant()`: auto-generate slug từ name, check unique LIKE prefix, insert row `status=PENDING`.
- `MemberService.find_or_create_member(partner_id, phone)` (đã dùng tham số `tenant_id` → đổi `partner_id`): SAVEPOINT atomic upsert. Logic giữ nguyên 100%.
- `VoucherService.claim()`: logic `UPDATE WHERE issued_count < max_issuances` giữ nguyên; chỉ rename field khi SELECT.

### 6.5. Router structure

Giữ 3-router pattern trong `partners.py` (file rename của `tenants.py`):

```python
# backend/app/api/partners.py
partners_router = APIRouter(prefix="/partners", tags=["partners"])
partner_router  = APIRouter(prefix="/partner",  tags=["partner"])   # owner/staff dashboard
users_router    = APIRouter(prefix="/users",    tags=["users"])     # customer /users/me/partners...
```

`main.py` include cả 3 router. Không gộp.

### 6.6. Global exception handler — lưu ý thêm

Đã cover chính ở 6.3. Optional improvement (không BLOCK merge, nhưng tiện):
- Đổi message "Slug đã tồn tại" → "Slug đối tác đã tồn tại" để UI tiếng Việt sát nghĩa hơn. Không bắt buộc vì substring `"slug"` không bị ảnh hưởng bởi rename.

### 6.7. Pydantic schema

Ví dụ `schemas/tenant.py` → `schemas/partner.py`:
```python
class PartnerCreate(BaseModel): ...
class PartnerRead(BaseModel): ...
class PartnerSummary(BaseModel): ...
class PartnerUpdate(BaseModel): ...
```
Field `tenant_id` trong các schema khác (VD `MembershipRead.tenant_id`) → `partner_id`.

---

## 7. Frontend changes

### 7.1. Route group rename

```
frontend/src/app/(merchant)/        → frontend/src/app/(partner)/
frontend/src/app/(merchant)/layout.tsx → (partner)/layout.tsx
frontend/src/app/(merchant)/merchant/page.tsx → (partner)/partner/page.tsx
```

Toàn bộ 13 file trong `(merchant)/` rename subpath `merchant/` → `partner/`:

- `(merchant)/merchant/page.tsx` → `(partner)/partner/page.tsx`
- `(merchant)/merchant/vouchers/page.tsx`
- `(merchant)/merchant/staff/page.tsx`
- `(merchant)/merchant/rewards/page.tsx`
- `(merchant)/merchant/members/page.tsx`
- `(merchant)/merchant/pos/transactions/new/page.tsx`
- `(merchant)/merchant/settings/page.tsx`
- `(merchant)/merchant/authorizations/page.tsx`
- `(merchant)/merchant/authorizations/[id]/page.tsx`
- `(merchant)/merchant/campaigns/page.tsx`
- `(merchant)/merchant/campaigns/[id]/page.tsx`
- `(merchant)/merchant/campaigns/enroll/page.tsx`

Staff route group `(staff)/staff/*` giữ nguyên (vai trò staff khác — POS interface).

### 7.2. File rename (verified bằng Glob `frontend/src/{lib,types,components}/**/*merchant*`)

```
frontend/src/lib/tenant-store.ts                    → partner-store.ts
frontend/src/lib/api-merchant.ts                    → api-partner.ts
frontend/src/lib/api-merchant-enroll.ts             → api-partner-enroll.ts
frontend/src/lib/hooks/use-merchant.ts              → use-partner.ts
frontend/src/lib/hooks/use-merchant-enroll.ts       → use-partner-enroll.ts
frontend/src/components/merchant/                   → frontend/src/components/partner/
frontend/src/components/merchant/tenant-picker.tsx  → partner/partner-picker.tsx
frontend/src/components/merchant/merchant-sidebar.tsx → partner/partner-sidebar.tsx
frontend/src/types/merchant.ts                      → types/partner.ts
frontend/src/types/merchant-enroll.ts               → types/partner-enroll.ts
```

Ngoài ra `frontend/src/types/admin.ts` (có type tenant-related theo review) cần grep + update field/type references, nhưng không rename file.

### 7.3. Symbol rename

- `useTenantStore` → `usePartnerStore` (all consumers: 12 file).
- `getActiveTenantId()` → `getActivePartnerId()`.
- **Storage key** `"active_tenant"` → `"active_partner"`. **Verified**: store dùng `sessionStorage` (không phải localStorage — xem `tenant-store.ts` dòng 23, 37, 39). Session-scoped: đóng tab là mất → **KHÔNG cần migration code**, user mở tab mới sau deploy tự pick partner lại qua picker.
- Axios interceptor `src/lib/api.ts`: path prefix check `startsWith("/merchant")` → `startsWith("/partner")`; header inject `"X-Tenant-Id"` → `"X-Partner-Id"`.
- Types: `Tenant`, `TenantItem`, `TenantStaffRole` → `Partner`, `PartnerItem`, `PartnerStaffRole`.

### 7.4. UI copy rename (customer-facing)

**`/member/shops/page.tsx`** — rename sang **`/member/partners/page.tsx`**:

- Header title "Cửa hàng" → "Đối tác".
- **XOÁ** section stats 2 ô: "Đang là thành viên X" + "Tổng shop Y".
- **XOÁ** membership filter pills: "Tất cả / Đã tham gia / Chưa tham gia".
- **XOÁ** button "Tham gia / Đã là thành viên" ở mỗi card partner.
- **XOÁ** hiển thị `tier_name` badge + `points_balance` trên card list (di chuyển sang detail page).
- Giữ: search, category pills (Cafe / Ăn uống / Bán lẻ / Mỹ phẩm), list card đơn giản (logo, tên, category, description).
- Click vào card → route tới `/member/partners/[slug]`.

**`/member/partners/[slug]/page.tsx`** — **trang mới:**
- Header: back button + tên partner + badge category.
- Section 1 — Thông tin: logo, name, category, description, address, contact_phone, contact_email, business_hours, website (hiển thị các field có dữ liệu).
- Section 2 — "Điểm của bạn" (chỉ hiện nếu membership tồn tại):
  - `points_balance` nổi bật.
  - `current_tier_name` với emoji (Bronze/Silver/Gold/Platinum).
  - Small stats: tổng điểm tích luỹ, tham gia từ ngày nào.
- Section 2' — Nếu membership null: placeholder "Chưa có giao dịch tại đối tác này. Hãy quét QR khi mua hàng để bắt đầu tích điểm."
- Section 3 — "Lịch sử tích/đổi điểm tại đây": list point_ledger entries filter `partner_slug` đó, paginate. Reuse component từ `/member/history/page.tsx`, thêm prop `partnerSlug`.

**`/member/page.tsx`** (dashboard):
- "Cửa hàng của tôi" → "Đối tác của tôi".
- "Bạn chưa tham gia cửa hàng nào." → "Chưa có giao dịch tại đối tác nào. Khám phá đối tác để bắt đầu tích điểm.".
- Link "Khám phá cửa hàng" → "Khám phá đối tác".
- Card "Shop #{tenant_id}" → "Đối tác #{partner_id}" — ideal là fetch `partner.name` thay vì hiện ID. Nếu scope tight, giữ `#{id}` nhưng copy đổi "Shop" → "Đối tác".
- Link `/member/shops` → `/member/partners`.

**`/member/history/page.tsx`**:
- Hook `useMyLedger` optionally nhận `partnerSlug` param (xem 5.3). Copy "Lịch sử tại các cửa hàng" → "Lịch sử tại các đối tác".

**`/member/qr/page.tsx`**, **`/member/vouchers/*`**:
- Grep references "cửa hàng"/"shop"/"tenant" → replace "đối tác".

### 7.5. UI copy rename (owner/staff-facing)

**`(partner)/layout.tsx`** (ex-merchant):
- Sidebar header "Merchant Dashboard" / "Trang chủ shop" → "Trang chủ đối tác".
- Logo title: logic tên partner giữ nguyên (đã lấy từ tenant.name → partner.name).

**`(partner)/partner/page.tsx`**:
- Greeting "Chào {name}, chủ shop!" → "Chào {name}, chủ đối tác!".

**`(auth)/register/merchant/page.tsx`**:
- URL → `/register/partner`.
- Heading "Đăng ký doanh nghiệp" → "Đăng ký đối tác" (hoặc giữ "Đăng ký doanh nghiệp" nếu hợp nghiệp vụ — user chưa cấm; mặc định thống nhất "đối tác").
- Form field labels: "Tên cửa hàng" → "Tên đối tác", "Loại cửa hàng" → "Loại hình đối tác" etc.

**`(auth)/login/page.tsx`**:
- Nếu có link "Đăng ký chủ shop" → "Đăng ký đối tác".

**Header page `tenant-picker.tsx`** (đã rename file):
- Component name `TenantPicker` → `PartnerPicker`.
- Label "Chọn cửa hàng" → "Chọn đối tác".

### 7.6. PWA / Serwist

`frontend/src/app/sw.ts` (nếu có) — precache paths. Nếu có route `/member/shops` trong precache manifest → đổi `/member/partners`. Bump SW version để force revalidate khi user quay lại sau deploy.

### 7.7. Zustand storage migration — **không cần**

Ban đầu spec cân nhắc 3-line migration script. **Sau verify code thực tế**: `tenant-store.ts` dùng `sessionStorage`, session-scoped (đóng tab/browser là mất). Vì vậy:

- Không có legacy data persistent cần migrate.
- User owner/staff sau deploy mở tab mới → picker tự hiện → pick partner lại 1 lần (UX 5 giây).
- Clean-break trọn vẹn, không có exception.

---

## 8. Migration strategy — M1 one-shot clean-break

### 8.1. Nguyên tắc

1. **1 Alembic revision** làm tất cả schema rename (bảng + cột + index + constraint + sequence).
2. **1 deploy window** (Docker Compose prod down → migrate → up → verify).
3. **Không có alias** route/header/field trong code mới.
4. **Migration revision id** theo pattern hex hiện có: `<12-char-hex>_rename_tenant_to_partner.py`, `down_revision` = head hiện tại sau commit `bf38bc6`.

### 8.2. Alembic revision skeleton

```python
"""rename tenant to partner

Revision ID: <hex>
Revises: <previous head hex>
Create Date: 2026-04-24
"""
from alembic import op

revision = "<hex>"
down_revision = "<previous>"
branch_labels = None
depends_on = None

TABLE_RENAMES = [
    ("tenants", "partners"),
    ("tenant_staff", "partner_staff"),
    ("tenant_authorizations", "partner_authorizations"),
    ("tenant_settings_audit", "partner_settings_audit"),
]

COLUMN_RENAMES = [
    # (table_after_rename, "tenant_id", "partner_id")
    ("memberships",            "tenant_id", "partner_id"),
    ("transactions",           "tenant_id", "partner_id"),
    ("point_ledger",           "tenant_id", "partner_id"),
    ("point_rules",            "tenant_id", "partner_id"),
    ("tiers",                  "tenant_id", "partner_id"),
    ("rewards",                "tenant_id", "partner_id"),
    ("redemptions",            "tenant_id", "partner_id"),
    ("vouchers",               "tenant_id", "partner_id"),
    ("campaigns",              "tenant_id", "partner_id"),
    ("campaign_issuances",     "tenant_id", "partner_id"),
    ("campaign_service_fees",  "tenant_id", "partner_id"),
    ("notifications",          "tenant_id", "partner_id"),
    ("partner_staff",          "tenant_id", "partner_id"),
    ("partner_authorizations", "tenant_id", "partner_id"),
    ("partner_settings_audit", "tenant_id", "partner_id"),
]

def upgrade() -> None:
    for old, new in TABLE_RENAMES:
        op.rename_table(old, new)
    for table, old_col, new_col in COLUMN_RENAMES:
        op.alter_column(table, old_col, new_column_name=new_col)
    # Rename sequences
    for old, new in TABLE_RENAMES:
        op.execute(f"ALTER SEQUENCE IF EXISTS {old}_id_seq RENAME TO {new}_id_seq")
    # Rename indexes, constraints — enumerate from pg_indexes / pg_constraint
    # Script helper: scan WHERE name LIKE '%tenant%' AND belongs to renamed tables
    # ...

def downgrade() -> None:
    # Reverse order
    for table, old_col, new_col in COLUMN_RENAMES:
        op.alter_column(table, new_col, new_column_name=old_col)
    for old, new in TABLE_RENAMES:
        op.rename_table(new, old)
    for old, new in TABLE_RENAMES:
        op.execute(f"ALTER SEQUENCE IF EXISTS {new}_id_seq RENAME TO {old}_id_seq")
```

**Note chi tiết cho implementation:** Plan file sẽ enumerate đầy đủ các index + constraint cần rename (không để comment placeholder) bằng cách `SELECT conname, indexrelid::regclass::text FROM pg_constraint ... WHERE conname LIKE '%tenant%'` ở dev DB trước khi viết migration.

### 8.3. Cutover procedure

Prod chạy Docker Compose `loyalty-prod`. Steps:

1. **T-0** — Branch `feat/partner-rename` đã merge vào main, CI green (backend tests pass + frontend build + lint).
2. **T+0** — `docker compose -p loyalty-prod -f docker-compose.prod.yml down backend frontend` (Postgres giữ chạy).
3. **T+0.5m** — **Check concurrent connections** tránh `ALTER TABLE` hang do AccessExclusiveLock:
   ```sql
   SELECT pid, application_name, query FROM pg_stat_activity
   WHERE datname='loyalty' AND pid <> pg_backend_pid();
   ```
   Nếu có connection pgAdmin/DBeaver/APScheduler → đóng/terminate trước.
4. **T+1m** — Build image mới: `docker compose -p loyalty-prod -f docker-compose.prod.yml build backend frontend`.
5. **T+2m** — Start backend: auto Alembic upgrade → migration chạy. Migration nên bắt đầu bằng `SET lock_timeout = '10s'` để tránh hang vô thời hạn nếu miss connection nào ở bước 3.
6. **T+3m** — Verify migration:
   ```sql
   \dt partners partner_staff partner_authorizations partner_settings_audit
   SELECT column_name FROM information_schema.columns WHERE table_name='memberships' AND column_name LIKE 'partner%';
   ```
7. **T+4m** — Start frontend.
8. **T+5m** — Smoke test:
   - `curl http://localhost:8000/health` → 200.
   - Login khách1 → xem dashboard → tap 1 partner → thấy detail.
   - Login owner@cafe.vn → dashboard `/partner/*` load.
   - Đặt POS transaction demo → point_ledger entry OK.
9. **T+10m** — Bump SW version (đã build trong image) → customers next load revalidate.

### 8.4. Rollback

- **Trong 30 phút đầu:** nếu gặp blocker (migration fail, 500 rate > 5%) → `docker tag` image trước đó, re-deploy image cũ, `alembic downgrade -1`. Downgrade path đã có (xem 8.2).
- **Sau 30 phút:** forward-fix only. Data nếu đã có giao dịch mới sẽ mất nếu downgrade, nên prefer hotfix.

---

## 9. Documentation changes

### 9.1. `CLAUDE.md` (project root)

- Section "Domain vocabulary": `tenant = shop` → xoá; thêm `partner = đối tác (SME tham gia platform)`.
- Section "Multi-tenant scoping": đổi tên → "Multi-partner scoping". Ví dụ `X-Tenant-Id` → `X-Partner-Id`, `require_staff_in_tenant` → `require_staff_in_partner`.
- Section "Frontend route groups": `(merchant)` → `(partner)`, URL `/merchant/*` → `/partner/*`.
- Section "Key domain invariants": VD `Voucher.code uniqueness is per-tenant` → `per-partner`.
- Section "Commands" (migrations): giữ nguyên, không có reference tenant.

### 9.2. `AGENTS.md`

Grep `tenant`/`merchant` → replace `partner`. Nếu có subagent description mention "merchant" context → update.

### 9.3. `README.md` (nếu có)

Grep + replace. UI screenshots nếu có — re-take sau khi rename UI.

### 9.4. `docs/mo-ta-so-do.md`

Chứa `X-Tenant-Id` (verified bằng grep) → update.

### 9.5. Docstrings / inline comments

Tất cả docstring trong backend/frontend có `tenant`/`merchant` → `partner`. Không giữ legacy docstring.

---

## 10. Báo cáo STU updates

`bao-cao/content/` có 8 file `.py` build docx:

| File | Động tới gì |
|---|---|
| `chuong_1.py` | Tổng quan — section vocabulary: "tenant = đối tác SME" → "partner". |
| `chuong_2.py` | Công nghệ — nếu có code snippet reference `X-Tenant-Id`/`/merchant` → update. |
| `chuong_3.py` | Phân tích thiết kế — **nặng nhất**: ERD, data dictionary (table `tenants`, column `tenant_id`), use case "Chủ doanh nghiệp", sequence diagram. Rename toàn bộ. |
| `chuong_4.py` | Implementation — code snippet, route table, screenshot URL `/member/shops` → `/member/partners`, `/merchant/*` → `/partner/*`. |
| `chuong_5.py` | Testing + kết luận — nếu có liệt kê API/test names, rename. |
| `phu_luc.py` | Phụ lục API / schema — rename hoàn toàn. |
| `loi_cam_on.py` | Lời cảm ơn — check vô. Thường không đụng. |
| `tltk.py` | Tài liệu tham khảo — không đụng. |

**Chiến lược:** grep pattern `r"\b(tenant|merchant|Tenant|Merchant|cửa hàng|shop)\b"` trong `bao-cao/content/*.py`, review từng hit một (một số có thể giữ "cửa hàng" nếu đang trong context kể chuyện về shop thực tế, nhưng các term kỹ thuật bắt buộc đổi). Screenshots trong `bao-cao/assets/` (nếu có) → re-capture sau deploy.

**Build scripts ở `bao-cao/` root:** `build_docx.py`, `builder.py`, `style.py`. Grep luôn — thường `build_docx.py` import từ `content/*.py` nên ít đụng text, nhưng `builder.py` có thể chứa template cố định. Sau khi sweep content + build lại docx: `python bao-cao/build_docx.py` và verify output không còn "tenant"/"merchant" literal.

**Artifacts khác trong `bao-cao/` (verified bằng grep):**
- `bao-cao/assets/make_diagrams.py` — chứa tenant references, update.
- `bao-cao/plan.md` — có tenant mentions, update.
- `bao-cao/diagrams/mermaid/seq_login_tenant.mmd` — filename chứa "tenant". Rename filename → `seq_login_partner.mmd` + update content.
- `bao-cao/assets/uml/seq_login_tenant.puml` — tương tự, rename + update.
- `bao-cao/diagrams/mermaid/seq_claim_voucher.mmd` — content có tenant, update.
- Các `.mmd`/`.puml` khác trong `bao-cao/` — grep sweep `\btenant\b` tìm hết.

---

## 11. Testing plan

### 11.1. Unit tests

- `tests/unit/test_partner_service.py`: tất cả test case cho `TenantService` (create, activate, suspend, slug unique) → chạy pass với class `PartnerService`.
- Các unit test khác dùng `tenant_id=` fixture → rename `partner_id=`.

### 11.2. Integration tests

- `tests/integration/test_auth_api.py`: test header `X-Partner-Id` thay vì `X-Tenant-Id`. 401/403 message updates.
- `tests/integration/test_partner_api.py` (rename từ `test_tenant_api.py`): create partner, approve, list as member, get by slug. Test cả **endpoint customer mới** `/users/me/partners/{slug}`.
- `tests/integration/test_tenant_isolation.py` → rename `test_partner_isolation.py`. Invariant không đổi: 2 partners, dữ liệu không lẫn.
- `tests/integration/test_transaction_api.py`: POS → lazy membership creation → check `memberships.partner_id` field.
- `tests/integration/test_voucher_api.py`: code uniqueness per partner.
- `tests/integration/test_campaign_api.py`: tất cả test với `partner_id`.
- **Test mới** `test_customer_partners_listing`: GET `/users/me/partners` không có field `is_member`, `points_balance`, `tier_name` trong response (verify contract shrink). GET `/users/me/partners/{slug}` có full detail.
- **Test mới** `test_ledger_filter_by_partner`: GET `/users/me/ledger?partner_slug=<slug>` chỉ trả entries partner đó.

### 11.3. Frontend type check + build

```bash
cd frontend
npx tsc --noEmit   # 0 error
npm run lint       # 0 error, 0 warning mới
npm run build      # prod build success, output routes có /partner/* + /member/partners
```

### 11.4. Manual smoke (sau deploy)

Matrix 4 role:

| Role | Test case |
|---|---|
| Customer mới (khách1) | Đăng ký → login → `/member` dashboard → tap "Khám phá đối tác" → list 2 partner không có nút "Tham gia" → tap 1 partner → detail "Chưa có giao dịch…" |
| Customer cũ có điểm | khách1 (seed đã có 2 membership) → `/member/partners` → tap Cafe Cộng → detail thấy points_balance, tier, history 3 entries |
| Partner owner | owner@cafe.vn → login → redirect `/partner/dashboard` → sidebar URL `/partner/*` → tạo campaign OK |
| Staff | staff account → `/staff/*` giữ nguyên → POS transaction tạo membership lazy cho SĐT mới |
| Super admin | admin@loyalty.vn → `/admin/partners` → approve pending partner OK |

### 11.5. Regression checklist

- [ ] `point_ledger` entries sau deploy có `partner_id` đúng giá trị cũ `tenant_id`.
- [ ] Không có route `/merchant/*` hoặc `/tenants/*` trả 200 (phải 404).
- [ ] Header `X-Tenant-Id` gửi đi → 400 `Missing X-Partner-Id`.
- [ ] Serwist SW bump version → customer reload thấy UI mới.
- [ ] Không có console.error trong browser khi load `/member`, `/member/partners`, `/member/partners/[slug]`, `/partner/dashboard`.

---

## 12. Rollout & risk

### 12.1. Thứ tự commit đề xuất (để plan file chia nhỏ)

1. **Backend models + schemas + services + deps** — đổi tên file + symbol (không route). Run unit test.
2. **Backend API + main.py** — đổi route prefix + header alias. Run integration test.
3. **Alembic migration** — viết revision + enum constraint/index rename. Run upgrade local.
4. **Frontend store + api client + types** — đổi tên file + symbol.
5. **Frontend route group rename** — move `(merchant)` → `(partner)`, update internal links.
6. **Frontend customer UX** — rename `/member/shops` → `/member/partners`, xoá dead UX, thêm detail page.
7. **Documentation** — `CLAUDE.md`, `AGENTS.md`.
8. **Báo cáo** — `bao-cao/content/*.py` sweep.
9. **Deploy + verify**.

Mỗi commit pass CI trước khi tiếp.

### 12.2. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Alembic migration miss index/constraint rename → runtime error khi ORM reflect | High | Trước khi chạy prod, enumerate `pg_indexes` / `pg_constraint` trên dev DB sau khi restore prod dump để chắc chắn covered hết. |
| Frontend/backend deploy async: 1 cái deploy trước, cái kia còn code cũ → API mismatch | High | Single Docker Compose up cả 2 service trong cùng window. Image build cùng branch. |
| Serwist PWA cache giữ route cũ → customer offline tap `/member/shops` → 404 | Med | Bump SW version trong `frontend/src/app/sw.ts` (hoặc config Serwist) → customer next online load revalidate. **Không** add alias redirect — vi phạm clean-break. Chấp nhận 404 cho customer offline chưa revalidate (rất hiếm). |
| Zustand storage — user active_partner null lần đầu vào | Low | Không cần migration (sessionStorage đã session-scoped; user pick lại 1 lần). Xem 7.7. |
| **Migration hang** do AccessExclusiveLock từ pgAdmin/DBeaver/APScheduler connection đang mở | **High** | (a) Query `pg_stat_activity` trước cutover, terminate stale connection; (b) migration đặt `SET lock_timeout = '10s'` để fail fast thay vì hang. Xem 8.3 bước T+0.5m. |
| FK constraint naming inconsistent: SA custom (`fk_memberships_tenant_id_tenants`) vs PG default (`memberships_tenant_id_fkey`) | Med | Discovery query glob `%tenant%` trên cả `pg_indexes` + `pg_constraint` bắt được cả 2 pattern. |
| GitNexus index stale sau rename → impact analysis sai | Low | Run `gitnexus analyze` post-deploy. |
| Báo cáo docx đã build có tên cũ → giáo viên thấy inconsistent với demo | Med | Rebuild docx sau khi sweep `bao-cao/content/*.py`. |
| Test count: 183 file đụng tenant → merge conflict nếu nhánh chạy lâu | Med | Làm trên branch riêng, rebase main thường xuyên, merge trong 3-5 ngày. |
| Slug conflict ở partner-registration (constraint `partners_slug_key` đổi tên nhưng logic uniqueness không test) | Low | Integration test `test_partner_create_slug_unique` phải pass. |

### 12.3. Success criteria (tổng)

- ✅ `rtk grep -r "\\btenant\\b" backend/app/ frontend/src/` → 0 match (trừ alembic history).
- ✅ `rtk grep -r "\\bmerchant\\b" backend/app/ frontend/src/` → 0 match (trừ alembic history).
- ✅ `rtk grep -r "X-Tenant-Id" backend/ frontend/` → 0 match.
- ✅ Full pytest suite pass.
- ✅ Frontend `tsc --noEmit` + `npm run build` pass.
- ✅ 5 manual smoke flows ở 11.4 pass.
- ✅ `gitnexus analyze` post-deploy success, `gitnexus context` resource trả tên symbol mới.
- ✅ Báo cáo docx rebuild + render OK + grep check pass trong output.

### 12.4. Follow-up (sau deploy, ngoài scope spec này)

- Remove dòng migration Zustand sau 2 tuần (khi biết chắc user đã reload).
- Monitor 1 tuần error log có 404 `/merchant/*` không (chứng tỏ có cache/bookmark cũ).
- Nếu phát hiện cần thêm filter partner theo category trong `/member/partners`, mở spec riêng.

---

## Phụ lục A — File inventory

### A.1. Backend files touched (ước lượng)

- Models: 4 rename + ~15 file update FK field.
- Services: ~3 rename + ~20 file update import/reference.
- Schemas: 3 rename + ~10 file update.
- API: 3 rename + ~15 file update (router prefix + deps import).
- Tests: ~25 file rename/update.
- `core/deps.py`, `core/limiter.py`, `main.py`, `seed_demo.py`, `jobs/*`: ~6 file.
- Alembic: 1 file new.

**Total estimate:** ~100 file backend.

### A.2. Frontend files touched

- Route group: 13 pages + 1 layout moved.
- Lib: 4 file rename + 1 interceptor update.
- Components: 1 folder rename + ~3 sub-component rename.
- Types: 2-3 file with interface rename.
- Customer pages: 5 file update copy + 1 new page.
- Hooks: 2 file rename.

**Total estimate:** ~35 file frontend.

### A.3. Docs

- `CLAUDE.md`, `AGENTS.md`, `README.md` (3).
- `bao-cao/content/*.py` (8) + `bao-cao/build-docx.py`/`rebuild-docx.py` (1-2).

**Total estimate:** ~12 file docs.

### A.4. Grand total

~150 file. Plan file sẽ nhóm theo commit (mục 12.1) để mỗi commit reviewable (<30 file/commit).

---

## Phụ lục B — Kiểm chứng cuối cùng trước merge

Trước khi merge vào main, chạy:

```bash
# Backend
cd D:/DoAn/backend
rtk grep -rn "tenant\|Tenant" app/ tests/ --glob='*.py' | grep -v alembic/versions/
rtk grep -rn "merchant\|Merchant" app/ tests/ --glob='*.py'
rtk pytest -v

# Frontend
cd D:/DoAn/frontend
rtk grep -rn "tenant\|Tenant\|merchant\|Merchant" src/ --glob='*.ts' --glob='*.tsx'
rtk tsc --noEmit
rtk npm run build

# Docs
cd D:/DoAn
rtk grep -rn "X-Tenant-Id\|/merchant\|/tenants" bao-cao/content/*.py CLAUDE.md AGENTS.md

# GitNexus
gitnexus analyze
# Sau đó check trong Claude Code: gitnexus_query "Partner"
```

Tất cả phải trả output rỗng (trừ alembic/versions/ có history). Nếu còn hit → fix trước khi merge.

---

**End of spec. Xin user review trước khi sang bước writing-plans.**
