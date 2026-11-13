import json
import os
from typing import List, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file if available
load_dotenv()


class Settings(BaseModel):
    """Application runtime configuration settings."""

    PROJECT_NAME: str = "CAI Campus Intelligence API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # CORS configuration
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: (
            json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173"]'))
            if os.getenv("CORS_ORIGINS")
            else ["http://localhost:5173"]
        )
    )


settings = Settings()

