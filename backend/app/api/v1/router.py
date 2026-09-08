"""
API v1 Root Router.
Aggregates all version 1 domain controllers.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.auth.router import router as auth_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount Version 1 Endpoints
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
