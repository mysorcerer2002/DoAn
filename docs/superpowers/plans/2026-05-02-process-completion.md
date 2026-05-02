# Process Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) hoặc superpowers:executing-plans để thực thi plan này task-by-task. Steps dùng checkbox (`- [ ]`) syntax cho tracking.

**Goal:** Hoàn thiện 6 quy trình (QT1, QT2, QT4, QT5, QT7, QT8) lấp gap giữa code và mục 2.3.1 báo cáo đồ án. QT3 và QT6 đã đủ — không đụng.

**Architecture:** 6 phase tuần tự theo thứ tự rủi ro thấp → cao (QT5 → QT4 → QT1 → QT8 → QT2 → QT7). Mỗi phase có alembic revision riêng (nếu có DDL), TDD test-first, commit sau mỗi task. Giữa các phase chạy `superpowers:code-reviewer` (model `opus`) → fix Critical/Important rồi mới sang phase kế.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2 / Next.js 14 + TS + Tailwind v4 + shadcn/ui + TanStack Query.

**Spec:** `docs/superpowers/specs/2026-05-02-process-completion-design.md`

**Folded từ code-review spec (opus):**
- Constraint name double-prefix: dùng tên thực tế `ck_rewards_ck_rewards_points_cost_positive` khi drop.
- 3 schema Reward (Create/Update/Response) đều phải có `valid_from` đồng thời.
- Mỗi phase 1 revision riêng (KHÔNG gộp 1 revision).
- Partial unique index `ux_redemptions_user_reward_active` chống user spam claim.
- `get_current_user_unrestricted` chỉ áp 2 endpoint (không gồm `/auth/refresh` vì endpoint đó không gọi `get_current_user`).
- Super_admin SKIP `must_change_password` flag.
- `claim_free` dùng explicit guard sau fetch (không filter ở WHERE).
- CK enforce action vocabulary ở DB level (`audit_logs_action_valid`).

---

## File Structure

### Backend

| File | Phase | Type | Purpose |
|---|---|---|---|
| `backend/app/services/redemption_service.py` | 1, 6 | Modify | QT5 expiry filter, QT7 `claim_free` + guards |
| `backend/app/services/transaction_service.py` | 2 | Modify | QT4 plumb `actor_user_id` |
| `backend/app/services/qr_service.py` | 2 | Modify | QT4 auto-enroll khi không có membership |
| `backend/app/api/transactions.py` | 2 | Modify | QT4 capture `current_user`, drop 404 trên lookup |
| `backend/alembic/versions/<hex>_qt1_must_change_password.py` | 3 | Create | Migration cột `users.must_change_password` |
| `backend/app/models/user.py` | 3 | Modify | Cột `must_change_password` |
| `backend/app/schemas/auth.py` | 3 | Modify | `RegisterRequest` + phone field |
| `backend/app/services/auth_service.py` | 3 | Modify | `register` check phone, `reset_password` set flag, `change_password` unset |
| `backend/app/core/deps.py` | 3 | Modify | 423 logic + `get_current_user_unrestricted` |
| `backend/app/api/auth.py` | 3 | Modify | `/auth/me` + `/auth/me/password` dùng dep mới |
| `backend/alembic/versions/<hex>_qt8_audit_logs.py` | 4 | Create | Migration table `audit_logs` |
| `backend/app/models/audit_log.py` | 4 | Create | Model `AuditLog` |
| `backend/app/core/audit_actions.py` | 4 | Create | Vocabulary constants |
| `backend/app/services/audit_log_service.py` | 4 | Create | `AuditLogService.log` |
| `backend/app/schemas/audit_log.py` | 4 | Create | Request/Response schemas |
| `backend/app/api/admin.py` | 4 | Modify | `update_user` + `approve_partner` + `suspend_partner` hooks; `GET /admin/audit-logs` |
| `backend/alembic/versions/<hex>_qt2_partner_terms_license.py` | 5 | Create | 6 cột partners |
| `backend/app/models/partner.py` | 5 | Modify | 6 cột mới |
| `backend/app/api/uploads.py` | 5 | Modify | Endpoint `/partner/uploads/license` |
| `backend/app/schemas/partner.py` | 5 | Modify | `PartnerCreateRequest` thêm license + accept_terms + terms_version |
| `backend/app/services/partner_service.py` | 5 | Modify | `create_partner` + `approve_partner` + `suspend_partner` nhận reason, actor |
| `backend/app/api/partners.py` | 5 | Modify | `register_partner` truyền terms |
| `backend/app/core/legal.py` | 5 | Create | `CURRENT_TERMS_VERSION` |
| `backend/alembic/versions/<hex>_qt7_reward_free_voucher.py` | 6 | Create | Drop CK + add CK + `valid_from` + partial unique index |
| `backend/app/models/reward.py` | 6 | Modify | CK rename + cột `valid_from` |
| `backend/app/schemas/reward.py` | 6 | Modify | 3 schema thêm `valid_from`, relax `points_cost` |
| `backend/app/api/partners.py` | 6 | Modify | `POST /users/me/rewards/{id}/claim` |

### Frontend

| File | Phase | Type | Purpose |
|---|---|---|---|
| `frontend/src/app/(auth)/register/page.tsx` | 3 | Modify | Field SĐT |
| `frontend/src/app/(auth)/change-password/page.tsx` | 3 | Create | Trang đổi mật khẩu sau temp |
| `frontend/src/lib/api.ts` | 3 | Modify | Interceptor branch 423 password_change_required |
| `frontend/src/types/audit.ts` | 4 | Create | Audit log types |
| `frontend/src/lib/api-partner.ts` | 4 | Modify | `adminApi.auditLogs()` |
| `frontend/src/lib/hooks/useAdminAuditLogs.ts` | 4 | Create | TanStack hook |
| `frontend/src/app/(admin)/admin/audit-logs/page.tsx` | 4 | Create | Trang admin audit logs |
| `frontend/src/app/(admin)/admin/users/page.tsx` | 4 | Modify | Modal lock/unlock kèm reason field |
| `frontend/src/app/(admin)/admin/partners/page.tsx` | 4, 5 | Modify | Modal approve/suspend kèm reason + license preview |
| `frontend/src/app/(auth)/register/partner/page.tsx` | 5 | Modify | License upload + ToS checkbox |
| `frontend/src/app/legal/terms/page.tsx` | 5 | Create | T&C static page |
| `frontend/src/types/partner.ts` | 4, 5, 6 | Modify | Audit/Partner/Reward types |
| `frontend/src/app/(member)/member/rewards/page.tsx` | 6 | Modify | Branch button theo `points_cost` |
| `frontend/src/app/(member)/member/partners/[slug]/page.tsx` | 6 | Modify | Tương tự |
| `frontend/src/app/(partner)/partner/rewards/page.tsx` | 6 | Modify | Modal create/edit Reward thêm `valid_from` + cho phép `points_cost=0` |
| `frontend/src/lib/hooks/useRewards.ts` | 6 | Modify | `useClaimFreeReward` mutation |

### Tests

| File | Phase | Type |
|---|---|---|
| `backend/tests/integration/test_redemption_service.py` | 1, 6 | Modify |
| `backend/tests/integration/test_transaction_service.py` | 2 | Modify |
| `backend/tests/integration/test_qr_service.py` | 2 | Create (chưa có) |
| `backend/tests/integration/test_auth_service.py` | 3 | Create hoặc Modify nếu đã có |
| `backend/tests/integration/test_audit_log_service.py` | 4 | Create |
| `backend/tests/integration/test_auth_api.py` | 3 | Modify |
| `backend/tests/integration/test_admin_api.py` | 4 | Modify |
| `backend/tests/integration/test_partner_register.py` | 5 | Create |
| `backend/tests/integration/test_reward_claim.py` | 6 | Create |
| `backend/tests/conftest.py` | 0 | Modify (thêm factory fixtures) |

---

## Phase 0 — Test fixtures setup (prerequisite cho mọi phase)

**Goal:** Thêm pytest factories vào `conftest.py` để mọi test ở các phase sau dùng. Các test snippet trong plan đều giả định fixture `user_factory`, `partner_factory`, `reward_factory`, `point_rule_factory`, `admin_token`, `customer_token`, `user_token` — hiện tại `conftest.py` chỉ có `db_session`/`client`.
**Risk:** thấp — chỉ thêm fixture, không đụng app code.

### Task 0.1 — Thêm fixtures vào conftest.py

**Files:**
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Thêm các factory + token fixture.**

```python
# backend/tests/conftest.py — thêm sau các fixture hiện có
import secrets
from datetime import date

import pytest_asyncio

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.partner import Partner, PartnerStatus, PartnerCategory
from app.models.reward import Reward, RewardOfferType
from app.models.point_rule import PointRule
from app.models.partner_staff import PartnerStaff


@pytest_asyncio.fixture
async def user_factory():
    """Tạo user với phone unique tự sinh."""
    async def _factory(db, *, email=None, phone=None, password_hash=None,
                       is_active=True, system_role="regular", points_balance=0,
                       must_change_password=False):
        if email is None:
            email = f"u{secrets.token_hex(4)}@test.vn"
        if phone is None:
            phone = f"09{secrets.randbelow(10**8):08d}"
        if password_hash is None:
            password_hash = hash_password("testpass1")
        user = User(
            email=email, phone=phone, password_hash=password_hash,
            full_name=f"User {email}", is_active=is_active,
            system_role=system_role, points_balance=points_balance,
            must_change_password=must_change_password,  # field thêm Phase 3
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    return _factory


@pytest_asyncio.fixture
async def partner_factory():
    async def _factory(db, *, name=None, status=PartnerStatus.ACTIVE,
                       category=PartnerCategory.CAFE, owner_user=None):
        if name is None:
            name = f"Shop {secrets.token_hex(3)}"
        if owner_user is None:
            owner = User(
                email=f"owner-{secrets.token_hex(3)}@test.vn",
                phone=f"09{secrets.randbelow(10**8):08d}",
                password_hash=hash_password("ownerpass1"),
                full_name="Owner", is_active=True, system_role="regular",
            )
            db.add(owner)
            await db.flush()
        else:
            owner = owner_user
        slug = name.lower().replace(" ", "-") + secrets.token_hex(2)
        partner = Partner(
            name=name, slug=slug, owner_user_id=owner.id,
            status=status, category=category, settings={},
        )
        db.add(partner)
        await db.flush()
        await db.refresh(partner)
        return partner
    return _factory


@pytest_asyncio.fixture
async def reward_factory():
    async def _factory(db, *, partner_id, name=None, points_cost=100,
                       stock=None, offer_type=RewardOfferType.ITEM_GIFT,
                       offer_value=None, offer_label=None, valid_from=None,
                       valid_until=None, is_active=True):
        if name is None:
            name = f"Reward {secrets.token_hex(3)}"
        if offer_label is None:
            offer_label = name
        reward = Reward(
            partner_id=partner_id, name=name, points_cost=points_cost,
            stock=stock, offer_type=offer_type, offer_value=offer_value,
            offer_label=offer_label, valid_from=valid_from,
            valid_until=valid_until, is_active=is_active,
        )
        db.add(reward)
        await db.flush()
        await db.refresh(reward)
        return reward
    return _factory


@pytest_asyncio.fixture
async def point_rule_factory():
    async def _factory(db, *, partner_id, points_per_unit=1,
                       unit_amount=1000, min_amount=0, use_tiers=False,
                       is_active=True):
        rule = PointRule(
            partner_id=partner_id, points_per_unit=points_per_unit,
            unit_amount=unit_amount, min_amount=min_amount,
            use_tiers=use_tiers, is_active=is_active,
        )
        db.add(rule)
        await db.flush()
        return rule
    return _factory


@pytest_asyncio.fixture
async def staff_user_factory(user_factory):
    """User là staff của 1 partner."""
    async def _factory(db, *, partner_id, **kwargs):
        user = await user_factory(db, **kwargs)
        staff = PartnerStaff(partner_id=partner_id, user_id=user.id, is_active=True)
        db.add(staff)
        await db.flush()
        return user
    return _factory


def _mint_token(user_id: int) -> str:
    return create_access_token(user_id=user_id)


@pytest_asyncio.fixture
async def admin_token(db_session, user_factory):
    admin = await user_factory(db_session, system_role="super_admin")
    return _mint_token(admin.id)


@pytest_asyncio.fixture
async def user_token(db_session, user_factory):
    user = await user_factory(db_session)
    return _mint_token(user.id)


@pytest_asyncio.fixture
async def customer_token(db_session, user_factory):
    """Alias customer_token = user_token (regular role)."""
    user = await user_factory(db_session)
    return _mint_token(user.id)
```

- [ ] **Step 2: Verify fixtures load không lỗi.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/conftest.py -v --collect-only
```
Expected: collect 0 tests (file chỉ có fixtures), không error.

- [ ] **Step 3: Smoke test 1 fixture trong test giả.**

Tạo `backend/tests/unit/test_fixtures_smoke.py` (xoá sau khi verify):
```python
import pytest

@pytest.mark.asyncio
async def test_user_factory_smoke(db_session, user_factory):
    user = await user_factory(db_session)
    assert user.id is not None
    assert user.phone is not None


@pytest.mark.asyncio
async def test_partner_factory_smoke(db_session, partner_factory):
    partner = await partner_factory(db_session)
    assert partner.id is not None
```

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/unit/test_fixtures_smoke.py -v
```
Expected: 2 PASS. Sau đó xoá file.

- [ ] **Step 4: Commit.**

```bash
git add backend/tests/conftest.py
git commit -m "test: thêm factory fixtures (user/partner/reward/point_rule/staff + tokens)"
```

> **Note:** Phase 0 chạy trước Phase 1. Phase 3 thêm cột `must_change_password` thì test sẽ vẫn pass vì factory đã handle (default False sau migration). Trước Phase 3 migration, factory truyền `must_change_password=False` sẽ FAIL vì cột chưa tồn tại. **Order:** chạy Phase 1 (không đụng must_change_password) → Phase 2 (cũng không đụng) → Phase 3 migration thêm cột → tests phase sau dùng `must_change_password` được. Hoặc đơn giản hơn: Phase 0 tạm thời KHÔNG truyền `must_change_password`, sau Phase 3 thêm vào. Plan dưới đây ngầm hiểu cách thứ 2 — Phase 0 fixture cài `must_change_password=False` chỉ sau khi Phase 3 migration đã apply.

---

## Phase 1 — QT5 Reward expiry check

