"""
AURELIS FLEET — Main Application Entrypoint.
Initializes FastAPI, mounts middleware, configures lifespan events,
registers global exception handlers, and includes versioned API routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_v1_router
from app.common.middleware import (
    CorrelationAndLoggingMiddleware,
    register_exception_handlers,
)
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import logger, setup_logging
from app.core.redis import redis_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management for resource allocation and graceful teardown."""
    # 1. Startup
    setup_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON_FORMAT)
    logger.info(
        f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' mode...",
        extra={"environment": settings.APP_ENV, "debug": settings.DEBUG},
    )
    await redis_manager.initialize()

    yield

    # 2. Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")
    await redis_manager.close()
    await engine.dispose()
    logger.info("Database and Redis connections closed cleanly.")


def create_application() -> FastAPI:
    """Factory creating and configuring FastAPI application instance."""
    app = FastAPI(
        title="AURELIS FLEET Operations API",
        description="Mission-critical backend for luxury logistics and operations management.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Correlation & Logging Middleware
    app.add_middleware(CorrelationAndLoggingMiddleware)

    # 3. Global Exception Handlers
    register_exception_handlers(app)

    # 4. Mount API Routers
    app.include_router(api_v1_router)

    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect root to interactive API documentation."""
        return RedirectResponse(url="/docs")

    return app


app = create_application()
