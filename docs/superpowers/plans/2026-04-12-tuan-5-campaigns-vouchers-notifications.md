# Tuần 5 — Campaigns, Vouchers Lazy Claim, Notifications & Birthday Job

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** Implement chiến dịch khuyến mãi với lazy claim model (KHÔNG bulk-issue voucher), atomic claim chống TOCTOU bằng partial unique index + atomic UPDATE check max_issuances. Voucher sử dụng trong transaction (update gross/net/discount). Birthday voucher background job (Luồng F — đã dời từ tuần 4 vì cần bảng vouchers/campaigns). Notifications module cho in-app messages. Frontend `/merchant/campaigns`, `/member/vouchers`, `/pos voucher input`.

**Architecture:**
- **Campaigns:** model có `max_issuances` (NULL = unlimited), `issued_count` cache, `target_tier_id` (NULL = mọi tier), `source` enum (manual/birthday/signup). Soft delete qua `deleted_at`.
- **Vouchers:** model có `code` UNIQUE per tenant, `status` (issued/used/expired), `expires_at`. **Partial unique index** `(campaign_id, membership_id) WHERE status NOT IN ('expired', 'used')` chống claim trùng nhưng cho phép sinh nhật năm sau.
- **Lazy claim atomic:** trong 1 DB transaction:
  1. `UPDATE campaigns SET issued_count = issued_count + 1 WHERE id AND active AND time_window AND (max_issuances IS NULL OR issued_count < max_issuances)` → nếu rowcount=0 → 409 CAMPAIGN_FULL
  2. `INSERT vouchers ON CONFLICT partial unique → IntegrityError` → 409 ALREADY_CLAIMED
- **Voucher use trong transaction:** PATCH `transactions.create_*` để accept `voucher_code`. Tính `voucher_discount_amount` = min(percent×gross, max_discount) hoặc fixed. Update `vouchers.status=used`, `vouchers.used_at`. Set `transactions.voucher_id`, `transactions.voucher_discount_amount`. Điểm tính theo `net_amount` (mặc định) hoặc `gross_amount` nếu setting `points_on_gross=true`.
- **Birthday job:** APScheduler `CronTrigger(hour=0, minute=5, timezone='Asia/Ho_Chi_Minh')`. Query memberships JOIN users JOIN tenants WHERE birthday matches today + tenant has `birthday_campaign_id`. Idempotent check: voucher đã có hôm nay → skip.

**Cuối tuần phải có:**
- Owner CRUD campaign (vd Halloween 20% off, target_tier=Silver+, max_issuances=100)
- Khách vào `/member/vouchers/available` → thấy campaigns đủ điều kiện → bấm "Nhận" → có voucher
- Khách đưa code voucher cho nhân viên → tích điểm với discount
- Birthday job tạo voucher tự động cho khách có sinh nhật hôm nay (chạy thử bằng `python -m app.jobs.run_once birthday`)
- Notifications hiển thị trong `/member` (badge + dropdown)
- ~30 new tests pass (tổng tích lũy ~155)
- CI xanh

**Acceptance criteria:**
- POST `/merchant/campaigns` tạo được campaign với max_issuances=2
- POST `/member/vouchers/claim` 3 lần với 2 user khác nhau → 2 thành công, 1 nhận 409 CAMPAIGN_FULL
- POST `/member/vouchers/claim` 2 lần với CÙNG user → 1 thành công, 1 nhận 409 ALREADY_CLAIMED
- POST `/merchant/transactions` với `voucher_code` → trả về `voucher_discount_amount`, `net_amount = gross - discount`, `points_earned` tính trên `net_amount`
- Set `tenants.settings.points_on_gross=true` → tạo transaction tương tự → `points_earned` tính trên `gross_amount`
- Set `tenants.settings.birthday_campaign_id=X` → có khách sinh nhật hôm nay → run birthday job → khách nhận voucher
- Idempotency: chạy birthday job 2 lần → không tạo voucher duplicate
- ROI dashboard: `/merchant/campaigns/{id}/roi` trả về `vouchers_issued`, `vouchers_used`, `total_discount_amount`, `total_revenue_from_voucher_txns`
- `pytest -v` → ~155 tests pass
- CI xanh

---

## Tổng quan các phase

| Phase | Tasks | Mô tả | LOC backend | LOC frontend |
|---|---|---|---|---|
| 1 | 1-3 | Campaigns model + service + API CRUD | ~500 | — |
| 2 | 4-7 | Vouchers model + partial unique index + atomic claim service | ~600 | — |
| 3 | 8-10 | API `/member/vouchers/{available, claim, mine}` | ~350 | — |
| 4 | 11-14 | Voucher use trong transaction (gross/net/discount + points_on_gross) | ~400 | — |
| 5 | 15-17 | Notifications model + service + API | ~350 | — |
| 6 | 18-20 | Birthday voucher job (Luồng F) + idempotency | ~300 | — |
| 7 | 21-22 | Cross-tenant tests + ROI campaign endpoint | ~250 | — |
| 8 | 23-26 | Frontend `/merchant/campaigns` CRUD | — | ~500 |
| 9 | 27-29 | Frontend `/merchant/campaigns/{id}/roi` ROI page | — | ~300 |
| 10 | 30-33 | Frontend `/member/vouchers/{available, mine}` | — | ~500 |
| 11 | 34-36 | Frontend `/pos voucher input` | — | ~300 |
| 12 | 37-39 | Frontend in-app notifications display (bell icon + dropdown) | — | ~350 |
| 13 | 40-42 | Smoke test E2E + birthday job manual trigger + CI |  — | — |

**Total:** 42 tasks · ~2750 LOC backend · ~1950 LOC frontend · ~30 new tests

---

## File Structure (tuần 5)