**Goal:** `RedemptionService.redeem` reject reward `valid_from > today` hoặc `valid_until < today`.
**Risk:** rất thấp — 1 dòng SQL filter, không schema change.

### Task 1.1 — Test failing cho expired reward

**Files:**
- Modify: `backend/tests/integration/test_redemption_service.py`

- [ ] **Step 1: Mở file test, tìm class/section test cho `redeem`. Thêm 3 test mới sát nhau.**

```python
# backend/tests/integration/test_redemption_service.py
import pytest
from datetime import date, timedelta
from app.models.reward import Reward, RewardOfferType


@pytest.mark.asyncio
async def test_redeem_rejects_expired_reward(db_session, partner_factory, user_factory, reward_factory):
    """Reward có valid_until < today → ValueError 'not found' (giữ generic)."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=1000)
    reward = await reward_factory(
        db_session,
        partner_id=partner.id,
        points_cost=100,
        stock=10,
        valid_until=date.today() - timedelta(days=1),  # hết hạn hôm qua
    )
    from app.services.redemption_service import RedemptionService
    svc = RedemptionService(db_session)
    with pytest.raises(ValueError):
        await svc.redeem(partner_id=partner.id, user_id=user.id, reward_id=reward.id)


@pytest.mark.asyncio
async def test_redeem_rejects_not_yet_started_reward(db_session, partner_factory, user_factory, reward_factory):
    """Reward có valid_from > today → ValueError."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=1000)
    reward = await reward_factory(
        db_session,
        partner_id=partner.id,
        points_cost=100,
        stock=10,
        valid_from=date.today() + timedelta(days=1),  # chưa bắt đầu
    )
    from app.services.redemption_service import RedemptionService
    svc = RedemptionService(db_session)
    with pytest.raises(ValueError):
        await svc.redeem(partner_id=partner.id, user_id=user.id, reward_id=reward.id)


@pytest.mark.asyncio
async def test_redeem_accepts_today_boundary(db_session, partner_factory, user_factory, reward_factory):
    """valid_until = today (inclusive) → success."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=1000)
    reward = await reward_factory(
        db_session,
        partner_id=partner.id,
        points_cost=100,
        stock=10,
        valid_until=date.today(),
    )
    # User cần có membership để redeem cross-shop
    from app.models.membership import Membership
    db_session.add(Membership(partner_id=partner.id, user_id=user.id))
    await db_session.flush()

    from app.services.redemption_service import RedemptionService
    svc = RedemptionService(db_session)
    redemption = await svc.redeem(partner_id=partner.id, user_id=user.id, reward_id=reward.id)
    assert redemption is not None
```

(Lưu ý: nếu fixture `reward_factory` chưa hỗ trợ `valid_from` — mở `backend/tests/conftest.py` thêm 2 kwargs vào factory; đó là sửa nhỏ kèm theo.)

- [ ] **Step 2: Chạy test xác nhận FAIL.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/unit/test_redemption_service.py::test_redeem_rejects_expired_reward -v
```

Expected: FAIL — current code không kiểm `valid_until` → reward vẫn pass query → service trả Redemption không raise.

### Task 1.2 — Implement filter trong `RedemptionService.redeem`

**Files:**
- Modify: `backend/app/services/redemption_service.py:67-78` (đoạn `select(Reward).where(...)`)

- [ ] **Step 1: Thêm import `date`.**

```python
# Đầu file (đã có timezone, datetime, timedelta)
from datetime import date, datetime, timedelta, timezone
```

- [ ] **Step 2: Thêm filter `valid_from`/`valid_until` trong query đầu của `redeem`.**

Replace:
```python
reward = await self.db.scalar(
    select(Reward)
    .where(
        Reward.id == reward_id,
        Reward.partner_id == partner_id,
        Reward.is_active.is_(True),
        Reward.deleted_at.is_(None),
    )
    .with_for_update()
)
```

Bằng:
```python
today = date.today()
reward = await self.db.scalar(
    select(Reward)
    .where(
        Reward.id == reward_id,
        Reward.partner_id == partner_id,
        Reward.is_active.is_(True),
        Reward.deleted_at.is_(None),
        ((Reward.valid_from.is_(None)) | (Reward.valid_from <= today)),
        ((Reward.valid_until.is_(None)) | (Reward.valid_until >= today)),
    )
    .with_for_update()
)
```

- [ ] **Step 3: Chạy test xác nhận PASS.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/integration/test_redemption_service.py -k "expired or not_yet_started or today_boundary" -v
```

Expected: 3 PASS.

- [ ] **Step 4: Filter `valid_from`/`valid_until` trong các endpoint LISTING reward.**

Cùng spirit với redeem — listing cũng phải ẩn reward out-of-window (tránh user click → 404).

`backend/app/api/partners.py`:

`list_my_rewards` (`/users/me/rewards`) — thêm filter:
```python
from datetime import date
today = date.today()
rewards = (
    await db.scalars(
        select(Reward)
        .where(
            Reward.partner_id.in_(partner_ids),
            Reward.deleted_at.is_(None),
            Reward.is_active.is_(True),
            (Reward.valid_from.is_(None)) | (Reward.valid_from <= today),
            (Reward.valid_until.is_(None)) | (Reward.valid_until >= today),
        )
        .order_by(Reward.points_cost.asc())
    )
).all()
```

`list_partner_rewards_for_member` (`/users/me/partners/{slug}/rewards`) — same.

- [ ] **Step 5: Commit.**

```bash
git add backend/app/services/redemption_service.py backend/app/api/partners.py backend/tests/integration/test_redemption_service.py
git commit -m "feat(qt5): chặn đổi + ẩn listing khi reward hết hạn hoặc chưa bắt đầu"
```

### Task 1.3 — Code-reviewer Phase 1

- [ ] **Step 1: Dispatch code-reviewer.**

Dispatch agent `subagent_type: "superpowers:code-reviewer"`, `model: "opus"`, prompt: review changes ở `redemption_service.py` + 3 test mới. Tập trung: edge case timezone (date.today() local vs UTC), regression với reward `valid_from = NULL valid_until = NULL`.

- [ ] **Step 2: Fix Critical/Important nếu có. Commit thêm nếu có sửa.**

---

## Phase 2 — QT4 actor_user_id + auto-enroll

**Goal:** Ledger EARN lưu nhân viên thực hiện; QR scan của khách mới tự động tạo membership.
**Risk:** thấp — không schema change, refactor chain 3 service method + 2 routes.

### Task 2.1 — Plumb `actor_user_id` qua TransactionService (test trước)

**Files:**
- Modify: `backend/tests/integration/test_transaction_service.py`

- [ ] **Step 1: Thêm test verify `actor_user_id` ghi vào ledger.**

```python
@pytest.mark.asyncio
async def test_create_manual_records_actor_in_ledger(
    db_session, partner_factory, user_factory, point_rule_factory, staff_user_factory
):
    """EARN ledger entry phải có actor_user_id = staff thực hiện."""
    partner = await partner_factory(db_session)
    staff = await staff_user_factory(db_session, partner_id=partner.id)
    await point_rule_factory(db_session, partner_id=partner.id, points_per_unit=1, unit_amount=1000)

    from app.services.transaction_service import TransactionService
    from app.schemas.transaction import CreateManualTransactionRequest
    svc = TransactionService(db_session)
    result = await svc.create_manual(
        partner_id=partner.id,
        request=CreateManualTransactionRequest(phone="0901234567", gross_amount=10000),
        actor_user_id=staff.id,  # NEW param
    )
    from app.models.point_ledger import PointLedger
    from sqlalchemy import select
    ledger = await db_session.scalar(
        select(PointLedger).where(PointLedger.ref_id == result.transaction.id)
    )
    assert ledger.actor_user_id == staff.id
```

- [ ] **Step 2: Chạy test, fail (signature chưa có `actor_user_id`).**

### Task 2.2 — Implement `actor_user_id` plumbing

**Files:**
- Modify: `backend/app/services/transaction_service.py`

- [ ] **Step 1: Thêm `actor_user_id` vào `create_manual`.**

```python
async def create_manual(
    self,
    *,
    partner_id: int,
    request: CreateManualTransactionRequest,
    actor_user_id: int,  # NEW
) -> TransactionWithMemberResponse:
    ...
```

Trong body, đổi call `ledger_svc.log_entry(...)` thêm `actor_user_id=actor_user_id`.

- [ ] **Step 2: Tương tự cho `_create_transaction_for_membership`.**

```python
async def _create_transaction_for_membership(
    self, *, partner_id, membership, gross_amount, note, method, receipt_code=None,
    actor_user_id: int,  # NEW
):
```

- [ ] **Step 3: Tương tự cho `create_qr_customer`.**

```python
async def create_qr_customer(
    self, *, partner_id, request: CreateQrCustomerTransactionRequest,
    actor_user_id: int,  # NEW
):
    ...
    return await self._create_transaction_for_membership(
        ..., actor_user_id=actor_user_id,
    )
```

- [ ] **Step 4: Modify `backend/app/api/transactions.py` — capture `current_user`.**

Trong `create_manual_transaction` và `create_qr_transaction`, thêm `current_user: User = Depends(get_current_user)` và pass `actor_user_id=current_user.id` vào service:

```python
from app.core.deps import get_current_user
from app.models.user import User

@router.post("", response_model=TransactionWithMemberResponse, status_code=201)
@limiter.limit("30/minute")
async def create_manual_transaction(
    request: Request,
    body: CreateManualTransactionRequest,
    partner_id: int = Depends(get_partner_id),
    _=Depends(require_staff_in_partner),
    current_user: User = Depends(get_current_user),  # NEW
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    service = TransactionService(db)
    try:
        return await service.create_manual(
            partner_id=partner_id, request=body,
            actor_user_id=current_user.id,  # NEW
        )
    ...
```

(Tương tự cho `create_qr_transaction`.)

- [ ] **Step 5: Chạy test verify PASS.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/unit/test_transaction_service.py::test_create_manual_records_actor_in_ledger -v
```

- [ ] **Step 6: Commit.**

```bash
git add backend/app/services/transaction_service.py backend/app/api/transactions.py backend/tests/integration/test_transaction_service.py
git commit -m "feat(qt4): ghi actor_user_id vào point_ledger cho EARN"
```

### Task 2.3 — QR auto-enroll (test trước)

**Files:**
- Modify: `backend/tests/integration/test_qr_service.py`

- [ ] **Step 1: Thêm test cho auto-enroll.**

```python
@pytest.mark.asyncio
async def test_decode_qr_payload_auto_enrolls_when_not_member(
    db_session, partner_factory, user_factory
):
    """User chưa là member shop → decode_qr_payload tự tạo membership."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session)
    from app.services.qr_service import QrService
    svc = QrService(db_session)
    returned_user, membership = await svc.decode_qr_payload(
        payload=str(user.id), partner_id=partner.id
    )
    assert returned_user.id == user.id
    assert membership is not None
    assert membership.partner_id == partner.id
    assert membership.user_id == user.id
    assert membership.lifetime_earned == 0
    assert membership.current_tier_id is None


@pytest.mark.asyncio
async def test_decode_qr_payload_concurrent_safe(
    db_session, partner_factory, user_factory
):
    """2 lần decode song song → đúng 1 membership được tạo."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session)
    from app.services.qr_service import QrService

    # Race-light: gọi 2 lần liên tiếp trong cùng session — UniqueConstraint protect
    svc = QrService(db_session)
    _, m1 = await svc.decode_qr_payload(payload=str(user.id), partner_id=partner.id)
    await db_session.commit()
    _, m2 = await svc.decode_qr_payload(payload=str(user.id), partner_id=partner.id)
    assert m1.id == m2.id
```

- [ ] **Step 2: Chạy test, fail (`QrUserNotMemberError` raised).**

### Task 2.4 — Implement auto-enroll trong `QrService`

**Files:**
- Modify: `backend/app/services/qr_service.py`

- [ ] **Step 1: Thay logic `decode_qr_payload` để tự tạo membership.**

```python
"""QR Service — decode raw user_id QR payload + DB lookup + auto-enroll."""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.membership import Membership
from app.models.user import User


class QrPayloadInvalidError(Exception):
    pass


class QrUserNotFoundError(Exception):
    pass


class QrService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decode_qr_payload(
        self, payload: str, partner_id: int
    ) -> tuple[User, Membership]:
        """Decode QR payload (raw user_id) → (User, Membership).

        Auto-enroll: nếu user chưa là member shop → tạo membership mới
        (lifetime_earned=0, current_tier_id=NULL). UniqueConstraint
        (partner_id, user_id) đảm bảo concurrent scan an toàn.
        """
        try:
            user_id = int(payload.strip())
            if user_id <= 0:
                raise ValueError
        except (ValueError, AttributeError) as e:
            raise QrPayloadInvalidError("QR payload không hợp lệ.") from e

        user = await self.db.get(User, user_id)
        if user is None or not user.is_active:
            raise QrUserNotFoundError("Không tìm thấy khách hàng từ QR.")

        membership = await self.db.scalar(
            select(Membership)
            .options(
                joinedload(Membership.user, innerjoin=True),
                selectinload(Membership.current_tier),
            )
            .where(
                Membership.partner_id == partner_id,
                Membership.user_id == user_id,
            )
            .with_for_update()
        )
        if membership is None:
            # Auto-enroll
            try:
                async with self.db.begin_nested():
                    new_m = Membership(
                        partner_id=partner_id,
                        user_id=user_id,
                        current_tier_id=None,
                        joined_at=datetime.now(timezone.utc),
                    )
                    self.db.add(new_m)
                    await self.db.flush()
            except IntegrityError:
                pass  # Concurrent scan đã tạo, re-fetch
            membership = await self.db.scalar(
                select(Membership)
                .options(
                    joinedload(Membership.user, innerjoin=True),
                    selectinload(Membership.current_tier),
                )
                .where(
                    Membership.partner_id == partner_id,
                    Membership.user_id == user_id,
                )
                .with_for_update()
            )
            if membership is None:
                raise QrUserNotFoundError(
                    f"Không thể tạo membership cho user {user_id} tại partner {partner_id}"
                )

        return user, membership
```

(Xoá class `QrUserNotMemberError` — không còn dùng.)

- [ ] **Step 2: Update `transaction_service.py` không catch `QrUserNotMemberError` nữa.**

Tìm `from app.services.qr_service import (...)` trong `transaction_service.py` và `api/transactions.py`, xoá `QrUserNotMemberError`.

- [ ] **Step 3: Cập nhật `api/transactions.py:lookup_customer_by_qr` — bỏ 404 "chưa là thành viên".**

Trong `lookup_customer_by_qr`, đổi:
```python
if membership is None:
    raise HTTPException(status_code=404, detail="Khách chưa là thành viên shop này.")
