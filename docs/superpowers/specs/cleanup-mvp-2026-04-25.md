# Spec — Cleanup MVP cho đồ án (2026-04-25)

**Status**: REVIEWED v2 — addressed C1-C7 từ code review 2026-04-25.
**Author**: Nguyễn Hải Đăng
**Decision date**: 2026-04-25
**Parent spec**: `docs/spec-mvp-2026-04-25.md` (Spec MVP "Cân bằng" — chốt cùng ngày).
**Goal**: Dọn toàn bộ code/tables/services/routes/pages **không thuộc MVP final** để 1 model = 1 table và class diagram phản ánh đúng codebase.

---

## §1. Bối cảnh & nguyên do

Spec MVP "Cân bằng" cắt nhiều module so với codebase hiện tại nhưng **mới chỉ là spec — chưa được dọn vào code**:

- Backend còn 22 models, MVP chỉ cần 11.
- Frontend còn ~10 page group ngoài MVP (`campaigns`, `vouchers`, `staff`, `authorizations`, `notifications`).
- Class diagram (`docs/class-diagram-mvp-2026-04-25.mmd`) vẽ theo MVP → trông "thiếu" vì code chưa khớp.

User yêu cầu (cụ thể trong session này):
1. "tại sao vẫn còn table VerificationCode, tôi đã yêu cần loại bỏ rồi mà"
2. "is_shadow là gì cần loại bỏ nốt luôn"
3. "không cần trường password_changed_at"
4. "partner cần loại bỏ trường points_wallet_balance"
5. "lại không thấy table quản lý voucher đâu" *(diễn giải: thấy diagram thiếu so với code, không phải request restore)*
6. "cần clean toàn bộ những gì không dùng tới, không còn trong project này nữa"

→ Hướng cleanup là **dọn code khớp spec MVP** (không phải vẽ thêm vào diagram).

---

## §2. Decisions (đã chốt 2026-04-25)

### D1 — `verification_codes`: DROP HOÀN TOÀN

User chốt: drop bảng `verification_codes` hoàn toàn. Forgot-password chuyển sang **gửi mật khẩu mới qua email** (không OTP, không reset link).

**Flow forgot-password mới:**
1. User submit `POST /auth/forgot-password {email}`.
2. Backend: lookup user → gen `temp_password = secrets.token_urlsafe(8)` → set `user.password_hash = bcrypt(temp_password)` → log temp password ra console (dev) hoặc gửi email (prod, nếu có SMTP). Không cần table OTP.
3. User dùng temp password login → vào `/profile` đổi mật khẩu mới (form `PATCH /users/me/password`).

**Bảo mật**: Gửi mật khẩu plain qua email là anti-pattern (không mã hoá channel). Accept cho đồ án — production thực phải dùng reset link JWT short-lived. Note rõ trong báo cáo.

**Spec MVP §4** phải được cập nhật ở Phase 6:
- `POST /auth/forgot-password` body chỉ `{email}`, response `{message: "Mật khẩu mới đã gửi về email."}`.
- `POST /auth/reset-password` **bỏ** (không còn flow nhập OTP).
- US-EU-02 wording đổi: "Là khách quên mật khẩu, tôi nhập email → nhận mật khẩu mới qua email → đăng nhập → đổi lại trong hồ sơ."
- Cần thêm endpoint mới: `PATCH /users/me/password` body `{current_password, new_password}` để user tự đổi sau khi login bằng temp password.

### D2 — `partners.points_wallet_balance`: BỎ LUÔN CƠ CHẾ

User chốt: **(A)** bỏ luôn cơ chế ví seed Shop 1tr điểm. POS earn không bị giới hạn theo ví Shop.

**Hệ quả:**
- Drop field `partners.points_wallet_balance` (chỉ ở spec, chưa migrate vào DB → không cần migration drop column, chỉ cập nhật spec).
- POS earn flow §4.1 trong spec MVP: bỏ step 4b (lock partner wallet), bỏ step 4e (wallet check), bỏ step 4f trừ wallet.
- Bỏ schema invariant "Wallet seed invariant" (spec MVP §3 dòng 336).
- Spec MVP §3 dòng 14, 108, 220 phải cập nhật.

