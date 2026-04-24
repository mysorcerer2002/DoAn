import pytest
from datetime import datetime, timezone

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.services.ledger_service import LedgerService


@pytest.fixture
async def membership_with_balance(db_session):
    user = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=user.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    m = Membership(
        partner_id=partner.id, user_id=user.id,
        points_balance=0, total_points_earned=0,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.mark.asyncio
async def test_log_entry_creates_record(db_session, membership_with_balance):
    service = LedgerService(db_session)
    entry = await service.log_entry(
        partner_id=membership_with_balance.partner_id,
        membership_id=membership_with_balance.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=100,
        description="Test entry",
    )
    assert entry.id is not None
    assert entry.delta == 100
    assert entry.balance_after == 100


@pytest.mark.asyncio
async def test_get_history_paginated(db_session, membership_with_balance):
    service = LedgerService(db_session)
    for i in range(5):
        await service.log_entry(
            partner_id=membership_with_balance.partner_id,
            membership_id=membership_with_balance.id,
            delta=10,
            reason=LedgerReason.EARN,
            ref_type=LedgerRefType.MANUAL,
            ref_id=None,
            new_balance=10 * (i + 1),
        )
    await db_session.flush()

    history = await service.get_history(
        partner_id=membership_with_balance.partner_id,
        membership_id=membership_with_balance.id,
        limit=3,
    )
    assert len(history) == 3
    assert history[0].balance_after >= history[-1].balance_after


@pytest.mark.asyncio
async def test_reconcile_consistent(db_session, membership_with_balance):
    service = LedgerService(db_session)
    membership_with_balance.points_balance = 50
    await service.log_entry(
        partner_id=membership_with_balance.partner_id,
        membership_id=membership_with_balance.id,
        delta=50,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=50,
    )
    await db_session.flush()

    result = await service.reconcile(
        partner_id=membership_with_balance.partner_id,
        membership_id=membership_with_balance.id,
    )
    assert result.is_consistent is True
    assert result.diff == 0


@pytest.mark.asyncio
async def test_reconcile_inconsistent_detects_diff(db_session, membership_with_balance):
    service = LedgerService(db_session)
    membership_with_balance.points_balance = 50
    await service.log_entry(
        partner_id=membership_with_balance.partner_id,
        membership_id=membership_with_balance.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        ref_id=None,
        new_balance=100,
    )
    await db_session.flush()

    result = await service.reconcile(
        partner_id=membership_with_balance.partner_id,
        membership_id=membership_with_balance.id,
    )
    assert result.is_consistent is False
    assert result.diff == 50
    assert result.expected_balance == 100
    assert result.actual_balance == 50
