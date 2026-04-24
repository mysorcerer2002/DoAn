# Partner Rename + Discovery UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) hoặc `superpowers:executing-plans` để thực thi plan này theo từng phase. Steps dùng checkbox (`- [ ]`) syntax để tracking.

**Goal:** Rename clean-break `Tenant` + `Merchant` → `Partner` trên toàn codebase (backend + frontend + docs + báo cáo STU) đồng thời xoá UX "join partner" dead ở `/member/shops` và thêm trang `/member/partners/[slug]` detail + filter ledger theo partner.

**Architecture:** M1 one-shot clean-break — 1 Alembic revision rename bảng + cột + index + constraint + sequence; 1 deploy cutover; không alias route/header/field. Backend layer thin routes → fat services giữ nguyên; chỉ rename symbol + string literal. Frontend rename route group `(merchant)` → `(partner)`, lib `tenant-store.ts` → `partner-store.ts`, update axios header `X-Partner-Id`. Zustand `sessionStorage` session-scoped nên không cần migration code.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2 / Next.js 14 App Router + TypeScript + Tailwind v4 + Zustand + TanStack Query. PostgreSQL 15. Docker Compose prod.

**Spec gốc:** `docs/superpowers/specs/2026-04-24-partner-rename-and-discovery-ux.md` — mọi "tại sao" và glossary chi tiết nằm trong spec, plan chỉ mô tả "làm gì + làm như thế nào".

---

## 0. Trước khi đọc

- Plan này execute trên branch riêng `feat/partner-rename`. Không làm trực tiếp trên `main`.
- Mỗi phase kết thúc bằng 1 commit (conventional message tiếng Việt). CI xanh trước khi merge PR cuối cùng.
- Không execute inline trên prod — test local đầy đủ, merge main, rồi mới cutover.
- **Commit message convention**: `<type>(<scope>): <mô tả tiếng Việt ngắn>` — xem examples ở mỗi phase.
- **Grep verify**: dùng `rtk grep` để tiết kiệm token. Khi plan viết `rtk grep -rn "pattern" path/` nghĩa là chạy nguyên lệnh đó.
- **GitNexus**: branch này đụng ~150 file → sau deploy cuối cùng chạy `gitnexus analyze` để rebuild index. Trong quá trình implement plan, không cần re-index mỗi commit (hook handle).
- **Test commands**: backend dùng pytest trong container hoặc venv `backend/`. Frontend dùng `npx tsc --noEmit` + `npm run build`. Xem CLAUDE.md section Commands.

---

## 1. File inventory (authoritative)

Phần này enumerate chính xác file bị touch. Nếu trong quá trình execute phát hiện file khác chứa `tenant`/`merchant` chưa liệt kê → update inventory trước khi commit.

### 1.1. Backend files — rename

| Cũ | Mới |
|---|---|
| `backend/app/models/tenant.py` | `backend/app/models/partner.py` |
| `backend/app/models/tenant_staff.py` | `backend/app/models/partner_staff.py` |
| `backend/app/models/tenant_authorization.py` | `backend/app/models/partner_authorization.py` |
| `backend/app/models/tenant_settings_audit.py` | `backend/app/models/partner_settings_audit.py` |
| `backend/app/services/tenant_service.py` | `backend/app/services/partner_service.py` |
| `backend/app/services/tenant_staff_service.py` | `backend/app/services/partner_staff_service.py` |
| `backend/app/services/tenant_authorization_service.py` | `backend/app/services/partner_authorization_service.py` |
| `backend/app/schemas/tenant.py` | `backend/app/schemas/partner.py` |
| `backend/app/schemas/tenant_staff.py` | `backend/app/schemas/partner_staff.py` |
| `backend/app/schemas/tenant_authorization.py` | `backend/app/schemas/partner_authorization.py` |
| `backend/app/api/tenants.py` | `backend/app/api/partners.py` |
| `backend/app/api/tenant_staff.py` | `backend/app/api/partner_staff.py` |
| `backend/app/api/tenant_authorization.py` | `backend/app/api/partner_authorization.py` |
| `backend/app/core/tenant_cache.py` | `backend/app/core/partner_cache.py` |
| `backend/tests/unit/test_tenant_service.py` | `backend/tests/unit/test_partner_service.py` |
| `backend/tests/unit/test_tenant_cache.py` | `backend/tests/unit/test_partner_cache.py` |
| `backend/tests/integration/test_tenant_*.py` | `backend/tests/integration/test_partner_*.py` (sweep) |

### 1.2. Backend files — update (không rename)

Không rename file, chỉ sửa nội dung (rename symbol, rename field `tenant_id` → `partner_id`, rename route prefix, rename import). Enumerate theo folder:

- `backend/app/models/__init__.py` — export list.
- `backend/app/models/{membership,transaction,point_ledger,point_rule,tier,reward,redemption,voucher,campaign,campaign_issuance,campaign_service_fee,notification}.py` — cột FK `tenant_id` → `partner_id` trong SA mapping.
- `backend/app/services/{member,transaction,voucher,campaign,campaign_approval,campaign_enrollment,campaign_fee,campaign_template,point_rule,redemption,reward,tier,settings,analytics,qr,notification,ledger,auth}_service.py` — parameter `tenant_id` → `partner_id`, import path, reference class.
- `backend/app/schemas/{auth,campaign,campaign_approval,campaign_enrollment,campaign_template,claim_shadow,ledger,member,notification,point_rule,qr,redemption,reward,settings,tier,transaction,voucher}.py` — field `tenant_id` → `partner_id` (nếu schema expose).
- `backend/app/api/{admin,admin_campaigns,analytics,auth,campaign_enrollment,campaigns,members,notifications,point_rules,qr,redemptions,rewards,settings,tiers,transactions,vouchers}.py` — import + router prefix + dep reference.
- `backend/app/core/{deps,limiter,config}.py` — xem phase 3 chi tiết.
- `backend/app/main.py` — CORS, exception handler, router include.
- `backend/app/jobs/*.py` — ref tenant/membership.tenant_id.
- `backend/seed_demo.py` — Tenant() → Partner(), tenant_id= → partner_id=.
- `backend/alembic/versions/<new>_rename_tenant_to_partner.py` — file mới (tạo ở Phase 1).

### 1.3. Frontend files — rename

| Cũ | Mới |
|---|---|
| `frontend/src/lib/tenant-store.ts` | `frontend/src/lib/partner-store.ts` |
| `frontend/src/lib/api-merchant.ts` | `frontend/src/lib/api-partner.ts` |
| `frontend/src/lib/api-merchant-enroll.ts` | `frontend/src/lib/api-partner-enroll.ts` |
| `frontend/src/lib/hooks/use-merchant.ts` | `frontend/src/lib/hooks/use-partner.ts` |
| `frontend/src/lib/hooks/use-merchant-enroll.ts` | `frontend/src/lib/hooks/use-partner-enroll.ts` |
| `frontend/src/types/merchant.ts` | `frontend/src/types/partner.ts` |
| `frontend/src/types/merchant-enroll.ts` | `frontend/src/types/partner-enroll.ts` |
| `frontend/src/components/merchant/` | `frontend/src/components/partner/` (folder) |
| `frontend/src/components/merchant/tenant-picker.tsx` | `frontend/src/components/partner/partner-picker.tsx` |
| `frontend/src/components/merchant/merchant-sidebar.tsx` | `frontend/src/components/partner/partner-sidebar.tsx` |
| `frontend/src/app/(merchant)/` | `frontend/src/app/(partner)/` (folder) |
| `frontend/src/app/(merchant)/merchant/` | `frontend/src/app/(partner)/partner/` (subpath) |
| `frontend/src/app/(auth)/register/merchant/page.tsx` | `frontend/src/app/(auth)/register/partner/page.tsx` |
| `frontend/src/app/(member)/member/shops/page.tsx` | `frontend/src/app/(member)/member/partners/page.tsx` |

### 1.4. Frontend files — new

| File | Mô tả |
|---|---|
| `frontend/src/app/(member)/member/partners/[slug]/page.tsx` | Trang detail partner cho customer — xem Phase 8 chi tiết. |
| `frontend/src/lib/hooks/use-partner-detail.ts` | TanStack Query hook fetch `/users/me/partners/{slug}`. |

### 1.5. Frontend files — update (không rename)

- `frontend/src/app/(member)/member/page.tsx` — dashboard copy + link.
- `frontend/src/app/(member)/member/history/page.tsx` — hook `useMyLedger` optional `partnerSlug`.
- `frontend/src/app/(member)/member/qr/page.tsx` — copy sweep.
- `frontend/src/app/(member)/member/vouchers/page.tsx` + `[id]/page.tsx` — copy.
- `frontend/src/app/(member)/member/profile/page.tsx` — copy.
- `frontend/src/app/(staff)/staff/*.tsx` — nếu có reference `/merchant/*` route link.
- `frontend/src/app/(auth)/login/page.tsx` — link đăng ký đối tác.
- `frontend/src/app/(admin)/admin/tenants/page.tsx` — rename folder → `admin/partners/page.tsx` (giữ nguyên admin group, chỉ đổi subpath).
- `frontend/src/lib/api.ts` — axios interceptor.
- `frontend/src/types/admin.ts` — types tenant-related (xem spec 7.2).
- `frontend/src/app/layout.tsx`, root metadata — nếu có reference.
- `frontend/src/components/member/bottom-nav-bar.tsx` — regex hide trên detail view `/member/partners/[slug]`.

### 1.6. Docs files

- `CLAUDE.md` (root).
- `AGENTS.md` (root).
- `README.md` (root, nếu tồn tại).
- `docs/mo-ta-so-do.md`.
- `backend/README.md` / `frontend/README.md` (grep check).

### 1.7. Báo cáo files

- `bao-cao/content/{loi_cam_on,chuong_1,chuong_2,chuong_3,chuong_4,chuong_5,phu_luc,tltk}.py` — grep + sweep.
- `bao-cao/build_docx.py`, `bao-cao/builder.py`, `bao-cao/style.py` — grep.
- `bao-cao/plan.md` — grep.
- `bao-cao/assets/make_diagrams.py` — grep.
- `bao-cao/diagrams/mermaid/seq_login_tenant.mmd` → rename `seq_login_partner.mmd`.
- `bao-cao/assets/uml/seq_login_tenant.puml` → rename `seq_login_partner.puml`.
- `bao-cao/diagrams/mermaid/seq_claim_voucher.mmd` — content sweep.
- Các `.mmd` / `.puml` khác trong `bao-cao/` — sweep.

---

## 2. Phases & commits

| Phase | Nội dung | Acceptance gate | Commit message |
|---|---|---|---|
| 1 | DB discovery query + viết Alembic revision (chưa apply) | Migration file tồn tại, `alembic check` pass | `chore(db): alembic revision rename tenants→partners (chưa apply)` |
| 2 | Backend models + enums + __tablename__ + `tenant_id` → `partner_id` cột FK | Unit test `pytest tests/unit/test_partner_service.py -v` pass sau apply migration local | `refactor(backend-models): Tenant→Partner + tenant_id→partner_id cột FK` |
| 3 | Backend services + schemas + core/deps + tenant_cache + main.py + seed + jobs | Unit test toàn bộ `pytest tests/unit -v` pass | `refactor(backend-core): rename service/schema/deps/cache Tenant→Partner` |
| 4 | Backend API routes + router prefix + header `X-Partner-Id` + endpoint mới `/users/me/partners/{slug}` + filter `?partner_slug=` cho ledger | Integration test `pytest tests/integration -v` pass | `refactor(backend-api): route prefix /partner/* + endpoint detail + filter ledger` |
| 5 | Backend apply migration + full verify + grep sạch | `alembic upgrade head` + `pytest -v` pass + grep tenant/merchant backend = 0 | `chore(backend): apply migration + verify grep sạch` |
| 6 | Frontend store + types + api client + hooks + components rename | `npx tsc --noEmit` pass | `refactor(frontend-lib): rename tenant-store/api-merchant/types → partner` |
| 7 | Frontend route group `(merchant)` → `(partner)` + register partner | `npm run build` pass, smoke test /partner/dashboard render | `refactor(frontend-routes): (merchant)/merchant/* → (partner)/partner/*` |
| 8 | Frontend customer UX: `/member/partners` + xoá dead UX + trang detail `/member/partners/[slug]` + hook ledger filter | Manual smoke pass (matrix 5 test case trong spec §11.4 — Customer mới, Customer cũ, Partner owner, Staff, Super admin) | `feat(member): xoá UX join + trang đối tác detail + ledger filter` |
| 9 | Frontend final verify — type check + build + lint + sweep copy | `tsc --noEmit + build + lint` 0 error/warning mới | `chore(frontend): final verify + copy sweep` |
| 10 | Docs — CLAUDE.md, AGENTS.md, docs/mo-ta-so-do.md | Grep `tenant\|merchant` trong docs = 0 | `docs: rename Tenant/Merchant → Partner trong docs chính` |
| 11 | Báo cáo STU — `bao-cao/content/*.py`, diagrams, build docx | Rebuild docx, grep output không còn `tenant`/`merchant`/`X-Tenant-Id` | `docs(bao-cao): rename Tenant/Merchant → Partner toàn báo cáo` |
| 12 | Deploy cutover (prod) + 5 smoke flows + post-deploy `gitnexus analyze` | 5 smoke flow pass, 0 error log 10 phút đầu | `chore(deploy): partner rename cutover prod` |

**Total: 12 commits ~ 5-7 ngày công.** Mỗi phase phải pass acceptance gate trước khi tiếp phase kế.

---

## Phase 1 — DB discovery + Alembic revision (chưa apply)

**Goal:** Tạo file migration có đầy đủ rename bảng + cột + index + constraint + sequence để Phase 5 chạy được `alembic upgrade head` không thiếu gì.

**Files:**
- Create: `backend/alembic/versions/<12-hex>_rename_tenant_to_partner.py`
- Tool: Script discovery query SQL (không commit, chỉ chạy để enumerate).

**Acceptance:** File migration tồn tại, `alembic check` pass, migration upgrade/downgrade logic đầy đủ.

### Step 1.1 — Discovery query trên dev DB

Khởi động dev Postgres (đang chạy qua `docker compose -p loyalty-prod -f docker-compose.prod.yml` với DB `loyalty` user `loyalty`):

