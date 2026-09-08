"""
Test Configuration Loading & Validation.
"""

from app.core.config import Settings


def test_settings_loading():
    """Verify that settings can be instantiated with valid defaults."""
    settings = Settings(
        APP_NAME="Aurelis Test Fleet",
        APP_ENV="test",
        JWT_SECRET="this_is_a_test_secret_that_has_at_least_32_characters",
        CORS_ORIGINS="http://localhost:3000,http://app.aurelis.io",
    )

    assert settings.APP_NAME == "Aurelis Test Fleet"
    assert settings.APP_ENV == "test"
    assert settings.is_production is False
    assert len(settings.CORS_ORIGINS) == 2
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://app.aurelis.io" in settings.CORS_ORIGINS


def test_production_flag_detection():
    """Verify is_production property behavior."""
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET="this_is_a_production_secret_with_32_chars!",
    )
    assert prod_settings.is_production is True