### D3 — `users.points_balance`: GIỮ THEO SPEC MVP (global wallet)

User clarify: tích điểm đi vào **`users.points_balance` global cross-shop** (theo memory `project_system_points_pivot.md`).

**Hệ quả** (đã có trong spec MVP, restate cho rõ):
- ADD `users.points_balance Integer NOT NULL DEFAULT 0`.
- DROP `memberships.points_balance` — `Membership` chỉ còn track lifetime_earned cho tier metric per-shop.
- Backfill `users.points_balance = SUM(point_ledger.delta WHERE user_id = users.id)` trong M5 migration.
- Schema invariant: `users.points_balance == SUM(point_ledger.delta WHERE user_id = u)`.

---

## §3. Scope cleanup chi tiết

### §3.1 Backend — DROP HOÀN TOÀN

| Layer | Symbol | Notes |
|---|---|---|
| Models | `voucher.py` | Campaign voucher cũ |
| Models | `campaign.py` | Campaign khuyến mãi NĐ 81 |
| Models | `campaign_template.py` | Template NĐ 81 (khác `voucher_template`) |
| Models | `campaign_regulatory_submission.py` | Hồ sơ pháp lý NĐ 81 |
| Models | `campaign_approval_event.py` | Audit chain NĐ 81 |
| Models | `campaign_issuance.py` | Voucher issuance log |
| Models | `partner_staff.py` | 1 account = 1 shop |
| Models | `partner_authorization.py` | Managed-service uỷ quyền |
| Models | `partner_settings_audit.py` | Settings audit |
| Models | `notification.py` | In-app noti (chỉ phục vụ campaign/voucher) |
| Models | `verification_code.py` | DROP hoàn toàn (D1) |
| Services | `voucher_service.py`, `campaign_service.py`, `campaign_approval_service.py`, `campaign_enrollment_service.py`, `campaign_template_service.py`, `partner_staff_service.py`, `partner_authorization_service.py`, `notification_service.py` | |
| Services | `verification_code_service.py` | DROP hoàn toàn (D1) |
| API routes | `vouchers.py`, `campaigns.py`, `campaign_enrollment.py`, `admin_campaigns.py`, `partner_staff.py`, `partner_authorization.py`, `notifications.py` | |
| Schemas | `voucher.py`, `campaign.py`, `campaign_template.py`, `campaign_enrollment.py`, `partner_staff.py`, `partner_authorization.py`, `notification.py` | |
| Schemas | `verification_code.py` (nếu có) | DROP hoàn toàn (D1) |
| Jobs | `birthday_voucher.py`, `expire_vouchers.py`, `check_post_report_overdue.py` | Phụ thuộc voucher/campaign |
| Jobs | `cleanup_codes.py` | DROP hoàn toàn (D1) |
| Tests | `test_voucher_service.py`, `test_vouchers_api.py`, `test_campaign_*` (5+ files), `test_campaigns_api.py`, `test_partner_staff_*` (2 files), `test_notification_service.py`, `test_birthday_job.py`, `test_jobs.py` | Drop toàn bộ test thuộc các module bị drop |
| Tests | `test_verification_code_service.py`, `test_claim_shadow.py` | DROP hoàn toàn (D1) |
| Scripts | `phase8_smoke.py` ... `phase15_smoke.py` | Smoke scripts cho các phase đã legacy — drop nếu touch module bị drop |

### §3.1.b Backend — MODIFY services (file giữ lại nhưng phải refactor)

**`auth_service.py`** (Phase 1):
- DROP method `request_claim()` (lines 105-127) — phụ thuộc `verification_code_service`.
- DROP method `claim_shadow()` (lines 129-160) — phụ thuộc `verification_code` + `is_shadow` flip.
- DROP `is_shadow=False` set ở `register()` (line 54) — column không còn.
- DROP `password_changed_at=now` set ở `register()` (line 56) — column không còn.

**`member_service.py`** (Phase 1):
- DROP `is_shadow=True` set ở line 44 — luồng tạo shadow user khi staff thêm member-by-phone đã out scope (MVP không có shadow user).
- Tinh chỉnh logic: thay vì tạo shadow user trước rồi flip `is_shadow=False` khi user claim, bắt user phải register thông qua `/auth/register` rồi staff mới link membership qua `phone`. Hoặc cho phép tạo `User` thật luôn với `password_hash = bcrypt(temp_password)` nếu staff cần thêm member-không-có-account; nhưng đó là **scope khác**, không thuộc cleanup. Phase 1 chỉ rip `is_shadow=True` set, để service tạo `User` không có cờ shadow → email/phone NOT NULL constraint check ở Pydantic.

**`transaction_service.py`** (Phase 2 — sau khi voucher table dropped):
- DROP method `_apply_voucher_if_provided()` (lines 262-...).
- DROP method `_maybe_issue_welcome_voucher()` (lines 549-...).
- DROP variable `voucher_id`, `voucher_discount` trong `create_transaction()` (lines 130-180) — points calc dùng thẳng `gross_amount` (hoặc `net_amount` = `gross_amount` luôn vì không còn discount voucher).
- DROP param `voucher_id` ở insert Transaction (line 180).
- DROP gọi `_maybe_issue_welcome_voucher` (line 226, 491) → `welcome_voucher_code` field response = None hoặc drop hẳn khỏi response schema.
- DROP `txn.voucher_discount_amount`, `txn.voucher_id` ở list/detail mapping (line 90).
- Update Pydantic schemas `TransactionResponse`, `TransactionWithMemberResponse` ở `schemas/transaction.py`: drop `voucher_id`, `voucher_discount_amount`, `legal_discount_ratio`, `welcome_voucher_code`.

**`auth.py` API** (Phase 1):
- DROP block JWT revoke check `pwd_changed_ts` (lines 104-116) — column không còn → JWT revoke after password change KHÔNG còn enforced ở backend.
- **Trade-off bảo mật**: Sau khi user đổi mật khẩu, JWT cũ vẫn valid đến hết `JWT_EXPIRE_MINUTES` (default 60min). Cho đồ án chấp nhận. Production thực phải có JWT version field hoặc redis blacklist — defer luận văn.

**`admin.py` API** (Phase 1):
- DROP field `is_shadow`, `password_changed_at` khỏi response schemas `AdminUserRow`, `AdminUserDetailResponse` (lines 421, 605, 608, 685, 688).
- DROP filter `User.is_shadow.is_(False)` ở các query list/detail (lines 461-462, 531, 636, 651, 709, 757) — không còn cần filter shadow user vì không tạo shadow nữa.
- DROP `target.password_changed_at = datetime.now(...)` ở reset-password endpoint (line 768) — không cần update column đã drop.

### §3.2 Backend — MODIFY (schema delta theo spec MVP)

