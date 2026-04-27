"""Integration tests: Reward service CRUD + soft delete."""

from datetime import timezone

import pytest
import pytest_asyncio

from app.models.reward import Reward, RewardOfferType
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.services.reward_service import RewardNotFoundError, RewardService
from app.schemas.reward import RewardCreateRequest, RewardUpdateRequest


async def _make_partner(db_session) -> tuple:
    owner = User(email="reward@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="RewardShop",
        slug="reward-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()
    return partner, owner


@pytest.mark.asyncio
async def test_create_reward(db_session):
    tenant, _owner = await _make_tenant(db_session)
    svc = RewardService(db_session)

    req = RewardCreateRequest(
        name="Ly nước miễn phí",
        description="Đổi 100 điểm lấy 1 ly coffee",
        points_cost=100,
        stock=50,
        offer_type=RewardOfferType.ITEM_GIFT,
        offer_label="Quà",
    )
    reward = await svc.create_reward(partner_id=partner.id, request=req)
    assert reward.id is not None
    assert reward.name == "Ly nước miễn phí"
    assert reward.points_cost == 100
    assert reward.stock == 50
    assert reward.is_active is True


@pytest.mark.asyncio
async def test_create_reward_unlimited_stock(db_session):
    tenant, _owner = await _make_tenant(db_session)
    svc = RewardService(db_session)

    req = RewardCreateRequest(
        name="Giảm giá 10%",
        points_cost=50,
        stock=None,
        offer_type=RewardOfferType.PERCENT_DISCOUNT,
        offer_value=10,
        offer_label="Giảm 10%",
    )
    reward = await svc.create_reward(partner_id=partner.id, request=req)
    assert reward.stock is None  # unlimited


@pytest.mark.asyncio
async def test_list_rewards(db_session):
    tenant, _owner = await _make_tenant(db_session)
    svc = RewardService(db_session)

    for i in range(3):
        await svc.create_reward(
            partner_id=partner.id,
            request=RewardCreateRequest(name=f"Reward {i}", points_cost=100, offer_type=RewardOfferType.ITEM_GIFT, offer_label="Quà"),
        )

    rewards = await svc.list_rewards(partner_id=partner.id)
    assert len(rewards) == 3


@pytest.mark.asyncio
async def test_update_reward(db_session):
    tenant, _owner = await _make_tenant(db_session)
    svc = RewardService(db_session)

    reward = await svc.create_reward(
        partner_id=partner.id,
        request=RewardCreateRequest(name="Old Name", points_cost=100, offer_type=RewardOfferType.ITEM_GIFT, offer_label="Quà"),
    )
    updated = await svc.update_reward(
        partner_id=partner.id,
        reward_id=reward.id,
        request=RewardUpdateRequest(name="New Name", points_cost=200),
    )
    assert updated.name == "New Name"
    assert updated.points_cost == 200


@pytest.mark.asyncio
async def test_soft_delete_reward(db_session):
    tenant, _owner = await _make_tenant(db_session)
    svc = RewardService(db_session)

    reward = await svc.create_reward(
        partner_id=partner.id,
        request=RewardCreateRequest(name="Deletable", points_cost=50, offer_type=RewardOfferType.ITEM_GIFT, offer_label="Quà"),
    )
    deleted = await svc.soft_delete_reward(partner_id=partner.id, reward_id=reward.id)
    assert deleted.deleted_at is not None
    assert deleted.is_active is False

    # Active-only list should not include it
    active_list = await svc.list_rewards(partner_id=partner.id, active_only=True)
    assert len(active_list) == 0


@pytest.mark.asyncio
async def test_get_reward_not_found(db_session):
    tenant, _owner = await _make_tenant(db_session)
    svc = RewardService(db_session)

    with pytest.raises(RewardNotFoundError):
        await svc.get_reward(partner_id=partner.id, reward_id=99999)
