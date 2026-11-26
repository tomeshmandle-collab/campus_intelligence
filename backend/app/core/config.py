import json
from typing import Any, List, Literal
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration settings managed by pydantic-settings."""

    # Project metadata
    PROJECT_NAME: str = "CAI Campus Intelligence API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: Literal["development", "production", "staging", "test"] = "development"
    DEBUG: bool = False

    # CORS configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Supabase service credentials (backend operations only)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Gemini AI provider
    GEMINI_API_KEY: str = ""

    # Processing and ingestion bounds
    MAX_UPLOAD_SIZE_BYTES: int = 10485760  # 10 MB default
    MAX_PAGE_COUNT: int = 10  # 10 pages default

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            val = v.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["http://localhost:5173"]

    @model_validator(mode="after")
    def validate_and_sync_credentials(self) -> "Settings":
        # Synchronize SUPABASE_KEY and SUPABASE_SERVICE_ROLE_KEY for seamless compatibility
        if not self.SUPABASE_KEY and self.SUPABASE_SERVICE_ROLE_KEY:
            self.SUPABASE_KEY = self.SUPABASE_SERVICE_ROLE_KEY
        elif not self.SUPABASE_SERVICE_ROLE_KEY and self.SUPABASE_KEY:
            self.SUPABASE_SERVICE_ROLE_KEY = self.SUPABASE_KEY

        # In production/staging, validate that essential integration credentials are provided
        if self.ENVIRONMENT in ("production", "staging"):
            missing = []
            if not self.SUPABASE_URL:
                missing.append("SUPABASE_URL")
            if not self.SUPABASE_KEY and not self.SUPABASE_SERVICE_ROLE_KEY:
                missing.append("SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY)")
            if not self.GEMINI_API_KEY:
                missing.append("GEMINI_API_KEY")
            if missing:
                raise ValueError(
                    f"Missing required configuration settings for environment '{self.ENVIRONMENT}': {', '.join(missing)}"
                )
        return self

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