| Bảng | Thay đổi |
|---|---|
| `users` | DROP CheckConstraint `ck_users_login_identifier` (vì cho phép `is_shadow=true` thay email/phone). DROP `is_shadow`, `password_changed_at`. ADD `points_balance Integer NOT NULL DEFAULT 0`. **Trade-off**: drop `password_changed_at` = mất khả năng JWT revoke after password change → JWT cũ valid đến hết TTL (60min). Accept đồ án. |
| `partners` | **D2** — bỏ luôn cơ chế ví seed Shop. Field `points_wallet_balance` chưa migrate vào DB → chỉ cần xoá ref khỏi spec MVP + class diagram, không có migration drop column. POS earn flow §4.1 spec MVP cũng phải sửa (bỏ wallet check). |
| `memberships` | DROP `points_balance`, `archived_at`. RENAME `total_points_earned` → `lifetime_earned`. Giữ `current_tier_id`. |
| `transactions` | DROP `voucher_id`, `voucher_discount_amount`, `legal_discount_ratio` (GENERATED column). DROP `staff_id` FK (Phase 3). |
| `point_ledger` | ADD `user_id FK users.id`, DROP `membership_id`. **Cẩn thận**: bảng có trigger `prevent_point_ledger_mutation` block UPDATE/DELETE → migration phải drop trigger trước khi backfill, restore trigger sau. Backfill `user_id` = `(SELECT user_id FROM memberships WHERE memberships.id = point_ledger.membership_id)`. |
| `redemptions` | ADD `user_id FK users.id`, DROP `membership_id`. ADD `snapshot_image_url String(500) NULL`. Backfill như point_ledger. |
| `rewards` | ADD `template_id FK voucher_templates.id NULL`, `offer_type Enum NOT NULL DEFAULT 'PERCENT_DISCOUNT'`, `offer_value Integer NULL`, `offer_label String(120) NOT NULL DEFAULT ''`, `valid_until Date NULL`, `terms Text NULL`. CheckConstraint `offer_value_matches_type` (xem spec MVP §3). |
| `voucher_templates` | **BẢNG MỚI** — schema theo spec MVP §3. |
| `point_rules` | Giữ nguyên — không touch. |
| `tiers` | Giữ nguyên — không touch (spec MVP có refactor riêng `sort_order` + drop `perks` nhưng đó scope khác, không thuộc cleanup này). |

### §3.3 Frontend — DROP

| Path | Lý do |
|---|---|
| `src/app/(admin)/admin/campaigns/page.tsx` + `[id]/` + `overdue/` | Campaign admin |
| `src/app/(partner)/partner/campaigns/page.tsx` + `[id]/` + `enroll/` | Campaign partner |
| `src/app/(partner)/partner/vouchers/page.tsx` | Voucher partner |
| `src/app/(partner)/partner/staff/page.tsx` | Staff partner |
| `src/app/(partner)/partner/authorizations/page.tsx` + `[id]/` | Partner authorization |
| `src/app/(member)/member/vouchers/page.tsx` + `[id]/` | Voucher member (khác Ví Voucher quà — Ví Voucher quà = `/member/redemptions` MVP mới) |
| `src/app/(staff)/staff/**/*` | Toàn bộ route group `(staff)` |
| `src/lib/api-partner-enroll.ts` | Campaign enrollment API client |
| `src/lib/api-partner.ts`: nhóm `campaigns`, `vouchers`, `staff` | Drop method group |
| `src/lib/api-admin.ts`: nhóm `campaigns`, `notifications` | Drop method group |
| `src/types/partner.ts`: `CampaignResponse`, `CampaignRoiResponse`, `CampaignCreateRequest`, `VoucherResponse`, `StaffResponse`, `StaffAddRequest`, `StaffAddResponse`, `is_shadow`, `password_changed_at`, `voucher_id`, `voucher_discount_amount`, `legal_discount_ratio` | Drop type definitions thuộc module bị drop |
| `src/components/partner/partner-sidebar.tsx`: link `/partner/campaigns`, `/partner/vouchers`, `/partner/staff`, `/partner/authorizations` | Cleanup nav |
| `src/components/admin/admin-sidebar.tsx`: link `/admin/campaigns` | Cleanup nav |
| `src/components/member/bottom-nav-bar.tsx`: tab `Voucher` (nếu link tới `/member/vouchers`) | Cleanup nav |
| `src/components/shared/pos-transaction-form.tsx`: field `voucher_code` | Drop voucher input |

### §3.4 Frontend — ADD (Phase 5)

| Path | Module MVP |
|---|---|
| `src/app/(admin)/admin/templates/page.tsx` (nếu chưa có) | Kho voucher template |
| Update `/member/page.tsx`: hiển thị `points_balance` global thay vì list theo partner |
| Update `/member/history/page.tsx`: ledger cross-shop |
| Update `/member/rewards/page.tsx`: list reward cross-shop với template render |

