"""Integration tests cho /partner/staff API."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.partner import Partner, PartnerStatus
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _make_active_partner_with_owner(db_session):
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
    db_session.add(
        PartnerStaff(partner_id=partner.id, user_id=owner.id, role=PartnerStaffRole.OWNER)
    )
    await db_session.flush()
    return partner, owner, create_access_token(user_id=owner.id)


async def test_add_staff_returns_201(client: AsyncClient, db_session):
    partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)

    response = await client.post(
        "/partner/staff",
        json={"email": "newstaff@example.com", "full_name": "New", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["staff"]["role"] == "staff"
    assert data["verification_code"] is None


async def test_add_staff_non_owner_returns_403(client: AsyncClient, db_session):
    partner, _owner, _ = await _make_active_partner_with_owner(db_session)

    staff_user = User(email="s@example.com", password_hash="x", is_active=True)
    db_session.add(staff_user)
    await db_session.flush()
    db_session.add(
        PartnerStaff(partner_id=partner.id, user_id=staff_user.id, role=PartnerStaffRole.STAFF)
    )
    await db_session.flush()
    staff_token = create_access_token(user_id=staff_user.id)

    response = await client.post(
        "/partner/staff",
        json={"email": "x@example.com", "full_name": "X", "role": "staff"},
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 403


async def test_list_staff_owner_sees_all(client: AsyncClient, db_session):
    partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)
    await client.post(
        "/partner/staff",
        json={"email": "s1@example.com", "full_name": "S1", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )

    response = await client.get(
        "/partner/staff",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_remove_staff(client: AsyncClient, db_session):
    partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)
    add = await client.post(
        "/partner/staff",
        json={"email": "s@example.com", "full_name": "S", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    staff_id = add.json()["staff"]["id"]

    response = await client.delete(
        f"/partner/staff/{staff_id}",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 204


async def test_missing_tenant_header_returns_400(client: AsyncClient, db_session):
    _partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)

    response = await client.get(
        "/partner/staff",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 400


async def test_cannot_remove_last_owner_returns_409(client: AsyncClient, db_session):
    """C3 fix: xóa owner cuối cùng → 409 LastOwnerError, không 500."""
    partner, owner, owner_token = await _make_active_partner_with_owner(db_session)
    # Lookup owner staff_id
    from sqlalchemy import select

    staff_row = await db_session.scalar(
        select(PartnerStaff).where(
            PartnerStaff.partner_id == partner.id, PartnerStaff.user_id == owner.id
        )
    )
    response = await client.delete(
        f"/partner/staff/{staff_row.id}",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 409
    assert "last owner" in response.json()["detail"].lower()


async def test_cannot_demote_last_owner_returns_409(client: AsyncClient, db_session):
    """C2 fix: demote owner cuối cùng → 409 LastOwnerError."""
    partner, owner, owner_token = await _make_active_partner_with_owner(db_session)
    from sqlalchemy import select

    staff_row = await db_session.scalar(
        select(PartnerStaff).where(
            PartnerStaff.partner_id == partner.id, PartnerStaff.user_id == owner.id
        )
    )
    response = await client.patch(
        f"/partner/staff/{staff_row.id}",
        json={"role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 409


async def test_can_demote_owner_when_multiple_owners(client: AsyncClient, db_session):
    """Demote owner OK khi còn owner khác."""
    partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)
    add = await client.post(
        "/partner/staff",
        json={"email": "owner2@example.com", "full_name": "Owner2", "role": "owner"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    second_owner_staff_id = add.json()["staff"]["id"]

    response = await client.patch(
        f"/partner/staff/{second_owner_staff_id}",
        json={"role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "staff"


async def test_staff_can_get_settings(client: AsyncClient, db_session):
    """I1 fix: STAFF role có thể GET settings (không phải owner-only)."""
    partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)
    add = await client.post(
        "/partner/staff",
        json={"email": "stf@example.com", "full_name": "Stf", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    staff_user_id = add.json()["staff"]["user_id"]
    staff_token = create_access_token(user_id=staff_user_id)

    response = await client.get(
        "/partners/me/settings",
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert response.status_code == 200
