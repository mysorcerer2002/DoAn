"""Integration tests: Campaign service CRUD + soft delete + ROI."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.campaign import CampaignCreateRequest, CampaignUpdateRequest
from app.services.campaign_service import CampaignNotFoundError, CampaignService


async def _make_tenant(db_session) -> tuple:
    owner = User(email="camp@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="CampShop",
        slug="camp-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant, owner


@pytest.mark.asyncio
async def test_create_campaign(db_session):
    tenant, _ = await _make_tenant(db_session)
    svc = CampaignService(db_session)

    now = datetime.now(timezone.utc)
    req = CampaignCreateRequest(
        name="Summer Sale",
        description="Giảm giá mùa hè",
        discount_type="percent",
        discount_value=10,
        min_order=50000,
        max_discount=20000,
        max_issuances=100,
        starts_at=now,
        ends_at=now + timedelta(days=30),
    )
    campaign = await svc.create_campaign(tenant_id=tenant.id, request=req)
    assert campaign.id is not None
    assert campaign.name == "Summer Sale"
    assert campaign.discount_type == DiscountType.PERCENT
    assert campaign.discount_value == 10
    assert campaign.is_active is True
    assert campaign.issued_count == 0


@pytest.mark.asyncio
async def test_list_campaigns_exclude_deleted(db_session):
    tenant, _ = await _make_tenant(db_session)
    svc = CampaignService(db_session)

    now = datetime.now(timezone.utc)
    for i in range(3):
        await svc.create_campaign(
            tenant_id=tenant.id,
            request=CampaignCreateRequest(
                name=f"Campaign {i}",
                discount_type="fixed",
                discount_value=5000,
                starts_at=now,
                ends_at=now + timedelta(days=7),
            ),
        )

    campaigns = await svc.list_campaigns(tenant_id=tenant.id)
    assert len(campaigns) == 3

    # Soft delete one
    await svc.soft_delete_campaign(tenant_id=tenant.id, campaign_id=campaigns[0].id)
    await db_session.flush()

    campaigns = await svc.list_campaigns(tenant_id=tenant.id)
    assert len(campaigns) == 2


@pytest.mark.asyncio
async def test_update_campaign(db_session):
    tenant, _ = await _make_tenant(db_session)
    svc = CampaignService(db_session)

    now = datetime.now(timezone.utc)
    campaign = await svc.create_campaign(
        tenant_id=tenant.id,
        request=CampaignCreateRequest(
            name="Original",
            discount_type="fixed",
            discount_value=10000,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        ),
    )

    updated = await svc.update_campaign(
        tenant_id=tenant.id,
        campaign_id=campaign.id,
        request=CampaignUpdateRequest(name="Updated", is_active=False),
    )
    assert updated.name == "Updated"
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_soft_delete_campaign(db_session):
    tenant, _ = await _make_tenant(db_session)
    svc = CampaignService(db_session)

    now = datetime.now(timezone.utc)
    campaign = await svc.create_campaign(
        tenant_id=tenant.id,
        request=CampaignCreateRequest(
            name="ToDelete",
            discount_type="percent",
            discount_value=5,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        ),
    )

    await svc.soft_delete_campaign(tenant_id=tenant.id, campaign_id=campaign.id)
    await db_session.flush()

    with pytest.raises(CampaignNotFoundError):
        await svc.get_campaign(tenant_id=tenant.id, campaign_id=campaign.id)


@pytest.mark.asyncio
async def test_campaign_not_found(db_session):
    tenant, _ = await _make_tenant(db_session)
    svc = CampaignService(db_session)

    with pytest.raises(CampaignNotFoundError):
        await svc.get_campaign(tenant_id=tenant.id, campaign_id=99999)


@pytest.mark.asyncio
async def test_cross_tenant_isolation(db_session):
    """Tenant A không thấy campaign của Tenant B."""
    tenant_a, _ = await _make_tenant(db_session)

    owner_b = User(email="campb@example.com", password_hash="x", is_active=True)
    db_session.add(owner_b)
    await db_session.flush()
    tenant_b = Tenant(
        name="CampShopB", slug="camp-shop-b",
        owner_user_id=owner_b.id, status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant_b)
    await db_session.flush()

    svc = CampaignService(db_session)
    now = datetime.now(timezone.utc)
    await svc.create_campaign(
        tenant_id=tenant_a.id,
        request=CampaignCreateRequest(
            name="A Campaign",
            discount_type="fixed",
            discount_value=5000,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        ),
    )

    # Tenant B should see 0 campaigns
    campaigns = await svc.list_campaigns(tenant_id=tenant_b.id)
    assert len(campaigns) == 0


@pytest.mark.asyncio
async def test_campaign_roi(db_session):
    """Test ROI calculation."""
    tenant, owner = await _make_tenant(db_session)
    svc = CampaignService(db_session)

    now = datetime.now(timezone.utc)
    campaign = await svc.create_campaign(
        tenant_id=tenant.id,
        request=CampaignCreateRequest(
            name="ROI Test",
            discount_type="fixed",
            discount_value=10000,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        ),
    )

    # Tạo membership + vouchers + transactions giả lập
    user = User(phone="0900000011", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    membership = Membership(
        tenant_id=tenant.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    voucher = Voucher(
        tenant_id=tenant.id,
        campaign_id=campaign.id,
        membership_id=membership.id,
        code="TESTCODE",
        status=VoucherStatus.USED,
        issued_at=now,
        used_at=now,
        expires_at=now + timedelta(days=7),
    )
    db_session.add(voucher)
    campaign.issued_count = 1
    await db_session.flush()

    # Transaction dùng voucher
    txn = Transaction(
        tenant_id=tenant.id,
        membership_id=membership.id,
        staff_id=owner.id,
        gross_amount=100000,
        voucher_id=voucher.id,
        voucher_discount_amount=10000,
        net_amount=90000,
        points_earned=90,
        method=TransactionMethod.MANUAL,
    )
    db_session.add(txn)
    await db_session.flush()

    roi = await svc.get_campaign_roi(tenant_id=tenant.id, campaign_id=campaign.id)
    assert roi.vouchers_issued == 1
    assert roi.vouchers_used == 1
    assert roi.total_discount_amount == 10000
    assert roi.total_revenue_from_voucher_txns == 90000
