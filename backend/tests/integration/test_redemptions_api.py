"""Integration tests: Redemptions API."""

from datetime import datetime, timezone

import pytest

from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.point_rule import PointRule
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
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

    tenant = Tenant(
        name="RedeemAPIShop",
        slug="redeem-api-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    db_session.add_all([
        TenantStaff(
            tenant_id=tenant.id,
            user_id=owner.id,
            role=TenantStaffRole.OWNER,
        ),
        TenantStaff(
            tenant_id=tenant.id,
            user_id=member_user.id,
            role=TenantStaffRole.STAFF,
        ),
    ])

    membership = Membership(
        tenant_id=tenant.id,
        user_id=member_user.id,
        points_balance=balance,
        total_points_earned=balance,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)

    rule = PointRule(
        tenant_id=tenant.id,
        points_per_unit=1,
        unit_amount=1000,
        min_amount=0,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    svc = RewardService(db_session)
    reward = await svc.create_reward(
        tenant_id=tenant.id,
        request=RewardCreateRequest(name="API Reward", points_cost=100, stock=stock),
    )
    await db_session.flush()

    owner_token = create_access_token(user_id=owner.id)
    owner_headers = {
        "Authorization": f"Bearer {owner_token}",
        "X-Tenant-Id": str(tenant.id),
    }

    member_token = create_access_token(user_id=member_user.id)
    member_headers = {
        "Authorization": f"Bearer {member_token}",
        "X-Tenant-Id": str(tenant.id),
    }

    return tenant, owner, member_user, membership, reward, owner_headers, member_headers


@pytest.mark.asyncio
async def test_redeem_api_for_member(client, db_session):
    """Staff đổi quà cho member qua API."""
    (
        _tenant, _owner, _member, membership, reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session)

    resp = await client.post(
        f"/merchant/redemptions/for-member/{membership.id}",
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
    """Khách tự đổi quà (cần staff trong tenant)."""
    (
        _tenant, _owner, _member, _membership, reward, _owner_headers, member_headers
    ) = await _setup_redeem_env(db_session)

    resp = await client.post(
        "/merchant/redemptions",
        json={"reward_id": reward.id},
        headers=member_headers,
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
        f"/merchant/redemptions/for-member/{membership.id}",
        json={"reward_id": reward.id},
        headers=owner_headers,
    )
    code = create_resp.json()["redemption_code"]

    # Xác nhận sử dụng
    resp = await client.post(
        "/merchant/redemptions/use",
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
            f"/merchant/redemptions/for-member/{membership.id}",
            json={"reward_id": reward.id},
            headers=owner_headers,
        )

    resp = await client.get("/merchant/redemptions", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_redeem_insufficient_points_api(client, db_session):
    (
        _tenant, _owner, _member, membership, reward, owner_headers, _member_headers
    ) = await _setup_redeem_env(db_session, balance=10)

    resp = await client.post(
        f"/merchant/redemptions/for-member/{membership.id}",
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
        "/merchant/redemptions/use",
        json={"code": "ZZZZZZZZ"},
        headers=owner_headers,
    )
    assert resp.status_code == 404