### §3.6 Auth dependency rewrite (C1 — partner_staff replacement)

`partner_staff` là **core auth dep chain**. Drop bare = backend chết import-time. Rewrite strategy:

**Vai trò mới**: MVP final chỉ có **1 owner / shop**. Drop role distinction. Auth chỉ còn check: `partners.owner_user_id == current_user.id`.

**Schema delta** (đã có `partners.owner_user_id` từ migration `162e25afc796`):
- Giữ nguyên FK `partners.owner_user_id → users.id`.
- Drop entirely table `partner_staff` + enum `PartnerStaffRole`.

**`backend/app/core/deps.py` refactor** (Phase 3):
- DROP: `get_current_partner_role`, `require_staff_in_partner`, `require_owner_in_partner` (legacy 3-dep chain).
- ADD: `require_owner_in_partner(current_user, partner_id, db) → Partner`. Body:
  ```python
  partner = await db.get(Partner, partner_id)
  if partner is None or partner.owner_user_id != current_user.id:
      raise HTTPException(403, "Bạn không phải chủ cửa hàng này.")
  return partner
  ```
- DROP staff caching helper (cache `_role_cache_get/set`) — không cần khi check 1 column.

**13 router files cần update** (rip `PartnerStaffRole` import + đổi dep):
1. `partners.py`
2. `transactions.py`
3. `point_rules.py`
4. `partner_authorization.py` *(file này drop hoàn toàn ở Phase 3)*
5. `campaigns.py` *(drop hoàn toàn ở Phase 2)*
6. `campaign_enrollment.py` *(drop hoàn toàn ở Phase 2)*
7. `members.py`
8. `settings.py`
9. `tiers.py`
10. `rewards.py`
11. `redemptions.py`
12. `analytics.py`
13. `partner_staff.py` *(drop hoàn toàn ở Phase 3)*

→ 8 file phải refactor (1, 2, 3, 7, 8, 9, 10, 11, 12), 5 file drop hoàn toàn (4, 5, 6, 13 + `notifications.py`).

**Test fixture** `tests/integration/conftest.py`: helper tạo staff record qua `partner_staff` table → đổi sang set `partner.owner_user_id` trực tiếp.

### §3.5 Docs

- Update `docs/spec-mvp-2026-04-25.md` — sync với decision Q1/Q2.
- Rebuild `docs/class-diagram-mvp-2026-04-25.{mmd,md,svg}` — drop reference tới model bị drop.
- Drop hoặc archive: `docs/mo-ta-so-do.md`, `docs/superpowers/plans/2026-04-12-tuan-*` (legacy plan), `docs/superpowers/plans/2026-04-22-*`, `docs/superpowers/plans/2026-04-24-partner-rename-*` nếu chứa reference module bị drop.
- Update `seed_demo.py` — drop seed campaign/voucher/staff/notification.

---

## §4. Migration ordering

Migrations **phải chạy đúng thứ tự** vì FK cascade:

