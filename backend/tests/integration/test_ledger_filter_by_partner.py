"""Integration tests cho GET /users/me/ledger?partner_slug= filter."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.partner import Partner, PartnerStatus
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.user import User

pytestmark = pytest.mark.asyncio


def _auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def _make_partner_with_membership(
    db_session, slug: str, customer: User, points: int = 100
) -> tuple[Partner, Membership]:
    owner = User(email=f"owner-{slug}@test.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name=slug.replace("-", " ").title(),
        slug=slug,
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()
    membership = Membership(
        partner_id=partner.id,
        user_id=customer.id,
        points_balance=points,
        total_points_earned=points,
    )
    db_session.add(membership)
    await db_session.flush()

    ledger = PointLedger(
        partner_id=partner.id,
        membership_id=membership.id,
        delta=points,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.TRANSACTION,
        ref_id=1,
        balance_after=points,
    )
    db_session.add(ledger)
    await db_session.flush()

    return partner, membership


# ── GET /users/me/ledger (no filter) ──


async def test_ledger_no_filter_returns_all(client: AsyncClient, db_session):
    """Không truyền partner_slug → trả ledger của TẤT CẢ partner."""
    customer = User(email="cust-all@test.com", password_hash="x", is_active=True)
    db_session.add(customer)
    await db_session.flush()

    await _make_partner_with_membership(db_session, "shop-ledger-a", customer, points=100)
    await _make_partner_with_membership(db_session, "shop-ledger-b", customer, points=200)

    resp = await client.get("/users/me/ledger", headers=_auth(customer.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2  # 1 ledger entry per partner


# ── GET /users/me/ledger?partner_slug=xxx ──


async def test_ledger_filter_by_partner_slug(client: AsyncClient, db_session):
    """Truyền partner_slug → chỉ trả ledger của partner đó."""
    customer = User(email="cust-filter@test.com", password_hash="x", is_active=True)
    db_session.add(customer)
    await db_session.flush()

    partner_a, _ = await _make_partner_with_membership(
        db_session, "shop-filter-a", customer, points=100
    )
    await _make_partner_with_membership(db_session, "shop-filter-b", customer, points=200)

    resp = await client.get(
        "/users/me/ledger",
        params={"partner_slug": partner_a.slug},
        headers=_auth(customer.id),
    )
    assert resp.status_code == 200
    data = resp.json()
    # Chỉ 1 ledger entry của partner A
    assert len(data) == 1


async def test_ledger_filter_partner_not_found(client: AsyncClient, db_session):
    """partner_slug không tồn tại → 404."""
    customer = User(email="cust-404@test.com", password_hash="x", is_active=True)
    db_session.add(customer)
    await db_session.flush()

    resp = await client.get(
        "/users/me/ledger",
        params={"partner_slug": "nonexistent-partner"},
        headers=_auth(customer.id),
    )
    assert resp.status_code == 404


async def test_ledger_filter_no_membership_returns_empty(client: AsyncClient, db_session):
    """Partner tồn tại nhưng customer không phải member → trả []."""
    customer = User(email="cust-nomem@test.com", password_hash="x", is_active=True)
    db_session.add(customer)
    await db_session.flush()

    # Tạo partner không có membership của customer này
    owner = User(email="owner-nomem@test.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name="No Mem Shop",
        slug="no-mem-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    resp = await client.get(
        "/users/me/ledger",
        params={"partner_slug": partner.slug},
        headers=_auth(customer.id),
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_ledger_unauthenticated(client: AsyncClient):
    resp = await client.get("/users/me/ledger")
    assert resp.status_code == 401


async def test_ledger_pagination(client: AsyncClient, db_session):
    """limit + offset param được tôn trọng."""
    customer = User(email="cust-page@test.com", password_hash="x", is_active=True)
    db_session.add(customer)
    await db_session.flush()

    owner = User(email="owner-page@test.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name="Page Shop", slug="page-shop",
        owner_user_id=owner.id, status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    membership = Membership(
        partner_id=partner.id, user_id=customer.id,
        points_balance=300, total_points_earned=300
    )
    db_session.add(membership)
    await db_session.flush()

    # Thêm 3 ledger entries
    running_balance = 0
    for delta in [100, 100, 100]:
        running_balance += delta
        db_session.add(PointLedger(
            partner_id=partner.id,
            membership_id=membership.id,
            delta=delta,
            reason=LedgerReason.EARN,
            ref_type=LedgerRefType.TRANSACTION,
            ref_id=1,
            balance_after=running_balance,
        ))
    await db_session.flush()

    resp = await client.get(
        "/users/me/ledger",
        params={"limit": 2, "offset": 0},
        headers=_auth(customer.id),
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp2 = await client.get(
        "/users/me/ledger",
        params={"limit": 2, "offset": 2},
        headers=_auth(customer.id),
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
