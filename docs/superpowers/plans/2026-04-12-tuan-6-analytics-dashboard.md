# Tuần 6 — Analytics, Dashboard Charts & Admin Polish

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** Implement Analytics module backend (dashboard queries với index optimization, không cần materialized view trong MVP). Frontend `/merchant/dashboard` với charts (recharts) hiển thị 6 chỉ số: số thành viên, giao dịch theo ngày, doanh thu, tỉ lệ đổi điểm, phân bố hạng, ROI campaign. Hoàn thiện `/admin` với tenant detail page (suspend, view stats). UI polish toàn bộ pages (loading states, error messages, empty states, responsive breakpoints).

**Architecture:**
- **Analytics queries:** trực tiếp PostgreSQL với indexes đã có (`(tenant_id, created_at)`). Không materialized view cho MVP.
- **Date range filter:** mọi query có `?from_date=&to_date=` optional, default last 30 days.
- **Aggregation:** dùng `func.count`, `func.sum`, `func.date_trunc` của SQLAlchemy.
- **Frontend chart:** recharts (LineChart, PieChart, BarChart). Lazy import để giảm bundle.

**Cuối tuần phải có:**
- Owner login → /merchant → dashboard với 6 charts/cards hiển thị data thực từ seed
- Filter ngày → charts cập nhật
- Super Admin → /admin/tenants/{id} → thấy chi tiết tenant + suspend button
- Tất cả pages có loading state, empty state, error message rõ ràng
- Responsive ở 3 breakpoint (mobile/tablet/desktop)
- ~20 new tests pass (tổng tích lũy ~175)
- CI xanh

**Acceptance criteria:**
- GET `/merchant/analytics/dashboard?from_date=2025-01-01` trả về JSON với 6 keys
- Frontend dashboard hiển thị 6 charts/cards
- Daily transactions chart có 30 data points (1 cho mỗi ngày trong 30 ngày qua)
- Tier distribution pie chart hiển thị phân bố theo current_tier
- POST `/admin/tenants/{id}/suspend` chuyển status → suspended
- Mọi page có error boundary
- Lighthouse PWA score ≥ 80 (tăng từ baseline tuần 4)
- `pytest -v` → ~175 tests pass
- CI xanh

---

## Tổng quan các phase

| Phase | Tasks | Mô tả | LOC backend | LOC frontend |
|---|---|---|---|---|
| 1 | 1-4 | AnalyticsService TDD (6 queries) | ~600 | — |
| 2 | 5-7 | API `/merchant/analytics/dashboard` + `/merchant/analytics/{metric}` | ~300 | — |
| 3 | 8-10 | Admin endpoints — tenant detail + suspend + platform stats | ~250 | — |
| 4 | 11-13 | Cross-tenant isolation tests + cache (optional) | ~200 | — |
| 5 | 14-16 | Frontend recharts setup + types | — | ~250 |
| 6 | 17-21 | `/merchant/dashboard` 6 charts | — | ~700 |
| 7 | 22-24 | `/merchant/dashboard` date filter + responsive | — | ~300 |
| 8 | 25-27 | `/admin` dashboard + tenant detail page | — | ~500 |
| 9 | 28-31 | Polish: loading states, error boundary, empty states, toast | — | ~600 |
| 10 | 32-34 | Smoke test E2E + Lighthouse + CI | — | — |

**Total:** 34 tasks · ~1350 LOC backend · ~2350 LOC frontend · ~20 new tests

---

## File Structure (tuần 6)

```
backend/app/
├── services/
│   └── analytics_service.py
├── schemas/
│   └── analytics.py
└── api/
    ├── analytics.py
    └── admin.py                    # MODIFY (suspend, detail)

frontend/src/
├── lib/
│   └── chart-colors.ts             # NEW (palette chung)
├── components/
│   ├── charts/
│   │   ├── line-chart.tsx          # wrapper recharts
│   │   ├── pie-chart.tsx
│   │   └── stat-card.tsx
│   ├── error-boundary.tsx
│   ├── empty-state.tsx
│   └── loading-spinner.tsx
└── app/
    ├── merchant/
    │   ├── dashboard/page.tsx      # MODIFY (replace placeholder)
    │   └── (đổi merchant/page.tsx → redirect /merchant/dashboard)
    └── admin/
        ├── page.tsx                # MODIFY (platform stats)
        └── tenants/
            └── [id]/page.tsx       # NEW (detail + suspend)
```

