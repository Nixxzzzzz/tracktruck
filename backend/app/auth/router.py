"""
Authentication REST API Endpoints.
Provides routes for login, token refresh, logout session revocation, and current user profile.
"""

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.auth.service import AuthService
from app.common.responses import ApiResponse, success_response
from app.core.database import get_db
from app.core.dependencies import (
    ROLE_PERMISSIONS,
    get_current_user,
    oauth2_scheme,
    require_roles,
)
from app.core.redis import RedisManager, get_redis
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Authenticate user and issue token pair",
)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    tokens = await AuthService.login(
        db=db,
        username_or_email=payload.username,
        password=payload.password,
    )
    request_id = getattr(request.state, "request_id", None)
    return success_response(data=tokens.model_dump(), request_id=request_id)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Refresh access token with refresh token rotation",
)
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis),
) -> dict:
    tokens = await AuthService.refresh_access_token(
        db=db,
        redis=redis,
        refresh_token=payload.refresh_token,
    )
    request_id = getattr(request.state, "request_id", None)
    return success_response(data=tokens.model_dump(), request_id=request_id)


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    summary="Invalidate active session and blacklist tokens",
)
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    refresh_token_header: str | None = Header(None, alias="X-Refresh-Token"),
    redis: RedisManager = Depends(get_redis),
) -> dict:
    await AuthService.logout(
        redis=redis,
        access_token=token,
        refresh_token=refresh_token_header,
    )
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"message": "Successfully logged out and session revoked."},
        request_id=request_id,
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Retrieve profile and permissions for currently authenticated user",
)
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict:
    user_dto = UserResponse.model_validate(current_user)
    permissions = list(ROLE_PERMISSIONS.get(current_user.role_id, set()))

    profile = UserProfileResponse(
        user=user_dto,
        permissions=permissions,
    )
    request_id = getattr(request.state, "request_id", None)
    return success_response(data=profile.model_dump(), request_id=request_id)


# RBAC Demonstration / Testing Endpoints
@router.get(
    "/test-admin-only",
    response_model=ApiResponse[dict],
    summary="Test endpoint restricted to SUPER_ADMIN and ADMIN roles",
)
async def test_admin_only(
    request: Request,
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
) -> dict:
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"message": f"Welcome Admin {current_user.username}. Authorized access confirmed."},
        request_id=request_id,
    )


@router.get(
    "/test-driver-only",
    response_model=ApiResponse[dict],
    summary="Test endpoint restricted to DRIVER role",
)
async def test_driver_only(
    request: Request,
    current_user: User = Depends(require_roles("DRIVER")),
) -> dict:
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"message": f"Welcome Driver {current_user.username}. Mobile terminal authorized."},
        request_id=request_id,
    )
