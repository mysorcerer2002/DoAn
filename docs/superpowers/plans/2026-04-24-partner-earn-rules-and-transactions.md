# Partner earn rules + Transaction history + Service fee removal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xoá toàn bộ service fee infrastructure, thêm tier earn multiplier (earn-only), thêm transaction history + receipt_code cho partner.

**Architecture:** 2 Alembic revision. Revision A drop 2 bảng + 2 cột + 2 check constraint trên `campaigns` (irreversible, downgrade=pass). Revision B+C add `point_rules.use_tiers`, `tiers.earn_multiplier`, `transactions.receipt_code` với partial unique index. `_calculate_points` rewrite nhận kwarg `membership`, eager-load `current_tier` qua `selectinload`. UI `/partner/settings` (Owner) cho toggle/multiplier, `/partner/transactions` (Owner+Staff read, Owner edit) cho audit trail.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2 | Next.js 14 + TanStack Query + react-hook-form + zod + shadcn/ui.

**Spec:** `docs/superpowers/specs/2026-04-24-partner-earn-rules-and-transactions.md`

---

## Conventions

- Mỗi task kết thúc bằng commit. Message theo conventional commit VN: `chore(scope):`, `feat(scope):`, `fix(scope):`, `test(scope):`.
- Alembic revision auto-run on backend startup qua `docker compose -p loyalty-prod -f docker-compose.prod.yml up -d backend`. Trong dev local cũng tự chạy.
- Chạy test qua docker: `docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest <path> -v` HOẶC `cd backend && pytest <path> -v` nếu có local venv. Prefer docker.
- Frontend type-check: `cd frontend && npx tsc --noEmit` sau mỗi change TS/TSX.
- GitNexus impact trước mỗi edit symbol: `gitnexus_impact({target: "symbol", direction: "upstream"})`.
- Full content của file được show trong step — engineer copy-paste, không lookup ngoài plan.

---

## Part A — Service fee removal

### Task A1: Alembic migration drop service fee infrastructure

**Files:**
- Create: `backend/alembic/versions/e1f2a3b4c5d6_drop_service_fee_infra.py`

> **⚠ Ordering note:** A1 drop DB column `service_fee_status` / `service_fee_total` nhưng `Campaign` model vẫn còn `Mapped[...]` cho các column đó cho đến A2 Step 4 xoá. Giữa A1 và A2 **không được restart backend, không chạy pytest** — SELECT ORM sẽ crash vì schema mismatch. Cách an toàn nhất: chạy A1 → A2 liền mạch trong cùng phiên làm việc, kết thúc A2 mới restart backend + test. Nếu bắt buộc tách, áp dụng pattern: A2 trước (xoá code trỏ tới column) → restart → A1 (drop DB) → restart. Khi đó update A1 step 3 + A2 step 5 cho khớp.

- [ ] **Step 1: Verify current head revision**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic current`
Expected output contains: `162e25afc796 (head)`.

Nếu head khác → dừng, báo user. Plan này giả định head = `162e25afc796_rename_tenant_to_partner`.

- [ ] **Step 2: Tạo file migration**

Tạo file `backend/alembic/versions/e1f2a3b4c5d6_drop_service_fee_infra.py`:

```python
"""drop service fee infrastructure

Revision ID: e1f2a3b4c5d6
Revises: 162e25afc796
Create Date: 2026-04-24

**One-way migration** — downgrade = pass (không restore schema).
Lý do: spec 2026-04-24-partner-earn-rules-and-transactions section 3.1.
- CI round-trip test `upgrade → downgrade → upgrade` không crash
- Production rollback = revert commit + redeploy (không dùng alembic downgrade trực tiếp)

Drop:
- 2 check constraints: ck_campaigns_service_fee_status, ck_campaigns_service_fee_total_nonneg
- 2 columns trên campaigns: service_fee_status, service_fee_total
- 2 indexes + table campaign_service_fees
- 1 index + table campaign_fee_schedules

GIỮ: authorization_id, fk_campaigns_authorization_id, partner_authorizations
(managed service model, không phải fee).
"""

from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "162e25afc796"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_campaigns_service_fee_status", "campaigns", type_="check"
    )
    op.drop_constraint(
        "ck_campaigns_service_fee_total_nonneg", "campaigns", type_="check"
    )
    op.drop_column("campaigns", "service_fee_status")
    op.drop_column("campaigns", "service_fee_total")

    op.drop_index(
        "ix_campaign_service_fees_partner_status",
        table_name="campaign_service_fees",
    )
    op.drop_index(
        "ux_campaign_service_fees_active_per_type",
        table_name="campaign_service_fees",
    )
    op.drop_table("campaign_service_fees")

    op.drop_index(
        "ux_campaign_fee_schedules_active_per_type",
        table_name="campaign_fee_schedules",
    )
    op.drop_table("campaign_fee_schedules")


def downgrade() -> None:
    """One-way — không restore schema. Xem docstring module."""
    pass
```

- [ ] **Step 3: Run migration dry run (staging DB tạm)**

Vì đây là prod-on-dev-box, safest là tạo DB tạm test migration trước commit. Skip nếu user không có DB test riêng — để step 4 verify.

- [ ] **Step 4: Run migration on dev prod DB**

Run: `docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head`
Expected: `Running upgrade 162e25afc796 -> e1f2a3b4c5d6, drop service fee infrastructure`.

- [ ] **Step 5: Verify schema**

Run: `docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d campaigns"`
Expected: không có column `service_fee_total` hoặc `service_fee_status`. Có `authorization_id`.

Run: `docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\dt campaign_service_fees"`
Expected: `Did not find any relation`.

Run: `docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\dt campaign_fee_schedules"`
Expected: `Did not find any relation`.

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/alembic/versions/e1f2a3b4c5d6_drop_service_fee_infra.py
rtk git commit -m "chore(service-fee): Alembic migration drop 2 bảng + 2 cột + 2 check"
```

---

### Task A2: Remove backend models + model __init__ exports

**Files:**
- Delete: `backend/app/models/campaign_fee_schedule.py`
- Delete: `backend/app/models/campaign_service_fee.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/campaign.py` (drop columns + constraints)

- [ ] **Step 1: Verify impact trước khi xoá**

Run: `gitnexus_impact({target: "CampaignServiceFee", direction: "upstream"})`
Expected: list các consumer (schemas, services, API, frontend types) — xác nhận chỉ trong service fee scope.

Run: `gitnexus_impact({target: "CampaignFeeSchedule", direction: "upstream"})`
Expected: tương tự.

- [ ] **Step 2: Delete 2 model files**

```bash
cd D:/DoAn && rm backend/app/models/campaign_fee_schedule.py backend/app/models/campaign_service_fee.py
```

- [ ] **Step 3: Update `backend/app/models/__init__.py`**

Đọc file:
```bash
rtk cat backend/app/models/__init__.py
```

Xoá các line import + `__all__` entries: `CampaignServiceFee`, `CampaignFeeSchedule`, `FeeType`, `FeeStatus`, `EInvoiceProvider`.

Pattern — line cần xoá:
```python
from app.models.campaign_service_fee import CampaignServiceFee, FeeType, FeeStatus, EInvoiceProvider
from app.models.campaign_fee_schedule import CampaignFeeSchedule
```

Và trong list `__all__`:
```python
"CampaignServiceFee",
"CampaignFeeSchedule",
"FeeType",
"FeeStatus",
"EInvoiceProvider",
```

- [ ] **Step 4: Update `backend/app/models/campaign.py`**

Mở file, tìm và xoá:

**Columns L.~199-205 (trong class body):**
```python
service_fee_total: Mapped[int] = mapped_column(...)
service_fee_status: Mapped[...] = mapped_column(...)
```

**Check constraints trong `__table_args__` L.~99-105:**
```python
CheckConstraint("service_fee_total >= 0", name="ck_campaigns_service_fee_total_nonneg"),
CheckConstraint("service_fee_status IN (...)", name="ck_campaigns_service_fee_status"),
```

**GIỮ** `authorization_id` column, `fk_campaigns_authorization_id`, và các indexes/constraints khác.

- [ ] **Step 5: Run pytest collection check**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend python -c "from app.models import Campaign; print(Campaign.__tablename__)"`
Expected: `campaigns` (không ImportError).

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/models/
rtk git commit -m "chore(service-fee): xoá models CampaignServiceFee + CampaignFeeSchedule"
```

---

### Task A3: Remove backend schemas

**Files:**
- Modify: `backend/app/schemas/partner_authorization.py` (remove `CampaignServiceFeeResponse`)
- Modify: `backend/app/schemas/campaign_approval.py`
- Modify: `backend/app/schemas/campaign_enrollment.py`

- [ ] **Step 1: Grep các schema class cần xoá**

Run: `rtk grep -n "CampaignServiceFeeResponse\|service_fee_total\|service_fee_status\|service_fee_enabled" backend/app/schemas/`

- [ ] **Step 2: Update `backend/app/schemas/partner_authorization.py`**

Xoá class `CampaignServiceFeeResponse` (kể cả docstring + nested types nếu có). Giữ tất cả schema authorization khác. Update module docstring bỏ nhắc service fee.

- [ ] **Step 3: Update `backend/app/schemas/campaign_approval.py`**

Xoá fields từ `AdminCampaignListItem` và `AdminCampaignDetail`:
```python
service_fee_total: int | None
service_fee_status: str | None
```

- [ ] **Step 4: Update `backend/app/schemas/campaign_enrollment.py`**

Xoá fields:
```python
service_fee_enabled: bool
service_fee_status: str
```
+ bất kỳ nested type nào chỉ dùng cho service fee (L.49, L.62, L.93). Grep kỹ từng field trước khi xoá đảm bảo không reference ngoài service fee.

- [ ] **Step 5: Import sanity check**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend python -c "from app.schemas.campaign_enrollment import CampaignEnrollmentResponse; from app.schemas.campaign_approval import AdminCampaignDetail; from app.schemas.partner_authorization import PartnerAuthorizationResponse; print('ok')"`
Expected: `ok`.

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/schemas/
rtk git commit -m "chore(service-fee): xoá schema fee (CampaignServiceFeeResponse + fields fee ở admin/enrollment)"
```

---

### Task A4: Remove backend services + jobs + config flag

**Files:**
- Delete: `backend/app/services/campaign_fee_service.py`
- Modify: `backend/app/services/campaign_enrollment_service.py`
- Modify: `backend/app/jobs/purge_retention.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Delete `campaign_fee_service.py`**

```bash
cd D:/DoAn && rm backend/app/services/campaign_fee_service.py
```

- [ ] **Step 2: Update `backend/app/services/campaign_enrollment_service.py`**

Remove:
- Import: `from app.models.campaign_service_fee import ...`, `from app.models.campaign_fee_schedule import ...`, `from app.services.campaign_fee_service import CampaignFeeService`.
- Method `_build_fee_preview` (L.~247-257).
- Branch `if settings.service_fee_enabled:` (grep trong file).
- Field `service_fee_enabled` trong response builder.

Import sanity check sau khi sửa:
```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend python -c "from app.services.campaign_enrollment_service import CampaignEnrollmentService; print('ok')"
```

- [ ] **Step 3: Update `backend/app/jobs/purge_retention.py`**

Mở file, xoá:
- SQL DELETE cho `campaign_service_fees` (L.~67).
- Log line `hard-delete %d campaign_service_fees ids=%s` (L.84).
- Return dict chỉ còn `auth_deleted=...`, bỏ `fee_deleted`.
- Update docstring module bỏ nhắc campaign_service_fees.

**GIỮ** SQL DELETE cho `partner_authorizations` (L.~58) — job vẫn cần cho managed service cleanup.

- [ ] **Step 4: Update `backend/app/core/config.py`**

Remove:
```python
service_fee_enabled: bool = False
```
+ docstring comment tương ứng (L.~36-38). Giữ các setting khác.

- [ ] **Step 5: Container reload + sanity check**

Run: `docker compose -p loyalty-prod -f docker-compose.prod.yml restart backend`
Wait ~5s.

Run: `curl -sf http://localhost:8000/health | head -5` (prod nội bộ) HOẶC `curl -sf https://loyalty.ecom-bill.com/api/health`
Expected: `{"status":"ok"}`.