```
M1 (Phase 1):
  - ALTER TABLE users DROP CONSTRAINT ck_users_login_identifier (vì constraint cho phép `is_shadow=true` thay email/phone — bỏ is_shadow → constraint cũ vô nghĩa, thay bằng NOT NULL trên ít nhất email/phone qua application-level validation hoặc giữ nguyên cho phép NULL cả hai vì MVP không có shadow user)
  - ALTER TABLE users DROP COLUMN is_shadow, DROP COLUMN password_changed_at
  - DROP TABLE verification_codes (D1 → drop hoàn toàn) — phải drop SAU khi rip code reference (auth_service.request_claim/claim_shadow + verification_code_service)
  - (Phase 1 cũng kéo theo) thêm endpoint mới /auth/forgot-password (gen temp pw, email) + /users/me/password (đổi pw) — code-only, không migration

M2 (Phase 2):
  - DROP VIEW IF EXISTS v_campaign_stats CASCADE  -- migration d8e9f0a1b2c3 tạo view depending on campaigns + vouchers, phải drop trước table
  - DROP TABLE campaign_approval_events (FK → campaigns)
  - DROP TABLE campaign_regulatory_submissions (FK → campaigns)
  - DROP TABLE campaign_issuances (FK → campaigns + vouchers)
  - DROP TABLE vouchers (FK → campaigns)
  - DROP TABLE campaigns (FK → campaign_templates)
  - DROP TABLE campaign_templates (no FK)
  - DROP TABLE partner_authorization_documents (FK → partner_authorizations) — promoted từ M3 vì model có FK cứng tới campaigns
  - DROP TABLE partner_authorizations — partner_authorization tồn tại chỉ để authorize phát hành campaign; khi campaign biến mất authorization mất ý nghĩa → drop kèm M2
  - ALTER TABLE transactions DROP COLUMN voucher_id, DROP COLUMN voucher_discount_amount, DROP COLUMN legal_discount_ratio (GENERATED — drop dễ)
  - UPDATE partners SET settings = settings - 'voucher_default_ttl_days' - 'birthday_campaign_id' (prune JSONB key cũ để PartnerSettings extra="forbid" không vỡ)

M3 (Phase 3):
  - DROP TABLE partner_staff
  - ALTER TABLE transactions DROP COLUMN staff_id (FK → partner_staff)
  - (Lưu ý: partner_authorizations + partner_authorization_documents đã drop trong M2.)

M4 (Phase 4):
  - DROP TABLE notifications
  - DROP TABLE partner_settings_audit

M5 (Phase 5 - schema rewrite):
  - ALTER TABLE users ADD COLUMN points_balance INTEGER NOT NULL DEFAULT 0
  - ALTER TABLE memberships RENAME COLUMN total_points_earned TO lifetime_earned
  - ALTER TABLE memberships DROP COLUMN points_balance, DROP COLUMN archived_at
  - DROP TRIGGER no_update_or_delete_point_ledger ON point_ledger  -- tên trigger thực, không nhầm với function `prevent_point_ledger_mutation`
  - ALTER TABLE point_ledger ADD COLUMN user_id INTEGER
  - UPDATE point_ledger SET user_id = (SELECT user_id FROM memberships WHERE memberships.id = point_ledger.membership_id)
  - ALTER TABLE point_ledger ALTER COLUMN user_id SET NOT NULL, ADD FK
  - ALTER TABLE point_ledger DROP COLUMN membership_id
  - CREATE TRIGGER no_update_or_delete_point_ledger ON point_ledger ... EXECUTE FUNCTION prevent_point_ledger_mutation();  (restore — tên trigger giữ nguyên)
  - ALTER TABLE redemptions ADD COLUMN user_id, snapshot_image_url; backfill; SET NOT NULL; DROP membership_id
  - CREATE TABLE voucher_templates (...)
  - ALTER TABLE rewards ADD COLUMN template_id, offer_type, offer_value, offer_label, valid_until, terms; backfill defaults; ADD CheckConstraint
  - (D2) `partners.points_wallet_balance` chưa migrate vào DB → KHÔNG có DDL cho field này. Chỉ cập nhật spec MVP + class-diagram + seed.
```

**Backfill points_balance cho user existing (M5)**:
```sql
UPDATE users SET points_balance = COALESCE(
  (SELECT SUM(delta) FROM point_ledger WHERE point_ledger.user_id = users.id),
  0
)
```

(Phải chạy **sau** khi point_ledger.user_id đã backfill xong.)

### §4.1 Pre-flight verify TRƯỚC khi chạy M5 (C7)

Trước khi exec M5, chạy SQL kiểm tra invariant:

