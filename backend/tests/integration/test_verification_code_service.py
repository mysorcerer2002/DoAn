import pytest

from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)


@pytest.fixture
async def user(db_session):
    u = User(email="u@example.com", password_hash="x", is_active=True)
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.mark.asyncio
async def test_create_code_returns_6_digit(db_session, user):
    service = VerificationCodeService(db_session)
    plain = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    assert len(plain) == 6
    assert plain.isdigit()


@pytest.mark.asyncio
async def test_verify_correct_code(db_session, user):
    service = VerificationCodeService(db_session)
    plain = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    verified = await service.verify_code(
        user_id=user.id,
        code=plain,
        purpose=VerificationCodePurpose.CLAIM_SHADOW,
    )
    assert verified is True


@pytest.mark.asyncio
async def test_verify_wrong_code_raises(db_session, user):
    service = VerificationCodeService(db_session)
    await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    with pytest.raises(InvalidCodeError):
        await service.verify_code(
            user_id=user.id,
            code="000000",
            purpose=VerificationCodePurpose.CLAIM_SHADOW,
        )


@pytest.mark.asyncio
async def test_create_code_invalidates_old(db_session, user):
    service = VerificationCodeService(db_session)
    old = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()
    new = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    # Code cũ không còn dùng được
    with pytest.raises(InvalidCodeError):
        await service.verify_code(
            user_id=user.id, code=old, purpose=VerificationCodePurpose.CLAIM_SHADOW
        )
    # Code mới dùng được
    assert await service.verify_code(
        user_id=user.id, code=new, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )


@pytest.mark.asyncio
async def test_verify_used_code_raises(db_session, user):
    service = VerificationCodeService(db_session)
    plain = await service.create_code(
        user_id=user.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()
    await service.verify_code(
        user_id=user.id, code=plain, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    with pytest.raises(InvalidCodeError):
        await service.verify_code(
            user_id=user.id, code=plain, purpose=VerificationCodePurpose.CLAIM_SHADOW
        )
