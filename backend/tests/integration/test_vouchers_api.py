"""Integration tests: Vouchers API (available, claim, mine)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.campaign import Campaign, CampaignSource, DiscountType
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup(db_session):
    owner = User(email="vapi@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="VoucherAPIShop", slug="voucher-api-shop",
        owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    db_session.add(
        TenantStaff(
            tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER,
        )
    )
    await db_session.flush()

    customer = User(phone="0900000033", password_hash="x", is_active=True)
    db_session.add(customer)
    await db_session.flush()

    membership = Membership(
        tenant_id=tenant.id, user_id=customer.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    campaign = Campaign(
        tenant_id=tenant.id,
        name="API Campaign",
        discount_type=DiscountType.FIXED,
        discount_value=5000,
        max_issuances=10,
        issued_count=0,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source=CampaignSource.MANUAL,
    )
    db_session.add(campaign)
    await db_session.flush()

    token = create_access_token(user_id=customer.id)
    headers = {"Authorization": f"Bearer {token}"}
    return tenant, campaign, customer, membership, headers


@pytest.mark.asyncio
async def test_list_available_campaigns(client, db_session):
    tenant, campaign, _, _, headers = await _setup(db_session)

    resp = await client.get(
        f"/member/vouchers/available/{tenant.slug}", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["campaign_id"] == campaign.id


@pytest.mark.asyncio
async def test_claim_voucher_api(client, db_session):
    tenant, campaign, _, _, headers = await _setup(db_session)

    resp = await client.post(
        f"/member/vouchers/claim/{tenant.slug}",
        json={"campaign_id": campaign.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["campaign_id"] == campaign.id
    assert data["status"] == "issued"
    assert len(data["code"]) == 8


@pytest.mark.asyncio
async def test_claim_duplicate_409(client, db_session):
    tenant, campaign, _, _, headers = await _setup(db_session)

    resp1 = await client.post(
        f"/member/vouchers/claim/{tenant.slug}",
        json={"campaign_id": campaign.id},
        headers=headers,
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        f"/member/vouchers/claim/{tenant.slug}",
        json={"campaign_id": campaign.id},
        headers=headers,
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_my_vouchers(client, db_session):
    tenant, campaign, _, _, headers = await _setup(db_session)

    await client.post(
        f"/member/vouchers/claim/{tenant.slug}",
        json={"campaign_id": campaign.id},
        headers=headers,
    )

    resp = await client.get(
        f"/member/vouchers/mine/{tenant.slug}", headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_not_member_403(client, db_session):
    """Khách không phải member → 403."""
    owner = User(email="vapi2@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="NonMemberShop", slug="non-member-shop",
        owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    non_member = User(phone="0900000044", password_hash="x", is_active=True)
    db_session.add(non_member)
    await db_session.flush()

    token = create_access_token(user_id=non_member.id)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get(
        f"/member/vouchers/available/{tenant.slug}", headers=headers
    )
    assert resp.status_code == 403
