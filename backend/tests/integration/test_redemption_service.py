"""Integration tests: Redemption service — redeem, use, edge cases."""

from datetime import datetime, timezone

import pytest

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, PointLedger
from app.models.point_rule import PointRule
from app.models.reward import Reward
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
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
    """Tạo tenant, membership với balance, và reward."""
    owner = User(email="rdm@example.com", password_hash="x", is_active=True)
    member_user = User(
        email="member@example.com", password_hash="x", is_active=True, phone="0901111111"
    )
    db_session.add_all([owner, member_user])
    await db_session.flush()

    tenant = Tenant(
        name="RedeemShop",
        slug="redeem-shop",
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

    membership = Membership(
        tenant_id=tenant.id,
        user_id=member_user.id,
        points_balance=balance,
        total_points_earned=balance,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.flush()

    svc = RewardService(db_session)
    reward = await svc.create_reward(
        tenant_id=tenant.id,
        request=RewardCreateRequest(name="Reward Test", points_cost=100, stock=stock),
    )
    await db_session.flush()

    return tenant, owner, member_user, membership, reward


@pytest.mark.asyncio
async def test_redeem_success(db_session):
    tenant, owner, _member, membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    redemption = await svc.redeem(
        tenant_id=tenant.id,
        membership_id=membership.id,
        reward_id=reward.id,
    )
    assert redemption.points_spent == 100
    assert redemption.redemption_code is not None
    assert len(redemption.redemption_code) == 8
    assert redemption.status.value == "pending"

    # Balance giảm
    assert membership.points_balance == 400


@pytest.mark.asyncio
async def test_redeem_insufficient_points(db_session):
    tenant, owner, _member, membership, reward = await _setup_for_redemption(
        db_session, balance=50
    )
    svc = RedemptionService(db_session)

    with pytest.raises(InsufficientPointsError):
        await svc.redeem(
            tenant_id=tenant.id,
            membership_id=membership.id,
            reward_id=reward.id,
        )


@pytest.mark.asyncio
async def test_redeem_out_of_stock(db_session):
    tenant, owner, _member, membership, reward = await _setup_for_redemption(
        db_session, balance=500, stock=0
    )
    svc = RedemptionService(db_session)

    with pytest.raises(OutOfStockError):
        await svc.redeem(
            tenant_id=tenant.id,
            membership_id=membership.id,
            reward_id=reward.id,
        )


@pytest.mark.asyncio
async def test_redeem_unlimited_stock(db_session):
    """Reward với stock=None = unlimited."""
    tenant, owner, _member, membership, reward = await _setup_for_redemption(
        db_session, balance=500, stock=10
    )
    # Override stock to NULL (unlimited)
    reward.stock = None
    await db_session.flush()

    svc = RedemptionService(db_session)
    redemption = await svc.redeem(
        tenant_id=tenant.id,
        membership_id=membership.id,
        reward_id=reward.id,
    )
    assert redemption.points_spent == 100


@pytest.mark.asyncio
async def test_use_redemption(db_session):
    tenant, owner, _member, membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    redemption = await svc.redeem(
        tenant_id=tenant.id,
        membership_id=membership.id,
        reward_id=reward.id,
    )
    code = redemption.redemption_code

    used = await svc.use_redemption(
        tenant_id=tenant.id, code=code, staff_id=owner.id
    )
    assert used.status.value == "used"
    assert used.used_by_staff_id == owner.id
    assert used.used_at is not None


@pytest.mark.asyncio
async def test_use_redemption_not_found(db_session):
    tenant, owner, _member, membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    with pytest.raises(RedemptionNotFoundError):
        await svc.use_redemption(
            tenant_id=tenant.id, code="ZZZZZZZZ", staff_id=owner.id
        )


@pytest.mark.asyncio
async def test_list_my_redemptions(db_session):
    tenant, owner, _member, membership, reward = await _setup_for_redemption(
        db_session, balance=1000
    )
    svc = RedemptionService(db_session)

    # Đổi 3 lần
    for _ in range(3):
        await svc.redeem(
            tenant_id=tenant.id,
            membership_id=membership.id,
            reward_id=reward.id,
        )

    results = await svc.list_my_redemptions(
        tenant_id=tenant.id, membership_id=membership.id
    )
    assert len(results) == 3


@pytest.mark.asyncio
async def test_redeem_creates_ledger_entry(db_session):
    """Đổi quà phải tạo entry trong point_ledger."""
    from sqlalchemy import select

    tenant, _owner, _member, membership, reward = await _setup_for_redemption(db_session)
    svc = RedemptionService(db_session)

    await svc.redeem(
        tenant_id=tenant.id,
        membership_id=membership.id,
        reward_id=reward.id,
    )
    await db_session.flush()

    entries = await db_session.scalars(
        select(PointLedger).where(
            PointLedger.membership_id == membership.id,
            PointLedger.reason == LedgerReason.REDEEM,
        )
    )
    ledger_list = list(entries.all())
    assert len(ledger_list) == 1
    assert ledger_list[0].delta == -100
    assert ledger_list[0].balance_after == 400
