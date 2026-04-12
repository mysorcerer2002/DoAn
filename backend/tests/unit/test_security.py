from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_different_hash_each_time():
    h1 = hash_password("supersecret123")
    h2 = hash_password("supersecret123")
    assert h1 != h2  # bcrypt has random salt
    assert h1.startswith("$2b$")


def test_verify_password_correct():
    pwd = "supersecret123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("supersecret123")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_returns_string():
    token = create_access_token(user_id=42)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # JWT has 3 parts


def test_decode_valid_access_token():
    token = create_access_token(user_id=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("invalid.token.here")


def test_decode_expired_token_raises():
    token = create_access_token(user_id=42, expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_token(token)