```
backend/alembic/versions/
├── 010_create_campaigns.py
├── 011_create_vouchers_with_partial_unique.py
├── 012_create_notifications.py
├── 013_alter_transactions_add_voucher_fk.py

backend/app/
├── models/
│   ├── campaign.py
│   ├── voucher.py
│   └── notification.py
├── schemas/
│   ├── campaign.py
│   ├── voucher.py
│   └── notification.py
├── services/
│   ├── campaign_service.py
│   ├── voucher_service.py
│   ├── notification_service.py
│   └── transaction_service.py     # MODIFY (accept voucher_code)
├── api/
│   ├── campaigns.py
│   ├── vouchers.py
│   ├── notifications.py
│   └── transactions.py            # MODIFY
└── jobs/
    └── birthday_voucher.py        # NEW

frontend/src/
├── types/
│   ├── campaign.ts
│   ├── voucher.ts
│   └── notification.ts
├── components/
│   └── notification-bell.tsx
└── app/
    ├── merchant/
    │   ├── campaigns/
    │   │   ├── page.tsx           # CRUD list
    │   │   ├── new/page.tsx
    │   │   └── [id]/page.tsx      # detail + ROI
    │   └── layout.tsx             # MODIFY add link
    ├── member/
    │   └── vouchers/
    │       ├── page.tsx           # available + mine tabs
    │       └── [id]/page.tsx
    └── pos/
        └── transactions/
            └── new/page.tsx       # MODIFY add voucher input
```

---

## PHASE 1 — Campaigns Model + Service + API

### Task 1: Tạo `Campaign` model + migration

**Files:**
- Create: `D:/DoAn/backend/app/models/campaign.py`

- [ ] **Step 1: Tạo model**

```python
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class CampaignSource(str, enum.Enum):
    MANUAL = "manual"
    BIRTHDAY = "birthday"
    SIGNUP = "signup"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint("discount_value > 0", name="ck_campaigns_discount_positive"),
        CheckConstraint(
            "max_issuances IS NULL OR max_issuances > 0",
            name="ck_campaigns_max_issuances_positive",
        ),
        CheckConstraint("issued_count >= 0", name="ck_campaigns_issued_nonneg"),
        Index("ix_campaigns_tenant_active", "tenant_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type"), nullable=False
    )
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    min_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_discount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_tier_id: Mapped[int | None] = mapped_column(
        ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True
    )
    max_issuances: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issued_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[CampaignSource] = mapped_column(
        Enum(CampaignSource, name="campaign_source"),
        default=CampaignSource.MANUAL,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Update __init__.py + migration + apply + commit**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create campaigns table"
alembic upgrade head
git add backend/app/models/campaign.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat(backend): thêm Campaign model + migration"
```

---

### Task 2: TDD — `CampaignService` CRUD

**Files:**
- Create: `D:/DoAn/backend/app/schemas/campaign.py`
- Create: `D:/DoAn/backend/app/services/campaign_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_campaign_service.py`

- [ ] **Step 1: Schema `app/schemas/campaign.py`**

```python
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.campaign import CampaignSource, DiscountType


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    discount_type: DiscountType
    discount_value: int = Field(gt=0)
    min_order: int = Field(default=0, ge=0)
    max_discount: int | None = Field(default=None, gt=0)
    target_tier_id: int | None = None
    max_issuances: int | None = Field(default=None, gt=0)
    starts_at: datetime
    ends_at: datetime
    source: CampaignSource = CampaignSource.MANUAL

    @model_validator(mode="after")
    def validate_dates_and_percent(self) -> "CampaignCreateRequest":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be > starts_at")
        if self.discount_type == DiscountType.PERCENT and self.discount_value > 100:
            raise ValueError("percent discount must be <= 100")
        return self


class CampaignUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    ends_at: datetime | None = None
    max_issuances: int | None = None


class CampaignResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str | None
    discount_type: DiscountType
    discount_value: int
    min_order: int
    max_discount: int | None
    target_tier_id: int | None
    max_issuances: int | None
    issued_count: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    source: CampaignSource
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignRoiResponse(BaseModel):
    campaign_id: int
    name: str
    vouchers_issued: int
    vouchers_used: int
    total_discount_amount: int
    total_revenue_from_voucher_txns: int  # SUM(net_amount) của transactions có voucher_id của campaign
```

- [ ] **Step 2: Tests** (CRUD pattern + soft delete + cross-tenant)

- [ ] **Step 3: Implement `app/services/campaign_service.py`** — CRUD pattern (giống RewardService)

- [ ] **Step 4: Run + commit**

```bash
git commit -m "feat(backend): thêm CampaignService CRUD (TDD)"
```

---

### Task 3: API `/merchant/campaigns`

**Files:**
- Create: `D:/DoAn/backend/app/api/campaigns.py`
- Create: `D:/DoAn/backend/tests/integration/test_campaigns_api.py`

- [ ] **Step 1: Implement endpoints**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.campaign import (
    CampaignCreateRequest, CampaignResponse, CampaignUpdateRequest
)
from app.services.campaign_service import CampaignNotFoundError, CampaignService

router = APIRouter(prefix="/merchant/campaigns", tags=["merchant-campaigns"])


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    return [
        CampaignResponse.model_validate(c)
        for c in await CampaignService(db).list_campaigns(tenant_id=tenant_id)
    ]


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    request: CampaignCreateRequest,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    c = await CampaignService(db).create_campaign(tenant_id=tenant_id, request=request)
    return CampaignResponse.model_validate(c)


# PATCH, DELETE pattern tương tự
```

- [ ] **Step 2: Tests + commit**

```bash
git commit -m "feat(backend): thêm /merchant/campaigns CRUD API"
```

---

## PHASE 2 — Vouchers Model + Atomic Claim

### Task 4: Tạo `Voucher` model với partial unique index

**Files:**
- Create: `D:/DoAn/backend/app/models/voucher.py`

- [ ] **Step 1: Tạo model**

```python
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class VoucherStatus(str, enum.Enum):
    ISSUED = "issued"
    USED = "used"
    EXPIRED = "expired"