```sql
-- 1. Mọi membership_id trong point_ledger phải có user_id ánh xạ được
SELECT COUNT(*) AS orphan_ledger
FROM point_ledger pl
LEFT JOIN memberships m ON m.id = pl.membership_id
WHERE m.id IS NULL;
-- Expect: 0. Nếu > 0 → có ledger row trỏ đến membership đã xoá → phải clean trước hoặc soft-orphan.

-- 2. Tổng delta point_ledger PER MEMBERSHIP phải khớp memberships.points_balance hiện tại
SELECT m.id, m.points_balance, COALESCE(SUM(pl.delta), 0) AS ledger_sum,
       (m.points_balance - COALESCE(SUM(pl.delta), 0)) AS diff
FROM memberships m
LEFT JOIN point_ledger pl ON pl.membership_id = m.id
GROUP BY m.id, m.points_balance
HAVING m.points_balance != COALESCE(SUM(pl.delta), 0);
-- Expect: empty. Nếu có row diff != 0 → ledger và balance lệch (do trigger không cover bug history) → fix manual hoặc accept loss.

-- 3. Mọi redemption.membership_id phải resolve user_id
SELECT COUNT(*) AS orphan_redemption
FROM redemptions r
LEFT JOIN memberships m ON m.id = r.membership_id
WHERE m.id IS NULL;
-- Expect: 0.

-- 4. Đếm tổng để sanity-check post-migration
SELECT COUNT(*) AS total_ledger_rows FROM point_ledger;
SELECT COUNT(*) AS total_redemption_rows FROM redemptions;
SELECT COUNT(*) AS total_users FROM users;
```

Nếu (1) hoặc (3) > 0 → migration sẽ fail ở bước SET NOT NULL → phải clean orphan trước.
Nếu (2) có lệch → balance sau migration sẽ không khớp → accept (đồ án data demo) hoặc UPDATE membership.points_balance = ledger_sum trước.

**Post-migration verify** (sau M5):
```sql
SELECT u.id, u.points_balance, COALESCE(SUM(pl.delta), 0) AS ledger_sum
FROM users u
LEFT JOIN point_ledger pl ON pl.user_id = u.id
GROUP BY u.id, u.points_balance
HAVING u.points_balance != COALESCE(SUM(pl.delta), 0);
-- Expect: empty.
```

---

## §5. Phase plan (verification & rollback)

| Phase | Sub-tasks | Verify | Rollback |
|---|---|---|---|
| **0** | Spec consolidated → review → commit | Spec file + review pass | Drop spec file |
| **1** | M1 migration + drop verification_code/is_shadow code + frontend prune | `pytest tests/integration/test_auth_*` pass; `npx tsc --noEmit` green; smoke /auth/login + /auth/forgot-password | Alembic downgrade -1 |
| **2** | M2 migration + drop campaign/voucher code + frontend pages + types | Backend boot OK; FE build OK; smoke /partner/me + /partner/rewards + /partner/transactions | Alembic downgrade -1 (recreate tables empty) |
| **3** | M3 migration + drop staff/authorization code + (staff) route group + **rewrite `deps.py` per §3.6 (drop 3-dep chain → 1-step owner check)** + update 8 router files | Backend boot OK; FE build OK; POS flow chỉ owner; smoke `/partner/me` + `/partner/transactions` POST | Alembic downgrade -1 |
| **4** | M4 migration + drop notification/audit code | Backend boot OK; FE build OK | Alembic downgrade -1 |
| **5** | **Pre-flight: chạy 4 SQL verify ở §4.1**, fix orphan nếu có. M5 migration + add user.points_balance + membership rename + ledger refactor + reward expand + voucher_template create. **Post-flight: SQL invariant `users.points_balance == SUM(point_ledger.delta)`** | Pre-flight 4 query: orphan_ledger=0, orphan_redemption=0, balance khớp. Post: invariant query trả empty. Backend boot OK; smoke POS earn | Alembic downgrade -1 (phức tạp do trigger) |
| **6** | Update spec + class-diagram + seed + UPDATE DB cafe-cong/lala banner + restart prod + verify URL | URL `https://loyalty.ecom-bill.com/member/partners/cafe-cong` hiển thị banner + giới thiệu + liên hệ | Restore DB snapshot trước Phase 6 |

