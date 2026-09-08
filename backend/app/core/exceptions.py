"""
Centralized Exception Hierarchy.
Provides domain-specific exceptions mapped to HTTP status codes and standard error codes.
"""

from typing import Any

from fastapi import status


class AppException(Exception):
    """Base application exception for all domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class AuthenticationException(AppException):
    """Raised when authentication credentials fail or token is invalid/expired."""

    def __init__(
        self,
        message: str = "Authentication failed. Invalid or expired credentials.",
        code: str = "AUTHENTICATION_FAILED",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationException(AppException):
    """Raised when an authenticated user lacks permissions for an operation."""

    def __init__(
        self,
        message: str = "Access denied. Insufficient permissions for this resource.",
        code: str = "ACCESS_DENIED",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource: str = "Resource",
        identifier: Any = "",
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        msg = message or f"{resource} '{identifier}' was not found."
        super().__init__(
            message=msg,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"resource": resource, "identifier": str(identifier)},
        )


class ConflictException(AppException):
    """Raised when a resource already exists or a state conflict occurs."""

    def __init__(
        self,
        message: str = "Conflict detected. Resource state contradicts requested operation.",
        code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationException(AppException):
    """Raised when domain business rules or input parameters fail validation."""

    def __init__(
        self,
        message: str = "Validation failed for one or more fields.",
        code: str = "VALIDATION_FAILED",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class DatabaseException(AppException):
    """Raised when a relational database query or transaction error occurs."""

    def __init__(
        self,
        message: str = "A database error occurred while processing the request.",
        code: str = "DATABASE_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )
