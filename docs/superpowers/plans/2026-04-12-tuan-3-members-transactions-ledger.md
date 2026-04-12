# Tuần 3 — Members, Transactions Thủ công, Point Ledger, Auto Upgrade Tier & /pos UI Skeleton

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement nghiệp vụ tích điểm cốt lõi: tạo membership cho khách qua SĐT (Luồng B Phần 1), tạo giao dịch tích điểm thủ công (method `manual`), ghi append-only vào `point_ledger` với DB trigger enforce, auto upgrade tier sau mỗi transaction (Luồng G), reconcile invariant `SUM(ledger.delta) = membership.points_balance`. Frontend `/pos` skeleton tablet-optimized cho nhân viên nhập giao dịch.

**Architecture:**
- **Members module:** upsert atomic user theo phone (E.164) + upsert membership cho `(tenant_id, user_id)` — handle 3 case (user mới hoàn toàn, shadow user của tenant khác, user thường đã có app)
- **Point ledger:** bảng append-only, PostgreSQL trigger chặn UPDATE/DELETE ở DB level (defense-in-depth)
- **Race condition:** `SELECT FOR UPDATE` trên `memberships` trước update balance, lock ordering rule (memberships luôn lock đầu tiên)
- **Reconcile:** test invariant chạy sau mọi kịch bản test + endpoint admin `POST /admin/reconcile/{membership_id}`
- **Tier auto-upgrade:** sau commit transaction, gọi `tier_service.recompute_tier()` — silent re-bind nếu tier config thay đổi (Luồng K cũ — tuần 5 mới hoàn thiện)

**Tech Stack additions:**
- `phonenumbers>=8.13.0` — chuẩn hóa số điện thoại sang E.164 format

**Cuối tuần phải có:**
- Nhân viên tại quầy nhập SĐT + số tiền → backend tạo user shadow nếu chưa có + tạo membership + tích điểm + ghi ledger + upgrade tier nếu đủ điểm
- Endpoint `POST /merchant/transactions` chạy được với 3 case khách (mới / shadow tenant khác / user thường)
- Test ledger invariant pass sau mọi scenario
- Endpoint `POST /admin/reconcile/{membership_id}` hoạt động
- Frontend `/pos` skeleton + form nhập giao dịch thủ công chạy được
- Trang `/merchant/members` list khách + detail + history giao dịch + ledger
- ~30 new tests pass (tổng tích lũy ~95)
- CI xanh

**Acceptance criteria:**
- Seed v1 từ tuần 2 chạy → login owner1 → vào `/pos` → nhập SĐT mới `0912345678` + 50000 VND → backend tạo user shadow + membership + transaction + 50 điểm (rule 1.00/1000 VND) → tier Bronze
- Lặp lại cho cùng SĐT với 500000 VND → tổng 550 điểm → tier upgrade Silver (min=500) → notification "Lên hạng Silver"
- Owner vào `/merchant/members` → thấy khách vừa tạo + history 2 giao dịch + ledger entries khớp balance
- Test cross-tenant: nhân viên tenant A tạo giao dịch với header X-Tenant-Id của tenant B → 403
- Test reconcile: chạy `POST /admin/reconcile/{membership_id}` cho mọi membership trong seed → tất cả pass (sum delta = balance)
- DB trigger chặn UPDATE/DELETE point_ledger: thử `UPDATE point_ledger SET delta=0` trong psql → raise exception
- `cd backend && pytest -v` → ~95 tests pass
- CI xanh

---

## Tổng quan các phase

| Phase | Tasks | Mô tả | LOC backend | LOC frontend |
|---|---|---|---|---|
| 1 | 1-3 | Phone E.164 utility + Members upsert service (Luồng B Phần 1) | ~200 | — |
| 2 | 4-7 | Transactions model + Point ledger model + DB trigger migration | ~250 | — |
| 3 | 8-11 | LedgerService TDD (append + reconcile + invariant test) | ~300 | — |
| 4 | 12-16 | TransactionService TDD method (a) manual + race condition handling | ~400 | — |
| 5 | 17-19 | Tier auto-upgrade (Luồng G) + integration với TransactionService | ~250 | — |
| 6 | 20-23 | API endpoints `/merchant/transactions` + `/merchant/members` | ~350 | — |
| 7 | 24-26 | Admin reconcile endpoint + cross-tenant tests | ~250 | — |
| 8 | 27-29 | Seed v2 (thêm 20 khách + 100 transactions) | ~200 | — |
| 9 | 30-33 | Frontend `/pos` layout + auth guard staff + tenant switcher | — | ~350 |
| 10 | 34-37 | Frontend `/pos/transactions` form (nhập SĐT + amount) | — | ~450 |
| 11 | 38-40 | Frontend `/merchant/members` list + detail + history | — | ~500 |
| 12 | 41-42 | Frontend ledger viewer trong member detail | — | ~250 |
| 13 | 43-44 | Smoke test E2E full + Run all tests + commit |  — | — |

**Total:** 44 tasks · ~2200 LOC backend · ~1550 LOC frontend · ~30 new tests

---

## File Structure (sẽ tạo / sửa trong tuần 3)

```
D:/DoAn/
├── backend/
│   ├── alembic/versions/
│   │   ├── 006_create_memberships.py              # NEW (★ FIX C1 final review)
│   │   ├── 007_create_transactions.py             # NEW
│   │   ├── 008_create_point_ledger.py             # NEW (kèm trigger append-only)
│   ├── app/
│   │   ├── core/
│   │   │   └── phone.py                           # NEW (E.164 normalize)
│   │   ├── models/
│   │   │   ├── membership.py                      # NEW (★ FIX C1 final review)
│   │   │   ├── transaction.py                     # NEW
│   │   │   └── point_ledger.py                    # NEW
│   │   ├── schemas/
│   │   │   ├── member.py                          # NEW
│   │   │   ├── transaction.py                     # NEW
│   │   │   └── ledger.py                          # NEW
│   │   ├── services/
│   │   │   ├── member_service.py                  # NEW (Luồng B Phần 1)
│   │   │   ├── transaction_service.py             # NEW
│   │   │   ├── ledger_service.py                  # NEW
│   │   │   └── tier_service.py                    # MODIFY (add recompute_tier)
│   │   └── api/
│   │       ├── members.py                         # NEW
│   │       ├── transactions.py                    # NEW
│   │       └── admin.py                           # MODIFY (add reconcile endpoint)
│   ├── scripts/
│   │   └── seed.py                                # MODIFY (seed v2 — thêm 20 khách + 100 txn)
│   ├── tests/
│   │   ├── unit/
│   │   │   └── test_phone.py                      # NEW
│   │   └── integration/
│   │       ├── test_member_service.py             # NEW
│   │       ├── test_transaction_service.py        # NEW
│   │       ├── test_ledger_service.py             # NEW
│   │       ├── test_ledger_invariant.py           # NEW
│   │       ├── test_transactions_api.py           # NEW
│   │       ├── test_members_api.py                # NEW
│   │       └── test_tenant_isolation.py           # MODIFY (add txn isolation)
│   └── pyproject.toml                             # MODIFY (add phonenumbers)
└── frontend/
    └── src/
        ├── lib/
        │   └── api.ts                             # MODIFY (add transactions/members API)
        ├── types/
        │   ├── transaction.ts                     # NEW
        │   ├── member.ts                          # NEW
        │   └── ledger.ts                          # NEW
        └── app/
            ├── pos/
            │   ├── layout.tsx                     # NEW
            │   ├── page.tsx                       # NEW (dashboard)
            │   └── transactions/
            │       ├── page.tsx                   # NEW (form nhập)
            │       └── new/page.tsx               # NEW
            └── merchant/
                └── members/
                    ├── page.tsx                   # NEW (list)
                    └── [id]/page.tsx              # NEW (detail + history)
```

---

## PHASE 1 — Phone E.164 + Members Service

### Task 1: Cài `phonenumbers` + tạo `app/core/phone.py`

**Files:**
- Modify: `D:/DoAn/backend/pyproject.toml`
- Create: `D:/DoAn/backend/app/core/phone.py`
- Create: `D:/DoAn/backend/tests/unit/test_phone.py`

- [ ] **Step 1: Thêm `phonenumbers>=8.13.0` vào `pyproject.toml`** dependencies

```toml
"phonenumbers>=8.13.0",
```

```bash
cd D:/DoAn/backend
pip install -e ".[dev]"
```

- [ ] **Step 2: Failing tests `tests/unit/test_phone.py`**

```python
import pytest
from app.core.phone import InvalidPhoneError, normalize_phone


def test_normalize_vn_local_to_e164():
    assert normalize_phone("0912345678") == "+84912345678"


def test_normalize_vn_with_country_code():
    assert normalize_phone("84912345678") == "+84912345678"


def test_normalize_already_e164():
    assert normalize_phone("+84912345678") == "+84912345678"


def test_normalize_strips_spaces_and_dashes():
    assert normalize_phone("091 234 5678") == "+84912345678"
    assert normalize_phone("091-234-5678") == "+84912345678"


def test_normalize_invalid_raises():
    with pytest.raises(InvalidPhoneError):
        normalize_phone("not-a-phone")


def test_normalize_too_short_raises():
    with pytest.raises(InvalidPhoneError):
        normalize_phone("123")


def test_normalize_empty_raises():
    with pytest.raises(InvalidPhoneError):
        normalize_phone("")
```

- [ ] **Step 3: Run → FAIL**

```bash
pytest tests/unit/test_phone.py -v
```

- [ ] **Step 4: Implement `app/core/phone.py`**

```python
import phonenumbers
from phonenumbers import NumberParseException


class InvalidPhoneError(ValueError):
    pass


def normalize_phone(raw: str, default_region: str = "VN") -> str:
    """Chuẩn hóa số điện thoại sang E.164 format (vd +84912345678).

    Args:
        raw: Số điện thoại bất kỳ format
        default_region: Quốc gia mặc định nếu không có country code (default VN)

    Returns:
        E.164 string

    Raises:
        InvalidPhoneError: Nếu số không hợp lệ
    """
    if not raw or not raw.strip():
        raise InvalidPhoneError("Phone cannot be empty")

    try:
        parsed = phonenumbers.parse(raw, default_region)
    except NumberParseException as e:
        raise InvalidPhoneError(f"Invalid phone format: {e}") from e

    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneError("Phone number is not valid")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
```

