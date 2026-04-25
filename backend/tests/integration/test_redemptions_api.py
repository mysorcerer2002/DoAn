"""Integration tests: Redemptions API."""

from datetime import datetime, timezone

import pytest

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.point_rule import PointRule
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.reward import RewardCreateRequest
from app.services.reward_service import RewardService


async def _setup_redeem_env(db_session, *, balance=500, stock=10):
    """Tạo tenant, owner, member (với balance), và reward."""
    owner = User(email="rdmapi@example.com", password_hash="x", is_active=True)
    member_user = User(
        email="memberapi@example.com",
        password_hash="x",
        is_active=True,
        phone="0909876543",
    )
    db_session.add_all([owner, member_user])
    await db_session.flush()

    partner = Partner(
        name="RedeemAPIShop",
        slug="redeem-api-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    db_session.add_all([
    ])

    member_user.points_balance = balance
    membership = Membership(
        partner_id=partner.id,
        user_id=member_user.id,
        lifetime_earned=balance,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)

    rule = PointRule(
        partner_id=partner.id,
        points_per_unit=1,
        unit_amount=1000,
        min_amount=0,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    svc = RewardService(db_session)
    reward = await svc.create_reward(
        partner_id=partner.id,
        request=RewardCreateRequest(name="API Reward", points_cost=100, stock=stock),
    )
    await db_session.flush()

    owner_token = create_access_token(user_id=owner.id)
    owner_headers = {
        "Authorization": f"Bearer {owner_token}",
        "X-Partner-Id": str(partner.id),
    }

    member_token = create_access_token(user_id=member_user.id)
    member_headers = {
        "Authorization": f"Bearer {member_token}",
        "X-Partner-Id": str(partner.id),
    }

    return partner, owner, member_user, membership, reward, owner_headers, member_headers


@pytest.mark.asyncio
async def test_redeem_api_for_member(client, db_session):
    """Staff đổi quà cho member qua API."""
    (
        _tenant, _owner, _member, membership, reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session)

    resp = await client.post(
        f"/partner/redemptions/for-member/{membership.id}",
        json={"reward_id": reward.id},
        headers=owner_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["points_spent"] == 100
    assert data["redemption_code"] is not None
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_redeem_api_self(client, db_session):
    """Khách tự đổi quà qua /users/me/redemptions — derive partner từ reward."""
    (
        _tenant, _owner, _member, _membership, reward, _owner_headers, member_headers
    ) = await _setup_redeem_env(db_session)

    # Customer flow không gửi X-Partner-Id; chỉ cần Authorization.
    auth_only = {"Authorization": member_headers["Authorization"]}
    resp = await client.post(
        "/users/me/redemptions",
        json={"reward_id": reward.id},
        headers=auth_only,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_use_redemption_api(client, db_session):
    (
        _tenant, _owner, _member, membership, reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session)

    # Đổi quà
    create_resp = await client.post(
        f"/partner/redemptions/for-member/{membership.id}",
        json={"reward_id": reward.id},
        headers=owner_headers,
    )
    code = create_resp.json()["redemption_code"]

    # Xác nhận sử dụng
    resp = await client.post(
        "/partner/redemptions/use",
        json={"code": code},
        headers=owner_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "used"


@pytest.mark.asyncio
async def test_list_redemptions_api(client, db_session):
    (
        _tenant, _owner, _member, membership, reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session, balance=1000)

    # Đổi 2 lần
    for _ in range(2):
        await client.post(
            f"/partner/redemptions/for-member/{membership.id}",
            json={"reward_id": reward.id},
            headers=owner_headers,
        )

    resp = await client.get("/partner/redemptions", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_redeem_insufficient_points_api(client, db_session):
    (
        _tenant, _owner, _member, membership, reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session, balance=10)

    resp = await client.post(
        f"/partner/redemptions/for-member/{membership.id}",
        json={"reward_id": reward.id},
        headers=owner_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_use_invalid_code_api(client, db_session):
    (
        _tenant, _owner, _member, _membership, _reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session)

    resp = await client.post(
        "/partner/redemptions/use",
        json={"code": "ZZZZZZZZ"},
        headers=owner_headers,
    )
    assert resp.status_code == 404
