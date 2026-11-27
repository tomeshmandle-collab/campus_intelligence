from pathlib import Path
import re
import uuid

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.supabase import SupabaseService, get_supabase_service

MIGRATION_002_PATH = (
    Path(__file__).resolve().parent.parent / "migrations" / "002_review_audit_and_lifecycle.sql"
)


@pytest.fixture(autouse=True)
def mock_supabase_service():
    """Ensure tests run with an isolated in-memory Supabase service."""
    svc = SupabaseService(is_mock=True)
    app.dependency_overrides[get_supabase_service] = lambda: svc
    yield svc
    app.dependency_overrides.pop(get_supabase_service, None)


@pytest.fixture
def uploader_headers():
    return {"Authorization": "Bearer mock-uploader-token"}


@pytest.fixture
def viewer_headers():
    return {"Authorization": "Bearer mock-viewer-token"}


def _seed_notice(
    svc: SupabaseService,
    *,
    notice_id: str | None = None,
    title: str = "Provisional Exam Notice",
    notice_date: str | None = "2026-11-10",
    deadline_date: str | None = "2026-11-25",
    audience: str = "student",
    category: str | None = "examination",
    summary: str | None = "Semester exam form submission notice.",
    processing_status: str = "completed",
    publication_status: str = "held",
    relationship_status: str = "current",
    review_reasons: list[str] | None = None,
    updated_at: str = "2026-11-12T10:30:00Z",
) -> str:
    nid = notice_id or str(uuid.uuid4())
    svc._in_memory_notices[nid] = {
        "id": nid,
        "title": title,
        "notice_date": notice_date,
        "deadline_date": deadline_date,
        "audience": audience,
        "category": category,
        "summary": summary,
        "storage_path": f"originals/{nid}.pdf",
        "processing_status": processing_status,
        "publication_status": publication_status,
        "relationship_status": relationship_status,
        "review_reasons": review_reasons if review_reasons is not None else [],
        "created_at": "2026-11-12T10:00:00Z",
        "updated_at": updated_at,
    }
    return nid


def test_review_endpoints_enforce_authentication_and_uploader_role(
    client: TestClient, viewer_headers: dict
):
    nid = str(uuid.uuid4())
    endpoints = [
        ("GET", "/api/v1/uploader/review-queue"),
        ("GET", "/api/v1/review-queue"),
        ("GET", f"/api/v1/uploader/notices/{nid}"),
        ("GET", f"/api/v1/notices/{nid}/review"),
        ("PATCH", f"/api/v1/uploader/notices/{nid}"),
        ("PATCH", f"/api/v1/notices/{nid}/fields"),
        ("POST", f"/api/v1/uploader/notices/{nid}/publish"),
        ("POST", f"/api/v1/notices/{nid}/publish"),
        ("POST", f"/api/v1/uploader/notices/{nid}/retry"),
        ("POST", f"/api/v1/notices/{nid}/relationships/1/confirm"),
        ("PATCH", "/api/v1/uploader/relations/1"),
    ]
    for method, url in endpoints:
        unauth_resp = client.request(method, url)
        assert unauth_resp.status_code == 401, f"Expected 401 for {method} {url}"

        forbid_resp = client.request(method, url, headers=viewer_headers)
        assert forbid_resp.status_code == 403, f"Expected 403 for {method} {url}"


