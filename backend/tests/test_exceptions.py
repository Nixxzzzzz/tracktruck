"""
Test Centralized Error Envelopes & Correlation Headers.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validation_error_envelope(client: AsyncClient):
    """Payload failing structural validation returns standard 422 error envelope."""
    invalid_payload = {
        "username": "ab",  # min_length is 3
        # missing password
    }
    response = await client.post("/api/v1/auth/login", json=invalid_payload)
    assert response.status_code == 422

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_FAILED"
    assert "errors" in body["error"]["details"]


@pytest.mark.asyncio
async def test_preserves_custom_request_id(client: AsyncClient):
    """Client-provided X-Request-ID is preserved in headers and response body."""
    custom_id = "test-custom-request-id-9876"
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": custom_id},
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id
    assert response.json()["request_id"] == custom_id
