"""Integration tests: Voucher service — claim, already claimed, campaign full, eligible, mark used."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.services.voucher_service import (
    AlreadyClaimedError,
    CampaignFullError,
    VoucherService,
)


async def _setup(db_session):
    owner = User(email="vouch@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="VouchShop", slug="vouch-shop",
        owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    user = User(phone="0900000022", password_hash="x", is_active=True)
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
        name="Test Campaign",
        discount_type=DiscountType.PERCENT,
        discount_value=10,
        max_issuances=5,
        issued_count=0,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source=CampaignSource.MANUAL,
    )
    db_session.add(campaign)
    await db_session.flush()

    return tenant, owner, user, membership, campaign


@pytest.mark.asyncio
async def test_claim_voucher_success(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    voucher = await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )
    assert voucher.id is not None
    assert voucher.status == VoucherStatus.ISSUED
    assert len(voucher.code) == 8
    assert voucher.campaign_id == campaign.id
    assert voucher.membership_id == membership.id


@pytest.mark.asyncio
async def test_claim_voucher_already_claimed(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )

    with pytest.raises(AlreadyClaimedError):
        await svc.claim(
            tenant_id=tenant.id,
            membership_id=membership.id,
            campaign_id=campaign.id,
        )


@pytest.mark.asyncio
async def test_claim_voucher_campaign_full(db_session):
    tenant, _, user, membership, campaign = await _setup(db_session)
    campaign.max_issuances = 1
    campaign.issued_count = 0
    await db_session.flush()

    svc = VoucherService(db_session)
    await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )

    # Tạo member thứ 2
    user2 = User(phone="0900000023", password_hash="x", is_active=True)
    db_session.add(user2)
    await db_session.flush()
    membership2 = Membership(
        tenant_id=tenant.id, user_id=user2.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership2)
    await db_session.flush()

    with pytest.raises(CampaignFullError):
        await svc.claim(
            tenant_id=tenant.id,
            membership_id=membership2.id,
            campaign_id=campaign.id,
        )


@pytest.mark.asyncio
async def test_list_eligible_campaigns(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    eligible = await svc.list_eligible_campaigns(
        tenant_id=tenant.id,
        membership_id=membership.id,
        current_tier_id=membership.current_tier_id,
    )
    assert len(eligible) == 1
    assert eligible[0].id == campaign.id


@pytest.mark.asyncio
async def test_list_eligible_excludes_claimed(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )

    eligible = await svc.list_eligible_campaigns(
        tenant_id=tenant.id,
        membership_id=membership.id,
        current_tier_id=membership.current_tier_id,
    )
    assert len(eligible) == 0


@pytest.mark.asyncio
async def test_list_my_vouchers(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )

    vouchers = await svc.list_my_vouchers(
        tenant_id=tenant.id,
        membership_id=membership.id,
    )
    assert len(vouchers) == 1


@pytest.mark.asyncio
async def test_mark_used(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    voucher = await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )

    await svc.mark_used(tenant_id=tenant.id, voucher_id=voucher.id)
    await db_session.flush()

    updated = await svc.find_by_code(tenant_id=tenant.id, code=voucher.code)
    assert updated is not None
    assert updated.status == VoucherStatus.USED
    assert updated.used_at is not None


@pytest.mark.asyncio
async def test_find_by_code(db_session):
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    voucher = await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )

    found = await svc.find_by_code(tenant_id=tenant.id, code=voucher.code)
    assert found is not None
    assert found.id == voucher.id


@pytest.mark.asyncio
async def test_reclaim_after_used(db_session):
    """Sau khi voucher đã used, member có thể claim lại campaign."""
    tenant, _, _, membership, campaign = await _setup(db_session)
    svc = VoucherService(db_session)

    voucher = await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )
    await svc.mark_used(tenant_id=tenant.id, voucher_id=voucher.id)
    await db_session.flush()

    # Partial unique index chỉ ngăn active vouchers, used thì claim lại OK
    voucher2 = await svc.claim(
        tenant_id=tenant.id,
        membership_id=membership.id,
        campaign_id=campaign.id,
    )
    assert voucher2.id != voucher.id
    assert voucher2.status == VoucherStatus.ISSUED
