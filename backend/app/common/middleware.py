"""
Centralized Request Correlation, Logging Middleware & Exception Handlers.
Intercepts all HTTP traffic to ensure correlation IDs, structured execution logs,
and uniform error envelopes.
"""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.responses import error_response
from app.core.exceptions import AppException
from app.core.logging import logger


class CorrelationAndLoggingMiddleware(BaseHTTPMiddleware):
    """
    Ensures every request has a correlation ID, records execution duration,
    and produces structured logs.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Correlation Request ID Handling
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 2. Process Request
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Let the exception handlers deal with response formation
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise exc

        # 3. Compute Metrics & Log
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Log request completion
        log_level = logger.info if response.status_code < 400 else logger.warning
        log_level(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "route": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers mapping domain exceptions to standard response envelopes."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        formatted_errors = {}
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err.get("loc", []))
            formatted_errors[field] = err.get("msg", "Invalid value")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                code="VALIDATION_FAILED",
                message="Request payload failed structural validation.",
                details={"errors": formatted_errors},
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred. Please contact system support.",
                details={"error_reference": request_id} if request_id else None,
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id} if request_id else None,
        )
