import pytest

from app.models.partner import Partner, PartnerStatus
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.user import User
from app.schemas.partner_staff import StaffAddRequest, StaffUpdateRoleRequest
from app.services.partner_staff_service import (
    StaffAlreadyInPartnerError,
    StaffNotFoundError,
    PartnerStaffService,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def active_partner(db_session):
    owner = User(email="owner@example.com", password_hash="x", is_active=True)
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

    db_session.add(PartnerStaff(partner_id=partner.id, user_id=owner.id, role=PartnerStaffRole.OWNER))
    await db_session.flush()

    return partner, owner


async def test_add_staff_existing_user(db_session, active_partner):
    partner, _owner = active_partner
    existing = User(email="staff@example.com", password_hash="x", is_active=True)
    db_session.add(existing)
    await db_session.flush()

    service = PartnerStaffService(db_session)
    result = await service.add_staff(
        partner_id=partner.id,
        request=StaffAddRequest(
            email="staff@example.com", full_name="Existing Staff", role=PartnerStaffRole.STAFF
        ),
    )
    assert result.staff.user_id == existing.id
    assert result.staff.role == PartnerStaffRole.STAFF
    assert result.verification_code is None


async def test_add_staff_new_user_creates_shadow(db_session, active_partner):
    partner, _owner = active_partner
    service = PartnerStaffService(db_session)
    result = await service.add_staff(
        partner_id=partner.id,
        request=StaffAddRequest(
            email="new@example.com", full_name="New Staff", role=PartnerStaffRole.STAFF
        ),
    )
    assert result.staff.user_id is not None
    assert result.verification_code is None

    user = await db_session.get(User, result.staff.user_id)
    assert user is not None
    assert user.password_hash is None
    assert user.email == "new@example.com"


async def test_add_staff_already_in_partner_raises(db_session, active_partner):
    partner, _owner = active_partner
    service = PartnerStaffService(db_session)
    await service.add_staff(
        partner_id=partner.id,
        request=StaffAddRequest(
            email="dup@example.com", full_name="Dup", role=PartnerStaffRole.STAFF
        ),
    )
    await db_session.flush()

    with pytest.raises(StaffAlreadyInPartnerError):
        await service.add_staff(
            partner_id=partner.id,
            request=StaffAddRequest(
                email="dup@example.com", full_name="Dup2", role=PartnerStaffRole.STAFF
            ),
        )


async def test_remove_staff(db_session, active_partner):
    partner, _owner = active_partner
    service = PartnerStaffService(db_session)
    result = await service.add_staff(
        partner_id=partner.id,
        request=StaffAddRequest(
            email="remove@example.com", full_name="R", role=PartnerStaffRole.STAFF
        ),
    )
    await db_session.flush()

    await service.remove_staff(partner_id=partner.id, staff_id=result.staff.id)
    await db_session.flush()

    found = await db_session.get(PartnerStaff, result.staff.id)
    assert found is None


async def test_update_role(db_session, active_partner):
    partner, _owner = active_partner
    service = PartnerStaffService(db_session)
    result = await service.add_staff(
        partner_id=partner.id,
        request=StaffAddRequest(
            email="staff@example.com", full_name="S", role=PartnerStaffRole.STAFF
        ),
    )
    await db_session.flush()

    updated = await service.update_role(
        partner_id=partner.id,
        staff_id=result.staff.id,
        request=StaffUpdateRoleRequest(role=PartnerStaffRole.OWNER),
    )
    assert updated.role == PartnerStaffRole.OWNER


async def test_list_staff_returns_only_partner_members(db_session, active_partner):
    partner, owner = active_partner
    service = PartnerStaffService(db_session)
    await service.add_staff(
        partner_id=partner.id,
        request=StaffAddRequest(
            email="s1@example.com", full_name="S1", role=PartnerStaffRole.STAFF
        ),
    )
    await db_session.flush()

    staff_list = await service.list_staff(partner_id=partner.id)
    emails = [s.user_email for s in staff_list]
    assert "owner@example.com" in emails
    assert "s1@example.com" in emails
    assert len(staff_list) == 2