- [ ] Chạy discovery query, lưu output vào scratch note:

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT indexname FROM pg_indexes WHERE indexname LIKE '%tenant%' ORDER BY indexname;"
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT conname FROM pg_constraint WHERE conname LIKE '%tenant%' ORDER BY conname;"
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT sequence_name FROM information_schema.sequences WHERE sequence_name LIKE '%tenant%' ORDER BY sequence_name;"
```

**Expected output — dùng làm input cho migration revision file** (verified count trên prod DB 2026-04-24):
- **~29 index** — bao gồm:
  - **4 PK custom** (Alembic naming convention): `pk_tenants`, `pk_tenant_staff`, `pk_tenant_authorizations`, `pk_tenant_settings_audit`. ⚠️ PK có tên custom **KHÔNG** auto-rename khi `RENAME TABLE` — phải `ALTER INDEX` explicit, quên sẽ để `pk_tenants` tồn tại trên bảng `partners` gây confusion.
  - `ix_*tenant*` (ví dụ `ix_memberships_tenant_id`, `ix_vouchers_tenant_id`, `ix_point_ledger_tenant_id`...).
  - Unique constraint-backed indexes `uq_*_tenant_*`.
  - **Partial unique index** `ux_tenant_authorizations_active_per_campaign` — partial UNIQUE (không phải constraint-backed → rename qua `ALTER INDEX`, không `ALTER TABLE RENAME CONSTRAINT`).
- **~34 constraint** — bao gồm:
  - FK có tenant trong **column part**: `fk_<table>_tenant_id_tenants`, `fk_<table>_tenant_id_<other_fk>`.
  - FK có tenant trong **table-name part** (không phải column): `fk_tenant_authorizations_campaign_id_campaigns`, `fk_tenant_authorizations_signed_by_user_id_users`, `fk_tenants_owner_user_id_users`.
  - **6 CHECK** tên dài double-prefix: `ck_tenant_authorizations_ck_tenant_authorizations_per_c_<hex>` etc (Alembic naming với 2 layer). Grep output sẽ hiện rõ — rename từng con theo new table name.
  - Unique `uq_<table>_tenant_*`.
- **4 sequence**: `tenants_id_seq`, `tenant_staff_id_seq`, `tenant_authorizations_id_seq`, `tenant_settings_audit_id_seq`.

Ghi output vào file tạm `tmp/discovery_tenant.txt` (ignored bởi git) để tham chiếu khi viết migration.

⚠️ **Không skip PK + partial index**: nếu count thực tế < 29 index thì query sót (thường do schema `public` không phải mặc định). Re-query với `schemaname = 'public'` filter.

### Step 1.2 — Lấy current head

- [ ] Xem head hiện tại:

```bash
docker exec loyalty-backend-prod alembic current
```

Hoặc check file:

```bash
rtk ls D:/DoAn/backend/alembic/versions/
```

Chọn revision mới nhất (file có timestamp mới nhất → open file → copy `revision = "<hex>"`). Lấy hex đó làm `down_revision` cho revision mới.

### Step 1.3 — Tạo revision file

- [ ] Tạo file `backend/alembic/versions/<new-hex>_rename_tenant_to_partner.py`. Sinh hex bằng `python -c "import secrets; print(secrets.token_hex(6))"`:

```python
"""rename tenant to partner

Revision ID: <new-hex>
Revises: <previous-head-hex>
Create Date: 2026-04-24 <HH:MM>:00
"""
from alembic import op

revision = "<new-hex>"
down_revision = "<previous-head-hex>"
branch_labels = None
depends_on = None


TABLE_RENAMES = [
    ("tenants", "partners"),
    ("tenant_staff", "partner_staff"),
    ("tenant_authorizations", "partner_authorizations"),
    ("tenant_settings_audit", "partner_settings_audit"),
]

COLUMN_RENAMES = [
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

# Liệt kê cụ thể từ output của Step 1.1 (thay ... bằng list thực tế):
INDEX_RENAMES = [
    # ("old_name", "new_name")
    ("ix_memberships_tenant_id", "ix_memberships_partner_id"),
    ("ix_transactions_tenant_id", "ix_transactions_partner_id"),
    # ... (bổ sung theo discovery)
]

CONSTRAINT_RENAMES = [
    # ("table_after_rename", "old_conname", "new_conname")
    ("memberships",  "uq_memberships_tenant_user",         "uq_memberships_partner_user"),
    ("memberships",  "fk_memberships_tenant_id_tenants",   "fk_memberships_partner_id_partners"),
    # ... (bổ sung theo discovery)
]

SEQUENCE_RENAMES = [
    ("tenants_id_seq",                "partners_id_seq"),
    ("tenant_staff_id_seq",           "partner_staff_id_seq"),
    ("tenant_authorizations_id_seq",  "partner_authorizations_id_seq"),
    ("tenant_settings_audit_id_seq",  "partner_settings_audit_id_seq"),
]


def upgrade() -> None:
    # Prevent hang do concurrent session giữ AccessExclusiveLock:
    op.execute("SET lock_timeout = '10s'")

    # 1. Rename bảng
    for old, new in TABLE_RENAMES:
        op.rename_table(old, new)

    # 2. Rename cột FK
    for table, old_col, new_col in COLUMN_RENAMES:
        op.alter_column(table, old_col, new_column_name=new_col)

    # 3. Rename index
    for old, new in INDEX_RENAMES:
        op.execute(f"ALTER INDEX IF EXISTS {old} RENAME TO {new}")

    # 4. Rename constraint
    for table, old, new in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old} TO {new}")

    # 5. Rename sequence
    for old, new in SEQUENCE_RENAMES:
        op.execute(f"ALTER SEQUENCE IF EXISTS {old} RENAME TO {new}")


def downgrade() -> None:
    op.execute("SET lock_timeout = '10s'")

    # Reverse order
    for old, new in SEQUENCE_RENAMES:
        op.execute(f"ALTER SEQUENCE IF EXISTS {new} RENAME TO {old}")

    for table, old, new in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new} TO {old}")

    for old, new in INDEX_RENAMES:
        op.execute(f"ALTER INDEX IF EXISTS {new} RENAME TO {old}")

    for table, old_col, new_col in COLUMN_RENAMES:
        op.alter_column(table, new_col, new_column_name=old_col)

    # Bảng rename ngược cuối cùng (FK đã theo tên mới → cần rename bảng về cũ cuối)
    for old, new in TABLE_RENAMES:
        op.rename_table(new, old)
```

**Không forget:** fill `INDEX_RENAMES` + `CONSTRAINT_RENAMES` từ discovery Step 1.1. Nếu để placeholder thì Phase 5 `alembic upgrade head` sẽ skip rename → ORM reflect sau rename table sẽ fail.

### Step 1.4 — Verify migration file syntactically valid

- [ ] Chạy trong container backend (chưa apply, chỉ parse):

```bash
docker exec loyalty-backend-prod alembic check
```

**Expected:** Output `No new upgrade operations detected.` (hoặc tương tự, không raise Python syntax error).

Nếu lỗi import — check hex id format, string quoting, typo table name.

### Step 1.5 — Commit

- [ ] Commit phase 1:

```bash
rtk git add backend/alembic/versions/<new-hex>_rename_tenant_to_partner.py
rtk git commit -m "chore(db): alembic revision rename tenants→partners (chưa apply)"
```

---

## Phase 2 — Backend models + enums + FK columns

**Goal:** Rename 4 file model, đổi class + enum + `__tablename__` + 15 cột FK `tenant_id` → `partner_id`. Đây là bước rộng nhất backend nhưng thuần rename.

**Files:** xem 1.1 (models) + 1.2 (models bulk update).

**Acceptance:** Sau phase này, unit test model-level + service test không đụng DB pass. Integration test chưa pass (route vẫn trỏ tên cũ, Phase 3-4 sẽ fix).

### Step 2.1 — Rename 4 model file + update class/enum/tablename

- [ ] `backend/app/models/tenant.py` → `partner.py`:

```bash
git mv backend/app/models/tenant.py backend/app/models/partner.py
```

Mở file, thay đổi:
- `class Tenant(Base, TimestampMixin):` → `class Partner(Base, TimestampMixin):`
- `__tablename__ = "tenants"` → `__tablename__ = "partners"`
- `class TenantStatus(str, Enum):` → `class PartnerStatus(str, Enum):`
- `class TenantCategory(str, Enum):` → `class PartnerCategory(str, Enum):`
- Mọi docstring / comment `tenant` → `partner`, `Tenant` → `Partner`, `"tenant"` → `"partner"` (giữ string `"đối tác"` trong comment VN).

- [ ] `backend/app/models/tenant_staff.py` → `partner_staff.py`:

```bash
git mv backend/app/models/tenant_staff.py backend/app/models/partner_staff.py
```

Update trong file:
- `class TenantStaff(Base, TimestampMixin):` → `class PartnerStaff(...)`
- `__tablename__ = "tenant_staff"` → `"partner_staff"`
- `class TenantStaffRole(str, Enum):` → `PartnerStaffRole`
- Cột `tenant_id: Mapped[int] = mapped_column(..., ForeignKey("tenants.id"), ...)` → `partner_id: Mapped[int] = mapped_column(..., ForeignKey("partners.id"), ...)`
- Relationship `tenant: Mapped["Tenant"] = relationship(...)` → `partner: Mapped["Partner"] = relationship(...)` (và back_populates update tương ứng trong `partner.py`).
- Unique constraint tên: đổi `"uq_tenant_staff_*"` → `"uq_partner_staff_*"` nếu có.

- [ ] `backend/app/models/tenant_authorization.py` → `partner_authorization.py`: tương tự, class `TenantAuthorization` → `PartnerAuthorization`.

- [ ] `backend/app/models/tenant_settings_audit.py` → `partner_settings_audit.py`: class `TenantSettingsAudit` → `PartnerSettingsAudit`.

### Step 2.2 — Update `backend/app/models/__init__.py`

- [ ] Mở file, thay toàn bộ import `tenant*` → `partner*`:

```python
from app.models.partner import (
    Partner, PartnerStatus, PartnerCategory,
)
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.partner_authorization import (
    AuthorizationScope, SignatureMethod, PartnerAuthorization,
)
from app.models.partner_settings_audit import PartnerSettingsAudit
# ... các import khác giữ nguyên ...

