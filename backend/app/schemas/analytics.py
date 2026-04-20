"""Schemas cho Analytics dashboard."""

from datetime import date, datetime

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
    category: str
    description: str | None = None
    logo_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address: str | None = None
    tax_code: str | None = None
    website: str | None = None
    business_hours: str | None = None
    created_at: datetime
    activated_at: datetime | None = None
    owner_id: int
    owner_name: str | None = None
    owner_email: str | None = None
    owner_phone: str | None = None
    member_count: int
    active_member_count: int
    staff_count: int
    transaction_count: int
    total_revenue: int
    campaign_count: int
    active_campaign_count: int
    voucher_count: int
    redemption_count: int
    reward_count: int


class AdminTenantListRow(BaseModel):
    """Row cho /admin/tenants: đã kèm metric + owner để tránh N+1 ở FE."""

    id: int
    name: str
    slug: str
    status: str
    category: str
    logo_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    created_at: datetime
    activated_at: datetime | None = None
    owner_id: int
    owner_name: str | None = None
    owner_email: str | None = None
    member_count: int
    staff_count: int
    transaction_count: int
    total_revenue: int


class AdminTenantStaffRow(BaseModel):
    """Nhân viên/owner của một tenant."""

    user_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str  # owner | staff
    added_at: datetime
    is_active: bool


class AdminTenantMemberRow(BaseModel):
    """Khách hàng của một tenant."""

    membership_id: int
    user_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    points_balance: int
    total_points_earned: int
    current_tier_name: str | None = None
    joined_at: datetime
    archived: bool


class PlatformStatsResponse(BaseModel):
    """Thống kê toàn platform cho admin."""

    total_tenants: int
    total_users: int
    total_transactions: int
