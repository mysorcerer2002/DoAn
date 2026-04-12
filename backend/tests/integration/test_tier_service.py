import pytest

from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.schemas.tier import TierCreateRequest, TierUpdateRequest
from app.services.tier_service import TierNotFoundError, TierService


@pytest.fixture
async def active_tenant(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.mark.asyncio
async def test_create_tier(db_session, active_tenant):
    service = TierService(db_session)
    tier = await service.create_tier(
        tenant_id=active_tenant.id,
        request=TierCreateRequest(name="Bronze", min_points=0),
    )
    assert tier.id is not None
    assert tier.name == "Bronze"
    assert tier.min_points == 0
    assert tier.is_active is True
    assert tier.deleted_at is None


@pytest.mark.asyncio
async def test_list_tiers_excludes_soft_deleted(db_session, active_tenant):
    service = TierService(db_session)
    bronze = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()
    await service.delete_tier(tenant_id=active_tenant.id, tier_id=bronze.id)
    await db_session.flush()

    tiers = await service.list_tiers(tenant_id=active_tenant.id)
    names = [t.name for t in tiers]
    assert "Silver" in names
    assert "Bronze" not in names


@pytest.mark.asyncio
async def test_list_tiers_sorted_by_min_points(db_session, active_tenant):
    service = TierService(db_session)
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Gold", min_points=2000)
    )
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Silver", min_points=500)
    )
    await db_session.flush()

    tiers = await service.list_tiers(tenant_id=active_tenant.id)
    assert [t.name for t in tiers] == ["Bronze", "Silver", "Gold"]


@pytest.mark.asyncio
async def test_update_tier(db_session, active_tenant):
    service = TierService(db_session)
    tier = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="Bronze", min_points=0)
    )
    await db_session.flush()

    updated = await service.update_tier(
        tenant_id=active_tenant.id,
        tier_id=tier.id,
        request=TierUpdateRequest(name="Bronze+", min_points=100),
    )
    assert updated.name == "Bronze+"
    assert updated.min_points == 100


@pytest.mark.asyncio
async def test_update_tier_wrong_tenant_raises(db_session, active_tenant):
    service = TierService(db_session)
    tier = await service.create_tier(
        tenant_id=active_tenant.id, request=TierCreateRequest(name="X", min_points=0)
    )
    await db_session.flush()

    with pytest.raises(TierNotFoundError):
        await service.update_tier(
            tenant_id=99999,
            tier_id=tier.id,
            request=TierUpdateRequest(name="hacked"),
        )
