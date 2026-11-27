from pathlib import Path
import re
import uuid

from fastapi.testclient import TestClient
import pytest

from app.core import config
from app.main import app
from app.services.public_notices_service import report_rate_limiter
from app.services.supabase import SupabaseService, get_supabase_service

MIGRATION_003_PATH = (
    Path(__file__).resolve().parent.parent / "migrations" / "003_withdrawal_columns.sql"
)


@pytest.fixture(autouse=True)
def isolated_services():
    """Provide isolated in-memory SupabaseService and clean rate-limiter state per test."""
    svc = SupabaseService(is_mock=True)
    report_rate_limiter.reset()
    app.dependency_overrides[get_supabase_service] = lambda: svc
    yield svc
    app.dependency_overrides.pop(get_supabase_service, None)
    report_rate_limiter.reset()


@pytest.fixture
def uploader_headers():
    return {"Authorization": "Bearer mock-uploader-token"}


@pytest.fixture
def viewer_headers():
    return {"Authorization": "Bearer mock-viewer-token"}


def _seed_notice(
    svc: SupabaseService,
    *,
    title: str = "Official Notice",
    publication_status: str = "published",
    processing_status: str = "completed",
    relationship_status: str = "current",
    created_at: str = "2026-11-12T09:00:00Z",
) -> str:
    nid = str(uuid.uuid4())
    svc._in_memory_notices[nid] = {
        "id": nid,
        "title": title,
        "notice_date": "2026-11-10",
        "deadline_date": "2026-11-28",
        "audience": "student",
        "category": "examination",
        "summary": "Official circular summary.",
        "storage_path": f"originals/{nid}.pdf",
        "processing_status": processing_status,
        "publication_status": publication_status,
        "relationship_status": relationship_status,
        "review_reasons": [],
        "uploaded_at": created_at,
        "published_at": "2026-11-12T10:30:00Z" if publication_status == "published" else None,
        "created_at": created_at,
        "updated_at": created_at,
    }
    return nid


def test_management_and_report_staff_endpoints_enforce_rbac(
    client: TestClient, viewer_headers: dict
):
    nid = str(uuid.uuid4())
    protected = [
        ("GET", "/api/v1/uploader/notices"),
        ("POST", f"/api/v1/uploader/notices/{nid}/withdraw"),
        ("GET", "/api/v1/uploader/reports"),
        ("PATCH", "/api/v1/uploader/reports/1"),
    ]
    for method, url in protected:
        assert client.request(method, url).status_code == 401
        assert client.request(method, url, headers=viewer_headers).status_code == 403


def test_management_notices_returns_all_statuses_and_supports_filters(
    client: TestClient, uploader_headers: dict, isolated_services: SupabaseService
):
    pub_id = _seed_notice(
        isolated_services,
        title="Published Notice",
        publication_status="published",
        processing_status="completed",
        created_at="2026-11-12T10:03:00Z",
    )
    held_id = _seed_notice(
        isolated_services,
        title="Held Notice",
        publication_status="held",
        processing_status="completed",
        created_at="2026-11-12T10:02:00Z",
    )
    withdrawn_id = _seed_notice(
        isolated_services,
        title="Withdrawn Notice",
        publication_status="withdrawn",
        processing_status="completed",
        created_at="2026-11-12T10:01:00Z",
    )
    failed_id = _seed_notice(
        isolated_services,
        title="Failed Notice",
        publication_status="held",
        processing_status="failed",
        created_at="2026-11-12T10:00:00Z",
    )

    resp_all = client.get("/api/v1/uploader/notices", headers=uploader_headers)
    assert resp_all.status_code == 200
    body = resp_all.json()
    assert body["pagination"]["total"] == 4
    assert [i["notice_id"] for i in body["items"]] == [
        pub_id,
        held_id,
        withdrawn_id,
        failed_id,
    ]

    resp_withdrawn = client.get(
        "/api/v1/uploader/notices?publication_status=withdrawn",
        headers=uploader_headers,
    )
    assert resp_withdrawn.status_code == 200
    assert [i["notice_id"] for i in resp_withdrawn.json()["items"]] == [withdrawn_id]

    resp_failed = client.get(
        "/api/v1/uploader/notices?processing_status=failed",
        headers=uploader_headers,
    )
    assert resp_failed.status_code == 200
    assert [i["notice_id"] for i in resp_failed.json()["items"]] == [failed_id]


