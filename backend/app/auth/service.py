"""
Authentication Domain Service.
Encapsulates login validation, token issuance, refresh token rotation, and revocation.
"""

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import TokenResponse
from app.core.config import get_settings
from app.core.exceptions import AuthenticationException
from app.core.logging import logger
from app.core.redis import RedisManager
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.users.models import User

settings = get_settings()


class AuthService:
    """Service handling credential verification, token lifecycle, and session revocation."""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username_or_email: str,
        password: str,
    ) -> User:
        """Finds user by username or email and validates password hash."""
        stmt = select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email),
            User.is_deleted.is_(False),
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            logger.warning(f"Failed authentication attempt for identifier: '{username_or_email}'")
            raise AuthenticationException(
                message="Invalid username/email or password.",
                code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise AuthenticationException(
                message="User account is inactive. Please contact administrator.",
                code="ACCOUNT_INACTIVE",
            )

        return user

    @classmethod
    async def login(
        cls,
        db: AsyncSession,
        username_or_email: str,
        password: str,
    ) -> TokenResponse:
        """Authenticates user and issues access and refresh token pair."""
        user = await cls.authenticate_user(db, username_or_email, password)

        access_token = create_access_token(
            subject=str(user.user_id),
            role=user.role_id,
            additional_claims={"username": user.username, "full_name": user.full_name},
        )
        refresh_token = create_refresh_token(
            subject=str(user.user_id),
            role=user.role_id,
        )

        logger.info(
            f"User '{user.username}' successfully authenticated with role '{user.role_id}'."
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @classmethod
    async def refresh_access_token(
        cls,
        db: AsyncSession,
        redis: RedisManager,
        refresh_token: str,
    ) -> TokenResponse:
        """Validates refresh token, checks revocation, revokes old token, and issues new token pair."""
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise AuthenticationException(
                message="Provided token is not a valid refresh token.",
                code="INVALID_TOKEN_TYPE",
            )

        old_jti = payload.get("jti")
        if old_jti and await redis.is_token_revoked(old_jti):
            logger.warning(f"Attempted reuse of revoked refresh token JTI: {old_jti}")
            raise AuthenticationException(
                message="Refresh token has been revoked.",
                code="TOKEN_REVOKED",
            )

        user_id_str = payload.get("sub")
        import uuid

        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise AuthenticationException(message="Invalid token subject.", code="INVALID_TOKEN")

        stmt = select(User).where(User.user_id == user_uuid, User.is_deleted.is_(False))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationException(
                message="User account no longer active or exists.",
                code="USER_INACTIVE",
            )

        # Revoke old refresh token to enforce refresh token rotation
        exp = payload.get("exp", 0)
        remaining_ttl = max(0, exp - int(datetime.now(UTC).timestamp()))
        if old_jti and remaining_ttl > 0:
            await redis.revoke_token(old_jti, remaining_ttl)

        # Issue fresh token pair
        new_access_token = create_access_token(
            subject=str(user.user_id),
            role=user.role_id,
            additional_claims={"username": user.username, "full_name": user.full_name},
        )
        new_refresh_token = create_refresh_token(
            subject=str(user.user_id),
            role=user.role_id,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @classmethod
    async def logout(
        cls,
        redis: RedisManager,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> bool:
        """Revokes active access and/or refresh tokens by adding their JTIs to the Redis blacklist."""
        now_ts = int(datetime.now(UTC).timestamp())

        for token in (access_token, refresh_token):
            if not token:
                continue
            try:
                payload = decode_token(token)
                jti = payload.get("jti")
                exp = payload.get("exp", 0)
                remaining_ttl = max(0, exp - now_ts)
                if jti and remaining_ttl > 0:
                    await redis.revoke_token(jti, remaining_ttl)
                    logger.info(f"Revoked token JTI '{jti}' with TTL {remaining_ttl}s.")
            except Exception as exc:
                logger.debug(f"Could not parse token during logout revocation: {str(exc)}")

        return True
