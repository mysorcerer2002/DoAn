import pytest


@pytest.mark.asyncio
async def test_register_endpoint_creates_user_and_returns_tokens(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "supersecret123",
            "full_name": "Alice",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {
        "email": "bob@example.com",
        "password": "pass12345",
        "full_name": "Bob",
    }
    r1 = await client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = await client.post("/auth/register", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/auth/register",
        json={"email": "not-email", "password": "pass12345", "full_name": "X"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_with_correct_credentials_returns_tokens(client):
    await client.post(
        "/auth/register",
        json={"email": "charlie@example.com", "password": "pass12345", "full_name": "Charlie"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": "charlie@example.com", "password": "pass12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client):
    await client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "pass12345", "full_name": "Dave"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(client):
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client):
    register_response = await client.post(
        "/auth/register",
        json={"email": "eve@example.com", "password": "pass12345", "full_name": "Eve"},
    )
    refresh_token = register_response.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(client):
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_returns_401(client):
    register_response = await client.post(
        "/auth/register",
        json={"email": "frank@example.com", "password": "pass12345", "full_name": "Frank"},
    )
    access_token = register_response.json()["access_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token_returns_user(client):
    register = await client.post(
        "/auth/register",
        json={"email": "grace@example.com", "password": "pass12345", "full_name": "Grace"},
    )
    access_token = register.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "grace@example.com"
    assert data["full_name"] == "Grace"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_rate_limit_429_after_excessive_attempts(client):
    """Endpoint /auth/login phải trả 429 khi vượt rate limit (5/phút/IP)."""
    payload = {"email": "ratelimit@example.com", "password": "wrong"}
    got_429 = False
    for _ in range(10):
        response = await client.post("/auth/login", json=payload)
        if response.status_code == 429:
            got_429 = True
            break
    assert got_429, "Expected 429 rate limit response"