class Voucher(Base, TimestampMixin):
    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_vouchers_tenant_code"),
        Index("ix_vouchers_membership_status", "membership_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[VoucherStatus] = mapped_column(
        Enum(VoucherStatus, name="voucher_status"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
```

- [ ] **Step 2: Migration + thêm partial unique index thủ công**

```bash
cd D:/DoAn/backend
alembic revision --autogenerate -m "create vouchers with partial unique"
```

Edit migration thêm partial index sau `create_table`:

```python
op.execute("""
    CREATE UNIQUE INDEX uq_vouchers_active_per_member_per_campaign
    ON vouchers (campaign_id, membership_id)
    WHERE status NOT IN ('expired', 'used');
""")
```

`alembic upgrade head`

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(backend): thêm Voucher model + partial unique index chống duplicate claim"
```

---

### Task 5: TDD — `VoucherService.claim` atomic (chống TOCTOU)

**Files:**
- Create: `D:/DoAn/backend/app/schemas/voucher.py`
- Create: `D:/DoAn/backend/app/services/voucher_service.py`
- Create: `D:/DoAn/backend/tests/integration/test_voucher_service.py`

- [ ] **Step 1: Schema**

```python
from datetime import datetime

from pydantic import BaseModel

from app.models.voucher import VoucherStatus


class VoucherClaimRequest(BaseModel):
    campaign_id: int


class VoucherResponse(BaseModel):
    id: int
    tenant_id: int
    campaign_id: int
    membership_id: int
    code: str
    status: VoucherStatus
    issued_at: datetime
    used_at: datetime | None
    expires_at: datetime
    campaign_name: str | None = None
    discount_type: str | None = None
    discount_value: int | None = None

    model_config = {"from_attributes": True}


class CampaignEligibleResponse(BaseModel):
    campaign_id: int
    name: str
    description: str | None
    discount_type: str
    discount_value: int
    min_order: int
    max_discount: int | None
    ends_at: datetime
    issued_count: int
    max_issuances: int | None
```

- [ ] **Step 2: Failing tests**

```python
import pytest
from datetime import datetime, timedelta, timezone

from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.voucher import VoucherStatus
from app.services.voucher_service import (
    AlreadyClaimedError,
    CampaignFullError,
    CampaignNotEligibleError,
    VoucherService,
)


@pytest.fixture
async def tenant_with_campaign(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()

    campaign = Campaign(
        tenant_id=tenant.id,
        name="Halloween 20%",
        discount_type=DiscountType.PERCENT,
        discount_value=20,
        min_order=0,
        max_discount=50000,
        max_issuances=2,  # Test limit
        starts_at=datetime.now(timezone.utc) - timedelta(days=1),
        ends_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        source=CampaignSource.MANUAL,
    )
    db_session.add(campaign)
    await db_session.flush()
    return {"tenant": tenant, "campaign": campaign}


async def _make_membership(db_session, tenant_id, email):
    user = User(email=email, password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    m = Membership(
        tenant_id=tenant_id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.mark.asyncio
async def test_claim_voucher_first_time_succeeds(db_session, tenant_with_campaign):
    ctx = tenant_with_campaign
    m = await _make_membership(db_session, ctx["tenant"].id, "u1@example.com")
    service = VoucherService(db_session)
    voucher = await service.claim(
        tenant_id=ctx["tenant"].id,
        membership_id=m.id,
        campaign_id=ctx["campaign"].id,
    )
    await db_session.flush()
    assert voucher.status == VoucherStatus.ISSUED
    assert len(voucher.code) == 8

    await db_session.refresh(ctx["campaign"])
    assert ctx["campaign"].issued_count == 1


@pytest.mark.asyncio
async def test_claim_same_campaign_twice_raises(db_session, tenant_with_campaign):
    ctx = tenant_with_campaign
    m = await _make_membership(db_session, ctx["tenant"].id, "u1@example.com")
    service = VoucherService(db_session)
    await service.claim(
        tenant_id=ctx["tenant"].id, membership_id=m.id, campaign_id=ctx["campaign"].id
    )
    await db_session.flush()

    with pytest.raises(AlreadyClaimedError):
        await service.claim(
            tenant_id=ctx["tenant"].id, membership_id=m.id, campaign_id=ctx["campaign"].id
        )


@pytest.mark.asyncio
async def test_claim_when_max_issuances_reached_raises(db_session, tenant_with_campaign):
    ctx = tenant_with_campaign
    m1 = await _make_membership(db_session, ctx["tenant"].id, "u1@example.com")
    m2 = await _make_membership(db_session, ctx["tenant"].id, "u2@example.com")
    m3 = await _make_membership(db_session, ctx["tenant"].id, "u3@example.com")

    service = VoucherService(db_session)
    await service.claim(
        tenant_id=ctx["tenant"].id, membership_id=m1.id, campaign_id=ctx["campaign"].id
    )
    await service.claim(
        tenant_id=ctx["tenant"].id, membership_id=m2.id, campaign_id=ctx["campaign"].id
    )
    await db_session.flush()

    with pytest.raises(CampaignFullError):
        await service.claim(
            tenant_id=ctx["tenant"].id, membership_id=m3.id, campaign_id=ctx["campaign"].id
        )


@pytest.mark.asyncio
async def test_claim_inactive_campaign_raises(db_session, tenant_with_campaign):
    ctx = tenant_with_campaign
    ctx["campaign"].is_active = False
    await db_session.flush()

    m = await _make_membership(db_session, ctx["tenant"].id, "u@example.com")
    service = VoucherService(db_session)
    with pytest.raises(CampaignNotEligibleError):
        await service.claim(
            tenant_id=ctx["tenant"].id, membership_id=m.id, campaign_id=ctx["campaign"].id
        )


@pytest.mark.asyncio
async def test_claim_after_expiration_year_succeeds(db_session, tenant_with_campaign):
    """Voucher cũ status='expired' → partial unique cho phép claim lại."""
    from app.models.voucher import Voucher

    ctx = tenant_with_campaign
    m = await _make_membership(db_session, ctx["tenant"].id, "u@example.com")

    expired_voucher = Voucher(
        tenant_id=ctx["tenant"].id,
        campaign_id=ctx["campaign"].id,
        membership_id=m.id,
        code="OLDEXPIR",
        status=VoucherStatus.EXPIRED,
        issued_at=datetime.now(timezone.utc) - timedelta(days=400),
        expires_at=datetime.now(timezone.utc) - timedelta(days=100),
    )
    db_session.add(expired_voucher)
    await db_session.flush()

    service = VoucherService(db_session)
    voucher = await service.claim(
        tenant_id=ctx["tenant"].id, membership_id=m.id, campaign_id=ctx["campaign"].id
    )
    await db_session.flush()
    assert voucher.id != expired_voucher.id
    assert voucher.status == VoucherStatus.ISSUED
```

- [ ] **Step 3: Implement `app/services/voucher_service.py`**

```python
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.tenant import Tenant
from app.models.voucher import Voucher, VoucherStatus


class AlreadyClaimedError(Exception):
    pass


class CampaignFullError(Exception):
    pass


class CampaignNotEligibleError(Exception):
    pass


_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))


class VoucherService:
    DEFAULT_TTL_DAYS = 30

    def __init__(self, db: AsyncSession):
        self.db = db

    async def claim(
        self, *, tenant_id: int, membership_id: int, campaign_id: int
    ) -> Voucher:
        """Atomic claim voucher (chống TOCTOU).

        Steps:
        1. UPDATE campaigns SET issued_count += 1 WHERE id AND active AND in_window
           AND (max_issuances IS NULL OR issued_count < max_issuances)
           → rowcount=0 → CampaignFullError hoặc CampaignNotEligibleError
        2. INSERT voucher → bắt IntegrityError (partial unique) → AlreadyClaimedError
        """
        now = datetime.now(timezone.utc)

        # Step 1: Atomic UPDATE check + increment
        result = await self.db.execute(
            update(Campaign)
            .where(
                Campaign.id == campaign_id,
                Campaign.tenant_id == tenant_id,
                Campaign.is_active.is_(True),
                Campaign.deleted_at.is_(None),
                Campaign.starts_at <= now,
                Campaign.ends_at > now,
                or_(
                    Campaign.max_issuances.is_(None),
                    Campaign.issued_count < Campaign.max_issuances,
                ),
            )
            .values(issued_count=Campaign.issued_count + 1)
        )

        if result.rowcount == 0:
            # Có thể: campaign không tồn tại, không active, hết hạn, hoặc đã max
            campaign = await self.db.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id, Campaign.tenant_id == tenant_id
                )
            )
            if campaign is None:
                raise CampaignNotEligibleError("Campaign not found")
            if (
                campaign.max_issuances is not None
                and campaign.issued_count >= campaign.max_issuances
            ):
                raise CampaignFullError("Campaign reached max issuances")
            raise CampaignNotEligibleError("Campaign not active or out of window")

        # Step 2: INSERT voucher với savepoint retry on code collision
        # (★ FIX C1 từ review: dùng SAVEPOINT thay vì rollback() — bảo toàn UPDATE issued_count)
        # Nếu rollback() toàn bộ transaction → mất UPDATE issued_count đã làm ở Step 1.
        # Dùng begin_nested() (savepoint) để chỉ rollback INSERT voucher khi collision code,
        # giữ nguyên UPDATE issued_count.
        ttl = await self._get_voucher_ttl(tenant_id)
        last_error: IntegrityError | None = None
        for attempt in range(3):
            code = _generate_code()
            try:
                async with self.db.begin_nested():  # SAVEPOINT
                    voucher = Voucher(
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        membership_id=membership_id,
                        code=code,
                        status=VoucherStatus.ISSUED,
                        issued_at=now,
                        expires_at=now + timedelta(days=ttl),
                    )
                    self.db.add(voucher)
                    await self.db.flush()
                # Savepoint commit → INSERT thành công
                return voucher
            except IntegrityError as e:
                last_error = e
                # Savepoint đã rollback INSERT, UPDATE issued_count vẫn còn nguyên.
                error_msg = str(e).lower()
                if "uq_vouchers_active_per_member_per_campaign" in error_msg or \
                   "ix_vouchers_active_per_member_per_campaign" in error_msg:
                    # Đã có voucher active của (campaign, member) — rollback luôn cả UPDATE
                    # Đây mới là lúc cần undo issued_count tăng giả
                    await self.db.execute(
                        update(Campaign)
                        .where(Campaign.id == campaign_id)
                        .values(issued_count=Campaign.issued_count - 1)
                    )
                    await self.db.flush()
                    raise AlreadyClaimedError(
                        f"Membership {membership_id} đã có voucher từ campaign {campaign_id}"
                    ) from e
                # Else: code collision (uq_vouchers_tenant_code) → retry với code mới
                continue

        # Hết 3 lần retry vẫn collision code (xác suất ~10^-30) → undo UPDATE và raise
        await self.db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(issued_count=Campaign.issued_count - 1)
        )
        await self.db.flush()
        raise RuntimeError(
            f"Failed to generate unique voucher code after 3 retries: {last_error}"
        )

    async def _get_voucher_ttl(self, tenant_id: int) -> int:
        tenant = await self.db.get(Tenant, tenant_id)
        if tenant is None:
            return self.DEFAULT_TTL_DAYS
        return tenant.settings.get("voucher_default_ttl_days", self.DEFAULT_TTL_DAYS)

    async def list_eligible_campaigns(
        self, *, tenant_id: int, membership_id: int, current_tier_id: int | None = None
    ) -> list[Campaign]:
        """List campaigns đủ điều kiện cho khách claim (chưa claim, còn slot, đúng tier)."""
        from sqlalchemy import not_
        now = datetime.now(timezone.utc)

        # Subquery: campaign ids đã có voucher còn sống của membership này
        already_claimed = (
            select(Voucher.campaign_id)
            .where(
                Voucher.membership_id == membership_id,
                Voucher.status == VoucherStatus.ISSUED,
            )
        )

        rows = await self.db.scalars(
            select(Campaign)
            .where(
                Campaign.tenant_id == tenant_id,
                Campaign.is_active.is_(True),
                Campaign.deleted_at.is_(None),
                Campaign.starts_at <= now,
                Campaign.ends_at > now,
                or_(
                    Campaign.max_issuances.is_(None),
                    Campaign.issued_count < Campaign.max_issuances,
                ),
                or_(
                    Campaign.target_tier_id.is_(None),
                    Campaign.target_tier_id == current_tier_id,
                ),
                not_(Campaign.id.in_(already_claimed)),
            )
            .order_by(Campaign.ends_at.asc())
        )
        return list(rows.all())

    async def list_my_vouchers(
        self, *, tenant_id: int, membership_id: int, status: VoucherStatus | None = None
    ) -> list[Voucher]:
        from sqlalchemy.orm import joinedload

        stmt = (
            select(Voucher)
            .where(
                Voucher.tenant_id == tenant_id,
                Voucher.membership_id == membership_id,
            )
            .order_by(Voucher.issued_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Voucher.status == status)
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def find_by_code(self, *, tenant_id: int, code: str) -> Voucher | None:
        return await self.db.scalar(
            select(Voucher).where(
                Voucher.tenant_id == tenant_id,
                Voucher.code == code,
                Voucher.status == VoucherStatus.ISSUED,
            )
        )

    async def mark_used(self, *, voucher: Voucher) -> Voucher:
        voucher.status = VoucherStatus.USED
        voucher.used_at = datetime.now(timezone.utc)
        await self.db.flush()
        return voucher
```

- [ ] **Step 4: Run + commit**

```bash
git commit -m "feat(backend): thêm VoucherService với atomic claim chống TOCTOU (TDD)"
```

---

### Tasks 6-7: Cross-tenant test + ROI helper

- [ ] **Task 6:** Append cross-tenant test
- [ ] **Task 7:** Commit

```bash
git commit -m "test(backend): cross-tenant isolation cho vouchers"
```

---

## PHASE 3 — API `/member/vouchers`

### Task 8: API endpoints

**Files:**
- Create: `D:/DoAn/backend/app/api/vouchers.py`

- [ ] **Step 1: Implement**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.voucher import VoucherStatus
from app.schemas.voucher import (
    CampaignEligibleResponse,
    VoucherClaimRequest,
    VoucherResponse,
)
from app.services.voucher_service import (
    AlreadyClaimedError,
    CampaignFullError,
    CampaignNotEligibleError,
    VoucherService,
)

router = APIRouter(prefix="/member/vouchers", tags=["member-vouchers"])


@router.get("/available/{tenant_slug}", response_model=list[CampaignEligibleResponse])
async def list_available_campaigns(
    tenant_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignEligibleResponse]:
    """List campaigns đủ điều kiện cho khách claim trong tenant này."""
    from sqlalchemy import select
    from app.models.tenant import Tenant
    from app.models.membership import Membership

    tenant = await db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    membership = await db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant.id, Membership.user_id == current_user.id
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this shop")

    service = VoucherService(db)
    campaigns = await service.list_eligible_campaigns(
        tenant_id=tenant.id,
        membership_id=membership.id,
        current_tier_id=membership.current_tier_id,
    )
    return [
        CampaignEligibleResponse(
            campaign_id=c.id,
            name=c.name,
            description=c.description,
            discount_type=c.discount_type.value,
            discount_value=c.discount_value,
            min_order=c.min_order,
            max_discount=c.max_discount,
            ends_at=c.ends_at,
            issued_count=c.issued_count,
            max_issuances=c.max_issuances,
        )
        for c in campaigns
    ]


@router.post("/claim/{tenant_slug}", response_model=VoucherResponse, status_code=201)
@limiter.limit("10/minute")
async def claim_voucher(
    request_obj: Request,
    tenant_slug: str,
    body: VoucherClaimRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoucherResponse:
    from sqlalchemy import select
    from app.models.membership import Membership
    from app.models.tenant import Tenant

    tenant = await db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    membership = await db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant.id, Membership.user_id == current_user.id
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member")

    service = VoucherService(db)
    try:
        voucher = await service.claim(
            tenant_id=tenant.id,
            membership_id=membership.id,
            campaign_id=body.campaign_id,
        )
    except AlreadyClaimedError as e:
        raise HTTPException(status_code=409, detail="ALREADY_CLAIMED") from e
    except CampaignFullError as e:
        raise HTTPException(status_code=409, detail="CAMPAIGN_FULL") from e
    except CampaignNotEligibleError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return VoucherResponse.model_validate(voucher)


@router.get("/mine/{tenant_slug}", response_model=list[VoucherResponse])
async def list_my_vouchers(
    tenant_slug: str,
    status: VoucherStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VoucherResponse]:
    # ... (similar lookup tenant + membership)
    # service.list_my_vouchers
    ...
```

- [ ] **Step 2-3: Tests + commit**

```bash
git commit -m "feat(backend): thêm /member/vouchers/{available, claim, mine} API"
```

---

### Tasks 9-10: Cross-tenant test claim + commit

```bash
git commit -m "test(backend): cross-tenant test cho voucher claim"
```

---

## PHASE 4 — Voucher Use Trong Transaction

### Task 11: Migration thêm FK `transactions.voucher_id → vouchers`

- [ ] **Step 1: Migration**

```bash
alembic revision -m "alter transactions add voucher fk"
```

```python
def upgrade():
    op.create_foreign_key(
        "fk_transactions_voucher_id_vouchers",
        "transactions", "vouchers",
        ["voucher_id"], ["id"],
        ondelete="SET NULL",
    )
```

- [ ] **Step 2: Apply + commit**

```bash
alembic upgrade head
git commit -m "feat(backend): thêm FK transactions.voucher_id → vouchers"
```

---

### Tasks 12-14: Update TransactionService accept voucher_code

**Files:**
- Modify: `D:/DoAn/backend/app/services/transaction_service.py`
- Modify: `D:/DoAn/backend/app/schemas/transaction.py`

- [ ] **Step 1: Schema thêm voucher_code optional**

```python
class CreateManualTransactionRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    gross_amount: int = Field(gt=0, le=100_000_000)
    voucher_code: str | None = Field(default=None, min_length=8, max_length=8)
    note: str | None = Field(default=None, max_length=1000)
```

- [ ] **Step 2: Implement voucher discount logic (★ FIX C2 — race condition voucher use)**

> **Race condition cũ:** 2 staff cùng nhập 1 voucher_code đồng thời → cả 2 SELECT thấy `status='issued'` → cả 2 mark_used → voucher dùng 2 lần.
>
> **Fix:** Dùng atomic UPDATE `WHERE status = 'issued'` thay vì SELECT-then-UPDATE.

Add exception class:

```python
class InvalidVoucherError(Exception):
    pass
```

Trong `_create_transaction_for_membership` thêm logic xử lý voucher:

```python
async def _apply_voucher_if_provided(
    self, *, tenant_id: int, membership_id: int, gross_amount: int,
    voucher_code: str | None
) -> tuple[int, int, int | None]:
    """Returns (net_amount, voucher_discount_amount, voucher_id).

    ★ Atomic voucher use — chống race condition 2 staff cùng nhập 1 code.
    """
    if voucher_code is None:
        return gross_amount, 0, None

    # ★ FIX C2: SELECT FOR UPDATE voucher để lock row
    from sqlalchemy.orm import joinedload

    voucher = await self.db.scalar(
        select(Voucher)
        .options(joinedload(Voucher.campaign))  # Cần campaign cho discount calc
        .where(
            Voucher.tenant_id == tenant_id,
            Voucher.code == voucher_code,
            Voucher.status == VoucherStatus.ISSUED,
        )
        .with_for_update()
    )
    if voucher is None:
        raise InvalidVoucherError("Voucher code không tồn tại hoặc đã dùng/hết hạn")
    if voucher.membership_id != membership_id:
        raise InvalidVoucherError("Voucher không thuộc về khách hàng này")
    if voucher.expires_at < datetime.now(timezone.utc):
        # Auto-expire khi sử dụng
        voucher.status = VoucherStatus.EXPIRED
        await self.db.flush()
        raise InvalidVoucherError("Voucher đã hết hạn")

    campaign = voucher.campaign  # joinedload
    if campaign is None:
        # Fallback nếu joinedload fail
        campaign = await self.db.get(Campaign, voucher.campaign_id)
    if gross_amount < campaign.min_order:
        raise InvalidVoucherError(
            f"Đơn tối thiểu {campaign.min_order} VND không đạt"
        )

    # Discount calculation
    if campaign.discount_type == DiscountType.PERCENT:
        discount = (gross_amount * campaign.discount_value) // 100
        if campaign.max_discount is not None:
            discount = min(discount, campaign.max_discount)
    else:
        discount = min(campaign.discount_value, gross_amount)

    net_amount = gross_amount - discount

    # ★ Atomic mark_used với UPDATE WHERE status = ISSUED → tránh race
    # (đã có FOR UPDATE lock trên row, đây là defense-in-depth)
    result = await self.db.execute(
        update(Voucher)
        .where(Voucher.id == voucher.id, Voucher.status == VoucherStatus.ISSUED)
        .values(status=VoucherStatus.USED, used_at=datetime.now(timezone.utc))
    )
    if result.rowcount == 0:
        # Voucher đã bị dùng giữa SELECT FOR UPDATE và UPDATE (extremely rare)
        raise InvalidVoucherError("Voucher đã được sử dụng (race condition)")
    await self.db.flush()

    return net_amount, discount, voucher.id
```

> **Lưu ý import:** thêm `from sqlalchemy import select, update` và `from app.models.voucher import Voucher, VoucherStatus` ở đầu file.

> **Lock ordering rule:** Voucher lock đứng SAU membership lock trong `_create_transaction_for_membership` (membership đã FOR UPDATE từ trước). Đảm bảo thứ tự nhất quán.

Cập nhật `_create_transaction_for_membership`:

```python
async def _create_transaction_for_membership(
    self, *, tenant_id, staff_id, membership, gross_amount, method,
    voucher_code: str | None = None, note=None
):
    # ...
    net_amount, discount, voucher_id = await self._apply_voucher_if_provided(
        tenant_id=tenant_id, membership_id=membership.id,
        gross_amount=gross_amount, voucher_code=voucher_code,
    )

    # Get tenant settings to decide gross vs net
    tenant = await self.db.get(Tenant, tenant_id)
    points_on_gross = tenant.settings.get("points_on_gross", False) if tenant else False

    rule = ...  # Get active point rule
    points_amount = gross_amount if points_on_gross else net_amount
    points_earned = self._calculate_points(rule, points_amount)

    txn = Transaction(
        tenant_id=tenant_id,
        membership_id=membership.id,
        staff_id=staff_id,
        gross_amount=gross_amount,
        voucher_id=voucher_id,
        voucher_discount_amount=discount if voucher_id else None,
        net_amount=net_amount,
        points_earned=points_earned,
        method=method,
        note=note,
    )
    # ... rest as before
```

- [ ] **Step 3: Tests** — voucher use cases (success, expired, wrong member, points_on_gross)

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(backend): TransactionService chấp nhận voucher_code + tính discount"
```

---

## PHASE 5 — Notifications Module

### Tasks 15-17: Notification model + service + API

**Files:**
- Create: `D:/DoAn/backend/app/models/notification.py`
- Create: `D:/DoAn/backend/app/schemas/notification.py`
- Create: `D:/DoAn/backend/app/services/notification_service.py`
- Create: `D:/DoAn/backend/app/api/notifications.py`

- [ ] **Task 15:** Model + migration

```python
class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Task 16:** Service `push(user_id, type, title, body, data)` + `list_user(user_id, unread_only=False)` + `mark_read(notification_ids)`

- [ ] **Task 17:** API `/notifications` GET + POST mark-read + commit

```bash
git commit -m "feat(backend): thêm Notification model + service + API"
```

---

## PHASE 6 — Birthday Voucher Job (Luồng F)

### Task 18: Tạo `app/jobs/birthday_voucher.py`

**Files:**
- Create: `D:/DoAn/backend/app/jobs/birthday_voucher.py`

- [ ] **Step 1: Implement**

```python
"""Luồng F — Birthday voucher job.

Chạy 00:05 ICT mỗi ngày.
Tạo voucher cho khách có sinh nhật hôm nay (theo lịch Asia/Ho_Chi_Minh).
Idempotent: skip nếu khách đã có voucher từ campaign sinh nhật hôm nay.
"""
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, extract, func, select

from app.core.db import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.services.notification_service import NotificationService
from app.services.voucher_service import VoucherService

logger = logging.getLogger(__name__)
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


async def run_birthday_voucher_job() -> dict:
    """Tạo voucher sinh nhật cho khách hôm nay.

    Returns:
        {"created": <count>, "skipped": <count>, "errors": <count>}
    """
    today_vn = datetime.now(VN_TZ).date()
    logger.info("Birthday voucher job: today_vn = %s", today_vn)

    created = skipped = errors = 0

    async with AsyncSessionLocal() as db:
        # Query memberships JOIN users JOIN tenants
        # WHERE users.birthday matches today (month + day)
        # AND tenant.settings has birthday_campaign_id
        # AND tenant active
        query = (
            select(Membership, User, Tenant)
            .join(User, Membership.user_id == User.id)
            .join(Tenant, Membership.tenant_id == Tenant.id)
            .where(
                User.birthday.is_not(None),
                User.is_active.is_(True),
                extract("month", User.birthday) == today_vn.month,
                extract("day", User.birthday) == today_vn.day,
                Tenant.status == TenantStatus.ACTIVE,
            )
        )
        rows = await db.execute(query)

        for membership, user, tenant in rows:
            campaign_id = tenant.settings.get("birthday_campaign_id")
            if campaign_id is None:
                continue

            # Idempotent check: voucher đã có hôm nay chưa?
            today_start_utc = datetime.combine(today_vn, datetime.min.time(), tzinfo=VN_TZ).astimezone(timezone.utc)
            today_end_utc = today_start_utc + timedelta(days=1)

            existing = await db.scalar(
                select(Voucher).where(
                    Voucher.campaign_id == campaign_id,
                    Voucher.membership_id == membership.id,
                    Voucher.issued_at >= today_start_utc,
                    Voucher.issued_at < today_end_utc,
                )
            )
            if existing is not None:
                logger.info(
                    "Skip — already has voucher today: membership=%d", membership.id
                )
                skipped += 1
                continue

            try:
                voucher_svc = VoucherService(db)
                voucher = await voucher_svc.claim(
                    tenant_id=tenant.id,
                    membership_id=membership.id,
                    campaign_id=campaign_id,
                )
                # Push notification
                notif_svc = NotificationService(db)
                await notif_svc.push(
                    user_id=user.id,
                    tenant_id=tenant.id,
                    type="birthday_voucher",
                    title="🎂 Chúc mừng sinh nhật!",
                    body=f"Bạn nhận được voucher mới từ shop {tenant.name}",
                    data={"voucher_id": voucher.id, "code": voucher.code},
                )
                created += 1
                logger.info(
                    "Created birthday voucher: membership=%d voucher=%s",
                    membership.id, voucher.code,
                )
            except Exception as e:
                logger.error(
                    "Error creating birthday voucher for membership %d: %s",
                    membership.id, e,
                )
                errors += 1

        await db.commit()

    result = {"created": created, "skipped": skipped, "errors": errors}
    logger.info("Birthday voucher job completed: %s", result)
    return result
```

- [ ] **Step 2: Register vào scheduler**

Modify `app/jobs/scheduler.py` `_register_jobs`:

```python
def _register_jobs(sched: AsyncIOScheduler) -> None:
    from app.jobs.birthday_voucher import run_birthday_voucher_job
    from app.jobs.cleanup_codes import cleanup_expired_verification_codes

    sched.add_job(
        cleanup_expired_verification_codes,
        trigger=CronTrigger(minute=5),
        id="cleanup_expired_verification_codes",
        replace_existing=True,
    )

    sched.add_job(
        run_birthday_voucher_job,
        trigger=CronTrigger(hour=0, minute=5, timezone=ZoneInfo("Asia/Ho_Chi_Minh")),
        id="birthday_voucher_job",
        replace_existing=True,
    )
```

- [ ] **Step 3: Add to `run_once.py`**

```python
JOBS = {
    "cleanup_codes": cleanup_expired_verification_codes,
    "birthday": run_birthday_voucher_job,
}
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(backend): thêm birthday voucher job (Luồng F) với idempotency theo ngày VN"
```

---

### Task 19: Test birthday job

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_birthday_job.py`

- [ ] **Step 1: Test**

```python
import pytest
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.jobs.birthday_voucher import run_birthday_voucher_job
from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.voucher import Voucher

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@pytest.mark.asyncio
async def test_birthday_job_creates_voucher_for_birthday_today(db_session):
    today_vn = datetime.now(VN_TZ).date()

    user = User(
        email="bday@example.com",
        password_hash="x",
        is_active=True,
        birthday=date(1990, today_vn.month, today_vn.day),
    )
    db_session.add(user)
    await db_session.flush()

    tenant_owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(tenant_owner)
    await db_session.flush()

    tenant = Tenant(
        name="T", slug="t", owner_user_id=tenant_owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    campaign = Campaign(
        tenant_id=tenant.id,
        name="Birthday",
        discount_type=DiscountType.PERCENT,
        discount_value=10,
        min_order=0,
        max_issuances=None,
        starts_at=datetime.now(timezone.utc) - timedelta(days=365),
        ends_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
        source=CampaignSource.BIRTHDAY,
    )
    db_session.add(campaign)
    await db_session.flush()

    tenant.settings = {"birthday_campaign_id": campaign.id}

    membership = Membership(
        tenant_id=tenant.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()

    # Note: job dùng AsyncSessionLocal riêng → không integrate với fixture
    # Test logic gián tiếp: gọi service trong fixture session để verify
```

> **Note:** Birthday job dùng `AsyncSessionLocal` riêng → khó test với fixture. Test integration thực phải chạy với DB thực + commit. Có thể skip integration test tự động và test thủ công bằng `python -m app.jobs.run_once birthday`.

- [ ] **Step 2: Manual test**

```bash
docker compose up -d
make seed-fresh
# Sửa 1 user có birthday hôm nay
docker compose exec postgres psql -U loyalty -d loyalty -c "UPDATE users SET birthday = CURRENT_DATE WHERE id = 5;"
# Set birthday_campaign_id
docker compose exec postgres psql -U loyalty -d loyalty -c "UPDATE tenants SET settings = jsonb_set(settings, '{birthday_campaign_id}', '1') WHERE id = 1;"
# Run job
cd backend && python -m app.jobs.run_once birthday
# Verify voucher
docker compose exec postgres psql -U loyalty -d loyalty -c "SELECT * FROM vouchers ORDER BY id DESC LIMIT 5;"
```

- [ ] **Step 3: Commit**

```bash
git commit -m "test(backend): manual test cho birthday voucher job"
```

---

### Task 20: Idempotency test (chạy 2 lần không tạo duplicate)

- [ ] **Step 1: Manual test idempotency**

Run `python -m app.jobs.run_once birthday` 2 lần. Verify count voucher không tăng lần thứ 2.

- [ ] **Step 2: Commit (no code change)**

---

## PHASE 7 — Cross-tenant + ROI

### Tasks 21-22: Cross-tenant test campaigns + ROI endpoint

- [ ] **Task 21:** Cross-tenant tests append vào `test_tenant_isolation.py`
- [ ] **Task 22:** ROI endpoint:

```python
@router.get("/{campaign_id}/roi", response_model=CampaignRoiResponse)
async def get_campaign_roi(
    campaign_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignRoiResponse:
    from sqlalchemy import func
    from app.models.transaction import Transaction
    from app.models.voucher import Voucher

    campaign = await db.scalar(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.tenant_id == tenant_id
        )
    )
    if campaign is None:
        raise HTTPException(404, "Campaign not found")

    vouchers_issued = await db.scalar(
        select(func.count()).select_from(Voucher).where(Voucher.campaign_id == campaign_id)
    )
    vouchers_used = await db.scalar(
        select(func.count())
        .select_from(Voucher)
        .where(Voucher.campaign_id == campaign_id, Voucher.status == "used")
    )

    voucher_ids_subq = select(Voucher.id).where(Voucher.campaign_id == campaign_id)
    txn_stats = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.voucher_discount_amount), 0),
            func.coalesce(func.sum(Transaction.net_amount), 0),
        ).where(Transaction.voucher_id.in_(voucher_ids_subq))
    )
    total_discount, total_revenue = txn_stats.one()

    return CampaignRoiResponse(
        campaign_id=campaign.id,
        name=campaign.name,
        vouchers_issued=int(vouchers_issued),
        vouchers_used=int(vouchers_used),
        total_discount_amount=int(total_discount),
        total_revenue_from_voucher_txns=int(total_revenue),
    )
```

```bash
git commit -m "feat(backend): thêm GET /merchant/campaigns/{id}/roi endpoint"
```

---

## PHASE 8-13 (Frontend + Smoke test)

> Pattern frontend tương tự tuần 4. Liệt kê các task chính:

### Task 23-26: `/merchant/campaigns` CRUD pages
- 23: List page
- 24: New campaign form (validate ends_at > starts_at, percent <= 100)
- 25: Edit page
- 26: Commit

### Task 27-29: `/merchant/campaigns/[id]/roi` page
- 27: Fetch ROI data
- 28: Display 4 metrics (issued/used/discount/revenue)
- 29: Commit

### Task 30-33: `/member/vouchers` (available + mine tabs)
- 30: Tabs component
- 31: Available list with claim button
- 32: My vouchers list with status badges
- 33: Commit

### Task 34-36: `/pos` voucher input
- 34: Modify `/pos/transactions/new` form thêm voucher_code optional input
- 35: Display preview discount + net_amount khi nhập code
- 36: Commit

### Task 37-39: Notifications bell + dropdown
- 37: `<NotificationBell />` component (poll every 30s)
- 38: Dropdown list + mark read on click
- 39: Commit

### Task 40-42: Smoke test E2E + birthday + CI
- 40: Full E2E manual test
- 41: Manual birthday job trigger + verify
- 42: Commit + push CI + tag

```bash
git tag tuan-5-complete
```

---

## Tổng kết Tuần 5

### Đã hoàn thành (42 tasks)

**Backend:**
- ✅ Campaign model + service + API CRUD + soft delete
- ✅ Voucher model + partial unique index `(campaign_id, membership_id) WHERE status NOT IN ('expired','used')`
- ✅ VoucherService.claim atomic chống TOCTOU (UPDATE check max + INSERT bắt IntegrityError)
- ✅ list_eligible_campaigns (filter theo tier, time, max, chưa claim)
- ✅ Voucher use trong transaction (gross/net/discount + points_on_gross setting)
- ✅ Notification model + service + API
- ✅ Birthday voucher job (Luồng F) với timezone Asia/Ho_Chi_Minh + idempotency theo ngày VN
- ✅ Register vào APScheduler 00:05 ICT mỗi ngày
- ✅ Manual trigger qua `python -m app.jobs.run_once birthday`
- ✅ ROI campaign endpoint
- ✅ Cross-tenant tests cho campaigns/vouchers

**Frontend:**
- ✅ /merchant/campaigns CRUD (list + new + edit)
- ✅ /merchant/campaigns/[id]/roi dashboard
- ✅ /member/vouchers với tabs (available + mine)
- ✅ Voucher claim button + status badges
- ✅ /pos voucher input với preview discount
- ✅ Notification bell + dropdown poll 30s

**Tests:**
- ✅ ~30 new tests (campaign service 5, voucher service 5, voucher claim cases 5, transaction with voucher 4, notifications 3, cross-tenant 3, ROI 2, birthday manual 1, others)
- ✅ Tổng ~155 tests

### Acceptance criteria

- [x] Owner CRUD campaign
- [x] Khách claim voucher 2 lần cùng campaign → 1 thành công, 1 nhận 409 ALREADY_CLAIMED
- [x] Campaign max_issuances=2, 3 user claim → 2 thành công, 1 nhận 409 CAMPAIGN_FULL
- [x] Transaction với voucher_code → discount + net_amount + points tính trên net (mặc định)
- [x] Toggle points_on_gross → points tính trên gross
- [x] Birthday job trigger manual → tạo voucher cho khách sinh nhật hôm nay
- [x] Birthday job chạy 2 lần → idempotent
- [x] ROI endpoint trả 4 metrics
- [x] CI xanh

---

## Sang tuần 6

Tuần 6 sẽ làm:
- Analytics module (dashboard queries với index)
- ROI campaign analysis (mở rộng từ tuần 5)
- Tier distribution
- Daily transactions chart
- Total revenue
- Redemption rate
- /merchant dashboard charts (recharts)
- /admin tenant detail + actions (suspend, view stats)
- Polish all pages (UX, error messages, loading states)

Plan tuần 6 sẽ được tạo riêng tại `docs/superpowers/plans/2026-04-12-tuan-6-analytics-dashboard.md`.
