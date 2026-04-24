"""Integration tests: AnalyticsService — dashboard queries."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward
from app.models.partner import Partner, PartnerStatus
from app.models.tier import Tier
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.services.analytics_service import AnalyticsService, _fill_missing_days
from app.schemas.analytics import DailyTransactionPoint


async def _seed_analytics(db_session):
    """Tạo partner, 3 members, tiers, transactions, redemptions, campaign+vouchers."""
    now = datetime.now(timezone.utc)

    owner = User(email="analytics-owner@test.com", password_hash="x", is_active=True)
    u1 = User(email="member1@test.com", password_hash="x", is_active=True)
    u2 = User(email="member2@test.com", password_hash="x", is_active=True)
    u3 = User(email="member3@test.com", password_hash="x", is_active=True)
    db_session.add_all([owner, u1, u2, u3])
    await db_session.flush()

    partner = Partner(
        name="AnalyticsShop",
        slug="analytics-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    # Tiers
    silver = Tier(
        partner_id=partner.id, name="Silver", min_points=0
    )
    gold = Tier(
        partner_id=partner.id, name="Gold", min_points=500
    )
    db_session.add_all([silver, gold])
    await db_session.flush()

    # Memberships
    m1 = Membership(
        partner_id=partner.id,
        user_id=u1.id,
        joined_at=now,
        current_tier_id=silver.id,
        points_balance=100,
        total_points_earned=100,
    )
    m2 = Membership(
        partner_id=partner.id,
        user_id=u2.id,
        joined_at=now,
        current_tier_id=gold.id,
        points_balance=600,
        total_points_earned=600,
    )
    m3 = Membership(
        partner_id=partner.id,
        user_id=u3.id,
        joined_at=now,
        current_tier_id=None,
        points_balance=0,
        total_points_earned=0,
    )
    db_session.add_all([m1, m2, m3])
    await db_session.flush()

    # Transactions — 3 ngày gần đây
    for i, (membership, days_ago) in enumerate(
        [(m1, 1), (m1, 2), (m2, 1), (m2, 3), (m2, 3)]
    ):
        txn = Transaction(
            partner_id=partner.id,
            membership_id=membership.id,
            staff_id=owner.id,
            gross_amount=100000,
            net_amount=90000,
            points_earned=10,
            method=TransactionMethod.MANUAL,
            created_at=now - timedelta(days=days_ago),
        )
        db_session.add(txn)
    await db_session.flush()

    # Reward + Redemption
    reward = Reward(
        partner_id=partner.id,
        name="Free Coffee",
        points_cost=50,
        stock=10,
        is_active=True,
    )
    db_session.add(reward)
    await db_session.flush()

    redemption = Redemption(
        partner_id=partner.id,
        membership_id=m1.id,
        reward_id=reward.id,
        points_spent=50,
        redemption_code="RDANALYC",
        status=RedemptionStatus.PENDING,
        redeemed_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=7),
    )
    db_session.add(redemption)
    await db_session.flush()

    # Campaign + Voucher
    campaign = Campaign(
        partner_id=partner.id,
        name="Summer Sale",
        discount_type=DiscountType.PERCENT,
        discount_value=10,
        is_active=True,
        source=CampaignSource.MANUAL,
        program_form="giam_gia",
        approval_status="auto_approved",
        approval_tier="none",
        estimated_cost=0,
        starts_at=now - timedelta(days=10),
        ends_at=now + timedelta(days=20),
    )
    db_session.add(campaign)
    await db_session.flush()

    v1 = Voucher(
        partner_id=partner.id,
        campaign_id=campaign.id,
        membership_id=m1.id,
        code="VANA0001",
        status=VoucherStatus.USED,
        issue_source="manual",
        discount_snapshot={"discount_type": "fixed", "discount_value": 10000},
        issued_at=now - timedelta(days=5),
        expires_at=now + timedelta(days=30),
    )
    v2 = Voucher(
        partner_id=partner.id,
        campaign_id=campaign.id,
        membership_id=m2.id,
        code="VANA0002",
        status=VoucherStatus.ISSUED,
        issue_source="manual",
        discount_snapshot={"discount_type": "fixed", "discount_value": 10000},
        issued_at=now - timedelta(days=5),
        expires_at=now + timedelta(days=30),
    )
    db_session.add_all([v1, v2])
    await db_session.flush()

    return {
        "partner": partner,
        "owner": owner,
        "memberships": [m1, m2, m3],
        "tiers": [silver, gold],
        "campaign": campaign,
        "vouchers": [v1, v2],
    }


@pytest.mark.asyncio
async def test_count_members(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    count = await service._count_members(data["partner"].id)
    assert count == 3


@pytest.mark.asyncio
async def test_count_members_excludes_archived(db_session):
    data = await _seed_analytics(db_session)
    # Archive 1 member
    data["memberships"][2].archived_at = datetime.now(timezone.utc)
    await db_session.flush()

    service = AnalyticsService(db_session)
    count = await service._count_members(data["partner"].id)
    assert count == 2


@pytest.mark.asyncio
async def test_transaction_stats(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    today = date.today()
    stats = await service._transaction_stats(
        data["partner"].id, today - timedelta(days=30), today
    )
    assert stats["count"] == 5
    assert stats["revenue"] == 5 * 90000


@pytest.mark.asyncio
async def test_redemption_count(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    today = date.today()
    count = await service._redemption_count(
        data["partner"].id, today - timedelta(days=30), today
    )
    assert count == 1


@pytest.mark.asyncio
async def test_daily_transactions(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    today = date.today()
    from_date = today - timedelta(days=7)
    daily = await service._daily_transactions(
        data["partner"].id, from_date, today
    )
    # Phải có 8 data points (7 ngày + today)
    assert len(daily) == 8
    # Tổng transactions qua các ngày phải == 5
    total_txn = sum(p.transaction_count for p in daily)
    assert total_txn == 5


@pytest.mark.asyncio
async def test_tier_distribution(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    dist = await service._tier_distribution(data["partner"].id)
    # 3 groups: NULL tier, Silver, Gold
    assert len(dist) == 3
    names = {p.tier_name for p in dist}
    assert "Silver" in names
    assert "Gold" in names
    assert "Chưa phân hạng" in names
    # Tổng = 3 members
    total = sum(p.member_count for p in dist)
    assert total == 3


@pytest.mark.asyncio
async def test_campaign_roi(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    today = date.today()
    roi = await service._campaign_roi(
        data["partner"].id, today - timedelta(days=30), today
    )
    assert len(roi) == 1
    assert roi[0].campaign_name == "Summer Sale"
    assert roi[0].vouchers_issued == 2
    assert roi[0].vouchers_used == 1


@pytest.mark.asyncio
async def test_get_dashboard_full(db_session):
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    today = date.today()
    result = await service.get_dashboard(
        partner_id=data["partner"].id,
        from_date=today - timedelta(days=30),
        to_date=today,
    )
    assert result.member_count == 3
    assert result.transaction_count == 5
    assert result.total_revenue == 5 * 90000
    assert result.total_redemption_count == 1
    # redemption_rate = 1/5 = 0.2
    assert abs(result.redemption_rate - 0.2) < 0.01
    assert len(result.daily_transactions) == 31
    assert len(result.tier_distribution) == 3
    assert len(result.campaign_roi) == 1


@pytest.mark.asyncio
async def test_cross_tenant_isolation(db_session):
    """Partner B không thấy data của tenant A."""
    data = await _seed_analytics(db_session)

    owner_b = User(email="ownerB@test.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()

    tenant_b = Partner(
        name="OtherShop",
        slug="other-shop",
        owner_user_id=owner_b.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()

    service = AnalyticsService(db_session)
    today = date.today()
    result = await service.get_dashboard(
        partner_id=tenant_b.id,
        from_date=today - timedelta(days=30),
        to_date=today,
    )
    assert result.member_count == 0
    assert result.transaction_count == 0
    assert result.total_revenue == 0
    assert result.total_redemption_count == 0
    assert result.redemption_rate == 0.0


def test_fill_missing_days():
    """Test helper fill missing days."""
    from_date = date(2025, 1, 1)
    to_date = date(2025, 1, 5)
    points = [
        DailyTransactionPoint(
            day=date(2025, 1, 2),
            transaction_count=3,
            total_revenue=100,
            total_points_earned=10,
        ),
    ]
    result = _fill_missing_days(points, from_date, to_date)
    assert len(result) == 5
    assert result[0].day == date(2025, 1, 1)
    assert result[0].transaction_count == 0
    assert result[1].day == date(2025, 1, 2)
    assert result[1].transaction_count == 3
    assert result[4].day == date(2025, 1, 5)
    assert result[4].transaction_count == 0


@pytest.mark.asyncio
async def test_dashboard_empty_date_range(db_session):
    """Dashboard với khoảng thời gian không có data."""
    data = await _seed_analytics(db_session)
    service = AnalyticsService(db_session)
    # Khoảng thời gian trong quá khứ xa
    result = await service.get_dashboard(
        partner_id=data["partner"].id,
        from_date=date(2020, 1, 1),
        to_date=date(2020, 1, 7),
    )
    assert result.transaction_count == 0
    assert result.total_revenue == 0
    assert result.total_redemption_count == 0
    assert len(result.daily_transactions) == 7
    assert all(p.transaction_count == 0 for p in result.daily_transactions)