- [ ] **Step 5: Run → PASS** (7 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/app/core/phone.py backend/tests/unit/test_phone.py
git commit -m "feat(backend): thêm utility chuẩn hóa số điện thoại E.164 với TDD"
```

---

### Task 2: TDD — `MemberService.find_or_create_member` (Luồng B Phần 1)

**Files:**
- Create: `D:/DoAn/backend/app/schemas/member.py`
- Create: `D:/DoAn/backend/app/services/member_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_member_service.py`

- [ ] **Step 1: Tạo schema `app/schemas/member.py`**

```python
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.tenant_staff import TenantStaffRole


class MemberLookupRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


class MemberResponse(BaseModel):
    membership_id: int
    tenant_id: int
    user_id: int
    user_phone: str | None
    user_full_name: str | None
    user_email: str | None
    points_balance: int
    total_points_earned: int
    current_tier_id: int | None
    current_tier_name: str | None
    joined_at: datetime
    last_activity_at: datetime | None
    is_new: bool  # True nếu vừa được tạo trong request này

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Failing tests `tests/integration/test_member_service.py`**

```python
import pytest
from sqlalchemy import select

from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.member_service import MemberService


@pytest.fixture
async def active_tenant(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.mark.asyncio
async def test_find_or_create_brand_new_user(db_session, active_tenant):
    """Case 1: SĐT hoàn toàn mới — tạo shadow user + membership."""
    service = MemberService(db_session)
    member = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    await db_session.flush()

    assert member.is_new is True
    assert member.user_phone == "+84912345678"
    assert member.points_balance == 0
    assert member.tenant_id == active_tenant.id

    user = await db_session.get(User, member.user_id)
    assert user.is_shadow is True


@pytest.mark.asyncio
async def test_find_existing_user_existing_membership(db_session, active_tenant):
    """Case khách quay lại — không tạo gì mới."""
    service = MemberService(db_session)
    first = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    await db_session.flush()

    second = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    assert second.is_new is False
    assert second.user_id == first.user_id
    assert second.membership_id == first.membership_id


@pytest.mark.asyncio
async def test_existing_user_other_tenant_creates_new_membership(db_session, active_tenant):
    """Case 2/3: User đã có (do tenant khác) — KHÔNG tạo user mới, chỉ tạo membership."""
    other_owner = User(email="other@example.com", password_hash="x", is_active=True)
    db_session.add(other_owner)
    await db_session.flush()
    other_tenant = Tenant(
        name="O", slug="o", owner_user_id=other_owner.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(other_tenant)
    await db_session.flush()

    service = MemberService(db_session)

    member_in_other = await service.find_or_create_member(
        tenant_id=other_tenant.id, phone="0912345678"
    )
    await db_session.flush()
    user_id = member_in_other.user_id

    member_in_active = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    await db_session.flush()

    assert member_in_active.user_id == user_id  # Cùng user
    assert member_in_active.membership_id != member_in_other.membership_id  # Khác membership
    assert member_in_active.is_new is True  # Membership mới (user không mới)


@pytest.mark.asyncio
async def test_normalize_phone_before_lookup(db_session, active_tenant):
    service = MemberService(db_session)
    a = await service.find_or_create_member(tenant_id=active_tenant.id, phone="0912345678")
    await db_session.flush()
    b = await service.find_or_create_member(tenant_id=active_tenant.id, phone="091 234 5678")
    assert a.user_id == b.user_id
    assert a.membership_id == b.membership_id
```

- [ ] **Step 3: Run → FAIL** (Membership model chưa có — sẽ tạo ở bước 4)

> **Lưu ý:** Membership model chưa được tạo trong tuần 1-2 (chỉ có User/Tenant/TenantStaff/Tier/PointRule/...). Cần tạo Membership model trước khi test pass. Tạo trong bước 4 dưới đây.

- [ ] **Step 4: Tạo Membership model + migration**

`app/models/membership.py`:

```python
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.tier import Tier
    from app.models.user import User


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),
        CheckConstraint("points_balance >= 0", name="ck_memberships_balance_nonneg"),
        CheckConstraint("total_points_earned >= 0", name="ck_memberships_total_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_tier_id: Mapped[int | None] = mapped_column(
        ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True
    )
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    user: Mapped["User"] = relationship("User")
    current_tier: Mapped["Tier | None"] = relationship("Tier", foreign_keys=[current_tier_id])
```

Update `app/models/__init__.py` add `Membership`.

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create memberships table"
alembic upgrade head
```

- [ ] **Step 5: Implement `app/services/member_service.py`**

```python
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.phone import normalize_phone
from app.models.membership import Membership
from app.models.tier import Tier
from app.models.user import User
from app.schemas.member import MemberResponse


class MemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_or_create_member(
        self, *, tenant_id: int, phone: str
    ) -> MemberResponse:
        """Luồng B Phần 1 — atomic upsert user theo phone + upsert membership.

        Handles 3 cases:
        - Case 1: User hoàn toàn mới → tạo shadow user + membership
        - Case 2: User đã có (shadow tenant khác) → tạo membership
        - Case 3: User đã có (regular) → tạo membership
        """
        normalized = normalize_phone(phone)

        existing_user = await self.db.scalar(
            select(User).where(User.phone == normalized)
        )

        is_user_new = False
        if existing_user is None:
            existing_user = User(
                phone=normalized,
                is_active=True,
                is_shadow=True,
                system_role="regular",
            )
            self.db.add(existing_user)
            await self.db.flush()
            is_user_new = True

        existing_membership = await self.db.scalar(
            select(Membership)
            .options(joinedload(Membership.current_tier))
            .where(
                Membership.tenant_id == tenant_id,
                Membership.user_id == existing_user.id,
            )
        )

        is_membership_new = False
        if existing_membership is None:
            existing_membership = Membership(
                tenant_id=tenant_id,
                user_id=existing_user.id,
                current_tier_id=None,
                points_balance=0,
                total_points_earned=0,
                joined_at=datetime.now(timezone.utc),
            )
            self.db.add(existing_membership)
            await self.db.flush()
            await self.db.refresh(existing_membership, attribute_names=["current_tier"])
            is_membership_new = True

        return MemberResponse(
            membership_id=existing_membership.id,
            tenant_id=tenant_id,
            user_id=existing_user.id,
            user_phone=existing_user.phone,
            user_full_name=existing_user.full_name,
            user_email=existing_user.email,
            points_balance=existing_membership.points_balance,
            total_points_earned=existing_membership.total_points_earned,
            current_tier_id=existing_membership.current_tier_id,
            current_tier_name=existing_membership.current_tier.name
            if existing_membership.current_tier
            else None,
            joined_at=existing_membership.joined_at,
            last_activity_at=existing_membership.last_activity_at,
            is_new=is_user_new or is_membership_new,
        )

    async def get_member_by_id(
        self, *, tenant_id: int, membership_id: int
    ) -> Membership | None:
        return await self.db.scalar(
            select(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.current_tier))
            .where(
                Membership.id == membership_id,
                Membership.tenant_id == tenant_id,
            )
        )

    async def list_members(
        self, *, tenant_id: int, limit: int = 50, offset: int = 0
    ) -> list[Membership]:
        rows = await self.db.scalars(
            select(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.current_tier))
            .where(Membership.tenant_id == tenant_id)
            .order_by(Membership.last_activity_at.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())
```

- [ ] **Step 6: Run → PASS** (4 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/membership.py backend/app/models/__init__.py backend/alembic/versions/ backend/app/schemas/member.py backend/app/services/member_service.py backend/tests/integration/test_member_service.py
git commit -m "feat(backend): thêm Membership model + MemberService với upsert atomic (Luồng B)"
```

---

### Task 3: Race condition test cho member service (concurrent upsert)

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_member_service.py`

- [ ] **Step 1: Append test concurrent**

```python
import asyncio


@pytest.mark.asyncio
async def test_concurrent_create_no_duplicates(db_session, active_tenant):
    """2 nhân viên cùng nhập 1 SĐT đồng thời — phải atomic, không tạo duplicate."""
    service = MemberService(db_session)

    results = await asyncio.gather(
        service.find_or_create_member(tenant_id=active_tenant.id, phone="0912345678"),
        service.find_or_create_member(tenant_id=active_tenant.id, phone="0912345678"),
    )
    await db_session.flush()

    assert results[0].user_id == results[1].user_id
    assert results[0].membership_id == results[1].membership_id

    from sqlalchemy import func
    user_count = await db_session.scalar(
        select(func.count()).select_from(User).where(User.phone == "+84912345678")
    )
    membership_count = await db_session.scalar(
        select(func.count())
        .select_from(Membership)
        .where(
            Membership.tenant_id == active_tenant.id,
            Membership.user_id == results[0].user_id,
        )
    )
    assert user_count == 1
    assert membership_count == 1
```

> **Note:** Test này dùng `asyncio.gather` nhưng cùng db_session — không thực sự concurrent. Để test atomic thật cần 2 connection riêng. Đây chỉ là smoke test cho race condition phía application. Test thực sự sẽ dùng `pytest-xdist` hoặc 2 transaction riêng — dành cho luận văn.

- [ ] **Step 2: Run → PASS**

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_member_service.py
git commit -m "test(backend): kiểm tra race condition khi tạo member đồng thời"
```

---

## PHASE 2 — Transactions Model + Point Ledger Model + DB Trigger

### Task 4: Tạo `Transaction` model