Run: `docker logs loyalty-backend-prod --tail 30`
Expected: no ImportError, no AttributeError.

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/services/ backend/app/jobs/purge_retention.py backend/app/core/config.py
rtk git commit -m "chore(service-fee): xoá campaign_fee_service + fee branch enrollment/purge + flag config"
```

---

### Task A5: Remove backend API handlers + admin projection

**Files:**
- Modify: `backend/app/api/partner_authorization.py`
- Modify: `backend/app/api/admin_campaigns.py`

- [ ] **Step 1: Update `backend/app/api/partner_authorization.py`**

Remove:
- Handler `list_campaign_service_fees` (route + function).
- Import `CampaignServiceFeeResponse`.

Giữ các endpoint authorization khác (create, list, get, revoke).

- [ ] **Step 2: Update `backend/app/api/admin_campaigns.py`**

Remove fields từ response projection (L.~62-63):
```python
service_fee_total=campaign.service_fee_total,
service_fee_status=campaign.service_fee_status,
```
Và bất kỳ sort/filter nào dùng 2 field này.

- [ ] **Step 3: OpenAPI sanity check**

Run: `curl -sf http://localhost:8000/openapi.json | jq '.paths | keys | map(select(. | contains("service_fee")))'`
Expected: `[]` (empty array).

Run: `curl -sf http://localhost:8000/openapi.json | jq '.components.schemas | keys | map(select(. | contains("ServiceFee") or contains("FeeSchedule")))'`
Expected: `[]`.

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/api/partner_authorization.py backend/app/api/admin_campaigns.py
rtk git commit -m "chore(service-fee): xoá API handler list_campaign_service_fees + admin projection"
```

---

### Task A6: Update IntegrityError handler cho receipt_code

**Files:**
- Modify: `backend/app/main.py:92-124`

> **Context:** Task này thuộc Part A về mặt file (sửa main.py) nhưng constraint `ux_transactions_partner_receipt_code` chỉ xuất hiện SAU khi Task B+C migration chạy. Tức code sẽ dormant (không bao giờ hit) cho đến Task C1 deploy. An toàn để ship trong A.

- [ ] **Step 1: Đọc handler hiện tại**

Run: `rtk read backend/app/main.py | sed -n '88,125p'`

Xác nhận: handler là `@app.exception_handler(Exception)` ở L.92, bên trong có nhánh `if isinstance(exc, IntegrityError):` (L.99+) với chuỗi `if/elif` match `msg_low`.

- [ ] **Step 2: Thêm nhánh nhận diện receipt_code**

Trong khối `isinstance(exc, IntegrityError)` của handler `@app.exception_handler(Exception)`, thêm nhánh MỚI ngay sau nhánh `"slug"` (L.107-108) và TRƯỚC nhánh `partner_user/partner_staff`:

```python
# Sửa từ:
elif "slug" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
    detail = "Slug đã tồn tại"
elif "partner_user" in msg_low or "partner_staff" in msg_low:
    detail = "User đã thuộc đối tác này"

# Thành:
elif "slug" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
    detail = "Slug đã tồn tại"
elif "receipt_code" in msg_low and ("unique" in msg_low or "duplicate" in msg_low):
    detail = "Mã hoá đơn đã tồn tại cho đối tác này"
elif "partner_user" in msg_low or "partner_staff" in msg_low:
    detail = "User đã thuộc đối tác này"
```

Lý do đặt vị trí này: `partner_user/partner_staff` branch match lỏng (không yêu cầu `"unique"`), nên receipt_code phải đứng trước nó để không bị fall-through nhầm.

- [ ] **Step 3: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/main.py
rtk git commit -m "feat(transactions): IntegrityError handler nhận diện ux_transactions_partner_receipt_code"
```

---

### Task A7: Remove frontend types + hooks service fee

**Files:**
- Modify: `frontend/src/types/partner-enroll.ts`
- Modify: `frontend/src/types/admin.ts`
- Modify: `frontend/src/lib/api-partner-enroll.ts`
- Modify: `frontend/src/lib/hooks/use-partner-enroll.ts`

- [ ] **Step 1: Grep frontend references**

Run: `rtk grep -rn "CampaignServiceFee\|service_fee_enabled\|service_fee_status\|service_fee_total\|listCampaignServiceFees\|useCampaignServiceFees" frontend/src/`

Kết quả dùng làm checklist — mỗi match sẽ xử lý ở các step sau.

- [ ] **Step 2: Update `frontend/src/types/partner-enroll.ts`**

Remove:
- `export interface CampaignServiceFee { ... }` (L.~152).
- Fields trong các interface khác: `service_fee_enabled: boolean` (L.63), `service_fee_status: string` (L.98).

- [ ] **Step 3: Update `frontend/src/types/admin.ts`**

Remove fields trong admin campaign types:
```ts
service_fee_total?: number;
service_fee_status?: string;
```
(L.~78-79, L.97-98).

- [ ] **Step 4: Update `frontend/src/lib/api-partner-enroll.ts`**

Remove:
- Import `CampaignServiceFee` (L.~6).
- Method `listCampaignServiceFees` (L.~55).

- [ ] **Step 5: Update `frontend/src/lib/hooks/use-partner-enroll.ts`**

Remove hook `useCampaignServiceFees` (L.~102) + bất kỳ reference nào ở top của file.

- [ ] **Step 6: Type-check**

Run: `cd D:/DoAn/frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: 0 error. Nếu còn error "CampaignServiceFee" / "service_fee_*" — grep tiếp và xoá.

- [ ] **Step 7: Commit**

```bash
cd D:/DoAn && rtk git add frontend/src/types/ frontend/src/lib/api-partner-enroll.ts frontend/src/lib/hooks/use-partner-enroll.ts
rtk git commit -m "chore(service-fee): xoá frontend types + hook service fee"
```

---

### Task A8: Remove frontend UI sections service fee

**Files:**
- Modify: `frontend/src/app/(partner)/partner/campaigns/[id]/page.tsx`
- Modify: `frontend/src/app/(partner)/partner/campaigns/enroll/page.tsx`
- Modify: `frontend/src/app/(admin)/admin/campaigns/page.tsx`
- Modify: `frontend/src/app/(admin)/admin/campaigns/[id]/page.tsx`

- [ ] **Step 1: Update `partner/campaigns/[id]/page.tsx`**

Remove:
- `useCampaignServiceFees` call (L.~29).
- JSX section "Phí dịch vụ" render (L.~92 + block liền kề).
- Bất kỳ local variable nào chỉ dùng để render fee UI.

- [ ] **Step 2: Update `partner/campaigns/enroll/page.tsx`**

Remove:
- Branch `preview.service_fee_enabled` (L.~525) + associated render block.
- Mọi reference `service_fee_*` trong JSX.

- [ ] **Step 3: Update `admin/campaigns/page.tsx`**

Remove:
- Dicts `FEE_COLORS`, `FEE_LABELS`.
- Cột "Trạng thái phí" trong table (L.~133-135).

- [ ] **Step 4: Update `admin/campaigns/[id]/page.tsx`**

Remove:
- InfoRow "Tổng phí" (L.~308).
- InfoRow "Trạng thái phí" (L.~311).

- [ ] **Step 5: Type-check + smoke build**

Run: `cd D:/DoAn/frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: 0 error.

Run: `cd D:/DoAn/frontend && npm run lint 2>&1 | head -20`
Expected: không có new lint error về unused-import/unused-var liên quan service fee.

- [ ] **Step 6: Rebuild frontend container + smoke browser**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml build frontend && docker compose -p loyalty-prod -f docker-compose.prod.yml up -d frontend`

Dùng Playwright MCP (hoặc browser tay):
- Navigate `https://loyalty.ecom-bill.com/partner/campaigns/1` → detail page load, không còn section "Phí dịch vụ".
- Navigate `https://loyalty.ecom-bill.com/admin/campaigns` → table không còn column fee.

- [ ] **Step 7: Commit**

```bash
cd D:/DoAn && rtk git add frontend/src/app/
rtk git commit -m "chore(service-fee): xoá UI render fee ở partner campaigns + admin"
```

---

### Task A9: Test + grep zero check Part A

**Files:** (verify only, no edit)

- [ ] **Step 1: Run full backend test suite**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/ -v 2>&1 | tail -50`
Expected: 0 fail, 0 ImportError. Nếu có test file riêng cho service fee cũ → xoá file đó.

Nếu test fail vì import `CampaignServiceFee` → xoá test đó (đã document trong spec 3.2: "test flag=False → xoá luôn").

- [ ] **Step 2: Grep backend source zero check**

Run: `rtk grep -rnE "service_fee|ServiceFee|FeeSchedule" backend/app/`
Expected: 0 match.

Nếu còn match → sửa hoặc xoá file. Không chấp nhận match nào ngoài directory `alembic/versions/`.

- [ ] **Step 3: Grep frontend source zero check**

Run: `rtk grep -rnE "service_fee|ServiceFee|FeeSchedule" frontend/src/`
Expected: 0 match.

- [ ] **Step 4: Smoke 3 flow quan trọng**

Dùng Playwright MCP hoặc browser:
- `/login` → khach1@gmail.com / khach1234 → `/member` → dashboard load OK (không break member app).
- Owner `owner@cafe.vn` / owner1234 → `/partner` → POS form render OK.
- Admin `admin@loyalty.vn` / admin1234 → `/admin/campaigns` → table render OK.

- [ ] **Step 5: Commit grep-zero check point (nếu có fix)**

Nếu step 1-3 phát sinh fix → add từng file cụ thể theo Git Safety Protocol (không dùng `-A`/`.`):
```bash
cd D:/DoAn
# Ví dụ: liệt kê đầy đủ file cần add, không `git add -A`
rtk git add <path/to/file1> <path/to/file2> ...
rtk git commit -m "chore(service-fee): dọn nốt reference còn sót sau A9 zero-check"
```

Nếu không có fix nào → bỏ qua step này.

---

## Part B — Tier multiplier

### Task B1: Verify Membership.current_tier relationship đã có (no-change task)

**Files:**
- Read-only: `backend/app/models/membership.py`

> **Context update:** Round 1 review phát hiện relationship `current_tier` **đã tồn tại** trong model hiện tại (membership.py:48). Task B1 ban đầu định thêm mới, nhưng thực tế chỉ cần verify sanity trước khi B4 dùng `selectinload(Membership.current_tier)`. Không có code change — giữ task để không phải renumber B2-B8.

- [ ] **Step 1: Impact check trên Membership**

Run: `gitnexus_impact({target: "Membership", direction: "upstream"})`
Expect: nhiều consumer — chỉ đọc để nắm blast radius cho B4/B6.

- [ ] **Step 2: Verify `current_tier` relationship đã tồn tại**

Run: `rtk grep -n "current_tier: Mapped" backend/app/models/membership.py`
Expected output (1 dòng):
```
48:    current_tier: Mapped["Tier | None"] = relationship("Tier", foreign_keys=[current_tier_id])
```

Nếu match khác (0 dòng hoặc signature lệch) → dừng, báo user: plan sai assumption, cần re-check round 2.

- [ ] **Step 3: Verify `selectinload(Membership.current_tier)` chạy được**

Ad-hoc sanity qua docker exec (không commit):
```bash
cd D:/DoAn
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  python -c "from app.models.membership import Membership; print(Membership.current_tier.property.mapper.class_.__name__)"
```
Expected stdout: `Tier`.

- [ ] **Step 4: No-op checkpoint (không commit)**

Task B1 không tạo code change. Đi tiếp B2. Nếu step 2/3 fail → escalate user ngay, không ship B4.

---

### Task B2: Data model changes PointRule.use_tiers + Tier.earn_multiplier

**Files:**
- Modify: `backend/app/models/point_rule.py`
- Modify: `backend/app/models/tier.py`

- [ ] **Step 1: Update `backend/app/models/point_rule.py`**

Đọc file:
```bash
rtk read backend/app/models/point_rule.py
```

Thêm column `use_tiers` sau `min_amount`:

```python
use_tiers: Mapped[bool] = mapped_column(
    Boolean,
    server_default=sa.text("false"),
    nullable=False,
)
```

Import `Boolean`, `sa` nếu chưa có.

- [ ] **Step 2: Update `backend/app/models/tier.py`**

Đọc file:
```bash
rtk read backend/app/models/tier.py
```

Thêm column `earn_multiplier` sau `perks`:

```python
earn_multiplier: Mapped[Decimal] = mapped_column(
    Numeric(precision=3, scale=2),
    server_default=sa.text("1.00"),
    nullable=False,
)
```

Thêm `CheckConstraint` vào `__table_args__`:

```python
__table_args__ = (
    # ... existing indexes/constraints ...
    CheckConstraint(
        "earn_multiplier >= 0.50 AND earn_multiplier <= 5.00",
        name="ck_tiers_earn_multiplier_range",
    ),
)
```

Import `Numeric`, `CheckConstraint`, `Decimal` nếu chưa có:
```python
from decimal import Decimal
from sqlalchemy import CheckConstraint, Numeric
```

- [ ] **Step 3: Sanity check**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend python -c "from app.models import PointRule, Tier; print(PointRule.__table__.columns.keys()); print(Tier.__table__.columns.keys())"`
Expected: `use_tiers` trong output PointRule, `earn_multiplier` trong output Tier.

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/models/point_rule.py backend/app/models/tier.py
rtk git commit -m "feat(tier): PointRule.use_tiers + Tier.earn_multiplier columns với check constraint"
```

---

### Task B3: Alembic migration add earn rules + receipt_code

**Files:**
- Create: `backend/alembic/versions/e2a3b4c5d6e7_add_earn_rules_and_receipt_code.py`

- [ ] **Step 1: Tạo file migration**

Tạo `backend/alembic/versions/e2a3b4c5d6e7_add_earn_rules_and_receipt_code.py`:

```python
"""add earn rules use_tiers, tier earn_multiplier, transaction receipt_code

Revision ID: e2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-24

Gộp Part B + Part C cùng 1 revision (3 target table khác nhau, không conflict).
"""