def test_review_queue_lists_held_and_failed_notices_only(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    held_id = _seed_notice(
        mock_supabase_service,
        title="Held Notice",
        publication_status="held",
        review_reasons=["missing_notice_date"],
        updated_at="2026-11-12T11:00:00Z",
    )
    failed_id = _seed_notice(
        mock_supabase_service,
        title="Failed Notice",
        processing_status="failed",
        publication_status="held",
        review_reasons=["ai_extraction_failed"],
        updated_at="2026-11-12T12:00:00Z",
    )
    _seed_notice(
        mock_supabase_service,
        title="Published Notice",
        publication_status="published",
        review_reasons=[],
    )
    _seed_notice(
        mock_supabase_service,
        title="Withdrawn Notice",
        publication_status="withdrawn",
        review_reasons=[],
    )

    for path in ("/api/v1/uploader/review-queue", "/api/v1/review-queue"):
        resp = client.get(path, headers=uploader_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 2
        ids = [item["notice_id"] for item in data["items"]]
        assert ids == [failed_id, held_id]
        assert data["items"][0]["review_reasons"] == ["ai_extraction_failed"]
        assert data["items"][1]["review_reasons"] == ["missing_notice_date"]
        assert data["items"][1]["hold_reason"] is not None


def test_review_queue_pagination(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    for idx in range(3):
        _seed_notice(
            mock_supabase_service,
            title=f"Held {idx}",
            review_reasons=["missing_notice_date"],
            updated_at=f"2026-11-12T10:0{idx}:00Z",
        )

    resp = client.get("/api/v1/uploader/review-queue?limit=2&offset=0", headers=uploader_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["pagination"] == {"limit": 2, "offset": 0, "total": 3, "has_more": True}


def test_get_review_detail_returns_evidence_pages_relations_without_storage_path(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    nid = _seed_notice(
        mock_supabase_service,
        review_reasons=["deadline_prior_to_notice_date"],
    )
    earlier_id = _seed_notice(mock_supabase_service, publication_status="published")

    mock_supabase_service._in_memory_notice_pages[nid] = [
        {"notice_id": nid, "page_number": 2, "extracted_text": "Page 2 text", "is_scanned": False},
        {"notice_id": nid, "page_number": 1, "extracted_text": "Page 1 text", "is_scanned": False},
    ]
    mock_supabase_service._in_memory_field_sources[nid] = [
        {
            "notice_id": nid,
            "field_name": "title",
            "value_text": "Provisional Exam Notice",
            "source_page": 1,
            "source_quote": "Provisional Exam Notice",
            "extraction_method": "ai",
            "verified": True,
            "human_edited": False,
        }
    ]
    mock_supabase_service._in_memory_relationships[1] = {
        "id": 1,
        "earlier_id": earlier_id,
        "later_id": nid,
        "relation": "amends",
        "basis": "explicit_reference",
        "evidence_page": 1,
        "evidence_text": "This notice amends the earlier notice.",
        "confirmed": False,
    }

    for path in (f"/api/v1/uploader/notices/{nid}", f"/api/v1/notices/{nid}/review"):
        resp = client.get(path, headers=uploader_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["notice"]["id"] == nid
        assert [p["page_number"] for p in data["pages"]] == [1, 2]
        assert data["pages"][0]["extracted_text"] == "Page 1 text"
        assert data["field_evidence"]["title"]["page_number"] == 1
        assert data["field_evidence"]["title"]["quote"] == "Provisional Exam Notice"
        assert len(data["relations"]) == 1
        assert data["relations"][0]["confirmed"] is False
        assert data["source"]["page_count"] == 2
        assert "storage_path" not in data["notice"]
        assert "storage_path" not in data["source"]

    missing = client.get(f"/api/v1/notices/{uuid.uuid4()}/review", headers=uploader_headers)
    assert missing.status_code == 404


def test_patch_fields_updates_record_logs_audit_and_keeps_held(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    nid = _seed_notice(
        mock_supabase_service,
        title="Old Title",
        notice_date=None,
        deadline_date="2026-11-30",
        audience="unspecified",
        category="general",
        review_reasons=["missing_notice_date", "unreliable_ocr"],
    )

    resp = client.patch(
        f"/api/v1/notices/{nid}/fields",
        headers=uploader_headers,
        json={
            "title": "Updated Exam Schedule",
            "notice_date": "2026-11-15",
            "deadline_date": "2026-11-30",
            "audience": "student",
            "category": "examination",
            "correction_note": "Verified from scanned PDF page 1.",
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    # Editing must never auto-publish
    assert body["notice"]["publication_status"] == "held"
    assert body["notice"]["title"] == "Updated Exam Schedule"
    assert body["notice"]["notice_date"] == "2026-11-15"
    assert body["notice"]["audience"] == "student"
    assert body["notice"]["category"] == "examination"
    assert body["review_reasons"] == []

    # Verify audit log entries in notice_edits
    edits = mock_supabase_service._in_memory_notice_edits[nid]
    changed_fields = {e["field_name"]: e for e in edits}
    assert changed_fields["title"]["old_value"] == "Old Title"
    assert changed_fields["title"]["new_value"] == "Updated Exam Schedule"
    assert changed_fields["notice_date"]["old_value"] is None
    assert changed_fields["notice_date"]["new_value"] == "2026-11-15"
    assert changed_fields["audience"]["old_value"] == "unspecified"
    assert changed_fields["audience"]["new_value"] == "student"
    assert changed_fields["category"]["new_value"] == "examination"
    assert changed_fields["title"]["note"] == "Verified from scanned PDF page 1."
    assert changed_fields["title"]["edited_by"] == "00000000-0000-0000-0000-000000000001"

    # Verify field_sources marked human_edited
    fs = {f["field_name"]: f for f in mock_supabase_service._in_memory_field_sources[nid]}
    assert fs["title"]["human_edited"] is True
    assert fs["title"]["extraction_method"] == "human"


def test_patch_fields_rejects_unapproved_fields_and_withdrawn_notices(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    nid = _seed_notice(mock_supabase_service, publication_status="held")
    bad_field = client.patch(
        f"/api/v1/uploader/notices/{nid}",
        headers=uploader_headers,
        json={"publication_status": "published"},
    )
    assert bad_field.status_code == 422

    empty_patch = client.patch(
        f"/api/v1/notices/{nid}/fields",
        headers=uploader_headers,
        json={"correction_note": "No actual field change"},
    )
    assert empty_patch.status_code == 400

    withdrawn_id = _seed_notice(mock_supabase_service, publication_status="withdrawn")
    withdrawn_resp = client.patch(
        f"/api/v1/notices/{withdrawn_id}/fields",
        headers=uploader_headers,
        json={"title": "Cannot edit"},
    )
    assert withdrawn_resp.status_code == 409


def test_publish_blocks_unresolved_reasons_and_publishes_when_cleared(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    nid = _seed_notice(
        mock_supabase_service,
        notice_date="2026-11-25",
        deadline_date="2026-11-10",
        review_reasons=["deadline_prior_to_notice_date"],
    )

    # Cannot publish while blocking reason remains
    blocked = client.post(
        f"/api/v1/uploader/notices/{nid}/publish",
        headers=uploader_headers,
        json={"confirmation": True},
    )
    assert blocked.status_code == 409
    assert "deadline_prior_to_notice_date" in blocked.json()["error"]["message"]
    assert mock_supabase_service._in_memory_notices[nid]["publication_status"] == "held"

    # Fix dates via PATCH; blocking reason clears
    fix_resp = client.patch(
        f"/api/v1/notices/{nid}/fields",
        headers=uploader_headers,
        json={"deadline_date": "2026-11-30"},
    )
    assert fix_resp.status_code == 200
    assert fix_resp.json()["review_reasons"] == []

    # Confirmation=false must be rejected
    unconfirmed = client.post(
        f"/api/v1/notices/{nid}/publish",
        headers=uploader_headers,
        json={"confirmation": False},
    )
    assert unconfirmed.status_code == 400

    # Publish succeeds once blocking issues are cleared
    pub_resp = client.post(
        f"/api/v1/notices/{nid}/publish",
        headers=uploader_headers,
    )
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()
    assert pub_data["notice_id"] == nid
    assert pub_data["publication_status"] == "published"
    assert pub_data["published_at"]

    stored = mock_supabase_service._in_memory_notices[nid]
    assert stored["publication_status"] == "published"
    assert stored["published_by"] == "00000000-0000-0000-0000-000000000001"
    assert stored["review_reasons"] == []


def test_retry_processing_requeues_eligible_notices_and_preserves_history(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    nid = _seed_notice(
        mock_supabase_service,
        processing_status="failed",
        publication_status="held",
        review_reasons=["ai_extraction_failed"],
    )
    mock_supabase_service._in_memory_processing_events[nid] = [
        {"notice_id": nid, "step": "ai_extraction", "outcome": "failed", "message": "Timeout"}
    ]

    resp = client.post(
        f"/api/v1/uploader/notices/{nid}/retry",
        headers=uploader_headers,
        json={"confirmation": True},
    )
    assert resp.status_code == 200
    assert resp.json() == {"notice_id": nid, "processing_status": "pending"}
    assert mock_supabase_service._in_memory_notices[nid]["processing_status"] == "pending"
    assert len(mock_supabase_service._in_memory_processing_events[nid]) == 2

    pub_id = _seed_notice(
        mock_supabase_service,
        processing_status="completed",
        publication_status="published",
    )
    ineligible = client.post(
        f"/api/v1/uploader/notices/{pub_id}/retry",
        headers=uploader_headers,
        json={"confirmation": True},
    )
    assert ineligible.status_code == 409


def test_confirm_relationship_updates_published_earlier_notice_only(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    published_earlier_id = _seed_notice(
        mock_supabase_service,
        title="Original Exam Notice",
        publication_status="published",
        relationship_status="current",
    )
    held_later_id = _seed_notice(
        mock_supabase_service,
        title="Extension Notice",
        publication_status="held",
        relationship_status="current",
        review_reasons=["low_extraction_confidence"],
    )
    mock_supabase_service._in_memory_relationships[10] = {
        "id": 10,
        "earlier_id": published_earlier_id,
        "later_id": held_later_id,
        "relation": "extends",
        "basis": "explicit_reference",
        "evidence_page": 1,
        "evidence_text": "Extends deadline of Original Exam Notice.",
        "confirmed": False,
    }

    resp = client.post(
        f"/api/v1/notices/{held_later_id}/relationships/10/confirm",
        headers=uploader_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome"] == "confirmed"
    assert data["earlier_relationship_status"] == "extended"

    # Earlier published notice updated; held later notice remains held & current
    assert (
        mock_supabase_service._in_memory_notices[published_earlier_id]["relationship_status"]
        == "extended"
    )
    assert mock_supabase_service._in_memory_notices[held_later_id]["publication_status"] == "held"
    assert (
        mock_supabase_service._in_memory_notices[held_later_id]["relationship_status"]
        == "current"
    )
    assert mock_supabase_service._in_memory_relationships[10]["confirmed"] is True


def test_confirm_relationship_does_not_modify_unapproved_held_notice(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    held_earlier_id = _seed_notice(
        mock_supabase_service,
        title="Unapproved Earlier Notice",
        publication_status="held",
        relationship_status="current",
    )
    held_later_id = _seed_notice(
        mock_supabase_service,
        title="Unapproved Later Notice",
        publication_status="held",
        relationship_status="current",
    )
    mock_supabase_service._in_memory_relationships[11] = {
        "id": 11,
        "earlier_id": held_earlier_id,
        "later_id": held_later_id,
        "relation": "replaces",
        "basis": "explicit_reference",
        "evidence_page": 1,
        "evidence_text": "Replaces earlier notice.",
        "confirmed": False,
    }

    resp = client.post(
        f"/api/v1/notices/{held_later_id}/relationships/11/confirm",
        headers=uploader_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "confirmed"

    # Unapproved earlier and later notices must remain completely unmodified
    assert mock_supabase_service._in_memory_notices[held_earlier_id]["publication_status"] == "held"
    assert (
        mock_supabase_service._in_memory_notices[held_earlier_id]["relationship_status"]
        == "current"
    )
    assert mock_supabase_service._in_memory_notices[held_later_id]["publication_status"] == "held"


def test_reject_relationship_removes_candidate_without_touching_notices(
    client: TestClient, uploader_headers: dict, mock_supabase_service: SupabaseService
):
    earlier_id = _seed_notice(
        mock_supabase_service,
        publication_status="published",
        relationship_status="current",
    )
    later_id = _seed_notice(
        mock_supabase_service,
        publication_status="held",
        relationship_status="current",
    )
    mock_supabase_service._in_memory_relationships[12] = {
        "id": 12,
        "earlier_id": earlier_id,
        "later_id": later_id,
        "relation": "cancels",
        "basis": "explicit_reference",
        "confirmed": False,
    }

    resp = client.patch(
        "/api/v1/uploader/relations/12",
        headers=uploader_headers,
        json={"action": "reject"},
    )
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "rejected"
    assert 12 not in mock_supabase_service._in_memory_relationships
    assert mock_supabase_service._in_memory_notices[earlier_id]["relationship_status"] == "current"


def test_migration_002_schema_and_rls_security():
    assert MIGRATION_002_PATH.exists()
    sql = MIGRATION_002_PATH.read_text(encoding="utf-8")

    for col in ("relationship_status", "published_at", "published_by"):
        assert re.search(rf"\b{col}\b", sql, re.IGNORECASE)

    for table in ("field_sources", "notice_edits", "processing_events"):
        assert re.search(rf"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+{table}\b", sql, re.IGNORECASE)
        assert re.search(
            rf"ALTER\s+TABLE\s+{table}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY\s*;",
            sql,
            re.IGNORECASE,
        )

    assert re.search(
        r"REVOKE\s+ALL\s+ON\s+ALL\s+TABLES\s+IN\s+SCHEMA\s+public\s+FROM\s+anon\s*,\s*authenticated\s*;",
        sql,
        re.IGNORECASE,
    )
