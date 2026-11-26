import io
import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status

from app.main import app
from app.services.supabase import get_supabase_service, SupabaseService

VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"


@pytest.fixture(autouse=True)
def mock_supabase_service():
    """Ensure tests run with an isolated in-memory Supabase service."""
    svc = SupabaseService(is_mock=True)
    app.dependency_overrides[get_supabase_service] = lambda: svc
    yield svc
    app.dependency_overrides.pop(get_supabase_service, None)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer mock-uploader-token"}


@pytest.fixture
def admin_headers():
    return {"Authorization": "Bearer mock-admin-token"}


@pytest.fixture
def viewer_headers():
    return {"Authorization": "Bearer mock-viewer-token"}


def test_upload_missing_auth_returns_401(client: TestClient):
    """Verify upload fails with 401 when Authorization header is omitted."""
    files = {"file": ("test.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files)
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_upload_invalid_token_returns_401(client: TestClient):
    """Verify upload fails with 401 when token is malformed."""
    files = {"file": ("test.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    headers = {"Authorization": "Bearer ???not-a-valid-jwt-or-token???"}
    response = client.post("/api/v1/notices/upload", files=files, headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_upload_unauthorized_role_returns_403(client: TestClient, viewer_headers: dict):
    """Verify non-uploader/admin role receives 403 Forbidden."""
    files = {"file": ("test.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=viewer_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_upload_valid_pdf_succeeds(client: TestClient, auth_headers: dict, mock_supabase_service: SupabaseService):
    """Verify valid upload returns 202 Accepted with notice_id and pending status."""
    filename = "KMC_Exam_Schedule_2026.pdf"
    files = {"file": (filename, io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=auth_headers)

    assert response.status_code == 202
    data = response.json()
    assert "notice_id" in data
    assert data["status"] == "pending"

    # Validate UUID format
    notice_id = data["notice_id"]
    parsed_uuid = uuid.UUID(notice_id)
    assert str(parsed_uuid) == notice_id

    # Verify storage and notice record
    svc = mock_supabase_service
    expected_path = f"notice-originals/originals/{notice_id}.pdf"
    assert expected_path in svc._in_memory_storage
    assert svc._in_memory_storage[expected_path] == VALID_PDF_BYTES

    notice = svc._in_memory_notices.get(notice_id)
    assert notice is not None
    assert notice["processing_status"] == "pending"
    assert notice["publication_status"] == "held"
    assert notice["storage_path"] == f"originals/{notice_id}.pdf"
    assert notice["title"] == filename


def test_upload_admin_role_succeeds(client: TestClient, admin_headers: dict):
    """Verify admin role is also permitted to upload notices."""
    files = {"file": ("Admin_Notice.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=admin_headers)
    assert response.status_code == 202
    assert response.json()["status"] == "pending"


def test_upload_alias_uploader_notices_endpoint(client: TestClient, auth_headers: dict):
    """Verify alias endpoint /api/v1/uploader/notices behaves identically."""
    files = {"file": ("Notice.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    response = client.post("/api/v1/uploader/notices", files=files, headers=auth_headers)
    assert response.status_code == 202
    assert "notice_id" in response.json()
    assert response.json()["status"] == "pending"


def test_upload_invalid_magic_bytes_returns_415(client: TestClient, auth_headers: dict):
    """Verify non-PDF file content rejected with 415 Unsupported Media Type."""
    fake_content = b"<html><body>Not a PDF file</body></html>"
    files = {"file": ("malicious.html.pdf", io.BytesIO(fake_content), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=auth_headers)

    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert "%PDF-" in data["error"]["message"]


def test_upload_empty_file_returns_400_or_415(client: TestClient, auth_headers: dict):
    """Verify zero-byte empty file is rejected."""
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=auth_headers)
    assert response.status_code in (400, 415)


def test_upload_oversized_file_returns_413(client: TestClient, auth_headers: dict, monkeypatch):
    """Verify files exceeding MAX_UPLOAD_SIZE_BYTES are rejected with 413 Payload Too Large."""
    # Temporarily set max size to 100 bytes for fast test execution
    from app.core import config
    monkeypatch.setattr(config.settings, "MAX_UPLOAD_SIZE_BYTES", 100)

    oversized_content = b"%PDF-" + b"A" * 200
    files = {"file": ("huge.pdf", io.BytesIO(oversized_content), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=auth_headers)

    assert response.status_code == 413
    data = response.json()
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_storage_failure_returns_502(client: TestClient, auth_headers: dict, mock_supabase_service: SupabaseService, monkeypatch):
    """Verify downstream storage failure returns 502 Bad Gateway."""
    async def mock_upload_failure(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service unavailable.",
        )

    monkeypatch.setattr(mock_supabase_service, "upload_file", mock_upload_failure)

    files = {"file": ("valid.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    response = client.post("/api/v1/notices/upload", files=files, headers=auth_headers)

    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "BAD_GATEWAY"
