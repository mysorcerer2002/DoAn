"""Integration tests: Rewards API CRUD."""

import pytest

from app.core.security import create_access_token
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.user import User


async def _setup_shop(db_session):
    owner = User(email="rewardapi@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="RewardAPIShop",
        slug="reward-api-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    db_session.add(
        TenantStaff(
            tenant_id=tenant.id,
            user_id=owner.id,
            role=TenantStaffRole.OWNER,
        )
    )
    await db_session.flush()

    token = create_access_token(user_id=owner.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": str(tenant.id),
    }
    return tenant, owner, headers


@pytest.mark.asyncio
async def test_create_reward_api(client, db_session):
    _tenant, _owner, headers = await _setup_shop(db_session)

    resp = await client.post(
        "/merchant/rewards",
        json={"name": "Free Coffee", "points_cost": 100, "stock": 50},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Free Coffee"
    assert data["points_cost"] == 100
    assert data["stock"] == 50
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_rewards_api(client, db_session):
    _tenant, _owner, headers = await _setup_shop(db_session)

    await client.post(
        "/merchant/rewards",
        json={"name": "Reward A", "points_cost": 50},
        headers=headers,
    )
    await client.post(
        "/merchant/rewards",
        json={"name": "Reward B", "points_cost": 100},
        headers=headers,
    )

    resp = await client.get("/merchant/rewards", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_reward_api(client, db_session):
    _tenant, _owner, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/rewards",
        json={"name": "Get Me", "points_cost": 75},
        headers=headers,
    )
    reward_id = create_resp.json()["id"]

    resp = await client.get(f"/merchant/rewards/{reward_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


@pytest.mark.asyncio
async def test_update_reward_api(client, db_session):
    _tenant, _owner, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/rewards",
        json={"name": "Old", "points_cost": 50},
        headers=headers,
    )
    reward_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/merchant/rewards/{reward_id}",
        json={"name": "Updated", "points_cost": 200},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["points_cost"] == 200


@pytest.mark.asyncio
async def test_delete_reward_api(client, db_session):
    _tenant, _owner, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/rewards",
        json={"name": "Delete Me", "points_cost": 30},
        headers=headers,
    )
    reward_id = create_resp.json()["id"]

    resp = await client.delete(f"/merchant/rewards/{reward_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is not None


@pytest.mark.asyncio
async def test_get_deleted_reward_returns_404(client, db_session):
    _tenant, _owner, headers = await _setup_shop(db_session)

    create_resp = await client.post(
        "/merchant/rewards",
        json={"name": "Will Delete", "points_cost": 30},
        headers=headers,
    )
    reward_id = create_resp.json()["id"]

    await client.delete(f"/merchant/rewards/{reward_id}", headers=headers)

    resp = await client.get(f"/merchant/rewards/{reward_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_staff_cannot_create_reward(client, db_session):
    """Staff (không phải owner) không được tạo reward."""
    owner = User(email="ownerr@example.com", password_hash="x", is_active=True)
    staff_user = User(email="staffr@example.com", password_hash="x", is_active=True)
    db_session.add_all([owner, staff_user])
    await db_session.flush()

    tenant = Tenant(
        name="StaffTestShop",
        slug="staff-test-shop",
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
            user_id=staff_user.id,
            role=TenantStaffRole.STAFF,
        ),
    ])
    await db_session.flush()

    staff_token = create_access_token(user_id=staff_user.id)
    staff_headers = {
        "Authorization": f"Bearer {staff_token}",
        "X-Tenant-Id": str(tenant.id),
    }

    resp = await client.post(
        "/merchant/rewards",
        json={"name": "No Access", "points_cost": 50},
        headers=staff_headers,
    )
    assert resp.status_code == 403
