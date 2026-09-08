"""
Test Authentication Workflow: Login, Profile, Refresh & Revocation.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Verify successful login returns standard envelope with access and refresh tokens."""
    payload = {
        "username": "test.admin",
        "password": "SecretAdminPass123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Verify login with wrong password returns 401 error envelope."""
    payload = {
        "username": "test.admin",
        "password": "WrongPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient):
    """Verify /auth/me returns authenticated user's profile and permissions."""
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "test.admin", "password": "SecretAdminPass123!"},
    )
    token = login_resp.json()["data"]["access_token"]

    # 2. Get Profile
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_body = me_resp.json()
    assert me_body["success"] is True
    assert me_body["data"]["user"]["username"] == "test.admin"
    assert me_body["data"]["user"]["role_id"] == "ADMIN"
    assert "master_data:read" in me_body["data"]["permissions"]


@pytest.mark.asyncio
async def test_refresh_token_lifecycle(client: AsyncClient):
    """Verify token refresh issues new token pair and revokes old refresh token."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "test.driver", "password": "SecretDriverPass123!"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # Refresh token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()["data"]
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Attempt reuse of old refresh token must be rejected
    reuse_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reuse_resp.status_code == 401
    assert reuse_resp.json()["error"]["code"] == "TOKEN_REVOKED"


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    """Verify logging out blacklists the active token in Redis."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "test.driver", "password": "SecretDriverPass123!"},
    )
    token = login_resp.json()["data"]["access_token"]

    # Profile works before logout
    pre_logout = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert pre_logout.status_code == 200

    # Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200

    # Profile fails after logout
    post_logout = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert post_logout.status_code == 401
    assert post_logout.json()["error"]["code"] == "TOKEN_REVOKED"