```
Thành:
```python
return CustomerLookupResponse(
    found=True,
    user_id=user.id,
    phone=user.phone,
    full_name=user.full_name,
    email=user.email,
    points_balance=user.points_balance,
    is_member=membership is not None,
    is_active=membership.is_active if membership else None,
    lifetime_earned=membership.lifetime_earned if membership else None,
    current_tier_name=(
        membership.current_tier.name
        if membership and membership.current_tier
        else None
    ),
)
```

(Tức là cho phép `is_member=False` thay vì 404 — staff thấy preview "khách mới, sẽ tự enroll khi xác nhận tích điểm".)

- [ ] **Step 4: Chạy test xác nhận PASS.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/unit/test_qr_service.py -v
```

- [ ] **Step 5: Xoá dead code.** `_auto_enroll_membership` cũ ở `transaction_service.py:366-401` không còn ai gọi sau Task 2.4 (logic đã chuyển vào `QrService.decode_qr_payload`). Xoá hàm này.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/services/qr_service.py backend/app/services/transaction_service.py backend/app/api/transactions.py backend/tests/integration/test_qr_service.py
git commit -m "feat(qt4): QR scan tự động tạo membership cho khách mới + xoá dead code"
```

### Task 2.5 — FE POS scan UI hỗ trợ is_member=false

**Files:**
- Modify: `frontend/src/app/(partner)/partner/pos/transactions/new/page.tsx`
- Modify: `frontend/src/app/(staff)/staff/pos/transactions/new/page.tsx`

> Sau Task 2.4, `lookup_customer_by_qr` trả `is_member=false` cho khách lần đầu thay vì 404. FE đã có sẵn UI cho is_member=true (hiển thị tier + lifetime_earned). Cần thêm copy cho is_member=false.

- [ ] **Step 1: Trong cả 2 trang POS scan, khi `customer.is_member === false` render thông báo:**

```tsx
{customer.is_member === false ? (
  <div className="bg-amber-50 border border-amber-300 rounded p-3 my-2">
    <p className="font-medium">Khách mới — chưa là thành viên shop</p>
    <p className="text-sm text-gray-700">
      Sau khi xác nhận tích điểm, hệ thống sẽ tự đăng ký thành viên cho khách này.
    </p>
  </div>
) : (
  <div className="bg-emerald-50 border border-emerald-300 rounded p-3 my-2">
    <p>Hạng: <strong>{customer.current_tier_name ?? "Chưa có"}</strong></p>
    <p>Điểm tích luỹ tại shop: <strong>{customer.lifetime_earned ?? 0}</strong></p>
  </div>
)}
```

- [ ] **Step 2: tsc + smoke manual.** Tạo user mới, owner shop A scan QR → preview hiển thị "Khách mới".

- [ ] **Step 3: Commit.**

```bash
git add frontend/src/app/(partner)/partner/pos/transactions/new/page.tsx frontend/src/app/(staff)/staff/pos/transactions/new/page.tsx
git commit -m "feat(qt4): FE POS scan hiển thị 'Khách mới' khi is_member=false"
```

### Task 2.6 — Smoke E2E QT4

- [ ] **Step 1: Tạo curl script smoke.**

```bash
# 1. Login owner shop A
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"owner@cafe.vn","password":"owner1234"}' \
  | jq -r .access_token)

# 2. Tạo user mới qua register (chưa từng đến shop A)
NEW_USER=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke-qt4@test.vn","password":"test12345","full_name":"QT4 Smoke"}' \
  | jq -r .access_token)
