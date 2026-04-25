import pytest
from datetime import datetime, timezone

from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType
from app.models.point_rule import PointRule
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.transaction import CreateManualTransactionRequest
from app.services.ledger_service import LedgerService
from app.services.transaction_service import TransactionService
from tests.helpers.ledger_invariant import assert_ledger_invariant


@pytest.fixture
async def membership_for_invariant(db_session):
    user = User(email="inv@example.com", password_hash="x", is_active=True)
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
async def test_invariant_after_earn(db_session, membership_for_invariant):
    m = membership_for_invariant
    service = LedgerService(db_session)
    m.points_balance = 100
    await service.log_entry(
        partner_id=m.partner_id, membership_id=m.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, ref_id=None,
        new_balance=100,
    )
    await db_session.flush()
    await assert_ledger_invariant(db_session, m.id)


@pytest.mark.asyncio
async def test_invariant_after_earn_and_redeem(db_session, membership_for_invariant):
    m = membership_for_invariant
    service = LedgerService(db_session)
    m.points_balance = 100
    await service.log_entry(
        partner_id=m.partner_id, membership_id=m.id,
        delta=100, reason=LedgerReason.EARN,
        ref_type=LedgerRefType.MANUAL, ref_id=None,
        new_balance=100,
    )
    m.points_balance = 60
    await service.log_entry(
        partner_id=m.partner_id, membership_id=m.id,
        delta=-40, reason=LedgerReason.REDEEM,
        ref_type=LedgerRefType.MANUAL, ref_id=None,
        new_balance=60,
    )
    await db_session.flush()
    await assert_ledger_invariant(db_session, m.id)


@pytest.mark.asyncio
async def test_invariant_e2e_via_transaction_service(db_session):
    """E2E: TransactionService tạo giao dịch -> invariant vẫn đúng."""
    owner = User(email="e2e-inv@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="E2E",
        slug="e2e-inv",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()
    rule = PointRule(
        partner_id=partner.id,
        points_per_unit=2,
        unit_amount=1000,
        min_amount=0,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    tx_service = TransactionService(db_session)

    # Tạo 3 giao dịch liên tiếp cho cùng 1 SĐT
    for amount in [10_000, 25_000, 50_000]:
        result = await tx_service.create_manual(
            partner_id=partner.id,
            request=CreateManualTransactionRequest(
                phone="0901234567", gross_amount=amount
            ),
        )

    # Kiểm tra invariant
    membership_id = result.transaction.membership_id
    await assert_ledger_invariant(db_session, membership_id)