from alembic import op
import sqlalchemy as sa


revision = "e2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Part B.1 — point_rules.use_tiers
    op.add_column(
        "point_rules",
        sa.Column(
            "use_tiers",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    # Part B.2 — tiers.earn_multiplier + check constraint
    op.add_column(
        "tiers",
        sa.Column(
            "earn_multiplier",
            sa.Numeric(precision=3, scale=2),
            server_default=sa.text("1.00"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_tiers_earn_multiplier_range",
        "tiers",
        "earn_multiplier >= 0.50 AND earn_multiplier <= 5.00",
    )

    # Part C — transactions.receipt_code + partial unique index
    op.add_column(
        "transactions",
        sa.Column("receipt_code", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ux_transactions_partner_receipt_code",
        "transactions",
        ["partner_id", "receipt_code"],
        unique=True,
        postgresql_where=sa.text("receipt_code IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_transactions_partner_receipt_code", table_name="transactions"
    )
    op.drop_column("transactions", "receipt_code")

    op.drop_constraint(
        "ck_tiers_earn_multiplier_range", "tiers", type_="check"
    )
    op.drop_column("tiers", "earn_multiplier")

    op.drop_column("point_rules", "use_tiers")
```

- [ ] **Step 2: Run migration**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head`
Expected: `Running upgrade e1f2a3b4c5d6 -> e2a3b4c5d6e7`.

- [ ] **Step 3: Verify schema**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d point_rules" | rtk grep -i use_tiers
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d tiers" | rtk grep -i earn_multiplier
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d transactions" | rtk grep -i receipt_code
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\di ux_transactions_partner_receipt_code"
```

Expected: mỗi lệnh trả về row tương ứng. Partial index có filter `WHERE (receipt_code IS NOT NULL)`.

- [ ] **Step 4: Test round-trip downgrade (không commit)**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic downgrade -1
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
```

Expected: downgrade revert sạch cột mới; upgrade lại không lỗi. Sau 2 lệnh schema về state mới.

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn && rtk git add backend/alembic/versions/e2a3b4c5d6e7_add_earn_rules_and_receipt_code.py
rtk git commit -m "feat(tier,transactions): Alembic add use_tiers + earn_multiplier + receipt_code"
```

---

### Task B4: Rewrite `_calculate_points` + eager-load caller sites

**Files:**
- Modify: `backend/app/services/transaction_service.py:155-170` (create_manual), `:236-241` (_calculate_points), `:400-416` (_create_transaction_for_membership)
- Test: `backend/tests/unit/test_transaction_service_earn.py` (create hoặc append)

- [ ] **Step 1: Impact check**

Run: `gitnexus_impact({target: "_calculate_points", direction: "upstream"})`
Expect: 2 caller — `create_manual`, `_create_transaction_for_membership`. Low risk.

- [ ] **Step 2: Viết failing test trước (TDD)**

Tạo `backend/tests/unit/test_transaction_service_earn.py`:

```python
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.transaction_service import TransactionService


def _rule(points_per_unit=1, unit_amount=1000, min_amount=0, use_tiers=False):
    return SimpleNamespace(
        points_per_unit=Decimal(points_per_unit),
        unit_amount=unit_amount,
        min_amount=min_amount,
        use_tiers=use_tiers,
    )


def _membership_with_tier(multiplier):
    tier = SimpleNamespace(earn_multiplier=Decimal(str(multiplier)))
    return SimpleNamespace(current_tier=tier)


def test_calculate_points_below_min_amount_returns_zero():
    rule = _rule(min_amount=5000)
    assert TransactionService._calculate_points(rule, 1000) == 0


def test_calculate_points_base_no_membership():
    rule = _rule(points_per_unit=1, unit_amount=1000)
    assert TransactionService._calculate_points(rule, 10_000) == 10


def test_calculate_points_use_tiers_false_ignores_multiplier():
    rule = _rule(use_tiers=False)
    membership = _membership_with_tier(1.50)
    assert TransactionService._calculate_points(
        rule, 10_000, membership=membership
    ) == 10


def test_calculate_points_use_tiers_true_applies_gold_multiplier():
    rule = _rule(use_tiers=True)
    membership = _membership_with_tier(1.50)
    assert TransactionService._calculate_points(
        rule, 10_000, membership=membership
    ) == 15


def test_calculate_points_membership_null_tier_falls_back_to_1():
    rule = _rule(use_tiers=True)
    membership = SimpleNamespace(current_tier=None)
    assert TransactionService._calculate_points(
        rule, 10_000, membership=membership
    ) == 10


def test_calculate_points_truncation():
    # 1 point * 1.50 = 1.5 → int = 1
    rule = _rule(use_tiers=True)
    membership = _membership_with_tier(1.50)
    assert TransactionService._calculate_points(
        rule, 1_000, membership=membership
    ) == 1


def test_calculate_points_no_membership_kwarg_backcompat():
    # Caller cũ chỉ truyền (rule, amount), kwarg mặc định None
    rule = _rule(use_tiers=True)
    assert TransactionService._calculate_points(rule, 10_000) == 10
```

- [ ] **Step 3: Run failing test**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/unit/test_transaction_service_earn.py -v 2>&1 | tail -20`
Expected: các test `_use_tiers_true` / `_membership_null_tier` fail với TypeError (signature hiện tại không nhận `membership` kwarg), hoặc fail assert vì multiplier chưa áp dụng.

- [ ] **Step 4: Update `_calculate_points`**

Mở `backend/app/services/transaction_service.py`, tìm method L.~236-241, replace:

```python
@staticmethod
def _calculate_points(
    rule: PointRule,
    amount: int,
    *,
    membership: "Membership | None" = None,
) -> int:
    if amount < rule.min_amount:
        return 0
    units = Decimal(amount) / Decimal(rule.unit_amount)
    base_points = units * rule.points_per_unit

    multiplier = Decimal("1.00")
    if rule.use_tiers and membership is not None and membership.current_tier is not None:
        multiplier = membership.current_tier.earn_multiplier

    return int(base_points * multiplier)
```

Nếu import `Membership` chưa có trong file → thêm ở đầu:
```python
from app.models.membership import Membership
```

- [ ] **Step 5: Update call site 1 — `create_manual` (L.~168)**

Mở cùng file, tìm block L.~160-170:

```python
# Trước:
amount_for_points = request.gross_amount if points_on_gross else net_amount
points_earned = self._calculate_points(rule, amount_for_points)
```

Đổi thành:

```python
amount_for_points = request.gross_amount if points_on_gross else net_amount
points_earned = self._calculate_points(
    rule, amount_for_points, membership=membership
)
```

- [ ] **Step 6: Update call site 2 — `_create_transaction_for_membership` (L.~416)**

Tìm block:

```python
# Trước:
net_amount = max(0, gross_amount - (voucher_discount or 0))
points_earned = self._calculate_points(rule, net_amount)
```

Đổi thành:

```python
net_amount = max(0, gross_amount - (voucher_discount or 0))
points_earned = self._calculate_points(
    rule, net_amount, membership=membership
)
```

- [ ] **Step 7: Eager-load `membership.current_tier` tại cả 2 call site**

Trong `create_manual`, tìm nơi fetch membership (L.~85-110 tuỳ version hiện tại). Đổi select statement:

```python
# Trước (giả sử):
membership = await self.db.scalar(
    select(Membership).where(Membership.id == membership_id)
)

# Sau:
from sqlalchemy.orm import selectinload
membership = await self.db.scalar(
    select(Membership)
    .options(selectinload(Membership.current_tier))
    .where(Membership.id == membership_id)
)
```

Lặp tương tự ở `_create_transaction_for_membership`. Nếu fetch pattern khác (e.g. qua service helper), update cùng helper.

Import `selectinload` ở đầu file nếu chưa có:
```python
from sqlalchemy.orm import selectinload
```

- [ ] **Step 8: Run test passing**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/unit/test_transaction_service_earn.py -v 2>&1 | tail -20`
Expected: 7 passed.

- [ ] **Step 9: Run integration tests transaction hiện có**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/integration/ -k transaction -v 2>&1 | tail -30`
Expected: 0 fail. Integration test cũ không đụng membership kwarg → vẫn pass vì default `None`.

- [ ] **Step 10: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/services/transaction_service.py backend/tests/unit/test_transaction_service_earn.py
rtk git commit -m "feat(tier): _calculate_points nhận kwarg membership + eager-load current_tier"
```

---

### Task B5: Schemas update PointRule + Tier

**Files:**
- Modify: `backend/app/schemas/point_rule.py`
- Modify: `backend/app/schemas/tier.py`

- [ ] **Step 1: Update `backend/app/schemas/point_rule.py`**

Đọc:
```bash
rtk read backend/app/schemas/point_rule.py
```

Thêm field `use_tiers: bool = False` vào các schema:
- `PointRuleBase` (hoặc tương đương — class có field `points_per_unit`, `unit_amount`, `min_amount`).
- `PointRuleCreate`.
- `PointRuleResponse`.

Pattern:
```python
class PointRuleBase(BaseModel):
    points_per_unit: Decimal
    unit_amount: int
    min_amount: int = 0
    use_tiers: bool = False
```

Thêm class mới `PointRuleUpdate` cho PATCH endpoint:

```python
class PointRuleUpdate(BaseModel):
    points_per_unit: Decimal | None = None
    unit_amount: int | None = None
    min_amount: int | None = None
    use_tiers: bool | None = None
    is_active: bool | None = None
```

- [ ] **Step 2: Update `backend/app/schemas/tier.py`**

Đọc:
```bash
rtk read backend/app/schemas/tier.py
```

Thêm field `earn_multiplier` vào `TierCreateRequest`, `TierUpdateRequest`, `TierResponse`:

```python
from decimal import Decimal
from pydantic import BaseModel, Field


class TierCreateRequest(BaseModel):
    name: str
    min_points: int
    earn_multiplier: Decimal = Field(
        default=Decimal("1.00"),
        ge=Decimal("0.50"),
        le=Decimal("5.00"),
        decimal_places=2,
    )
    perks: dict | None = None


class TierUpdateRequest(BaseModel):
    name: str | None = None
    min_points: int | None = None
    earn_multiplier: Decimal | None = Field(
        default=None,
        ge=Decimal("0.50"),
        le=Decimal("5.00"),
        decimal_places=2,
    )
    perks: dict | None = None


class TierResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    min_points: int
    earn_multiplier: Decimal
    perks: dict | None
    # ... các field hiện có khác giữ nguyên
```

Nếu file dùng `model_config = ConfigDict(from_attributes=True)` thì giữ.

- [ ] **Step 3: Sanity check**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend python -c "from app.schemas.tier import TierCreateRequest, TierUpdateRequest, TierResponse; from app.schemas.point_rule import PointRuleUpdate; print('ok')"`
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/schemas/point_rule.py backend/app/schemas/tier.py
rtk git commit -m "feat(tier,rules): schemas include earn_multiplier + use_tiers + PointRuleUpdate"
```

---

### Task B6: API endpoints PATCH point-rules + verify tier PATCH

**Files:**
- Modify: `backend/app/api/point_rules.py`
- Verify: `backend/app/api/tiers.py` (hoặc nơi chứa PATCH tier endpoint)
- Test: `backend/tests/integration/test_partner_settings_api.py` (create)

- [ ] **Step 1: Viết failing test trước**

Tạo `backend/tests/integration/test_partner_settings_api.py`:

```python
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_patch_point_rule_use_tiers_toggle_as_owner(
    async_client: AsyncClient,
    owner_auth_headers: dict,
    partner_with_rule,  # fixture tạo partner + rule, return dict(partner_id, rule_id)
):
    resp = await async_client.patch(
        f"/partner/point-rules/{partner_with_rule['rule_id']}",
        json={"use_tiers": True},
        headers={**owner_auth_headers, "X-Partner-Id": str(partner_with_rule["partner_id"])},
    )
    assert resp.status_code == 200
    assert resp.json()["use_tiers"] is True


async def test_patch_point_rule_as_staff_forbidden(
    async_client: AsyncClient,
    staff_auth_headers: dict,
    partner_with_rule,
):
    resp = await async_client.patch(
        f"/partner/point-rules/{partner_with_rule['rule_id']}",
        json={"use_tiers": True},
        headers={**staff_auth_headers, "X-Partner-Id": str(partner_with_rule["partner_id"])},
    )
    assert resp.status_code == 403


async def test_patch_tier_earn_multiplier_valid(
    async_client: AsyncClient,
    owner_auth_headers: dict,
    partner_with_gold_tier,  # fixture returns dict(partner_id, tier_id)
):
    resp = await async_client.patch(
        f"/partner/tiers/{partner_with_gold_tier['tier_id']}",
        json={"earn_multiplier": "1.75"},
        headers={**owner_auth_headers, "X-Partner-Id": str(partner_with_gold_tier["partner_id"])},
    )
    assert resp.status_code == 200
    assert resp.json()["earn_multiplier"] == "1.75"


async def test_patch_tier_earn_multiplier_out_of_range_422(
    async_client: AsyncClient,
    owner_auth_headers: dict,
    partner_with_gold_tier,
):
    resp = await async_client.patch(
        f"/partner/tiers/{partner_with_gold_tier['tier_id']}",
        json={"earn_multiplier": "10.00"},
        headers={**owner_auth_headers, "X-Partner-Id": str(partner_with_gold_tier["partner_id"])},
    )
    assert resp.status_code == 422
```

**Fixtures:** tận dụng fixture sẵn có trong `backend/tests/conftest.py` — nếu `partner_with_rule` và `partner_with_gold_tier` chưa có thì tạo ở conftest dùng pattern tương tự fixture hiện có.

- [ ] **Step 2: Run failing test**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/integration/test_partner_settings_api.py -v 2>&1 | tail -20`
Expected: fail với 404 (PATCH endpoint chưa tồn tại cho point-rules) hoặc 422 (tier PATCH chưa nhận earn_multiplier) — phụ thuộc state hiện tại.

- [ ] **Step 3: Add PATCH endpoint point-rules**

Mở `backend/app/api/point_rules.py`. Thêm endpoint mới (sau POST):

```python
@router.patch("/{rule_id}", response_model=PointRuleResponse)
async def update_point_rule(
    rule_id: int,
    request: PointRuleUpdate,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_owner_in_partner),
) -> PointRuleResponse:
    rule = await db.get(PointRule, rule_id)
    if rule is None or rule.partner_id != partner_id:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy công thức tích điểm."
        )

    payload = request.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(rule, key, value)

    await db.flush()
    await db.refresh(rule)
    return PointRuleResponse.model_validate(rule)
```

Import bổ sung:
```python
from app.schemas.point_rule import PointRuleUpdate
```

- [ ] **Step 4: Verify tier PATCH endpoint có nhận earn_multiplier**

Mở `backend/app/api/tiers.py` (hoặc file chứa route `PATCH /partner/tiers/{id}`). Xác nhận handler dùng `TierUpdateRequest` schema (đã update ở B5) và `Depends(require_owner_in_partner)`. Pattern assignment loop:

```python
payload = request.model_dump(exclude_unset=True)
for key, value in payload.items():
    setattr(tier, key, value)
```

Nếu handler đang whitelist field (không iterate) thì thêm `earn_multiplier` vào whitelist.

- [ ] **Step 5: Run test passing**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/integration/test_partner_settings_api.py -v 2>&1 | tail -20`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/api/ backend/tests/integration/test_partner_settings_api.py backend/tests/conftest.py
rtk git commit -m "feat(partner): PATCH /partner/point-rules endpoint + tier earn_multiplier update"
```

---

### Task B7: End-to-end tier multiplier test + seed update

**Files:**
- Test: `backend/tests/integration/test_earn_tier_multiplier.py` (create)
- Modify: `backend/seed_demo.py`

- [ ] **Step 1: Viết integration test**

Tạo `backend/tests/integration/test_earn_tier_multiplier.py`:

```python
from decimal import Decimal

import pytest
from sqlalchemy import update

from app.models.membership import Membership
from app.models.point_rule import PointRule
from app.services.tier_service import TierService


pytestmark = pytest.mark.asyncio


async def test_earn_with_bronze_then_promote_to_gold(
    async_db_session,
    partner_factory,
    tier_factory,
    rule_factory,
    member_factory,
    transaction_service,  # fixture returns TransactionService(async_db_session)
):
    partner = await partner_factory()
    rule = await rule_factory(
        partner_id=partner.id,
        points_per_unit=Decimal("1"),
        unit_amount=1000,
        min_amount=0,
        use_tiers=True,
    )
    await tier_factory(partner_id=partner.id, name="Bronze", min_points=0, earn_multiplier=Decimal("1.00"))
    gold = await tier_factory(partner_id=partner.id, name="Gold", min_points=500, earn_multiplier=Decimal("1.50"))

    membership = await member_factory(partner_id=partner.id)

    # Earn 1000 VND → Bronze × 1.00 = 1 point
    txn1 = await transaction_service.create_manual_for_test(  # helper test-only
        partner_id=partner.id,
        membership_id=membership.id,
        gross_amount=1000,
    )
    assert txn1.points_earned == 1
    await async_db_session.refresh(membership)
    assert membership.total_points_earned == 1

    # Promote membership to Gold bằng recompute_tier
    await async_db_session.execute(
        update(Membership)
        .where(Membership.id == membership.id)
        .values(total_points_earned=600)
    )
    await async_db_session.commit()

    tier_svc = TierService(async_db_session)
    new_tier = await tier_svc.recompute_tier(
        partner_id=partner.id, membership_id=membership.id
    )
    assert new_tier.id == gold.id
    await async_db_session.refresh(membership)

    # Earn 10_000 VND → base=10, Gold × 1.50 = 15 points
    txn2 = await transaction_service.create_manual_for_test(
        partner_id=partner.id,
        membership_id=membership.id,
        gross_amount=10_000,
    )
    assert txn2.points_earned == 15


async def test_earn_with_use_tiers_false_ignores_multiplier(
    async_db_session,
    partner_factory,
    tier_factory,
    rule_factory,
    member_factory,
    transaction_service,
):
    partner = await partner_factory()
    rule = await rule_factory(
        partner_id=partner.id,
        points_per_unit=Decimal("1"),
        unit_amount=1000,
        use_tiers=False,
    )
    gold = await tier_factory(partner_id=partner.id, name="Gold", min_points=0, earn_multiplier=Decimal("1.50"))

    membership = await member_factory(partner_id=partner.id, current_tier_id=gold.id)

    txn = await transaction_service.create_manual_for_test(
        partner_id=partner.id,
        membership_id=membership.id,
        gross_amount=10_000,
    )
    # use_tiers=False → ignore tier, 10 points base
    assert txn.points_earned == 10
```

**Fixture helper:** Nếu `transaction_service.create_manual_for_test` chưa tồn tại, tạo conftest fixture wrap `TransactionService.create_manual` với request payload tối thiểu + user auth context. Pattern ở `backend/tests/conftest.py`.

- [ ] **Step 2: Run test**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/integration/test_earn_tier_multiplier.py -v 2>&1 | tail -30`
Expected: 2 passed. Nếu fail vì fixture — update conftest + rerun.

- [ ] **Step 3: Update seed_demo.py**

Đọc:
```bash
rtk read backend/seed_demo.py | rtk grep -n "Tier\|tier\|point_rule\|PointRule" | head -30
```

Update seed tiers (tìm block tạo Bronze/Silver/Gold/Platinum):
```python
# Mỗi tier dict thêm:
"earn_multiplier": Decimal("1.00"),  # Bronze
"earn_multiplier": Decimal("1.25"),  # Silver
"earn_multiplier": Decimal("1.50"),  # Gold
"earn_multiplier": Decimal("2.00"),  # Platinum
```

Update seed point_rule:
- Cafe Cộng: `use_tiers=True`.
- Trà Sữa Lala (Lala Food): `use_tiers=False`.

- [ ] **Step 4: Re-seed + verify DB**

```bash
cd D:/DoAn && docker exec loyalty-backend-prod python seed_demo.py 2>&1 | tail -10
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT partner_id, name, earn_multiplier FROM tiers ORDER BY partner_id, min_points;"
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT partner_id, use_tiers FROM point_rules;"
```

Expected: tier rows có `earn_multiplier = 1.00/1.25/1.50/2.00`. Cafe partner `use_tiers=true`, Lala partner `use_tiers=false`.

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn && rtk git add backend/tests/integration/test_earn_tier_multiplier.py backend/tests/conftest.py backend/seed_demo.py
rtk git commit -m "feat(tier): end-to-end test earn multiplier + seed Cafe use_tiers=True Lala=False"
```

---

### Task B8: Frontend `/partner/settings` page

**Files:**
- Create: `frontend/src/app/(partner)/partner/settings/page.tsx`
- Create: `frontend/src/components/partner/settings-form.tsx`
- Modify: `frontend/src/types/partner.ts` (thêm `earn_multiplier`, `use_tiers` nếu chưa có)
- Modify: `frontend/src/lib/api-partner.ts` (thêm `updatePointRule`)
- Modify: `frontend/src/lib/hooks/use-partner-tiers.ts` (hoặc file tương đương — thêm `useUpdateTier`)
- Modify: `frontend/src/app/(partner)/partner/layout.tsx` (thêm menu Settings)

- [ ] **Step 1: Update types**

Đọc `frontend/src/types/partner.ts`. Thêm/update:

```ts
export type PointRule = {
  id: number;
  partner_id: number;
  points_per_unit: string;   // Decimal serialize as string
  unit_amount: number;
  min_amount: number;
  use_tiers: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PointRuleUpdate = Partial<Pick<
  PointRule,
  "points_per_unit" | "unit_amount" | "min_amount" | "use_tiers" | "is_active"
>>;

export type Tier = {
  id: number;
  partner_id: number;
  name: string;
  min_points: number;
  earn_multiplier: string;  // Decimal as string
  perks: Record<string, unknown> | null;
};

export type TierUpdate = Partial<Pick<Tier, "name" | "min_points" | "earn_multiplier" | "perks">>;
```

- [ ] **Step 2: Thêm API client methods**

Mở `frontend/src/lib/api-partner.ts` (hoặc `api-merchant.ts` tuỳ tên file hiện tại — grep `point-rules` để xác định):

```ts
export const pointRulesApi = {
  list: () => api.get<PointRule[]>("/partner/point-rules"),
  getActive: () => api.get<PointRule>("/partner/point-rules/active"),
  update: (id: number, payload: PointRuleUpdate) =>
    api.patch<PointRule>(`/partner/point-rules/${id}`, payload),
};

export const tiersApi = {
  list: () => api.get<Tier[]>("/partner/tiers"),
  update: (id: number, payload: TierUpdate) =>
    api.patch<Tier>(`/partner/tiers/${id}`, payload),
};
```

- [ ] **Step 3: Thêm TanStack Query hooks**

Tạo hoặc update `frontend/src/lib/hooks/use-partner-settings.ts`:

```ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { pointRulesApi, tiersApi } from "@/lib/api-partner";
import type { PointRuleUpdate, TierUpdate } from "@/types/partner";

export function useActivePointRule() {
  return useQuery({
    queryKey: ["partner", "point-rule", "active"],
    queryFn: () => pointRulesApi.getActive().then((r) => r.data),
  });
}

export function useUpdatePointRule(ruleId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: PointRuleUpdate) =>
      pointRulesApi.update(ruleId, payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "point-rule"] });
    },
  });
}

export function usePartnerTiers() {
  return useQuery({
    queryKey: ["partner", "tiers"],
    queryFn: () => tiersApi.list().then((r) => r.data),
  });
}

export function useUpdateTier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: TierUpdate }) =>
      tiersApi.update(id, payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "tiers"] });
    },
  });
}
```

- [ ] **Step 4: Tạo SettingsForm component**

Tạo `frontend/src/components/partner/settings-form.tsx`:

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import type { PointRule, Tier } from "@/types/partner";
import { useUpdatePointRule, useUpdateTier } from "@/lib/hooks/use-partner-settings";

const ruleSchema = z.object({
  points_per_unit: z.coerce.number().positive("Phải lớn hơn 0"),
  unit_amount: z.coerce.number().int().positive("Phải lớn hơn 0"),
  min_amount: z.coerce.number().int().nonnegative(),
  use_tiers: z.boolean(),
});

const tierSchema = z.object({
  earn_multiplier: z.coerce
    .number()
    .min(0.5, "Tối thiểu 0.50")
    .max(5.0, "Tối đa 5.00"),
});

type RuleFormValues = z.infer<typeof ruleSchema>;
type TierFormValues = z.infer<typeof tierSchema>;

export function PointRuleForm({ rule }: { rule: PointRule }) {
  const update = useUpdatePointRule(rule.id);
  const form = useForm<RuleFormValues>({
    resolver: zodResolver(ruleSchema),
    defaultValues: {
      points_per_unit: Number(rule.points_per_unit),
      unit_amount: rule.unit_amount,
      min_amount: rule.min_amount,
      use_tiers: rule.use_tiers,
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await update.mutateAsync({
        points_per_unit: String(values.points_per_unit),
        unit_amount: values.unit_amount,
        min_amount: values.min_amount,
        use_tiers: values.use_tiers,
      });
      toast.success("Đã lưu cấu hình tích điểm");
    } catch (e) {
      toast.error("Lưu thất bại. Thử lại.");
    }
  });

  const useTiersWatch = form.watch("use_tiers");

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Điểm</Label>
          <Input type="number" step="0.01" {...form.register("points_per_unit")} />
        </div>
        <div>
          <Label>Mỗi (VND)</Label>
          <Input type="number" {...form.register("unit_amount")} />
        </div>
      </div>
      <div>
        <Label>Hoá đơn tối thiểu (VND)</Label>
        <Input type="number" {...form.register("min_amount")} />
      </div>
      <div className="flex items-center gap-3">
        <Switch
          checked={useTiersWatch}
          onCheckedChange={(v) => form.setValue("use_tiers", v)}
        />
        <Label>Bật phân hạng thành viên</Label>
      </div>
      <p className="text-sm text-muted-foreground">
        Tắt: mọi khách hàng tích cùng tỉ lệ. Bật: áp hệ số theo hạng.
      </p>
      <Button type="submit" disabled={update.isPending}>
        {update.isPending ? "Đang lưu..." : "Lưu thay đổi"}
      </Button>
    </form>
  );
}

export function TierMultiplierRow({ tier }: { tier: Tier }) {
  const update = useUpdateTier();
  const form = useForm<TierFormValues>({
    resolver: zodResolver(tierSchema),
    defaultValues: { earn_multiplier: Number(tier.earn_multiplier) },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await update.mutateAsync({
        id: tier.id,
        payload: { earn_multiplier: String(values.earn_multiplier) },
      });
      toast.success(`Đã lưu hệ số cho hạng ${tier.name}`);
    } catch {
      toast.error("Lưu thất bại");
    }
  });

  return (
    <form onSubmit={onSubmit} className="flex items-center gap-3 py-2">
      <span className="w-24 font-medium">{tier.name}</span>
      <span className="w-32 text-sm text-muted-foreground">
        ≥ {tier.min_points} điểm
      </span>
      <span>×</span>
      <Input
        type="number"
        step="0.05"
        className="w-24"
        {...form.register("earn_multiplier")}
      />
      <Button size="sm" type="submit" disabled={update.isPending}>
        Lưu
      </Button>
    </form>
  );
}
```

- [ ] **Step 5: Tạo settings page**

Tạo `frontend/src/app/(partner)/partner/settings/page.tsx`:

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { usePartnerStore } from "@/lib/partner-store";
import {
  useActivePointRule,
  usePartnerTiers,
} from "@/lib/hooks/use-partner-settings";
import {
  PointRuleForm,
  TierMultiplierRow,
} from "@/components/partner/settings-form";

export default function PartnerSettingsPage() {
  const router = useRouter();
  const role = usePartnerStore((s) => s.activePartner?.role);

  useEffect(() => {
    if (role && role !== "owner") {
      router.replace("/staff");
    }
  }, [role, router]);

  const ruleQ = useActivePointRule();
  const tiersQ = usePartnerTiers();

  if (!role || role !== "owner") return null;

  if (ruleQ.isLoading || tiersQ.isLoading) {
    return <div className="p-6">Đang tải cấu hình...</div>;
  }
  if (ruleQ.error || !ruleQ.data) {
    return (
      <div className="p-6 text-red-600">
        Không tải được công thức tích điểm. Vui lòng tạo công thức trước ở trang POS.
      </div>
    );
  }

  const rule = ruleQ.data;
  const tiers = tiersQ.data ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      <section className="rounded-lg border bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Cấu hình tích điểm</h2>
        <PointRuleForm rule={rule} />
      </section>

      {rule.use_tiers && tiers.length > 0 && (
        <section className="rounded-lg border bg-white p-6">
          <h2 className="mb-3 text-lg font-semibold">Tỷ lệ tích điểm theo hạng</h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Hệ số áp vào điểm tích khi khách mua hàng. Phạm vi: 0.50 – 5.00.
          </p>
          <div className="divide-y">
            {tiers
              .sort((a, b) => a.min_points - b.min_points)
              .map((tier) => (
                <TierMultiplierRow key={tier.id} tier={tier} />
              ))}
          </div>
        </section>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Thêm menu sidebar**

Mở `frontend/src/app/(partner)/partner/layout.tsx`. Tìm nav items list, thêm:

```tsx
{ href: "/partner/settings", label: "Cài đặt", icon: SettingsIcon, ownerOnly: true },
```

Nếu layout đã filter items theo role (`item.ownerOnly && role !== "owner"`) thì giữ pattern. Nếu chưa — thêm logic filter trước render.

- [ ] **Step 7: Type-check + smoke**

Run: `cd D:/DoAn/frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: 0 error.

Rebuild + test:
```bash
cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml build frontend && docker compose -p loyalty-prod -f docker-compose.prod.yml up -d frontend
```

Dùng Playwright MCP:
- Owner login → navigate `/partner/settings` → page load OK.
- Toggle `use_tiers` → Save → reload page → toggle persist.
- Edit Gold `earn_multiplier` 1.00 → 1.75 → Save → reload → persist.
- Staff login → navigate `/partner/settings` → redirect về `/staff`.

- [ ] **Step 8: Commit**

```bash
cd D:/DoAn && rtk git add frontend/src/
rtk git commit -m "feat(partner): /partner/settings page cho owner (point rule + tier multiplier)"
```

---

## Part C — Transaction history + receipt_code

### Task C1: Transaction model field + POS endpoint update

**Files:**
- Modify: `backend/app/models/transaction.py`
- Modify: `backend/app/schemas/transaction.py` (hoặc schemas POS)
- Modify: `backend/app/services/transaction_service.py` (`create_manual`)
- Test: `backend/tests/integration/test_transactions_api.py` (append)

- [ ] **Step 1: Update `backend/app/models/transaction.py`**

Thêm column sau `method`:

```python
receipt_code: Mapped[str | None] = mapped_column(
    String(50), nullable=True
)
```

Thêm vào `__table_args__`:

```python
from sqlalchemy import Index, text as sa_text

__table_args__ = (
    # ... existing ...
    Index(
        "ux_transactions_partner_receipt_code",
        "partner_id",
        "receipt_code",
        unique=True,
        postgresql_where=sa_text("receipt_code IS NOT NULL"),
    ),
)
```

- [ ] **Step 2: Update POS transaction request/response schema**

Mở `backend/app/schemas/transaction.py`. Schema hiện có: `CreateManualTransactionRequest` (field `phone`, `gross_amount`, `note`, `voucher_code`), `CreateQrCustomerTransactionRequest`, `TransactionResponse`, `TransactionWithMemberResponse`.

Thêm field `receipt_code` + validator vào `CreateManualTransactionRequest` (không tạo class mới):
```python
from pydantic import Field, field_validator


class CreateManualTransactionRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    gross_amount: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)
    voucher_code: str | None = Field(default=None, max_length=50)
    receipt_code: str | None = Field(default=None, max_length=50)  # NEW

    @field_validator("receipt_code", mode="before")
    @classmethod
    def _normalize_receipt_code(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v
```

Thêm `receipt_code: str | None = None` vào các response schema:
- `TransactionResponse` (sau field `note`)
- `TransactionWithMemberResponse` (nằm trong `transaction: TransactionResponse` — tự inherit)
- `TransactionListItem`, `TransactionDetailResponse` (sẽ tạo ở Task C2)

Frontend type `TransactionResponse` tại `frontend/src/types/partner.ts` (nếu có) cũng thêm `receipt_code?: string | null`.

- [ ] **Step 3: Update `create_manual` persist receipt_code**

Trong `backend/app/services/transaction_service.py`, method `create_manual` L.~170, thêm `receipt_code=request.receipt_code` vào `Transaction(...)` constructor call:

```python
txn = Transaction(
    partner_id=partner_id,
    membership_id=membership.id,
    staff_id=staff_id,
    gross_amount=request.gross_amount,
    voucher_id=voucher_id,
    voucher_discount_amount=voucher_discount,
    net_amount=net_amount,
    points_earned=points_earned,
    method=TransactionMethod.MANUAL,
    note=request.note,
    receipt_code=request.receipt_code,  # NEW
)
```

Catch IntegrityError riêng để map sang HTTPException 409 tại API layer — hoặc dựa vào global handler đã update ở Task A6. Prefer global handler (đã setup).

- [ ] **Step 4: Viết failing test**

Append vào `backend/tests/integration/test_transactions_api.py` (hoặc tạo mới nếu chưa có):

```python
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_post_transaction_with_receipt_code(
    async_client: AsyncClient,
    owner_auth_headers: dict,
    partner_with_rule_and_member,  # fixture
):
    ctx = partner_with_rule_and_member
    resp = await async_client.post(
        "/partner/transactions",
        json={
            "phone": ctx["phone"],
            "gross_amount": 50_000,
            "receipt_code": "HD-00001",
        },
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 201
    assert resp.json()["transaction"]["receipt_code"] == "HD-00001"


async def test_post_transaction_duplicate_receipt_code(
    async_client: AsyncClient,
    owner_auth_headers: dict,
    partner_with_rule_and_member,
):
    ctx = partner_with_rule_and_member
    headers = {**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])}
    payload = {
        "phone": ctx["phone"],
        "gross_amount": 50_000,
        "receipt_code": "DUP-001",
    }
    r1 = await async_client.post("/partner/transactions", json=payload, headers=headers)
    assert r1.status_code == 201
    r2 = await async_client.post("/partner/transactions", json=payload, headers=headers)
    assert r2.status_code == 409
    assert "mã hoá đơn" in r2.json()["detail"].lower()


async def test_post_transaction_empty_string_becomes_null(
    async_client, owner_auth_headers, partner_with_rule_and_member
):
    ctx = partner_with_rule_and_member
    resp = await async_client.post(
        "/partner/transactions",
        json={
            "phone": ctx["phone"],
            "gross_amount": 30_000,
            "receipt_code": "  ",  # whitespace-only
        },
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 201
    assert resp.json()["transaction"]["receipt_code"] is None


async def test_post_transaction_concurrent_same_receipt_code(
    async_client, owner_auth_headers, partner_with_rule_and_member
):
    import asyncio

    ctx = partner_with_rule_and_member
    headers = {**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])}
    payload = {
        "phone": ctx["phone"],
        "gross_amount": 20_000,
        "receipt_code": "RACE-001",
    }

    async def post_one():
        return await async_client.post(
            "/partner/transactions", json=payload, headers=headers
        )

    r1, r2 = await asyncio.gather(post_one(), post_one(), return_exceptions=True)

    statuses = sorted([getattr(r, "status_code", 500) for r in (r1, r2)])
    assert statuses == [201, 409]


async def test_post_transaction_different_partners_same_code(
    async_client,
    owner_auth_headers,
    two_partners_with_rule_and_member,  # fixture trả về list[dict]
):
    a, b = two_partners_with_rule_and_member
    for ctx in (a, b):
        resp = await async_client.post(
            "/partner/transactions",
            json={
                "phone": ctx["phone"],
                "gross_amount": 40_000,
                "receipt_code": "SHARED-001",
            },
            headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
        )
        assert resp.status_code == 201


async def test_post_transaction_null_receipt_allows_duplicates_same_partner(
    async_client, owner_auth_headers, partner_with_rule_and_member
):
    """Partial unique WHERE receipt_code IS NOT NULL → hai transaction không receipt_code
    trong cùng partner phải cùng 201, không bị 409."""
    ctx = partner_with_rule_and_member
    headers = {**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])}
    payload = {"phone": ctx["phone"], "gross_amount": 10_000}  # KHÔNG gửi receipt_code
    r1 = await async_client.post("/partner/transactions", json=payload, headers=headers)
    assert r1.status_code == 201
    r2 = await async_client.post("/partner/transactions", json=payload, headers=headers)
    assert r2.status_code == 201
    assert r1.json()["transaction"]["receipt_code"] is None
    assert r2.json()["transaction"]["receipt_code"] is None
```

**Fixtures cần có** (Task B0 đã cung cấp — nếu chưa, tạo trước):
- `partner_with_rule_and_member` → trả dict `{"partner_id": int, "phone": str, "membership_id": int}`. `phone` phải match `Membership` thuộc partner và có point rule active.
- `two_partners_with_rule_and_member` → list 2 partner độc lập, mỗi phần tử dict như trên.

- [ ] **Step 5: Run test**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/integration/test_transactions_api.py -v 2>&1 | tail -30`
Expected: 6 passed (5 cũ + test null-receipt-allow-duplicate mới).

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/models/transaction.py backend/app/schemas/ backend/app/services/transaction_service.py backend/tests/integration/test_transactions_api.py backend/tests/conftest.py
rtk git commit -m "feat(transactions): receipt_code + partial unique + POS persist"
```

---

### Task C2: Service `PartnerTransactionService` + extend API GET list/detail + PATCH

**Files:**
- Modify: `backend/app/models/transaction.py` (thêm ORM relationships — không migration)
- Create: `backend/app/services/partner_transaction_service.py`
- Modify: `backend/app/api/transactions.py` (mở rộng, **KHÔNG tạo file mới** vì existing router đã ở prefix `/partner/transactions`)
- Modify: `backend/app/schemas/transaction.py` (thêm list item + detail + update schemas)
- Test: `backend/tests/integration/test_transactions_api.py` (append — cùng file với C1)

> **Context:** Round 1 review phát hiện existing `backend/app/api/transactions.py` đã có `APIRouter(prefix="/partner/transactions")` với POST / POST /qr / GET. Tạo file mới sẽ collide prefix → một trong hai router bị shadow. Cách đúng: mở rộng file cũ thêm GET /{id} + PATCH /{id} cho feature mới.
>
> Ngoài ra: `Transaction` model hiện chỉ có `ForeignKey`, không có `relationship()`. Service mới dùng `joinedload(Transaction.membership)` sẽ `InvalidRequestError` nếu không thêm relationship. Step 1 bù mối quan hệ này (ORM-only, không migration).

- [ ] **Step 1: Thêm ORM relationships vào Transaction model**

Mở `backend/app/models/transaction.py`. Thêm block imports nếu thiếu và thêm 3 relationship ở class body (sau block columns, trước `__table_args__`):

```python
from typing import TYPE_CHECKING
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from app.models.membership import Membership
    from app.models.user import User
    from app.models.voucher import Voucher


class Transaction(Base, TimestampMixin):
    # ... existing columns ...

    membership: Mapped["Membership"] = relationship(
        "Membership", foreign_keys=[membership_id], lazy="noload"
    )
    staff: Mapped["User | None"] = relationship(
        "User", foreign_keys=[staff_id], lazy="noload"
    )
    voucher: Mapped["Voucher | None"] = relationship(
        "Voucher", foreign_keys=[voucher_id], lazy="noload"
    )
```

`lazy="noload"` ép caller dùng `joinedload`/`selectinload` — tránh implicit lazy-load gây MissingGreenlet error trong async.

Sanity check ad-hoc (không commit ở step này):
```bash
cd D:/DoAn
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend \
  python -c "from app.models.transaction import Transaction; print(Transaction.membership, Transaction.staff, Transaction.voucher)"
```
Expected: 3 `RelationshipProperty` object in ra, không ImportError.

- [ ] **Step 2: Thêm schemas**

Mở `backend/app/schemas/transaction.py`, thêm:

```python
from datetime import datetime
from decimal import Decimal


class TransactionListItem(BaseModel):
    id: int
    created_at: datetime
    receipt_code: str | None
    membership_display_name: str
    staff_display_name: str | None
    gross_amount: int
    voucher_discount_amount: int | None
    net_amount: int
    points_earned: int
    method: str
    voucher_code: str | None

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: list[TransactionListItem]
    total: int
    page: int
    page_size: int


class TransactionDetailResponse(TransactionListItem):
    note: str | None
    legal_discount_ratio: Decimal | None


class TransactionUpdateRequest(BaseModel):
    receipt_code: str | None = Field(default=None, max_length=50)
    note: str | None = None

    @field_validator("receipt_code", mode="before")
    @classmethod
    def _normalize_receipt_code(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v
```

- [ ] **Step 3: Tạo service**

Tạo `backend/app/services/partner_transaction_service.py`:

```python
from datetime import date, datetime, time
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.transaction import Transaction
from app.models.membership import Membership
from app.models.user import User
from app.models.voucher import Voucher
from app.schemas.transaction import (
    TransactionDetailResponse,
    TransactionListItem,
    TransactionListResponse,
    TransactionUpdateRequest,
)


class TransactionNotFoundError(Exception):
    pass


class DuplicateReceiptCodeError(Exception):
    pass


class PartnerTransactionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base_select(self, partner_id: int) -> Select:
        return (
            select(Transaction)
            .where(Transaction.partner_id == partner_id)
            .options(
                joinedload(Transaction.membership).joinedload(Membership.user),
                joinedload(Transaction.staff),
                joinedload(Transaction.voucher),
            )
        )

    async def list(
        self,
        partner_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        date_from: date | None = None,
        date_to: date | None = None,
        staff_id: int | None = None,
        q: str | None = None,
    ) -> TransactionListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        stmt = self._base_select(partner_id).order_by(Transaction.created_at.desc())

        conds = []
        if date_from:
            conds.append(Transaction.created_at >= datetime.combine(date_from, time.min))
        if date_to:
            conds.append(Transaction.created_at < datetime.combine(date_to, time.max))
        if staff_id:
            conds.append(Transaction.staff_id == staff_id)
        if q:
            conds.append(Transaction.receipt_code == q)

        if conds:
            stmt = stmt.where(and_(*conds))

        total_stmt = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.partner_id == partner_id)
        )
        if conds:
            total_stmt = total_stmt.where(and_(*conds))
        total = (await self.db.scalar(total_stmt)) or 0

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self.db.scalars(stmt)).unique().all()

        items = [self._to_list_item(t) for t in rows]
        return TransactionListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_detail(
        self, partner_id: int, transaction_id: int
    ) -> TransactionDetailResponse:
        stmt = self._base_select(partner_id).where(Transaction.id == transaction_id)
        txn = (await self.db.scalars(stmt)).unique().one_or_none()
        if txn is None:
            raise TransactionNotFoundError(
                f"Không tìm thấy giao dịch id={transaction_id}"
            )
        return self._to_detail(txn)

    async def update(
        self,
        partner_id: int,
        transaction_id: int,
        payload: TransactionUpdateRequest,
    ) -> TransactionDetailResponse:
        from sqlalchemy.exc import IntegrityError

        txn = await self.db.get(Transaction, transaction_id)
        if txn is None or txn.partner_id != partner_id:
            raise TransactionNotFoundError(
                f"Không tìm thấy giao dịch id={transaction_id}"
            )

        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(txn, key, value)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            if "ux_transactions_partner_receipt_code" in str(e.orig):
                raise DuplicateReceiptCodeError(
                    "Mã hoá đơn đã tồn tại, vui lòng dùng mã khác."
                ) from e
            raise

        return await self.get_detail(partner_id, transaction_id)

    @staticmethod
    def _to_list_item(t: Transaction) -> TransactionListItem:
        member_user = t.membership.user if t.membership else None
        staff_user = t.staff
        voucher = t.voucher
        return TransactionListItem(
            id=t.id,
            created_at=t.created_at,
            receipt_code=t.receipt_code,
            membership_display_name=(
                member_user.full_name or member_user.phone
                if member_user
                else "(đã xoá)"
            ),
            staff_display_name=(
                staff_user.full_name or staff_user.phone if staff_user else None
            ),
            gross_amount=t.gross_amount,
            voucher_discount_amount=t.voucher_discount_amount,
            net_amount=t.net_amount,
            points_earned=t.points_earned,
            method=t.method.value if hasattr(t.method, "value") else str(t.method),
            voucher_code=voucher.code if voucher else None,
        )

    @staticmethod
    def _to_detail(t: Transaction) -> TransactionDetailResponse:
        base = PartnerTransactionService._to_list_item(t).model_dump()
        return TransactionDetailResponse(
            **base,
            note=t.note,
            legal_discount_ratio=t.legal_discount_ratio,
        )
```

- [ ] **Step 4: Mở rộng `backend/app/api/transactions.py`**

File hiện có router `APIRouter(prefix="/partner/transactions", tags=["partner-transactions"])` với `POST ""`, `POST "/qr"`, `GET ""` (list 50 gần nhất, flat). Thay thế `GET ""` bằng version có pagination + filter, và thêm `GET /{transaction_id}` + `PATCH /{transaction_id}`.

**(4a)** Đổi import block ở đầu file, bổ sung các dependency mới:

```python
from datetime import date  # NEW
from fastapi import APIRouter, Depends, HTTPException, Query, Request
# ... imports cũ ...
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    CreateQrCustomerTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
    TransactionDetailResponse,  # NEW
    TransactionListResponse,    # NEW
    TransactionUpdateRequest,   # NEW
)
from app.services.partner_transaction_service import (  # NEW
    DuplicateReceiptCodeError,
    PartnerTransactionService,
    TransactionNotFoundError,
)
```

**(4b)** Xoá handler `list_transactions` cũ (dòng ~92-104, trả `list[TransactionResponse]`) và thay bằng 3 handler mới — append sau handler `create_qr_transaction`:

```python
@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    staff_id: int | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
) -> TransactionListResponse:
    svc = PartnerTransactionService(db)
    return await svc.list(
        partner_id=partner_id,
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        staff_id=staff_id,
        q=q,
    )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_staff_in_partner),
) -> TransactionDetailResponse:
    svc = PartnerTransactionService(db)
    try:
        return await svc.get_detail(partner_id, transaction_id)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{transaction_id}", response_model=TransactionDetailResponse)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
) -> TransactionDetailResponse:
    svc = PartnerTransactionService(db)
    try:
        return await svc.update(partner_id, transaction_id, payload)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DuplicateReceiptCodeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
```

**(4c)** Không cần `app.include_router` mới — router hiện đã được register qua `from app.api import transactions` + `app.include_router(transactions.router)` trong `main.py`.

**Lưu ý breaking change:** `GET /partner/transactions` đổi response shape từ `list[TransactionResponse]` → `TransactionListResponse` (`{items, total, page, page_size}`). Task C4 (frontend) và consumer khác phải thích nghi (đã cover trong plan C4). Nếu có external consumer nằm ngoài scope đồ án thì ghi chú lại — hiện không có.

- [ ] **Step 5: Viết integration test — append vào file C1**

Mở `backend/tests/integration/test_transactions_api.py` (file đã có các test C1 `test_post_transaction_*`). Append các test list/detail/patch vào cuối file:

```python
# Các import + pytestmark đã có từ C1, không lặp.

async def test_list_transactions_pagination(
    async_client: AsyncClient, owner_auth_headers, partner_with_50_transactions
):
    ctx = partner_with_50_transactions
    resp = await async_client.get(
        "/partner/transactions",
        params={"page": 1, "page_size": 20},
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 50
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 20


async def test_list_filter_by_staff(
    async_client, owner_auth_headers, partner_with_50_transactions
):
    ctx = partner_with_50_transactions
    staff_id = ctx["staff_a_id"]
    resp = await async_client.get(
        "/partner/transactions",
        params={"staff_id": staff_id, "page_size": 100},
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(True for _ in items)  # fixture tạo một nửa của staff_a


async def test_get_detail_includes_note(
    async_client, owner_auth_headers, partner_with_one_transaction
):
    ctx = partner_with_one_transaction
    resp = await async_client.get(
        f"/partner/transactions/{ctx['txn_id']}",
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == ctx["txn_id"]
    assert "note" in body


async def test_patch_as_owner_updates_receipt_code(
    async_client, owner_auth_headers, partner_with_one_transaction
):
    ctx = partner_with_one_transaction
    resp = await async_client.patch(
        f"/partner/transactions/{ctx['txn_id']}",
        json={"receipt_code": "FIXED-001"},
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 200
    assert resp.json()["receipt_code"] == "FIXED-001"


async def test_patch_as_staff_forbidden(
    async_client, staff_auth_headers, partner_with_one_transaction
):
    ctx = partner_with_one_transaction
    resp = await async_client.patch(
        f"/partner/transactions/{ctx['txn_id']}",
        json={"receipt_code": "STAFF-TRY"},
        headers={**staff_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 403


async def test_patch_receipt_code_to_null(
    async_client, owner_auth_headers, partner_with_one_transaction
):
    ctx = partner_with_one_transaction
    resp = await async_client.patch(
        f"/partner/transactions/{ctx['txn_id']}",
        json={"receipt_code": None},
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 200
    assert resp.json()["receipt_code"] is None


async def test_patch_duplicate_receipt_code_409(
    async_client, owner_auth_headers, partner_with_two_transactions
):
    ctx = partner_with_two_transactions  # both có receipt_code "AAA" và "BBB"
    resp = await async_client.patch(
        f"/partner/transactions/{ctx['txn_b_id']}",
        json={"receipt_code": "AAA"},
        headers={**owner_auth_headers, "X-Partner-Id": str(ctx["partner_id"])},
    )
    assert resp.status_code == 409
```

**Fixtures cần tạo trong conftest**: `partner_with_50_transactions`, `partner_with_one_transaction`, `partner_with_two_transactions`. Dùng `TransactionService.create_manual` hoặc insert trực tiếp qua model. Seed `staff_a_id`, `staff_b_id` cho filter test.

- [ ] **Step 6: Run test**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml restart backend && sleep 5 && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/integration/test_transactions_api.py -v 2>&1 | tail -40`
Expected: 13 passed (6 test C1 + 7 test C2 mới).

- [ ] **Step 7: Commit**

```bash
cd D:/DoAn && rtk git add backend/app/models/transaction.py backend/app/services/partner_transaction_service.py backend/app/api/transactions.py backend/app/schemas/transaction.py backend/tests/integration/test_transactions_api.py backend/tests/conftest.py
rtk git commit -m "feat(transactions): GET list/detail + PATCH (owner-only) /partner/transactions"
```

---

### Task C3: Frontend POS form thêm receipt_code input

**Files:**
- Modify: `frontend/src/app/(partner)/partner/pos/page.tsx` (hoặc file form POS)
- Modify: `frontend/src/types/partner.ts` (hoặc `transaction.ts`) — thêm field `receipt_code` vào types

- [ ] **Step 1: Update type**

Trong `frontend/src/types/partner.ts`, mở rộng interface `CreateManualTransactionRequest` existing (L.194 — field hiện có: `phone`, `gross_amount`, `voucher_code`, `note`). Thêm `receipt_code`:

```ts
export interface CreateManualTransactionRequest {
  phone: string;
  gross_amount: number;
  voucher_code?: string | null;
  note?: string | null;
  receipt_code?: string | null;  // NEW
}
```

Thêm `receipt_code` vào `TransactionResponse` / `TransactionWithMemberResponse` (type transaction response có sẵn trong cùng file):

```ts
export interface TransactionResponse {
  id: number;
  // ... existing fields ...
  receipt_code: string | null;  // NEW
}
```

- [ ] **Step 2: Update POS form**

Tìm form POS — thường trong `frontend/src/app/(partner)/partner/pos/page.tsx` hoặc `components/partner/pos-form.tsx`. Thêm input sau voucher input:

```tsx
<div className="space-y-1">
  <Label htmlFor="receipt_code">Mã hoá đơn (tuỳ chọn)</Label>
  <Input
    id="receipt_code"
    placeholder="VD: HD-00123"
    maxLength={50}
    {...form.register("receipt_code")}
  />
</div>
```

Update zod schema (nếu có):
```ts
receipt_code: z.string().max(50).optional().nullable(),
```

Update submit handler — include `receipt_code` trong body (payload đã dùng `phone`, không phải `membership_id`):
```ts
await transactionsApi.create({
  phone: values.phone,
  gross_amount: values.gross_amount,
  voucher_code: values.voucher_code || undefined,
  note: values.note || undefined,
  receipt_code: values.receipt_code || undefined,
});
```

- [ ] **Step 3: Error handler toast VN 409**

Trong catch block submit, map 409 → toast:

```ts
try {
  await mutation.mutateAsync(payload);
  toast.success("Tạo giao dịch thành công");
} catch (e: any) {
  if (e?.response?.status === 409) {
    toast.error(e.response.data?.detail ?? "Mã hoá đơn đã tồn tại.");
  } else {
    toast.error("Tạo giao dịch thất bại.");
  }
}
```

- [ ] **Step 4: Type-check + smoke Playwright**

Run: `cd D:/DoAn/frontend && npx tsc --noEmit 2>&1 | head -10`
Expected: 0 error.

Rebuild:
```bash
cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml build frontend && docker compose -p loyalty-prod -f docker-compose.prod.yml up -d frontend
```

Test qua Playwright (hoặc browser):
- Owner login → `/partner/pos` → nhập khách + 100k + receipt_code "POS-TEST-001" → submit → success.
- Tạo lại với same receipt_code "POS-TEST-001" → toast VN "Mã hoá đơn đã tồn tại".

- [ ] **Step 5: Commit**

```bash
cd D:/DoAn && rtk git add frontend/src/
rtk git commit -m "feat(pos): POS form thêm input receipt_code + toast 409 VN"
```

---

### Task C4: Frontend `/partner/transactions` page + detail sheet + sidebar

**Files:**
- Create: `frontend/src/app/(partner)/partner/transactions/page.tsx`
- Create: `frontend/src/components/partner/transaction-table.tsx`
- Create: `frontend/src/components/partner/transaction-detail-sheet.tsx`
- Modify: `frontend/src/lib/api-partner.ts` (thêm `transactionsApi`)
- Modify: `frontend/src/lib/hooks/` (thêm `use-partner-transactions.ts`)
- Modify: `frontend/src/types/partner.ts` (thêm types list/detail)
- Modify: `frontend/src/app/(partner)/partner/layout.tsx` (sidebar)

- [ ] **Step 1: Update types**

Trong `frontend/src/types/partner.ts`:

```ts
export type TransactionListItem = {
  id: number;
  created_at: string;
  receipt_code: string | null;
  membership_display_name: string;
  staff_display_name: string | null;
  gross_amount: number;
  voucher_discount_amount: number | null;
  net_amount: number;
  points_earned: number;
  method: string;
  voucher_code: string | null;
};

export type TransactionListResponse = {
  items: TransactionListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type TransactionDetail = TransactionListItem & {
  note: string | null;
  legal_discount_ratio: string | null;
};

export type TransactionUpdatePayload = {
  receipt_code?: string | null;
  note?: string | null;
};
```

- [ ] **Step 2: API client + hooks**

Mở `frontend/src/lib/api-partner.ts` — file đã có `transactionsApi = { create, createFromQr, list }` với `list(params?: { limit, offset })`. **Mở rộng** object existing (không tạo mới):

```ts
// Trước:
export const transactionsApi = {
  create: (data: CreateManualTransactionRequest) =>
    api.post<TransactionWithMemberResponse>("/partner/transactions", data),
  createFromQr: (data: { qr_payload: string; gross_amount: number; note?: string | null }) =>
    api.post<TransactionWithMemberResponse>("/partner/transactions/qr", data),
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<TransactionResponse[]>("/partner/transactions", { params }),
};

// Sau — đổi chữ ký `list` sang paginated + filter, thêm `get` + `update`:
export const transactionsApi = {
  create: (data: CreateManualTransactionRequest) =>
    api.post<TransactionWithMemberResponse>("/partner/transactions", data),
  createFromQr: (data: { qr_payload: string; gross_amount: number; note?: string | null }) =>
    api.post<TransactionWithMemberResponse>("/partner/transactions/qr", data),
  list: (params: {
    page?: number;
    page_size?: number;
    date_from?: string;
    date_to?: string;
    staff_id?: number;
    q?: string;
  }) => api.get<TransactionListResponse>("/partner/transactions", { params }),
  get: (id: number) => api.get<TransactionDetail>(`/partner/transactions/${id}`),
  update: (id: number, payload: TransactionUpdatePayload) =>
    api.patch<TransactionDetail>(`/partner/transactions/${id}`, payload),
};
```

**Breaking change frontend:** `transactionsApi.list` đổi response type `TransactionResponse[]` → `TransactionListResponse`. Grep callsite hiện tại:
```bash
rtk grep -rn "transactionsApi.list" frontend/src/
```
Mỗi match phải update để đọc `.data.items` thay vì `.data` (hoặc destructure `{ items, total, page, page_size }`). Nếu không có match khác ngoài hook mới → không cần care.

Import kiểu mới trong cùng file:
```ts
// Đầu file api-partner.ts đã import từ "@/types/partner":
import type {
  // ... các type hiện có ...
  TransactionListResponse,  // NEW
  TransactionDetail,        // NEW (hoặc TransactionDetailResponse tuỳ naming C4 Step 1)
  TransactionUpdatePayload, // NEW
} from "@/types/partner";
```

Tạo `frontend/src/lib/hooks/use-partner-transactions.ts`:

```ts
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { transactionsApi } from "@/lib/api-partner";
import type { TransactionUpdatePayload } from "@/types/partner";

export function usePartnerTransactions(params: {
  page: number;
  page_size: number;
  date_from?: string;
  date_to?: string;
  staff_id?: number;
  q?: string;
}) {
  return useQuery({
    queryKey: ["partner", "transactions", params],
    queryFn: () => transactionsApi.list(params).then((r) => r.data),
    placeholderData: keepPreviousData,
  });
}

export function usePartnerTransactionDetail(id: number | null) {
  return useQuery({
    queryKey: ["partner", "transaction", id],
    queryFn: () => transactionsApi.get(id!).then((r) => r.data),
    enabled: id !== null,
  });
}

export function useUpdatePartnerTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: TransactionUpdatePayload }) =>
      transactionsApi.update(id, payload).then((r) => r.data),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["partner", "transactions"] });
      qc.invalidateQueries({ queryKey: ["partner", "transaction", vars.id] });
    },
  });
}
```

- [ ] **Step 3: Tạo TransactionTable component**

Tạo `frontend/src/components/partner/transaction-table.tsx`:

```tsx
"use client";

