from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import app


class SamplePayload(BaseModel):
    required_field: str


@app.post("/api/v1/test-validation", include_in_schema=False)
def sample_validation_route(payload: SamplePayload):
    return {"status": "ok"}


def test_404_error_envelope(client: TestClient):
    """Test 404 StarletteHTTPException transforms into API_CONTRACTS envelope."""
    response = client.get("/api/v1/unknown-endpoint-404")
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "NOT_FOUND"
    assert "message" in error
    assert "request_id" in error


def test_validation_error_envelope(client: TestClient):
    """Test 422 RequestValidationError transforms into API_CONTRACTS envelope."""
    # Send empty body which is missing required_field
    response = client.post("/api/v1/test-validation", json={})
    assert response.status_code == 422

    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "The request could not be processed" in error["message"]
    assert "request_id" in error
    assert isinstance(error["details"], list)
    assert len(error["details"]) > 0
    assert error["details"][0]["field"] == "required_field"

