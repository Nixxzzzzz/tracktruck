"""
PostgreSQL Database Foundation.
Configures SQLAlchemy 2.0 async engine, connection pool, session factory,
declarative base, and atomic transaction boundary management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.0 relational models."""

    pass


class TimestampMixin:
    """Reusable mixin providing created_at and updated_at audit timestamps."""

    created_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def create_engine_instance() -> AsyncEngine:
    """Creates SQLAlchemy async engine with connection pooling and pre-ping validation."""
    connect_args = {}

    # SQLite async support for testing
    if "sqlite" in settings.DATABASE_URL:
        connect_args["check_same_thread"] = False
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            connect_args=connect_args,
        )

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )


engine: AsyncEngine = create_engine_instance()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injecting an async database session into route handlers.
    Automatically closes session upon request completion.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            logger.error(f"Database session rolled back due to error: {str(exc)}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def atomic_transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Atomic transaction context manager for multi-step operational state transitions.
    Ensures that compound mutations (e.g. status update + event row + audit log)
    either commit completely or roll back atomically.
    """
    if session.in_transaction():
        yield session
    else:
        async with session.begin():
            try:
                yield session
            except Exception as exc:
                await session.rollback()
                logger.error(f"Atomic transaction aborted and rolled back: {str(exc)}")
                raise
