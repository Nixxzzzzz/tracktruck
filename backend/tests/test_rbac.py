"""
Test Role-Based Access Control (RBAC) Enforcement.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rbac_admin_allowed_on_admin_route(client: AsyncClient):
    """Admin role should access admin-only endpoint successfully."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "test.admin", "password": "SecretAdminPass123!"},
    )
    admin_token = login_resp.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/test-admin-only",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_rbac_driver_forbidden_on_admin_route(client: AsyncClient):
    """Driver role should be rejected on admin endpoint with 403 Forbidden."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "test.driver", "password": "SecretDriverPass123!"},
    )
    driver_token = login_resp.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/test-admin-only",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INSUFFICIENT_ROLE"


@pytest.mark.asyncio
async def test_rbac_driver_allowed_on_driver_route(client: AsyncClient):
    """Driver role should access driver endpoint successfully."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "test.driver", "password": "SecretDriverPass123!"},
    )
    driver_token = login_resp.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/test-driver-only",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_rbac_unauthenticated_request_rejected(client: AsyncClient):
    """Request without authorization header should return 401."""
    response = await client.get("/api/v1/auth/test-admin-only")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CREDENTIALS_MISSING"
