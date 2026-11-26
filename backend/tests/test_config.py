import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_default_settings():
    """Verify default values for application settings in development."""
    cfg = Settings()
    assert cfg.PROJECT_NAME == "CAI Campus Intelligence API"
    assert cfg.ENVIRONMENT in ["development", "production", "staging", "test"]
    assert cfg.MAX_UPLOAD_SIZE_BYTES == 10485760
    assert cfg.MAX_PAGE_COUNT == 10
    assert isinstance(cfg.CORS_ORIGINS, list)
    assert "http://localhost:5173" in cfg.CORS_ORIGINS


def test_settings_custom_env(monkeypatch):
    """Verify environment variables override defaults in production."""
    monkeypatch.setenv("PROJECT_NAME", "Custom Campus Intelligence")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SUPABASE_URL", "https://custom.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret-key")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_BYTES", "5242880")
    monkeypatch.setenv("MAX_PAGE_COUNT", "25")

    cfg = Settings()
    assert cfg.PROJECT_NAME == "Custom Campus Intelligence"
    assert cfg.ENVIRONMENT == "production"
    assert cfg.SUPABASE_URL == "https://custom.supabase.co"
    assert cfg.SUPABASE_SERVICE_ROLE_KEY == "service-role-secret"
    assert cfg.SUPABASE_KEY == "service-role-secret"
    assert cfg.GEMINI_API_KEY == "gemini-secret-key"
    assert cfg.MAX_UPLOAD_SIZE_BYTES == 5242880
    assert cfg.MAX_PAGE_COUNT == 25


def test_supabase_key_synchronization(monkeypatch):
    """Verify SUPABASE_KEY and SUPABASE_SERVICE_ROLE_KEY sync seamlessly."""
    monkeypatch.setenv("ENVIRONMENT", "development")

    # Provided SUPABASE_KEY populates SUPABASE_SERVICE_ROLE_KEY
    monkeypatch.setenv("SUPABASE_KEY", "test-key-1")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    cfg1 = Settings()
    assert cfg1.SUPABASE_KEY == "test-key-1"
    assert cfg1.SUPABASE_SERVICE_ROLE_KEY == "test-key-1"

    # Provided SUPABASE_SERVICE_ROLE_KEY populates SUPABASE_KEY
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key-2")
    cfg2 = Settings()
    assert cfg2.SUPABASE_KEY == "test-key-2"
    assert cfg2.SUPABASE_SERVICE_ROLE_KEY == "test-key-2"


def test_production_missing_secrets_raises(monkeypatch):
    """Verify configuration loader rejects missing required secrets in production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    errors_str = str(exc_info.value)
    assert "Missing required configuration settings for environment 'production'" in errors_str
    assert "SUPABASE_URL" in errors_str
    assert "GEMINI_API_KEY" in errors_str