**Files:**
- Create: `D:/DoAn/backend/app/models/transaction.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo `app/models/transaction.py`**

```python
import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TransactionMethod(str, enum.Enum):
    MANUAL = "manual"
    QR_SHOP = "qr_shop"
    QR_CUSTOMER = "qr_customer"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="ck_transactions_gross_nonneg"),
        CheckConstraint("net_amount >= 0", name="ck_transactions_net_nonneg"),
        CheckConstraint(
            "net_amount <= gross_amount", name="ck_transactions_net_le_gross"
        ),
        CheckConstraint("points_earned >= 0", name="ck_transactions_points_nonneg"),
        Index("ix_transactions_tenant_created", "tenant_id", "created_at"),
        Index("ix_transactions_membership_created", "membership_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    staff_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    gross_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    voucher_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voucher_discount_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    net_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[TransactionMethod] = mapped_column(
        Enum(TransactionMethod, name="transaction_method"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
```

> **Note:** `voucher_id` chưa có FK đến `vouchers` table vì bảng vouchers sẽ tạo ở tuần 5. Tạm để là plain Integer (không FK), tuần 5 sẽ thêm FK qua migration.

- [ ] **Step 2: Update `__init__.py` add Transaction**

- [ ] **Step 3: Generate migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create transactions table"
alembic upgrade head
docker compose exec postgres psql -U loyalty -d loyalty -c "\d transactions"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/transaction.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): thêm Transaction model + migration"
```

---

### Task 5: Tạo `PointLedger` model

**Files:**
- Create: `D:/DoAn/backend/app/models/point_ledger.py`
- Modify: `D:/DoAn/backend/app/models/__init__.py`

- [ ] **Step 1: Tạo file**

```python
import enum

from sqlalchemy import Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LedgerReason(str, enum.Enum):
    EARN = "earn"
    REDEEM = "redeem"
    ADJUST = "adjust"
    EXPIRE = "expire"
    REFUND = "refund"


class LedgerRefType(str, enum.Enum):
    TRANSACTION = "transaction"
    REDEMPTION = "redemption"
    MANUAL = "manual"
    SYSTEM = "system"


class PointLedger(Base, TimestampMixin):
    """Append-only ledger ghi mọi biến động điểm.

    PostgreSQL trigger chặn UPDATE/DELETE — xem migration.
    """
    __tablename__ = "point_ledger"
    __table_args__ = (
        Index("ix_point_ledger_membership_created", "membership_id", "created_at"),
        Index("ix_point_ledger_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)  # + hoặc -
    reason: Mapped[LedgerReason] = mapped_column(
        Enum(LedgerReason, name="ledger_reason"), nullable=False
    )
    ref_type: Mapped[LedgerRefType] = mapped_column(
        Enum(LedgerRefType, name="ledger_ref_type"), nullable=False
    )
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

- [ ] **Step 2: Update `__init__.py` add PointLedger**

- [ ] **Step 3: Generate migration**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create point_ledger table"
```

- [ ] **Step 4: Commit (chưa có trigger, sẽ thêm ở task 6)**

```bash
git add backend/app/models/point_ledger.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): thêm PointLedger model + migration"
```

---

### Task 6: Thêm DB trigger append-only cho `point_ledger`

**Files:**
- Create: New alembic migration

- [ ] **Step 1: Tạo migration mới**

```bash
cd D:/DoAn/backend
alembic revision -m "add append only trigger on point_ledger"
```

- [ ] **Step 2: Edit migration file vừa tạo**

```python
"""add append only trigger on point_ledger

Revision ID: <auto>
Revises: <prev>
Create Date: ...
"""
from alembic import op


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_point_ledger_mutation()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'point_ledger is append-only — UPDATE/DELETE not allowed';
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER no_update_or_delete_point_ledger
    BEFORE UPDATE OR DELETE ON point_ledger
    FOR EACH ROW EXECUTE FUNCTION prevent_point_ledger_mutation();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS no_update_or_delete_point_ledger ON point_ledger;")
    op.execute("DROP FUNCTION IF EXISTS prevent_point_ledger_mutation();")
```

- [ ] **Step 3: Apply + verify**

```bash
alembic upgrade head
docker compose exec postgres psql -U loyalty -d loyalty -c "\d+ point_ledger" | grep -i trigger
```

Test trigger:

```bash
docker compose exec postgres psql -U loyalty -d loyalty -c "
INSERT INTO point_ledger (tenant_id, membership_id, delta, reason, ref_type, balance_after, created_at)
VALUES (1, 1, 100, 'earn', 'manual', 100, NOW()) RETURNING id;
"
docker compose exec postgres psql -U loyalty -d loyalty -c "UPDATE point_ledger SET delta = 0 WHERE id = 1;"
```

Expected: UPDATE raise exception "point_ledger is append-only".

- [ ] **Step 4: Cleanup test row**

```bash
# Trigger chặn cả DELETE → cần dùng TRUNCATE hoặc disable trigger tạm
docker compose exec postgres psql -U loyalty -d loyalty -c "
ALTER TABLE point_ledger DISABLE TRIGGER no_update_or_delete_point_ledger;
DELETE FROM point_ledger WHERE id = 1;
ALTER TABLE point_ledger ENABLE TRIGGER no_update_or_delete_point_ledger;
"
```

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(backend): thêm PostgreSQL trigger append-only cho point_ledger"
```

---

### Task 7: Test trigger từ Python (integration test)

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_point_ledger_trigger.py`

- [ ] **Step 1: Tạo test**

```python
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User


@pytest.fixture
async def membership(db_session):
    user = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    from datetime import datetime, timezone
    m = Membership(
        tenant_id=tenant.id, user_id=user.id, points_balance=0,
        total_points_earned=0, joined_at=datetime.now(timezone.utc)
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.mark.asyncio
async def test_can_insert_ledger_entry(db_session, membership):
    entry = PointLedger(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        balance_after=100,
    )
    db_session.add(entry)
    await db_session.flush()
    assert entry.id is not None


@pytest.mark.asyncio
async def test_cannot_update_ledger_entry(db_session, membership):
    entry = PointLedger(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, balance_after=100,
    )
    db_session.add(entry)
    await db_session.flush()
    entry_id = entry.id

    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("UPDATE point_ledger SET delta = 0 WHERE id = :id"),
            {"id": entry_id},
        )
        await db_session.flush()
    assert "append-only" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_cannot_delete_ledger_entry(db_session, membership):
    entry = PointLedger(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, balance_after=100,
    )
    db_session.add(entry)
    await db_session.flush()
    entry_id = entry.id

    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("DELETE FROM point_ledger WHERE id = :id"),
            {"id": entry_id},
        )
        await db_session.flush()
    assert "append-only" in str(exc_info.value).lower()
```

- [ ] **Step 2: Run → PASS** (3 tests)

> **★ FIX C3 — BẮT BUỘC SỬA conftest.py:** `Base.metadata.create_all` KHÔNG apply trigger từ migration. Phải apply trigger thủ công trong fixture engine để test_point_ledger_trigger pass.

**Update `tests/conftest.py` đầy đủ (fixture engine session-scoped + db_session function-scoped với rollback):**

```python
# tests/conftest.py — full file
import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.models.base import Base


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def database_url(postgres_container):
    sync_url = postgres_container.get_connection_url()
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest_asyncio.fixture(scope="session")
async def engine(database_url):
    """Session-scoped engine — chỉ tạo schema 1 lần cho toàn bộ test session."""
    eng = create_async_engine(database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # ★ FIX C3: Apply append-only trigger (từ migration 008)
        # Base.metadata.create_all KHÔNG biết về DDL trigger — phải execute raw SQL.
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION prevent_point_ledger_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'point_ledger is append-only — UPDATE/DELETE not allowed';
            END;
            $$ LANGUAGE plpgsql;
        """))
        await conn.execute(text(
            "DROP TRIGGER IF EXISTS no_update_or_delete_point_ledger ON point_ledger;"
        ))
        await conn.execute(text("""
            CREATE TRIGGER no_update_or_delete_point_ledger
            BEFORE UPDATE OR DELETE ON point_ledger
            FOR EACH ROW EXECUTE FUNCTION prevent_point_ledger_mutation();
        """))
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped session với rollback (test isolation qua transaction)."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async_session = async_sessionmaker(
            bind=connection, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session
        await transaction.rollback()
```

> **Lưu ý:** Việc đổi từ function-scoped sang session-scoped engine giúp test chạy nhanh hơn nhiều (~5x). Trade-off: trigger DDL chạy 1 lần đầu, nếu test có CREATE TRIGGER khác sẽ conflict. Trong tuần 3 chỉ có 1 trigger, không vấn đề.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_point_ledger_trigger.py backend/tests/conftest.py
git commit -m "test(backend): kiểm tra DB trigger append-only chặn UPDATE/DELETE point_ledger"
```

---

### Task 7.5 (★ NEW — fix C3 final review): Update Makefile `seed-fresh` để TRUNCATE bảng mới + bypass trigger point_ledger

**Files:**
- Modify: `D:/DoAn/Makefile`

> **★ FIX C3:** Tuần 2 Makefile chỉ TRUNCATE 7 bảng đầu. Tuần 3 thêm `memberships`, `transactions`, `point_ledger` — TRUNCATE phải bypass trigger append-only của point_ledger (DELETE bị chặn nhưng TRUNCATE ... CASCADE không chạy DELETE trigger, vẫn cần explicit list).

- [ ] **Step 1: Update `Makefile` target `seed-fresh`**

```makefile
.PHONY: seed-fresh
seed-fresh:
	docker compose exec postgres psql -U loyalty -d loyalty -c "TRUNCATE \
		users, tenants, tenant_staff, tiers, point_rules, \
		verification_codes, tenant_settings_audit, \
		memberships, transactions, point_ledger \
		RESTART IDENTITY CASCADE;"
	$(MAKE) seed
```

> **Lưu ý:** `RESTART IDENTITY` reset auto-increment ID về 1. `CASCADE` xoá rows phụ thuộc. PostgreSQL `TRUNCATE` không trigger row-level DELETE trigger (bypass append-only check) — đây là behavior chuẩn, không phải bug.

- [ ] **Step 2: Test**

```bash
cd D:/DoAn
make seed-fresh
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT COUNT(*) FROM point_ledger;"
```

Expected: 0 (sau truncate, trước seed transactions chưa chạy).

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: update make seed-fresh truncate memberships/transactions/point_ledger"
```

> **Note tuần 4 + 5:** Khi thêm bảng `rewards`, `redemptions`, `campaigns`, `vouchers`, `notifications` — phải lặp lại task này (mở rộng `TRUNCATE` list) ở tuần 4 và tuần 5.

---

## PHASE 3 — LedgerService TDD (Append + Reconcile + Invariant)

### Task 8: TDD — `LedgerService.log_entry`

**Files:**
- Create: `D:/DoAn/backend/app/schemas/ledger.py`
- Create: `D:/DoAn/backend/app/services/ledger_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_ledger_service.py`

- [ ] **Step 1: Schema `app/schemas/ledger.py`**

```python
from datetime import datetime

from pydantic import BaseModel

from app.models.point_ledger import LedgerReason, LedgerRefType


class LedgerEntryResponse(BaseModel):
    id: int
    delta: int
    reason: LedgerReason
    ref_type: LedgerRefType
    ref_id: int | None
    balance_after: int
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReconcileResponse(BaseModel):
    membership_id: int
    expected_balance: int  # SUM(delta)
    actual_balance: int    # memberships.points_balance
    is_consistent: bool
    diff: int
```

- [ ] **Step 2: Failing tests `tests/integration/test_ledger_service.py`**

```python
import pytest

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.ledger_service import LedgerService


@pytest.fixture
async def membership_with_balance(db_session):
    user = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    from datetime import datetime, timezone
    m = Membership(
        tenant_id=tenant.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.mark.asyncio
async def test_log_entry_creates_record(db_session, membership_with_balance):
    service = LedgerService(db_session)
    entry = await service.log_entry(
        tenant_id=membership_with_balance.tenant_id,
        membership_id=membership_with_balance.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=100,
        description="Test entry",
    )
    assert entry.id is not None
    assert entry.delta == 100
    assert entry.balance_after == 100


@pytest.mark.asyncio
async def test_get_history_paginated(db_session, membership_with_balance):
    service = LedgerService(db_session)
    for i in range(5):
        await service.log_entry(
            tenant_id=membership_with_balance.tenant_id,
            membership_id=membership_with_balance.id,
            delta=10,
            reason=LedgerReason.EARN,
            ref_type=LedgerRefType.MANUAL,
            ref_id=None,
            new_balance=10 * (i + 1),
        )
    await db_session.flush()

    history = await service.get_history(
        tenant_id=membership_with_balance.tenant_id,
        membership_id=membership_with_balance.id,
        limit=3,
    )
    assert len(history) == 3
    # Sorted desc by created_at
    assert history[0].balance_after >= history[-1].balance_after


@pytest.mark.asyncio
async def test_reconcile_consistent(db_session, membership_with_balance):
    service = LedgerService(db_session)
    membership_with_balance.points_balance = 50
    await service.log_entry(
        tenant_id=membership_with_balance.tenant_id,
        membership_id=membership_with_balance.id,
        delta=50,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=50,
    )
    await db_session.flush()

    result = await service.reconcile(
        tenant_id=membership_with_balance.tenant_id,
        membership_id=membership_with_balance.id,
    )
    assert result.is_consistent is True
    assert result.diff == 0


@pytest.mark.asyncio
async def test_reconcile_inconsistent_detects_diff(db_session, membership_with_balance):
    service = LedgerService(db_session)
    # Ledger có delta 100 nhưng cache balance chỉ 50 → lệch
    membership_with_balance.points_balance = 50
    await service.log_entry(
        tenant_id=membership_with_balance.tenant_id,
        membership_id=membership_with_balance.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=100,
    )
    await db_session.flush()

    result = await service.reconcile(
        tenant_id=membership_with_balance.tenant_id,
        membership_id=membership_with_balance.id,
    )
    assert result.is_consistent is False
    assert result.diff == 50
    assert result.expected_balance == 100
    assert result.actual_balance == 50
```

- [ ] **Step 3: Implement `app/services/ledger_service.py`**

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.schemas.ledger import LedgerEntryResponse, ReconcileResponse


class LedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_entry(
        self,
        *,
        tenant_id: int,
        membership_id: int,
        delta: int,
        reason: LedgerReason,
        ref_type: LedgerRefType,
        ref_id: int | None,
        new_balance: int,
        description: str | None = None,
    ) -> PointLedger:
        entry = PointLedger(
            tenant_id=tenant_id,
            membership_id=membership_id,
            delta=delta,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
            balance_after=new_balance,
            description=description,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_history(
        self, *, tenant_id: int, membership_id: int, limit: int = 50, offset: int = 0
    ) -> list[PointLedger]:
        rows = await self.db.scalars(
            select(PointLedger)
            .where(
                PointLedger.tenant_id == tenant_id,
                PointLedger.membership_id == membership_id,
            )
            .order_by(PointLedger.created_at.desc(), PointLedger.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())

    async def reconcile(
        self, *, tenant_id: int, membership_id: int
    ) -> ReconcileResponse:
        expected_sum = await self.db.scalar(
            select(func.coalesce(func.sum(PointLedger.delta), 0)).where(
                PointLedger.tenant_id == tenant_id,
                PointLedger.membership_id == membership_id,
            )
        )
        membership = await self.db.get(Membership, membership_id)
        if membership is None or membership.tenant_id != tenant_id:
            raise ValueError(f"Membership {membership_id} not found in tenant {tenant_id}")

        actual = membership.points_balance
        return ReconcileResponse(
            membership_id=membership_id,
            expected_balance=int(expected_sum),
            actual_balance=actual,
            is_consistent=int(expected_sum) == actual,
            diff=int(expected_sum) - actual,
        )
```

- [ ] **Step 4: Run → PASS** (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/ledger.py backend/app/services/ledger_service.py backend/tests/integration/test_ledger_service.py
git commit -m "feat(backend): thêm LedgerService với log_entry + reconcile (TDD)"
```

---

### Task 9-11: Ledger invariant test pattern + helper

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_ledger_invariant.py`
- Create: `D:/DoAn/backend/tests/helpers/__init__.py`
- Create: `D:/DoAn/backend/tests/helpers/ledger_invariant.py`

- [ ] **Step 1: Tạo helper `tests/helpers/ledger_invariant.py`**

```python
"""Reusable helper để verify ledger invariant trong mọi test."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.point_ledger import PointLedger


async def assert_ledger_invariant(db: AsyncSession, membership_id: int) -> None:
    """Assert SUM(point_ledger.delta) == memberships.points_balance.

    Dùng trong mọi test sau khi modify balance để catch bug sớm.
    """
    membership = await db.get(Membership, membership_id)
    assert membership is not None, f"Membership {membership_id} not found"

    expected = await db.scalar(
        select(func.coalesce(func.sum(PointLedger.delta), 0)).where(
            PointLedger.membership_id == membership_id
        )
    )
    actual = membership.points_balance
    assert int(expected) == actual, (
        f"LEDGER INVARIANT VIOLATED for membership {membership_id}: "
        f"sum(ledger.delta)={expected} != memberships.points_balance={actual}"
    )
```

- [ ] **Step 2: Tạo `tests/helpers/__init__.py`** (empty)

- [ ] **Step 3: Tạo invariant test file `tests/integration/test_ledger_invariant.py`**

```python
"""Smoke test: invariant phải đúng sau mọi luồng cốt lõi."""
import pytest
from datetime import datetime, timezone

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.ledger_service import LedgerService
from tests.helpers.ledger_invariant import assert_ledger_invariant


@pytest.mark.asyncio
async def test_invariant_after_single_earn(db_session):
    user = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    m = Membership(
        tenant_id=tenant.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(m)
    await db_session.flush()

    service = LedgerService(db_session)
    m.points_balance = 50
    await service.log_entry(
        tenant_id=tenant.id, membership_id=m.id,
        delta=50, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, ref_id=None, new_balance=50,
    )
    await db_session.flush()

    await assert_ledger_invariant(db_session, m.id)


@pytest.mark.asyncio
async def test_invariant_after_earn_and_redeem(db_session):
    # Setup
    user = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    m = Membership(
        tenant_id=tenant.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(m)
    await db_session.flush()

    service = LedgerService(db_session)

    # Earn 100
    m.points_balance = 100
    m.total_points_earned = 100
    await service.log_entry(
        tenant_id=tenant.id, membership_id=m.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, ref_id=None, new_balance=100,
    )
    await db_session.flush()
    await assert_ledger_invariant(db_session, m.id)

    # Redeem 30
    m.points_balance = 70
    await service.log_entry(
        tenant_id=tenant.id, membership_id=m.id,
        delta=-30, reason=LedgerReason.REDEEM,
        ref_type=LedgerRefType.MANUAL, ref_id=None, new_balance=70,
    )
    await db_session.flush()
    await assert_ledger_invariant(db_session, m.id)
```

- [ ] **Step 4: Run → PASS** (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/tests/helpers/ backend/tests/integration/test_ledger_invariant.py
git commit -m "test(backend): thêm helper assert_ledger_invariant + smoke tests"
```

---

## PHASE 4 — TransactionService TDD Method (a) Manual

### Task 12: TDD — `TransactionService.create_manual_transaction`

**Files:**
- Create: `D:/DoAn/backend/app/schemas/transaction.py`
- Create: `D:/DoAn/backend/app/services/transaction_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_transaction_service.py`

- [ ] **Step 1: Schema `app/schemas/transaction.py`**

```python
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.transaction import TransactionMethod


class CreateManualTransactionRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    gross_amount: int = Field(gt=0, le=100_000_000)
    note: str | None = Field(default=None, max_length=1000)


class TransactionResponse(BaseModel):
    id: int
    tenant_id: int
    membership_id: int
    staff_id: int
    gross_amount: int
    voucher_id: int | None
    voucher_discount_amount: int | None
    net_amount: int
    points_earned: int
    method: TransactionMethod
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionWithMemberResponse(BaseModel):
    transaction: TransactionResponse
    member_phone: str | None
    member_full_name: str | None
    new_balance: int
    new_total_earned: int
    new_tier_id: int | None
    new_tier_name: str | None
    tier_upgraded: bool
```

- [ ] **Step 2: Failing tests `tests/integration/test_transaction_service.py`**

```python
import pytest
from datetime import datetime, timezone

from app.models.point_rule import PointRule
from app.models.tenant import Tenant, TenantStatus
from app.models.tier import Tier
from app.models.user import User
from app.schemas.transaction import CreateManualTransactionRequest
from app.services.transaction_service import (
    NoActivePointRuleError,
    TransactionService,
)
from tests.helpers.ledger_invariant import assert_ledger_invariant


@pytest.fixture
async def shop_with_rule_and_tiers(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="Shop", slug="shop", owner_user_id=owner.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()

    from decimal import Decimal
    rule = PointRule(
        tenant_id=tenant.id,
        points_per_unit=Decimal("1.00"),
        unit_amount=1000,
        min_amount=0,
        is_active=True,
    )
    db_session.add(rule)

    bronze = Tier(tenant_id=tenant.id, name="Bronze", min_points=0, perks={}, is_active=True)
    silver = Tier(tenant_id=tenant.id, name="Silver", min_points=500, perks={}, is_active=True)
    db_session.add_all([bronze, silver])
    await db_session.flush()

    return {"tenant": tenant, "owner": owner, "rule": rule, "bronze": bronze, "silver": silver}


@pytest.mark.asyncio
async def test_create_manual_transaction_brand_new_customer(
    db_session, shop_with_rule_and_tiers
):
    """Khách mới hoàn toàn → tạo user shadow + membership + transaction + ledger."""
    ctx = shop_with_rule_and_tiers
    service = TransactionService(db_session)

    result = await service.create_manual(
        tenant_id=ctx["tenant"].id,
        staff_id=ctx["owner"].id,
        request=CreateManualTransactionRequest(phone="0912345678", gross_amount=50000),
    )
    await db_session.flush()

    assert result.transaction.points_earned == 50  # 50000 / 1000 * 1.00
    assert result.new_balance == 50
    assert result.new_total_earned == 50
    assert result.new_tier_name == "Bronze"
    assert result.tier_upgraded is False  # Bronze is min tier, no upgrade noti

    await assert_ledger_invariant(db_session, result.transaction.membership_id)


@pytest.mark.asyncio
async def test_create_transaction_triggers_tier_upgrade(
    db_session, shop_with_rule_and_tiers
):
    """Tích đủ 500 điểm → upgrade Bronze → Silver."""
    ctx = shop_with_rule_and_tiers
    service = TransactionService(db_session)

    # Lần 1: 450000 VND → 450 điểm → vẫn Bronze
    r1 = await service.create_manual(
        tenant_id=ctx["tenant"].id,
        staff_id=ctx["owner"].id,
        request=CreateManualTransactionRequest(phone="0911111111", gross_amount=450000),
    )
    await db_session.flush()
    assert r1.new_tier_name == "Bronze"
    assert r1.tier_upgraded is False

    # Lần 2: 100000 VND → 100 điểm → tổng 550 → Silver
    r2 = await service.create_manual(
        tenant_id=ctx["tenant"].id,
        staff_id=ctx["owner"].id,
        request=CreateManualTransactionRequest(phone="0911111111", gross_amount=100000),
    )
    await db_session.flush()
    assert r2.new_total_earned == 550
    assert r2.new_tier_name == "Silver"
    assert r2.tier_upgraded is True

    await assert_ledger_invariant(db_session, r2.transaction.membership_id)


@pytest.mark.asyncio
async def test_create_transaction_without_active_rule_raises(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()

    service = TransactionService(db_session)
    with pytest.raises(NoActivePointRuleError):
        await service.create_manual(
            tenant_id=tenant.id,
            staff_id=user.id,
            request=CreateManualTransactionRequest(phone="0912345678", gross_amount=50000),
        )


@pytest.mark.asyncio
async def test_create_transaction_below_min_amount_zero_points(db_session):
    """gross < min_amount → 0 điểm nhưng vẫn tạo transaction."""
    from decimal import Decimal

    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()

    rule = PointRule(
        tenant_id=tenant.id, points_per_unit=Decimal("1.00"),
        unit_amount=1000, min_amount=100000, is_active=True
    )
    db_session.add(rule)
    bronze = Tier(tenant_id=tenant.id, name="Bronze", min_points=0, perks={}, is_active=True)
    db_session.add(bronze)
    await db_session.flush()

    service = TransactionService(db_session)
    result = await service.create_manual(
        tenant_id=tenant.id,
        staff_id=user.id,
        request=CreateManualTransactionRequest(phone="0912345678", gross_amount=50000),
    )
    await db_session.flush()
    assert result.transaction.points_earned == 0
    assert result.new_balance == 0
```

- [ ] **Step 3: Implement `app/services/transaction_service.py` (★ FIXED — apply patches từ review tuần 3)**

```python
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.point_rule import PointRule
from app.models.tier import Tier  # ★ FIX C1 — cần để query tier riêng
from app.models.transaction import Transaction, TransactionMethod
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
)
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService
from app.services.tier_service import TierService


class NoActivePointRuleError(Exception):
    pass


# LOCK ORDERING RULE (xem 6.1 spec):
# Mọi transaction cần lock nhiều bảng phải lock theo thứ tự cố định:
# 1. memberships (luôn đầu tiên — SELECT FOR UPDATE)
# 2. tiers / point_rules (chỉ đọc, không cần lock)
# 3. vouchers (tuần 5)
# 4. rewards (tuần 4)


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_manual(
        self,
        *,
        tenant_id: int,
        staff_id: int,
        request: CreateManualTransactionRequest,
    ) -> TransactionWithMemberResponse:
        """Tạo giao dịch tích điểm method=manual.

        Steps (trong cùng DB transaction):
        1. find_or_create_member theo phone
        2. SELECT FOR UPDATE membership (lock — KHÔNG joinedload nullable FK)
        3. Snapshot old_tier_min_points (cho diff sau recompute)
        4. Get active point_rule
        5. Calculate points_earned
        6. INSERT transaction
        7. UPDATE membership balance + total + last_activity_at
        8. INSERT point_ledger entry
        9. Recompute tier (Luồng G)
        10. So sánh new_tier.min_points vs old_tier_min_points → tier_upgraded
        """
        member_svc = MemberService(self.db)
        ledger_svc = LedgerService(self.db)
        tier_svc = TierService(self.db)

        member = await member_svc.find_or_create_member(
            tenant_id=tenant_id, phone=request.phone
        )

        # ★ FIX C2: KHÔNG joinedload(current_tier) cùng FOR UPDATE
        # PostgreSQL không cho FOR UPDATE trên nullable side của OUTER JOIN.
        # Tách thành 2 queries: 1 để lock + load user (INNER JOIN OK),
        # tier query riêng để snapshot old_tier_min_points.
        membership = await self.db.scalar(
            select(Membership)
            .options(joinedload(Membership.user))  # user_id NOT NULL → INNER JOIN OK
            .where(Membership.id == member.membership_id)
            .with_for_update()
        )
        if membership is None:
            raise ValueError(f"Membership {member.membership_id} not found")

        # ★ FIX C1: Snapshot old_tier_min_points TRƯỚC khi recompute
        # KHÔNG dựa vào membership.current_tier sau recompute (relationship có thể stale).
        old_tier_id = membership.current_tier_id
        old_tier_min_points = 0
        if old_tier_id is not None:
            old_tier = await self.db.get(Tier, old_tier_id)
            old_tier_min_points = old_tier.min_points if old_tier else 0

        rule = await self.db.scalar(
            select(PointRule).where(
                PointRule.tenant_id == tenant_id, PointRule.is_active.is_(True)
            )
        )
        if rule is None:
            raise NoActivePointRuleError(
                f"Tenant {tenant_id} has no active point rule"
            )

        # Manual transaction không có voucher → net == gross
        # Tuần 5 sẽ wrap helper _create_transaction_for_membership với voucher logic
        net_amount = request.gross_amount
        points_earned = self._calculate_points(rule, net_amount)

        txn = Transaction(
            tenant_id=tenant_id,
            membership_id=membership.id,
            staff_id=staff_id,
            gross_amount=request.gross_amount,
            voucher_id=None,
            voucher_discount_amount=None,
            net_amount=net_amount,
            points_earned=points_earned,
            method=TransactionMethod.MANUAL,
            note=request.note,
        )
        self.db.add(txn)
        await self.db.flush()

        new_balance = membership.points_balance + points_earned
        membership.points_balance = new_balance
        membership.total_points_earned += points_earned
        membership.last_activity_at = datetime.now(timezone.utc)

        if points_earned > 0:
            await ledger_svc.log_entry(
                tenant_id=tenant_id,
                membership_id=membership.id,
                delta=points_earned,
                reason=LedgerReason.EARN,
                ref_type=LedgerRefType.TRANSACTION,
                ref_id=txn.id,
                new_balance=new_balance,
                description=f"Manual transaction #{txn.id}",
            )

        # Recompute tier (Luồng G)
        new_tier = await tier_svc.recompute_tier(
            tenant_id=tenant_id, membership_id=membership.id
        )
        await self.db.flush()

        # ★ FIX C1: So sánh new_tier.min_points vs old_tier_min_points (snapshot)
        # — KHÔNG dùng membership.current_tier (đã thay đổi sau recompute, có thể stale)
        tier_upgraded = False
        if new_tier is not None and old_tier_id is not None and new_tier.id != old_tier_id:
            tier_upgraded = new_tier.min_points > old_tier_min_points
        # First-time assign (old_tier_id is None) → tier_upgraded = False

        return TransactionWithMemberResponse(
            transaction=TransactionResponse.model_validate(txn),
            member_phone=member.user_phone,
            member_full_name=member.user_full_name,
            new_balance=membership.points_balance,
            new_total_earned=membership.total_points_earned,
            new_tier_id=membership.current_tier_id,
            new_tier_name=new_tier.name if new_tier else None,
            tier_upgraded=tier_upgraded,
        )

    @staticmethod
    def _calculate_points(rule: PointRule, net_amount: int) -> int:
        """Calculate points earned.

        Args:
            net_amount: net (sau voucher). Manual transaction không có voucher → net == gross.
                        Tuần 5 thêm voucher → caller phải truyền net_amount (hoặc gross
                        nếu tenant.settings.points_on_gross=true).
        """
        if net_amount < rule.min_amount:
            return 0
        units = Decimal(net_amount) / Decimal(rule.unit_amount)
        return int(units * rule.points_per_unit)

    async def list_transactions(
        self, *, tenant_id: int, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        rows = await self.db.scalars(
            select(Transaction)
            .where(Transaction.tenant_id == tenant_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.all())
```

> **Note:** `TierService.recompute_tier` chưa có (sẽ tạo ở Phase 5). Tạm import rồi sẽ implement.

- [ ] **Step 4: Run → tạm fail vì tier_service.recompute_tier chưa có**

- [ ] **Step 5: Commit (chưa run được test)**

```bash
git add backend/app/schemas/transaction.py backend/app/services/transaction_service.py backend/tests/integration/test_transaction_service.py
git commit -m "feat(backend): thêm TransactionService.create_manual (chờ tier_service.recompute_tier)"
```

---

### Tasks 13-16: Lock ordering, retry deadlock, IntegrityError handling

- [ ] **Task 13: Document lock ordering rule** trong code comment

Thêm vào đầu `transaction_service.py`:

```python
# LOCK ORDERING RULE (xem 6.1 trong spec):
# Mọi transaction cần lock nhiều bảng phải lock theo thứ tự cố định:
# 1. memberships (luôn đầu tiên, dùng SELECT FOR UPDATE)
# 2. tiers / point_rules (chỉ đọc, không cần lock)
# 3. vouchers (nếu có, từ tuần 5)
# 4. rewards (nếu có, từ tuần 4)
# Không tuân thủ → deadlock khi 2 transaction concurrent.
```

- [ ] **Task 14: IntegrityError → 409 mapping** đã có sẵn ở pattern tuần 1 — verify trong API endpoint sẽ implement ở Phase 6

- [ ] **Task 15: Test deadlock** — skip cho MVP, document trong README luận văn

- [ ] **Task 16: Commit comments**

```bash
git add backend/app/services/transaction_service.py
git commit -m "docs(backend): thêm comment lock ordering rule trong TransactionService"
```

---

## PHASE 5 — Tier Auto-upgrade (Luồng G)

### Task 17: Mở rộng `TierService` thêm `recompute_tier`

**Files:**
- Modify: `D:/DoAn/backend/app/services/tier_service.py`
- Modify: `D:/DoAn/backend/tests/integration/test_tier_service.py`

- [ ] **Step 1: Failing tests append**

```python
@pytest.mark.asyncio
async def test_recompute_tier_first_assignment(db_session, active_tenant):
    """Membership chưa có tier → assign tier lowest matching."""
    from app.models.membership import Membership
    from datetime import datetime, timezone

    user = User(email="m@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    bronze = await TierService(db_session).create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    silver = await TierService(db_session).create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()

    membership = Membership(
        tenant_id=active_tenant.id, user_id=user.id,
        current_tier_id=None, points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    new_tier = await TierService(db_session).recompute_tier(
        tenant_id=active_tenant.id, membership_id=membership.id
    )
    assert new_tier is not None
    assert new_tier.id == bronze.id


@pytest.mark.asyncio
async def test_recompute_tier_upgrades_when_enough_points(db_session, active_tenant):
    from app.models.membership import Membership
    from datetime import datetime, timezone

    user = User(email="m@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TierService(db_session)
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    silver = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    gold = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Gold", min_points=2000)
    )
    await db_session.flush()

    membership = Membership(
        tenant_id=active_tenant.id, user_id=user.id,
        current_tier_id=None, points_balance=600, total_points_earned=600,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    new_tier = await service.recompute_tier(
        tenant_id=active_tenant.id, membership_id=membership.id
    )
    assert new_tier.id == silver.id  # 600 >= 500 nhưng < 2000


@pytest.mark.asyncio
async def test_recompute_tier_excludes_soft_deleted(db_session, active_tenant):
    from app.models.membership import Membership
    from datetime import datetime, timezone

    user = User(email="m@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TierService(db_session)
    bronze = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    silver_deleted = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()
    await service.delete_tier(tenant_id=active_tenant.id, tier_id=silver_deleted.id)
    await db_session.flush()

    membership = Membership(
        tenant_id=active_tenant.id, user_id=user.id,
        current_tier_id=None, points_balance=600, total_points_earned=600,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    new_tier = await service.recompute_tier(
        tenant_id=active_tenant.id, membership_id=membership.id
    )
    assert new_tier.id == bronze.id  # Silver bị xoá, fallback Bronze
```

- [ ] **Step 2: Implement `recompute_tier` trong `TierService`**

```python
async def recompute_tier(
    self, *, tenant_id: int, membership_id: int
) -> Tier | None:
    """Luồng G — tính lại tier theo total_points_earned.

    Returns:
        Tier mới (hoặc None nếu không có tier nào). Membership.current_tier_id được update.
    """
    from app.models.membership import Membership

    membership = await self.db.get(Membership, membership_id)
    if membership is None or membership.tenant_id != tenant_id:
        raise ValueError(f"Membership {membership_id} not found in tenant {tenant_id}")

    new_tier = await self.db.scalar(
        select(Tier)
        .where(
            Tier.tenant_id == tenant_id,
            Tier.is_active.is_(True),
            Tier.deleted_at.is_(None),
            Tier.min_points <= membership.total_points_earned,
        )
        .order_by(Tier.min_points.desc())
        .limit(1)
    )

    if new_tier is None:
        membership.current_tier_id = None
        await self.db.flush()
        return None

    if membership.current_tier_id != new_tier.id:
        membership.current_tier_id = new_tier.id
        await self.db.flush()

    return new_tier
```

- [ ] **Step 3: Run → PASS**

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/tier_service.py backend/tests/integration/test_tier_service.py
git commit -m "feat(backend): thêm TierService.recompute_tier (Luồng G upgrade hạng)"
```

---

### Task 18: Run lại `test_transaction_service.py` (giờ có recompute_tier)

```bash
cd D:/DoAn/backend
pytest tests/integration/test_transaction_service.py -v
```

Expected: 4 passed.

- [ ] **Commit (no code change, just verify)**

---

### Task 19: Test ledger invariant với TransactionService end-to-end

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_ledger_invariant.py`

- [ ] **Append test**

```python
@pytest.mark.asyncio
async def test_invariant_after_transaction_service_create_manual(
    db_session, shop_with_rule_and_tiers
):
    """End-to-end: tạo giao dịch qua TransactionService → invariant phải đúng."""
    from app.schemas.transaction import CreateManualTransactionRequest
    from app.services.transaction_service import TransactionService

    ctx = shop_with_rule_and_tiers
    service = TransactionService(db_session)

    for amount in [50000, 200000, 350000, 100000]:
        result = await service.create_manual(
            tenant_id=ctx["tenant"].id,
            staff_id=ctx["owner"].id,
            request=CreateManualTransactionRequest(phone="0912345678", gross_amount=amount),
        )
        await db_session.flush()
        await assert_ledger_invariant(db_session, result.transaction.membership_id)
```

> **Note:** `shop_with_rule_and_tiers` fixture từ `test_transaction_service.py` — copy/import.

- [ ] **Run → PASS, commit**

```bash
git add backend/tests/integration/test_ledger_invariant.py
git commit -m "test(backend): kiểm tra ledger invariant qua TransactionService end-to-end"
```

---

## PHASE 6 — API Endpoints

### Task 20: API `POST /merchant/transactions`

**Files:**
- Create: `D:/DoAn/backend/app/api/transactions.py`
- Create: `D:/DoAn/backend/tests/integration/test_transactions_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Failing tests** — register tenant + tier + rule + create transaction qua API + verify response + verify ledger

- [ ] **Step 2: Implement**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_staff_in_tenant
from app.core.phone import InvalidPhoneError
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.schemas.transaction import (
    CreateManualTransactionRequest,
    TransactionResponse,
    TransactionWithMemberResponse,
)
from app.services.transaction_service import (
    NoActivePointRuleError,
    TransactionService,
)

router = APIRouter(prefix="/merchant/transactions", tags=["merchant-transactions"])


@router.post("", response_model=TransactionWithMemberResponse, status_code=201)
async def create_manual_transaction(
    request: CreateManualTransactionRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionWithMemberResponse:
    service = TransactionService(db)
    try:
        return await service.create_manual(
            tenant_id=tenant_id, staff_id=user.id, request=request
        )
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=f"Invalid phone: {e}") from e
    except NoActivePointRuleError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail="Database integrity violation"
        ) from e


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[TransactionResponse]:
    service = TransactionService(db)
    rows = await service.list_transactions(tenant_id=tenant_id, limit=limit, offset=offset)
    return [TransactionResponse.model_validate(t) for t in rows]
```

- [ ] **Step 3: Update main.py**

- [ ] **Step 4: Run + commit**

```bash
git add backend/app/api/transactions.py backend/app/main.py backend/tests/integration/test_transactions_api.py
git commit -m "feat(backend): thêm API POST /merchant/transactions + GET list"
```

---

### Task 21: API `/merchant/members` (list + detail + history)

**Files:**
- Create: `D:/DoAn/backend/app/api/members.py`
- Create: `D:/DoAn/backend/tests/integration/test_members_api.py`
- Modify: `D:/DoAn/backend/app/main.py`

- [ ] **Step 1: Implement**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_staff_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.ledger import LedgerEntryResponse
from app.schemas.member import MemberResponse
from app.schemas.transaction import TransactionResponse
from app.services.ledger_service import LedgerService
from app.services.member_service import MemberService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/merchant/members", tags=["merchant-members"])


@router.get("", response_model=list[MemberResponse])
async def list_members(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    service = MemberService(db)
    members = await service.list_members(tenant_id=tenant_id, limit=limit, offset=offset)
    return [
        MemberResponse(
            membership_id=m.id,
            tenant_id=m.tenant_id,
            user_id=m.user_id,
            user_phone=m.user.phone,
            user_full_name=m.user.full_name,
            user_email=m.user.email,
            points_balance=m.points_balance,
            total_points_earned=m.total_points_earned,
            current_tier_id=m.current_tier_id,
            current_tier_name=m.current_tier.name if m.current_tier else None,
            joined_at=m.joined_at,
            last_activity_at=m.last_activity_at,
            is_new=False,
        )
        for m in members
    ]


@router.get("/{membership_id}", response_model=MemberResponse)
async def get_member(
    membership_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    service = MemberService(db)
    m = await service.get_member_by_id(tenant_id=tenant_id, membership_id=membership_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return MemberResponse(
        membership_id=m.id,
        tenant_id=m.tenant_id,
        user_id=m.user_id,
        user_phone=m.user.phone,
        user_full_name=m.user.full_name,
        user_email=m.user.email,
        points_balance=m.points_balance,
        total_points_earned=m.total_points_earned,
        current_tier_id=m.current_tier_id,
        current_tier_name=m.current_tier.name if m.current_tier else None,
        joined_at=m.joined_at,
        last_activity_at=m.last_activity_at,
        is_new=False,
    )


@router.get("/{membership_id}/ledger", response_model=list[LedgerEntryResponse])
async def get_member_ledger(
    membership_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_staff_in_tenant),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[LedgerEntryResponse]:
    service = LedgerService(db)
    rows = await service.get_history(
        tenant_id=tenant_id, membership_id=membership_id, limit=limit
    )
    return [LedgerEntryResponse.model_validate(r) for r in rows]
```

- [ ] **Step 2-4: Tests + main.py + commit**

```bash
git add backend/app/api/members.py backend/app/main.py backend/tests/integration/test_members_api.py
git commit -m "feat(backend): thêm API /merchant/members list + detail + ledger"
```

---

### Tasks 22-23: API rate limit + thêm vào main.py

- [ ] **Task 22:** Apply rate limit `30/phút/staff` cho `POST /merchant/transactions`

```python
from app.core.limiter import limiter
from fastapi import Request

@router.post("", response_model=TransactionWithMemberResponse, status_code=201)
@limiter.limit("30/minute")
async def create_manual_transaction(
    request_obj: Request,  # Cần cho slowapi
    body: CreateManualTransactionRequest,
    ...
):
    ...
```

Update test rate limit pattern.

- [ ] **Task 23:** Commit

```bash
git commit -m "feat(backend): rate limit 30/phút/staff cho POST /merchant/transactions"
```

---

## PHASE 7 — Admin Reconcile + Cross-tenant Tests

### Task 24: Admin endpoint `POST /admin/reconcile/{membership_id}`

**Files:**
- Modify: `D:/DoAn/backend/app/api/admin.py`

- [ ] **Step 1: Append endpoint**

```python
from app.schemas.ledger import ReconcileResponse
from app.services.ledger_service import LedgerService


@router.post("/reconcile/{membership_id}", response_model=ReconcileResponse)
async def reconcile_membership(
    membership_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ReconcileResponse:
    """Verify SUM(point_ledger.delta) == memberships.points_balance."""
    from sqlalchemy import select
    from app.models.membership import Membership

    membership = await db.get(Membership, membership_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    service = LedgerService(db)
    return await service.reconcile(
        tenant_id=membership.tenant_id, membership_id=membership_id
    )
```

- [ ] **Step 2-4: Tests + commit**

```bash
git commit -m "feat(backend): thêm POST /admin/reconcile/{id} endpoint"
```

---

### Task 25-26: Cross-tenant isolation tests cho transactions + members

**Files:**
- Modify: `D:/DoAn/backend/tests/integration/test_tenant_isolation.py`

- [ ] **Append tests**

```python
@pytest.mark.asyncio
async def test_owner_a_cannot_create_transaction_in_tenant_b(
    client, two_tenants_with_owners
):
    ctx = two_tenants_with_owners
    response = await client.post(
        "/merchant/transactions",
        json={"phone": "0912345678", "gross_amount": 50000},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_a_cannot_list_members_in_tenant_b(client, two_tenants_with_owners):
    ctx = two_tenants_with_owners
    response = await client.get(
        "/merchant/members",
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_members_isolated_by_tenant(client, two_tenants_with_owners, db_session):
    """Khách tạo ở tenant A không thấy ở tenant B (cùng SĐT khác membership)."""
    ctx = two_tenants_with_owners
    # Setup point_rule cho cả 2 tenant
    from decimal import Decimal
    from app.models.point_rule import PointRule
    from app.models.tier import Tier

    for t in [ctx["tenant_a"], ctx["tenant_b"]]:
        db_session.add(PointRule(
            tenant_id=t.id, points_per_unit=Decimal("1.00"),
            unit_amount=1000, min_amount=0, is_active=True
        ))
        db_session.add(Tier(
            tenant_id=t.id, name="Bronze", min_points=0, perks={}, is_active=True
        ))
    await db_session.flush()

    # Tạo giao dịch trong tenant A
    await client.post(
        "/merchant/transactions",
        json={"phone": "0912345678", "gross_amount": 50000},
        headers={
            "Authorization": f"Bearer {ctx['token_a']}",
            "X-Tenant-Id": str(ctx["tenant_a"].id),
        },
    )

    # Tenant B list members → empty
    list_b = await client.get(
        "/merchant/members",
        headers={
            "Authorization": f"Bearer {ctx['token_b']}",
            "X-Tenant-Id": str(ctx["tenant_b"].id),
        },
    )
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0
```

```bash
git commit -m "test(backend): cross-tenant isolation cho transactions + members"
```

---

## PHASE 8 — Seed v2

### Task 27-29: Mở rộng `scripts/seed.py` thêm 20 khách + 100 transactions

**Files:**
- Modify: `D:/DoAn/backend/scripts/seed.py`

- [ ] **Step 1: Thêm function `seed_members_and_transactions`**

```python
import random
from app.schemas.transaction import CreateManualTransactionRequest
from app.services.transaction_service import TransactionService


SAMPLE_PHONES = [
    f"091{random.randint(1000000, 9999999)}" for _ in range(10)
] + [
    f"098{random.randint(1000000, 9999999)}" for _ in range(10)
]


async def seed_members_and_transactions(db, tenant, owner):
    txn_service = TransactionService(db)
    print(f"      → Seeding 50 transactions for tenant {tenant.name}...")
    for i in range(50):
        phone = random.choice(SAMPLE_PHONES)
        amount = random.choice([20000, 50000, 100000, 200000, 500000])
        try:
            await txn_service.create_manual(
                tenant_id=tenant.id,
                staff_id=owner.id,
                request=CreateManualTransactionRequest(
                    phone=phone, gross_amount=amount
                ),
            )
            await db.flush()
        except Exception as e:
            print(f"      ⚠️  Skip txn: {e}")
    print(f"      ✓ 50 transactions seeded")


# Trong seed():
# Sau khi seed tier + point_rule cho mỗi tenant:
await seed_members_and_transactions(db, tenant, owner)
```

- [ ] **Step 2: Test seed**

```bash
cd D:/DoAn
make seed-fresh
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT COUNT(*) FROM transactions;"
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT COUNT(*) FROM memberships;"
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT COUNT(*) FROM point_ledger;"
```

Expected: ~100 transactions, ~20-40 unique memberships, ~100 ledger entries.

- [ ] **Step 3: Verify reconcile invariant tự động cho mọi membership sau seed**

Thêm vào cuối seed():

```python
print("\n  Verifying ledger invariant for all memberships...")
from app.services.ledger_service import LedgerService
from app.models.membership import Membership

ledger_service = LedgerService(db)
all_memberships = list((await db.scalars(select(Membership))).all())
inconsistent = []
for m in all_memberships:
    result = await ledger_service.reconcile(
        tenant_id=m.tenant_id, membership_id=m.id
    )
    if not result.is_consistent:
        inconsistent.append((m.id, result.diff))

if inconsistent:
    print(f"  ❌ {len(inconsistent)} memberships INCONSISTENT: {inconsistent}")
else:
    print(f"  ✓ All {len(all_memberships)} memberships ledger invariant OK")
```

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/seed.py
git commit -m "feat(backend): seed v2 thêm 100 transactions + auto verify ledger invariant"
```

---

## PHASE 9 — Frontend `/pos` Layout + Auth Guard

### Task 30: Tạo `/pos` layout với staff guard

**Files:**
- Create: `D:/DoAn/frontend/src/app/pos/layout.tsx`
- Modify: `D:/DoAn/frontend/src/components/auth-guard.tsx`

- [ ] **Step 1: Update AuthGuard support tenant role**

```typescript
"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import { useTenantStore } from "@/lib/tenant-store";

interface AuthGuardProps {
  children: ReactNode;
  requireRole?: "super_admin" | "regular";
  requireTenantRole?: "owner" | "staff" | "any";
}

export function AuthGuard({ children, requireRole, requireTenantRole }: AuthGuardProps) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const tenant = useTenantStore((s) => s.currentTenant);

  useEffect(() => {
    if (!user) fetchMe();
  }, [user, fetchMe]);

  useEffect(() => {
    if (user === null) return;
    if (requireRole && user.system_role !== requireRole) {
      router.push("/");
    }
    if (requireTenantRole && !tenant) {
      router.push("/merchant/register");
    }
  }, [user, requireRole, requireTenantRole, tenant, router]);

  if (user === null) {
    return <div className="p-8 text-center">Đang tải...</div>;
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Tạo `app/pos/layout.tsx`**

```typescript
import type { ReactNode } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { TenantContextProvider } from "@/components/tenant-context-provider";

export default function PosLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard requireTenantRole="any">
      <TenantContextProvider>
        <div className="min-h-screen bg-slate-50">
          <header className="bg-slate-900 text-white p-4 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">POS</h1>
              <p className="text-xs text-slate-400">Tích điểm tại quầy</p>
            </div>
            <nav className="flex gap-4">
              <Link href="/pos" className="hover:underline">Trang chính</Link>
              <Link href="/pos/transactions" className="hover:underline">Giao dịch</Link>
              <Link href="/merchant" className="hover:underline">Merchant</Link>
            </nav>
          </header>
          <main className="p-6 max-w-6xl mx-auto">{children}</main>
        </div>
      </TenantContextProvider>
    </AuthGuard>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/auth-guard.tsx frontend/src/app/pos/layout.tsx
git commit -m "feat(frontend): thêm /pos layout với staff guard"
```

---

### Task 31-33: `/pos` dashboard + tenant switcher + theme

- [ ] **Task 31:** Tạo `/pos/page.tsx` dashboard với button "Tạo giao dịch mới"

```typescript
"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenantStore } from "@/lib/tenant-store";

export default function PosDashboard() {
  const tenant = useTenantStore((s) => s.currentTenant);
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">{tenant?.name}</h2>
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Tạo giao dịch tích điểm</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Nhập số điện thoại khách + số tiền để tích điểm thủ công.
          </p>
          <Button asChild className="w-full">
            <Link href="/pos/transactions/new">+ Tạo giao dịch mới</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Task 32:** Tenant switcher (skip cho MVP, document deferred)

- [ ] **Task 33:** Commit

```bash
git add frontend/src/app/pos/page.tsx
git commit -m "feat(frontend): thêm /pos dashboard"
```

---

## PHASE 10 — Frontend `/pos/transactions` Form

### Task 34: API client extension

**Files:**
- Modify: `D:/DoAn/frontend/src/lib/api.ts`
- Create: `D:/DoAn/frontend/src/types/transaction.ts`
- Create: `D:/DoAn/frontend/src/types/member.ts`
- Create: `D:/DoAn/frontend/src/types/ledger.ts`

- [ ] **Step 1: Tạo type files**

`types/transaction.ts`:

```typescript
export type TransactionMethod = "manual" | "qr_shop" | "qr_customer";

export interface Transaction {
  id: number;
  tenant_id: number;
  membership_id: number;
  staff_id: number;
  gross_amount: number;
  voucher_id: number | null;
  voucher_discount_amount: number | null;
  net_amount: number;
  points_earned: number;
  method: TransactionMethod;
  note: string | null;
  created_at: string;
}

export interface CreateManualTransactionRequest {
  phone: string;
  gross_amount: number;
  note?: string;
}

export interface TransactionWithMemberResponse {
  transaction: Transaction;
  member_phone: string | null;
  member_full_name: string | null;
  new_balance: number;
  new_total_earned: number;
  new_tier_id: number | null;
  new_tier_name: string | null;
  tier_upgraded: boolean;
}
```

`types/member.ts`:

```typescript
export interface Member {
  membership_id: number;
  tenant_id: number;
  user_id: number;
  user_phone: string | null;
  user_full_name: string | null;
  user_email: string | null;
  points_balance: number;
  total_points_earned: number;
  current_tier_id: number | null;
  current_tier_name: string | null;
  joined_at: string;
  last_activity_at: string | null;
  is_new: boolean;
}
```

`types/ledger.ts`:

```typescript
export type LedgerReason = "earn" | "redeem" | "adjust" | "expire" | "refund";
export type LedgerRefType = "transaction" | "redemption" | "manual" | "system";

export interface LedgerEntry {
  id: number;
  delta: number;
  reason: LedgerReason;
  ref_type: LedgerRefType;
  ref_id: number | null;
  balance_after: number;
  description: string | null;
  created_at: string;
}
```

- [ ] **Step 2: Append `transactionApi`, `memberApi`, `ledgerApi` vào `lib/api.ts`**

```typescript
import type { Member } from "@/types/member";
import type {
  CreateManualTransactionRequest,
  Transaction,
  TransactionWithMemberResponse,
} from "@/types/transaction";
import type { LedgerEntry } from "@/types/ledger";

export const transactionApi = {
  createManual: (tenantId: number, data: CreateManualTransactionRequest) =>
    api.post<TransactionWithMemberResponse>(
      "/merchant/transactions",
      data,
      withTenant(tenantId),
    ),
  list: (tenantId: number, limit = 50, offset = 0) =>
    api.get<Transaction[]>(
      `/merchant/transactions?limit=${limit}&offset=${offset}`,
      withTenant(tenantId),
    ),
};

export const memberApi = {
  list: (tenantId: number, limit = 50, offset = 0) =>
    api.get<Member[]>(
      `/merchant/members?limit=${limit}&offset=${offset}`,
      withTenant(tenantId),
    ),
  get: (tenantId: number, membershipId: number) =>
    api.get<Member>(`/merchant/members/${membershipId}`, withTenant(tenantId)),
  ledger: (tenantId: number, membershipId: number, limit = 50) =>
    api.get<LedgerEntry[]>(
      `/merchant/members/${membershipId}/ledger?limit=${limit}`,
      withTenant(tenantId),
    ),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/ frontend/src/lib/api.ts
git commit -m "feat(frontend): thêm transaction/member/ledger types + API client"
```

---

### Task 35: Tạo `/pos/transactions/new` form

**Files:**
- Create: `D:/DoAn/frontend/src/app/pos/transactions/new/page.tsx`

- [ ] **Step 1: Tạo form lớn cho tablet**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { transactionApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { TransactionWithMemberResponse } from "@/types/transaction";

const schema = z.object({
  phone: z.string().min(8).max(20),
  gross_amount: z.coerce.number().int().min(1).max(100_000_000),
  note: z.string().max(1000).optional(),
});

type FormData = z.infer<typeof schema>;

export default function NewTransactionPage() {
  const router = useRouter();
  const tenant = useTenantStore((s) => s.currentTenant);
  const [result, setResult] = useState<TransactionWithMemberResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    if (!tenant) return;
    setError(null);
    setSubmitting(true);
    try {
      const res = await transactionApi.createManual(tenant.id, {
        phone: data.phone,
        gross_amount: data.gross_amount,
        note: data.note || undefined,
      });
      setResult(res.data);
      reset();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Lỗi tạo giao dịch");
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-green-600">✓ Tích điểm thành công</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-lg">
            <div>
              <p className="text-sm text-muted-foreground">Khách</p>
              <p className="font-semibold">
                {result.member_full_name || "—"} ({result.member_phone})
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Số tiền</p>
              <p className="font-semibold">
                {result.transaction.gross_amount.toLocaleString("vi-VN")} VND
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Điểm tích</p>
              <p className="font-semibold text-2xl text-green-600">
                +{result.transaction.points_earned}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Tổng điểm</p>
              <p className="font-semibold text-2xl">{result.new_balance}</p>
            </div>
            <div className="col-span-2">
              <p className="text-sm text-muted-foreground">Hạng hiện tại</p>
              <p className="font-semibold">
                {result.new_tier_name || "—"}
                {result.tier_upgraded && (
                  <span className="ml-2 text-sm bg-yellow-100 text-yellow-900 px-2 py-1 rounded">
                    🎉 Vừa lên hạng!
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setResult(null)} className="flex-1">
              Tạo giao dịch mới
            </Button>
            <Button variant="outline" onClick={() => router.push("/pos")}>
              Trở về POS
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Tạo giao dịch tích điểm</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <Label htmlFor="phone" className="text-lg">
              Số điện thoại khách
            </Label>
            <Input
              id="phone"
              type="tel"
              placeholder="0912345678"
              className="text-2xl h-14 text-center font-mono"
              {...register("phone")}
            />
            {errors.phone && (
              <p className="text-sm text-red-500">{errors.phone.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="gross_amount" className="text-lg">
              Số tiền (VND)
            </Label>
            <Input
              id="gross_amount"
              type="number"
              placeholder="50000"
              className="text-2xl h-14 text-center"
              {...register("gross_amount")}
            />
            {errors.gross_amount && (
              <p className="text-sm text-red-500">{errors.gross_amount.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="note">Ghi chú (tuỳ chọn)</Label>
            <Input id="note" {...register("note")} />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button type="submit" disabled={submitting} className="w-full h-14 text-lg">
            {submitting ? "Đang tạo..." : "Tích điểm"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Test thủ công**

```bash
docker compose up -d && make seed-fresh
# Login owner1, vào /pos/transactions/new
# Nhập 0912345678, 50000 → verify success card
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/pos/transactions/
git commit -m "feat(frontend): thêm /pos/transactions/new form tablet-optimized"
```

---

### Tasks 36-37: Recent transactions list + member quick lookup (skip cho MVP, defer)

- [ ] **Task 36:** Note "deferred" trong code comment
- [ ] **Task 37:** Smoke test E2E

---

## PHASE 11 — Frontend `/merchant/members`

### Task 38: Tạo `/merchant/members/page.tsx` (list)

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/members/page.tsx`

- [ ] **Step 1: Tạo file**

```typescript
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

import { memberApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { Member } from "@/types/member";

export default function MerchantMembersPage() {
  const tenant = useTenantStore((s) => s.currentTenant);
  const [members, setMembers] = useState<Member[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    if (!tenant) return;
    setLoading(true);
    const { data } = await memberApi.list(tenant.id);
    setMembers(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, [tenant]);

  const filtered = members.filter((m) =>
    [m.user_phone, m.user_full_name, m.user_email]
      .filter(Boolean)
      .some((f) => f!.toLowerCase().includes(search.toLowerCase())),
  );

  if (loading) return <p>Đang tải...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Thành viên ({members.length})</h1>
      <Input
        placeholder="Tìm theo SĐT / tên / email..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-md"
      />

      <div className="space-y-2">
        {filtered.map((m) => (
          <Link key={m.membership_id} href={`/merchant/members/${m.membership_id}`}>
            <Card className="hover:bg-slate-50 cursor-pointer">
              <CardContent className="py-4 flex items-center justify-between">
                <div>
                  <p className="font-semibold">{m.user_full_name || "—"}</p>
                  <p className="text-sm text-muted-foreground font-mono">
                    {m.user_phone || m.user_email}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-lg">{m.points_balance.toLocaleString("vi-VN")}</p>
                  <p className="text-xs text-muted-foreground">{m.current_tier_name || "—"}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/members/page.tsx
git commit -m "feat(frontend): thêm /merchant/members list với search"
```

---

### Tasks 39-40: Member detail + ledger viewer

**Files:**
- Create: `D:/DoAn/frontend/src/app/merchant/members/[id]/page.tsx`

- [ ] **Step 1: Tạo file detail**

```typescript
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { memberApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { LedgerEntry } from "@/types/ledger";
import type { Member } from "@/types/member";

export default function MemberDetailPage() {
  const params = useParams();
  const tenant = useTenantStore((s) => s.currentTenant);
  const membershipId = Number(params.id);

  const [member, setMember] = useState<Member | null>(null);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      setLoading(true);
      const [m, l] = await Promise.all([
        memberApi.get(tenant.id, membershipId),
        memberApi.ledger(tenant.id, membershipId),
      ]);
      setMember(m.data);
      setLedger(l.data);
      setLoading(false);
    })();
  }, [tenant, membershipId]);

  if (loading || !member) return <p>Đang tải...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{member.user_full_name || member.user_phone}</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Điểm hiện tại</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{member.points_balance.toLocaleString("vi-VN")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Tổng tích lũy</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{member.total_points_earned.toLocaleString("vi-VN")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Hạng</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{member.current_tier_name || "—"}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lịch sử biến động điểm</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {ledger.map((entry) => (
              <div
                key={entry.id}
                className="flex justify-between border-b py-2 text-sm"
              >
                <div>
                  <span className="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded mr-2">
                    {entry.reason}
                  </span>
                  <span className="text-muted-foreground">{entry.description || "—"}</span>
                </div>
                <div className="text-right">
                  <span
                    className={
                      entry.delta > 0 ? "text-green-600 font-bold" : "text-red-600 font-bold"
                    }
                  >
                    {entry.delta > 0 ? "+" : ""}
                    {entry.delta}
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">
                    → {entry.balance_after}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/merchant/members/
git commit -m "feat(frontend): thêm /merchant/members/[id] detail với ledger history"
```

---

## PHASE 12 — Smoke Test E2E + Run Tests

### Tasks 41-42: Add `/merchant/members` link vào sidebar + smoke test

- [ ] **Task 41:** Update `/merchant/layout.tsx` thêm link "Thành viên"

```typescript
<Link href="/merchant/members" className="block hover:underline">Thành viên</Link>
```

- [ ] **Task 42:** Smoke test E2E full

```bash
cd D:/DoAn
docker compose down
docker compose up -d --build
make seed-fresh
cd backend && pytest -v
```

Expected: ~95 tests pass (60 từ tuần 2 + ~30 mới).

Manual test:
1. Login owner1 → /pos/transactions/new → nhập 0912345678 + 50000 → success
2. Lặp lại với 500000 → verify upgrade Silver
3. Vào /merchant/members → thấy 0912345678 trong list
4. Click → detail → ledger có 2 entries
5. Cross-tenant: sửa X-Tenant-Id sang tenant 2 → 403

```bash
git add frontend/src/app/merchant/layout.tsx
git commit -m "feat(frontend): thêm link Thành viên vào /merchant sidebar"
```

---

## PHASE 13 — Final Smoke + CI

### Task 43-44: CI pass + commit final

- [ ] **Task 43:** Push lên GitHub, verify CI xanh
- [ ] **Task 44:** Tag commit cuối tuần 3

```bash
cd D:/DoAn
git push origin main
# Verify GitHub Actions xanh
git tag tuan-3-complete
```

---

## Tổng kết Tuần 3

### Đã hoàn thành (44 tasks)

**Backend:**
- ✅ Phone E.164 normalization utility
- ✅ Membership model + migration
- ✅ Transaction model + migration
- ✅ Point ledger model + DB trigger append-only (PostgreSQL function + trigger)
- ✅ MemberService — Luồng B Phần 1 (find_or_create_member với 3 case)
- ✅ TransactionService.create_manual với lock ordering rule
- ✅ LedgerService log + reconcile + invariant
- ✅ TierService.recompute_tier (Luồng G auto upgrade)
- ✅ API endpoints: POST/GET /merchant/transactions, /merchant/members
- ✅ Admin reconcile endpoint
- ✅ Seed v2: thêm 100 transactions + auto verify ledger invariant
- ✅ Cross-tenant isolation tests cho transactions/members
- ✅ Test ledger invariant helper + 3 smoke scenarios
- ✅ Test DB trigger chặn UPDATE/DELETE

**Frontend:**
- ✅ AuthGuard mở rộng `requireTenantRole`
- ✅ /pos layout tablet-optimized + dashboard
- ✅ /pos/transactions/new form lớn (font 2xl, height 14)
- ✅ Success card hiển thị balance + tier upgrade
- ✅ /merchant/members list với search
- ✅ /merchant/members/[id] detail + ledger viewer
- ✅ API client: transactionApi, memberApi, ledgerApi

**Tests:**
- ✅ ~30 new tests (member service 5, transaction service 4, ledger service 4, ledger trigger 3, ledger invariant 3, transactions API ~5, members API ~5, cross-tenant 3)
- ✅ Tổng tests: ~95 (60 từ tuần 2 + 30 tuần 3)

### Acceptance criteria

- [x] POS form tạo transaction → user shadow + membership + transaction + ledger + tier upgrade hoạt động end-to-end
- [x] Test ledger invariant pass cho mọi membership
- [x] DB trigger chặn UPDATE/DELETE point_ledger
- [x] Cross-tenant isolation tests pass
- [x] Seed v2 tạo data demo realistic
- [x] CI xanh

---

## Sang tuần 4

Tuần 4 sẽ làm:
- QR shop deeplink + HMAC token
- QR personal customer (JWT signed exp 120s + fallback_code)
- Transaction method (b) qr_shop và (c) qr_customer
- Rewards module (CRUD + soft delete + stock NULL = unlimited)
- Redemption flow (Luồng D với atomic stock decrement)
- Birthday voucher background job (APScheduler timezone Asia/Ho_Chi_Minh)
- /pos QR scanner (html5-qrcode)
- /pos QR shop display
- /member PWA QR cá nhân rolling
- /member rewards browse + redeem
- PWA service worker enable production

Plan tuần 4 sẽ được tạo riêng tại `docs/superpowers/plans/2026-04-12-tuan-4-qr-rewards-redemption.md`.
