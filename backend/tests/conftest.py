import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a TestClient instance for API tests."""
    return TestClient(app)