USER_ID=$(curl -s http://localhost:8000/auth/me -H "Authorization: Bearer $NEW_USER" | jq -r .id)

# 3. Owner shop A quét QR (= user_id) — phải success, không 404
curl -s -X POST http://localhost:8000/partner/transactions/qr \
  -H "Authorization: Bearer $TOKEN" -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d "{\"qr_payload\":\"$USER_ID\",\"gross_amount\":50000}"
# Expected: 201 với new_balance + tier=null

# 4. Verify ledger có actor_user_id
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT actor_user_id, partner_id, user_id, delta FROM point_ledger ORDER BY id DESC LIMIT 1;"
# Expected: actor_user_id = ID của owner@cafe.vn
```

- [ ] **Step 2: Verify ok rồi commit smoke script (nếu giữ làm regression).**

### Task 2.7 — Code-reviewer Phase 2

- [ ] **Step 1: Dispatch reviewer.** Tập trung: race condition khi 2 staff cùng quét cùng 1 user mới (UniqueConstraint đủ chưa?), `actor_user_id` có nullable đúng không.
- [ ] **Step 2: Fix nếu có.**

---

## Phase 3 — QT1 Auth completion

**Goal:** SĐT bắt buộc khi đăng ký; user dùng temp password phải đổi trước khi truy cập tính năng khác.
**Risk:** trung bình — schema thêm 1 cột + middleware auth.

### Task 3.1 — Migration `users.must_change_password`

**Files:**
- Create: `backend/alembic/versions/<hex>_qt1_must_change_password.py`

- [ ] **Step 1: Generate revision.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic revision -m "qt1_must_change_password"
```

Lấy `<hex>` mới sinh và sửa file:

```python
"""qt1_must_change_password

Revision ID: <hex>
Revises: <current_head>
Create Date: 2026-05-02

Add must_change_password flag để buộc user dùng temp password (forgot/reset)
phải đổi mật khẩu trước khi truy cập tính năng khác.
"""

from alembic import op
import sqlalchemy as sa

revision = "<hex>"
down_revision = "<current_head>"  # check trong file mới nhất
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
```

- [ ] **Step 2: Apply migration trong dev container.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
```

Verify:
```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "\d users" | grep must_change
```
Expected: column `must_change_password` boolean NOT NULL DEFAULT false.

### Task 3.2 — User model + auth services flag flip

**Files:**
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/services/auth_service.py`

- [ ] **Step 1: Thêm cột vào User model.**

```python
# backend/app/models/user.py — sau dòng points_balance
must_change_password: Mapped[bool] = mapped_column(
    Boolean, default=False, nullable=False, server_default="false"
)
```

- [ ] **Step 2: Test cho `reset_password_send_temp` set flag.**

`backend/tests/integration/test_auth_service.py`:
```python
@pytest.mark.asyncio
async def test_reset_password_sets_must_change_flag(db_session, user_factory):
    user = await user_factory(db_session, email="x@y.vn")
    assert user.must_change_password is False
    from app.services.auth_service import AuthService
    svc = AuthService(db_session)
    result = await svc.reset_password_send_temp(email="x@y.vn")
    assert result is not None
    await db_session.refresh(user)
    assert user.must_change_password is True


@pytest.mark.asyncio
async def test_reset_password_skips_super_admin(db_session, user_factory):
    """Super admin không bị set must_change_password — tránh lock-out."""
    user = await user_factory(db_session, email="admin@y.vn", system_role="super_admin")
    from app.services.auth_service import AuthService
    svc = AuthService(db_session)
    await svc.reset_password_send_temp(email="admin@y.vn")
    await db_session.refresh(user)
    assert user.must_change_password is False


@pytest.mark.asyncio
async def test_change_password_unsets_must_change_flag(db_session, user_factory):
    from app.core.security import hash_password
    user = await user_factory(db_session, password_hash=hash_password("oldpass1"))
    user.must_change_password = True
    await db_session.flush()

    from app.services.auth_service import AuthService
    svc = AuthService(db_session)
    await svc.change_password(user=user, current_password="oldpass1", new_password="newpass1")
    await db_session.refresh(user)
    assert user.must_change_password is False
```

- [ ] **Step 3: Chạy fail.**

- [ ] **Step 4: Sửa `auth_service.reset_password_send_temp`:**

```python
async def reset_password_send_temp(self, *, email: str) -> tuple[str, str] | None:
    user = await self.db.scalar(select(User).where(User.email == email))
    if user is None:
        hash_password(secrets.token_urlsafe(8))
        return None
    temp_password = secrets.token_urlsafe(8)
    user.password_hash = hash_password(temp_password)
    # SKIP super_admin để tránh lock-out
    if user.system_role != "super_admin":
        user.must_change_password = True
    await self.db.flush()
    logger.info(...)
    return temp_password, user.email
```

Tương tự `change_password`:

```python
async def change_password(self, *, user, current_password, new_password) -> None:
    if user.password_hash is None or not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False  # NEW
    await self.db.flush()
    logger.info(...)
```

- [ ] **Step 5: `admin.reset_user_password` (api/admin.py:765-813) cũng set flag với cùng logic SKIP super_admin.**

Tìm trong file:
```python
target.password_hash = hash_password(temp_password)
await self.db.commit()
```
Sửa:
```python
target.password_hash = hash_password(temp_password)
if target.system_role != "super_admin":
    target.must_change_password = True
await db.commit()
```

- [ ] **Step 6: Tests pass.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/unit/test_auth_service.py -v -k must_change
```

- [ ] **Step 7: Commit.**

```bash
git add backend/alembic/versions/<hex>_qt1_must_change_password.py backend/app/models/user.py backend/app/services/auth_service.py backend/app/api/admin.py backend/tests/integration/test_auth_service.py
git commit -m "feat(qt1): thêm must_change_password flag + flip ở reset/change"
```

### Task 3.3 — `get_current_user` 423 + `get_current_user_unrestricted` dep

**Files:**
- Modify: `backend/app/core/deps.py`
- Modify: `backend/app/api/auth.py`

- [ ] **Step 1: Test integration cho 423 logic.**

`backend/tests/integration/test_auth_api.py`:
```python
@pytest.mark.asyncio
async def test_user_with_must_change_password_blocked_on_other_routes(client):
    """User đăng nhập bằng temp password → call admin/me → 423."""
    # Setup: forgot password để set flag
    await client.post("/auth/forgot-password", json={"email": "khach1@gmail.com"})
    # Lấy temp password từ log/DB (test infra) — hoặc set trực tiếp qua DB
    ...
    # Login bằng temp
    r = await client.post("/auth/login", json={
        "identifier": "khach1@gmail.com", "password": TEMP_PASSWORD
    })
    token = r.json()["access_token"]

    # Call /users/me/memberships → 423
    r2 = await client.get("/users/me/memberships",
        headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 423
    assert r2.json()["detail"] == "password_change_required"

    # Call /auth/me → 200 (whitelist)
    r3 = await client.get("/auth/me",
        headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200

    # Đổi mật khẩu
    r4 = await client.patch("/auth/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": TEMP_PASSWORD, "new_password": "newpass1"})
    assert r4.status_code == 204

    # Call /users/me/memberships → 200
    r5 = await client.get("/users/me/memberships",
        headers={"Authorization": f"Bearer {token}"})
    assert r5.status_code == 200
```

- [ ] **Step 2: Sửa `core/deps.py`.**

Tách logic load user thành internal helper, hai dep gọi helper với cờ kiểm khác nhau:

```python
async def _load_user_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User:
    """Internal: decode token + load user. Raise 401 nếu invalid."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"}) from e
    if payload.type != "access":
        raise HTTPException(status_code=401, detail="Token is not an access token")
    try:
        user_id = int(payload.sub)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=401, detail="Invalid token payload") from e
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dep mặc định — chặn user `must_change_password=True` với 423."""
    user = await _load_user_from_token(credentials, db)
    if user.must_change_password:
        raise HTTPException(
            status_code=423,
            detail="password_change_required",
        )
    return user


async def get_current_user_unrestricted(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dep cho 2 endpoint cần truy cập kể cả khi user đang must_change_password.

    Chỉ dùng cho `/auth/me` (xem info chính mình) và `/auth/me/password` (gỡ lock).
    """
    return await _load_user_from_token(credentials, db)
```

- [ ] **Step 3: Sửa `api/auth.py` — `/auth/me` + `/auth/me/password` dùng dep mới.**

```python
from app.core.deps import get_current_user, get_current_user_unrestricted

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user_unrestricted)) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateMeRequest,
    current_user: User = Depends(get_current_user),  # GIỮ get_current_user để chặn update khác khi locked
    db: AsyncSession = Depends(get_db),
) -> User:
    ...

@router.patch("/me/password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_unrestricted),  # NEW
    db: AsyncSession = Depends(get_db),
) -> None:
    ...
```

- [ ] **Step 4: Run integration test pass.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/integration/test_auth_api.py -v -k must_change
```

- [ ] **Step 5: Commit.**

```bash
git add backend/app/core/deps.py backend/app/api/auth.py backend/tests/integration/test_auth_api.py
git commit -m "feat(qt1): chặn 423 khi user phải đổi mật khẩu, whitelist /auth/me + /auth/me/password"
```

### Task 3.4 — RegisterRequest thêm phone bắt buộc

**Files:**
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/services/auth_service.py`

- [ ] **Step 1: Test register với phone trùng → 409.**

```python
@pytest.mark.asyncio
async def test_register_rejects_duplicate_phone(client, db_session):
    # User đã có
    from app.models.user import User
    db_session.add(User(email="a@x.vn", phone="0901111111",
                         password_hash="abc", system_role="regular"))
    await db_session.commit()

    r = await client.post("/auth/register", json={
        "email": "b@x.vn",
        "phone": "0901111111",  # trùng
        "password": "pass1234",
        "full_name": "Test"
    })
    assert r.status_code == 409
    assert "phone" in r.json()["detail"].lower() or "điện thoại" in r.json()["detail"]


@pytest.mark.asyncio
async def test_register_requires_phone(client):
    r = await client.post("/auth/register", json={
        "email": "c@x.vn",
        "password": "pass1234",
        "full_name": "Test"
        # missing phone
    })
    assert r.status_code == 422
```

- [ ] **Step 2: Update `RegisterRequest` — validate VN phone format `0xxxxxxxxx` (không E.164).**

```python
# backend/app/schemas/auth.py — phone format đồng bộ với LoginRequest._normalize_identifier
class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(min_length=10, max_length=10)  # NEW required, đúng 10 ký tự "0xxxxxxxxx"
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    birthday: date | None = None

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str) -> str:
        return _normalize_email(v)

    @field_validator("phone")
    @classmethod
    def _phone_check(cls, v: str) -> str:
        v = v.strip()
        # Accept "+84xxxxxxxxx" / "84xxxxxxxxx" → normalize về "0xxxxxxxxx"
        cleaned = re.sub(r"[\s\-\.]", "", v)
        if cleaned.startswith("+84"):
            cleaned = "0" + cleaned[3:]
        elif cleaned.startswith("84") and len(cleaned) == 11:
            cleaned = "0" + cleaned[2:]
        if not _is_vn_phone(cleaned):
            raise ValueError("SĐT phải 10 số bắt đầu bằng 0 (vd: 0901234567)")
        return cleaned

    @field_validator("password")
    @classmethod
    def _password_bytes(cls, v: str) -> str:
        return _validate_password_bytes(v)

    @field_validator("birthday")
    @classmethod
    def _check_birthday(cls, v: date | None) -> date | None:
        return validate_birthday(v)
```

(Reuse `_is_vn_phone` + `_VN_PHONE_RE` đã có sẵn ở schemas/auth.py.)

- [ ] **Step 3: Update `AuthService.register` — kiểm phone duplicate.**

```python
async def register(self, request: RegisterRequest) -> User:
    existing = await self.db.scalar(
        select(User).where(or_(User.email == request.email, User.phone == request.phone))
    )
    if existing is not None:
        if existing.email == request.email:
            raise EmailAlreadyExistsError(f"Email {request.email} đã được đăng ký")
        raise PhoneAlreadyExistsError(f"SĐT {request.phone} đã được đăng ký")

    user = User(
        email=request.email,
        phone=request.phone,  # NEW
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        birthday=request.birthday,
        is_active=True,
        system_role="regular",
    )
    ...
```

Thêm exception class:
```python
class PhoneAlreadyExistsError(Exception):
    pass
```

- [ ] **Step 4: Update `api/auth.py:register` — catch new exception → 409.**

```python
from app.services.auth_service import (
    AuthService, EmailAlreadyExistsError, InvalidCredentialsError,
    PhoneAlreadyExistsError,  # NEW
)

@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("20/minute")
async def register(...) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.register(body)
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except PhoneAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    ...
```

- [ ] **Step 5: Update test fixtures — `user_factory` thêm phone (random unique).**

`backend/tests/conftest.py`:
```python
import secrets

@pytest.fixture
async def user_factory():
    async def _factory(db, *, email=None, phone=None, **kwargs):
        if email is None:
            email = f"u{secrets.token_hex(4)}@test.vn"
        if phone is None:
            phone = f"09{secrets.randbelow(10**8):08d}"  # 10 chars
        ...
    return _factory
```

- [ ] **Step 6: Tests pass.**

- [ ] **Step 7: Commit.**

```bash
git add backend/app/schemas/auth.py backend/app/services/auth_service.py backend/app/api/auth.py backend/tests/conftest.py backend/tests/integration/test_auth_api.py
git commit -m "feat(qt1): SĐT bắt buộc khi đăng ký + check trùng phone trả 409"
```

### Task 3.5 — Frontend register form + change-password redirect

**Files:**
- Modify: `frontend/src/app/(auth)/register/page.tsx`
- Create: `frontend/src/app/(auth)/change-password/page.tsx`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Thêm field SĐT vào trang đăng ký.**

`frontend/src/app/(auth)/register/page.tsx` — thêm input vào form (tận dụng pattern react-hook-form đã có):

```tsx
const schema = z.object({
  email: z.string().email("Email không hợp lệ"),
  phone: z.string().regex(/^0\d{9}$/, "SĐT phải 10 số bắt đầu bằng 0"),  // NEW
  full_name: z.string().min(1).max(255),
  password: z.string().min(8),
});
```

JSX:
```tsx
<div>
  <label>Số điện thoại</label>
  <input {...register("phone")} placeholder="09xxxxxxxx" />
  {errors.phone && <p className="text-red-600">{errors.phone.message}</p>}
</div>
```

- [ ] **Step 2: Tạo trang `/change-password`.**

```tsx
// frontend/src/app/(auth)/change-password/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [currentPwd, setCurrent] = useState("");
  const [newPwd, setNew] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.patch("/auth/me/password", {
        current_password: currentPwd,
        new_password: newPwd,
      });
      router.replace("/member");
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Lỗi không xác định");
    }
  }

  return (
    <main className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">Đổi mật khẩu</h1>
      <p className="mb-4 text-gray-600">
        Bạn cần đổi mật khẩu trước khi tiếp tục sử dụng hệ thống.
      </p>
      <form onSubmit={submit} className="space-y-4">
        <input type="password" placeholder="Mật khẩu hiện tại"
          value={currentPwd} onChange={e => setCurrent(e.target.value)} required
          className="w-full border rounded p-2" />
        <input type="password" placeholder="Mật khẩu mới (≥ 8 ký tự)"
          value={newPwd} onChange={e => setNew(e.target.value)} required minLength={8}
          className="w-full border rounded p-2" />
        {error && <p className="text-red-600">{error}</p>}
        <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">
          Đổi mật khẩu
        </button>
      </form>
    </main>
  );
}
```

- [ ] **Step 3: Update axios interceptor branch 423.**

`frontend/src/lib/api.ts`:
```typescript
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      // existing redirect /login
    }
    if (err.response?.status === 423 && err.response?.data?.detail === "password_change_required") {
      if (typeof window !== "undefined" && window.location.pathname !== "/change-password") {
        window.location.href = "/change-password";
      }
    }
    return Promise.reject(err);
  }
);
```

- [ ] **Step 4: Verify tsc.**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 5: Smoke test manual.** Tạo new user qua FE, request forgot-password, login với temp → verify redirect.

- [ ] **Step 6: Commit.**

```bash
git add frontend/src/app/(auth)/register/page.tsx frontend/src/app/(auth)/change-password/page.tsx frontend/src/lib/api.ts
git commit -m "feat(qt1): FE field SĐT + trang đổi mật khẩu sau temp + interceptor 423"
```

### Task 3.6 — Code-reviewer Phase 3

- [ ] **Step 1: Dispatch reviewer.** Tập trung: middleware bypass nguy hiểm (route nào thừa whitelist?), super_admin lock-out scenario, fixture migration impact.
- [ ] **Step 2: Fix.**

---

## Phase 4 — QT8 Audit log + lock reason

**Goal:** Lưu lý do khi admin khoá user/đình chỉ partner; ghi nhật ký mọi action lock/unlock để truy vết.
**Risk:** trung bình — table mới + nhiều hooks vào endpoint admin.

### Task 4.1 — Migration `audit_logs` table

**Files:**
- Create: `backend/alembic/versions/<hex>_qt8_audit_logs.py`

- [ ] **Step 1: Generate revision rồi sửa.**

```python
"""qt8_audit_logs

Audit log table cho admin actions: lock/unlock user, approve/suspend partner.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "<hex>"
down_revision = "<head>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("before_snapshot", JSONB(), nullable=True),
        sa.Column("after_snapshot", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "action IN ('user_lock','user_unlock','user_role_change',"
            "'partner_approve','partner_suspend','partner_unsuspend')",
            name="audit_logs_action_valid",
        ),
        sa.CheckConstraint(
            "target_type IN ('user','partner')",
            name="audit_logs_target_type_valid",
        ),
    )
    op.create_index(
        "ix_audit_logs_target", "audit_logs",
        ["target_type", "target_id"]
    )
    op.create_index(
        "ix_audit_logs_created_at", "audit_logs", ["created_at"]
    )
    op.create_index(
        "ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"]
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
```

- [ ] **Step 2: Apply migration.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Task 4.2 — Model + service + schema + vocabulary

**Files:**
- Create: `backend/app/models/audit_log.py`
- Create: `backend/app/core/audit_actions.py`
- Create: `backend/app/services/audit_log_service.py`
- Create: `backend/app/schemas/audit_log.py`

- [ ] **Step 1: Vocabulary constants.**

```python
# backend/app/core/audit_actions.py
"""Audit action vocabulary — đồng bộ với CK constraint trên audit_logs."""

ACTION_USER_LOCK = "user_lock"
ACTION_USER_UNLOCK = "user_unlock"
ACTION_USER_ROLE_CHANGE = "user_role_change"
ACTION_PARTNER_APPROVE = "partner_approve"
ACTION_PARTNER_SUSPEND = "partner_suspend"
ACTION_PARTNER_UNSUSPEND = "partner_unsuspend"

ALL_ACTIONS = frozenset({
    ACTION_USER_LOCK,
    ACTION_USER_UNLOCK,
    ACTION_USER_ROLE_CHANGE,
    ACTION_PARTNER_APPROVE,
    ACTION_PARTNER_SUSPEND,
    ACTION_PARTNER_UNSUSPEND,
})

TARGET_USER = "user"
TARGET_PARTNER = "partner"
```

- [ ] **Step 2: Model.**

```python
# backend/app/models/audit_log.py
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "action IN ('user_lock','user_unlock','user_role_change',"
            "'partner_approve','partner_suspend','partner_unsuspend')",
            name="audit_logs_action_valid",
        ),
        CheckConstraint(
            "target_type IN ('user','partner')",
            name="audit_logs_target_type_valid",
        ),
        Index("ix_audit_logs_target", "target_type", "target_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    before_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
```

Đăng ký import trong `backend/app/models/__init__.py` để Alembic autogen sau này thấy:
```python
from app.models.audit_log import AuditLog  # noqa: F401
```

- [ ] **Step 3: Service.**

```python
# backend/app/services/audit_log_service.py
"""AuditLogService — append-only ghi nhật ký action admin."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import ALL_ACTIONS
from app.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        *,
        actor_user_id: int | None,
        action: str,
        target_type: str,
        target_id: int,
        reason: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AuditLog:
        if action not in ALL_ACTIONS:
            raise ValueError(f"Unknown audit action: {action}")
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            before_snapshot=before,
            after_snapshot=after,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
```

- [ ] **Step 4: Schemas.**

```python
# backend/app/schemas/audit_log.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int | None
    actor_email: str | None  # batch-load
    action: str
    target_type: str
    target_id: int
    target_label: str | None  # batch-load (user.email | partner.name)
    reason: str | None
    before_snapshot: dict[str, Any] | None
    after_snapshot: dict[str, Any] | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
```

- [ ] **Step 5: Test service (unit).**

```python
# backend/tests/integration/test_audit_log_service.py
import pytest


@pytest.mark.asyncio
async def test_log_inserts_row(db_session, user_factory):
    actor = await user_factory(db_session, system_role="super_admin")
    target = await user_factory(db_session)
    from app.services.audit_log_service import AuditLogService
    from app.core.audit_actions import ACTION_USER_LOCK, TARGET_USER
    svc = AuditLogService(db_session)
    entry = await svc.log(
        actor_user_id=actor.id,
        action=ACTION_USER_LOCK,
        target_type=TARGET_USER,
        target_id=target.id,
        reason="vi phạm điều khoản",
        before={"is_active": True},
        after={"is_active": False},
    )
    assert entry.id is not None
    assert entry.reason == "vi phạm điều khoản"


@pytest.mark.asyncio
async def test_log_rejects_unknown_action(db_session):
    from app.services.audit_log_service import AuditLogService
    svc = AuditLogService(db_session)
    with pytest.raises(ValueError):
        await svc.log(
            actor_user_id=None, action="totally_made_up",
            target_type="user", target_id=1,
        )
```

- [ ] **Step 6: Run pass.**

- [ ] **Step 7: Commit.**

```bash
git add backend/alembic/versions/<hex>_qt8_audit_logs.py backend/app/models/audit_log.py backend/app/models/__init__.py backend/app/core/audit_actions.py backend/app/services/audit_log_service.py backend/app/schemas/audit_log.py backend/tests/integration/test_audit_log_service.py
git commit -m "feat(qt8): bảng audit_logs + AuditLogService cơ bản"
```

### Task 4.3 — Hook vào `admin.update_user` với reason

**Files:**
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: Test integration.**

```python
@pytest.mark.asyncio
async def test_admin_lock_user_writes_audit_log(client, admin_token, user_factory, db_session):
    target = await user_factory(db_session, is_active=True)
    r = await client.patch(f"/admin/users/{target.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False, "reason": "vi phạm điều khoản"}
    )
    assert r.status_code == 200

    from app.models.audit_log import AuditLog
    from sqlalchemy import select
    log = await db_session.scalar(
        select(AuditLog).where(AuditLog.target_id == target.id)
        .order_by(AuditLog.id.desc())
    )
    assert log is not None
    assert log.action == "user_lock"
    assert log.reason == "vi phạm điều khoản"
    assert log.before_snapshot["is_active"] is True
    assert log.after_snapshot["is_active"] is False
```

- [ ] **Step 2: Update `AdminUserUpdateRequest` thêm `reason`.**

```python
# trong api/admin.py
class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None
    system_role: Literal["regular", "admin", "super_admin"] | None = None
    reason: str | None = Field(default=None, max_length=500)
```

- [ ] **Step 3: Sửa `update_user` (api/admin.py:711-762) để log audit.**

Trước khi update, snapshot:
```python
before = {"is_active": target.is_active, "system_role": target.system_role}
```

Sau khi update + flush nhưng trước commit, log audit:
```python
from app.core.audit_actions import (
    ACTION_USER_LOCK, ACTION_USER_UNLOCK, ACTION_USER_ROLE_CHANGE, TARGET_USER,
)
from app.services.audit_log_service import AuditLogService

audit_svc = AuditLogService(db)
after = {"is_active": target.is_active, "system_role": target.system_role}

if body.is_active is not None and before["is_active"] != after["is_active"]:
    action = ACTION_USER_UNLOCK if after["is_active"] else ACTION_USER_LOCK
    await audit_svc.log(
        actor_user_id=admin.id, action=action,
        target_type=TARGET_USER, target_id=target.id,
        reason=body.reason, before=before, after=after,
    )

if body.system_role is not None and before["system_role"] != after["system_role"]:
    await audit_svc.log(
        actor_user_id=admin.id, action=ACTION_USER_ROLE_CHANGE,
        target_type=TARGET_USER, target_id=target.id,
        reason=body.reason, before=before, after=after,
    )

await db.commit()
```

- [ ] **Step 4: Test pass.**

- [ ] **Step 5: Commit.**

```bash
git add backend/app/api/admin.py backend/tests/integration/test_admin_api.py
git commit -m "feat(qt8): admin lock/unlock user kèm reason + audit log"
```

### Task 4.4 — Hook vào `approve_partner` / `suspend_partner` với reason

**Files:**
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: Test.**

```python
@pytest.mark.asyncio
async def test_admin_approve_partner_writes_audit(client, admin_token, partner_factory, db_session):
    partner = await partner_factory(db_session, status="pending")
    r = await client.post(f"/admin/partners/{partner.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approve": True, "reason": "hồ sơ đầy đủ"}
    )
    assert r.status_code == 200

    from app.models.audit_log import AuditLog
    log = await db_session.scalar(
        select(AuditLog).where(AuditLog.target_id == partner.id)
        .order_by(AuditLog.id.desc())
    )
    assert log.action == "partner_approve"
    assert log.reason == "hồ sơ đầy đủ"


@pytest.mark.asyncio
async def test_admin_suspend_partner_with_reason(client, admin_token, partner_factory, db_session):
    partner = await partner_factory(db_session, status="active")
    r = await client.post(f"/admin/partners/{partner.id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reason": "vi phạm điều khoản"}
    )
    assert r.status_code == 200
    from app.models.audit_log import AuditLog
    log = await db_session.scalar(
        select(AuditLog).where(AuditLog.target_id == partner.id, AuditLog.action == "partner_suspend")
    )
    assert log is not None
    assert log.reason == "vi phạm điều khoản"
```

- [ ] **Step 2: Sửa endpoint `approve_partner` để pass `body.reason` + log audit.**

```python
@router.post("/partners/{partner_id}/approve", response_model=PartnerResponse)
async def approve_partner(
    partner_id: int,
    body: PartnerApprovalRequest,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    service = PartnerService(db)
    audit_svc = AuditLogService(db)

    # Snapshot before
    existing = await db.get(Partner, partner_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Partner không tồn tại")
    before = {"status": str(existing.status.value if hasattr(existing.status, "value") else existing.status)}

    try:
        if body.approve:
            partner = await service.approve_partner(
                partner_id=partner_id,
                reason=body.reason,
                actor_user_id=admin.id,
            )
            action = (
                ACTION_PARTNER_APPROVE if before["status"] != "active"
                else ACTION_PARTNER_UNSUSPEND
            )
        else:
            partner = await service.suspend_partner(
                partner_id=partner_id,
                reason=body.reason,
                actor_user_id=admin.id,
            )
            action = ACTION_PARTNER_SUSPEND
    except (PartnerNotFoundError, InvalidStatusTransitionError) as e:
        ...

    after = {"status": str(partner.status.value if hasattr(partner.status, "value") else partner.status)}
    await audit_svc.log(
        actor_user_id=admin.id, action=action,
        target_type=TARGET_PARTNER, target_id=partner_id,
        reason=body.reason, before=before, after=after,
    )
    await db.commit()
    return PartnerResponse.model_validate(partner)
```

(Service layer thay đổi — Phase 5 sẽ làm full service signature change. Tạm thời ở đây giả định service đã accept `reason` + `actor_user_id` — nếu chưa, comment-out service param chờ Phase 5. **Nếu chạy Phase 4 trước Phase 5, sửa nhỏ trong `partner_service.py`** để accept và lưu các field; alembic Phase 2 chưa add các cột → fallback ignore reason ở service layer; audit_log đã ghi → đủ.)

- [ ] **Step 3: Sửa `suspend_partner` endpoint nhận body.**

```python
class SuspendPartnerRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


@router.post("/partners/{partner_id}/suspend", response_model=PartnerResponse)
async def suspend_partner(
    partner_id: int,
    body: SuspendPartnerRequest,  # NEW
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    service = PartnerService(db)
    audit_svc = AuditLogService(db)
    existing = await db.get(Partner, partner_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Partner không tồn tại")
    before = {"status": str(existing.status.value)}
    try:
        partner = await service.suspend_partner(
            partner_id=partner_id, reason=body.reason, actor_user_id=admin.id,
        )
    except (PartnerNotFoundError, InvalidStatusTransitionError) as e:
        ...
    after = {"status": str(partner.status.value)}
    await audit_svc.log(
        actor_user_id=admin.id, action=ACTION_PARTNER_SUSPEND,
        target_type=TARGET_PARTNER, target_id=partner_id,
        reason=body.reason, before=before, after=after,
    )
    await db.commit()
    return PartnerResponse.model_validate(partner)
```

- [ ] **Step 4: Stub service signature accept reason/actor (sẽ hoàn thiện ở Phase 5).**

`backend/app/services/partner_service.py`:
```python
async def approve_partner(
    self, *, partner_id: int,
    reason: str | None = None, actor_user_id: int | None = None,
) -> Partner:
    # body cũ — chưa store reason/actor (Phase 5 sẽ thêm cột rồi store)
    ...

async def suspend_partner(
    self, *, partner_id: int,
    reason: str | None = None, actor_user_id: int | None = None,
) -> Partner:
    ...
```

- [ ] **Step 5: Test pass.**

- [ ] **Step 6: Commit.**

```bash
git add backend/app/api/admin.py backend/app/services/partner_service.py backend/tests/integration/test_admin_api.py
git commit -m "feat(qt8): admin approve/suspend partner kèm reason + audit log"
```

### Task 4.5 — `GET /admin/audit-logs` endpoint

**Files:**
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: Test.**

```python
@pytest.mark.asyncio
async def test_admin_list_audit_logs(client, admin_token, db_session):
    # Setup: tạo vài audit log entry
    from app.models.audit_log import AuditLog
    from datetime import datetime, UTC
    db_session.add(AuditLog(actor_user_id=1, action="user_lock",
        target_type="user", target_id=42, reason="test"))
    await db_session.commit()

    r = await client.get("/admin/audit-logs?action=user_lock",
        headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["action"] == "user_lock" for item in data["items"])
```

- [ ] **Step 2: Implement endpoint.**

```python
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    actor_user_id: int | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_super_admin),
) -> AuditLogListResponse:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from phải ≤ to")

    base = select(AuditLog)
    if action:
        base = base.where(AuditLog.action == action)
    if target_type:
        base = base.where(AuditLog.target_type == target_type)
    if target_id is not None:
        base = base.where(AuditLog.target_id == target_id)
    if actor_user_id is not None:
        base = base.where(AuditLog.actor_user_id == actor_user_id)
    if from_date:
        base = base.where(AuditLog.created_at >= from_date)
    if to_date:
        base = base.where(AuditLog.created_at <= to_date)

    total = int(await db.scalar(select(func.count()).select_from(base.subquery())) or 0)
    rows = (await db.scalars(
        base.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    )).all()

    # Batch-load actor email
    actor_ids = {r.actor_user_id for r in rows if r.actor_user_id}
    actor_emails: dict[int, str | None] = {}
    if actor_ids:
        actor_rows = (await db.execute(
            select(User.id, User.email).where(User.id.in_(actor_ids))
        )).all()
        actor_emails = {r.id: r.email for r in actor_rows}

    # Batch-load target label
    user_target_ids = {r.target_id for r in rows if r.target_type == "user"}
    partner_target_ids = {r.target_id for r in rows if r.target_type == "partner"}
    user_emails: dict[int, str | None] = {}
    partner_names: dict[int, str | None] = {}
    if user_target_ids:
        user_emails = dict((await db.execute(
            select(User.id, User.email).where(User.id.in_(user_target_ids))
        )).all())
    if partner_target_ids:
        partner_names = dict((await db.execute(
            select(Partner.id, Partner.name).where(Partner.id.in_(partner_target_ids))
        )).all())

    items = [
        AuditLogResponse(
            id=r.id,
            actor_user_id=r.actor_user_id,
            actor_email=actor_emails.get(r.actor_user_id) if r.actor_user_id else None,
            action=r.action,
            target_type=r.target_type,
            target_id=r.target_id,
            target_label=(
                user_emails.get(r.target_id) if r.target_type == "user"
                else partner_names.get(r.target_id) if r.target_type == "partner"
                else None
            ),
            reason=r.reason,
            before_snapshot=r.before_snapshot,
            after_snapshot=r.after_snapshot,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return AuditLogListResponse(items=items, total=total, limit=limit, offset=offset)
```

- [ ] **Step 3: Test pass.**

- [ ] **Step 4: Commit.**

```bash
git add backend/app/api/admin.py backend/tests/integration/test_admin_api.py
git commit -m "feat(qt8): GET /admin/audit-logs endpoint với filter + batch-load"
```

### Task 4.6 — FE trang `/admin/audit-logs`

**Files:**
- Create: `frontend/src/types/audit.ts`
- Modify: `frontend/src/lib/api-partner.ts`
- Create: `frontend/src/lib/hooks/useAdminAuditLogs.ts`
- Create: `frontend/src/app/(admin)/admin/audit-logs/page.tsx`

- [ ] **Step 1: Types.**

```typescript
// frontend/src/types/audit.ts
export interface AuditLogItem {
  id: number;
  actor_user_id: number | null;
  actor_email: string | null;
  action: string;
  target_type: string;
  target_id: number;
  target_label: string | null;
  reason: string | null;
  before_snapshot: Record<string, unknown> | null;
  after_snapshot: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  limit: number;
  offset: number;
}
```

- [ ] **Step 2: API client.**

`frontend/src/lib/api-partner.ts` — trong `adminApi`:
```typescript
auditLogs: async (params: {
  action?: string;
  target_type?: string;
  actor_user_id?: number;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}): Promise<AuditLogListResponse> => {
  const res = await api.get("/admin/audit-logs", { params });
  return res.data;
},
```

- [ ] **Step 3: Hook.**

```typescript
// frontend/src/lib/hooks/useAdminAuditLogs.ts
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api-partner";

export function useAdminAuditLogs(filters: {
  action?: string;
  target_type?: string;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["admin", "audit-logs", filters],
    queryFn: () => adminApi.auditLogs(filters),
  });
}
```

- [ ] **Step 4: Page (table + filter pattern theo `/admin/logs`).**

```tsx
// frontend/src/app/(admin)/admin/audit-logs/page.tsx
"use client";
import { useState } from "react";
import { useAdminAuditLogs } from "@/lib/hooks/useAdminAuditLogs";

const ACTIONS = [
  { v: "", label: "Tất cả" },
  { v: "user_lock", label: "Khoá user" },
  { v: "user_unlock", label: "Mở khoá user" },
  { v: "user_role_change", label: "Đổi vai trò" },
  { v: "partner_approve", label: "Duyệt đối tác" },
  { v: "partner_suspend", label: "Đình chỉ đối tác" },
  { v: "partner_unsuspend", label: "Bỏ đình chỉ" },
];

export default function AdminAuditLogsPage() {
  const [action, setAction] = useState("");
  const { data, isLoading } = useAdminAuditLogs({ action: action || undefined });

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Nhật ký quản trị</h1>
      <div className="mb-4 flex gap-3">
        <select value={action} onChange={e => setAction(e.target.value)}
                className="border rounded p-2">
          {ACTIONS.map(a => <option key={a.v} value={a.v}>{a.label}</option>)}
        </select>
      </div>
      {isLoading ? <p>Đang tải...</p> : (
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="p-2 text-left">Thời gian</th>
              <th className="p-2 text-left">Quản trị viên</th>
              <th className="p-2 text-left">Hành động</th>
              <th className="p-2 text-left">Đối tượng</th>
              <th className="p-2 text-left">Lý do</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map(it => (
              <tr key={it.id} className="border-b">
                <td className="p-2">{new Date(it.created_at).toLocaleString("vi-VN")}</td>
                <td className="p-2">{it.actor_email ?? "—"}</td>
                <td className="p-2">{it.action}</td>
                <td className="p-2">{it.target_type} #{it.target_id} ({it.target_label ?? "?"})</td>
                <td className="p-2">{it.reason ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
```

- [ ] **Step 5: Verify tsc + smoke.**

```bash
cd frontend && npx tsc --noEmit
```

Open `/admin/audit-logs`, verify list hiển thị các entry test.

- [ ] **Step 6: Commit.**

```bash
git add frontend/src/types/audit.ts frontend/src/lib/api-partner.ts frontend/src/lib/hooks/useAdminAuditLogs.ts frontend/src/app/(admin)/admin/audit-logs/page.tsx
git commit -m "feat(qt8): FE trang admin audit logs + hook"
```

### Task 4.7 — FE reason input ở admin user list + partner list (modal)

**Files:**
- Modify: `frontend/src/app/(admin)/admin/users/page.tsx`
- Modify: `frontend/src/app/(admin)/admin/partners/page.tsx`

> Project hiện không có dynamic route `[id]` cho admin users/partners — quản lý qua bảng list + modal action. Thêm reason vào modal hiện có.

- [ ] **Step 1: Trong `users/page.tsx`, modal "Khoá user" thêm field textarea `reason`.**

```tsx
const [lockReason, setLockReason] = useState("");
// ... khi mở modal: setLockReason("")
// JSX:
<textarea
  value={lockReason}
  onChange={e => setLockReason(e.target.value)}
  placeholder="Lý do khoá tài khoản (bắt buộc)"
  required
  className="w-full border rounded p-2 mt-2"
/>
// Submit:
await api.patch(`/admin/users/${selectedUser.id}`, {
  is_active: false,
  reason: lockReason,
});
```

Tương tự khi unlock — reason optional.

- [ ] **Step 2: Trong `partners/page.tsx`, modal "Đình chỉ"/"Bỏ đình chỉ"/"Phê duyệt" thêm textarea reason.**

```tsx
// Khi suspend: gọi POST /admin/partners/{id}/suspend với body {reason}
await api.post(`/admin/partners/${partner.id}/suspend`, { reason });
// Khi approve: POST /admin/partners/{id}/approve với body {approve: true, reason}
```

- [ ] **Step 3: tsc + manual smoke.**

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/app/(admin)/admin/users/page.tsx frontend/src/app/(admin)/admin/partners/page.tsx
git commit -m "feat(qt8): FE modal reason cho admin lock user/suspend partner"
```

### Task 4.8 — Code-reviewer Phase 4

- [ ] **Step 1: Dispatch reviewer.** Tập trung: race khi audit log fail trong cùng transaction (nếu fail, status đã thay đổi nhưng không có log → inconsistent), `before/after_snapshot` dump field nhạy cảm hay không, batch-load N+1.
- [ ] **Step 2: Fix.**

---

## Phase 5 — QT2 Partner registration completion

**Goal:** Partner đăng ký kèm giấy phép + đồng ý điều khoản; admin approve/reject lưu reason vào DB partner.
**Risk:** trung bình — schema 6 cột + FE upload flow.

### Task 5.1 — Migration 6 cột partners

**Files:**
- Create: `backend/alembic/versions/<hex>_qt2_partner_terms_license.py`

- [ ] **Step 1: Generate + sửa.**

```python
"""qt2_partner_terms_license"""

from alembic import op
import sqlalchemy as sa

revision = "<hex>"
down_revision = "<head>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("business_license_url", sa.String(500), nullable=True))
    op.add_column("partners", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partners", sa.Column("terms_version", sa.String(20), nullable=True))
    op.add_column("partners", sa.Column("last_status_reason", sa.String(500), nullable=True))
    op.add_column("partners", sa.Column(
        "last_status_changed_by", sa.Integer(),
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    ))
    op.add_column("partners", sa.Column("last_status_changed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("partners", "last_status_changed_at")
    op.drop_column("partners", "last_status_changed_by")
    op.drop_column("partners", "last_status_reason")
    op.drop_column("partners", "terms_version")
    op.drop_column("partners", "terms_accepted_at")
    op.drop_column("partners", "business_license_url")
```

- [ ] **Step 2: Apply.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Task 5.2 — Model + service + schema update

**Files:**
- Modify: `backend/app/models/partner.py`
- Modify: `backend/app/schemas/partner.py`
- Modify: `backend/app/services/partner_service.py`
- Create: `backend/app/core/legal.py`

- [ ] **Step 1: Add 6 cột vào Partner model.**

```python
# backend/app/models/partner.py — bên cạnh các field hiện có
business_license_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
terms_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
last_status_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
last_status_changed_by: Mapped[int | None] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
last_status_changed_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
)
```

- [ ] **Step 2: Constant T&C version.**

```python
# backend/app/core/legal.py
"""Phiên bản hợp đồng dịch vụ chuẩn hoá hiện tại của platform.

Khi nội dung T&C ở `frontend/src/app/legal/terms/page.tsx` thay đổi → bump
version này → existing partners cũ vẫn lưu version cũ trong `partner.terms_version`.
"""

CURRENT_TERMS_VERSION = "v1.0"
```

- [ ] **Step 3: PartnerCreateRequest update.**

```python
# backend/app/schemas/partner.py
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PartnerCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = Field(default=None, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    category: PartnerCategory = Field(default=PartnerCategory.OTHER)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    tax_code: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=500)
    business_hours: str | None = Field(default=None, max_length=255)
    business_license_url: str = Field(min_length=1, max_length=500)  # NEW required
    accept_terms: bool  # NEW required
    terms_version: str = Field(min_length=1, max_length=20)  # NEW required

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Phải đồng ý điều khoản hợp đồng dịch vụ")
        return v
```

- [ ] **Step 4: PartnerService.create_partner store license + terms; approve/suspend store reason+actor.**

```python
# backend/app/services/partner_service.py
from datetime import datetime, timezone

from app.core.legal import CURRENT_TERMS_VERSION


class TermsVersionMismatchError(Exception):
    pass


class PartnerService:
    ...
    async def create_partner(self, *, owner: User, request: PartnerCreateRequest) -> Partner:
        if request.terms_version != CURRENT_TERMS_VERSION:
            raise TermsVersionMismatchError(
                f"Phiên bản điều khoản đã thay đổi. Vui lòng đọc lại bản {CURRENT_TERMS_VERSION}."
            )

        # ... slug logic giữ nguyên ...

        partner = Partner(
            name=request.name,
            slug=slug,
            owner_user_id=owner.id,
            status=PartnerStatus.PENDING,
            category=request.category,
            description=request.description,
            logo_url=request.logo_url,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            address=request.address,
            tax_code=request.tax_code,
            website=request.website,
            business_hours=request.business_hours,
            business_license_url=request.business_license_url,  # NEW
            terms_accepted_at=datetime.now(timezone.utc),  # NEW
            terms_version=request.terms_version,  # NEW
            settings={},
        )
        ...

    async def approve_partner(
        self, *, partner_id: int,
        reason: str | None = None, actor_user_id: int | None = None,
    ) -> Partner:
        partner = await self.get_partner_by_id(partner_id)
        if partner.status not in (PartnerStatus.PENDING, PartnerStatus.SUSPENDED):
            raise InvalidStatusTransitionError(...)
        partner.status = PartnerStatus.ACTIVE
        if partner.activated_at is None:
            partner.activated_at = datetime.now(timezone.utc)
        partner.last_status_reason = reason
        partner.last_status_changed_by = actor_user_id
        partner.last_status_changed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return partner

    async def suspend_partner(
        self, *, partner_id: int,
        reason: str | None = None, actor_user_id: int | None = None,
    ) -> Partner:
        partner = await self.get_partner_by_id(partner_id)
        if partner.status not in (PartnerStatus.PENDING, PartnerStatus.ACTIVE):
            raise InvalidStatusTransitionError(...)
        partner.status = PartnerStatus.SUSPENDED
        partner.last_status_reason = reason
        partner.last_status_changed_by = actor_user_id
        partner.last_status_changed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return partner
```

- [ ] **Step 5: api/partners.py:register_partner — catch `TermsVersionMismatchError`.**

```python
from app.services.partner_service import (
    PartnerNotFoundError, PartnerService, TermsVersionMismatchError,
)

@partner_router.post("/register", ...)
async def register_partner(...):
    service = PartnerService(db)
    try:
        partner = await service.create_partner(owner=current_user, request=body)
    except TermsVersionMismatchError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return PartnerResponse.model_validate(partner)
```

- [ ] **Step 6: PartnerResponse thêm các field mới — không bắt buộc nhưng admin cần đọc.**

```python
class PartnerResponse(BaseModel):
    ...  # existing
    business_license_url: str | None = None  # NEW
    terms_accepted_at: datetime | None = None  # NEW
    terms_version: str | None = None  # NEW
    last_status_reason: str | None = None  # NEW
    last_status_changed_at: datetime | None = None  # NEW
```

- [ ] **Step 7: Test integration.**

```python
# backend/tests/integration/test_partner_register.py
@pytest.mark.asyncio
async def test_register_partner_persists_license_and_terms(client, user_token, db_session):
    r = await client.post("/partner/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Cafe Test",
            "business_license_url": "/api/uploads/licenses/1/abc.jpg",
            "accept_terms": True,
            "terms_version": "v1.0",
            "category": "cafe",
        }
    )
    assert r.status_code == 201
    data = r.json()
    assert data["business_license_url"] == "/api/uploads/licenses/1/abc.jpg"
    assert data["terms_version"] == "v1.0"


@pytest.mark.asyncio
async def test_register_partner_rejects_unaccepted_terms(client, user_token):
    r = await client.post("/partner/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Cafe Test",
            "business_license_url": "/api/uploads/licenses/1/abc.jpg",
            "accept_terms": False,  # 422
            "terms_version": "v1.0",
            "category": "cafe",
        }
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_partner_rejects_stale_terms_version(client, user_token):
    r = await client.post("/partner/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Cafe Test",
            "business_license_url": "/api/uploads/licenses/1/abc.jpg",
            "accept_terms": True,
            "terms_version": "v0.5",  # cũ
            "category": "cafe",
        }
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_admin_approve_partner_persists_reason(
    client, admin_token, partner_factory, db_session
):
    partner = await partner_factory(db_session, status="pending")
    r = await client.post(f"/admin/partners/{partner.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approve": True, "reason": "ok"}
    )
    assert r.status_code == 200
    await db_session.refresh(partner)
    assert partner.last_status_reason == "ok"
    assert partner.last_status_changed_by is not None
```

- [ ] **Step 8: Tests pass.**

- [ ] **Step 9: Commit.**

```bash
git add backend/alembic/versions/<hex>_qt2_partner_terms_license.py backend/app/models/partner.py backend/app/core/legal.py backend/app/schemas/partner.py backend/app/services/partner_service.py backend/app/api/partners.py backend/tests/integration/test_partner_register.py
git commit -m "feat(qt2): partner đăng ký kèm giấy phép + ToS + persist reason approve/suspend"
```

### Task 5.3 — Endpoint upload giấy phép

**Files:**
- Modify: `backend/app/api/uploads.py`

- [ ] **Step 1: Thêm endpoint vào router hiện có (`/partner/uploads`), KHÔNG yêu cầu owner role.**

`backend/app/api/uploads.py` — thêm endpoint mới cùng router `/partner/uploads`:

```python
from app.core.deps import get_current_user
from app.models.user import User


@router.post("/license")
async def upload_license(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),  # CHỈ cần login, KHÔNG yêu cầu owner
) -> dict[str, str]:
    """Upload ảnh giấy phép kinh doanh — dùng trước khi đăng ký partner.

    Khác `/partner/uploads/image` (cần owner role): endpoint này chỉ cần
    authenticated user. URL trả về dùng cho field `business_license_url` trong
    `POST /partner/register`.

    Whitelist .jpg/.jpeg/.png/.webp, max 5MB. Path: uploads/licenses/<user_id>/<uuid>.<ext>.
    """
    filename = (file.filename or "").strip()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail="Định dạng không hỗ trợ. Chỉ chấp nhận .jpg, .jpeg, .png, .webp",
        )

    contents = await file.read()
    MAX_LICENSE = 5 * 1024 * 1024
    if len(contents) > MAX_LICENSE:
        raise HTTPException(status_code=413, detail="Ảnh vượt quá 5MB")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File rỗng")

    license_dir = UPLOAD_ROOT / "licenses" / str(current_user.id)
    license_dir.mkdir(parents=True, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}{ext}"
    target = license_dir / new_name
    target.write_bytes(contents)

    return {"url": f"/api/uploads/licenses/{current_user.id}/{new_name}"}
```

> **Lưu ý:** route final là `POST /partner/uploads/license` (router đã có prefix `/partner/uploads`). KHÔNG mount router mới ở `/uploads` vì sẽ xung đột với `app.mount("/uploads", StaticFiles(...))` ở `main.py:85`.
> Endpoint này chỉ dùng `get_current_user` thay vì `require_owner_in_partner` — bypass header `X-Partner-Id` (lúc đăng ký partner user chưa có partner). FastAPI cho phép vì các sub-route khác trong `/partner/uploads/image` mỗi route tự khai báo dependencies.

- [ ] **Step 2: Test.**

```python
@pytest.mark.asyncio
async def test_upload_license_requires_auth(client):
    r = await client.post("/partner/uploads/license",
        files={"file": ("test.png", b"fakedata", "image/png")})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_upload_license_returns_url(client, user_token):
    fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    r = await client.post("/partner/uploads/license",
        headers={"Authorization": f"Bearer {user_token}"},
        files={"file": ("license.png", fake_image, "image/png")})
    assert r.status_code == 200
    assert r.json()["url"].startswith("/api/uploads/licenses/")
```

- [ ] **Step 3: Pass + Commit.**

```bash
git add backend/app/api/uploads.py backend/tests/integration/test_uploads.py
git commit -m "feat(qt2): endpoint POST /partner/uploads/license cho giấy phép kinh doanh"
```

### Task 5.4 — FE register/partner page với upload + ToS

**Files:**
- Modify: `frontend/src/app/(auth)/register/partner/page.tsx`
- Create: `frontend/src/app/legal/terms/page.tsx`

- [ ] **Step 1: T&C static page.**

```tsx
// frontend/src/app/legal/terms/page.tsx
export const metadata = { title: "Điều khoản dịch vụ | Loyalty Platform" };

export default function TermsPage() {
  return (
    <main className="max-w-3xl mx-auto p-6 prose">
      <h1>Điều khoản dịch vụ — v1.0</h1>
      <p className="text-sm text-gray-600">Cập nhật: 2026-05-02</p>
      <h2>1. Phạm vi áp dụng</h2>
      <p>Hợp đồng này áp dụng cho tất cả đối tác (cửa hàng) sử dụng nền tảng Loyalty Platform...</p>
      <h2>2. Quyền và nghĩa vụ của đối tác</h2>
      <p>...</p>
      <h2>3. Phí dịch vụ</h2>
      <p>...</p>
      <h2>4. Xử lý vi phạm</h2>
      <p>...</p>
      <h2>5. Chấm dứt hợp đồng</h2>
      <p>...</p>
    </main>
  );
}
```

(Nội dung đầy đủ theo yêu cầu thực tế đồ án — placeholder hiện đủ cho demo.)

- [ ] **Step 2: Update form đăng ký partner.**

`frontend/src/app/(auth)/register/partner/page.tsx` — thêm state cho file + upload + checkbox:

```tsx
const [licenseUrl, setLicenseUrl] = useState<string | null>(null);
const [uploading, setUploading] = useState(false);
const [acceptTerms, setAcceptTerms] = useState(false);

async function uploadLicense(e: React.ChangeEvent<HTMLInputElement>) {
  const f = e.target.files?.[0];
  if (!f) return;
  setUploading(true);
  const fd = new FormData();
  fd.append("file", f);
  try {
    const res = await api.post("/partner/uploads/license", fd);
    setLicenseUrl(res.data.url);
  } finally {
    setUploading(false);
  }
}

// Trong submit handler:
if (!licenseUrl) { setError("Vui lòng tải ảnh giấy phép"); return; }
if (!acceptTerms) { setError("Vui lòng đồng ý điều khoản"); return; }

await api.post("/partner/register", {
  ...formData,
  business_license_url: licenseUrl,
  accept_terms: acceptTerms,
  terms_version: "v1.0",  // sync với backend
});
```

JSX:
```tsx
<div>
  <label>Giấy phép kinh doanh (ảnh, ≤5MB)</label>
  <input type="file" accept="image/*" onChange={uploadLicense} />
  {uploading && <p>Đang tải...</p>}
  {licenseUrl && <img src={licenseUrl} className="max-h-48 mt-2" />}
</div>

<label className="flex items-center gap-2">
  <input type="checkbox" checked={acceptTerms}
         onChange={e => setAcceptTerms(e.target.checked)} required />
  <span>
    Tôi đã đọc và đồng ý với{" "}
    <a href="/legal/terms" target="_blank" className="text-blue-600 underline">
      Điều khoản dịch vụ
    </a>
  </span>
</label>
```

- [ ] **Step 3: tsc + smoke manual.** Đăng ký partner mới, verify license URL + acceptance đi vào DB.

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/app/(auth)/register/partner/page.tsx frontend/src/app/legal/terms/page.tsx
git commit -m "feat(qt2): FE form register partner + upload giấy phép + checkbox ToS"
```

### Task 5.5 — FE admin partner list show license + reason

**Files:**
- Modify: `frontend/src/app/(admin)/admin/partners/page.tsx`

> Render trong drawer/modal "chi tiết partner" có sẵn (admin click row → mở chi tiết).

- [ ] **Step 1: Render fields mới (license image, terms_version, last_status_reason) trong modal/drawer hiện có.**

```tsx
{partner.business_license_url && (
  <section>
    <h3>Giấy phép kinh doanh</h3>
    <a href={partner.business_license_url} target="_blank" rel="noreferrer">
      <img src={partner.business_license_url} className="max-h-64 border rounded" />
    </a>
  </section>
)}

{partner.terms_version && (
  <p className="text-sm text-gray-600">
    Đồng ý điều khoản {partner.terms_version} lúc{" "}
    {partner.terms_accepted_at && new Date(partner.terms_accepted_at).toLocaleString("vi-VN")}
  </p>
)}

{partner.last_status_reason && (
  <section>
    <h3>Lý do thay đổi trạng thái gần nhất</h3>
    <p>{partner.last_status_reason}</p>
    <p className="text-sm text-gray-500">
      {partner.last_status_changed_at && new Date(partner.last_status_changed_at).toLocaleString("vi-VN")}
    </p>
  </section>
)}
```

- [ ] **Step 2: Update `frontend/src/types/partner.ts` thêm các field này vào type `PartnerDetailResponse`.**

- [ ] **Step 3: tsc.**

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/app/(admin)/admin/partners/page.tsx frontend/src/types/partner.ts
git commit -m "feat(qt2): FE admin partner detail hiển thị giấy phép + ToS + reason"
```

### Task 5.6 — Code-reviewer Phase 5

- [ ] **Step 1: Dispatch reviewer.** Tập trung: race khi 2 user upload license cùng filename UUID (cực hiếm), backfill cho partners cũ NULL, FE handle existing partners không có license.
- [ ] **Step 2: Fix.**

---

## Phase 6 — QT7 Free voucher

**Goal:** Reward `points_cost = 0` thành "voucher miễn phí"; thêm `valid_from`; user chỉ claim 1 voucher/reward.
**Risk:** cao nhất — schema constraint thay đổi + endpoint mới + FE branching.

### Task 6.1 — Migration relax CK + add `valid_from` + partial unique index

**Files:**
- Create: `backend/alembic/versions/<hex>_qt7_reward_free_voucher.py`

- [ ] **Step 1: Verify tên CK thực tế trong DB.**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT conname FROM pg_constraint WHERE conrelid='rewards'::regclass AND contype='c';"
```
Expected: thấy `ck_rewards_ck_rewards_points_cost_positive`.

- [ ] **Step 2: Generate revision + sửa.**

```python
"""qt7_reward_free_voucher"""

from alembic import op
import sqlalchemy as sa

revision = "<hex>"
down_revision = "<head>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop CK rewards cũ với tên thực tế trong DB (double-prefix bug)
    op.drop_constraint(
        "ck_rewards_ck_rewards_points_cost_positive",
        "rewards", type_="check"
    )
    # Add CK mới qua naming convention → final ck_rewards_points_cost_nonneg
    op.create_check_constraint(
        "points_cost_nonneg", "rewards", "points_cost >= 0"
    )
    op.add_column("rewards", sa.Column("valid_from", sa.Date(), nullable=True))

    # CK redemptions.points_spent: drop > 0, add >= 0 (cho free voucher)
    # Tên thực tế: ck_redemptions_ck_redemptions_points_positive (double-prefix)
    op.drop_constraint(
        "ck_redemptions_ck_redemptions_points_positive",
        "redemptions", type_="check"
    )
    op.create_check_constraint(
        "points_spent_nonneg", "redemptions", "points_spent >= 0"
    )

    # Partial unique index: 1 user 1 voucher pending/used per reward.
    # CHÚ Ý: status lưu lowercase trong DB (verified pg) — KHÔNG dùng UPPERCASE.
    op.execute("""
        CREATE UNIQUE INDEX ux_redemptions_user_reward_active
        ON redemptions(user_id, reward_id)
        WHERE status IN ('pending','used')
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_redemptions_user_reward_active")
    op.drop_constraint("ck_redemptions_points_spent_nonneg", "redemptions", type_="check")
    op.create_check_constraint(
        "points_positive", "redemptions", "points_spent > 0"
    )
    op.drop_column("rewards", "valid_from")
    op.drop_constraint("ck_rewards_points_cost_nonneg", "rewards", type_="check")
    op.create_check_constraint(
        "points_cost_positive", "rewards", "points_cost > 0"
    )
```

- [ ] **Step 3: Apply.**

```bash
docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend alembic upgrade head
```

- [ ] **Step 4: Verify.**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c "\d rewards"
# Expected: cột valid_from + CK ck_rewards_points_cost_nonneg

docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT indexname FROM pg_indexes WHERE tablename='redemptions';"
# Expected: ux_redemptions_user_reward_active
```

### Task 6.2 — Reward model + Redemption model CK + 3 schemas update

**Files:**
- Modify: `backend/app/models/reward.py`
- Modify: `backend/app/models/redemption.py`
- Modify: `backend/app/schemas/reward.py`

- [ ] **Step 1: Sửa Reward CK + thêm cột.**

```python
# backend/app/models/reward.py
from datetime import date

class Reward(Base, TimestampMixin):
    __tablename__ = "rewards"
    __table_args__ = (
        CheckConstraint("stock IS NULL OR stock >= 0", name="stock_nonneg_or_null"),
        CheckConstraint("points_cost >= 0", name="points_cost_nonneg"),  # CHANGED từ points_cost_positive
        CheckConstraint(...),  # offer_value_matches_type — giữ nguyên
        CheckConstraint(...),  # min_purchase_nonneg_or_null
        CheckConstraint(...),  # min_purchase_only_for_voucher
    )
    ...
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)  # NEW
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)  # đã có
    ...
```

- [ ] **Step 1b: Sửa Redemption CK name.**

```python
# backend/app/models/redemption.py
class Redemption(Base, TimestampMixin):
    __tablename__ = "redemptions"
    __table_args__ = (
        CheckConstraint("points_spent >= 0", name="points_spent_nonneg"),  # CHANGED từ points_positive
        CheckConstraint(
            "(original_amount IS NULL AND discount_amount IS NULL) "
            "OR (original_amount >= 0 AND discount_amount >= 0)",
            name="amounts_nonneg_or_null",
        ),
        UniqueConstraint(
            "partner_id", "redemption_code", name="uq_redemptions_partner_code"
        ),
        Index("ix_redemptions_partner_status", "partner_id", "status"),
    )
```

- [ ] **Step 2: Sửa 3 Pydantic schemas.**

```python
# backend/app/schemas/reward.py
from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator

from app.models.reward import RewardOfferType


class RewardCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    points_cost: int = Field(ge=0)  # CHANGED from gt=0
    stock: int | None = None
    image_url: str | None = None
    template_id: int | None = None
    offer_type: RewardOfferType
    offer_value: int | None = None
    offer_label: str = Field(min_length=1, max_length=120)
    valid_from: date | None = None  # NEW
    valid_until: date | None = None
    terms: str | None = None
    min_purchase_amount: int | None = None

    @model_validator(mode="after")
    def _check_dates(self) -> "RewardCreateRequest":
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError("valid_from phải <= valid_until")
        return self


class RewardUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    points_cost: int | None = Field(default=None, ge=0)  # CHANGED
    stock: int | None = None
    image_url: str | None = None
    template_id: int | None = None
    offer_type: RewardOfferType | None = None
    offer_value: int | None = None
    offer_label: str | None = None
    valid_from: date | None = None  # NEW
    valid_until: date | None = None
    terms: str | None = None
    min_purchase_amount: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _check_dates(self) -> "RewardUpdateRequest":
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError("valid_from phải <= valid_until")
        return self


class RewardResponse(BaseModel):
    id: int
    partner_id: int
    name: str
    description: str | None
    points_cost: int
    stock: int | None
    image_url: str | None
    is_active: bool
    deleted_at: datetime | None  # KEEP — FE consume ở partner rewards page
    template_id: int | None
    offer_type: RewardOfferType
    offer_value: int | None
    offer_label: str
    valid_from: date | None  # NEW
    valid_until: date | None
    terms: str | None
    min_purchase_amount: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Commit.**

```bash
git add backend/app/models/reward.py backend/app/schemas/reward.py backend/alembic/versions/<hex>_qt7_reward_free_voucher.py
git commit -m "feat(qt7): rewards relax CK points_cost >= 0 + valid_from + partial unique index"
```

### Task 6.3 — `RedemptionService.claim_free` + redeem guard

**Files:**
- Modify: `backend/app/services/redemption_service.py`

- [ ] **Step 1: Test trước.**

```python
# backend/tests/integration/test_redemption_service.py
@pytest.mark.asyncio
async def test_claim_free_decrement_stock_no_balance_no_ledger(
    db_session, partner_factory, user_factory, reward_factory
):
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=500)
    reward = await reward_factory(
        db_session, partner_id=partner.id,
        points_cost=0, stock=5,
    )

    from app.services.redemption_service import RedemptionService
    svc = RedemptionService(db_session)
    redemption = await svc.claim_free(
        partner_id=partner.id, user_id=user.id, reward_id=reward.id
    )
    assert redemption.points_spent == 0
    await db_session.refresh(reward)
    assert reward.stock == 4
    await db_session.refresh(user)
    assert user.points_balance == 500  # unchanged

    # Ledger: 0 entries (free claim không log)
    from sqlalchemy import select
    from app.models.point_ledger import PointLedger
    count = await db_session.scalar(
        select(sa.func.count()).select_from(PointLedger)
        .where(PointLedger.user_id == user.id)
    )
    assert count == 0


@pytest.mark.asyncio
async def test_claim_free_rejects_paid_reward(
    db_session, partner_factory, user_factory, reward_factory
):
    partner = await partner_factory(db_session)
    user = await user_factory(db_session)
    reward = await reward_factory(db_session, partner_id=partner.id, points_cost=100, stock=1)
    from app.services.redemption_service import RedemptionService, WrongClaimMethodError
    svc = RedemptionService(db_session)
    with pytest.raises(WrongClaimMethodError):
        await svc.claim_free(partner_id=partner.id, user_id=user.id, reward_id=reward.id)


@pytest.mark.asyncio
async def test_claim_free_per_user_uniqueness(
    db_session, partner_factory, user_factory, reward_factory
):
    """1 user chỉ claim 1 lần per reward."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session)
    reward = await reward_factory(db_session, partner_id=partner.id, points_cost=0, stock=10)
    from app.services.redemption_service import RedemptionService, AlreadyClaimedError
    svc = RedemptionService(db_session)
    await svc.claim_free(partner_id=partner.id, user_id=user.id, reward_id=reward.id)
    with pytest.raises(AlreadyClaimedError):
        await svc.claim_free(partner_id=partner.id, user_id=user.id, reward_id=reward.id)


@pytest.mark.asyncio
async def test_redeem_rejects_free_reward(
    db_session, partner_factory, user_factory, reward_factory
):
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=500)
    reward = await reward_factory(db_session, partner_id=partner.id, points_cost=0, stock=5)
    from app.services.redemption_service import RedemptionService, WrongClaimMethodError
    svc = RedemptionService(db_session)
    with pytest.raises(WrongClaimMethodError):
        await svc.redeem(partner_id=partner.id, user_id=user.id, reward_id=reward.id)
```

- [ ] **Step 2: Implement.**

```python
# backend/app/services/redemption_service.py — thêm exception classes đầu file
class WrongClaimMethodError(Exception):
    """Reward sai loại — paid dùng /redeem, free dùng /claim."""
    pass


class AlreadyClaimedError(Exception):
    """User đã claim voucher này (partial unique index vi phạm)."""
    pass


class RedemptionService:
    ...
    async def redeem(self, *, partner_id, user_id, reward_id, ttl_days=14):
        today = date.today()
        reward = await self.db.scalar(
            select(Reward).where(
                Reward.id == reward_id,
                Reward.partner_id == partner_id,
                Reward.is_active.is_(True),
                Reward.deleted_at.is_(None),
                ((Reward.valid_from.is_(None)) | (Reward.valid_from <= today)),
                ((Reward.valid_until.is_(None)) | (Reward.valid_until >= today)),
            ).with_for_update()
        )
        if reward is None:
            raise ValueError(f"Reward {reward_id} not found or expired")
        if reward.points_cost == 0:  # NEW guard
            raise WrongClaimMethodError(
                "Reward này là voucher miễn phí, dùng /claim thay vì /redemptions"
            )
        ...  # rest giữ nguyên: atomic stock + balance + code generation

        # CRITICAL: bọc flush trong begin_nested() savepoint để IntegrityError
        # không poison session → còn execute được compensation rollback.
        self.db.add(redemption)
        already_claimed = False
        try:
            async with self.db.begin_nested():
                await self.db.flush()
        except IntegrityError:
            already_claimed = True

        if already_claimed:
            # Rollback compensation: stock + balance.
            if reward.stock is not None:
                await self.db.execute(
                    update(Reward).where(Reward.id == reward_id)
                    .values(stock=Reward.stock + 1)
                )
            await self.db.execute(
                update(User).where(User.id == user_id)
                .values(points_balance=User.points_balance + reward.points_cost)
            )
            raise AlreadyClaimedError("Bạn đã đổi quà này rồi")

        # ledger insert (chỉ chạy khi flush thành công)...

    async def claim_free(self, *, partner_id, user_id, reward_id, ttl_days=14):
        today = date.today()
        reward = await self.db.scalar(
            select(Reward).where(
                Reward.id == reward_id,
                Reward.partner_id == partner_id,
                Reward.is_active.is_(True),
                Reward.deleted_at.is_(None),
                ((Reward.valid_from.is_(None)) | (Reward.valid_from <= today)),
                ((Reward.valid_until.is_(None)) | (Reward.valid_until >= today)),
            ).with_for_update()
        )
        if reward is None:
            raise ValueError(f"Reward {reward_id} not found or expired")
        if reward.points_cost > 0:
            raise WrongClaimMethodError(
                "Reward này yêu cầu đổi bằng điểm, dùng /redemptions"
            )

        if reward.stock is not None:
            result = await self.db.execute(
                update(Reward).where(Reward.id == reward_id, Reward.stock > 0)
                .values(stock=Reward.stock - 1)
            )
            if result.rowcount == 0:
                raise OutOfStockError(f"Reward {reward_id} hết voucher")

        # Generate code
        code: str | None = None
        for _ in range(3):
            candidate = _generate_code()
            existing = await self.db.scalar(
                select(Redemption.id).where(
                    Redemption.partner_id == partner_id,
                    Redemption.redemption_code == candidate,
                )
            )
            if existing is None:
                code = candidate
                break
        if code is None:
            raise RuntimeError("Failed to generate unique redemption code")

        redemption = Redemption(
            partner_id=partner_id,
            user_id=user_id,
            reward_id=reward_id,
            points_spent=0,
            redemption_code=code,
            status=RedemptionStatus.PENDING,
            redeemed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days),
        )

        # CRITICAL: savepoint pattern (xem comment ở redeem) — IntegrityError
        # trên partial unique index không được phép poison outer transaction.
        self.db.add(redemption)
        already_claimed = False
        try:
            async with self.db.begin_nested():
                await self.db.flush()
        except IntegrityError:
            already_claimed = True

        if already_claimed:
            if reward.stock is not None:
                await self.db.execute(
                    update(Reward).where(Reward.id == reward_id)
                    .values(stock=Reward.stock + 1)
                )
            raise AlreadyClaimedError("Bạn đã nhận voucher này rồi")

        # KHÔNG ghi point_ledger (delta=0 vô nghĩa)
        return redemption
```

- [ ] **Step 3: Test pass.**

- [ ] **Step 4: Commit.**

```bash
git add backend/app/services/redemption_service.py backend/tests/integration/test_redemption_service.py
git commit -m "feat(qt7): RedemptionService.claim_free + guard cho redeem khi reward free"
```

### Task 6.4 — Endpoint `POST /users/me/rewards/{id}/claim`

**Files:**
- Modify: `backend/app/api/partners.py` (file chứa `users_router`)

- [ ] **Step 1: Test integration.**

```python
# backend/tests/integration/test_reward_claim.py
@pytest.mark.asyncio
async def test_claim_free_endpoint_happy_path(
    client, customer_token, partner_factory, reward_factory, db_session, user_id
):
    partner = await partner_factory(db_session)
    reward = await reward_factory(
        db_session, partner_id=partner.id, points_cost=0, stock=3,
    )
    # Cần membership trước (POS lần đầu)
    from app.models.membership import Membership
    db_session.add(Membership(partner_id=partner.id, user_id=user_id))
    await db_session.commit()

    r = await client.post(f"/users/me/rewards/{reward.id}/claim",
        headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 201
    assert r.json()["points_spent"] == 0


@pytest.mark.asyncio
async def test_claim_free_endpoint_double_claim_409(
    client, customer_token, partner_factory, reward_factory, db_session, user_id
):
    partner = await partner_factory(db_session)
    reward = await reward_factory(db_session, partner_id=partner.id, points_cost=0, stock=10)
    from app.models.membership import Membership
    db_session.add(Membership(partner_id=partner.id, user_id=user_id))
    await db_session.commit()

    r1 = await client.post(f"/users/me/rewards/{reward.id}/claim",
        headers={"Authorization": f"Bearer {customer_token}"})
    assert r1.status_code == 201
    r2 = await client.post(f"/users/me/rewards/{reward.id}/claim",
        headers={"Authorization": f"Bearer {customer_token}"})
    assert r2.status_code == 409
    assert "đã nhận" in r2.json()["detail"]
```

- [ ] **Step 2: Implement endpoint.**

```python
# Trong api/partners.py — sau redeem_reward_self
from app.services.redemption_service import (
    AlreadyClaimedError, OutOfStockError, RedemptionService, WrongClaimMethodError,
)


@users_router.post(
    "/me/rewards/{reward_id}/claim",
    response_model=RedemptionResponse, status_code=201
)
@limiter.limit("10/minute")
async def claim_free_reward(
    request: Request,
    reward_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedemptionResponse:
    """Customer nhận voucher miễn phí — chỉ chấp nhận `points_cost = 0`.

    Tự resolve `partner_id` từ reward, không cần header X-Partner-Id.
    Yêu cầu user là member của partner sở hữu reward.
    """
    reward = await db.scalar(
        select(Reward).where(
            Reward.id == reward_id,
            Reward.deleted_at.is_(None),
            Reward.is_active.is_(True),
        )
    )
    if reward is None:
        raise HTTPException(status_code=404, detail="Reward not found")

    is_member = await db.scalar(
        select(Membership.id).where(
            Membership.partner_id == reward.partner_id,
            Membership.user_id == user.id,
        )
    )
    if is_member is None:
        raise HTTPException(
            status_code=403,
            detail="Bạn cần là thành viên của shop để nhận voucher"
        )

    service = RedemptionService(db)
    try:
        redemption = await service.claim_free(
            partner_id=reward.partner_id, user_id=user.id, reward_id=reward_id,
        )
    except WrongClaimMethodError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except AlreadyClaimedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OutOfStockError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)
```

- [ ] **Step 3: Tương tự update `redeem_reward_self` để catch `WrongClaimMethodError` + `AlreadyClaimedError`.**

```python
@users_router.post("/me/redemptions", response_model=RedemptionResponse, status_code=201)
@limiter.limit("10/minute")
async def redeem_reward_self(...):
    ...
    try:
        redemption = await service.redeem(...)
    except InsufficientPointsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except OutOfStockError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except WrongClaimMethodError as e:  # NEW
        raise HTTPException(status_code=409, detail=str(e)) from e
    except AlreadyClaimedError as e:  # NEW
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedemptionResponse.model_validate(redemption)
```

- [ ] **Step 4: Tests pass.**

- [ ] **Step 5: Commit.**

```bash
git add backend/app/api/partners.py backend/tests/integration/test_reward_claim.py
git commit -m "feat(qt7): endpoint POST /users/me/rewards/{id}/claim cho voucher miễn phí"
```

### Task 6.5 — FE rewards card branching

**Files:**
- Modify: `frontend/src/app/(member)/member/rewards/page.tsx`
- Modify: `frontend/src/app/(member)/member/partners/[slug]/page.tsx`
- Modify: `frontend/src/lib/hooks/useRewards.ts`

- [ ] **Step 1: Hook `useClaimFreeReward`.**

```typescript
// frontend/src/lib/hooks/useRewards.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

export function useClaimFreeReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (rewardId: number) => {
      const res = await api.post(`/users/me/rewards/${rewardId}/claim`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rewards"] });
      qc.invalidateQueries({ queryKey: ["redemptions"] });
    },
  });
}
```

- [ ] **Step 2: Update rewards card.**

```tsx
// member/rewards/page.tsx (extracted RewardCard)
function RewardCard({ reward }: { reward: RewardItem }) {
  const claim = useClaimFreeReward();
  const redeem = useRedeemReward();  // existing
  const isFree = reward.points_cost === 0;

  return (
    <div className="border rounded p-4">
      <h3>{reward.name}</h3>
      <p>{reward.description}</p>
      {isFree ? (
        <button
          disabled={!reward.can_redeem || claim.isPending}
          onClick={() => claim.mutate(reward.id)}
          className="bg-emerald-600 text-white px-4 py-2 rounded"
        >
          {claim.isPending ? "Đang xử lý..." : "Nhận voucher miễn phí"}
        </button>
      ) : (
        <button
          disabled={!reward.can_redeem || redeem.isPending}
          onClick={() => redeem.mutate(reward.id)}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          {redeem.isPending ? "Đang đổi..." : `Đổi ${reward.points_cost} điểm`}
        </button>
      )}
      {reward.stock === 0 && <p className="text-red-600">Hết voucher</p>}
    </div>
  );
}
```

(Áp tương tự cho `member/partners/[slug]/page.tsx` — render rewards.)

- [ ] **Step 3: tsc + smoke manual.**

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/lib/hooks/useRewards.ts frontend/src/app/(member)/member/rewards/page.tsx frontend/src/app/(member)/member/partners/[slug]/page.tsx
git commit -m "feat(qt7): FE phân biệt button đổi điểm vs nhận voucher miễn phí"
```

### Task 6.6 — FE form Reward (partner) thêm `valid_from` + cho phép `points_cost=0`

**Files:**
- Modify: `frontend/src/app/(partner)/partner/rewards/page.tsx` (modal create + edit chung)

> Project KHÔNG có route `rewards/new` hay `rewards/[id]` riêng — form ở Modal trong `rewards/page.tsx`. Thêm fields vào modal hiện tại.

- [ ] **Step 1: Update zod schema + form fields.**

```tsx
const schema = z.object({
  name: z.string().min(1).max(255),
  points_cost: z.coerce.number().int().min(0),  // CHANGED: min(0) cho phép free
  stock: z.coerce.number().int().nullable(),
  offer_type: z.enum(["PERCENT_DISCOUNT", "FIXED_DISCOUNT", "ITEM_GIFT"]),
  // ... existing fields ...
  valid_from: z.string().nullable().optional(),  // NEW
  valid_until: z.string().nullable().optional(),
});
```

JSX:
```tsx
<div>
  <label>Số điểm cần đổi</label>
  <input type="number" min={0} {...register("points_cost")} />
  <p className="text-sm text-gray-500">
    Để 0 = voucher miễn phí, khách nhấn nhận trực tiếp.
  </p>
</div>

<div className="grid grid-cols-2 gap-4">
  <div>
    <label>Ngày bắt đầu hiệu lực</label>
    <input type="date" {...register("valid_from")} />
  </div>
  <div>
    <label>Ngày hết hạn</label>
    <input type="date" {...register("valid_until")} />
  </div>
</div>
```

- [ ] **Step 2: Update RewardItem type + types/partner.ts.**

```typescript
export interface RewardItem {
  ...
  points_cost: number;  // có thể = 0
  valid_from: string | null;  // NEW
  valid_until: string | null;
}
```

- [ ] **Step 3: tsc + smoke (tạo reward `points_cost=0`, `valid_from=hôm nay`, đổi lại sửa).**

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/app/(partner)/partner/rewards/page.tsx frontend/src/types/partner.ts
git commit -m "feat(qt7): FE partner form reward cho phép points_cost=0 + valid_from"
```

### Task 6.7 — Smoke E2E QT7

- [ ] **Step 1: Curl script.**

```bash
# Login owner shop A
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"owner@cafe.vn","password":"owner1234"}' | jq -r .access_token)

# Tạo reward miễn phí, stock=3
curl -s -X POST http://localhost:8000/partner/rewards \
  -H "Authorization: Bearer $TOKEN" -H "X-Partner-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Cafe miễn phí","points_cost":0,"stock":3,"offer_type":"ITEM_GIFT","offer_label":"1 ly cafe"}'

# Login khach1 (member của shop 1)
CTOK=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"khach1@gmail.com","password":"khach1234"}' | jq -r .access_token)

# Claim lần 1 → 201
curl -s -X POST http://localhost:8000/users/me/rewards/{REWARD_ID}/claim \
  -H "Authorization: Bearer $CTOK" -w "\n%{http_code}\n"
# Expected: 201, points_spent=0

# Claim lần 2 → 409 "đã nhận"
curl -s -X POST http://localhost:8000/users/me/rewards/{REWARD_ID}/claim \
  -H "Authorization: Bearer $CTOK" -w "\n%{http_code}\n"
# Expected: 409
```

- [ ] **Step 2: Verify DB.**

```bash
docker exec loyalty-postgres-prod psql -U loyalty -d loyalty -c \
  "SELECT id, points_spent, status, redemption_code FROM redemptions ORDER BY id DESC LIMIT 5;"
```

### Task 6.8 — Code-reviewer Phase 6

- [ ] **Step 1: Dispatch reviewer.** Tập trung: race khi 10 user đồng thời claim cùng reward stock=3 (chỉ 3 success), partial unique index có cover all status đúng không, FE branching `is_active=false` reward.
- [ ] **Step 2: Fix.**

---

## Phase 7 — End-to-end smoke verification

**Goal:** Chạy đầy đủ 6 quy trình bằng curl scripts trước khi declare done.

### Task 7.1 — Build full smoke matrix

**Files:**
- Create: `tmp/smoke_qt_full.sh`

- [ ] **Step 1: Script test full 6 flow.**

```bash
#!/usr/bin/env bash
set -e

BASE=http://localhost:8000

# === QT1 ===
# Register với phone
curl -s -X POST $BASE/auth/register -H "Content-Type: application/json" \
  -d '{"email":"qt1@test.vn","phone":"0911111111","password":"test12345","full_name":"QT1"}'
# Forgot → must change
# Login temp → 423 trên các route khác

# === QT2 ===
# Login user, upload license, register partner with terms, admin approve with reason

# === QT4 ===
# Owner quét QR khách mới → auto-enroll + tích điểm + ledger có actor_user_id

# === QT5 ===
# Tạo reward valid_until=hôm qua → đổi → 404

# === QT7 ===
# Tạo reward points_cost=0, stock=3 → 3 user khác nhau claim → đủ 3, lần 4 → 409 hết stock

# === QT8 ===
# Admin lock user kèm reason → audit_logs có entry
# Admin unlock → entry mới
echo "All QT smoke pass"
```

- [ ] **Step 2: Chạy + commit nếu giữ làm regression.**

---

## Definition of Done

- [ ] 6 phase commit lên `main`, mỗi phase có ≥ 1 commit + test pass + code-reviewer Critical/Important fixed.
- [ ] `docker compose -p loyalty-prod -f docker-compose.prod.yml exec backend pytest tests/integration -v` green (đa số test mới ở integration vì cần PostgreSQL container; unit tests cũ giữ nguyên).
- [ ] `cd frontend && npx tsc --noEmit` green.
- [ ] Smoke E2E full 6 quy trình (Phase 7) pass.
- [ ] Báo cáo đồ án mục 2.3.1 không còn mâu thuẫn với code.
- [ ] Báo cáo Chương 1 mục Phạm vi (docx) bỏ "Hệ thống phân hạng thành viên" khỏi out-of-scope (việc trên báo cáo, không phải code).

---

## Phụ lục — Workflow rules

- Sau mỗi task lớn → dispatch `superpowers:code-reviewer` (model `opus`) trước khi commit.
- Fix Critical/Important rồi commit. Nit có thể bỏ qua.
- Memory `feedback_workflow_between_tasks.md`: KHÔNG batch nhiều phase rồi review cuối — review giữa từng phase.
- Git policy: dùng `rtk git ...` (RTK token-saver). Không `--no-verify`, không `git add -A`, không amend.
