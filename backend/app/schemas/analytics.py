"""Schemas cho Analytics dashboard."""

from datetime import date

from pydantic import BaseModel


class DailyTransactionPoint(BaseModel):
    """Một ngày trong biểu đồ giao dịch theo ngày."""

    day: date
    transaction_count: int
    total_revenue: int
    total_points_earned: int


class TierDistributionPoint(BaseModel):
    """Phân bố hạng thành viên."""

    tier_id: int | None
    tier_name: str
    member_count: int


class CampaignRoiPoint(BaseModel):
    """ROI từng campaign."""

    campaign_id: int
    campaign_name: str
    vouchers_issued: int
    vouchers_used: int
    total_discount: int
    total_revenue_from_voucher_txns: int


class DashboardResponse(BaseModel):
    """Phản hồi tổng hợp dashboard analytics."""

    period_from: date
    period_to: date
    member_count: int
    transaction_count: int
    total_revenue: int
    total_redemption_count: int
    redemption_rate: float
    daily_transactions: list[DailyTransactionPoint]
    tier_distribution: list[TierDistributionPoint]
    campaign_roi: list[CampaignRoiPoint]


class TenantDetailStats(BaseModel):
    """Stats cho trang chi tiết tenant (admin)."""

    member_count: int
    transaction_count: int
    total_revenue: int


class TenantDetailResponse(BaseModel):
    """Phản hồi chi tiết tenant cho admin."""

    id: int
    name: str
    slug: str
    status: str
    member_count: int
    transaction_count: int
    total_revenue: int


class PlatformStatsResponse(BaseModel):
    """Thống kê toàn platform cho admin."""

    total_tenants: int
    total_users: int
    total_transactions: int
