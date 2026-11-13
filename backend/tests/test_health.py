from datetime import datetime
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test GET /api/v1/health returns expected status and fields."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data

    # Verify timestamp is valid ISO format
    parsed_time = datetime.fromisoformat(data["timestamp"])
    assert parsed_time is not None


def test_cors_header(client: TestClient):
    """Test CORS headers for http://localhost:5173."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