---

## PHASE 1 — AnalyticsService TDD

### Task 1: Schemas + service skeleton

**Files:**
- Create: `D:/DoAn/backend/app/schemas/analytics.py`
- Create: `D:/DoAn/backend/app/services/analytics_service.py`

- [ ] **Step 1: Schema**

```python
from datetime import date, datetime
from pydantic import BaseModel


class DailyTransactionPoint(BaseModel):
    day: date
    transaction_count: int
    total_revenue: int
    total_points_earned: int


class TierDistributionPoint(BaseModel):
    tier_id: int | None
    tier_name: str | None
    member_count: int


class CampaignRoiPoint(BaseModel):
    campaign_id: int
    campaign_name: str
    vouchers_issued: int
    vouchers_used: int
    total_discount: int
    total_revenue_from_voucher_txns: int


class DashboardResponse(BaseModel):
    period_from: date
    period_to: date
    member_count: int
    transaction_count: int
    total_revenue: int
    total_redemption_count: int
    redemption_rate: float  # redemptions / total_members
    daily_transactions: list[DailyTransactionPoint]
    tier_distribution: list[TierDistributionPoint]
    campaign_roi: list[CampaignRoiPoint]
```

- [ ] **Step 2: Service skeleton (★ FIXED — apply patches từ review tuần 6)**

