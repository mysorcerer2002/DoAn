import pytest
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.partner import Partner, PartnerStatus
from app.models.user import User


@pytest.fixture
async def user_membership(db_session):
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
        lifetime_earned=0, joined_at=datetime.now(timezone.utc)
    )
    db_session.add(m)
    await db_session.flush()
    return user, m


@pytest.mark.asyncio
async def test_can_insert_ledger_entry(db_session, user_membership):
    user, m = user_membership
    entry = PointLedger(
        partner_id=m.partner_id,
        user_id=user.id,
        delta=100,
        reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL,
        balance_after=100,
    )
    db_session.add(entry)
    await db_session.flush()
    assert entry.id is not None


@pytest.mark.asyncio
async def test_cannot_update_ledger_entry(db_session, user_membership):
    user, m = user_membership
    entry = PointLedger(
        partner_id=m.partner_id,
        user_id=user.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, balance_after=100,
    )
    db_session.add(entry)
    await db_session.flush()
    entry_id = entry.id

    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("UPDATE point_ledger SET delta = 0 WHERE id = :id"),
            {"id": entry_id},
        )
    assert "append-only" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_cannot_delete_ledger_entry(db_session, user_membership):
    user, m = user_membership
    entry = PointLedger(
        partner_id=m.partner_id,
        user_id=user.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, balance_after=100,
    )
    db_session.add(entry)
    await db_session.flush()
    entry_id = entry.id

    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("DELETE FROM point_ledger WHERE id = :id"),
            {"id": entry_id},
        )
    assert "append-only" in str(exc_info.value).lower()
