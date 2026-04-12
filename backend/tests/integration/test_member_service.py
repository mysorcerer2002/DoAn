import pytest
from sqlalchemy import select

from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.member_service import MemberService


@pytest.fixture
async def active_tenant(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=owner.id, status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.mark.asyncio
async def test_find_or_create_brand_new_user(db_session, active_tenant):
    """Case 1: SĐT hoàn toàn mới — tạo shadow user + membership."""
    service = MemberService(db_session)
    member = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    await db_session.flush()

    assert member.is_new is True
    assert member.user_phone == "+84912345678"
    assert member.points_balance == 0
    assert member.tenant_id == active_tenant.id

    user = await db_session.get(User, member.user_id)
    assert user.is_shadow is True


@pytest.mark.asyncio
async def test_find_existing_user_existing_membership(db_session, active_tenant):
    """Case khách quay lại — không tạo gì mới."""
    service = MemberService(db_session)
    first = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    await db_session.flush()

    second = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    assert second.is_new is False
    assert second.user_id == first.user_id
    assert second.membership_id == first.membership_id


@pytest.mark.asyncio
async def test_existing_user_other_tenant_creates_new_membership(db_session, active_tenant):
    """Case 2/3: User đã có (do tenant khác) — KHÔNG tạo user mới, chỉ tạo membership."""
    other_owner = User(email="other@example.com", password_hash="x", is_active=True)
    db_session.add(other_owner)
    await db_session.flush()
    other_tenant = Tenant(
        name="O", slug="o", owner_user_id=other_owner.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(other_tenant)
    await db_session.flush()

    service = MemberService(db_session)

    member_in_other = await service.find_or_create_member(
        tenant_id=other_tenant.id, phone="0912345678"
    )
    await db_session.flush()
    user_id = member_in_other.user_id

    member_in_active = await service.find_or_create_member(
        tenant_id=active_tenant.id, phone="0912345678"
    )
    await db_session.flush()

    assert member_in_active.user_id == user_id
    assert member_in_active.membership_id != member_in_other.membership_id
    assert member_in_active.is_new is True


@pytest.mark.asyncio
async def test_normalize_phone_before_lookup(db_session, active_tenant):
    service = MemberService(db_session)
    a = await service.find_or_create_member(tenant_id=active_tenant.id, phone="0912345678")
    await db_session.flush()
    b = await service.find_or_create_member(tenant_id=active_tenant.id, phone="091 234 5678")
    assert a.user_id == b.user_id
    assert a.membership_id == b.membership_id