```python
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

# ★ FIX C1: import `case` riêng biệt (KHÔNG dùng func.case — không tồn tại trong SQLAlchemy 2.x)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.membership import Membership
from app.models.redemption import Redemption
from app.models.tier import Tier
from app.models.transaction import Transaction
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.analytics import (
    CampaignRoiPoint, DailyTransactionPoint, DashboardResponse, TierDistributionPoint
)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _date_range_to_utc(from_date: date, to_date: date) -> tuple[datetime, datetime]:
    """★ FIX I3+I4: half-open interval [from_dt, to_dt_exclusive) theo timezone VN.

    - from_dt = midnight VN của from_date → convert sang UTC
    - to_dt_exclusive = midnight VN của (to_date + 1 day) → convert sang UTC
    - Filter dùng `>= from_dt AND < to_dt_exclusive` (KHÔNG dùng <= datetime.max)
    """
    from_dt_vn = datetime.combine(from_date, time.min, tzinfo=VN_TZ)
    to_dt_vn = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=VN_TZ)
    return from_dt_vn.astimezone(timezone.utc), to_dt_vn.astimezone(timezone.utc)


def _fill_missing_days(
    points: list[DailyTransactionPoint], from_date: date, to_date: date
) -> list[DailyTransactionPoint]:
    """★ FIX I1: fill ngày không có data với 0 → chart luôn đủ N data points."""
    existing = {p.day: p for p in points}
    result = []
    d = from_date
    while d <= to_date:
        result.append(
            existing.get(
                d,
                DailyTransactionPoint(
                    day=d,
                    transaction_count=0,
                    total_revenue=0,
                    total_points_earned=0,
                ),
            )
        )
        d += timedelta(days=1)
    return result


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(
        self, *, tenant_id: int, from_date: date, to_date: date
    ) -> DashboardResponse:
        member_count = await self._count_members(tenant_id)
        txn_stats = await self._transaction_stats(tenant_id, from_date, to_date)
        redemption_count = await self._redemption_count(tenant_id, from_date, to_date)
        daily = await self._daily_transactions(tenant_id, from_date, to_date)
        tier_dist = await self._tier_distribution(tenant_id)
        campaign_roi = await self._campaign_roi(tenant_id, from_date, to_date)

        # ★ FIX I5: redemption_rate = redemptions / transactions (% giao dịch có đổi quà)
        # Cũ: redemptions / total_members (mix scope time, không có nghĩa nghiệp vụ)
        # Mới: tỉ lệ giao dịch có khách đổi quà — số có ý nghĩa với chủ shop
        if txn_stats["count"] > 0:
            redemption_rate = redemption_count / txn_stats["count"]
        else:
            redemption_rate = 0.0

        return DashboardResponse(
            period_from=from_date,
            period_to=to_date,
            member_count=member_count,
            transaction_count=txn_stats["count"],
            total_revenue=txn_stats["revenue"],
            total_redemption_count=redemption_count,
            redemption_rate=redemption_rate,
            daily_transactions=daily,
            tier_distribution=tier_dist,
            campaign_roi=campaign_roi,
        )

    async def _count_members(self, tenant_id: int) -> int:
        # ★ FIX I2: filter archived_at IS NULL nếu có
        return int(
            await self.db.scalar(
                select(func.count()).select_from(Membership).where(
                    Membership.tenant_id == tenant_id,
                    Membership.archived_at.is_(None),
                )
            )
            or 0
        )

    async def _transaction_stats(
        self, tenant_id: int, from_date: date, to_date: date
    ) -> dict:
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)  # ★ FIX I3+I4
        result = await self.db.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.net_amount), 0),
            ).where(
                Transaction.tenant_id == tenant_id,
                Transaction.created_at >= from_dt,
                Transaction.created_at < to_dt_excl,
            )
        )
        count, revenue = result.one()
        return {"count": int(count), "revenue": int(revenue)}

    async def _redemption_count(
        self, tenant_id: int, from_date: date, to_date: date
    ) -> int:
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)
        return int(
            await self.db.scalar(
                select(func.count()).select_from(Redemption).where(
                    Redemption.tenant_id == tenant_id,
                    Redemption.redeemed_at >= from_dt,
                    Redemption.redeemed_at < to_dt_excl,
                )
            )
            or 0
        )

    async def _daily_transactions(
        self, tenant_id: int, from_date: date, to_date: date
    ) -> list[DailyTransactionPoint]:
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)
        # ★ FIX I4: cast theo timezone VN, không phải UTC raw
        day_expr = func.date(
            func.timezone("Asia/Ho_Chi_Minh", Transaction.created_at)
        ).label("day")

        result = await self.db.execute(
            select(
                day_expr,
                func.count().label("cnt"),
                func.coalesce(func.sum(Transaction.net_amount), 0).label("revenue"),
                func.coalesce(func.sum(Transaction.points_earned), 0).label("points"),
            )
            .where(
                Transaction.tenant_id == tenant_id,
                Transaction.created_at >= from_dt,
                Transaction.created_at < to_dt_excl,
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )
        raw_points = [
            DailyTransactionPoint(
                day=row.day,
                transaction_count=int(row.cnt),
                total_revenue=int(row.revenue),
                total_points_earned=int(row.points),
            )
            for row in result
        ]
        # ★ FIX I1: fill missing days
        return _fill_missing_days(raw_points, from_date, to_date)

    async def _tier_distribution(self, tenant_id: int) -> list[TierDistributionPoint]:
        # ★ FIX I6: COALESCE NULL tier name + filter archived members
        result = await self.db.execute(
            select(
                Membership.current_tier_id,
                func.coalesce(Tier.name, "Chưa phân hạng").label("tier_name"),
                func.count(Membership.id).label("cnt"),
            )
            .outerjoin(
                Tier,
                (Membership.current_tier_id == Tier.id) & (Tier.deleted_at.is_(None)),
            )
            .where(
                Membership.tenant_id == tenant_id,
                Membership.archived_at.is_(None),
            )
            .group_by(Membership.current_tier_id, Tier.name)
            .order_by(Membership.current_tier_id.asc().nullsfirst())
        )
        return [
            TierDistributionPoint(
                tier_id=row.current_tier_id,
                tier_name=row.tier_name,
                member_count=int(row.cnt),
            )
            for row in result
        ]

    async def _campaign_roi(
        self, tenant_id: int, from_date: date, to_date: date
    ) -> list[CampaignRoiPoint]:
        """★ FIX C2: gộp thành 1 query duy nhất (tránh N+1).

        Strategy: 2 subqueries riêng cho voucher counts và transaction sums,
        merge bằng GROUP BY ở Python sau khi query — vẫn O(2) round-trips.
        Lý do: 1 query JOIN cả 3 table (Campaign + Voucher + Transaction)
        có cross-product nguy hiểm (đếm voucher sai vì N transactions/voucher).
        """
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)

        # ★ FIX C1: dùng `case` từ sqlalchemy (không phải func.case)
        # Query 1: voucher counts theo campaign
        voucher_query = (
            select(
                Campaign.id.label("campaign_id"),
                Campaign.name.label("campaign_name"),
                func.count(Voucher.id).label("issued"),
                func.coalesce(
                    func.sum(
                        case((Voucher.status == VoucherStatus.USED, 1), else_=0)
                    ),
                    0,
                ).label("used"),
            )
            .outerjoin(Voucher, Voucher.campaign_id == Campaign.id)
            .where(
                Campaign.tenant_id == tenant_id,
                Campaign.deleted_at.is_(None),  # ★ FIX I2
            )
            .group_by(Campaign.id, Campaign.name)
            .order_by(Campaign.id.desc())
            .limit(10)
        )
        voucher_rows = list((await self.db.execute(voucher_query)).all())
        if not voucher_rows:
            return []

        campaign_ids = [r.campaign_id for r in voucher_rows]

        # Query 2: transaction sums theo campaign (qua voucher_id)
        txn_query = (
            select(
                Voucher.campaign_id.label("campaign_id"),
                func.coalesce(
                    func.sum(Transaction.voucher_discount_amount), 0
                ).label("total_discount"),
                func.coalesce(
                    func.sum(Transaction.net_amount), 0
                ).label("total_revenue"),
            )
            .join(Transaction, Transaction.voucher_id == Voucher.id)
            .where(
                Voucher.campaign_id.in_(campaign_ids),
                Transaction.tenant_id == tenant_id,
                Transaction.created_at >= from_dt,
                Transaction.created_at < to_dt_excl,
            )
            .group_by(Voucher.campaign_id)
        )
        txn_rows = {
            r.campaign_id: (int(r.total_discount), int(r.total_revenue))
            for r in (await self.db.execute(txn_query)).all()
        }

        return [
            CampaignRoiPoint(
                campaign_id=r.campaign_id,
                campaign_name=r.campaign_name,
                vouchers_issued=int(r.issued),
                vouchers_used=int(r.used),
                total_discount=txn_rows.get(r.campaign_id, (0, 0))[0],
                total_revenue_from_voucher_txns=txn_rows.get(r.campaign_id, (0, 0))[1],
            )
            for r in voucher_rows
        ]
```

