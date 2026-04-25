import pytest

from app.models.partner import Partner, PartnerStatus
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
    assert settings.redemption_default_ttl_days == 14


@pytest.mark.asyncio
async def test_update_settings_persists_changes(db_session, partner_with_owner):
    partner, user = partner_with_owner
    service = SettingsService(db_session)
    new = await service.update_settings(
        partner_id=partner.id,
        request=SettingsUpdateRequest(points_on_gross=True, redemption_default_ttl_days=60),
    )
    assert new.points_on_gross is True
    assert new.redemption_default_ttl_days == 60

    refetched = await service.get_settings(partner_id=partner.id)
    assert refetched.points_on_gross is True
    assert refetched.redemption_default_ttl_days == 60
