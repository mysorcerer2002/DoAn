import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models.point_rule import PointRule
from app.models.partner import Partner, PartnerStatus
from app.models.tier import Tier
from app.models.user import User
from app.schemas.transaction import CreateManualTransactionRequest
from app.services.transaction_service import (
    NoActivePointRuleError,
    TransactionService,
)
from tests.helpers.ledger_invariant import assert_ledger_invariant


@pytest.fixture
async def shop_with_rule_and_tiers(db_session):
    owner = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()
    partner = Partner(
        name="Shop", slug="shop", owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()

    rule = PointRule(
        partner_id=partner.id,
        points_per_unit=Decimal("1.00"),
        unit_amount=1000,
        min_amount=0,
        is_active=True,
    )
    db_session.add(rule)

    bronze = Tier(partner_id=partner.id, name="Bronze", min_points=0, perks={}, is_active=True)
    silver = Tier(partner_id=partner.id, name="Silver", min_points=500, perks={}, is_active=True)
    db_session.add_all([bronze, silver])
    await db_session.flush()

    return {"partner": partner, "owner": owner, "rule": rule, "bronze": bronze, "silver": silver}


@pytest.mark.asyncio
async def test_create_manual_transaction_brand_new_customer(
    db_session, shop_with_rule_and_tiers
):
    """Khách mới hoàn toàn → tạo user shadow + membership + transaction + ledger."""
    ctx = shop_with_rule_and_tiers
    service = TransactionService(db_session)

    result = await service.create_manual(
        partner_id=ctx["tenant"].id,
        request=CreateManualTransactionRequest(phone="0912345678", gross_amount=50000),
    )
    await db_session.flush()

    assert result.transaction.points_earned == 50  # 50000 / 1000 * 1.00
    assert result.new_balance == 50
    assert result.new_total_earned == 50
    assert result.new_tier_name == "Bronze"
    assert result.tier_upgraded is False

    await assert_ledger_invariant(db_session, result.transaction.membership_id)


@pytest.mark.asyncio
async def test_create_transaction_triggers_tier_upgrade(
    db_session, shop_with_rule_and_tiers
):
    """Tích đủ 500 điểm → upgrade Bronze → Silver."""
    ctx = shop_with_rule_and_tiers
    service = TransactionService(db_session)

    # Lần 1: 450000 VND → 450 điểm → vẫn Bronze
    r1 = await service.create_manual(
        partner_id=ctx["tenant"].id,
        request=CreateManualTransactionRequest(phone="0911111111", gross_amount=450000),
    )
    await db_session.flush()
    assert r1.new_tier_name == "Bronze"
    assert r1.tier_upgraded is False

    # Lần 2: 100000 VND → 100 điểm → tổng 550 → Silver
    r2 = await service.create_manual(
        partner_id=ctx["tenant"].id,
        request=CreateManualTransactionRequest(phone="0911111111", gross_amount=100000),
    )
    await db_session.flush()
    assert r2.new_total_earned == 550
    assert r2.new_tier_name == "Silver"
    assert r2.tier_upgraded is True

    await assert_ledger_invariant(db_session, r2.transaction.membership_id)


@pytest.mark.asyncio
async def test_create_transaction_without_active_rule_raises(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=user.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()

    service = TransactionService(db_session)
    with pytest.raises(NoActivePointRuleError):
        await service.create_manual(
            partner_id=partner.id,
            request=CreateManualTransactionRequest(phone="0912345678", gross_amount=50000),
        )


@pytest.mark.asyncio
async def test_create_transaction_below_min_amount_zero_points(db_session):
    """gross < min_amount → 0 điểm nhưng vẫn tạo transaction."""
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=user.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()

    rule = PointRule(
        partner_id=partner.id, points_per_unit=Decimal("1.00"),
        unit_amount=1000, min_amount=100000, is_active=True
    )
    db_session.add(rule)
    bronze = Tier(partner_id=partner.id, name="Bronze", min_points=0, perks={}, is_active=True)
    db_session.add(bronze)
    await db_session.flush()

    service = TransactionService(db_session)
    result = await service.create_manual(
        partner_id=partner.id,
        request=CreateManualTransactionRequest(phone="0912345678", gross_amount=50000),
    )
    await db_session.flush()
    assert result.transaction.points_earned == 0
    assert result.new_balance == 0
