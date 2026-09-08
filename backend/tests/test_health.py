"""
Test Health & Diagnostics Endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verify health endpoint reports healthy status for app, db, and redis."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert body["data"]["status"] == "healthy"
    assert body["data"]["dependencies"]["database"]["status"] == "healthy"
    assert body["data"]["dependencies"]["redis"]["status"] == "healthy"

    # Verify correlation request ID header is returned
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"] == body["request_id"]
