"""
Centralized Application Configuration.
Uses Pydantic Settings (v2) to validate environment variables at startup.
"""

from functools import lru_cache
from typing import Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Metadata
    APP_NAME: str = Field(
        default="Aurelis Fleet Operations", description="Application display name"
    )
    APP_ENV: str = Field(
        default="development", description="Environment: development, staging, production"
    )
    DEBUG: bool = Field(default=False, description="Debug mode toggle")
    PORT: int = Field(default=8000, description="Service listening port")
    HOST: str = Field(default="0.0.0.0", description="Service listening interface")

    # Database Configuration (PostgreSQL 16)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://aurelis_admin:aurelis_dev_secret@localhost:5432/aurelis_fleet",
        description="Async database connection string for SQLAlchemy engine",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://aurelis_admin:aurelis_dev_secret@localhost:5432/aurelis_fleet",
        description="Synchronous database connection string for Alembic migrations",
    )
    DB_POOL_SIZE: int = Field(default=10, description="SQLAlchemy connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="SQLAlchemy connection pool max overflow")

    # Redis Configuration (Redis 7)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching, locks, and token revocation",
    )

    # Authentication & Security
    JWT_SECRET: str = Field(
        default="aurelis_super_secret_dev_key_change_in_production_32char_minimum",
        min_length=32,
        description="Cryptographic secret for signing JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, description="Access token expiration in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Cross-Origin Resource Sharing (CORS)
    CORS_ORIGINS: Union[str, list[str]] = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Allowed CORS origins as comma-delimited string or list",
    )

    # Observability & Logging
    LOG_LEVEL: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    LOG_JSON_FORMAT: bool = Field(default=True, description="Enable structured JSON log format")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, list[str]]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached accessor for singleton application settings."""
    return Settings()
