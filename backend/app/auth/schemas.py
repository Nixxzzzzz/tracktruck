"""
Authentication Schemas (Requests and Responses).
"""

from pydantic import BaseModel, Field

from app.users.schemas import UserResponse


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or registered email address")
    password: str = Field(..., description="Account password")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived cryptographic refresh token")
    token_type: str = Field(default="bearer", description="Token schema type")
    expires_in: int = Field(..., description="Access token expiration window in seconds")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Active refresh token")


class UserProfileResponse(BaseModel):
    user: UserResponse
    permissions: list[str] = Field(
        default_factory=list, description="Computed permissions for role"
    )
