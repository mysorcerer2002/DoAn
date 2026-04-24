import pytest
from sqlalchemy import select

from app.models.partner import Partner, PartnerStatus
from app.models.partner_settings_audit import PartnerSettingsAudit
from app.models.user import User
from app.schemas.settings import SettingsUpdateRequest, PartnerSettings
from app.services.settings_service import SettingsService


@pytest.fixture
async def partner_with_owner(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    partner = Partner(
        name="T", slug="t", owner_user_id=user.id,
        status=PartnerStatus.ACTIVE, settings={}
    )
    db_session.add(partner)
    await db_session.flush()
    return partner, user


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(db_session, partner_with_owner):
    partner, _user = partner_with_owner
    service = SettingsService(db_session)
    settings = await service.get_settings(partner_id=partner.id)
    assert isinstance(settings, PartnerSettings)
    assert settings.points_on_gross is False
    assert settings.voucher_default_ttl_days == 30


@pytest.mark.asyncio
async def test_update_settings_writes_audit(db_session, partner_with_owner):
    partner, user = partner_with_owner
    service = SettingsService(db_session)
    new = await service.update_settings(
        partner_id=partner.id,
        user_id=user.id,
        request=SettingsUpdateRequest(points_on_gross=True, voucher_default_ttl_days=60),
    )
    assert new.points_on_gross is True
    assert new.voucher_default_ttl_days == 60

    audits = await db_session.scalars(
        select(PartnerSettingsAudit).where(PartnerSettingsAudit.partner_id == partner.id)
    )
    audit_list = list(audits.all())
    assert len(audit_list) == 2
    keys = {a.field_key for a in audit_list}
    assert keys == {"points_on_gross", "voucher_default_ttl_days"}