__all__ = [
    "User", "Partner", "PartnerStatus", "PartnerStaff", "PartnerStaffRole",
    "Tier", "PointRule", "PartnerSettingsAudit",
    "VerificationCode", "VerificationCodePurpose",
    "Membership", "Transaction", "TransactionMethod",
    "PointLedger", "LedgerReason", "LedgerRefType",
    "Reward", "Redemption", "RedemptionStatus",
    "Campaign", "CampaignSource", "DiscountType",
    "ApprovalStatus", "ApprovalTier", "ServiceFeeStatus",
    "CampaignTemplate", "ProgramForm",
    "CampaignIssuance", "IssueMode",
    "CampaignRegulatorySubmission", "RegulatoryDocType",
    "CampaignApprovalEvent", "ApprovalEventType",
    "PartnerAuthorization", "AuthorizationScope", "SignatureMethod",
    "CampaignServiceFee", "FeeType", "FeeStatus", "EInvoiceProvider",
    "CampaignFeeSchedule",
    "Voucher", "VoucherStatus", "IssueSource", "Notification",
]
```

Lưu ý: cột `PartnerCategory` có export không — check file model gốc. Nếu có, thêm vào `__all__`.

### Step 2.3 — Update 12 model còn lại (cột FK `tenant_id` → `partner_id`)

Danh sách 12 model có cột `tenant_id` (spec 4.2):

- [ ] Với mỗi file trong danh sách:
  - `backend/app/models/membership.py`
  - `backend/app/models/transaction.py`
  - `backend/app/models/point_ledger.py`
  - `backend/app/models/point_rule.py`
  - `backend/app/models/tier.py`
  - `backend/app/models/reward.py`
  - `backend/app/models/redemption.py`
  - `backend/app/models/voucher.py`
  - `backend/app/models/campaign.py`
  - `backend/app/models/campaign_issuance.py`
  - `backend/app/models/campaign_service_fee.py`
  - `backend/app/models/notification.py`

Thay đổi trong mỗi file:
- Cột `tenant_id: Mapped[int] = mapped_column(..., ForeignKey("tenants.id"), ...)` → `partner_id: Mapped[int] = mapped_column(..., ForeignKey("partners.id"), ...)`.
- Relationship `tenant: Mapped["Tenant"] = relationship(...)` → `partner: Mapped["Partner"] = relationship(...)`; update `back_populates` nếu dùng.
- Unique constraint tên: `"uq_<table>_tenant_*"` → `"uq_<table>_partner_*"` (phải khớp với discovery Phase 1 để constraint rename migration + ORM khai báo match).
- Index tên: `"ix_<table>_tenant_id"` → `"ix_<table>_partner_id"` nếu có khai báo ORM-side (phần lớn ở `voucher.py` + `membership.py` có).
- Import `from app.models.tenant import Tenant` → `from app.models.partner import Partner`.

**Verify mỗi file xong:** `rtk grep -n "tenant" backend/app/models/<file>.py` phải rỗng (trừ comment có "đối tác" tiếng Việt).

### Step 2.4 — Verify toàn bộ models không còn reference tenant

- [ ] Chạy:

```bash
rtk grep -rn "tenant\|Tenant" D:/DoAn/backend/app/models/ --glob='*.py'
```

**Expected:** 0 match. Nếu còn — sửa tiếp.

### Step 2.5 — Apply migration local + chạy model-level test

- [ ] Apply migration Phase 1 lên dev DB để models load được (bảng đã rename):

```bash
docker exec loyalty-backend-prod alembic upgrade head
```

**Expected:** Output `Running upgrade <prev> -> <new>, rename tenant to partner`. Nếu lỗi `relation "tenants" does not exist` → migration chạy trước khi model rename, nhưng Phase này model rename rồi nên không sao. Nếu lỗi `column "tenant_id" already renamed` → rollback: `alembic downgrade -1` rồi re-run.

- [ ] Chạy model-level test — verify SA mapping:

```bash
docker exec loyalty-backend-prod pytest backend/tests/unit/test_partner_cache.py -v
# Nếu file chưa rename, skip; sẽ rename ở Phase 3.
```

### Step 2.6 — Commit Phase 2

- [ ] Commit:

```bash
rtk git add backend/app/models/
rtk git commit -m "refactor(backend-models): Tenant→Partner + tenant_id→partner_id cột FK"
```

---

## Phase 3 — Backend services + schemas + core/deps + main + seed + jobs

**Goal:** Rename toàn bộ layer service + schemas + core + main.py + jobs + seed. Sau phase này, backend code không còn từ `tenant`/`merchant`/`Tenant`/`Merchant`/`TenantStaff` etc ngoại trừ trong `alembic/versions/` history.

**Files:** xem 1.1 (services + schemas + tenant_cache) + 1.2 (core, main, seed, jobs).

**Acceptance:**
- Unit test suite pass: `pytest tests/unit -v`.
- Grep: `rtk grep -rn "\btenant\b\|\bTenant\b\|\bmerchant\b\|\bMerchant\b" backend/app/services backend/app/schemas backend/app/core backend/app/jobs backend/app/main.py backend/seed_demo.py --glob='*.py'` = 0 match.

### Step 3.1 — Rename 3 service file + class + error

- [ ] `backend/app/services/tenant_service.py` → `partner_service.py`:

```bash
git mv backend/app/services/tenant_service.py backend/app/services/partner_service.py
```

Update nội dung:
- `class TenantService:` → `class PartnerService:`
- `class TenantNotFoundError(Exception):` → `class PartnerNotFoundError(Exception):` (nếu error khai báo trong file này, thường là vậy).
- Method: `create_tenant` → `create_partner`, `get_tenant_by_id` → `get_partner_by_id`, `list_tenants` → `list_partners`, `get_tenant_by_slug` → `get_partner_by_slug`, etc.
- Param: `tenant_id: int` → `partner_id: int`.
- Import: `from app.models.tenant import Tenant, TenantStatus` → `from app.models.partner import Partner, PartnerStatus`.
- Docstring + comment sweep tiếng Việt: "tenant"/"shop" → "đối tác" nếu phù hợp context.

- [ ] `backend/app/services/tenant_staff_service.py` → `partner_staff_service.py` + class + ref.
- [ ] `backend/app/services/tenant_authorization_service.py` → `partner_authorization_service.py` + class.

### Step 3.2 — Update các service khác reference tenant

Danh sách 17 service khác trong `backend/app/services/`:

- [ ] Với mỗi file `{member,transaction,voucher,campaign,campaign_approval,campaign_enrollment,campaign_fee,campaign_template,point_rule,redemption,reward,tier,settings,analytics,qr,notification,ledger}_service.py`:

Grep file để tìm reference:

```bash
rtk grep -n "tenant\|Tenant" backend/app/services/<file>_service.py
```

Sửa theo pattern:
- Import `from app.models.tenant import Tenant, TenantStatus` → `from app.models.partner import Partner, PartnerStatus`.
- Import `from app.services.tenant_service import TenantService, TenantNotFoundError` → `from app.services.partner_service import PartnerService, PartnerNotFoundError`.
- Import `from app.models.tenant_staff import TenantStaff, TenantStaffRole` → `from app.models.partner_staff import PartnerStaff, PartnerStaffRole`.
- Method param `tenant_id: int` → `partner_id: int`.
- Model reference `Tenant(...)` → `Partner(...)`, `TenantStatus.ACTIVE` → `PartnerStatus.ACTIVE`.
- `Membership.tenant_id` → `Membership.partner_id`, `Voucher.tenant_id` → `Voucher.partner_id`, tương tự cho các model khác.
- Raise `TenantNotFoundError` → `PartnerNotFoundError`.
- Method tên: nếu có `tenant_id=` trong call signature → `partner_id=`.
- Log message: `"tenant"` → `"partner"` / `"đối tác"` (tiếng Việt phù hợp).

**Đặc biệt `member_service.py`**: method `find_or_create_member(tenant_id, phone)` → `find_or_create_member(partner_id, phone)`. Caller là POS `transaction_service.py` — đi qua cùng lượt update.

### Step 3.3 — Rename 3 schema file + class + field

- [ ] `backend/app/schemas/tenant.py` → `partner.py`:

```bash
git mv backend/app/schemas/tenant.py backend/app/schemas/partner.py
```

Update:
- `class TenantCreate(BaseModel):` → `PartnerCreate`
- `class TenantRead(BaseModel):` → `PartnerRead`
- `class TenantSummary(BaseModel):` → `PartnerSummary`
- `class TenantUpdate(BaseModel):` → `PartnerUpdate`
- `class TenantApprove(BaseModel):` → `PartnerApprove` (nếu có)
- `class TenantSuspend(BaseModel):` → `PartnerSuspend`
- Field `tenant_id: int` → `partner_id: int` (nếu schema có).

- [ ] `tenant_staff.py` → `partner_staff.py` + classes.
- [ ] `tenant_authorization.py` → `partner_authorization.py` + classes.

### Step 3.4 — Update các schema khác

Danh sách schema còn có `tenant_id`: grep để biết chính xác:

```bash
rtk grep -rln "tenant_id\|Tenant" D:/DoAn/backend/app/schemas/ --glob='*.py'
```

- [ ] Với mỗi file: đổi field `tenant_id: int` → `partner_id: int`, import tương ứng.

Khả năng cao cần sửa: `member.py`, `transaction.py`, `voucher.py`, `campaign.py`, `tier.py`, `reward.py`, `redemption.py`, `point_rule.py`, `settings.py`, `notification.py`, `ledger.py`.

### Step 3.5 — Rename `tenant_cache.py` → `partner_cache.py`

- [ ] Rename file:

```bash
git mv backend/app/core/tenant_cache.py backend/app/core/partner_cache.py
```

Update nội dung file (xem `backend/app/core/tenant_cache.py` 44 dòng):
- `class TenantRoleCache:` → `class PartnerRoleCache:`
- Parameter method: `tenant_id` → `partner_id` trong `_key()`, `get()`, `set()`, `invalidate()`.
- Key tuple: `(user_id, tenant_id)` → `(user_id, partner_id)` — giữ format, chỉ đổi tên.
- Docstring `tenant` → `partner`.
- Singleton `tenant_role_cache = TenantRoleCache(maxsize=1024, ttl=60)` → `partner_role_cache = PartnerRoleCache(maxsize=1024, ttl=60)`.

### Step 3.6 — Update `backend/app/core/deps.py`

File này có 8 chỗ đụng tenant. Mở file, thay:

- [ ] Function `extract_tenant_id_from_header(x_tenant_id: str | None) -> int:` → `extract_partner_id_from_header(x_partner_id: str | None) -> int:`. Inside:
  - Detail text `"Missing X-Tenant-Id header"` → `"Missing X-Partner-Id header"`.
  - Detail text `"X-Tenant-Id must be a positive integer"` → `"X-Partner-Id must be a positive integer"`.
  - Variable local `tenant_id` → `partner_id`.
- [ ] `async def get_tenant_id(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"))` → `async def get_partner_id(x_partner_id: str | None = Header(default=None, alias="X-Partner-Id"))`.
- [ ] `async def get_verified_tenant_id(tenant_id: int = Depends(get_tenant_id), ...) -> int:` → `async def get_verified_partner_id(partner_id: int = Depends(get_partner_id), ...) -> int:`. Inside: `from app.models.tenant import Tenant, TenantStatus` → `from app.models.partner import Partner, PartnerStatus`. Detail `"Tenant not found"` → `"Partner not found"`, `"Tenant is {status}, not active"` → `"Partner is {status}, not active"`.
- [ ] `async def get_current_tenant_role(...)` → `async def get_current_partner_role(...)`. Inside: import cache `from app.core.tenant_cache import tenant_role_cache` → `from app.core.partner_cache import partner_role_cache`. Model import `from app.models.tenant_staff import TenantStaff, TenantStaffRole` → `from app.models.partner_staff import PartnerStaff, PartnerStaffRole`. Cache call + DB query đổi `tenant_id=tenant_id` → `partner_id=partner_id`. Detail `"Access denied for this tenant"` → `"Access denied for this partner"`.
- [ ] `async def require_staff_in_tenant(...)` → `async def require_staff_in_partner(...)`.
- [ ] `async def require_owner_in_tenant(...)` → `async def require_owner_in_partner(...)`. Inside: `from app.models.tenant_staff import TenantStaffRole` → `from app.models.partner_staff import PartnerStaffRole`; `if role != TenantStaffRole.OWNER` → `PartnerStaffRole.OWNER`.
- [ ] `async def require_customer_in_tenant(...)` → `async def require_customer_in_partner(...)`. Inside: `Membership.tenant_id == tenant_id` → `Membership.partner_id == partner_id`. Detail `"Not a member of this tenant"` → `"Not a member of this partner"`.
- [ ] Comment/docstring sweep: `"tenant"` → `"partner"`.

### Step 3.7 — Update `backend/app/main.py`

File 130 dòng (xem Read ở session trước). Thay:

- [ ] Imports:
```python
from app.api.tenant_authorization import router as tenant_authorization_router
from app.api.tenant_staff import router as tenant_staff_router
from app.api.tenants import merchant_router, tenants_router, users_router
```
→
```python
from app.api.partner_authorization import router as partner_authorization_router
from app.api.partner_staff import router as partner_staff_router
from app.api.partners import partner_router, partners_router, users_router
```

- [ ] `app.add_middleware(CORSMiddleware, ..., allow_headers=[..., "X-Tenant-Id"])` → `..., "X-Partner-Id"]`.

- [ ] Global IntegrityError handler (dòng 99-118):
  - `elif "tenant_user" in msg_low or "tenant_staff" in msg_low:` → `elif "partner_user" in msg_low or "partner_staff" in msg_low:`
  - `detail = "User đã thuộc tenant này"` → `detail = "User đã thuộc đối tác này"`

- [ ] Router include:
```python
app.include_router(merchant_router)   # → partner_router
app.include_router(tenants_router)    # → partners_router
app.include_router(tenant_staff_router)         # → partner_staff_router
app.include_router(tenant_authorization_router) # → partner_authorization_router
```

### Step 3.8 — Update `backend/app/core/limiter.py` + `config.py`

- [ ] `limiter.py`: verified trong spec là không có tenant reference. Chỉ grep sweep comment — nếu có "tenant" trong comment/docstring → đổi "partner"/"đối tác". Không đụng code.

- [ ] `config.py`: verified không có `TENANT_*` env var. Grep sweep comment.

### Step 3.9 — Update `backend/seed_demo.py`

- [ ] Grep file:

```bash
rtk grep -n "tenant\|Tenant" backend/seed_demo.py
```

Thay đổi:
- `from app.models import Tenant, TenantStatus, TenantStaff, TenantStaffRole` → `Partner, PartnerStatus, PartnerStaff, PartnerStaffRole`.
- `Tenant(name="Cafe Cộng", ...)` → `Partner(name="Cafe Cộng", ...)` (giữ tiếng Việt data copy).
- `TenantStaff(tenant_id=t.id, user_id=u.id, role=TenantStaffRole.OWNER)` → `PartnerStaff(partner_id=p.id, user_id=u.id, role=PartnerStaffRole.OWNER)`.
- Variable tên local `tenant1`, `tenant2` → `partner1`, `partner2` (tuỳ style — không bắt buộc, nhưng clean).
- Mọi `tenant_id=` trong `Membership()`, `Transaction()`, `Voucher()`, `Campaign()` etc → `partner_id=`.

### Step 3.10 — Update `backend/app/jobs/*.py`

- [ ] Grep sweep:

```bash
rtk grep -rn "tenant\|Tenant" backend/app/jobs/ --glob='*.py'
```

Thường có file `birthday_voucher_job.py` hoặc tương tự. Đổi:
- `Membership.tenant_id` → `Membership.partner_id`.
- `Tenant.status == TenantStatus.ACTIVE` → `Partner.status == PartnerStatus.ACTIVE`.
- Import + docstring.

File `scheduler.py` có khả năng không đụng — chỉ wire up jobs. Grep để chắc.

### Step 3.11 — Verify + chạy unit test

- [ ] Grep backend core/services/schemas/main/jobs/seed sạch:

```bash
rtk grep -rn "\btenant\b\|\bTenant\b\|\bTenantStaff\b\|\bTenantStatus\b\|\bTenantService\b\|\btenant_id\b\|\btenant_role_cache\b" D:/DoAn/backend/app/services D:/DoAn/backend/app/schemas D:/DoAn/backend/app/core D:/DoAn/backend/app/jobs D:/DoAn/backend/app/main.py D:/DoAn/backend/seed_demo.py --glob='*.py'
```

**Expected:** 0 match. Nếu còn hit → fix tiếp.

- [ ] Chạy unit test (CHƯA bao gồm integration — phase 4 mới có):

```bash
docker exec loyalty-backend-prod pytest backend/tests/unit -v
```

**Expected:** toàn bộ unit test pass. Nếu fail:
- `ImportError: cannot import name 'TenantService'` → còn file test ref tên cũ, rename ở phase 2 test sweep.
- `AttributeError: 'Membership' object has no attribute 'tenant_id'` → còn fixture ref cũ.

Fix từng cái, grep rộng hơn nếu cần.

### Step 3.12 — Commit Phase 3

- [ ] Commit:

```bash
rtk git add backend/app/services/ backend/app/schemas/ backend/app/core/ backend/app/main.py backend/app/jobs/ backend/seed_demo.py
rtk git commit -m "refactor(backend-core): rename service/schema/deps/cache Tenant→Partner"
```

---

## Phase 4 — Backend API routes + routers + header + endpoint mới

**Goal:** Rename route prefix `/merchant/*` → `/partner/*`, `/tenants/*` → `/partners/*`; rename header `X-Tenant-Id` → `X-Partner-Id`; thêm endpoint mới `GET /users/me/partners/{slug}` + query param `?partner_slug=` cho `/users/me/ledger`; rename `/users/me/shops` → `/users/me/partners` + shrink response.

**Files:** xem 1.1 (api renames) + 1.2 (api bulk update).

**Acceptance:** Integration test suite pass `pytest tests/integration -v`; endpoint mới có test coverage.

### Step 4.1 — Rename 3 API file

- [ ] `backend/app/api/tenants.py` → `partners.py`:

```bash
git mv backend/app/api/tenants.py backend/app/api/partners.py
```

Update:
- Router definitions (xem file gốc dòng 34-36):
  ```python
  merchant_router = APIRouter(prefix="/merchant", tags=["merchant"])
  tenants_router  = APIRouter(prefix="/tenants", tags=["tenants"])
  users_router    = APIRouter(prefix="/users", tags=["users"])
  ```
  →
  ```python
  partner_router  = APIRouter(prefix="/partner",  tags=["partner"])
  partners_router = APIRouter(prefix="/partners", tags=["partners"])
  users_router    = APIRouter(prefix="/users",    tags=["users"])
  ```
- Imports: `TenantService`, `TenantNotFoundError`, `Tenant`, `TenantStatus` → `Partner*`.
- Deps import: `from app.core.deps import get_tenant_id, require_staff_in_tenant, require_owner_in_tenant, get_verified_tenant_id, get_current_tenant_role, require_customer_in_tenant` → `get_partner_id, require_staff_in_partner, require_owner_in_partner, get_verified_partner_id, get_current_partner_role, require_customer_in_partner`.
- Endpoint decorator:
  - `@merchant_router.get(...)` → `@partner_router.get(...)` (staff/owner dashboard endpoints).
  - `@tenants_router.get(...)` → `@partners_router.get(...)`.
- Endpoint path: đặc biệt `@users_router.get("/me/shops")` → `@users_router.get("/me/partners")`. `@users_router.get("/me/tenants")` (cho staff list partner-của-mình) → `@users_router.get("/me/partners-as-staff")` (đổi tên rõ ràng tránh collision với `/me/partners` cho customer).
- Function name: `get_my_shops` → `get_my_partners`, `get_my_tenants` → `get_my_partners_as_staff`, tương tự cho các endpoint khác.

- [ ] `backend/app/api/tenant_staff.py` → `partner_staff.py`:

```bash
git mv backend/app/api/tenant_staff.py backend/app/api/partner_staff.py
```

Update: router prefix (nếu `APIRouter(prefix="/tenant-staff")` → `/partner-staff`), import, function tên, tag.

- [ ] `backend/app/api/tenant_authorization.py` → `partner_authorization.py`: tương tự.

### Step 4.2 — Update 15 API file còn lại

Danh sách 15 file `backend/app/api/{admin,admin_campaigns,analytics,auth,campaign_enrollment,campaigns,members,notifications,point_rules,qr,redemptions,rewards,settings,tiers,transactions,vouchers}.py`.

- [ ] Với mỗi file:

```bash
rtk grep -n "tenant\|Tenant\|merchant\|/tenants\|/merchant" backend/app/api/<file>.py
```

Sửa:
- Import `from app.core.deps import get_tenant_id, ...` → `get_partner_id, ...`.
- Import `from app.services.tenant_service import TenantService` → `partner_service → PartnerService`.
- Import model.
- Route prefix: nếu `APIRouter(prefix="/merchant/...")` → `/partner/...`.
- Function param: `tenant_id: int = Depends(get_tenant_id)` → `partner_id: int = Depends(get_partner_id)`.
- Model query: `Membership.tenant_id == tenant_id` → `Membership.partner_id == partner_id`, tương tự tất cả model.
- Docstring + log sweep.

**Đặc biệt `admin.py`**: có endpoint list tenants cho super_admin. Đổi `@admin_router.get("/tenants")` → `@admin_router.get("/partners")`, function `list_all_tenants` → `list_all_partners`. Ngoài ra, check các admin endpoints liên quan tenant approve/suspend — đổi naming tương ứng.

### Step 4.3 — Cải thiện response shape `/users/me/partners`

Per spec 5.3:

- [ ] Trong `backend/app/api/partners.py`, tìm endpoint GET `/users/me/partners` (hoặc handler `get_my_partners`):

Hiện tại (trước rename shop → partner) response trả schema có `is_member`, `points_balance`, `tier_name`. Sau rename, **drop** các field này để simplify UX list. Sửa:

```python
# Trước:
class MyShopItem(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: str | None
    logo_url: str | None
    is_member: bool
    points_balance: int
    tier_name: str | None

# Sau:
class MyPartnerSummary(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: str | None
    logo_url: str | None
```

(Tên schema có thể để trong `backend/app/schemas/partner.py` — xem Step 3.3.)

- [ ] Endpoint code chỉ query + map: không cần join `memberships` nữa. Query đơn giản `SELECT FROM partners WHERE status='active' ORDER BY name`. Nếu có search/filter category thì giữ.

### Step 4.4 — Thêm endpoint mới `GET /users/me/partners/{slug}`

Per spec 5.3:

- [ ] Trong `partners.py`, thêm handler + schema:

```python
# schemas/partner.py:
class PartnerDetailForMember(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: str | None
    logo_url: str | None
    contact_phone: str | None
    contact_email: str | None
    address: str | None
    business_hours: str | None
    website: str | None
    tax_code: str | None
    points_balance: int | None  # None nếu chưa có membership
    total_points_earned: int | None
    current_tier_name: str | None
    joined_at: datetime | None
    last_activity_at: datetime | None

# api/partners.py:
@users_router.get("/me/partners/{slug}", response_model=PartnerDetailForMember)
async def get_my_partner_detail(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PartnerDetailForMember:
    """Detail 1 partner + state user tại đó (null nếu chưa giao dịch)."""
    partner = await db.scalar(select(Partner).where(Partner.slug == slug, Partner.status == PartnerStatus.ACTIVE))
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")

    membership = await db.scalar(
        select(Membership).where(
            Membership.partner_id == partner.id,
            Membership.user_id == user.id,
        )
    )
    tier_name = None
    if membership and membership.current_tier_id:
        tier = await db.get(Tier, membership.current_tier_id)
        tier_name = tier.name if tier else None

    return PartnerDetailForMember(
        id=partner.id,
        slug=partner.slug,
        name=partner.name,
        category=partner.category,
        description=partner.description,
        logo_url=partner.logo_url,
        contact_phone=partner.contact_phone,
        contact_email=partner.contact_email,
        address=partner.address,
        business_hours=partner.business_hours,
        website=partner.website,
        tax_code=partner.tax_code,
        points_balance=(membership.points_balance if membership else None),
        total_points_earned=(membership.total_points_earned if membership else None),
        current_tier_name=tier_name,
        joined_at=(membership.created_at if membership else None),
        last_activity_at=(membership.updated_at if membership else None),
    )
```

Lưu ý: tên field `total_points_earned`, `current_tier_id`, `points_balance` phải khớp schema `Membership` thực tế. Check `backend/app/models/membership.py` trước khi copy. Nếu tên khác → adjust.

### Step 4.5 — Thêm query param `?partner_slug=` cho `/users/me/ledger`

Per spec 5.3 — **giữ flat response shape** của endpoint hiện tại (`list[LedgerEntryResponse]`), chỉ thêm filter optional.

**Fact về endpoint hiện tại** (đọc `backend/app/api/tenants.py:68-103` trước khi sửa):
- Response: `list[LedgerEntryResponse]` — flat, **không wrapped** `{items, total, limit, offset}`.
- Filter theo user: `PointLedger.membership_id.in_(subquery membership)` — **KHÔNG có `PointLedger.user_id`** (cột không tồn tại; model chỉ có `id, tenant_id, membership_id, delta, reason, ref_type, ref_id, balance_after, description, created_at, updated_at`).
- Spec §5.3 chỉ yêu cầu thêm filter, không đổi shape → **giữ flat**.

- [ ] Mở `backend/app/api/partners.py` (đã rename từ `tenants.py` ở Step 4.1), cập nhật handler `list_my_ledger` thành:

```python
@users_router.get("/me/ledger", response_model=list[LedgerEntryResponse])
async def list_my_ledger(
    user: User = Depends(get_current_user),
    partner_slug: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    """Lịch sử tích điểm của current user, optional filter theo 1 partner."""
    # Subquery membership — filter theo partner nếu có slug
    membership_stmt = select(Membership.id).where(
        Membership.user_id == user.id,
        Membership.archived_at.is_(None),
    )
    if partner_slug is not None:
        partner_id_scalar = await db.scalar(
            select(Partner.id).where(Partner.slug == partner_slug)
        )
        if partner_id_scalar is None:
            raise HTTPException(status_code=404, detail="Partner not found")
        membership_stmt = membership_stmt.where(Membership.partner_id == partner_id_scalar)

    membership_ids = [row for row in (await db.scalars(membership_stmt)).all()]
    if not membership_ids:
        return []

    rows = (
        await db.scalars(
            select(PointLedger)
            .where(PointLedger.membership_id.in_(membership_ids))
            .order_by(PointLedger.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [LedgerEntryResponse.model_validate(r) for r in rows]
```

**Chú ý**:
- Giữ nguyên `response_model=list[LedgerEntryResponse]` — không đổi schema.
- Không thêm class `LedgerListResponse` (không có trong `backend/app/schemas/`).
- Nếu filter theo `partner_slug` mà user chưa có membership ở partner đó → `membership_ids` rỗng → trả `[]`.
- Caller frontend đang tiêu thụ flat (`/member/history/page.tsx` + `api.ts`) → không break.

### Step 4.6 — Viết test cho endpoint mới

Phase này **TDD**:

- [ ] Viết test trước (failing):

```python
# backend/tests/integration/test_customer_partner_listing.py (NEW)
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_my_partners_list_shape_shrink(client: AsyncClient, customer_token: str):
    """GET /users/me/partners không có is_member, points_balance, tier_name."""
    resp = await client.get(
        "/users/me/partners",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    first = items[0]
    # Expected keys
    assert set(first.keys()) >= {"id", "slug", "name", "category"}
    # Must NOT have these
    assert "is_member" not in first
    assert "points_balance" not in first
    assert "tier_name" not in first


@pytest.mark.asyncio
async def test_my_partner_detail_with_membership(client: AsyncClient, customer_token: str, partner_with_membership):
    """GET /users/me/partners/{slug} trả points_balance, tier khi có membership."""
    slug = partner_with_membership.slug
    resp = await client.get(
        f"/users/me/partners/{slug}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == slug
    assert data["points_balance"] is not None
    assert data["current_tier_name"] is not None


@pytest.mark.asyncio
async def test_my_partner_detail_without_membership(client: AsyncClient, customer_token: str, partner_no_membership):
    """GET /users/me/partners/{slug} trả null khi chưa có giao dịch."""
    slug = partner_no_membership.slug
    resp = await client.get(
        f"/users/me/partners/{slug}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["points_balance"] is None
    assert data["current_tier_name"] is None
    assert data["joined_at"] is None
```

```python
# backend/tests/integration/test_ledger_filter_by_partner.py (NEW)
@pytest.mark.asyncio
async def test_ledger_filter_by_partner_slug(client, customer_token, partner_a_with_ledger, partner_b_with_ledger):
    """GET /users/me/ledger?partner_slug=A chỉ trả entries của A."""
    resp = await client.get(
        f"/users/me/ledger?partner_slug={partner_a_with_ledger.slug}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    for item in items:
        assert item["partner_id"] == partner_a_with_ledger.id


@pytest.mark.asyncio
async def test_ledger_no_filter_returns_all(client, customer_token, partner_a_with_ledger, partner_b_with_ledger):
    resp = await client.get(
        "/users/me/ledger",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    items = resp.json()["items"]
    partner_ids = {item["partner_id"] for item in items}
    assert {partner_a_with_ledger.id, partner_b_with_ledger.id}.issubset(partner_ids)
```

Fixture `partner_with_membership`, `partner_no_membership`, `partner_a_with_ledger`, `partner_b_with_ledger` — nếu chưa có trong `conftest.py` thì thêm. Consult existing `conftest.py` style (xem `backend/tests/conftest.py`).

- [ ] Chạy để verify fail:

```bash
docker exec loyalty-backend-prod pytest backend/tests/integration/test_customer_partner_listing.py -v
```

**Expected:** FAIL (endpoint chưa implement hoặc response shape chưa shrink). Sau Step 4.3 + 4.4 thì PASS.

### Step 4.7 — Rename test file integration Tenant → Partner

- [ ] List test files:

```bash
rtk grep -rln "tenant\|Tenant" backend/tests/ --glob='*.py'
```

- [ ] Rename:
  - `test_tenant_api.py` → `test_partner_api.py`
  - `test_tenant_isolation.py` → `test_partner_isolation.py`
  - `test_tenant_service.py` (unit) → `test_partner_service.py` (đã làm ở Phase 3 nếu có)
  - `test_tenant_cache.py` → `test_partner_cache.py`

```bash
git mv backend/tests/integration/test_tenant_api.py backend/tests/integration/test_partner_api.py
git mv backend/tests/integration/test_tenant_isolation.py backend/tests/integration/test_partner_isolation.py
git mv backend/tests/unit/test_tenant_service.py backend/tests/unit/test_partner_service.py
git mv backend/tests/unit/test_tenant_cache.py backend/tests/unit/test_partner_cache.py
```

- [ ] Update content các file test (trong mọi file test):
  - Import `from app.models.tenant import Tenant` → `from app.models.partner import Partner`.
  - Fixture `tenant_id=` → `partner_id=`.
  - Header `"X-Tenant-Id": str(tenant.id)` → `"X-Partner-Id": str(partner.id)`.
  - URL `/merchant/*` → `/partner/*`, `/tenants/*` → `/partners/*`, `/users/me/shops` → `/users/me/partners`, `/users/me/tenants` → `/users/me/partners-as-staff`.
  - Function name `test_create_tenant` → `test_create_partner`, tương tự tất cả.
  - Assertion `resp.json()["tenant_id"]` → `resp.json()["partner_id"]`.

- [ ] Update `conftest.py`:

```bash
rtk grep -n "tenant\|Tenant" backend/tests/conftest.py
```

Fixture `tenant_factory` → `partner_factory`, `tenant_owner_token` → `partner_owner_token`, etc. Header chuẩn `X-Tenant-Id` → `X-Partner-Id`.

### Step 4.7b — Sweep nội dung TẤT CẢ test file (kể cả file không đổi tên)

**Why:** Step 4.7 chỉ đổi content 4 file được rename. Còn 20+ test file khác (`test_voucher_api.py`, `test_campaign_api.py`, `test_reward_api.py`, `test_membership_*.py`, `test_transaction_api.py`, ...) vẫn còn reference `Tenant`/`tenant_id`/`X-Tenant-Id` ở import / fixture / assertion. Quên sweep → test suite fail hàng loạt vì ImportError `app.models.tenant` không tồn tại.

- [ ] Grep toàn bộ test file còn reference:

```bash
rtk grep -rln "\bTenant\b\|\btenant_id\b\|\bTenantStaff\b\|\bTenantStatus\b\|X-Tenant-Id\|api.models.tenant\|app.services.tenant\|app.api.tenants\|/merchant\|/tenants" backend/tests/ --glob='*.py'
```

**Expected:** chỉ còn tên file nào, mở file đó đọc kỹ.

- [ ] Với MỖI file match, thay thế theo bảng:

| Pattern cũ | Pattern mới |
|---|---|
| `from app.models.tenant import Tenant` | `from app.models.partner import Partner` |
| `from app.services.tenant_service import TenantService` | `from app.services.partner_service import PartnerService` |
| `from app.schemas.tenant import ...` | `from app.schemas.partner import ...` |
| `from app.api.tenants import ...` | `from app.api.partners import ...` |
| `tenant_id=` | `partner_id=` |
| `tenant: Tenant` (type annotation) | `partner: Partner` |
| `"X-Tenant-Id": str(tenant.id)` | `"X-Partner-Id": str(partner.id)` |
| `resp.json()["tenant_id"]` | `resp.json()["partner_id"]` |
| `client.post("/merchant/...")` | `client.post("/partner/...")` |
| `client.get("/tenants/...")` | `client.get("/partners/...")` |
| `client.get("/users/me/shops")` | `client.get("/users/me/partners")` |
| `client.get("/users/me/tenants")` | `client.get("/users/me/partners-as-staff")` |

- [ ] Re-grep xác nhận 0 match:

```bash
rtk grep -rln "\bTenant\b\|\btenant_id\b\|\bTenantStaff\b\|\bTenantStatus\b\|X-Tenant-Id\|app.models.tenant\|app.services.tenant\|app.api.tenants\|/merchant\b\|/tenants\b" backend/tests/ --glob='*.py'
```

**Expected:** empty output (không file nào còn match).

### Step 4.8 — Chạy integration test suite

- [ ] Chạy toàn bộ:

```bash
docker exec loyalty-backend-prod pytest backend/tests/integration -v
```

**Expected:** tất cả pass. Fail thường gặp:
- `404 Not Found` cho `/partner/*` → main.py chưa include `partner_router` (recheck Step 3.7).
- `400 Missing X-Partner-Id header` ở test không gửi header → fix test fixture.
- `AttributeError: 'Membership' has no attribute 'tenant_id'` → còn file test ref cũ.

### Step 4.9 — Commit Phase 4

- [ ] Commit:

```bash
rtk git add backend/app/api/ backend/app/schemas/partner.py backend/tests/
rtk git commit -m "refactor(backend-api): route prefix /partner/* + endpoint detail + filter ledger"
```

---

## Phase 5 — Backend re-verify migration + full test + grep sạch

**Goal:** Sau khi Phase 2 đã apply migration (Step 2.5) và Phase 3–4 đổi code/test, re-verify toàn bộ backend rename xong: test pass, grep tenant/merchant = 0. **Không apply migration lại** — Phase 2 đã apply rồi; Step 5.1 chỉ là tuỳ chọn reset DB nếu state hỗn loạn.

**Acceptance:** Full `pytest -v` xanh + grep check = 0 match + (tuỳ chọn) reset + re-upgrade thành công.

### Step 5.1 — Reset DB + apply migration fresh (tuỳ chọn, nếu dev DB đã hỗn loạn)

- [ ] Nếu dev DB đã có state không đồng nhất từ debug trước, drop + recreate:

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec loyalty-backend-prod alembic upgrade head
docker exec loyalty-backend-prod python backend/seed_demo.py
```

### Step 5.2 — Chạy pytest toàn bộ

- [ ] 

```bash
docker exec loyalty-backend-prod pytest backend/tests -v --tb=short
```

**Expected:** 100% pass. Nếu còn fail — fix rồi lặp lại đến xanh.

### Step 5.3 — Grep sạch

- [ ] Backend grep toàn cục:

```bash
rtk grep -rn "\btenant\b\|\bTenant\b\|\bTenantStaff\b\|\bTenantStatus\b\|\bTenantService\b\|\btenant_id\b\|\btenant_role_cache\b\|\bTenantRoleCache\b\|merchant_router\|tenants_router" D:/DoAn/backend/app D:/DoAn/backend/tests D:/DoAn/backend/seed_demo.py --glob='*.py'
```

**Expected:** 0 match. Exception: `backend/alembic/versions/` giữ history — nhưng đã filter bằng `grep -v alembic/versions`.

- [ ] Backend `/merchant` path grep:

```bash
rtk grep -rn "/merchant\|/tenants" D:/DoAn/backend/app --glob='*.py'
```

**Expected:** 0 match (trừ comment nếu có).

- [ ] Backend `X-Tenant-Id` grep:

```bash
rtk grep -rn "X-Tenant-Id" D:/DoAn/backend
```

**Expected:** 0 match.

### Step 5.4 — Commit Phase 5

- [ ] Commit (có thể empty commit nếu Step 5.3 không sửa gì, nhưng thường vẫn có fix tail):

```bash
rtk git add backend/
rtk git commit -m "chore(backend): apply migration + verify grep sạch"
```

Nếu không có thay đổi → skip commit (Phase 5 chỉ là verify gate).

---

## Phase 6 — Frontend lib: store + types + api client + hooks + components

**Goal:** Rename tất cả non-page TypeScript file (lib, types, components) từ `merchant`/`tenant` → `partner`. Update axios interceptor + types + hooks. Không đụng route group hay customer UX (dành cho Phase 7, 8).

**Files:** xem 1.3 (frontend renames).

**Acceptance:** `npx tsc --noEmit` pass (có thể còn type error ở page/component chưa update — chấp nhận ở phase này, Phase 7-8 xử lý). Sau Phase 9 mới 0 error.

### Step 6.1 — Rename `tenant-store.ts` → `partner-store.ts`

- [ ] 

```bash
git mv frontend/src/lib/tenant-store.ts frontend/src/lib/partner-store.ts
```

Update nội dung file (xem file gốc — 40-50 dòng):
- Interface `Tenant` trong file → đã có type chuẩn ở `types/partner.ts` (rename ở Step 6.4); import từ đó.
- Hook `export const useTenantStore = create(...)` → `useParterStore` — à đánh máy: `usePartnerStore`.
- Store state: `activeTenant: Tenant | null` → `activePartner: Partner | null`.
- Store action: `setActiveTenant` → `setActivePartner`, `clearTenant` → `clearPartner`.
- `const STORAGE_KEY = "active_tenant"` → `"active_partner"`.
- `sessionStorage.getItem`, `setItem`, `removeItem` → giữ nguyên (vẫn là sessionStorage). Key chỉ đổi giá trị string.
- Helper `getActiveTenantId()` → `getActivePartnerId()`.

### Step 6.2 — Rename `api-merchant.ts` + `api-merchant-enroll.ts`

- [ ] 

```bash
git mv frontend/src/lib/api-merchant.ts frontend/src/lib/api-partner.ts
git mv frontend/src/lib/api-merchant-enroll.ts frontend/src/lib/api-partner-enroll.ts
```

Update nội dung:
- Import `Tenant`, `TenantStaff` → `Partner`, `PartnerStaff`.
- Function tên: `createTenantApi`, `listTenantsApi`, `getTenantApi`, `approveTenantApi`, `suspendTenantApi` → `*Partner*`.
- URL literal: `'/tenants'`, `'/merchant/...'`, `'/tenants/me'` → `/partners`, `/partner/...`, `/partners/me`.
- Tên hàm nhận param `tenantId` → `partnerId`.

### Step 6.3 — Rename `use-merchant.ts` + `use-merchant-enroll.ts` (hooks)

- [ ] 

```bash
git mv frontend/src/lib/hooks/use-merchant.ts frontend/src/lib/hooks/use-partner.ts
git mv frontend/src/lib/hooks/use-merchant-enroll.ts frontend/src/lib/hooks/use-partner-enroll.ts
```

Update:
- Hook name: `useMerchantList`, `useMerchantDashboard`, `useMerchantApprove` → `usePartnerList`, `usePartnerDashboard`, `usePartnerApprove`.
- Query key: `['tenant', id]` → `['partner', id]`, `['merchant', ...]` → `['partner', ...]`.
- Import API function đổi tên.

### Step 6.4 — Rename `types/merchant.ts` + `types/merchant-enroll.ts`

- [ ] 

```bash
git mv frontend/src/types/merchant.ts frontend/src/types/partner.ts
git mv frontend/src/types/merchant-enroll.ts frontend/src/types/partner-enroll.ts
```

Update:
- `interface Tenant { ... }` → `interface Partner { ... }`; field `tenant_id` → `partner_id` nếu có field này.
- `interface TenantItem { ... }` → `PartnerItem`.
- `interface TenantStaffRole { ... }` → `PartnerStaffRole`.
- `interface MerchantDashboard` → `PartnerDashboard` (nếu có).
- Export statement.

### Step 6.5 — Rename `components/merchant/` → `components/partner/`

- [ ] 

```bash
git mv frontend/src/components/merchant frontend/src/components/partner
git mv frontend/src/components/partner/tenant-picker.tsx frontend/src/components/partner/partner-picker.tsx
git mv frontend/src/components/partner/merchant-sidebar.tsx frontend/src/components/partner/partner-sidebar.tsx
```

Update nội dung component:
- `partner-picker.tsx`: `export function TenantPicker()` → `export function PartnerPicker()`. Label UI: "Chọn cửa hàng" → "Chọn đối tác". State hook `useTenantStore` → `usePartnerStore`.
- `partner-sidebar.tsx`: `export function MerchantSidebar()` → `export function PartnerSidebar()`. Link `/merchant/*` → `/partner/*`. Copy "Dashboard merchant" / "Trang chủ shop" → "Trang chủ đối tác".
- Các component nhỏ khác trong folder: grep + sweep.

### Step 6.6 — Update `lib/api.ts` (axios interceptor)

- [ ] Grep:

```bash
rtk grep -n "tenant\|Tenant\|merchant" D:/DoAn/frontend/src/lib/api.ts
```

**Fact về file hiện tại** (đọc `frontend/src/lib/api.ts:25-35` trước khi sửa):
- Interceptor có **2 branch** match URL: `url.startsWith("/merchant") || url.startsWith("/tenants/me")` (không phải 1 branch!).
- Check header key literal: `"X-Tenant-Id" in config.headers`.

Thay **đầy đủ 5 chỗ**:
- Import: `import { getActiveTenantId } from "@/lib/tenant-store"` → `import { getActivePartnerId } from "@/lib/partner-store"`.
- Rule match URL (2 prefix): `url.startsWith("/merchant") || url.startsWith("/tenants/me")` → `url.startsWith("/partner") || url.startsWith("/partners/me")`. **Phải đổi cả 2** — quên `/partners/me` sẽ làm endpoint owner-update-settings (spec §5.2) không được inject header → 400 Missing.
- Header key literal check: `"X-Tenant-Id" in config.headers` → `"X-Partner-Id" in config.headers`.
- Variable: `const tenantId = getActiveTenantId()` → `const partnerId = getActivePartnerId()`.
- Set header: `config.headers["X-Tenant-Id"] = String(tenantId)` → `config.headers["X-Partner-Id"] = String(partnerId)`.

Comment trên block: `// Auto-inject X-Tenant-Id cho /merchant/* và /tenants/me/* routes` → `// Auto-inject X-Partner-Id cho /partner/* và /partners/me/* routes`.

### Step 6.7 — Update `types/admin.ts`

- [ ] Grep:

```bash
rtk grep -n "tenant\|Tenant" D:/DoAn/frontend/src/types/admin.ts
```

Thay type `Tenant` references (VD `type AdminTenantItem`) → `AdminPartnerItem`. Field `tenant_id` → `partner_id`.

### Step 6.8 — Update all consumers (import path + hook name)

- [ ] Grep danh sách file import tên cũ:

```bash
rtk grep -rln "from '@/lib/tenant-store'\|from '@/lib/api-merchant'\|from '@/lib/hooks/use-merchant'\|from '@/types/merchant'\|from '@/components/merchant'" D:/DoAn/frontend/src --glob='*.{ts,tsx}'
```

- [ ] Với mỗi file:
  - Import path: `'@/lib/tenant-store'` → `'@/lib/partner-store'`, `'@/lib/api-merchant'` → `'@/lib/api-partner'`, etc.
  - Hook name: `useTenantStore` → `usePartnerStore`, `useMerchantList` → `usePartnerList`.
  - Type: `Tenant` → `Partner`, `TenantItem` → `PartnerItem`.
  - Variable: `activeTenant` → `activePartner`, `tenantId` → `partnerId` (cần context-aware — chỉ đổi tên biến, không đổi cú pháp JSX).

Số file ước lượng: ~12-18 file page + component.

### Step 6.9 — Verify type check (partial — sẽ còn error ở pages chưa update)

- [ ] 

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -40
```

**Expected:** Một số error còn lại là do page trong `(merchant)/` chưa rename (Phase 7). Không block. Các error như `Cannot find module '@/lib/tenant-store'` → đã fix ở bước 6.8. Nếu còn → grep sót.

### Step 6.10 — Commit Phase 6

- [ ] 

```bash
rtk git add frontend/src/lib/ frontend/src/types/ frontend/src/components/
rtk git commit -m "refactor(frontend-lib): rename tenant-store/api-merchant/types → partner"
```

---

## Phase 7 — Frontend route group `(merchant)` → `(partner)` + register partner

**Goal:** Move folder `(merchant)/merchant/*` → `(partner)/partner/*`. Rename `/register/merchant` → `/register/partner`. Update all internal Link/router.push ref cũ.

**Files:** 13 page trong `(merchant)/` + 1 layout + `(auth)/register/merchant/page.tsx` + các file có `/merchant/` hoặc `/tenants/` internal link.

**Acceptance:** `npm run build` pass, route `/partner/dashboard` render (smoke local).

### Step 7.1 — Move folder `(merchant)` → `(partner)` + subpath

- [ ] Đầu tiên create folder mới, move file:

```bash
git mv "frontend/src/app/(merchant)" "frontend/src/app/(partner)"
git mv "frontend/src/app/(partner)/merchant" "frontend/src/app/(partner)/partner"
```

(Trên bash Windows dùng quotes vì có ngoặc đơn.)

Nếu `git mv` không hoạt động với folder `(merchant)` (ngoặc), fallback:

```bash
mkdir -p "frontend/src/app/(partner)"
mv frontend/src/app/\(merchant\)/* "frontend/src/app/(partner)/"
rmdir frontend/src/app/\(merchant\)
mv "frontend/src/app/(partner)/merchant" "frontend/src/app/(partner)/partner"
git add -A frontend/src/app/
```

### Step 7.2 — Update layout + page content

- [ ] `frontend/src/app/(partner)/layout.tsx`:

Grep nội dung:
```bash
rtk grep -n "tenant\|Tenant\|merchant\|Merchant\|/merchant" D:/DoAn/frontend/src/app/\(partner\)/layout.tsx
```

Thay:
- Import `MerchantSidebar` → `PartnerSidebar` (đã rename ở Phase 6).
- Title "Merchant Dashboard" / "Trang chủ shop" → "Trang chủ đối tác".
- URL `/merchant/*` → `/partner/*`.
- `useTenantStore` → `usePartnerStore`.

- [ ] `frontend/src/app/(partner)/partner/page.tsx` (dashboard owner):
- Greeting "Chào {name}, chủ shop!" → "Chào {name}, chủ đối tác!".
- Copy "Shop của bạn" → "Đối tác của bạn".
- Any data field `tenant_id` → `partner_id`.
- Hook `useMerchantDashboard` → `usePartnerDashboard`.

- [ ] Các page khác trong `(partner)/partner/*/page.tsx`:

```bash
rtk grep -rln "tenant\|Tenant\|merchant\|Merchant" "D:/DoAn/frontend/src/app/(partner)" --glob='*.{ts,tsx}'
```

Với mỗi file — sweep symbol + URL + copy.

Danh sách:
- `partner/vouchers/page.tsx`
- `partner/staff/page.tsx`
- `partner/rewards/page.tsx`
- `partner/members/page.tsx`
- `partner/pos/transactions/new/page.tsx`
- `partner/settings/page.tsx`
- `partner/authorizations/page.tsx`
- `partner/authorizations/[id]/page.tsx`
- `partner/campaigns/page.tsx`
- `partner/campaigns/[id]/page.tsx`
- `partner/campaigns/enroll/page.tsx`

### Step 7.3 — Rename `/register/merchant` → `/register/partner`

- [ ] 

```bash
git mv "frontend/src/app/(auth)/register/merchant" "frontend/src/app/(auth)/register/partner"
```

- [ ] Update `frontend/src/app/(auth)/register/partner/page.tsx`:
- URL links / redirects: `router.push('/register/merchant')` → `'/register/partner'`.
- Heading: "Đăng ký doanh nghiệp" → "Đăng ký đối tác".
- Form labels: "Tên cửa hàng" → "Tên đối tác", "Loại cửa hàng" → "Loại hình đối tác".
- API call `createTenantApi()` → `createPartnerApi()` (đã rename ở Phase 6).
- Post-success redirect `/merchant/dashboard` → `/partner/dashboard`.

- [ ] `frontend/src/app/(auth)/login/page.tsx`: nếu có link "Đăng ký chủ shop" / "Đăng ký merchant" → "Đăng ký đối tác", URL → `/register/partner`.

### Step 7.4 — Update admin portal rename route

- [ ] `frontend/src/app/(admin)/admin/tenants/` → `frontend/src/app/(admin)/admin/partners/`:

```bash
git mv "frontend/src/app/(admin)/admin/tenants" "frontend/src/app/(admin)/admin/partners"
```

Update content: URL, title "Quản lý cửa hàng" → "Quản lý đối tác", API call, type.

### Step 7.5 — Grep toàn cục `/merchant`, `/tenants`, `/register/merchant` trong frontend

- [ ] 

```bash
rtk grep -rn "'/merchant\|\"/merchant\|'/tenants\|\"/tenants\|'/register/merchant\|\"/register/merchant" D:/DoAn/frontend/src --glob='*.{ts,tsx}'
```

**Expected:** 0 match sau khi Step 7.1-7.4 hoàn tất.

Nếu còn hit: thường là hard-coded `Link href="/merchant/..."` hoặc `redirect('/tenants/me')` — thay `/partner/*` tương ứng.

### Step 7.6 — Verify build + type check

- [ ] 

```bash
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

**Expected:** 0 error. Nếu fail:
- `Module not found: '@/app/(merchant)/...'` → import còn trỏ đường cũ, grep fix.
- `Cannot find name 'TenantPicker'` → component chưa rename, check Phase 6.5.
- Route collision: nếu `/merchant/*` trả 404 (chính là điều đã muốn) không phải error build — là runtime.

### Step 7.7 — Commit Phase 7

- [ ] 

```bash
rtk git add "frontend/src/app/(partner)" "frontend/src/app/(auth)/register/partner" "frontend/src/app/(admin)/admin/partners" frontend/src/app/
rtk git commit -m "refactor(frontend-routes): (merchant)/merchant/* → (partner)/partner/*"
```

---

## Phase 8 — Frontend customer UX `/member/partners` + detail page + ledger filter

**Goal:** Rename `/member/shops` → `/member/partners`; xoá UX join (pill filter, button Tham gia, stats membership count); thêm trang detail `/member/partners/[slug]`; update `/member/page.tsx` dashboard copy; update `/member/history/page.tsx` nhận `partnerSlug` param.

**Files:**
- Move: `(member)/member/shops/page.tsx` → `(member)/member/partners/page.tsx`.
- Create: `(member)/member/partners/[slug]/page.tsx`.
- Create: `frontend/src/lib/hooks/use-partner-detail.ts`.
- Update: `(member)/member/page.tsx`, `(member)/member/history/page.tsx`, `(member)/member/qr/page.tsx`, `(member)/member/vouchers/*`, `(member)/member/profile/page.tsx`.
- Update: `components/member/bottom-nav-bar.tsx` hide regex.

**Acceptance:** Manual smoke matrix 5 test case (spec §11.4 — Customer mới, Customer cũ, Partner owner, Staff, Super admin) pass trong browser local.

### Step 8.1 — Rename folder `shops` → `partners`

- [ ] 

```bash
git mv "frontend/src/app/(member)/member/shops" "frontend/src/app/(member)/member/partners"
```

### Step 8.2 — Viết lại `(member)/member/partners/page.tsx` (list đã xoá dead UX)

- [ ] Đọc file cũ trước để biết structure:

```bash
rtk read "frontend/src/app/(member)/member/partners/page.tsx"
```

- [ ] Re-write file. Target structure (dựa trên spec 7.4):

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type PartnerSummary = {
  id: number;
  slug: string;
  name: string;
  category: string;
  description: string | null;
  logo_url: string | null;
};

const CATEGORIES = [
  { value: "all", label: "Tất cả" },
  { value: "cafe", label: "Cafe" },
  { value: "food", label: "Ăn uống" },
  { value: "retail", label: "Bán lẻ" },
  { value: "beauty", label: "Mỹ phẩm" },
];

export default function MemberPartnersPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  const { data: partners = [], isLoading } = useQuery({
    queryKey: ["my-partners", search, category],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (category !== "all") params.set("category", category);
      const resp = await apiClient.get<PartnerSummary[]>(
        `/users/me/partners?${params.toString()}`
      );
      return resp.data;
    },
  });

  return (
    <div className="p-4 space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Đối tác</h1>
        <p className="text-sm text-muted-foreground">
          Khám phá đối tác — giao dịch tại bất kỳ đối tác nào để bắt đầu tích điểm.
        </p>
      </header>

      <Input
        placeholder="Tìm đối tác..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="flex gap-2 overflow-x-auto pb-2">
        {CATEGORIES.map((c) => (
          <Button
            key={c.value}
            variant={category === c.value ? "default" : "outline"}
            size="sm"
            onClick={() => setCategory(c.value)}
          >
            {c.label}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div>Đang tải...</div>
      ) : partners.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          Không tìm thấy đối tác phù hợp.
        </div>
      ) : (
        <ul className="space-y-3">
          {partners.map((p) => (
            <li key={p.id}>
              <Link
                href={`/member/partners/${p.slug}`}
                className="block p-4 border rounded-lg hover:border-primary transition"
              >
                <div className="flex items-start gap-3">
                  {p.logo_url ? (
                    <img
                      src={p.logo_url}
                      alt={p.name}
                      className="w-12 h-12 rounded object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded bg-muted" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold truncate">{p.name}</h3>
                      <Badge variant="secondary">{p.category}</Badge>
                    </div>
                    {p.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                        {p.description}
                      </p>
                    )}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

**Đã XOÁ (so với file gốc):**
- Pill filter "Đã tham gia / Chưa tham gia".
- Stats header "Đang là thành viên X / Tổng shop Y".
- Button "Tham gia / Đã là thành viên" trên card.
- Badge `tier_name` + `points_balance` trên card list.

Copy + paste structure shadcn đúng. Component Button/Badge/Input import từ existing `@/components/ui/*`.

### Step 8.3 — Tạo trang detail `(member)/member/partners/[slug]/page.tsx`

- [ ] Tạo folder + file:

```bash
mkdir -p "frontend/src/app/(member)/member/partners/[slug]"
```

- [ ] Viết page — target structure từ spec 7.4 (3 section):

```tsx
"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Phone, Mail, MapPin, Clock, Globe } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PartnerLedgerList } from "@/components/member/partner-ledger-list";

type PartnerDetail = {
  id: number;
  slug: string;
  name: string;
  category: string;
  description: string | null;
  logo_url: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  address: string | null;
  business_hours: string | null;
  website: string | null;
  tax_code: string | null;
  points_balance: number | null;
  total_points_earned: number | null;
  current_tier_name: string | null;
  joined_at: string | null;
  last_activity_at: string | null;
};

const TIER_EMOJI: Record<string, string> = {
  Bronze: "🥉",
  Silver: "🥈",
  Gold: "🥇",
  Platinum: "💎",
};

export default function PartnerDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);

  const { data, isLoading, error } = useQuery({
    queryKey: ["partner-detail", slug],
    queryFn: async () => {
      const resp = await apiClient.get<PartnerDetail>(
        `/users/me/partners/${slug}`
      );
      return resp.data;
    },
  });

  if (isLoading) {
    return <div className="p-4">Đang tải...</div>;
  }
  if (error || !data) {
    return <div className="p-4">Không tìm thấy đối tác.</div>;
  }

  const hasMembership = data.points_balance !== null;

  return (
    <div className="pb-20">
      <header className="sticky top-0 bg-background border-b p-3 flex items-center gap-2">
        <Link href="/member/partners">
          <Button variant="ghost" size="icon">
            <ArrowLeft />
          </Button>
        </Link>
        <h1 className="font-semibold truncate">{data.name}</h1>
        <Badge variant="secondary" className="ml-auto">
          {data.category}
        </Badge>
      </header>

      {/* Section 1: Thông tin đối tác */}
      <section className="p-4 space-y-3">
        {data.logo_url && (
          <img
            src={data.logo_url}
            alt={data.name}
            className="w-24 h-24 rounded-lg object-cover"
          />
        )}
        {data.description && (
          <p className="text-sm text-muted-foreground">{data.description}</p>
        )}
        <div className="space-y-2 text-sm">
          {data.address && (
            <div className="flex items-start gap-2">
              <MapPin className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{data.address}</span>
            </div>
          )}
          {data.contact_phone && (
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4" />
              <a href={`tel:${data.contact_phone}`}>{data.contact_phone}</a>
            </div>
          )}
          {data.contact_email && (
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              <a href={`mailto:${data.contact_email}`}>{data.contact_email}</a>
            </div>
          )}
          {data.business_hours && (
            <div className="flex items-start gap-2">
              <Clock className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{data.business_hours}</span>
            </div>
          )}
          {data.website && (
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              <a href={data.website} target="_blank" rel="noopener noreferrer">
                {data.website}
              </a>
            </div>
          )}
        </div>
      </section>

      {/* Section 2: Điểm của bạn */}
      <section className="p-4 border-t">
        <h2 className="font-semibold mb-3">Điểm của bạn tại đây</h2>
        {hasMembership ? (
          <div className="space-y-3">
            <div className="p-4 bg-primary/5 rounded-lg">
              <div className="text-3xl font-bold text-primary">
                {data.points_balance?.toLocaleString("vi-VN")}
              </div>
              <div className="text-sm text-muted-foreground">Điểm khả dụng</div>
            </div>
            {data.current_tier_name && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-2xl">
                  {TIER_EMOJI[data.current_tier_name] ?? "🎖️"}
                </span>
                <span>
                  Hạng hiện tại:{" "}
                  <strong>{data.current_tier_name}</strong>
                </span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 text-sm">
              {data.total_points_earned !== null && (
                <div>
                  <div className="text-muted-foreground">Tổng đã tích</div>
                  <div className="font-semibold">
                    {data.total_points_earned.toLocaleString("vi-VN")}
                  </div>
                </div>
              )}
              {data.joined_at && (
                <div>
                  <div className="text-muted-foreground">Tham gia từ</div>
                  <div className="font-semibold">
                    {new Date(data.joined_at).toLocaleDateString("vi-VN")}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-4 text-center text-muted-foreground bg-muted rounded-lg text-sm">
            Chưa có giao dịch tại đối tác này. Hãy quét QR khi mua hàng để bắt
            đầu tích điểm.
          </div>
        )}
      </section>

      {/* Section 3: Lịch sử tại đối tác */}
      {hasMembership && (
        <section className="p-4 border-t">
          <h2 className="font-semibold mb-3">Lịch sử tích/đổi điểm</h2>
          <PartnerLedgerList partnerSlug={slug} />
        </section>
      )}
    </div>
  );
}
```

### Step 8.4 — Tạo component `PartnerLedgerList`

Backend trả **flat** `LedgerEntry[]` (không wrapped). `useInfiniteQuery` tự infer next page bằng length heuristic: nếu page cuối trả đủ `limit` entries → còn trang; ngược lại → dừng.

- [ ] Tạo file `frontend/src/components/member/partner-ledger-list.tsx`:

```tsx
"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type LedgerEntry = {
  id: number;
  reason: string;
  delta: number;
  balance_after: number;
  ref_type: string | null;
  created_at: string;
};

