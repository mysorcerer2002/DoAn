import pytest


@pytest.mark.asyncio
async def test_decode_qr_payload_auto_enrolls_when_not_member(
    db_session, partner_factory, user_factory
):
    """User chưa là member shop → decode_qr_payload tự tạo membership."""
    partner = await partner_factory(db_session)
    user = await user_factory(db_session)
    from app.services.qr_service import QrService

    svc = QrService(db_session)
    returned_user, membership = await svc.decode_qr_payload(
        payload=str(user.id), partner_id=partner.id
    )
    assert returned_user.id == user.id
    assert membership is not None
    assert membership.partner_id == partner.id
    assert membership.user_id == user.id
    assert membership.lifetime_earned == 0
    assert membership.current_tier_id is None


@pytest.mark.asyncio
async def test_decode_qr_payload_invalid(db_session, partner_factory):
    partner = await partner_factory(db_session)
    from app.services.qr_service import QrPayloadInvalidError, QrService

    svc = QrService(db_session)
    with pytest.raises(QrPayloadInvalidError):
        await svc.decode_qr_payload(payload="abc", partner_id=partner.id)
    with pytest.raises(QrPayloadInvalidError):
        await svc.decode_qr_payload(payload="0", partner_id=partner.id)


@pytest.mark.asyncio
async def test_decode_qr_payload_user_not_found(db_session, partner_factory):
    partner = await partner_factory(db_session)
    from app.services.qr_service import QrService, QrUserNotFoundError

    svc = QrService(db_session)
    with pytest.raises(QrUserNotFoundError):
        await svc.decode_qr_payload(payload="99999999", partner_id=partner.id)
