"""
B6 — Integration tests for PATCH /partner/point-rules/{rule_id} và
PATCH /partner/tiers/{tier_id} earn_multiplier field.
"""
from decimal import Decimal

import pytest

from app.core.security import create_access_token
from app.models.partner import Partner, PartnerStatus
from app.models.point_rule import PointRule
from app.models.tier import Tier
from app.models.user import User


async def _setup_owner(db_session):
    """Tạo owner + partner + PartnerStaff OWNER. Trả (partner, owner_token)."""
    owner = User(email="owner@test.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name="Test Shop",
        slug="test-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()
    await db_session.flush()
    token = create_access_token(user_id=owner.id)
    return partner, token


async def _create_rule(db_session, partner_id: int) -> PointRule:
    """Tạo PointRule trực tiếp trong DB cho partner_id."""
    rule = PointRule(
        partner_id=partner_id,
        earn_percent=Decimal("1.00"),
        use_tiers=False,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()
    await db_session.refresh(rule)
    return rule


async def _create_tier(db_session, partner_id: int) -> Tier:
    """Tạo Tier Bronze trực tiếp trong DB cho partner_id."""
    tier = Tier(
        partner_id=partner_id,
        name="Bronze",
        min_points=0,
        perks={},
        is_active=True,
    )
    db_session.add(tier)
    await db_session.flush()
    await db_session.refresh(tier)
    return tier


@pytest.mark.asyncio
async def test_patch_point_rule_use_tiers_toggle_as_owner(client, db_session):
    """Owner PATCH use_tiers=true → 200, trường use_tiers trong response là true."""
    partner, token = await _setup_owner(db_session)
    rule = await _create_rule(db_session, partner.id)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    response = await client.patch(
        f"/partner/point-rules/{rule.id}",
        json={"use_tiers": True},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["use_tiers"] is True
    assert data["id"] == rule.id


@pytest.mark.asyncio
async def test_patch_point_rule_as_staff_forbidden(client, db_session):
    """Staff (không phải owner) PATCH point-rule → 403."""
    partner, _owner_token = await _setup_owner(db_session)
    rule = await _create_rule(db_session, partner.id)

    # Tạo staff user riêng
    staff_user = User(email="staff@test.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    await db_session.flush()
    staff_token = create_access_token(user_id=staff_user.id)

    response = await client.patch(
        f"/partner/point-rules/{rule.id}",
        json={"use_tiers": True},
        headers={"Authorization": f"Bearer {staff_token}", "X-Partner-Id": str(partner.id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_patch_tier_earn_multiplier_valid(client, db_session):
    """Owner PATCH earn_multiplier=1.75 → 200, response earn_multiplier == '1.75'."""
    partner, token = await _setup_owner(db_session)
    tier = await _create_tier(db_session, partner.id)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    response = await client.patch(
        f"/partner/tiers/{tier.id}",
        json={"earn_multiplier": "1.75"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["earn_multiplier"] == "1.75"


@pytest.mark.asyncio
async def test_patch_tier_earn_multiplier_out_of_range_422(client, db_session):
    """earn_multiplier=10.00 ngoài khoảng [0.50, 5.00] → 422 Unprocessable Entity."""
    partner, token = await _setup_owner(db_session)
    tier = await _create_tier(db_session, partner.id)
    headers = {"Authorization": f"Bearer {token}", "X-Partner-Id": str(partner.id)}

    response = await client.patch(
        f"/partner/tiers/{tier.id}",
        json={"earn_multiplier": "10.00"},
        headers=headers,
    )
    assert response.status_code == 422