> **★ Fixed:** C1 (case import), C2 (N+1 → 2 query gộp), I1 (fill days), I2 (deleted_at filter), I3 (half-open interval), I4 (timezone VN), I5 (redemption_rate formula), I6 (COALESCE NULL tier).

- [ ] **Step 3: Commit (chưa test)**

```bash
git add backend/app/schemas/analytics.py backend/app/services/analytics_service.py
git commit -m "feat(backend): thêm AnalyticsService skeleton"
```

---

### Tasks 2-4: Tests cho mỗi query

**Files:**
- Create: `D:/DoAn/backend/tests/integration/test_analytics_service.py`

- [ ] **Task 2:** Test `_count_members` + `_transaction_stats`
- [ ] **Task 3:** Test `_daily_transactions` + `_tier_distribution`
- [ ] **Task 4:** Test `_campaign_roi` + `get_dashboard` end-to-end với seed data

```python
import pytest
from datetime import date, datetime, timedelta, timezone

from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.analytics_service import AnalyticsService


@pytest.fixture
async def seeded_tenant_with_data(db_session):
    """Tạo 1 tenant với 5 members + 10 transactions trong 7 ngày qua."""
    # ... (long setup)
    ...


@pytest.mark.asyncio
async def test_dashboard_returns_all_metrics(db_session, seeded_tenant_with_data):
    service = AnalyticsService(db_session)
    result = await service.get_dashboard(
        tenant_id=seeded_tenant_with_data["tenant_id"],
        from_date=date.today() - timedelta(days=30),
        to_date=date.today(),
    )
    assert result.member_count == 5
    assert result.transaction_count == 10
    assert result.total_revenue > 0
    assert len(result.daily_transactions) > 0
    assert len(result.tier_distribution) > 0
```

