import pytest

from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User
from app.schemas.tenant_staff import StaffAddRequest, StaffUpdateRoleRequest
from app.services.tenant_staff_service import (
    StaffAlreadyInTenantError,
    StaffNotFoundError,
    TenantStaffService,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def active_tenant(db_session):
    owner = User(email="owner@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="Test Shop",
        slug="test-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    db_session.add(TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER))
    await db_session.flush()

    return tenant, owner


async def test_add_staff_existing_user(db_session, active_tenant):
    tenant, _owner = active_tenant
    existing = User(email="staff@example.com", password_hash="x", is_active=True)
    db_session.add(existing)
    await db_session.flush()

    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="staff@example.com", full_name="Existing Staff", role=TenantStaffRole.STAFF
        ),
    )
    assert result.staff.user_id == existing.id
    assert result.staff.role == TenantStaffRole.STAFF
    assert result.verification_code is None


async def test_add_staff_new_user_creates_shadow(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="new@example.com", full_name="New Staff", role=TenantStaffRole.STAFF
        ),
    )
    assert result.staff.user_id is not None
    assert result.verification_code is not None
    assert len(result.verification_code) == 6
    assert result.verification_code.isdigit()

    user = await db_session.get(User, result.staff.user_id)
    assert user.is_shadow is True
    assert user.email == "new@example.com"


async def test_add_staff_already_in_tenant_raises(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="dup@example.com", full_name="Dup", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    with pytest.raises(StaffAlreadyInTenantError):
        await service.add_staff(
            tenant_id=tenant.id,
            request=StaffAddRequest(
                email="dup@example.com", full_name="Dup2", role=TenantStaffRole.STAFF
            ),
        )


async def test_remove_staff(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="remove@example.com", full_name="R", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    await service.remove_staff(tenant_id=tenant.id, staff_id=result.staff.id)
    await db_session.flush()

    found = await db_session.get(TenantStaff, result.staff.id)
    assert found is None


async def test_update_role(db_session, active_tenant):
    tenant, _owner = active_tenant
    service = TenantStaffService(db_session)
    result = await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="staff@example.com", full_name="S", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    updated = await service.update_role(
        tenant_id=tenant.id,
        staff_id=result.staff.id,
        request=StaffUpdateRoleRequest(role=TenantStaffRole.OWNER),
    )
    assert updated.role == TenantStaffRole.OWNER


async def test_list_staff_returns_only_tenant_members(db_session, active_tenant):
    tenant, owner = active_tenant
    service = TenantStaffService(db_session)
    await service.add_staff(
        tenant_id=tenant.id,
        request=StaffAddRequest(
            email="s1@example.com", full_name="S1", role=TenantStaffRole.STAFF
        ),
    )
    await db_session.flush()

    staff_list = await service.list_staff(tenant_id=tenant.id)
    emails = [s.user_email for s in staff_list]
    assert "owner@example.com" in emails
    assert "s1@example.com" in emails
    assert len(staff_list) == 2
