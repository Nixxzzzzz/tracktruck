"""
Authentication and RBAC Dependencies.
Provides reusable FastAPI dependency injectors for JWT validation, user resolution,
and role/permission checking.
"""

from typing import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.logging import logger
from app.core.redis import RedisManager, get_redis
from app.core.security import decode_token
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

# Role Permission Mapping Baseline for Foundation
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "SUPER_ADMIN": {"*"},
    "ADMIN": {
        "master_data:read",
        "master_data:write",
        "trips:read",
        "trips:write",
        "trips:override",
        "reports:read",
        "audit:read",
    },
    "MANAGER": {
        "master_data:read",
        "trips:read",
        "trips:write",
        "trips:override",
        "reports:read",
    },
    "SUPERVISOR": {
        "master_data:read",
        "trips:read",
        "incidents:write",
        "operations:read",
    },
    "DRIVER": {
        "trips:assigned:read",
        "trips:events:write",
        "incidents:write",
    },
}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis),
) -> User:
    """
    Validates JWT access token, checks revocation in Redis, and retrieves
    the active user record from database.
    """
    if not token:
        raise AuthenticationException(
            message="Missing authentication credentials.",
            code="CREDENTIALS_MISSING",
        )

    # 1. Decode & Cryptographically Verify Token
    payload = decode_token(token)

    # Ensure token type is 'access'
    if payload.get("type") != "access":
        raise AuthenticationException(
            message="Invalid token type. Access token required.",
            code="INVALID_TOKEN_TYPE",
        )

    # 2. Verify Token Revocation Blacklist
    token_jti = payload.get("jti")
    if token_jti and await redis.is_token_revoked(token_jti):
        raise AuthenticationException(
            message="Token has been revoked.",
            code="TOKEN_REVOKED",
        )

    # 3. Retrieve User from Database
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException(message="Token subject missing.", code="INVALID_TOKEN")

    import uuid

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationException(
            message="Invalid user identifier format in token.", code="INVALID_TOKEN"
        )

    stmt = select(User).where(
        User.user_id == user_uuid,
        User.is_deleted.is_(False),
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationException(
            message="User account associated with this token was not found or has been removed.",
            code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise AuthorizationException(
            message="User account is inactive. Please contact system administrator.",
            code="ACCOUNT_INACTIVE",
        )

    return user


def require_roles(*allowed_roles: str) -> Callable:
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that the current authenticated user possesses one of the allowed roles.
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if "SUPER_ADMIN" == current_user.role_id:
            # Super Admin has universal access
            return current_user

        if current_user.role_id not in allowed_roles:
            logger.warning(
                f"Access denied for user '{current_user.username}' with role '{current_user.role_id}'. "
                f"Required roles: {allowed_roles}"
            )
            raise AuthorizationException(
                message=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
                code="INSUFFICIENT_ROLE",
                details={"required_roles": list(allowed_roles), "user_role": current_user.role_id},
            )
        return current_user

    return role_checker


def require_permission(permission: str) -> Callable:
    """
    Permission-Based Access Control dependency factory.
    Verifies that the user's role grants the required fine-grained permission.
    """

    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        role = current_user.role_id
        granted_permissions = ROLE_PERMISSIONS.get(role, set())

        if "*" in granted_permissions or permission in granted_permissions:
            return current_user

        raise AuthorizationException(
            message=f"Access denied. Required permission: '{permission}'",
            code="INSUFFICIENT_PERMISSION",
            details={"required_permission": permission, "user_role": role},
        )

    return permission_checker