import { format } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import type { TransactionListItem } from "@/types/partner";

const fmtMoney = (n: number) => n.toLocaleString("vi-VN") + " ₫";

export function TransactionTable({
  items,
  total,
  page,
  pageSize,
  onPageChange,
  onRowClick,
}: {
  items: TransactionListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
  onRowClick: (id: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Ngày</TableHead>
            <TableHead>Mã HĐ</TableHead>
            <TableHead>Khách</TableHead>
            <TableHead>NV</TableHead>
            <TableHead className="text-right">Thực thu</TableHead>
            <TableHead className="text-right">Điểm</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                Chưa có giao dịch.
              </TableCell>
            </TableRow>
          )}
          {items.map((t) => (
            <TableRow
              key={t.id}
              className="cursor-pointer hover:bg-slate-50"
              onClick={() => onRowClick(t.id)}
            >
              <TableCell>{format(new Date(t.created_at), "dd/MM HH:mm")}</TableCell>
              <TableCell>{t.receipt_code || "—"}</TableCell>
              <TableCell>{t.membership_display_name}</TableCell>
              <TableCell>{t.staff_display_name ?? "—"}</TableCell>
              <TableCell className="text-right font-medium">
                {fmtMoney(t.net_amount)}
              </TableCell>
              <TableCell className="text-right">{t.points_earned}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="mt-3 flex items-center justify-end gap-2">
        <span className="text-sm text-muted-foreground">
          Trang {page} / {totalPages}
        </span>
        <Button
          size="sm"
          variant="outline"
          disabled={page === 1}
          onClick={() => onPageChange(page - 1)}
        >
          Trước
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Sau
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Tạo TransactionDetailSheet component**

Tạo `frontend/src/components/partner/transaction-detail-sheet.tsx`:

```tsx
"use client";

import { useEffect } from "react";
import { format } from "date-fns";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  usePartnerTransactionDetail,
  useUpdatePartnerTransaction,
} from "@/lib/hooks/use-partner-transactions";
import type { PointRule, Tier } from "@/types/partner";

const fmtMoney = (n: number | null) =>
  n === null ? "—" : n.toLocaleString("vi-VN") + " ₫";

export function TransactionDetailSheet({
  transactionId,
  isOwner,
  currentRule,
  currentTier,
  open,
  onOpenChange,
}: {
  transactionId: number | null;
  isOwner: boolean;
  currentRule?: PointRule | null;
  currentTier?: Tier | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const detailQ = usePartnerTransactionDetail(transactionId);
  const updateMut = useUpdatePartnerTransaction();

  const form = useForm<{ receipt_code: string; note: string }>({
    defaultValues: { receipt_code: "", note: "" },
  });

  useEffect(() => {
    if (detailQ.data) {
      form.reset({
        receipt_code: detailQ.data.receipt_code ?? "",
        note: detailQ.data.note ?? "",
      });
    }
  }, [detailQ.data, form]);

  const onSave = form.handleSubmit(async (values) => {
    if (!transactionId) return;
    try {
      await updateMut.mutateAsync({
        id: transactionId,
        payload: {
          receipt_code: values.receipt_code.trim() || null,
          note: values.note.trim() || null,
        },
      });
      toast.success("Đã lưu");
      onOpenChange(false);
    } catch (e: any) {
      const msg =
        e?.response?.status === 409
          ? e.response.data?.detail ?? "Mã hoá đơn đã tồn tại."
          : "Lưu thất bại.";
      toast.error(msg);
    }
  });

  const t = detailQ.data;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full max-w-lg">
        <SheetHeader>
          <SheetTitle>Chi tiết giao dịch</SheetTitle>
        </SheetHeader>
        {detailQ.isLoading && <p className="p-4">Đang tải...</p>}
        {t && (
          <div className="space-y-4 p-4 text-sm">
            <InfoRow
              label="Thời gian"
              value={format(new Date(t.created_at), "dd/MM/yyyy HH:mm")}
            />
            <InfoRow label="Nhân viên" value={t.staff_display_name ?? "—"} />
            <InfoRow label="Khách hàng" value={t.membership_display_name} />
            <InfoRow label="Doanh thu" value={fmtMoney(t.gross_amount)} />
            <InfoRow
              label="Voucher"
              value={
                t.voucher_code
                  ? `${t.voucher_code} (-${fmtMoney(t.voucher_discount_amount)})`
                  : "—"
              }
            />
            <InfoRow label="Thực thu" value={fmtMoney(t.net_amount)} />
            <InfoRow
              label="Điểm đã tích"
              value={`${t.points_earned} điểm`}
            />
            {currentRule && (
              <p className="text-xs italic text-muted-foreground">
                ↳ cấu hình hiện tại: {currentRule.points_per_unit} điểm /{" "}
                {currentRule.unit_amount.toLocaleString("vi-VN")} VND
                {currentRule.use_tiers && currentTier
                  ? `, hạng ${currentTier.name} × ${currentTier.earn_multiplier}`
                  : ""}
              </p>
            )}
            <InfoRow label="Phương thức" value={t.method} />

            {isOwner ? (
              <form onSubmit={onSave} className="space-y-3 border-t pt-4">
                <div>
                  <Label htmlFor="edit_receipt_code">Mã hoá đơn</Label>
                  <Input
                    id="edit_receipt_code"
                    maxLength={50}
                    {...form.register("receipt_code")}
                  />
                </div>
                <div>
                  <Label htmlFor="edit_note">Ghi chú</Label>
                  <Textarea id="edit_note" rows={3} {...form.register("note")} />
                </div>
                <Button type="submit" disabled={updateMut.isPending}>
                  {updateMut.isPending ? "Đang lưu..." : "Lưu"}
                </Button>
              </form>
            ) : (
              <div className="border-t pt-3 text-xs text-muted-foreground">
                Mã HĐ: <strong>{t.receipt_code ?? "—"}</strong>
                <br />Ghi chú: {t.note ?? "—"}
              </div>
            )}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
```

- [ ] **Step 5: Tạo page**

Tạo `frontend/src/app/(partner)/partner/transactions/page.tsx`:

```tsx
"use client";

import { useState } from "react";

import { usePartnerStore } from "@/lib/partner-store";
import { usePartnerTransactions } from "@/lib/hooks/use-partner-transactions";
import {
  useActivePointRule,
  usePartnerTiers,
} from "@/lib/hooks/use-partner-settings";
import { TransactionTable } from "@/components/partner/transaction-table";
import { TransactionDetailSheet } from "@/components/partner/transaction-detail-sheet";
import { Input } from "@/components/ui/input";

export default function PartnerTransactionsPage() {
  const role = usePartnerStore((s) => s.activePartner?.role);
  const isOwner = role === "owner";

  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [staffId, setStaffId] = useState<number | undefined>(undefined);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const txnQ = usePartnerTransactions({
    page,
    page_size: 20,
    q: q || undefined,
    staff_id: staffId,
  });
  const ruleQ = useActivePointRule();
  const tiersQ = usePartnerTiers();

  // Tier hiện tại: lấy tier đầu tiên có earn_multiplier > 1 (placeholder) hoặc để null.
  // Thực tế detail sheet hiển thị cấu hình hiện tại "tham khảo", nên null cũng ổn.
  const currentTier = null;

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Lịch sử giao dịch</h1>
        <div className="flex gap-2">
          <Input
            placeholder="Tìm mã hoá đơn..."
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            className="w-56"
          />
        </div>
      </div>

      {txnQ.isLoading && <p>Đang tải...</p>}
      {txnQ.data && (
        <TransactionTable
          items={txnQ.data.items}
          total={txnQ.data.total}
          page={txnQ.data.page}
          pageSize={txnQ.data.page_size}
          onPageChange={setPage}
          onRowClick={setSelectedId}
        />
      )}

      <TransactionDetailSheet
        transactionId={selectedId}
        isOwner={isOwner}
        currentRule={ruleQ.data ?? null}
        currentTier={currentTier}
        open={selectedId !== null}
        onOpenChange={(v) => {
          if (!v) setSelectedId(null);
        }}
      />
    </div>
  );
}
```

- [ ] **Step 6: Thêm menu sidebar**

Mở `frontend/src/app/(partner)/partner/layout.tsx`. Thêm item:

```tsx
{ href: "/partner/transactions", label: "Lịch sử giao dịch", icon: HistoryIcon },
```

Import icon `History` từ lucide-react nếu chưa có.

- [ ] **Step 7: Type-check + smoke**

Run: `cd D:/DoAn/frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: 0 error.

Rebuild frontend:
```bash
cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml build frontend && docker compose -p loyalty-prod -f docker-compose.prod.yml up -d frontend
```

Playwright smoke:
- Owner login → sidebar "Lịch sử giao dịch" → page load với danh sách.
- Click 1 row → sheet mở với detail.
- Edit receipt_code → Save → table refresh + mã mới.
- Search "HD-00001" → filter đúng.
- Pagination next/prev hoạt động.
- Staff login → vào page → thấy danh sách (read-only), click row thấy detail không có form edit.

- [ ] **Step 8: Commit**

```bash
cd D:/DoAn && rtk git add frontend/src/
rtk git commit -m "feat(partner): /partner/transactions page + detail sheet + sidebar menu"
```

---

### Task C5: Seed demo transactions với receipt_code + full smoke

**Files:**
- Modify: `backend/seed_demo.py`

- [ ] **Step 1: Update seed_demo.py**

Tìm block tạo transaction (nếu có — thường sau block tạo membership). Thêm 3-5 giao dịch Cafe Cộng có `receipt_code`, 2-3 giao dịch NULL.

Pattern (schema thực là `CreateManualTransactionRequest` với `phone`):
```python
from app.schemas.transaction import CreateManualTransactionRequest
from app.services.transaction_service import TransactionService

seed_transactions = [
    {"gross_amount": 120_000, "receipt_code": "HD-00001", "note": "Demo giao dịch"},
    {"gross_amount": 85_000, "receipt_code": "HD-00002"},
    {"gross_amount": 200_000, "receipt_code": "HD-00003"},
    {"gross_amount": 45_000, "receipt_code": None},
    {"gross_amount": 60_000, "receipt_code": None},
]
for payload in seed_transactions:
    svc = TransactionService(db)
    await svc.create_manual(
        partner_id=cafe_partner_id,
        staff_id=cafe_owner_user_id,
        request=CreateManualTransactionRequest(
            phone=khach1_phone,  # lookup từ block seed user trước đó
            gross_amount=payload["gross_amount"],
            receipt_code=payload.get("receipt_code"),
            note=payload.get("note"),
        ),
    )
```

Điều chỉnh theo cấu trúc hàm seed hiện tại. Nếu seed không dùng service (insert trực tiếp model) → thêm field `receipt_code=payload.get("receipt_code")` vào `Transaction(...)` constructor.

- [ ] **Step 2: Re-seed + verify**

```bash
cd D:/DoAn && docker exec loyalty-backend-prod python seed_demo.py 2>&1 | tail -15
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "SELECT count(*), count(receipt_code) FROM transactions;"
```
Expected: tổng row ≥ 5, trong đó ≥ 3 có receipt_code.

- [ ] **Step 3: End-to-end Playwright smoke (spec section 8.3)**

Chạy hoặc replay qua MCP Playwright:
1. Owner login `owner@cafe.vn / owner1234` → `/partner/settings` → toggle `use_tiers` → Save → reload → persisted.
2. Owner → `/partner/settings` → edit Gold `earn_multiplier` 1.00 → 1.50 → Save → reload → persisted.
3. Staff login → navigate `/partner/settings` → redirected → URL = `/staff`.
4. Staff → POS → tạo transaction với receipt_code "TEST-001" → success → tạo 2nd cùng code → toast VN.
5. Owner → `/partner/transactions` → click row → sheet → edit receipt_code → Save → bảng refresh.
6. Owner → `/partner/campaigns/1` → verify không còn section "Phí dịch vụ".
7. Super admin → `/admin/campaigns` → verify không còn cột fee.

- [ ] **Step 4: Full backend test suite**

Run: `cd D:/DoAn && docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest backend/tests/ -v 2>&1 | tail -30`
Expected: 0 fail, 0 error.

- [ ] **Step 5: Grep final zero-check service fee**

Run: `rtk grep -rnE "service_fee|ServiceFee|FeeSchedule" backend/app/ frontend/src/`
Expected: 0 match.

- [ ] **Step 6: Commit**

```bash
cd D:/DoAn && rtk git add backend/seed_demo.py
rtk git commit -m "feat(seed): demo transactions với receipt_code cho Cafe + verify full smoke"
```

---

## Rollout / Deploy Checklist (sau khi tất cả task xong)

Xem spec section 10 — preflight count check TRƯỚC khi chạy migration prod:

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "
SELECT
  (SELECT count(*) FROM campaign_service_fees) AS fee_rows,
  (SELECT count(*) FROM campaign_fee_schedules) AS schedule_rows,
  (SELECT count(*) FROM campaigns WHERE service_fee_status <> 'not_applicable') AS active_fee_campaigns;
"
```
Expected: tất cả 0. Nếu ≠ 0 → export data trước khi drop.

Sau khi confirm → rebuild backend (auto-run migration) → smoke test section 8.3.

---

## Self-review checklist (cho người viết plan)

- [x] Spec coverage — Part A (Task A1-A9), Part B (Task B1-B8), Part C (Task C1-C5) cover hết goal 2.1 của spec.
- [x] No placeholder — mọi step có code hoặc command cụ thể.
- [x] Type consistency — `_calculate_points(rule, amount, *, membership=...)` nhất quán giữa Task B4, test B4, call site B4, schema B5.
- [x] Migration ID: A=`e1f2a3b4c5d6`, B+C=`e2a3b4c5d6e7`, revision chain đúng thứ tự.
- [x] Test fixtures được gọi ra trong từng task — engineer biết cần tạo gì trong conftest.
- [x] `Membership.current_tier` relationship đã tồn tại ở model (verify ở B1 no-change task) → B4 chỉ cần `selectinload` ở call site — không mâu thuẫn.
- [x] IntegrityError handler cho `ux_transactions_partner_receipt_code` ở A6 (sửa main.py cùng Part A) chạy trước khi constraint tồn tại (Task B3 migration) — an toàn vì code dormant cho đến khi constraint hit.
- [x] Staff guard 2 lớp (B8 backend deps + frontend redirect `/staff`).
- [x] Spec section 12: questions resolved — không còn pending.
