"""Integration tests: Redemption service — redeem, use, edge cases."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, PointLedger
from app.models.reward import Reward, RewardOfferType
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.reward import RewardCreateRequest
from app.services.redemption_service import (
    InsufficientPointsError,
    OutOfStockError,
    RedemptionNotFoundError,
    RedemptionService,
)
from app.services.reward_service import RewardService


async def _setup_for_redemption(db_session, *, balance=500, stock=10):
    """Tạo partner, user/membership với balance global, và reward."""
    owner = User(email="rdm@example.com", password_hash="x", is_active=True)
    member_user = User(
        email="member@example.com", password_hash="x", is_active=True,
        phone="0901111111", points_balance=balance,
    )
    db_session.add_all([owner, member_user])
    await db_session.flush()

    partner = Partner(
        name="RedeemShop",
        slug="redeem-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    membership = Membership(
        partner_id=partner.id,
        user_id=member_user.id,
        lifetime_earned=balance,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    svc = RewardService(db_session)
    reward = await svc.create_reward(
        partner_id=partner.id,
        request=RewardCreateRequest(name="Reward Test", points_cost=100, stock=stock, offer_type=RewardOfferType.ITEM_GIFT, offer_label="Quà"),
    )
    await db_session.flush()

    return partner, owner, member_user, membership, reward


@pytest.mark.asyncio
async def test_redeem_success(db_session):
    partner, _owner, member_user, _membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    redemption = await svc.redeem(
        partner_id=partner.id,
        user_id=member_user.id,
        reward_id=reward.id,
    )
    assert redemption.points_spent == 100
    assert redemption.redemption_code is not None
    assert len(redemption.redemption_code) == 8
    assert redemption.status == "pending"

    await db_session.refresh(member_user)
    assert member_user.points_balance == 400


@pytest.mark.asyncio
async def test_redeem_insufficient_points(db_session):
    partner, _owner, member_user, _membership, reward = await _setup_for_redemption(
        db_session, balance=50
    )
    svc = RedemptionService(db_session)

    with pytest.raises(InsufficientPointsError):
        await svc.redeem(
            partner_id=partner.id,
            user_id=member_user.id,
            reward_id=reward.id,
        )


@pytest.mark.asyncio
async def test_redeem_out_of_stock(db_session):
    partner, _owner, member_user, _membership, reward = await _setup_for_redemption(
        db_session, balance=500, stock=0
    )
    svc = RedemptionService(db_session)

    with pytest.raises(OutOfStockError):
        await svc.redeem(
            partner_id=partner.id,
            user_id=member_user.id,
            reward_id=reward.id,
        )


@pytest.mark.asyncio
async def test_redeem_unlimited_stock(db_session):
    """Reward với stock=None = unlimited."""
    partner, _owner, member_user, _membership, reward = await _setup_for_redemption(
        db_session, balance=500, stock=10
    )
    reward.stock = None
    await db_session.flush()

    svc = RedemptionService(db_session)
    redemption = await svc.redeem(
        partner_id=partner.id,
        user_id=member_user.id,
        reward_id=reward.id,
    )
    assert redemption.points_spent == 100


@pytest.mark.asyncio
async def test_use_redemption(db_session):
    partner, owner, member_user, _membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    redemption = await svc.redeem(
        partner_id=partner.id,
        user_id=member_user.id,
        reward_id=reward.id,
    )
    code = redemption.redemption_code

    used = await svc.use_redemption(
        partner_id=partner.id, code=code, staff_id=owner.id
    )
    assert used.status == "used"
    assert used.used_by_staff_id == owner.id
    assert used.used_at is not None


@pytest.mark.asyncio
async def test_use_redemption_not_found(db_session):
    partner, owner, _member_user, _membership, _reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    with pytest.raises(RedemptionNotFoundError):
        await svc.use_redemption(
            partner_id=partner.id, code="ZZZZZZZZ", staff_id=owner.id
        )


@pytest.mark.asyncio
async def test_list_my_redemptions(db_session):
    partner, _owner, member_user, _membership, reward = await _setup_for_redemption(
        db_session, balance=1000
    )
    svc = RedemptionService(db_session)

    for _ in range(3):
        await svc.redeem(
            partner_id=partner.id,
            user_id=member_user.id,
            reward_id=reward.id,
        )

    results = await svc.list_my_redemptions(
        partner_id=partner.id, user_id=member_user.id
    )
    assert len(results) == 3


@pytest.mark.asyncio
async def test_redeem_creates_ledger_entry(db_session):
    """Đổi quà phải tạo entry trong point_ledger."""
    from sqlalchemy import select

    partner, _owner, member_user, _membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    await svc.redeem(
        partner_id=partner.id,
        user_id=member_user.id,
        reward_id=reward.id,
    )
    await db_session.flush()

    entries = await db_session.scalars(
        select(PointLedger).where(
            PointLedger.user_id == member_user.id,
            PointLedger.reason == LedgerReason.REDEEM,
        )
    )
    ledger_list = list(entries.all())
    assert len(ledger_list) == 1
    assert ledger_list[0].delta == -100
    assert ledger_list[0].balance_after == 400


@pytest.mark.asyncio
async def test_redeem_rejects_expired_reward(
    db_session, partner_factory, user_factory, reward_factory
):
    """Reward valid_until < today → ValueError (giữ generic message)."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=1000)
    reward = await reward_factory(
        db_session,
        partner_id=partner.id,
        points_cost=100,
        stock=10,
        valid_until=date.today() - timedelta(days=1),  # hết hạn hôm qua
    )
    from app.services.redemption_service import RedemptionService
    svc = RedemptionService(db_session)
    with pytest.raises(ValueError):
        await svc.redeem(partner_id=partner.id, user_id=user.id, reward_id=reward.id)


@pytest.mark.asyncio
async def test_redeem_accepts_today_boundary(
    db_session, partner_factory, user_factory, reward_factory
):
    """valid_until = today (inclusive) → success."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session, points_balance=1000)
    reward = await reward_factory(
        db_session,
        partner_id=partner.id,
        points_cost=100,
        stock=10,
        valid_until=date.today(),
    )
    # User cần membership để redeem
    from app.models.membership import Membership
    db_session.add(Membership(partner_id=partner.id, user_id=user.id))
    await db_session.flush()

    from app.services.redemption_service import RedemptionService
    svc = RedemptionService(db_session)
    redemption = await svc.redeem(partner_id=partner.id, user_id=user.id, reward_id=reward.id)
    assert redemption is not None
    assert redemption.status.value == "pending"
