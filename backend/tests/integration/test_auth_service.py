import pytest

from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService, EmailAlreadyExistsError, InvalidCredentialsError


@pytest.mark.asyncio
async def test_register_creates_user(db_session):
    service = AuthService(db_session)
    request = RegisterRequest(
        email="alice@example.com",
        password="supersecret123",
        full_name="Alice",
    )
    user = await service.register(request)
    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.full_name == "Alice"
    assert user.password_hash != "supersecret123"
    assert user.is_active is True
    assert user.is_shadow is False
    assert user.system_role == "regular"


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(db_session):
    service = AuthService(db_session)
    req1 = RegisterRequest(email="bob@example.com", password="pass12345", full_name="Bob")
    await service.register(req1)
    await db_session.flush()

    req2 = RegisterRequest(email="bob@example.com", password="other12345", full_name="Bob2")
    with pytest.raises(EmailAlreadyExistsError):
        await service.register(req2)


@pytest.mark.asyncio
async def test_login_with_correct_credentials(db_session):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(email="charlie@example.com", password="pass12345", full_name="Charlie")
    )
    await db_session.flush()

    user = await service.authenticate(email="charlie@example.com", password="pass12345")
    assert user is not None
    assert user.email == "charlie@example.com"
    assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_login_with_wrong_password_raises(db_session):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(email="dave@example.com", password="pass12345", full_name="Dave")
    )
    await db_session.flush()

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(email="dave@example.com", password="wrongpass")


@pytest.mark.asyncio
async def test_login_with_nonexistent_email_raises(db_session):
    service = AuthService(db_session)
    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(email="nobody@example.com", password="anything")
