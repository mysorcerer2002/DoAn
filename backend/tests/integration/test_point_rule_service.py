from decimal import Decimal

import pytest

from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.point_rule import PointRuleCreateRequest
from app.services.point_rule_service import PointRuleService


@pytest.fixture
async def active_partner(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=user.id, status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    return partner


@pytest.mark.asyncio
async def test_create_first_active_rule(db_session, active_partner):
    service = PointRuleService(db_session)
    rule = await service.create_rule(
        partner_id=active_partner.id,
        request=PointRuleCreateRequest(earn_percent=Decimal("1.00")),
    )
    assert rule.is_active is True
    assert rule.earn_percent == Decimal("1.00")


@pytest.mark.asyncio
async def test_create_second_rule_deactivates_old(db_session, active_partner):
    service = PointRuleService(db_session)
    old = await service.create_rule(
        partner_id=active_partner.id,
        request=PointRuleCreateRequest(earn_percent=Decimal("1.00")),
    )
    await db_session.flush()
    new = await service.create_rule(
        partner_id=active_partner.id,
        request=PointRuleCreateRequest(earn_percent=Decimal("2.00")),
    )
    await db_session.flush()
    await db_session.refresh(old)
    assert old.is_active is False
    assert new.is_active is True


@pytest.mark.asyncio
async def test_get_active_rule(db_session, active_partner):
    service = PointRuleService(db_session)
    await service.create_rule(
        partner_id=active_partner.id,
        request=PointRuleCreateRequest(earn_percent=Decimal("1.00")),
    )
    await db_session.flush()

    rule = await service.get_active_rule(partner_id=active_partner.id)
    assert rule is not None
    assert rule.earn_percent == Decimal("1.00")


@pytest.mark.asyncio
async def test_get_active_rule_none_when_no_rule(db_session, active_partner):
    service = PointRuleService(db_session)
    rule = await service.get_active_rule(partner_id=active_partner.id)
    assert rule is None