def test_withdraw_notice_records_reason_and_excludes_from_public_endpoints(
    client: TestClient, uploader_headers: dict, isolated_services: SupabaseService
):
    nid = _seed_notice(
        isolated_services,
        title="Circular to Withdraw",
        publication_status="published",
    )

    # Visible publicly before withdrawal
    assert client.get(f"/api/v1/notices/{nid}").status_code == 200

    resp = client.post(
        f"/api/v1/uploader/notices/{nid}/withdraw",
        headers=uploader_headers,
        json={"reason": "The source notice was recalled by the Registrar."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["notice_id"] == nid
    assert data["publication_status"] == "withdrawn"
    assert data["withdrawn_at"]

    stored = isolated_services._in_memory_notices[nid]
    assert stored["publication_status"] == "withdrawn"
    assert stored["withdrawal_reason"] == "The source notice was recalled by the Registrar."
    assert stored["withdrawn_by"] == "00000000-0000-0000-0000-000000000001"
    assert len(isolated_services._in_memory_processing_events[nid]) == 1

    # Excluded from all public endpoints after withdrawal
    assert client.get(f"/api/v1/notices/{nid}").status_code == 404
    assert client.get("/api/v1/notices").json()["items"] == []

    # Double withdrawal rejected with 409; empty reason rejected with 422
    assert (
        client.post(
            f"/api/v1/uploader/notices/{nid}/withdraw",
            headers=uploader_headers,
            json={"reason": "Already withdrawn"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/uploader/notices/{nid}/withdraw",
            headers=uploader_headers,
            json={"reason": "  "},
        ).status_code
        == 422
    )


def test_public_error_report_submission_and_isolation(
    client: TestClient, isolated_services: SupabaseService
):
    pub_id = _seed_notice(
        isolated_services, title="Published Notice", publication_status="published"
    )
    held_id = _seed_notice(
        isolated_services, title="Held Notice", publication_status="held"
    )
    withdrawn_id = _seed_notice(
        isolated_services, title="Withdrawn Notice", publication_status="withdrawn"
    )

    resp = client.post(
        f"/api/v1/notices/{pub_id}/reports",
        json={
            "issue_type": "incorrect_information",
            "description": "The displayed deadline appears incorrect.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "received"
    assert body["report_id"]

    # Reporting does NOT directly alter or hide the published notice
    assert isolated_services._in_memory_notices[pub_id]["publication_status"] == "published"

    # Cannot report held, withdrawn, or non-existent notices
    for hidden_id in (held_id, withdrawn_id, str(uuid.uuid4())):
        hidden_resp = client.post(
            f"/api/v1/notices/{hidden_id}/reports",
            json={"issue_type": "other", "description": "Testing hidden notice"},
        )
        assert hidden_resp.status_code == 404

    # Invalid issue_type and oversized description rejected
    assert (
        client.post(
            f"/api/v1/notices/{pub_id}/reports",
            json={"issue_type": "invalid_type", "description": "Bad type"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/notices/{pub_id}/reports",
            json={"issue_type": "other", "description": "X" * 1001},
        ).status_code
        == 422
    )


def test_public_error_report_ip_rate_limit(
    client: TestClient, isolated_services: SupabaseService, monkeypatch
):
    monkeypatch.setattr(config.settings, "REPORT_RATE_LIMIT_MAX_REQUESTS", 3)
    monkeypatch.setattr(config.settings, "REPORT_RATE_LIMIT_WINDOW_SECONDS", 60)

    pub_id = _seed_notice(isolated_services, publication_status="published")
    payload = {"issue_type": "incorrect_information", "description": "Wrong date"}

    for _ in range(3):
        ok_resp = client.post(
            f"/api/v1/notices/{pub_id}/reports",
            headers={"X-Forwarded-For": "203.0.113.10"},
            json=payload,
        )
        assert ok_resp.status_code == 201

    limited_resp = client.post(
        f"/api/v1/notices/{pub_id}/reports",
        headers={"X-Forwarded-For": "203.0.113.10"},
        json=payload,
    )
    assert limited_resp.status_code == 429
    assert limited_resp.json()["error"]["code"] == "RATE_LIMITED"

    # Different IP is unaffected
    other_ip_resp = client.post(
        f"/api/v1/notices/{pub_id}/reports",
        headers={"X-Forwarded-For": "203.0.113.99"},
        json=payload,
    )
    assert other_ip_resp.status_code == 201


def test_uploader_list_and_resolve_or_dismiss_reports(
    client: TestClient, uploader_headers: dict, isolated_services: SupabaseService
):
    pub_id = _seed_notice(
        isolated_services,
        title="Scholarship Notice 2026",
        publication_status="published",
    )

    r1 = client.post(
        f"/api/v1/notices/{pub_id}/reports",
        json={"issue_type": "incorrect_information", "description": "Wrong deadline"},
    ).json()["report_id"]
    r2 = client.post(
        f"/api/v1/notices/{pub_id}/reports",
        json={"issue_type": "other", "description": "Duplicate mention"},
    ).json()["report_id"]

    # Default GET /uploader/reports returns open reports with notice_title
    open_resp = client.get("/api/v1/uploader/reports", headers=uploader_headers)
    assert open_resp.status_code == 200
    open_data = open_resp.json()
    assert open_data["pagination"]["total"] == 2
    assert open_data["items"][0]["notice_title"] == "Scholarship Notice 2026"

    # Resolve first report
    resolve_resp = client.patch(
        f"/api/v1/uploader/reports/{r1}",
        headers=uploader_headers,
        json={"status": "resolved", "resolution_note": "Corrected deadline field."},
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "resolved"
    assert resolve_resp.json()["resolved_at"]

    # Dismiss second report
    dismiss_resp = client.patch(
        f"/api/v1/uploader/reports/{r2}",
        headers=uploader_headers,
        json={"status": "dismissed", "resolution_note": "Matches original PDF."},
    )
    assert dismiss_resp.status_code == 200
    assert dismiss_resp.json()["status"] == "dismissed"

    # Re-resolving already closed report returns 409; missing report returns 404
    assert (
        client.patch(
            f"/api/v1/uploader/reports/{r1}",
            headers=uploader_headers,
            json={"status": "dismissed"},
        ).status_code
        == 409
    )
    assert (
        client.patch(
            "/api/v1/uploader/reports/99999",
            headers=uploader_headers,
            json={"status": "resolved"},
        ).status_code
        == 404
    )

    # Filtered status queries reflect updates; notice itself remains published
    assert (
        client.get("/api/v1/uploader/reports?status=open", headers=uploader_headers)
        .json()["pagination"]["total"]
        == 0
    )
    assert (
        client.get("/api/v1/uploader/reports?status=resolved", headers=uploader_headers)
        .json()["items"][0]["resolution_note"]
        == "Corrected deadline field."
    )
    assert isolated_services._in_memory_notices[pub_id]["publication_status"] == "published"


def test_migration_003_withdrawal_columns():
    assert MIGRATION_003_PATH.exists()
    sql = MIGRATION_003_PATH.read_text(encoding="utf-8")
    for col in ("withdrawn_at", "withdrawn_by", "withdrawal_reason"):
        assert re.search(rf"\b{col}\b", sql, re.IGNORECASE)
