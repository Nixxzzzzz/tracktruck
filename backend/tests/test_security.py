"""
Test Security Primitives: Password Hashing & JWT Token Engine.
"""

from datetime import timedelta

import pytest

from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    """Verify password hashing produces verifiable hash and rejects wrong password."""
    password = "SuperSecureFleetPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_token_creation_and_decoding():
    """Verify access token encodes claims and decodes accurately."""
    token = create_access_token(
        subject="user-123",
        role="MANAGER",
        additional_claims={"username": "test.manager"},
    )
    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == "MANAGER"
    assert payload["type"] == "access"
    assert payload["username"] == "test.manager"
    assert "jti" in payload
    assert "exp" in payload


def test_jwt_refresh_token_creation():
    """Verify refresh token specifies type 'refresh'."""
    token = create_refresh_token(subject="user-456", role="DRIVER")
    payload = decode_token(token)

    assert payload["sub"] == "user-456"
    assert payload["role"] == "DRIVER"
    assert payload["type"] == "refresh"


def test_jwt_expired_token_rejection():
    """Verify expired token raises AuthenticationException."""
    token = create_access_token(
        subject="user-expired",
        role="DRIVER",
        expires_delta=timedelta(seconds=-10),  # expired in past
    )
    with pytest.raises(AuthenticationException) as exc_info:
        decode_token(token)

    assert exc_info.value.code == "TOKEN_EXPIRED"


def test_jwt_tampered_token_rejection():
    """Verify tampered token is rejected."""
    token = create_access_token(subject="user-tampered", role="ADMIN")
    tampered_token = token[:-5] + "XXXXX"

    with pytest.raises(AuthenticationException) as exc_info:
        decode_token(tampered_token)

    assert exc_info.value.code == "INVALID_TOKEN"