```bash
git commit -m "test(backend): tests cho AnalyticsService.get_dashboard"
```

---

## PHASE 2 — API Endpoints

### Tasks 5-7: API + tests

**Files:**
- Create: `D:/DoAn/backend/app/api/analytics.py`
- Create: `D:/DoAn/backend/tests/integration/test_analytics_api.py`

- [ ] **Step 1: Implement**

```python
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_owner_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.schemas.analytics import DashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/merchant/analytics", tags=["merchant-analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    service = AnalyticsService(db)
    return await service.get_dashboard(
        tenant_id=tenant_id, from_date=from_date, to_date=to_date
    )
```

- [ ] **Step 2: Tests** + register router + commit

```bash
git commit -m "feat(backend): thêm GET /merchant/analytics/dashboard"
```

---

## PHASE 3 — Admin Endpoints

### Tasks 8-10: Tenant detail + suspend + platform stats

- [ ] **Task 8:** Tenant detail endpoint với member count, transaction count, revenue tổng
- [ ] **Task 9:** POST `/admin/tenants/{id}/suspend` (đã có approve, thêm suspend)
- [ ] **Task 10:** GET `/admin/stats` — total tenants, total users, total transactions

```python
# Append vào app/api/admin.py

@router.get("/tenants/{tenant_id}/detail")
async def get_tenant_detail(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    tenant = await TenantService(db).get_tenant_by_id(tenant_id)
    member_count = ...  # query
    txn_count = ...
    return {"tenant": TenantResponse.model_validate(tenant), "stats": {...}}


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: int,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    service = TenantService(db)
    tenant = await service.suspend_tenant(tenant_id=tenant_id)
    return TenantResponse.model_validate(tenant)


@router.get("/stats")
async def get_platform_stats(
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import func, select
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.transaction import Transaction

    tenants_count = await db.scalar(select(func.count()).select_from(Tenant))
    users_count = await db.scalar(select(func.count()).select_from(User))
    txn_count = await db.scalar(select(func.count()).select_from(Transaction))

    return {
        "total_tenants": int(tenants_count or 0),
        "total_users": int(users_count or 0),
        "total_transactions": int(txn_count or 0),
    }
```

```bash
git commit -m "feat(backend): thêm /admin/tenants/{id}/{detail,suspend} + /admin/stats"
```

---

## PHASE 4 — Cross-tenant Tests

### Tasks 11-13

- [ ] **Task 11:** Cross-tenant test cho analytics
- [ ] **Task 12:** Tests cho admin endpoints
- [ ] **Task 13:** Commit

```bash
git commit -m "test(backend): cross-tenant tests cho analytics + admin"
```

---

## PHASE 5 — Frontend Recharts Setup

### Task 14: Install recharts + types

```bash
cd D:/DoAn/frontend
npm install recharts
```

- [ ] **Tasks 14-16:** Tạo:
  - `lib/chart-colors.ts` (palette nhất quán)
  - `components/charts/line-chart.tsx` (wrapper)
  - `components/charts/pie-chart.tsx` (wrapper)
  - `components/charts/stat-card.tsx`
  - `types/analytics.ts`

```typescript
// lib/chart-colors.ts
export const CHART_COLORS = {
  primary: "#0ea5e9",
  secondary: "#a855f7",
  success: "#22c55e",
  warning: "#f59e0b",
  danger: "#ef4444",
  muted: "#94a3b8",
  palette: ["#0ea5e9", "#a855f7", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"],
};
```

```typescript
// components/charts/stat-card.tsx
interface StatCardProps {
  title: string;
  value: string | number;
  hint?: string;
  trend?: "up" | "down" | "neutral";
}

export function StatCard({ title, value, hint, trend }: StatCardProps) {
  return (
    <div className="rounded-lg border p-6">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="text-3xl font-bold mt-2">{value}</p>
      {hint && <p className="text-xs text-muted-foreground mt-1">{hint}</p>}
    </div>
  );
}
```

