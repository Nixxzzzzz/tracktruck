"""
Standard API Response Envelopes.
Ensures uniform contract across all successful responses and error states.
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable unique error code")
    message: str = Field(..., description="Human-readable error explanation")
    details: dict[str, Any] | None = Field(
        default=None, description="Granular error context or field errors"
    )


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Indicates request outcome")
    data: T | None = Field(default=None, description="Payload data for successful requests")
    error: ErrorDetail | None = Field(default=None, description="Error detail if request failed")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 server timestamp",
    )
    request_id: str | None = Field(default=None, description="Unique correlation request ID")


def success_response(data: Any = None, request_id: str | None = None) -> dict[str, Any]:
    """Helper to construct standard successful JSON response dict."""
    return {
        "success": True,
        "data": data,
        "error": None,
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": request_id,
    }


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Helper to construct standard error JSON response dict."""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": request_id,
    }
