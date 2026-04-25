"""Integration tests cho GET /users/me/partners và GET /users/me/partners/{slug}."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.partner import Partner, PartnerStatus
from app.models.user import User

pytestmark = pytest.mark.asyncio


def _auth(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def _make_active_partner(db_session, name: str, slug: str) -> Partner:
    owner = User(
        email=f"owner-{slug}@test.com", password_hash="x", is_active=True
    )
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name=name,
        slug=slug,
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()
    await db_session.flush()
    return partner


async def _make_customer(db_session, email: str) -> User:
    user = User(email=email, password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    return user


# ── GET /users/me/partners ──


async def test_list_partners_returns_active_only(client: AsyncClient, db_session):
    """Chỉ partner ACTIVE được trả về."""
    partner_a = await _make_active_partner(db_session, "Shop A", "shop-a")
    customer = await _make_customer(db_session, "cust@test.com")

    # Tạo thêm partner PENDING không nên xuất hiện
    pending_owner = User(email="pending@test.com", password_hash="x", is_active=True)
    db_session.add(pending_owner)
    await db_session.flush()
    pending = Partner(
        name="Pending Shop",
        slug="pending-shop",
        owner_user_id=pending_owner.id,
        status=PartnerStatus.PENDING,
        settings={},
    )
    db_session.add(pending)
    await db_session.flush()

    resp = await client.get("/users/me/partners", headers=_auth(customer.id))
    assert resp.status_code == 200
    data = resp.json()
    slugs = [p["slug"] for p in data]
    assert "shop-a" in slugs
    assert "pending-shop" not in slugs


async def test_list_partners_no_membership_required(client: AsyncClient, db_session):
    """Customer không cần là member để xem danh sách partner."""
    await _make_active_partner(db_session, "Open Shop", "open-shop")
    customer = await _make_customer(db_session, "stranger@test.com")

    resp = await client.get("/users/me/partners", headers=_auth(customer.id))
    assert resp.status_code == 200
    slugs = [p["slug"] for p in resp.json()]
    assert "open-shop" in slugs


async def test_list_partners_unauthenticated(client: AsyncClient):
    resp = await client.get("/users/me/partners")
    assert resp.status_code == 401


async def test_list_partners_schema(client: AsyncClient, db_session):
    """Response phải có đúng fields của MyPartnerSummary, kèm membership-conditional fields."""
    await _make_active_partner(db_session, "Schema Shop", "schema-shop")
    customer = await _make_customer(db_session, "schema@test.com")

    resp = await client.get("/users/me/partners", headers=_auth(customer.id))
    assert resp.status_code == 200
    item = next((p for p in resp.json() if p["slug"] == "schema-shop"), None)
    assert item is not None
    assert "id" in item
    assert "name" in item
    assert "slug" in item
    assert "category" in item
    # Membership-conditional: customer chưa join shop này
    assert item["is_member"] is False
    assert item["points_balance"] is None
    assert item["current_tier_name"] is None


async def test_list_partners_membership_fields(client: AsyncClient, db_session):
    """Customer là member của 1 shop: shop đó có points + tier; shop kia null."""
    from app.models.tier import Tier

    member_shop = await _make_active_partner(db_session, "Member Shop", "list-member")
    other_shop = await _make_active_partner(db_session, "Other Shop", "list-other")
    customer = await _make_customer(db_session, "listmember@test.com")

    tier = Tier(
        partner_id=member_shop.id,
        name="Bạc",
        min_points=100,
    )
    db_session.add(tier)
    await db_session.flush()

    customer.points_balance = 320
    db_session.add(
        Membership(
            partner_id=member_shop.id,
            user_id=customer.id,
            current_tier_id=tier.id,
            lifetime_earned=420,
        )
    )
    await db_session.flush()

    resp = await client.get("/users/me/partners", headers=_auth(customer.id))
    assert resp.status_code == 200
    by_slug = {p["slug"]: p for p in resp.json()}

    assert by_slug["list-member"]["is_member"] is True
    assert by_slug["list-member"]["points_balance"] == 320
    assert by_slug["list-member"]["current_tier_name"] == "Bạc"

    assert by_slug["list-other"]["is_member"] is False
    assert by_slug["list-other"]["points_balance"] is None
    assert by_slug["list-other"]["current_tier_name"] is None


# ── GET /users/me/partners/{slug} ──


async def test_partner_detail_non_member(client: AsyncClient, db_session):
    """Customer chưa join: is_member=False, membership fields là null."""
    partner = await _make_active_partner(db_session, "Detail Shop", "detail-shop")
    customer = await _make_customer(db_session, "nonmember@test.com")

    resp = await client.get(f"/users/me/partners/{partner.slug}", headers=_auth(customer.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_member"] is False
    # points_balance luôn = ví toàn cục (mặc định 0 cho user mới)
    assert data["points_balance"] == 0
    assert data["lifetime_earned"] is None
    assert data["current_tier_name"] is None
    assert data["joined_at"] is None


async def test_partner_detail_member(client: AsyncClient, db_session):
    """Customer đã join: is_member=True, points_balance có giá trị."""
    partner = await _make_active_partner(db_session, "Member Shop", "member-shop")
    customer = await _make_customer(db_session, "member@test.com")

    customer.points_balance = 250
    membership = Membership(
        partner_id=partner.id,
        user_id=customer.id,
        lifetime_earned=250,
    )
    db_session.add(membership)
    await db_session.flush()

    resp = await client.get(f"/users/me/partners/{partner.slug}", headers=_auth(customer.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_member"] is True
    assert data["points_balance"] == 250
    assert data["lifetime_earned"] == 250


async def test_partner_detail_not_found(client: AsyncClient, db_session):
    """Partner không tồn tại → 404."""
    customer = await _make_customer(db_session, "ghost@test.com")
    resp = await client.get("/users/me/partners/nonexistent-slug", headers=_auth(customer.id))
    assert resp.status_code == 404


async def test_partner_detail_pending_not_found(client: AsyncClient, db_session):
    """Partner PENDING không được lộ ra — coi như 404."""
    pending_owner = User(email="pend2@test.com", password_hash="x", is_active=True)
    db_session.add(pending_owner)
    await db_session.flush()
    pending = Partner(
        name="Hidden Shop",
        slug="hidden-shop",
        owner_user_id=pending_owner.id,
        status=PartnerStatus.PENDING,
        settings={},
    )
    db_session.add(pending)
    await db_session.flush()

    customer = await _make_customer(db_session, "seeker@test.com")
    resp = await client.get("/users/me/partners/hidden-shop", headers=_auth(customer.id))
    assert resp.status_code == 404


async def test_partner_detail_unauthenticated(client: AsyncClient, db_session):
    partner = await _make_active_partner(db_session, "Auth Shop", "auth-shop")
    resp = await client.get(f"/users/me/partners/{partner.slug}")
    assert resp.status_code == 401
