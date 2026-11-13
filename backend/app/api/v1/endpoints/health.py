from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns service health status, current timestamp, and API version.",
)
async def get_health() -> HealthResponse:
    """Return application health status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.PROJECT_VERSION,
    )