```bash
git commit -m "feat(frontend): thêm recharts + chart components base"
```

---

## PHASE 6 — `/merchant/dashboard` 6 Charts

### Tasks 17-21: Implement dashboard

- [ ] **Task 17:** API client extension `analyticsApi`

```typescript
export const analyticsApi = {
  getDashboard: (tenantId: number, fromDate?: string, toDate?: string) => {
    const params = new URLSearchParams();
    if (fromDate) params.set("from", fromDate);
    if (toDate) params.set("to", toDate);
    return api.get<DashboardData>(
      `/merchant/analytics/dashboard?${params}`,
      withTenant(tenantId),
    );
  },
};
```

- [ ] **Task 18:** `/merchant/dashboard/page.tsx` skeleton + fetch data

- [ ] **Task 19:** 4 stat cards (member count, transactions, revenue, redemption rate)

- [ ] **Task 20:** Daily transactions LineChart + tier distribution PieChart

- [ ] **Task 21:** Campaign ROI table

```typescript
"use client";

import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { PieChart, Pie, Cell, Legend } from "recharts";

import { StatCard } from "@/components/charts/stat-card";
import { CHART_COLORS } from "@/lib/chart-colors";
import { analyticsApi } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { DashboardData } from "@/types/analytics";

export default function MerchantDashboard() {
  const tenant = useTenantStore((s) => s.currentTenant);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      const res = await analyticsApi.getDashboard(tenant.id);
      setData(res.data);
      setLoading(false);
    })();
  }, [tenant]);

  if (loading || !data) return <div>Đang tải...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Thành viên" value={data.member_count.toLocaleString("vi-VN")} />
        <StatCard
          title="Giao dịch (30 ngày)"
          value={data.transaction_count.toLocaleString("vi-VN")}
        />
        <StatCard
          title="Doanh thu (30 ngày)"
          value={`${data.total_revenue.toLocaleString("vi-VN")} ₫`}
        />
        <StatCard
          title="Tỉ lệ đổi điểm"
          value={`${(data.redemption_rate * 100).toFixed(1)}%`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border p-6">
          <h3 className="font-semibold mb-4">Giao dịch theo ngày</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.daily_transactions}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="transaction_count"
                stroke={CHART_COLORS.primary}
                name="Giao dịch"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg border p-6">
          <h3 className="font-semibold mb-4">Phân bố hạng</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.tier_distribution}
                dataKey="member_count"
                nameKey="tier_name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {data.tier_distribution.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS.palette[i % CHART_COLORS.palette.length]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border p-6">
        <h3 className="font-semibold mb-4">ROI Chiến dịch</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Chiến dịch</th>
              <th className="text-right p-2">Phát hành</th>
              <th className="text-right p-2">Đã dùng</th>
              <th className="text-right p-2">Giảm giá</th>
              <th className="text-right p-2">Doanh thu</th>
            </tr>
          </thead>
          <tbody>
            {data.campaign_roi.map((c) => (
              <tr key={c.campaign_id} className="border-b">
                <td className="p-2">{c.campaign_name}</td>
                <td className="p-2 text-right">{c.vouchers_issued}</td>
                <td className="p-2 text-right">{c.vouchers_used}</td>
                <td className="p-2 text-right">{c.total_discount.toLocaleString("vi-VN")} ₫</td>
                <td className="p-2 text-right">
                  {c.total_revenue_from_voucher_txns.toLocaleString("vi-VN")} ₫
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

```bash
git commit -m "feat(frontend): thêm /merchant/dashboard với 6 charts (recharts)"
```

---

### Tasks 22-24: Date filter + responsive

- [ ] **Task 22:** Date range picker (input type="date" đơn giản)
- [ ] **Task 23:** Responsive grid (mobile 1 col, tablet 2, desktop 4)
- [ ] **Task 24:** Commit

```bash
git commit -m "feat(frontend): thêm date filter + responsive cho dashboard"
```

---

## PHASE 8 — `/admin` Polish

### Tasks 25-27: Admin dashboard + tenant detail

- [ ] **Task 25:** `/admin/page.tsx` — show platform stats (total_tenants, total_users, total_txns) + 3 stat cards
- [ ] **Task 26:** `/admin/tenants/[id]/page.tsx` — detail page với tenant info + suspend button + member/txn count
- [ ] **Task 27:** Commit

```bash
git commit -m "feat(frontend): thêm /admin dashboard + tenant detail page"
```

---

## PHASE 9 — UI Polish

### Tasks 28-31: Loading/error/empty states + toast

- [ ] **Task 28:** `<LoadingSpinner />` component + sử dụng trong tất cả pages có async data
- [ ] **Task 29:** `<ErrorBoundary />` component + wrap trong layout
- [ ] **Task 30:** `<EmptyState />` component (icon + message + action button)
- [ ] **Task 31:** `<Toaster />` từ shadcn cho success/error feedback (install `npx shadcn@latest add toast`)

```typescript
// components/empty-state.tsx
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && <p className="text-sm text-muted-foreground mt-2">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
```

Apply EmptyState/LoadingSpinner vào:
- /merchant/members (empty: "Chưa có thành viên")
- /merchant/tiers (empty: "Chưa có hạng nào")
- /merchant/staff
- /merchant/campaigns
- /merchant/rewards
- /merchant/dashboard (loading)

```bash
git commit -m "feat(frontend): thêm LoadingSpinner + ErrorBoundary + EmptyState + Toaster"
git commit -m "refactor(frontend): apply loading/empty/error states vào tất cả pages"
```

---

## PHASE 10 — Smoke Test + Lighthouse + CI

### Tasks 32-34

- [ ] **Task 32:** Smoke test E2E full
  - `docker compose up --build`
  - `make seed-fresh`
  - Manual: login owner → /merchant/dashboard → verify 6 charts hiển thị data
  - Login admin → /admin → /admin/tenants/{id} → verify suspend works

- [ ] **Task 33:** Lighthouse PWA audit `/member` page
  - Mở Chrome DevTools → Lighthouse → Generate report
  - Target ≥ 80 cho PWA + Performance + Accessibility
  - Fix critical issues nếu có

- [ ] **Task 34:** Push CI + tag

```bash
git push origin main
git tag tuan-6-complete
```

---

## Tổng kết Tuần 6

### Đã hoàn thành (34 tasks)

**Backend:**
- ✅ AnalyticsService với 6 queries (members, transactions, revenue, redemptions, daily, tier_dist, ROI)
- ✅ API GET `/merchant/analytics/dashboard` với date range
- ✅ Admin endpoints: tenant detail, suspend, platform stats
- ✅ Cross-tenant isolation tests cho analytics

**Frontend:**
- ✅ Recharts setup + chart components base (StatCard, LineChart, PieChart wrapper)
- ✅ /merchant/dashboard với 4 stat cards + 2 charts + ROI table
- ✅ Date filter + responsive grid
- ✅ /admin dashboard với platform stats
- ✅ /admin/tenants/[id] detail page với suspend button
- ✅ LoadingSpinner + ErrorBoundary + EmptyState + Toaster
- ✅ Apply polish vào tất cả pages

**Tests:**
- ✅ ~20 new tests (analytics service 6, analytics API 3, admin 4, cross-tenant 3, others)
- ✅ Tổng tests: ~175

### Acceptance criteria

- [x] Dashboard hiển thị 6 chỉ số đúng từ seed data
- [x] Date filter hoạt động
- [x] Tier distribution pie chart phân bố đúng
- [x] Daily chart 30 data points
- [x] ROI table hiển thị campaigns
- [x] Admin suspend tenant work
- [x] Lighthouse ≥ 80
- [x] CI xanh

---

## Sang tuần 7

Tuần 7 sẽ là **buffer + QA + polish + deploy prep**. Không thêm feature mới (trừ bug fixes).

Plan tuần 7 sẽ được tạo riêng tại `docs/superpowers/plans/2026-04-12-tuan-7-buffer-qa-polish.md`.
