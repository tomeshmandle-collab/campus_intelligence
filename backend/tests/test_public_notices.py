from datetime import date, datetime, timedelta, timezone
import uuid

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.supabase import SupabaseService, get_supabase_service


@pytest.fixture(autouse=True)
def mock_supabase_service():
    """Ensure tests run with an isolated in-memory Supabase service."""
    svc = SupabaseService(is_mock=True)
    app.dependency_overrides[get_supabase_service] = lambda: svc
    yield svc
    app.dependency_overrides.pop(get_supabase_service, None)


def _seed_notice(
    svc: SupabaseService,
    *,
    notice_id: str | None = None,
    title: str = "Notice Title",
    notice_date: str | None = "2026-11-10",
    deadline_date: str | None = None,
    audience: str = "student",
    category: str | None = "examination",
    summary: str | None = "Structured summary of official circular.",
    publication_status: str = "published",
    processing_status: str = "completed",
    relationship_status: str = "current",
    published_at: str = "2026-11-12T10:00:00Z",
    review_reasons: list[str] | None = None,
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
        "review_reasons": review_reasons or [],
        "published_at": published_at,
        "published_by": "00000000-0000-0000-0000-000000000001",
        "withdrawn_by": "00000000-0000-0000-0000-000000000002"
        if publication_status == "withdrawn"
        else None,
        "withdrawal_reason": "Superseded internally"
        if publication_status == "withdrawn"
        else None,
        "created_at": "2026-11-12T09:00:00Z",
        "updated_at": published_at,
    }
    return nid


def test_filters_endpoint_returns_controlled_vocabularies(client: TestClient):
    resp = client.get("/api/v1/filters")
    assert resp.status_code == 200
    data = resp.json()
    assert [a["id"] for a in data["audiences"]] == [
        "student",
        "faculty",
        "staff",
        "all",
        "unspecified",
    ]
    assert [c["id"] for c in data["categories"]] == [
        "academic",
        "examination",
        "admissions",
        "events_workshops",
        "faculty",
        "administration",
        "general",
        "other",
    ]


def test_list_notices_strictly_excludes_held_withdrawn_and_internal_fields(
    client: TestClient, mock_supabase_service: SupabaseService
):
    pub_id = _seed_notice(
        mock_supabase_service,
        title="Published Exam Notice",
        publication_status="published",
        deadline_date="2026-12-01",
    )
    _seed_notice(
        mock_supabase_service,
        title="Held Confidential Notice",
        publication_status="held",
        review_reasons=["missing_notice_date"],
    )
    _seed_notice(
        mock_supabase_service,
        title="Withdrawn Notice",
        publication_status="withdrawn",
    )
    _seed_notice(
        mock_supabase_service,
        title="Failed Held Notice",
        publication_status="held",
        processing_status="failed",
    )

    resp = client.get("/api/v1/notices")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] == 1
    assert [item["id"] for item in data["items"]] == [pub_id]

    item = data["items"][0]
    for forbidden in (
        "storage_path",
        "review_reasons",
        "processing_status",
        "published_by",
        "withdrawn_by",
        "withdrawal_reason",
    ):
        assert forbidden not in item


