import pytest
from sqlalchemy import select

from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_settings_audit import TenantSettingsAudit
from app.models.user import User
from app.schemas.settings import SettingsUpdateRequest, TenantSettings
from app.services.settings_service import SettingsService


@pytest.fixture
async def tenant_with_owner(db_session):
    user = User(email="o@example.com", password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    tenant = Tenant(
        name="T", slug="t", owner_user_id=user.id,
        status=TenantStatus.ACTIVE, settings={}
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant, user


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(db_session, tenant_with_owner):
    tenant, _user = tenant_with_owner
    service = SettingsService(db_session)
    settings = await service.get_settings(tenant_id=tenant.id)
    assert isinstance(settings, TenantSettings)
    assert settings.points_on_gross is False
    assert settings.voucher_default_ttl_days == 30


@pytest.mark.asyncio
async def test_update_settings_writes_audit(db_session, tenant_with_owner):
    tenant, user = tenant_with_owner
    service = SettingsService(db_session)
    new = await service.update_settings(
        tenant_id=tenant.id,
        user_id=user.id,
        request=SettingsUpdateRequest(points_on_gross=True, voucher_default_ttl_days=60),
    )
    assert new.points_on_gross is True
    assert new.voucher_default_ttl_days == 60

    audits = await db_session.scalars(
        select(TenantSettingsAudit).where(TenantSettingsAudit.tenant_id == tenant.id)
    )
    audit_list = list(audits.all())
    assert len(audit_list) == 2
    keys = {a.field_key for a in audit_list}
    assert keys == {"points_on_gross", "voucher_default_ttl_days"}
