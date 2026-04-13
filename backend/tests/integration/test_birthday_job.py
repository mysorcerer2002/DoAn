"""Integration tests: Birthday voucher job."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.notification import Notification
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus


async def _setup_birthday(db_session, birthday: date):
    """Tạo tenant + user có sinh nhật + membership + birthday campaign."""
    owner = User(email="bday@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="BdayShop", slug="bday-shop",
        owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        phone="0900000066", password_hash="x", is_active=True,
        birthday=birthday,
    )
    db_session.add(user)
    await db_session.flush()

    membership = Membership(
        tenant_id=tenant.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    campaign = Campaign(
        tenant_id=tenant.id,
        name="Happy Birthday",
        discount_type=DiscountType.FIXED,
        discount_value=50000,
        max_issuances=1000,
        issued_count=0,
        starts_at=now - timedelta(days=30),
        ends_at=now + timedelta(days=365),
        is_active=True,
        source=CampaignSource.BIRTHDAY,
    )
    db_session.add(campaign)
    await db_session.flush()

    return tenant, user, membership, campaign


@pytest.mark.asyncio
async def test_birthday_job_issues_voucher(db_session):
    """Job tạo voucher cho user có sinh nhật hôm nay (VN timezone)."""
    today = datetime.now(VN_TZ).date()
    birthday = date(1990, today.month, today.day)

    tenant, user, membership, campaign = await _setup_birthday(db_session, birthday)
    await db_session.commit()

    from app.jobs import birthday_voucher

    test_factory = async_sessionmaker(
        bind=db_session.bind, class_=AsyncSession, expire_on_commit=False,
    )

    with patch.object(birthday_voucher, "AsyncSessionLocal", test_factory):
        result = await birthday_voucher.birthday_voucher_job()
    assert result["issued"] >= 1

    # Verify voucher được tạo
    async with test_factory() as fresh_session:
        vouchers = (
            await fresh_session.scalars(
                select(Voucher).where(
                    Voucher.campaign_id == campaign.id,
                    Voucher.membership_id == membership.id,
                )
            )
        ).all()
        assert len(vouchers) >= 1
        assert vouchers[0].status == VoucherStatus.ISSUED


@pytest.mark.asyncio
async def test_birthday_job_idempotent(db_session):
    """Chạy job 2 lần → chỉ tạo 1 voucher."""
    today = datetime.now(VN_TZ).date()
    birthday = date(1990, today.month, today.day)

    tenant, user, membership, campaign = await _setup_birthday(db_session, birthday)
    await db_session.commit()

    from app.jobs import birthday_voucher

    test_factory = async_sessionmaker(
        bind=db_session.bind, class_=AsyncSession, expire_on_commit=False,
    )

    with patch.object(birthday_voucher, "AsyncSessionLocal", test_factory):
        result1 = await birthday_voucher.birthday_voucher_job()
        result2 = await birthday_voucher.birthday_voucher_job()

    assert result2["skipped"] >= 1

    async with test_factory() as fresh_session:
        vouchers = (
            await fresh_session.scalars(
                select(Voucher).where(
                    Voucher.campaign_id == campaign.id,
                    Voucher.membership_id == membership.id,
                )
            )
        ).all()
        assert len(vouchers) == 1


@pytest.mark.asyncio
async def test_birthday_job_no_campaign(db_session):
    """Không có birthday campaign → issued=0."""
    from app.jobs import birthday_voucher

    test_factory = async_sessionmaker(
        bind=db_session.bind, class_=AsyncSession, expire_on_commit=False,
    )

    with patch.object(birthday_voucher, "AsyncSessionLocal", test_factory):
        result = await birthday_voucher.birthday_voucher_job()
    assert result["issued"] == 0
    assert result["skipped"] == 0


@pytest.mark.asyncio
async def test_birthday_job_different_day(db_session):
    """User có sinh nhật ngày khác → không tạo voucher."""
    today = datetime.now(VN_TZ).date()
    # Sinh nhật ngày mai
    tomorrow = today + timedelta(days=1)
    birthday = date(1990, tomorrow.month, tomorrow.day)

    tenant, user, membership, campaign = await _setup_birthday(db_session, birthday)
    await db_session.commit()

    from app.jobs import birthday_voucher

    test_factory = async_sessionmaker(
        bind=db_session.bind, class_=AsyncSession, expire_on_commit=False,
    )

    with patch.object(birthday_voucher, "AsyncSessionLocal", test_factory):
        result = await birthday_voucher.birthday_voucher_job()
    assert result["issued"] == 0