def test_list_notices_audience_and_category_filtering_rules(
    client: TestClient, mock_supabase_service: SupabaseService
):
    student_id = _seed_notice(
        mock_supabase_service,
        title="Student Exam Form",
        audience="student",
        category="examination",
        published_at="2026-11-12T10:03:00Z",
    )
    all_id = _seed_notice(
        mock_supabase_service,
        title="Campus Holiday",
        audience="all",
        category="general",
        published_at="2026-11-12T10:02:00Z",
    )
    faculty_id = _seed_notice(
        mock_supabase_service,
        title="Faculty FDP",
        audience="faculty",
        category="events_workshops",
        published_at="2026-11-12T10:01:00Z",
    )
    unspec_id = _seed_notice(
        mock_supabase_service,
        title="Unspecified Audience Circular",
        audience="unspecified",
        category="general",
        published_at="2026-11-12T10:00:00Z",
    )

    # Unfiltered / audience=all includes unspecified
    resp_all = client.get("/api/v1/notices")
    assert resp_all.status_code == 200
    assert [i["id"] for i in resp_all.json()["items"]] == [
        student_id,
        all_id,
        faculty_id,
        unspec_id,
    ]

    # audience=student includes student + all, never unspecified
    resp_student = client.get("/api/v1/notices?audience=student")
    assert resp_student.status_code == 200
    assert [i["id"] for i in resp_student.json()["items"]] == [student_id, all_id]

    # audience=unspecified returns ONLY unspecified
    resp_unspec = client.get("/api/v1/notices?audience=unspecified")
    assert resp_unspec.status_code == 200
    assert [i["id"] for i in resp_unspec.json()["items"]] == [unspec_id]

    # category filter (and alias 'exams')
    resp_cat = client.get("/api/v1/notices?category=exams")
    assert resp_cat.status_code == 200
    assert [i["id"] for i in resp_cat.json()["items"]] == [student_id]

    # pagination
    resp_page = client.get("/api/v1/notices?limit=2&offset=1")
    assert resp_page.status_code == 200
    assert [i["id"] for i in resp_page.json()["items"]] == [all_id, faculty_id]
    assert resp_page.json()["pagination"] == {
        "limit": 2,
        "offset": 1,
        "total": 4,
        "has_more": True,
    }


def test_briefing_returns_top_5_upcoming_deadlines_and_newest_published(
    client: TestClient, mock_supabase_service: SupabaseService
):
    today_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()

    # Create 7 published notices with upcoming deadlines
    upcoming_ids = []
    for days_ahead in (12, 2, 20, 4, 1, 9, 15):
        nid = _seed_notice(
            mock_supabase_service,
            title=f"Deadline in {days_ahead} days",
            deadline_date=(today_ist + timedelta(days=days_ahead)).isoformat(),
            published_at=f"2026-11-{10 + (days_ahead % 10):02d}T10:00:00Z",
        )
        upcoming_ids.append((days_ahead, nid))

    # Past deadline should NOT appear in upcoming_deadlines
    _seed_notice(
        mock_supabase_service,
        title="Past Deadline Notice",
        deadline_date=(today_ist - timedelta(days=2)).isoformat(),
        published_at="2026-11-01T10:00:00Z",
    )

    # Cancelled/superseded notice deadline must be excluded from upcoming deadlines
    _seed_notice(
        mock_supabase_service,
        title="Cancelled Notice",
        deadline_date=(today_ist + timedelta(days=1)).isoformat(),
        relationship_status="cancelled",
        published_at="2026-11-19T10:00:00Z",
    )

    # Held notice must NEVER appear in briefing
    _seed_notice(
        mock_supabase_service,
        title="Held Secret Deadline",
        deadline_date=(today_ist + timedelta(days=1)).isoformat(),
        publication_status="held",
        published_at="2026-11-25T10:00:00Z",
    )

    for path in ("/api/v1/notices/briefing", "/api/v1/briefing"):
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()

        # Top 5 upcoming deadlines sorted earliest first
        deadlines = data["upcoming_deadlines"]
        assert len(deadlines) == 5
        expected_top5_days = [1, 2, 4, 9, 12]
        expected_ids = [
            next(nid for d, nid in upcoming_ids if d == target_d)
            for target_d in expected_top5_days
        ]
        assert [item["notice_id"] for item in deadlines] == expected_ids

        # Top 5 newest published notices
        newest = data["newest_notices"]
        assert len(newest) == 5
        assert len(data["sections"]["recently_posted"]) == 5
        assert all(item["title"] != "Held Secret Deadline" for item in newest)


