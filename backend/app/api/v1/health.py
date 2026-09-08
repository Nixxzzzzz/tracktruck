"""
Health Check & Dependency Diagnostics Endpoint (`/api/v1/health`).
Verifies application liveness and tests connectivity to PostgreSQL and Redis.
"""

import time
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import ApiResponse, success_response
from app.core.config import get_settings
from app.core.database import get_db
from app.core.redis import RedisManager, get_redis

router = APIRouter(tags=["Health & Diagnostics"])
settings = get_settings()


@router.get(
    "/health",
    response_model=ApiResponse[dict[str, Any]],
    summary="Comprehensive service liveness and dependency readiness check",
)
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis),
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    dependencies: dict[str, Any] = {}
    is_healthy = True

    # 1. PostgreSQL Database Connectivity Check
    db_start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - db_start) * 1000, 2)
        dependencies["database"] = {
            "status": "healthy",
            "type": "PostgreSQL 16",
            "latency_ms": db_latency_ms,
        }
    except Exception:
        is_healthy = False
        dependencies["database"] = {
            "status": "unhealthy",
            "error": "Database connection query failed",
        }

    # 2. Redis Cache & Revocation Store Check
    redis_start = time.perf_counter()
    try:
        redis_ok = await redis.ping()
        redis_latency_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        if redis_ok:
            dependencies["redis"] = {
                "status": "healthy",
                "type": "Redis 7",
                "latency_ms": redis_latency_ms,
            }
        else:
            is_healthy = False
            dependencies["redis"] = {
                "status": "unhealthy",
                "error": "Redis ping returned false",
            }
    except Exception:
        is_healthy = False
        dependencies["redis"] = {
            "status": "unhealthy",
            "error": "Redis connection ping failed",
        }

    overall_status = "healthy" if is_healthy else "degraded"
    payload = {
        "status": overall_status,
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "dependencies": dependencies,
    }

    http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    response_content = success_response(data=payload, request_id=request_id)

    return JSONResponse(status_code=http_status, content=response_content)
