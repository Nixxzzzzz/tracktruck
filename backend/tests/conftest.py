"""
Pytest Fixtures and Test Environment Setup.
Configures in-memory SQLite database, mock/in-memory Redis client,
and asynchronous HTTP client for testing.
"""

import os
import uuid
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment flags before importing application modules
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"
os.environ["JWT_SECRET"] = "test_secret_key_minimum_32_characters_for_unit_tests!"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.core.database import Base, get_db
from app.core.redis import RedisManager, get_redis
from app.core.security import hash_password
from app.main import create_application
from app.users.models import Role, User

# In-memory test engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean database session per test function with fresh tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Seed standard roles for testing
        roles = [
            Role(role_id="SUPER_ADMIN", description="System Owner"),
            Role(role_id="ADMIN", description="Operations Director"),
            Role(role_id="MANAGER", description="Fleet Dispatcher"),
            Role(role_id="SUPERVISOR", description="Depot Supervisor"),
            Role(role_id="DRIVER", description="Commercial Driver"),
        ]
        session.add_all(roles)
        await session.commit()

        # Seed test accounts
        test_admin = User(
            user_id=uuid.uuid4(),
            role_id="ADMIN",
            username="test.admin",
            email="admin@test.local",
            password_hash=hash_password("SecretAdminPass123!"),
            full_name="Test Administrator",
            is_active=True,
        )
        test_driver = User(
            user_id=uuid.uuid4(),
            role_id="DRIVER",
            username="test.driver",
            email="driver@test.local",
            password_hash=hash_password("SecretDriverPass123!"),
            full_name="Test Driver",
            is_active=True,
        )
        session.add_all([test_admin, test_driver])
        await session.commit()

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_redis() -> RedisManager:
    """Provides an isolated RedisManager with in-memory fallback store."""
    manager = RedisManager()
    manager._is_fallback = True
    manager._in_memory_store = {}
    return manager


@pytest_asyncio.fixture(scope="function")
async def client(
    db_session: AsyncSession, test_redis: RedisManager
) -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous HTTP test client with database and Redis dependency overrides."""
    app = create_application()

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return test_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