def test_briefing_recent_changes_excludes_unconfirmed_and_hides_held_related_notice(
    client: TestClient, mock_supabase_service: SupabaseService
):
    held_earlier = _seed_notice(
        mock_supabase_service,
        title="Held Earlier Notice",
        publication_status="held",
    )
    pub_later = _seed_notice(
        mock_supabase_service,
        title="Published Amending Notice",
        publication_status="published",
        published_at="2026-11-20T10:00:00Z",
    )
    pub_other = _seed_notice(
        mock_supabase_service,
        title="Published Unconfirmed Later",
        publication_status="published",
    )

    mock_supabase_service._in_memory_relationships[1] = {
        "id": 1,
        "earlier_id": held_earlier,
        "later_id": pub_later,
        "relation": "amends",
        "confirmed": True,
    }
    mock_supabase_service._in_memory_relationships[2] = {
        "id": 2,
        "earlier_id": pub_later,
        "later_id": pub_other,
        "relation": "replaces",
        "confirmed": False,
    }

    resp = client.get("/api/v1/notices/briefing")
    assert resp.status_code == 200
    changes = resp.json()["sections"]["recent_changes"]
    assert len(changes) == 1
    assert changes[0]["notice_id"] == pub_later
    assert changes[0]["related_notice"] is None


def test_notice_detail_returns_15min_signed_url_and_404_for_held_or_withdrawn(
    client: TestClient, mock_supabase_service: SupabaseService, monkeypatch
):
    pub_id = _seed_notice(
        mock_supabase_service,
        title="Merit Scholarship Guidelines",
        notice_date="2026-11-10",
        deadline_date="2026-11-30",
        audience="student",
        category="academic",
        summary="Detailed scholarship application steps.",
        publication_status="published",
    )
    held_id = _seed_notice(mock_supabase_service, publication_status="held")
    withdrawn_id = _seed_notice(mock_supabase_service, publication_status="withdrawn")

    mock_supabase_service._in_memory_field_sources[pub_id] = [
        {
            "notice_id": pub_id,
            "field_name": "title",
            "human_edited": True,
        },
        {
            "notice_id": pub_id,
            "field_name": "summary",
            "human_edited": False,
        },
    ]

    # Confirmed link to published earlier notice vs held notice
    pub_earlier = _seed_notice(
        mock_supabase_service,
        title="Earlier Published Notice",
        publication_status="published",
    )
    mock_supabase_service._in_memory_relationships[1] = {
        "id": 1,
        "earlier_id": pub_earlier,
        "later_id": pub_id,
        "relation": "extends",
        "confirmed": True,
    }
    mock_supabase_service._in_memory_relationships[2] = {
        "id": 2,
        "earlier_id": held_id,
        "later_id": pub_id,
        "relation": "amends",
        "confirmed": True,
    }

    captured_sign_args = {}

    async def fake_create_signed_url(bucket: str, path: str, expires_in: int = 900):
        captured_sign_args["bucket"] = bucket
        captured_sign_args["path"] = path
        captured_sign_args["expires_in"] = expires_in
        return "https://signed.example.supabase.co/token-123"

    monkeypatch.setattr(mock_supabase_service, "create_signed_url", fake_create_signed_url)

    resp = client.get(f"/api/v1/notices/{pub_id}")
    assert resp.status_code == 200
    body = resp.json()["notice"]
    assert body["id"] == pub_id
    assert body["title"] == "Merit Scholarship Guidelines"
    assert body["summary"] == "Detailed scholarship application steps."
    assert body["issue_date"] == "2026-11-10"
    assert body["important_dates"][0]["starts_on"] == "2026-11-30"
    assert body["field_labels"] == {"title": "human_corrected", "summary": "ai_extracted"}
    assert body["source_file"] == {
        "available": True,
        "download_url": "https://signed.example.supabase.co/token-123",
    }
    assert captured_sign_args == {
        "bucket": "notice-originals",
        "path": f"originals/{pub_id}.pdf",
        "expires_in": 900,
    }
    # Only the published confirmed relation appears; held relation is excluded
    assert body["related_notices"] == [
        {
            "notice_id": pub_earlier,
            "title": "Earlier Published Notice",
            "relation": "extends",
            "direction": "earlier",
        }
    ]
    for forbidden in ("storage_path", "review_reasons", "processing_status", "published_by"):
        assert forbidden not in body

    # Held, withdrawn, and non-existent notices must all return 404 identically
    for hidden_id in (held_id, withdrawn_id, str(uuid.uuid4())):
        hidden_resp = client.get(f"/api/v1/notices/{hidden_id}")
        assert hidden_resp.status_code == 404
        assert hidden_resp.json()["error"]["code"] == "NOT_FOUND"
