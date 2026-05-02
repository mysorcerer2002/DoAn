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


class DailyRedemptionPoint(BaseModel):
    """Một ngày trong biểu đồ quà phát ra theo ngày."""

    day: date
    redemption_count: int


class TopRewardRow(BaseModel):
    """Một hàng trong bảng Top 5 quà."""

    reward_id: int
    name: str
    issued: int
    used: int


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
    daily_redemptions: list[DailyRedemptionPoint]
    top_rewards: list[TopRewardRow]


class PartnerDetailStats(BaseModel):
    """Stats cho trang chi tiết đối tác (admin)."""

    member_count: int
    transaction_count: int
    total_revenue: int


class PartnerDetailResponse(BaseModel):
    """Phản hồi chi tiết đối tác cho admin."""

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
    transaction_count: int
    total_revenue: int
    redemption_count: int
    reward_count: int
    business_license_url: str | None = None
    terms_accepted_at: datetime | None = None
    terms_version: str | None = None
    last_status_reason: str | None = None
    last_status_changed_at: datetime | None = None


class AdminPartnerListRow(BaseModel):
    """Row cho /admin/partners: đã kèm metric + owner để tránh N+1 ở FE.

    `active_member_count`: tổng số membership thuộc partner. `active_member_count_30d`:
    khách có giao dịch trong 30 ngày gần nhất — tham gia "active shop" tag.
    """

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
    active_member_count: int
    active_member_count_30d: int


class AdminPartnerStaffRow(BaseModel):
    """Nhân viên/owner của một đối tác."""

    user_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str  # owner | staff
    added_at: datetime
    is_active: bool


class AdminPartnerMemberRow(BaseModel):
    """Khách hàng của một đối tác.

    `points_balance` = ví toàn cục từ users.points_balance.
    `lifetime_earned` = tổng điểm tích luỹ tại shop này (per-shop tier metric).
    """

    membership_id: int
    user_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    points_balance: int
    lifetime_earned: int
    current_tier_name: str | None = None
    joined_at: datetime


class PlatformStatsResponse(BaseModel):
    """Thống kê toàn platform cho admin."""

    # XXX: rename total_tenants → total_partners khi frontend migrate sang Partner (Phase 6+)
    total_tenants: int
    total_users: int
    total_transactions: int
    total_points_circulating: int = 0
