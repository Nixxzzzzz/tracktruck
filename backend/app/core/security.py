"""
Authentication Primitives, Password Hashing & JWT Security Engine.
Implements Argon2id password hashing and cryptographic JWT creation, verification,
and revocation handling.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AuthenticationException
from app.core.logging import logger

settings = get_settings()

# CryptContext configured with Argon2id primary and bcrypt compatibility
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hashes plaintext password using Argon2id algorithm."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id/bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    payload: dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    """Creates a signed JWT with unique JTI, expiration, and token type."""
    now = datetime.now(UTC)
    expire = now + expires_delta
    token_jti = str(uuid.uuid4())

    to_encode = payload.copy()
    to_encode.update(
        {
            "jti": token_jti,
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": "aurelis-fleet-core",
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_access_token(
    subject: str,
    role: str,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Generates a short-lived access token (default 15 minutes)."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
    }
    if additional_claims:
        payload.update(additional_claims)
    return create_token(payload, token_type="access", expires_delta=delta)


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Generates a long-lived refresh token (default 7 days)."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "role": role,
    }
    return create_token(payload, token_type="refresh", expires_delta=delta)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodes and cryptographically validates a JWT token.
    Raises AuthenticationException on expiration, signature mismatch, or tampering.
    """
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "jti", "type"]},
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise AuthenticationException(
            message="Token has expired. Please authenticate again.",
            code="TOKEN_EXPIRED",
        )
    except jwt.InvalidTokenError as exc:
        logger.warning(f"Invalid token rejected: {str(exc)}")
        raise AuthenticationException(
            message="Invalid authentication token.",
            code="INVALID_TOKEN",
        )