---

## §6. Risk & mitigation

| Risk | Severity | Mitigation |
|---|---|---|
| Drop table FK còn ref → migration fail | High | Migration ordering chặt theo §4. `pytest --maxfail=1` mỗi phase. |
| Append-only trigger trên `point_ledger` block backfill `user_id` | High | Migration M5 phải `DROP TRIGGER` trước backfill, `CREATE TRIGGER` sau. |
| Frontend type breakage hidden bởi `unknown` cast | Medium | Mỗi phase chạy `npx tsc --noEmit` → fix lỗi trước commit. |
| Seed_demo.py reference symbol bị drop → seed crash | Medium | Update seed cùng phase touch model tương ứng. |
| Test fixture có ref symbol bị drop | Medium | Drop test file cùng phase; conftest.py prune. |
| Production data có row trong table bị drop | Low (đồ án — data demo) | Migration drop_table sẽ mất data; chấp nhận. Nếu cần preserve → export CSV trước khi run M2/M3/M4. |
| Code-review giữa phase tốn thời gian | Low | Theo memory `feedback_workflow_between_tasks.md` — bắt buộc; không skip. |
| Rebuild prod giữa phase causing downtime | Low (đồ án) | Chấp nhận; rebuild cuối cùng ở Phase 6. |

---

## §7. Success criteria

- [ ] `backend/app/models/` chỉ còn 11 file (đúng MVP).
- [ ] `backend/app/services/` không còn import `voucher`, `campaign*`, `partner_staff`, `partner_authorization`, `notification`, `verification_code` (trừ purpose RESET_PASSWORD nếu Q1=A).
- [ ] `backend/app/api/__init__.py` chỉ register router thuộc MVP.
- [ ] `pytest tests/` exit 0 (drop test thuộc module bị drop trước).
- [ ] `cd frontend && npx tsc --noEmit` exit 0.
- [ ] `cd frontend && npm run build` exit 0.
- [ ] `docker compose -p loyalty-prod` up clean, no migration error.
- [ ] `docs/class-diagram-mvp-2026-04-25.mmd` không còn class `Campaign`, `Voucher`, `PartnerStaff`, `PartnerAuthorization`, `Notification` (trừ `VerificationCode` nếu Q1=A).
- [ ] Mỗi class trong diagram có file tương ứng `backend/app/models/<name>.py`.
- [ ] URL `https://loyalty.ecom-bill.com/member/partners/cafe-cong` render đầy đủ banner + logo + giới thiệu + liên hệ + 3 tab.

---

## §8. Out of scope

- Refactor `tiers` model (drop `perks`, add `sort_order`) — spec MVP §3 có nhắc nhưng không phải yêu cầu user trong session này. Để phase sau.
- Refactor `transactions` table thành event-sourced — không liên quan cleanup.
- Migration data từ schema cũ sang schema mới ở **prod** — đồ án dùng data demo, accept loss.
- Build feature MVP còn thiếu (forgot-password, voucher template render PNG, /admin/templates page) — đó là spec MVP execution, không phải cleanup.

---

## §9. Workflow

- **Decisions D1, D2, D3**: đã chốt 2026-04-25 (xem §2).
- **Phase ordering**: 6 phase tuần tự theo §5. Không merge phase vì migration ordering chặt theo §4.
- **Code-review per phase**: BẮT BUỘC theo memory `feedback_workflow_between_tasks.md`. Sau mỗi phase implement → dispatch `superpowers:code-reviewer` với model `opus` → fix Critical/Important → commit → sang phase tiếp.
- **Rebuild prod**: chỉ rebuild cuối Phase 6 để minimize downtime + 1 lần verify duy nhất `https://loyalty.ecom-bill.com`. Mỗi phase verify bằng `pytest` + `npx tsc --noEmit` + `npm run build` local.
- **Commit**: 1-2 commit/phase. BE và FE có thể tách commit riêng nếu phase đụng cả 2.
