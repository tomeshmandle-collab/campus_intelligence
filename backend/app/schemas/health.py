from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""

    status: str = Field(default="healthy", description="Service health status")
    timestamp: str = Field(description="ISO 8601 timestamp with timezone")
    version: str = Field(default="1.0.0", description="API application version")

