"""Integration tests cho /admin endpoints — test scope: reconcile + tenant approve."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _make_admin(db_session, email: str = "admin@x.com") -> User:
    admin = User(
        email=email,
        password_hash="x",
        is_active=True,
        system_role="super_admin",
    )
    db_session.add(admin)
    await db_session.flush()
    return admin


async def _make_tenant_with_member(db_session) -> tuple[Tenant, Membership]:
    owner = User(email="owner-r@x.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    tenant = Tenant(
        name="Recon Shop",
        slug="recon-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(
        TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER)
    )
    member = Membership(
        tenant_id=tenant.id,
        user_id=owner.id,
        points_balance=100,
        total_points_earned=100,
    )
    db_session.add(member)
    await db_session.flush()
    return tenant, member


async def test_reconcile_membership_consistent(client: AsyncClient, db_session):
    """C1 fix: /admin/reconcile/{id} không crash với TypeError."""
    admin = await _make_admin(db_session)
    tenant, member = await _make_tenant_with_member(db_session)

    # Add 1 ledger entry khớp với balance
    db_session.add(
        PointLedger(
            tenant_id=tenant.id,
            membership_id=member.id,
            delta=100,
            reason=LedgerReason.EARN,
            ref_type=LedgerRefType.TRANSACTION,
            ref_id=1,
            balance_after=100,
        )
    )
    await db_session.flush()

    response = await client.post(
        f"/admin/reconcile/{member.id}",
        headers={"Authorization": f"Bearer {create_access_token(user_id=admin.id)}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["membership_id"] == member.id
    assert data["expected_balance"] == 100
    assert data["actual_balance"] == 100
    assert data["is_consistent"] is True


async def test_reconcile_membership_not_found(client: AsyncClient, db_session):
    admin = await _make_admin(db_session)
    response = await client.post(
        "/admin/reconcile/99999",
        headers={"Authorization": f"Bearer {create_access_token(user_id=admin.id)}"},
    )
    assert response.status_code == 404


async def test_reconcile_requires_super_admin(client: AsyncClient, db_session):
    """Regular user không thể gọi reconcile."""
    user = User(email="reg@x.com", password_hash="x", is_active=True, system_role="regular")
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/admin/reconcile/1",
        headers={"Authorization": f"Bearer {create_access_token(user_id=user.id)}"},
    )
    assert response.status_code == 403


async def test_admin_approve_already_active_returns_409(client: AsyncClient, db_session):
    """C6 fix Section 2: invalid status transition → 409 thay vì 200."""
    admin = await _make_admin(db_session, email="admin-tt@x.com")
    tenant, _ = await _make_tenant_with_member(db_session)
    # tenant đã ACTIVE → approve lại nên 409
    response = await client.post(
        f"/admin/tenants/{tenant.id}/approve",
        json={"approve": True},
        headers={"Authorization": f"Bearer {create_access_token(user_id=admin.id)}"},
    )
    assert response.status_code == 409
