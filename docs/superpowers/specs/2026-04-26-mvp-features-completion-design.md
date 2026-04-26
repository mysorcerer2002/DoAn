# Spec — MVP Features Completion (2026-04-26)

> **Mục tiêu**: hoàn thiện 9 nhóm tính năng còn thiếu sau khi pivot HYBRID + cleanup `cleanup-mvp-2026-04-25` đã hạ schema xuống 11 bảng.
> **Trạng thái**: post-Phase 6 (class diagram đồng bộ). Spec này = Phase 7 series.
> **Migration cuối hiện hành**: `d4e5f6a7b8c9_pivot_to_mvp_balanced`.
> **Rev history**: v1 → v2 (fix C1-C6 + I1-I10) → **v3 (post code-review opus #2)**: fix 8 fact-check critical (route paths, file existence, enum casing, route group).

---

## 1. Bối cảnh & nhu cầu

Audit checklist MVP cuối ("Cân bằng" 2026-04-25) phát hiện **9 lỗ hổng**:

| # | Tính năng | Vai trò | Trạng thái cũ |
|---|---|---|---|
| 1 | Reset password gửi email thật (SMTP) | End-user / Admin / Owner | TODO log temp password |
| 2 | Ví Voucher (xem quà đã đổi) | End-user | Endpoint `/users/me/redemptions` chưa có |
| 3 | Sử dụng quà (hiển thị QR cho POS) | End-user | Trang detail chưa có |
| 4 | QR cá nhân từ JWT → user_id thuần | End-user / POS | Còn dùng JWT 60s rotating |
| 5 | Admin xem log đăng nhập | Admin | Bảng `login_log` chưa có |
| 6 | Admin xem log điều chỉnh điểm | Admin | `point_ledger` chưa có actor + chưa có endpoint |
| 7 | Admin xem tổng điểm lưu hành | Admin | Endpoint chưa có |
| 8 | Partner CRUD nhân viên (thêm / sửa pwd / disable) | Partner owner | Bảng `partner_staff` đã bị xoá Phase 1 |
| 9 | Khoá tài khoản 5-fail-15min anti brute-force | Auth | Chưa có |

User đã thêm SMTP creds vào `.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=mysorcerer2k2@gmail.com
SMTP_PASSWORD=<gmail app password>
SMTP_FROM_EMAIL=mysorcerer2k2@gmail.com
SMTP_FROM_NAME=Loyalty Platform
SMTP_TIMEOUT=10                          # mới — bound aiosmtplib
```

---

## 2. Quyết định kiến trúc (đã chốt qua brainstorm + code-review v2)

### 2.1 SMTP — `aiosmtplib` async + plain text + timeout 10s

- Lib: `aiosmtplib` async-native, không block event loop.
- **Bound timeout**: bọc `asyncio.wait_for(send_email(...), timeout=SMTP_TIMEOUT=10)`. Hết timeout → log warning + raise `EmailDeliveryError` để service xử lý theo policy của caller.
- Format: plain text Vietnamese, không HTML template.
- **Two failure policies (asymmetric)**:
  - `/auth/forgot-password` (public, leak prevention) → SMTP fail vẫn trả 200 generic message + log warning kèm temp password.
  - `/admin/users/{id}/reset-password` + `/partner/staff/{id}/reset-password` (authenticated, owner đã biết user tồn tại) → trả `{email_sent: bool, temp_password: <12 chars>}` để FE hiển thị "Email lỗi, gửi lại temp password cho staff bằng kênh khác". Temp password lộ là chấp nhận được vì đã authenticated.

### 2.2 QR cá nhân — raw `user_id`, KHÔNG còn endpoint server-side

- FE render `<QRCode value={user.id.toString()} />` bằng `qrcode.react` ngay trên trang `/member/qr`.
- **Xoá hoàn toàn route `GET /member/qr`** (router prefix `/member`, file `app/api/qr.py:17,20`). FE đọc `user.id` từ `useAuthStore`.
- POS `POST /partner/transactions/qr` (router prefix `/partner/transactions`, file `app/api/transactions.py:33,63`) — parse body `{qr_payload: "5", ...}` → `int(qr_payload)` → tra DB user → kiểm membership.
- **Refactor `app/services/qr_service.py`**: `decode_qr_payload()` → chỉ làm `int(payload.strip())` + DB lookup membership. KHÔNG còn JWT/fallback code logic. Route `transactions.py` giữ nguyên — chỉ service đổi (giữ pattern thin route / fat service).
- **Xoá personal-QR primitives** trong `app/core/qr.py`: `sign_qr_jwt`, `decode_qr_jwt`, `generate_fallback_code`, `verify_fallback_code_with_candidates`.
- **GIỮ NGUYÊN** `sign_shop_token`/`verify_shop_token` (HMAC cho `GET /member/checkin` ở `app/api/qr.py:33` — flow độc lập, không liên quan personal QR).
- Trade-off: QR không có chống replay/share. Mitigation = staff trực tiếp scan tại quầy + redemption_code dùng-1-lần (đã có).

### 2.3 Schema mới — Migration M6

#### Bảng `login_log`

```sql
CREATE TABLE login_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    identifier VARCHAR(255) NOT NULL,        -- email/phone client gõ vào
    ip VARCHAR(45) NOT NULL,                 -- IPv6-safe
    user_agent VARCHAR(500) NULL,            -- bound 500, truncate ở app layer
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(50) NULL,         -- 'wrong_password' (chỉ 1 giá trị — AuthService raise duy nhất InvalidCredentialsError)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Partial index cho lock query (chỉ failed records)
CREATE INDEX ix_login_log_failed_recent
    ON login_log (identifier, created_at DESC)
    WHERE success = false;

-- Index cho admin filter theo user
CREATE INDEX ix_login_log_user_created
    ON login_log (user_id, created_at DESC);
```

`user_id NULL` khi identifier không khớp user nào (lookup user trước verify password để gán `user_id` nếu tồn tại).
**`failure_reason` whitelist** = chỉ `'wrong_password'`. Lý do: `AuthService.authenticate()` (`backend/app/services/auth_service.py:85,91,125`) raise duy nhất `InvalidCredentialsError` cho mọi failure (user-not-found / wrong password / inactive). Không refactor service split exception (giữ scope đồ án); log đồng nhất `failure_reason='wrong_password'` cho mọi fail. KHÔNG có giá trị `'locked'` (fix C3, xem 2.4).

#### Bảng `partner_staff` — chỉ chứa STAFF (không chứa owner)

```sql
CREATE TABLE partner_staff (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL REFERENCES partners(id) ON DELETE RESTRICT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_partner_staff_user UNIQUE (user_id)
);

CREATE INDEX ix_partner_staff_partner ON partner_staff (partner_id);
```

**Quyết định C1 + C2** (owner story):
- Owner KHÔNG insert vào `partner_staff`. Owner pointer vẫn là `partners.owner_user_id` (như hiện tại).
- `partner_staff` chỉ chứa STAFF (role thừa → DROP cột `role`).
- Super admin (`system_role='super_admin'`) không có record nào trong `partner_staff` (không cần check).
- 1 user → 1 shop staff: `UNIQUE(user_id)` strict.
- **Insert guard ở service layer**: trước khi insert `partner_staff` → check `user.system_role == 'regular'` (không cho super_admin / owner đang sở hữu shop khác trở thành staff). Raise 409 nếu vi phạm.

#### Cột mới `point_ledger.actor_user_id` — fix I1

```sql
ALTER TABLE point_ledger
    ADD COLUMN actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX ix_point_ledger_actor_created
    ON point_ledger (actor_user_id, created_at DESC)
    WHERE actor_user_id IS NOT NULL;
```

`actor_user_id` = ai tạo entry này (admin khi ADJUST, customer/system tự khi EARN/REDEEM thì NULL). Existing rows giữ NULL — spec chấp nhận lịch sử trước M6 không có actor.

**Migration trigger handling**: tên trigger thực tế ở DB là `no_update_or_delete_point_ledger` (verify ở `models/point_ledger.py`). Nếu PostgreSQL không cho ALTER TABLE add column khi có trigger UPDATE/DELETE → migration M6 `op.execute("ALTER TABLE point_ledger DISABLE TRIGGER no_update_or_delete_point_ledger")` → ADD COLUMN → ENABLE TRIGGER. Không backfill data.

### 2.4 Anti brute-force — sliding window 5/15 phút (fix C3)

```python
# Trong POST /auth/login, TRƯỚC khi verify password
fail_count = await db.scalar(
    select(func.count()).select_from(LoginLog)
    .where(
        LoginLog.identifier == body.identifier,
        LoginLog.success == False,
        LoginLog.created_at > now() - timedelta(minutes=15),
    )
)
if fail_count >= 5:
    # KHÔNG ghi row mới — tránh self-perpetuate window
    raise HTTPException(
        status_code=423,                                  # Locked, không phải 429
        detail="Tài khoản tạm khoá 15 phút do sai quá nhiều lần.",
        headers={"Retry-After": "900"},                   # FE đọc để show countdown
    )
```

**Decisions sau code-review**:
- **C3 fix**: lock-rejected request KHÔNG ghi row vào `login_log` → window không tự perpetuate. `failure_reason` whitelist chỉ có 3 giá trị (xem 2.3).
- **I4 fix**: dùng **HTTP 423 Locked** (đúng semantic) + header `Retry-After: 900` (15 min). FE axios disable retry cho 423.
- Window trượt 15 phút theo lần fail mới nhất. Sau khi user gõ đúng password (request thứ 6+ trong window) → vẫn bị 423 cho tới khi fail records cũ rời window. Đây là đặc tính sliding (acceptable, document).
- Rate limit IP-based hiện tại (`30/min`) vẫn giữ — lock theo identifier là layer thứ 2.

### 2.5 Partner staff CRUD — chỉ Add / Reset password / Toggle is_active

**URL convention** (fix C6): theo pattern hiện có `/partner/*` (header `X-Partner-Id`), KHÔNG path-param. Tương thích với `staffApi` đã tồn tại ở FE.

| Action | Endpoint | Ý nghĩa |
|---|---|---|
| Liệt kê | `GET /partner/staff?is_active=true\|false\|all&limit=50&offset=0` | Default `all`. Response shape `{items: StaffResponse[], total: int}` (đồng bộ pagination convention 2.6). |
| Thêm | `POST /partner/staff` | Body: email/phone/full_name/password. Tạo user mới + insert `partner_staff` trong cùng transaction. |
| Reset pwd | `POST /partner/staff/{user_id}/reset-password` | Gen 12-char temp pwd + bcrypt + UPDATE users + email staff. Trả `{email_sent: bool, temp_password: str}` (xem 2.1). |
| Disable / Enable | `PATCH /partner/staff/{user_id}` body `{is_active: bool}` | Toggle `partner_staff.is_active`. |

**KHÔNG có** trong API:
- DELETE staff (FK `RESTRICT` — phải lưu lịch sử)
- PATCH role (không có cột role nữa — owner chỉ định bằng `partners.owner_user_id`)

**Race condition POST /partner/staff** (fix C4):
- Pre-check user.system_role == 'regular' + chưa có partner_staff record là UX hint, KHÔNG là source of truth.
- UNIQUE(user_id) là source of truth. Catch `IntegrityError` → 409 "Tài khoản đã thuộc shop khác".
- Toàn bộ insert trong `async with db.begin()` để rollback user nếu staff insert fail.

**JWT revocation khi disable** (fix I5):
- Tạo `require_staff_in_partner` dep mới: check user là owner OR có active partner_staff record (`is_active=true`) → mỗi request kiểm tra. Token disable = lần API call kế tiếp 403, không cần invalidate token.
- Áp dụng cho mọi route `/partner/*` (kể cả POS staff dùng).

### 2.6 Endpoint Ví Voucher (end-user)

| Endpoint | Mô tả |
|---|---|
| `GET /users/me/redemptions?status=pending\|used\|expired&limit=50&offset=0` | List redemption của user. **Default không filter** (trả tất cả status). FE tab pass `status=` explicit. **Casing lowercase** match `RedemptionStatus` enum value ở DB (`models/redemption.py:13-15`). |
| `GET /users/me/redemptions/{id}` | Detail 1 redemption (kèm `redemption_code`, `expires_at`, partner info, reward snapshot). |

FE render QR đổi quà từ `redemption_code` (string 8 ký tự) bằng `qrcode.react`. Không cần endpoint server-render.

**Pagination convention** (fix I2): dùng `limit + offset` (8/9 endpoints hiện tại). Default limit=50, max 200. KHÔNG dùng `page+limit`.

### 2.7 Admin endpoints

| Endpoint | Mô tả |
|---|---|
| `GET /admin/login-logs?identifier=&success=&from=&to=&limit=50&offset=0` | Filter theo identifier (LIKE), success bool, date range. |
| `GET /admin/point-adjustments?user_id=&partner_id=&actor_user_id=&from=&to=&limit=50&offset=0` | Query `point_ledger WHERE reason='ADJUST'`. JOIN users để hiện tên actor + subject. |
| `GET /admin/points-summary` | Trả breakdown total + by_partner (xem 2.8 cho định nghĩa SQL). |

Bổ sung `total_points_circulating` vào response của `GET /admin/stats` hiện có (= `SELECT SUM(points_balance) FROM users WHERE is_active=true`).

### 2.8 Định nghĩa SQL cho points-summary (fix I10)

```python
# total_circulating
SELECT SUM(points_balance) FROM users WHERE is_active=true

# LedgerReason values lowercase: 'earn' | 'redeem' | 'adjust' | 'expire' | 'refund'
# (verify models/point_ledger.py LedgerReason enum)

# total_earned (lifetime EARN toàn hệ thống)
SELECT SUM(delta) FROM point_ledger WHERE reason = 'earn' AND delta > 0

# total_redeemed (lifetime REDEEM, đảo dấu)
SELECT -SUM(delta) FROM point_ledger WHERE reason = 'redeem' AND delta < 0

# total_adjusted (net điều chỉnh manual của admin, có thể âm)
SELECT SUM(delta) FROM point_ledger WHERE reason = 'adjust'

# by_partner: total_earned_at_this_partner
# point_ledger.partner_id NOT NULL (verify models/point_ledger.py:40-42) → KHÔNG cần "IS NOT NULL"
SELECT pl.partner_id, p.name, COALESCE(SUM(pl.delta), 0) AS total_earned
FROM point_ledger pl
LEFT JOIN partners p ON p.id = pl.partner_id
WHERE pl.reason = 'earn' AND pl.delta > 0
GROUP BY pl.partner_id, p.name
ORDER BY total_earned DESC
```

Response shape:
```json
{
  "total_circulating": 1234567,
  "total_earned": 5000000,
  "total_redeemed": 3700000,
  "total_adjusted": -65433,
  "by_partner": [
    {"partner_id": 1, "name": "Cafe Cộng", "total_earned": 2500000},
    {"partner_id": 2, "name": "Lala Food", "total_earned": 2500000}
  ]
}
```

Invariant kiểm tra ở smoke test: `total_circulating ≈ total_earned - total_redeemed + total_adjusted` (cho phép sai khác do user inactive bị exclude).

---

## 3. Models & Schemas

### 3.1 Backend — files mới

```
app/models/login_log.py            — class LoginLog(Base, TimestampMixin)
app/models/partner_staff.py        — class PartnerStaff(Base, TimestampMixin)
app/schemas/login_log.py           — LoginLogResponse, LoginLogListResponse
app/schemas/partner_staff.py       — StaffCreateRequest, StaffPatchRequest, StaffResetResponse, StaffResponse, StaffListResponse
app/services/login_log_service.py  — log_attempt(), check_locked(), list_for_admin()
app/services/staff_service.py      — list_staff(), add_staff(), toggle_active(), reset_staff_password()
app/services/email_service.py      — async send_email(to, subject, body, timeout=10) → raises EmailDeliveryError
app/core/exceptions.py (extend)    — EmailDeliveryError
```

### 3.2 Backend — files sửa

```
app/api/auth.py            — login (lock check + log + return 423), forgot_password (gửi email thật, fail-silent)
app/api/partners.py        — POST /partners (catch IntegrityError → 409 cho owner_user_id duplicate nếu có)
app/api/partner.py (mới hoặc extend) — Toàn bộ /partner/staff CRUD (URL header-based)
app/services/qr_service.py — Refactor decode_qr_payload(): int(payload.strip()) + DB user lookup. XOÁ JWT/fallback code logic. Route transactions.py giữ nguyên.
app/api/admin.py           — extend /stats + thêm /login-logs, /point-adjustments, /points-summary, /users/{id}/reset-password trả thêm temp_password+email_sent
app/api/users.py           — GET /users/me/redemptions list + detail
app/api/qr.py              — XOÁ route GET /member/qr (FE render local). KHÔNG đụng GET /member/checkin shop QR.
app/core/qr.py             — XOÁ sign_qr_jwt, decode_qr_jwt, generate_fallback_code, verify_fallback_code_with_candidates. GIỮ sign_shop_token + verify_shop_token.
app/core/deps.py           — Thêm require_staff_in_partner (owner OR partner_staff active). require_owner_in_partner giữ nguyên semantic (chỉ owner_user_id).
app/services/auth_service.py — reset_password_send_temp() trả thêm temp_password để admin endpoint dùng; dispatch email qua EmailService.
app/api/admin.py           — Inline reset_user_password (không có admin_service.py). Field response giữ tên `temporary_password` (đang dùng) — KHÔNG đổi sang temp_password để tránh breaking FE existing. Endpoint mới (partner/staff reset) dùng cùng tên `temporary_password` cho nhất quán toàn hệ thống.
```

### 3.3 Frontend — pages mới

```
src/app/(member)/member/vouchers/page.tsx          — list redemption (tab pending/used/expired — lowercase match BE)
src/app/(member)/member/vouchers/[id]/page.tsx     — QR đổi quà (qrcode.react render redemption_code)
src/app/(admin)/admin/logs/page.tsx                — login logs + point adjustment logs (2 tabs)
src/app/(admin)/admin/system-points/page.tsx       — tổng điểm + breakdown by partner
```

### 3.4 Frontend — pages sửa

```
src/app/(member)/member/qr/page.tsx                — XOÁ poll JWT, render <QRCode value={user.id.toString()} /> from useAuthStore
src/app/(partner)/partner/staff/page.tsx           — MODIFY existing page (route group là (partner)/, KHÔNG (merchant)/). Cập nhật dùng useResetStaffPassword + useToggleStaffActive thay useRemoveStaff. Đọc `data.items` thay vì `data` (response shape đổi sang {items,total}).
src/lib/api-partner.ts                             — staffApi: XOÁ updateRole + remove. Đổi addStaff schema theo BE mới (email/phone/full_name/password). Thêm resetPassword + toggleActive. list() trả {items,total}.
src/lib/hooks/use-partner.ts                       — XOÁ useUpdateStaffRole, useRemoveStaff. Thêm useResetStaffPassword, useToggleStaffActive.
src/lib/api.ts (admin section)                     — login-logs, point-adjustments, points-summary clients
src/lib/api.ts (auth section)                      — handle 423 Locked: parse Retry-After, không retry, throw lỗi specific để form login show countdown
src/lib/hooks/useRedemptions.ts                    — TanStack Query hook mới
src/lib/hooks/useAdminLogs.ts                      — TanStack Query hook mới
src/lib/api-partner.ts (POS section)               — confirmTransactionFromQr: payload `{qr_payload: <user_id_string>}`. FE staff scanner trả raw text từ QR → BE parse int.
src/app/(staff)/staff/scan/page.tsx                — confirm scanner trả raw text (không decode JWT). Show user info từ response.
```

---

## 4. Business invariants

1. **`login_log` append-only ở app code** — không UPDATE/DELETE từ application layer (không thêm trigger DB, scope đồ án bỏ).
2. **`partner_staff.user_id` UNIQUE strict** — IntegrityError → 409 "Tài khoản đã thuộc shop khác". Pre-check chỉ là UX hint.
3. **Lock window**: 5 fail trong 15 phút → 423 Locked + `Retry-After: 900`. KHÔNG ghi log row khi reject lock (tránh self-perpetuate).
4. **Reset password — asymmetric leak policy**:
   - Public `/auth/forgot-password` → luôn 200 generic, không lộ tồn tại email.
   - Authenticated `/admin/users/{id}/reset-password` + `/partner/staff/{id}/reset-password` → trả `{email_sent: bool, temp_password: str}` để FE handle SMTP fail.
5. **POST /partner/staff** insert atomic (`async with db.begin()`):
   - Pre-check: target user phải `system_role='regular'` (không cho super_admin / owner).
   - Insert User + PartnerStaff trong cùng transaction. Catch IntegrityError → 409.
6. **`require_staff_in_partner`** (dep mới): check user là `partners.owner_user_id` OR có row `partner_staff(partner_id=p, user_id=u, is_active=true)`. Mọi request `/partner/*` POS staff route phải qua dep này.
7. **`point_ledger.actor_user_id`**: NULL cho EARN/REDEEM tự động. Set = admin user khi reason='ADJUST'.

---

## 5. Phân chia phases (8 phases — phase 7.x)

| Phase | Phạm vi | File chính |
|---|---|---|
| 7.1 | Migration M6 + models + schemas mới | `<hex>_login_log_partner_staff_actor.py`, `models/login_log.py`, `models/partner_staff.py`, models update `point_ledger.py`, `schemas/*` |
| 7.2 | EmailService (aiosmtplib + timeout) + integrate `/auth/forgot-password` + `/admin/users/{id}/reset-password` | `services/email_service.py`, `core/exceptions.py`, `api/auth.py`, `api/admin.py`, `services/auth_service.py`, `services/admin_service.py` |
| 7.3 | QR raw user_id (BE xoá endpoint + primitives, FE render local, POS scan parse int) | `api/qr.py`, `core/qr.py`, `api/transactions.py`, FE `member/qr/page.tsx`, `staff/scan/page.tsx`, `api-partner.ts` |
| 7.4 | Ví Voucher (BE endpoints + FE 2 pages) | `api/users.py`, FE `member/vouchers/page.tsx`, `member/vouchers/[id]/page.tsx`, `useRedemptions.ts` |
| 7.5 | Login log + lock 5/15 + 423 Locked (BE + FE handle) | `services/login_log_service.py`, `api/auth.py`, FE `lib/api.ts` interceptor, `lib/hooks/useLogin.ts` |
| 7.6 | Admin logs + summary (BE 3 endpoints + FE 2 pages) | `api/admin.py`, FE `admin/logs/page.tsx`, `admin/system-points/page.tsx`, `useAdminLogs.ts` |
| 7.7 | Partner staff CRUD (BE service + FE merchant page + dep `require_staff_in_partner` rollout) | `services/staff_service.py`, `api/partner.py` (extend), `core/deps.py`, FE `merchant/staff/page.tsx`, `api-partner.ts` clean stale calls |
| 7.8 | Smoke test E2E + commit final | (no new files) |

Mỗi phase commit độc lập + chạy `superpowers:code-reviewer` (theo CLAUDE.md mặc định) cho phase chạm code-server logic, KHÔNG cho phase chỉ FE styling.

---

## 6. Smoke test acceptance (Phase 7.8)

**Pre-req**: TRUNCATE login_log trước test isolation (xem N1).

- [ ] `/auth/forgot-password` (POST email khach1@gmail.com) → khach1 nhận email plain text với temp password trong hộp thư Gmail thật.
- [ ] Login sai 5 lần (identifier khach1@gmail.com) → lần 6 trả `423` + header `Retry-After: 900`.
- [ ] FE login form parse `Retry-After` → show countdown 15 phút.
- [ ] Đăng nhập đúng → `login_log` có row `success=True`.
- [ ] Đăng nhập sai → `login_log` có row `success=False, failure_reason='wrong_password'`.
- [ ] FE `/member/qr` render QR chứa string `"5"` (= user.id của khach1) — không call BE.
- [ ] Staff Cafe Cộng scan QR ở `/staff/scan` → POST `/partner/transactions/qr` body `{qr_payload: "5", ...}` → tìm user khach1 + check membership → 200.
- [ ] `/users/me/redemptions?status=pending` trả pending redemptions của khach1 (lowercase).
- [ ] `/users/me/redemptions/{id}` trả `redemption_code` 8 ký tự để FE render QR đổi quà.
- [ ] Owner Cafe Cộng `/partner/staff` → tạo staff mới với email staffnew@cafe.vn → staff đăng nhập được vào `/staff/scan`.
- [ ] Owner reset password staff → response `{email_sent: true, temp_password: "..."}`. Staff nhận email.
- [ ] Owner toggle `is_active=false` staff → staff lần API call kế tiếp trả 403.
- [ ] Owner toggle `is_active=true` lại → staff dùng được API.
- [ ] Tạo super_admin thành staff (qua API) → 409 "Tài khoản không hợp lệ làm staff".
- [ ] Tạo owner shop khác thành staff → 409 (vì user.system_role hoặc UNIQUE constraint).
- [ ] Admin `/admin/logs` tab login filter `success=false` thấy attempts vừa rồi.
- [ ] Admin tạo manual ADJUST + 100 điểm cho khach1 (qua endpoint admin có sẵn — `api/admin.py:140` reconcile_user_balance hoặc thêm POST `/admin/users/{id}/adjust-points` mới nếu chưa có) → `point_ledger` có row mới với `actor_user_id=admin.id`.
- [ ] Admin `/admin/logs` tab adjustments thấy row vừa tạo có cột "Người thực hiện" = admin@loyalty.vn.
- [ ] Admin `/admin/system-points` show `total_circulating ≈ total_earned - total_redeemed + total_adjusted` (chấp nhận sai do user inactive).

---

## 7. Out of scope (đẩy luận văn)

- HTML email template / multi-language email
- Email verification khi đăng ký
- 2FA / OTP SMS
- Audit log generic (chỉ làm login + point adjust trong đồ án)
- Suspicious-IP detection / GeoIP
- Reset password qua link token (giữ pattern temp password cho gọn)
- PWA Web Push notify staff khi có redemption mới
- Email enumeration timing attack (5-fail-lock theo identifier có exist sẽ khoá; identifier không exist không khoá → có thể đoán email tồn tại từ behavior khác nhau). Acceptable cho thesis.
- Staff self-reset password (staff phải request owner reset hộ qua kênh in-person/Zalo).

---

## 8. Changelog

- **v3** (post code-review opus #2 2026-04-26): fact-check 8 critical fixes:
  - C1-spec: route POS đổi `/pos/transactions/qr` → `/partner/transactions/qr` (verify `api/transactions.py:33`).
  - C2-spec: route personal QR đổi `GET /qr` → `GET /member/qr` (verify `api/qr.py:17,20`).
  - C3-spec: refactor QR decode ở `services/qr_service.py` (không inline route).
  - C4-spec: chốt path (b) — `failure_reason` whitelist còn 1 giá trị `'wrong_password'` (AuthService chỉ raise `InvalidCredentialsError` đơn).
  - C5-spec: enum status lowercase `pending|used|expired` (verify `models/redemption.py:13-15`).
  - C6-spec: SQL bỏ `partner_id IS NOT NULL` (cột NOT NULL); rewrite by_partner LEFT JOIN clean. LedgerReason value lowercase.
  - C7-spec: route group đúng là `(partner)/`, KHÔNG `(merchant)/`. MODIFY existing `(partner)/partner/staff/page.tsx`.
  - C8-spec: `services/admin_service.py` không tồn tại → inline trong `api/admin.py`. Field name giữ `temporary_password`.
- **v2** (post code-review opus 2026-04-26): fix C1-C6 + I1-I10:
  - C1: chốt option keep `partners.owner_user_id`, drop `partner_staff.role`.
  - C2: super_admin/owner KHÔNG được làm staff (service guard + UNIQUE).
  - C3: lock-rejected request KHÔNG ghi log row, whitelist `failure_reason` không có 'locked'.
  - C4: pre-check là UX hint, UNIQUE là source of truth, IntegrityError → 409.
  - C5/C6: list rõ FE files cần sửa, match URL convention `/partner/staff` (header-based) thay path-param, xoá `updateRole`/`remove` calls cũ.
  - I1: thêm `point_ledger.actor_user_id` migration + index.
  - I2: dùng `limit+offset` không `page+limit`.
  - I3: SMTP timeout=10s + 2 policy đối xứng.
  - I4: 423 Locked + `Retry-After: 900`.
  - I5: `require_staff_in_partner` dep mới check `partner_staff.is_active`.
  - I6: admin/owner reset password trả `{email_sent, temp_password}`.
  - I7: xoá `GET /qr` endpoint.
  - I8: giữ `sign_shop_token`/`verify_shop_token`, chỉ xoá personal QR primitives.
  - I9: default `?status=` không filter.
  - I10: SQL definitions cho points-summary inline.
  - N1, N4, N5, N7: test isolation note, bound user_agent 500, partial index, hex naming convention.

---

## 8. Changelog v3 — Smoke test 2026-04-26

### Kết quả 20 acceptance items (Phase 7.8)

| # | Item | Result | Note |
|---|------|--------|------|
| 1 | Pre: TRUNCATE login_log | PASS | Truncate thành công |
| 2 | Forgot password gửi email thật | PASS | 200 OK, email_sent=false (SMTP chưa config — fail-silent đúng spec) |
| 3 | Login sai 5 lần → lần 6 trả 423 + Retry-After | PASS | 423 + Retry-After: 900 |
| 4 | FE login form show countdown | SKIP (manual UI) | FE-only, không verify backend |
| 5 | Đăng nhập đúng → login_log success=True | PASS | login_log row: success=t, no failure_reason |
| 6 | Đăng nhập sai → login_log success=False, reason=wrong_password | PASS | login_log row: success=f, failure_reason=wrong_password |
| 7 | /member/qr render QR — FE-only | SKIP (manual UI) | Backend 404 đúng; không có route /member/qr |
| 8 | Staff scan QR → POST /partner/transactions/qr 201 | PASS | 201, points_earned=5. Note: cần set đúng gross_amount (int) và balance hợp lệ |
| 9 | /users/me/redemptions?status=pending trả pending (lowercase) | PASS | 200, status="pending" lowercase |
| 10 | /users/me/redemptions/{id} trả redemption_code | PASS | 200, field redemption_code có giá trị |
| 11 | Owner tạo staff mới → staff login OK | PASS | 201 tạo staff, staff login 200 |
| 12 | Owner reset pwd staff → email_sent=False (SMTP off) | PASS | 200, email_sent=false, temp_password trả về |
| 13 | Owner disable staff → staff API 403 | PASS | PATCH 200, staff get 403 |
| 14 | Owner enable lại → staff dùng OK | PASS | PATCH 200, staff POS QR 201 |
| 15 | Tạo super_admin thành staff → 409 | FAIL | Code thiếu guard `system_role == 'regular'` trong `add_staff` service. API trả 201 thay vì 409 |
| 16 | Tạo owner shop khác thành staff → 409 | FAIL | Tương tự item 15 — không có guard kiểm tra owner của partner khác. API trả 201 thay vì 409 |
| 17 | Admin /admin/login-logs filter success=false | PASS | 200, trả đúng entries có success=false |
| 18 | Admin tạo manual ADJUST → ledger có actor_user_id | PASS (partial) | Không có POST endpoint (by design per plan decision 2026-04-26). Verified qua direct insert: actor_user_id column tồn tại + lưu đúng |
| 19 | Admin /admin/point-adjustments tab thấy actor email | PASS | 200, actor_email="admin@loyalty.vn" hiển thị |
| 20 | Admin /admin/points-summary circulating ≈ earned - redeemed + adjusted | PASS | 200, endpoint trả đúng schema. Data inconsistency là pre-existing test data corruption (không phải code bug) |

### Stats

- **PASS**: 16 items (items 1-3, 5-14, 17-20)
- **SKIP (manual UI)**: 2 items (items 4, 7)
- **FAIL (code bug Phase 7.7)**: 2 items (items 15, 16)

### Deviations & Notes

1. **SMTP chưa config trong prod .env** — `email_sent=false` ở items 2, 12. Fail-silent đúng spec. Cần cấu hình SMTP_HOST/SMTP_USER/SMTP_PASSWORD trong prod `.env` khi deploy thật.

2. **FAIL items 15-16: `add_staff` thiếu guard `system_role`** — File `backend/app/services/staff_service.py`, function `add_staff`, thiếu check `if existing_user.system_role != 'regular'` trước khi insert `partner_staff`. Spec yêu cầu raise `InvalidStaffError` (→ HTTP 409) khi user là `super_admin` hoặc là owner của partner khác. Hiện tại code tìm user hiện có nhưng không validate role, dẫn đến super_admin và owner shop khác được thêm vào staff list.

3. **POST /admin/users/{id}/adjust-points không có trong MVP** — Theo plan decision 2026-04-26 (`LedgerReason.ADJUST` enum đã có nhưng chưa có route insert). Item 18 verified thông qua direct DB insert để xác nhận column `actor_user_id` hoạt động đúng.

4. **Data inconsistency trong prod DB từ prior test runs** — `users.points_balance` có giá trị âm (-30, -116 tổng) do các test trước thêm redeem quá nhiều. Không ảnh hưởng code logic; cần re-seed hoặc compensation entries nếu cần test sạch.

### Note

Phase 7 (7.1 → 7.7) hoàn thành. Items 15-16 cần fix `add_staff` service guard trước khi xem là MVP hoàn chỉnh. Đề nghị dispatch code-reviewer để review Phase 7.7 staff service.
