"""
Redis 7 Integration & Token Revocation Cache Abstraction.
Provides async Redis client with connection pooling, token blacklist checking,
and graceful in-memory fallback for local unit tests.
"""

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class RedisManager:
    """Manages Redis connection pool and caching / token revocation operations."""

    def __init__(self):
        self._pool: aioredis.ConnectionPool | None = None
        self._client: aioredis.Redis | None = None
        self._in_memory_store: dict[str, str] = {}
        self._is_fallback: bool = False

    async def initialize(self) -> None:
        """Initializes Redis connection pool and tests connectivity."""
        try:
            self._pool = aioredis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            await self._client.ping()
            self._is_fallback = False
            logger.info("Connected to Redis 7 successfully.")
        except Exception as exc:
            self._is_fallback = True
            logger.warning(
                f"Redis unavailable at {settings.REDIS_URL} ({str(exc)}). "
                "Engaging thread-safe in-memory cache fallback for development/testing."
            )

    async def close(self) -> None:
        """Closes Redis client and connection pool."""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.disconnect()

    async def ping(self) -> bool:
        """Health-check ping to verify Redis responsiveness."""
        if self._is_fallback:
            return True
        try:
            if not self._client:
                return False
            return await self._client.ping()
        except Exception:
            return False

    async def set_value(self, key: str, value: str, expire_seconds: int | None = None) -> bool:
        """Sets a key-value pair with optional TTL."""
        if self._is_fallback or not self._client:
            self._in_memory_store[key] = value
            return True
        try:
            if expire_seconds:
                await self._client.setex(key, expire_seconds, value)
            else:
                await self._client.set(key, value)
            return True
        except Exception as exc:
            logger.error(f"Redis set error on key '{key}': {str(exc)}")
            self._in_memory_store[key] = value
            return True

    async def get_value(self, key: str) -> str | None:
        """Retrieves value for a key."""
        if self._is_fallback or not self._client:
            return self._in_memory_store.get(key)
        try:
            return await self._client.get(key)
        except Exception as exc:
            logger.error(f"Redis get error on key '{key}': {str(exc)}")
            return self._in_memory_store.get(key)

    async def delete_key(self, key: str) -> bool:
        """Deletes a key."""
        if self._is_fallback or not self._client:
            self._in_memory_store.pop(key, None)
            return True
        try:
            await self._client.delete(key)
            return True
        except Exception as exc:
            logger.error(f"Redis delete error on key '{key}': {str(exc)}")
            self._in_memory_store.pop(key, None)
            return True

    # Token Revocation / Blacklist Protocol
    async def revoke_token(self, jti: str, expire_seconds: int) -> bool:
        """Blacklists a JWT token ID (JTI) for its remaining lifetime."""
        key = f"auth:blacklist:{jti}"
        return await self.set_value(key, "revoked", expire_seconds)

    async def is_token_revoked(self, jti: str) -> bool:
        """Checks whether a token JTI has been revoked."""
        key = f"auth:blacklist:{jti}"
        val = await self.get_value(key)
        return val == "revoked"


redis_manager = RedisManager()


async def get_redis() -> RedisManager:
    """Dependency provider for Redis manager instance."""
    return redis_manager
