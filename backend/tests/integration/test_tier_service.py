import pytest

from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.tier import TierCreateRequest, TierUpdateRequest
from app.services.tier_service import TierNotFoundError, TierService


@pytest.fixture
async def active_partner(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=user.id, status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    return partner


@pytest.mark.asyncio
async def test_create_tier(db_session, active_partner):
    service = TierService(db_session)
    tier = await service.create_tier(
        partner_id=active_partner.id,
        request=TierCreateRequest(name="Bronze", min_points=0),
    )
    assert tier.id is not None
    assert tier.name == "Bronze"
    assert tier.min_points == 0
    assert tier.is_active is True
    assert tier.deleted_at is None


@pytest.mark.asyncio
async def test_list_tiers_excludes_soft_deleted(db_session, active_partner):
    service = TierService(db_session)
    bronze = await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()
    await service.delete_tier(partner_id=active_partner.id, tier_id=bronze.id)
    await db_session.flush()

    tiers = await service.list_tiers(partner_id=active_partner.id)
    names = [t.name for t in tiers]
    assert "Silver" in names
    assert "Bronze" not in names


@pytest.mark.asyncio
async def test_list_tiers_sorted_by_min_points(db_session, active_partner):
    service = TierService(db_session)
    await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Gold", min_points=2000)
    )
    await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()

    tiers = await service.list_tiers(partner_id=active_partner.id)
    assert [t.name for t in tiers] == ["Bronze", "Silver", "Gold"]


@pytest.mark.asyncio
async def test_update_tier(db_session, active_partner):
    service = TierService(db_session)
    tier = await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await db_session.flush()

    updated = await service.update_tier(
        partner_id=active_partner.id,
        tier_id=tier.id,
        request=TierUpdateRequest(name="Bronze+", min_points=100),
    )
    assert updated.name == "Bronze+"
    assert updated.min_points == 100


@pytest.mark.asyncio
async def test_update_tier_wrong_tenant_raises(db_session, active_partner):
    service = TierService(db_session)
    tier = await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="X", min_points=0)
    )
    await db_session.flush()

    with pytest.raises(TierNotFoundError):
        await service.update_tier(
            partner_id=99999,
            tier_id=tier.id,
            request=TierUpdateRequest(name="hacked"),
        )


@pytest.mark.asyncio
async def test_recompute_tier_first_assignment(db_session, active_partner):
    """Membership chưa có tier → assign tier lowest matching."""
    from app.models.membership import Membership
    from datetime import datetime, timezone

    user = User(email="m@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    bronze = await TierService(db_session).create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await TierService(db_session).create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()

    membership = Membership(
        partner_id=active_partner.id, user_id=user.id,
        current_tier_id=None, lifetime_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    new_tier = await TierService(db_session).recompute_tier(
        partner_id=active_partner.id, membership_id=membership.id
    )
    assert new_tier is not None
    assert new_tier.id == bronze.id


@pytest.mark.asyncio
async def test_recompute_tier_upgrades_when_enough_points(db_session, active_partner):
    from app.models.membership import Membership
    from datetime import datetime, timezone

    user = User(email="m@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TierService(db_session)
    await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    silver = await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Gold", min_points=2000)
    )
    await db_session.flush()

    membership = Membership(
        partner_id=active_partner.id, user_id=user.id,
        current_tier_id=None, lifetime_earned=600,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    new_tier = await service.recompute_tier(
        partner_id=active_partner.id, membership_id=membership.id
    )
    assert new_tier.id == silver.id


@pytest.mark.asyncio
async def test_recompute_tier_excludes_soft_deleted(db_session, active_partner):
    from app.models.membership import Membership
    from datetime import datetime, timezone

    user = User(email="m@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()

    service = TierService(db_session)
    bronze = await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    silver_deleted = await service.create_tier(
        partner_id=active_partner.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()
    await service.delete_tier(partner_id=active_partner.id, tier_id=silver_deleted.id)
    await db_session.flush()

    membership = Membership(
        partner_id=active_partner.id, user_id=user.id,
        current_tier_id=None, lifetime_earned=600,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    new_tier = await service.recompute_tier(
        partner_id=active_partner.id, membership_id=membership.id
    )
    assert new_tier.id == bronze.id
