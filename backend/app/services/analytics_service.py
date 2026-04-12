"""AnalyticsService — Dashboard queries cho merchant analytics."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.membership import Membership
from app.models.redemption import Redemption
from app.models.tier import Tier
from app.models.transaction import Transaction
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.analytics import (
    CampaignRoiPoint,
    DailyTransactionPoint,
    DashboardResponse,
    TierDistributionPoint,
)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _date_range_to_utc(
    from_date: date, to_date: date
) -> tuple[datetime, datetime]:
    """Half-open interval [from_dt, to_dt_exclusive) theo timezone VN → UTC."""
    from_dt_vn = datetime.combine(from_date, time.min, tzinfo=VN_TZ)
    to_dt_vn = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=VN_TZ)
    return from_dt_vn.astimezone(timezone.utc), to_dt_vn.astimezone(timezone.utc)


def _fill_missing_days(
    points: list[DailyTransactionPoint], from_date: date, to_date: date
) -> list[DailyTransactionPoint]:
    """Fill ngày không có data với 0 → chart luôn đủ data points."""
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
        redemption_count = await self._redemption_count(
            tenant_id, from_date, to_date
        )
        daily = await self._daily_transactions(tenant_id, from_date, to_date)
        tier_dist = await self._tier_distribution(tenant_id)
        campaign_roi = await self._campaign_roi(tenant_id, from_date, to_date)

        # redemption_rate = redemptions / transactions (% giao dịch có đổi quà)
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
        """Đếm thành viên active (chưa archived)."""
        return int(
            await self.db.scalar(
                select(func.count())
                .select_from(Membership)
                .where(
                    Membership.tenant_id == tenant_id,
                    Membership.archived_at.is_(None),
                )
            )
            or 0
        )

    async def _transaction_stats(
        self, tenant_id: int, from_date: date, to_date: date
    ) -> dict:
        """Tổng số giao dịch + doanh thu trong khoảng thời gian."""
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)
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
        """Đếm lượt đổi quà trong khoảng thời gian."""
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)
        return int(
            await self.db.scalar(
                select(func.count())
                .select_from(Redemption)
                .where(
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
        """Giao dịch theo ngày (timezone VN)."""
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)
        day_expr = func.date(
            func.timezone("Asia/Ho_Chi_Minh", Transaction.created_at)
        ).label("day")

        result = await self.db.execute(
            select(
                day_expr,
                func.count().label("cnt"),
                func.coalesce(func.sum(Transaction.net_amount), 0).label("revenue"),
                func.coalesce(func.sum(Transaction.points_earned), 0).label(
                    "points"
                ),
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
        return _fill_missing_days(raw_points, from_date, to_date)

    async def _tier_distribution(
        self, tenant_id: int
    ) -> list[TierDistributionPoint]:
        """Phân bố hạng thành viên (COALESCE NULL tier)."""
        result = await self.db.execute(
            select(
                Membership.current_tier_id,
                func.coalesce(Tier.name, "Chưa phân hạng").label("tier_name"),
                func.count(Membership.id).label("cnt"),
            )
            .outerjoin(
                Tier,
                (Membership.current_tier_id == Tier.id)
                & (Tier.deleted_at.is_(None)),
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
        """ROI campaign — 2 queries riêng tránh cross-product."""
        from_dt, to_dt_excl = _date_range_to_utc(from_date, to_date)

        # Query 1: voucher counts theo campaign
        voucher_query = (
            select(
                Campaign.id.label("campaign_id"),
                Campaign.name.label("campaign_name"),
                func.count(Voucher.id).label("issued"),
                func.coalesce(
                    func.sum(
                        case(
                            (Voucher.status == VoucherStatus.USED, 1), else_=0
                        )
                    ),
                    0,
                ).label("used"),
            )
            .outerjoin(Voucher, Voucher.campaign_id == Campaign.id)
            .where(
                Campaign.tenant_id == tenant_id,
                Campaign.deleted_at.is_(None),
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
                func.coalesce(func.sum(Transaction.net_amount), 0).label(
                    "total_revenue"
                ),
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
                total_revenue_from_voucher_txns=txn_rows.get(
                    r.campaign_id, (0, 0)
                )[1],
            )
            for r in voucher_rows
        ]