const PAGE_LIMIT = 20;

const REASON_LABEL: Record<string, string> = {
  earn: "Tích điểm",
  redeem: "Đổi quà",
  expire: "Hết hạn",
  adjust: "Điều chỉnh",
};

export function PartnerLedgerList({ partnerSlug }: { partnerSlug: string }) {
  const { data, fetchNextPage, hasNextPage, isLoading } = useInfiniteQuery({
    queryKey: ["ledger", partnerSlug],
    queryFn: async ({ pageParam = 0 }) => {
      const resp = await api.get<LedgerEntry[]>(
        `/users/me/ledger?partner_slug=${partnerSlug}&limit=${PAGE_LIMIT}&offset=${pageParam}`
      );
      return { items: resp.data, offset: pageParam as number };
    },
    initialPageParam: 0,
    // Backend flat response → dùng length heuristic thay cho wrapped total
    getNextPageParam: (last) =>
      last.items.length === PAGE_LIMIT ? last.offset + PAGE_LIMIT : undefined,
  });

  if (isLoading) return <div className="text-sm">Đang tải...</div>;
  const entries = data?.pages.flatMap((p) => p.items) ?? [];
  if (entries.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        Chưa có giao dịch tích/đổi điểm.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      <ul className="divide-y border rounded-lg">
        {entries.map((e) => (
          <li key={e.id} className="p-3 flex justify-between items-start">
            <div>
              <div className="font-medium text-sm">
                {REASON_LABEL[e.reason] ?? e.reason}
              </div>
              <div className="text-xs text-muted-foreground">
                {new Date(e.created_at).toLocaleString("vi-VN")}
              </div>
            </div>
            <div
              className={`font-semibold ${
                e.delta > 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {e.delta > 0 ? "+" : ""}
              {e.delta.toLocaleString("vi-VN")}
            </div>
          </li>
        ))}
      </ul>
      {hasNextPage && (
        <button
          className="w-full text-sm py-2 text-muted-foreground hover:text-foreground"
          onClick={() => fetchNextPage()}
        >
          Xem thêm
        </button>
      )}
    </div>
  );
}
```

### Step 8.5 — Update `(member)/member/page.tsx`

- [ ] Grep + sửa copy:

```bash
rtk grep -n "cửa hàng\|Shop\|Cửa hàng\|/member/shops\|tenant" "frontend/src/app/(member)/member/page.tsx"
```

Thay:
- "Cửa hàng của tôi" → "Đối tác của tôi".
- "Bạn chưa tham gia cửa hàng nào." → "Chưa có giao dịch tại đối tác nào. Khám phá đối tác để bắt đầu tích điểm."
- "Khám phá cửa hàng" → "Khám phá đối tác".
- `/member/shops` (Link href) → `/member/partners`.
- Nếu render "Shop #{tenant_id}" → "Đối tác #{partner_id}" (ideal là fetch name, nhưng nếu giữ ID thì chỉ đổi copy).

### Step 8.6 — Update `(member)/member/history/page.tsx`

- [ ] Grep:

```bash
rtk grep -n "cửa hàng\|Shop\|shop\|tenant" "frontend/src/app/(member)/member/history/page.tsx"
```

Thay:
- Copy "Lịch sử tại các cửa hàng" → "Lịch sử tại các đối tác".
- Nếu page có UI chọn partner filter → thêm dropdown với `partnerSlug` state, pass vào `useMyLedger({ partnerSlug })`.
- Update hook signature (trong file hooks) — **giữ flat shape, dùng length heuristic** như Step 8.4:

```ts
const PAGE_LIMIT = 20;

type LedgerEntry = {
  id: number;
  reason: string;
  delta: number;
  balance_after: number;
  ref_type: string | null;
  created_at: string;
};

export function useMyLedger(opts: { partnerSlug?: string } = {}) {
  return useInfiniteQuery({
    queryKey: ["my-ledger", opts.partnerSlug ?? null],
    queryFn: async ({ pageParam = 0 }) => {
      const params = new URLSearchParams();
      if (opts.partnerSlug) params.set("partner_slug", opts.partnerSlug);
      params.set("limit", String(PAGE_LIMIT));
      params.set("offset", String(pageParam));
      const resp = await api.get<LedgerEntry[]>(
        `/users/me/ledger?${params.toString()}`
      );
      return { items: resp.data, offset: pageParam as number };
    },
    initialPageParam: 0,
    getNextPageParam: (last) =>
      last.items.length === PAGE_LIMIT ? last.offset + PAGE_LIMIT : undefined,
  });
}
```

### Step 8.7 — Update các member page khác (copy sweep)

- [ ] Grep:

```bash
rtk grep -rln "cửa hàng\|Cửa hàng\|Shop\|shop\|tenant\|Tenant\|/member/shops" "D:/DoAn/frontend/src/app/(member)" --glob='*.tsx'
```

Các file khả năng:
- `member/qr/page.tsx`
- `member/vouchers/page.tsx`
- `member/vouchers/[id]/page.tsx`
- `member/profile/page.tsx`
- `member/rewards/page.tsx`

Với mỗi file: đổi copy + URL. Ví dụ:
- "Quét QR tại cửa hàng" → "Quét QR tại đối tác".
- "Shop: {name}" → "Đối tác: {name}".

### Step 8.8 — Update `components/member/bottom-nav-bar.tsx` hide regex

- [ ] Grep:

```bash
rtk grep -n "/member/qr\|/member/vouchers\|/member/shops\|/member/partners" D:/DoAn/frontend/src/components/member/bottom-nav-bar.tsx
```

Tìm regex hide nav bar hiện tại (spec CLAUDE.md mô tả: hide trên `/member/qr` và `/member/vouchers/[id]`). Thêm hide trên `/member/partners/[slug]` (detail page thu gọn):

```ts
const HIDE_NAV_PATTERNS = [
  /^\/member\/qr$/,
  /^\/member\/vouchers\/[^/]+$/,
  /^\/member\/partners\/[^/]+$/,  // mới
];
```

### Step 8.9 — Verify build + smoke browser

- [ ] 

```bash
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

**Expected:** 0 error, 0 type complaint.

- [ ] Start dev + manual smoke:

```bash
cd frontend && npm run dev
# Open http://localhost:3000/member (login as khach1@gmail.com / khach1234)
```

Check:
- Dashboard `/member` có copy "Đối tác của tôi".
- Link "Khám phá đối tác" → `/member/partners`.
- List partner không có button "Tham gia".
- Click 1 card → detail `/member/partners/<slug>`.
- Detail có section "Điểm của bạn tại đây" + history (nếu khách1 có giao dịch sẵn) hoặc placeholder.
- Tap back button → về list.

### Step 8.10 — Commit Phase 8

- [ ] 

```bash
rtk git add "frontend/src/app/(member)" frontend/src/components/member/ frontend/src/lib/hooks/
rtk git commit -m "feat(member): xoá UX join + trang đối tác detail + ledger filter"
```

---

## Phase 9 — Frontend final verify (type check + build + lint + copy sweep)

**Goal:** Verify toàn bộ frontend không còn `tenant`/`merchant`/`/merchant` literal. Build production success.

**Acceptance:**
- `tsc --noEmit`: 0 error.
- `npm run build`: success.
- `npm run lint`: 0 error, 0 warning mới so với baseline main.
- Grep checks = 0.

### Step 9.1 — Grep toàn cục frontend

- [ ] 

```bash
rtk grep -rn "\btenant\b\|\bTenant\b\|\bTenantItem\b\|\bTenantPicker\b\|\bTenantStore\b\|\bmerchant\b\|\bMerchant\b\|\bMerchantSidebar\b\|X-Tenant-Id\|/merchant\|/tenants\|tenant-store\|api-merchant\|components/merchant\|types/merchant\|use-merchant" D:/DoAn/frontend/src --glob='*.{ts,tsx}'
```

**Expected:** 0 match. Nếu còn — sửa.

- [ ] Sweep UI copy:

```bash
rtk grep -rn "cửa hàng\|Cửa hàng\|Shop\| shop\|Chủ shop\|chủ shop\|Merchant\|merchant" D:/DoAn/frontend/src --glob='*.{ts,tsx}'
```

Với mỗi hit — assess context:
- Nếu là UI label hoặc comment về shop thực tế tiếng Việt → giữ "cửa hàng" chấp nhận (trong context đời thực user nhắc "cửa hàng" dễ hiểu hơn "đối tác"). Không phải mọi hit phải thay.
- Nếu là technical reference (log, field, variable) → đổi "partner"/"đối tác".

**Judgment call**: spec priority là "Đối tác" thống nhất. Nếu gặp nhiều hit "cửa hàng" trong user-facing copy → đổi. Nhưng ví dụ copy "Nhân viên bán hàng tại cửa hàng" có nghĩa rõ giữ là OK.

### Step 9.2 — Type check + build + lint

- [ ] 

```bash
cd frontend && npx tsc --noEmit
cd frontend && npm run build
cd frontend && npm run lint
```

**Expected:**
- `tsc`: 0 error.
- `build`: success, output routes list có `/partner/*`, `/member/partners`, `/member/partners/[slug]`.
- `lint`: 0 error + 0 warning mới (baseline main có thể có warning nào).

### Step 9.3 — PWA version bump

- [ ] Grep `sw.ts` hoặc `next.config.js` Serwist config:

```bash
rtk grep -n "sw\|serwist\|precache\|revision" D:/DoAn/frontend/src/app/sw.ts D:/DoAn/frontend/next.config.js 2>/dev/null
```

Nếu có hard-coded route `/member/shops` trong precache manifest → đổi `/member/partners`. Bump SW version (nếu file `sw.ts` có `const CACHE_VERSION` hoặc tương tự) → tăng số → force customer revalidate sau deploy.

Nếu Serwist auto-discover route thì không cần — build tự generate manifest mới.

### Step 9.4 — Commit Phase 9

- [ ] 

```bash
rtk git add frontend/
rtk git commit -m "chore(frontend): final verify + copy sweep + PWA bump"
```

Nếu không có thay đổi → skip (Phase 9 chỉ là verify gate).

---

## Phase 10 — Documentation: CLAUDE.md, AGENTS.md, docs/mo-ta-so-do.md, README

**Goal:** Update docs chính — CLAUDE.md, AGENTS.md, README.md (nếu có), docs/mo-ta-so-do.md — phản ánh tên mới.

**Files:** 1.6.

**Acceptance:** Grep docs không còn `tenant`/`merchant`/`X-Tenant-Id`/`/merchant`.

### Step 10.1 — Update `CLAUDE.md`

- [ ] 

```bash
rtk grep -n "tenant\|Tenant\|merchant\|Merchant\|X-Tenant-Id\|/merchant" D:/DoAn/CLAUDE.md
```

Thay section:

- "Domain vocabulary" (~line 10-15): xoá dòng `tenant = shop`; thêm `partner = đối tác (SME tham gia platform)`.
- "Multi-tenant scoping" section: rename heading → "Multi-partner scoping". Header mention → "X-Partner-Id". Dep references: `get_tenant_id`, `require_staff_in_tenant`, etc. → `get_partner_id`, `require_staff_in_partner`.
- "Backend layering" tree: `app/models/tenant.py` → `partner.py`.
- "Frontend route groups" tree: `src/app/(merchant)` → `(partner)`.
- "Key domain invariants" section: `Voucher.code uniqueness is enforced per-tenant` → `per-partner`.
- Bất kỳ code snippet reference nào → update.

### Step 10.2 — Update `AGENTS.md`

- [ ] 

```bash
rtk grep -n "tenant\|Tenant\|merchant\|Merchant" D:/DoAn/AGENTS.md
```

Sweep tương tự. Nếu có subagent description mention "merchant context" → update.

### Step 10.3 — Update `docs/mo-ta-so-do.md`

- [ ] 

```bash
rtk grep -n "tenant\|Tenant\|X-Tenant-Id\|merchant\|/merchant" D:/DoAn/docs/mo-ta-so-do.md
```

Sweep: header references, route naming.

### Step 10.4 — Update `README.md` / `backend/README.md` / `frontend/README.md`

- [ ] Check tồn tại:

```bash
rtk ls D:/DoAn/README.md D:/DoAn/backend/README.md D:/DoAn/frontend/README.md 2>/dev/null
```

Với file tồn tại: grep + sweep.

### Step 10.5 — Verify + commit

- [ ] Grep sạch docs:

```bash
rtk grep -rn "tenant\|Tenant\|merchant\|Merchant\|X-Tenant-Id\|/merchant\|/tenants" D:/DoAn/CLAUDE.md D:/DoAn/AGENTS.md D:/DoAn/docs/ D:/DoAn/README.md 2>/dev/null
```

**Expected:** 0 match.

- [ ] Commit:

```bash
rtk git add CLAUDE.md AGENTS.md docs/ README.md backend/README.md frontend/README.md 2>/dev/null
rtk git commit -m "docs: rename Tenant/Merchant → Partner trong docs chính"
```

---

## Phase 11 — Báo cáo STU

**Goal:** Update `bao-cao/content/*.py`, build scripts, diagram files. Rebuild docx. Grep output không còn tên cũ.

**Files:** xem 1.7.

**Acceptance:** Rebuild thành công, grep output docx (converted to text) không còn `tenant`/`merchant`/`X-Tenant-Id`/`/merchant`.

### Step 11.1 — Grep inventory `bao-cao/`

- [ ] 

```bash
rtk grep -rln "tenant\|Tenant\|merchant\|Merchant\|X-Tenant-Id\|/merchant\|/tenants\|cửa hàng\|Cửa hàng" D:/DoAn/bao-cao
```

Sẽ có danh sách ~15-20 file. Lưu lại để sweep từng file.

### Step 11.2 — Sweep `bao-cao/content/*.py`

- [ ] Với mỗi file 8 chương:
  - `loi_cam_on.py` — check, thường không đụng.
  - `chuong_1.py` — tổng quan. Section "vocabulary" → đổi "tenant = shop" → "partner = đối tác".
  - `chuong_2.py` — công nghệ. Code snippet nếu có `X-Tenant-Id`, `/merchant` → update.
  - `chuong_3.py` — **nặng nhất**. ERD references (diagrams link + text), table names, column names (tenant_id → partner_id), use case "Chủ doanh nghiệp", sequence diagram link. Rename triệt để.
  - `chuong_4.py` — implementation. Code snippet, route table `/merchant/*` → `/partner/*`, screenshot URL `/member/shops` → `/member/partners`.
  - `chuong_5.py` — testing + kết luận. API names, test names.
  - `phu_luc.py` — API spec / schema table. Rename hoàn toàn.
  - `tltk.py` — tài liệu tham khảo, thường không đụng.

**Chiến lược per file**: regex search `\b(tenant|merchant|Tenant|Merchant|cửa hàng|/merchant|/tenants|X-Tenant-Id)\b`, review từng hit.

**Judgement call cho "cửa hàng" trong copy kể chuyện**: nếu câu "Mô hình cho phép nhiều cửa hàng tham gia platform" → có thể giữ "cửa hàng" (nghĩa đời thường). Nhưng nếu context kỹ thuật "bảng `tenants`" → đổi `partners`.

### Step 11.3 — Sweep build scripts

- [ ] 

```bash
rtk grep -n "tenant\|Tenant\|merchant" D:/DoAn/bao-cao/build_docx.py D:/DoAn/bao-cao/builder.py D:/DoAn/bao-cao/style.py D:/DoAn/bao-cao/plan.md 2>/dev/null
```

Sweep theo hit.

### Step 11.4 — Sweep diagrams + rename

- [ ] Rename file:

```bash
git mv bao-cao/diagrams/mermaid/seq_login_tenant.mmd bao-cao/diagrams/mermaid/seq_login_partner.mmd
git mv bao-cao/assets/uml/seq_login_tenant.puml bao-cao/assets/uml/seq_login_partner.puml
```

- [ ] Update content 2 file mới rename:
- Tên sequence / title trong file `.mmd`: `sequenceDiagram ... title Login (tenant)` → `title Login (partner)`.
- Lane names `Tenant` → `Partner`.
- Message `X-Tenant-Id` → `X-Partner-Id`.

- [ ] Update `seq_claim_voucher.mmd`:

```bash
rtk grep -n "tenant\|Tenant" bao-cao/diagrams/mermaid/seq_claim_voucher.mmd
```

Sweep.

- [ ] Các `.mmd`/`.puml` khác:

```bash
rtk grep -rln "tenant\|Tenant" bao-cao/diagrams/ bao-cao/assets/uml/
```

Sweep each.

- [ ] Update `bao-cao/assets/make_diagrams.py`:

```bash
rtk grep -n "tenant\|Tenant\|seq_login_tenant" bao-cao/assets/make_diagrams.py
```

Nếu code list file `.mmd` / `.puml` chứa tên cũ → đổi sang `seq_login_partner.*`.

### Step 11.5 — Rebuild docx

- [ ] 

```bash
cd bao-cao && python build_docx.py
```

**Expected:** Success output `bao-cao-final.docx`. Nếu fail:
- `ModuleNotFoundError` → thiếu dep, chạy `pip install -r requirements.txt` trong `bao-cao/`.
- `FileNotFoundError: seq_login_tenant.mmd` → build script còn ref tên cũ, sửa Step 11.4.

### Step 11.6 — Grep output docx

- [ ] Convert docx → text + grep:

```bash
python -c "from docx import Document; d = Document('bao-cao/bao-cao-final.docx'); print('\n'.join(p.text for p in d.paragraphs))" | grep -iE "tenant|merchant|X-Tenant-Id|/merchant|/tenants"
```

Hoặc nếu không tiện: mở docx bằng Word, Ctrl+F search "tenant" và "merchant" manually.

**Expected:** 0 match.

Nếu còn hit: tìm nguồn (file nào trong `content/*.py` tạo ra), sửa, rebuild.

### Step 11.7 — Commit Phase 11

- [ ] 

```bash
rtk git add bao-cao/
rtk git commit -m "docs(bao-cao): rename Tenant/Merchant → Partner toàn báo cáo"
```

---

## Phase 12 — Deploy cutover + 5 smoke flows + post-deploy `gitnexus analyze`

**Goal:** Apply rename migration vào prod DB, restart backend + frontend, smoke test matrix 5 test case (spec §11.4) + verify 0 error log.

**Acceptance:**
- Migration applied thành công (kiểm verify list bảng).
- 5 smoke flow spec 11.4 + 11.5 pass.
- 10 phút đầu sau deploy: 0 error log 5xx từ backend.

### Step 12.1 — Merge branch vào main (trước deploy)

- [ ] Ensure CI xanh trên branch `feat/partner-rename`. Ví dụ GitHub Actions pass.
- [ ] Merge qua PR hoặc `git merge --no-ff`:

```bash
rtk git checkout main
rtk git merge --no-ff feat/partner-rename
rtk git push origin main
```

### Step 12.2 — Pre-cutover DB connection check

- [ ] Check concurrent connection (spec 8.3 T+0.5m):

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT pid, application_name, query FROM pg_stat_activity WHERE datname='loyalty' AND pid <> pg_backend_pid();"
```

**Expected:** Chỉ có backend + scheduler connection. Nếu có pgAdmin/DBeaver/query tay chạy lâu → đóng tool + re-verify rỗng. Nếu có APScheduler job đang chạy → đợi xong hoặc terminate:

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT pg_terminate_backend(<pid>);"
```

### Step 12.3 — Down backend + frontend (giữ postgres)

- [ ] 

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml stop backend frontend
```

### Step 12.4 — Build image mới

- [ ] 

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml build backend frontend
```

**Expected:** Build success. Nếu fail — thường do local uncommitted changes không reachable hoặc cache issue. Kiểm `docker system prune` rồi retry.

### Step 12.5 — Start backend (auto migration)

- [ ] 

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml up -d backend
docker logs loyalty-backend-prod --tail 50 -f
```

**Expected:** Thấy output `Running upgrade <prev> -> <new>, rename tenant to partner`. Sau vài giây, `Application startup complete`. Nếu thấy error migration:
- `OperationalError: lock_timeout expired` → có connection chưa đóng, quay lại Step 12.2.
- `FK constraint does not exist` → discovery Phase 1 sót index/constraint, `alembic downgrade -1` rồi fix revision.

### Step 12.6 — Verify schema + start frontend

- [ ] 

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\dt partner*"
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT column_name FROM information_schema.columns WHERE table_name='memberships' AND column_name LIKE 'partner%';"
```

**Expected:**
- 4 table: `partners`, `partner_staff`, `partner_authorizations`, `partner_settings_audit`.
- `memberships.partner_id` tồn tại.

- [ ] Start frontend:

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml up -d frontend
curl -I http://localhost:3000/
```

**Expected:** 200 OK (hoặc redirect 307 → /login).

### Step 12.7 — Smoke test 5 flow (spec 11.4 + 11.5)

- [ ] Flow 1: Customer mới
  - Đăng ký `/register` với SĐT `09xxxxxxxx` → login OK.
  - `/member` dashboard load OK.
  - Tap "Khám phá đối tác" → `/member/partners` list 2 partner.
  - Card không có button "Tham gia".
  - Tap partner Cafe Cộng → detail page `/member/partners/cafe-cong`.
  - Section "Điểm của bạn tại đây" hiển thị "Chưa có giao dịch tại đối tác này…".

- [ ] Flow 2: Customer cũ có điểm
  - Login `khach1@gmail.com` / `khach1234`.
  - `/member/partners` → tap Cafe Cộng.
  - Section "Điểm của bạn" hiển thị points_balance, tier "Silver"/"Gold" (tuỳ seed data).
  - Section "Lịch sử" render ledger entries của partner này.

- [ ] Flow 3: Partner owner
  - Login `owner@cafe.vn` / `owner1234`.
  - Redirect tới `/partner/dashboard` (route mới).
  - Sidebar URLs `/partner/*`.
  - Tạo campaign demo → success.

- [ ] Flow 4: Staff POS
  - Login staff account → `/staff/*` load OK.
  - Tạo transaction demo với SĐT mới `09yyyyyyyy` → lazy membership tạo OK (check DB `SELECT * FROM memberships WHERE partner_id = X ORDER BY id DESC LIMIT 1`).

- [ ] Flow 5: Super admin
  - Login `admin@loyalty.vn` / `admin1234`.
  - `/admin/partners` load OK, list có 2 partner.
  - Approve pending partner OK.

### Step 12.8 — Monitor error log 10 phút

- [ ] 

```bash
docker logs loyalty-backend-prod --tail 100 -f
```

Verify:
- 0 log 5xx.
- 0 log "X-Tenant-Id missing" (client cũ).
- 0 log `AttributeError: 'Membership' object has no attribute 'tenant_id'`.

Nếu có log 5xx — rollback plan (Step 12.10).

### Step 12.9 — Post-deploy grep từ external

- [ ] Hit prod URL kiểm route:

```bash
curl -I https://loyalty.ecom-bill.com/partner/dashboard
# Expected: 200 (hoặc 401 redirect) — không 404.

curl -I https://loyalty.ecom-bill.com/merchant/dashboard
# Expected: 404.

curl -I https://loyalty.ecom-bill.com/member/partners
# Expected: 200 (hoặc 401).

curl -I https://loyalty.ecom-bill.com/member/shops
# Expected: 404.
```

### Step 12.10 — Rollback (nếu blocker phát hiện < 30 phút)

Không execute trừ khi thực sự cần. Chỉ document:

```bash
# 1. Down current
docker compose -p loyalty-prod -f docker-compose.prod.yml stop backend frontend

# 2. Downgrade migration
docker exec loyalty-backend-prod alembic downgrade -1

# 3. Tag image cũ + deploy lại (giả sử có image tag `loyalty-backend:pre-rename`)
docker tag loyalty-backend:pre-rename loyalty-backend:latest
docker tag loyalty-frontend:pre-rename loyalty-frontend:latest

# 4. Start lại
docker compose -p loyalty-prod -f docker-compose.prod.yml up -d backend frontend
```

Sau 30 phút — forward-fix only (data mới sẽ mất nếu downgrade).

### Step 12.11 — Post-deploy `gitnexus analyze`

- [ ] 

```bash
gitnexus analyze
```

**Expected:** Index rebuilt với symbol mới (`Partner`, `PartnerService`, etc.). Verify qua Claude Code:

```
gitnexus_query {"query": "Partner"}
# Hoặc
gitnexus_context {"name": "PartnerService"}
```

### Step 12.12 — Commit deploy notes

- [ ] Nếu có change gì sau smoke (hot fix), commit:

```bash
rtk git add .
rtk git commit -m "chore(deploy): partner rename cutover prod"
```

Nếu deploy sạch không có hot fix → skip commit (chỉ là deploy step).

---

## 3. Acceptance criteria tổng (final gate)

Kiểm tra toàn diện sau Phase 12:

- [ ] `rtk grep -rn "\btenant\b" backend/app/ frontend/src/` → 0 match.
- [ ] `rtk grep -rn "\bmerchant\b" backend/app/ frontend/src/` → 0 match.
- [ ] `rtk grep -rn "X-Tenant-Id" backend/ frontend/` → 0 match.
- [ ] `rtk grep -rn "/merchant\|/tenants" frontend/src/` → 0 match.
- [ ] Full pytest suite pass (unit + integration): `docker exec loyalty-backend-prod pytest backend/tests -v`.
- [ ] Frontend `tsc --noEmit` + `npm run build` pass.
- [ ] 5 manual smoke flow ở Step 12.7 pass.
- [ ] `gitnexus analyze` post-deploy success, `gitnexus_context {"name": "PartnerService"}` trả data.
- [ ] Báo cáo docx rebuild + grep check pass.
- [ ] 10 phút monitor error log prod: 0 log 5xx liên quan rename.

---

## 4. Rủi ro & mitigation (tóm từ spec 12.2)

| Rủi ro | Severity | Mitigation |
|---|---|---|
| Alembic miss index/constraint rename → ORM reflect fail | High | Phase 1 Step 1.1 query `pg_indexes` + `pg_constraint` + `pg_sequences` trên prod dump; fill đầy đủ vào revision trước apply. |
| Frontend/backend deploy async → API mismatch | High | Phase 12 deploy cả 2 trong 1 Docker Compose up cùng window. |
| Serwist PWA cache giữ `/member/shops` → 404 | Med | Phase 9 Step 9.3 bump SW version. |
| Migration hang do AccessExclusiveLock | High | Phase 12 Step 12.2 pre-check `pg_stat_activity`; revision có `SET lock_timeout = '10s'`. |
| FK constraint naming inconsistent (SA vs PG default) | Med | Discovery query glob `%tenant%` trên cả 2 nguồn — Phase 1 Step 1.1 covers. |
| GitNexus index stale sau rename | Low | Phase 12 Step 12.11 `gitnexus analyze`. |
| Báo cáo docx đã build tên cũ | Med | Phase 11 rebuild; grep output docx. |
| Merge conflict do branch chạy lâu | Med | Execute plan trong 3-5 ngày tối đa; rebase `main` mỗi ngày. |
| Zustand sessionStorage — user active_partner null lần đầu | Low | Không cần migration code — spec 7.7 xác nhận; user pick lại 1 lần. |
| Slug conflict ở partner-registration | Low | Test `test_partner_create_slug_unique` trong Phase 4. |

---

## 5. Execution notes

Plan này có **12 phase** với **~70 step** tổng cộng. Ước lượng effort: **5-7 ngày công full-time** (solo dev). Kéo dài hơn nếu chia ngày hoặc gặp issue integration test.

**Recommend execution mode:** `superpowers:subagent-driven-development` — dispatch 1 subagent per phase, review giữa phase. Fresh subagent tránh context rot. Parent (bạn) giữ vai trò: review sau mỗi phase, merge tiếp hay request fix.

**Alternative:** `superpowers:executing-plans` — execute inline từng phase trong cùng session. OK cho user muốn theo sát từng bước; nhưng context window sẽ fill nhanh khi tới Phase 8 (detail page code block lớn).

**Lưu ý cho engineer thực thi:**

- **Giữ rule workflow**: sau mỗi phase, chạy `superpowers:code-reviewer` (opus) TRƯỚC khi commit. Fix Critical/Important feedback. Xem rule `~/.claude/CLAUDE.md` section "Code review".
- **GitNexus**: trước edit một file có symbol đụng consumer (VD `require_staff_in_tenant` có 30+ caller) → `gitnexus_impact` trước. Phase 3 Step 3.6 sweep deps.py là high-impact — impact check bắt buộc.
- **Commit policy**: mỗi phase có 1 commit conventional message tiếng Việt. Xem table section 2.
- **RTK commands**: dùng `rtk git`/`rtk grep`/`rtk pytest` thay lệnh thường để tiết kiệm token.

---

**End of plan.** Xin bạn review trước khi chọn execution mode (subagent-driven recommended, hoặc inline executing-plans).
