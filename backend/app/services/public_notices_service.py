from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
import time
from typing import Any, Deque, Dict, List, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.notices import (
    BriefingDateItem,
    BriefingRecentChangeItem,
    BriefingRelatedNoticeRef,
    BriefingResponse,
    BriefingSections,
    ErrorReportCreateRequest,
    ErrorReportCreateResponse,
    FilterOption,
    FilterOptionsResponse,
    PublicAudienceTarget,
    PublicImportantDate,
    PublicNoticeDetail,
    PublicNoticeDetailResponse,
    PublicNoticeListItem,
    PublicNoticeListResponse,
    PublicRelatedNotice,
    PublicSourceFile,
)
from app.schemas.uploader import PaginationMeta
from app.services.supabase import SupabaseService

IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
SIGNED_URL_EXPIRY_SECONDS = 900  # 15 minutes

AUDIENCE_OPTIONS: List[FilterOption] = [
    FilterOption(id="student", label="Students"),
    FilterOption(id="faculty", label="Faculty"),
    FilterOption(id="staff", label="Staff"),
    FilterOption(id="all", label="Everyone"),
    FilterOption(id="unspecified", label="Not specified"),
]

CATEGORY_OPTIONS: List[FilterOption] = [
    FilterOption(id="academic", label="Academic"),
    FilterOption(id="examination", label="Examination"),
    FilterOption(id="admissions", label="Admissions"),
    FilterOption(id="events_workshops", label="Events and workshops"),
    FilterOption(id="faculty", label="Faculty"),
    FilterOption(id="administration", label="Administration"),
    FilterOption(id="general", label="General"),
    FilterOption(id="other", label="Other"),
]

CATEGORY_ALIASES: Dict[str, str] = {
    "exams": "examination",
    "exam": "examination",
    "events": "events_workshops",
    "events and workshops": "events_workshops",
}


def get_filter_options() -> FilterOptionsResponse:
    """Return controlled audience and category filter options per API_CONTRACTS.md §7.2."""
    return FilterOptionsResponse(
        audiences=AUDIENCE_OPTIONS,
        categories=CATEGORY_OPTIONS,
    )


def _normalize_category(category: Optional[str]) -> Optional[str]:
    if not category:
        return None
    cleaned = category.strip().lower()
    if not cleaned:
        return None
    return CATEGORY_ALIASES.get(cleaned, cleaned)


def _matches_audience(notice: Dict[str, Any], audience_filter: Optional[str]) -> bool:
    """Apply audience matching rules from API_CONTRACTS.md §5.1 and PRD §7.5."""
    notice_audience = (notice.get("audience") or "unspecified").lower()
    if not audience_filter or audience_filter == "all":
        return True
    if audience_filter in ("student", "faculty", "staff"):
        return notice_audience in (audience_filter, "all")
    if audience_filter == "unspecified":
        return notice_audience == "unspecified"
    return False


def _parse_iso_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def _build_important_dates(notice: Dict[str, Any]) -> List[PublicImportantDate]:
    deadline_str = notice.get("deadline_date")
    if not deadline_str:
        return []
    if isinstance(deadline_str, date):
        deadline_str = deadline_str.isoformat()
    return [
        PublicImportantDate(
            kind="deadline",
            label="Deadline",
            starts_on=str(deadline_str),
        )
    ]


def _to_public_list_item(notice: Dict[str, Any]) -> PublicNoticeListItem:
    audience = notice.get("audience") or "unspecified"
    published_at = notice.get("published_at") or notice.get("updated_at") or notice.get("created_at")
    return PublicNoticeListItem(
        id=str(notice["id"]),
        title=notice.get("title"),
        reference_number=notice.get("reference_number"),
        category=notice.get("category"),
        summary=notice.get("summary"),
        audiences=[audience],
        important_dates=_build_important_dates(notice),
        relationship_status=notice.get("relationship_status") or "current",
        published_at=published_at,
    )


def _sort_timestamp(notice: Dict[str, Any]) -> str:
    return str(notice.get("published_at") or notice.get("updated_at") or notice.get("created_at") or "")


async def list_public_notices(
    svc: SupabaseService,
    *,
    audience: Optional[str] = None,
    category: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> PublicNoticeListResponse:
    """Return paginated published notices strictly filtered by publication_status='published'."""
    rows = await svc.list_published_notices()
    published_only = [r for r in rows if r.get("publication_status") == "published"]

    norm_category = _normalize_category(category)
    query_text = q.strip().lower() if q else None

    filtered: List[Dict[str, Any]] = []
    for row in published_only:
        if not _matches_audience(row, audience):
            continue
        if norm_category and (row.get("category") or "").lower() != norm_category:
            continue
        row_notice_date = _parse_iso_date(row.get("notice_date"))
        if from_date and (row_notice_date is None or row_notice_date < from_date):
            continue
        if to_date and (row_notice_date is None or row_notice_date > to_date):
            continue
        if query_text:
            haystack = f"{row.get('title') or ''} {row.get('summary') or ''}".lower()
            if query_text not in haystack:
                continue
        filtered.append(row)

    if sort == "deadline_asc":
        filtered.sort(
            key=lambda r: (
                r.get("deadline_date") is None,
                str(r.get("deadline_date") or ""),
            )
        )
    elif sort == "notice_date_desc":
        filtered.sort(key=lambda r: str(r.get("notice_date") or ""), reverse=True)
    else:
        filtered.sort(key=_sort_timestamp, reverse=True)

    total = len(filtered)
    page_rows = filtered[offset : offset + limit]
    items = [_to_public_list_item(row) for row in page_rows]

    return PublicNoticeListResponse(
        items=items,
        pagination=PaginationMeta(
            limit=limit,
            offset=offset,
            total=total,
            has_more=(offset + len(items)) < total,
        ),
    )


async def get_public_briefing(
    svc: SupabaseService,
    *,
    audience: Optional[str] = None,
    limit: int = 5,
    today: Optional[date] = None,
) -> BriefingResponse:
    """Build home briefing from stored published notice data without calling Gemini."""
    now_ist = datetime.now(IST_TIMEZONE)
    current_date = today or now_ist.date()
    week_end = current_date + timedelta(days=7)

    all_published = [
        r for r in await svc.list_published_notices() if r.get("publication_status") == "published"
    ]
    published_by_id = {str(r["id"]): r for r in all_published}
    audience_filtered = [r for r in all_published if _matches_audience(r, audience)]

    # Top upcoming deadlines (excluding superseded / cancelled)
    upcoming_candidates: List[tuple[date, Dict[str, Any]]] = []
    for row in audience_filtered:
        rel_status = row.get("relationship_status") or "current"
        if rel_status in ("superseded", "cancelled"):
            continue
        dl_date = _parse_iso_date(row.get("deadline_date"))
        if dl_date is not None and dl_date >= current_date:
            upcoming_candidates.append((dl_date, row))

    upcoming_candidates.sort(key=lambda pair: pair[0])

    def _to_briefing_date_item(row: Dict[str, Any], dl: date) -> BriefingDateItem:
        return BriefingDateItem(
            notice_id=str(row["id"]),
            title=row.get("title"),
            kind="deadline",
            label="Deadline",
            starts_on=dl.isoformat(),
            relationship_status=row.get("relationship_status") or "current",
        )

    upcoming_deadlines = [
        _to_briefing_date_item(row, dl) for dl, row in upcoming_candidates[:limit]
    ]
    this_week = [
        _to_briefing_date_item(row, dl)
        for dl, row in upcoming_candidates
        if dl <= week_end
    ][:limit]
    coming_up = [
        _to_briefing_date_item(row, dl)
        for dl, row in upcoming_candidates
        if dl > week_end
    ][:limit]

    newest_sorted = sorted(audience_filtered, key=_sort_timestamp, reverse=True)[:limit]
    recently_posted = [_to_public_list_item(row) for row in newest_sorted]

    # Confirmed relationships where the later notice is published and matches audience
    confirmed_rels = await svc.list_confirmed_relationships()
    recent_changes: List[BriefingRecentChangeItem] = []
    for rel in confirmed_rels:
        later_id = str(rel["later_id"])
        earlier_id = str(rel["earlier_id"])
        later_notice = published_by_id.get(later_id)
        if not later_notice or not _matches_audience(later_notice, audience):
            continue
        earlier_notice = published_by_id.get(earlier_id)
        related_ref = (
            BriefingRelatedNoticeRef(
                notice_id=earlier_id,
                title=earlier_notice.get("title"),
            )
            if earlier_notice
            else None
        )
        recent_changes.append(
            BriefingRecentChangeItem(
                notice_id=later_id,
                title=later_notice.get("title"),
                relation=rel["relation"],
                related_notice=related_ref,
                published_at=_sort_timestamp(later_notice) or None,
            )
        )
        if len(recent_changes) >= limit:
            break

    return BriefingResponse(
        generated_at=now_ist.astimezone(timezone.utc).isoformat(),
        audience=audience or "all",
        sections=BriefingSections(
            this_week=this_week,
            coming_up=coming_up,
            recently_posted=recently_posted,
            action_items=[],
            recent_changes=recent_changes,
        ),
        upcoming_deadlines=upcoming_deadlines,
        newest_notices=recently_posted,
    )


async def get_public_notice_detail(
    svc: SupabaseService, notice_id: str
) -> PublicNoticeDetailResponse:
    """Return published notice detail with a 15-minute signed download URL, or 404."""
    notice = await svc.get_notice(notice_id)
    if notice is None or notice.get("publication_status") != "published":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found.",
        )

    storage_path = notice.get("storage_path") or ""
    signed_url = await svc.create_signed_url(
        "notice-originals",
        storage_path,
        expires_in=SIGNED_URL_EXPIRY_SECONDS,
    )

    field_sources = await svc.get_field_sources(notice_id)
    field_labels: Dict[str, str] = {}
    for src in field_sources:
        fname = src.get("field_name")
        if fname:
            field_labels[fname] = (
                "human_corrected" if src.get("human_edited") else "ai_extracted"
            )

    rels = await svc.get_notice_relationships(notice_id)
    related_notices: List[PublicRelatedNotice] = []
    for rel in rels:
        if not rel.get("confirmed"):
            continue
        earlier_id = str(rel["earlier_id"])
        later_id = str(rel["later_id"])
        if earlier_id == notice_id:
            other_id = later_id
            direction = "later"
        else:
            other_id = earlier_id
            direction = "earlier"

        other_notice = await svc.get_notice(other_id)
        if other_notice and other_notice.get("publication_status") == "published":
            related_notices.append(
                PublicRelatedNotice(
                    notice_id=other_id,
                    title=other_notice.get("title"),
                    relation=rel["relation"],
                    direction=direction,
                )
            )

    audience = notice.get("audience") or "unspecified"
    issue_date = notice.get("notice_date")
    if isinstance(issue_date, date):
        issue_date = issue_date.isoformat()

    detail = PublicNoticeDetail(
        id=str(notice["id"]),
        title=notice.get("title"),
        reference_number=notice.get("reference_number"),
        category=notice.get("category"),
        summary=notice.get("summary"),
        issuing_authority=notice.get("issuing_authority"),
        issue_date=issue_date,
        audiences=[audience],
        audience_targets=[PublicAudienceTarget(role=audience)],
        important_dates=_build_important_dates(notice),
        action_items=[],
        relationship_status=notice.get("relationship_status") or "current",
        related_notices=related_notices,
        field_labels=field_labels,  # type: ignore[arg-type]
        source_file=PublicSourceFile(
            available=bool(storage_path),
            download_url=signed_url,
        ),
        published_at=notice.get("published_at") or notice.get("created_at"),
        updated_at=notice.get("updated_at"),
    )
    return PublicNoticeDetailResponse(notice=detail)


class SlidingWindowRateLimiter:
    """In-memory per-IP sliding-window rate limiter for public report submissions."""

    def __init__(self) -> None:
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)

    def reset(self) -> None:
        self._requests.clear()

    def check_and_record(
        self,
        client_ip: str,
        *,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> None:
        limit = (
            max_requests
            if max_requests is not None
            else settings.REPORT_RATE_LIMIT_MAX_REQUESTS
        )
        window = (
            window_seconds
            if window_seconds is not None
            else settings.REPORT_RATE_LIMIT_WINDOW_SECONDS
        )
        now = time.monotonic()
        cutoff = now - window
        timestamps = self._requests[client_ip]
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many error reports submitted. Please try again later.",
            )
        timestamps.append(now)


report_rate_limiter = SlidingWindowRateLimiter()


async def submit_public_error_report(
    svc: SupabaseService,
    notice_id: str,
    payload: ErrorReportCreateRequest,
    *,
    client_ip: str,
) -> ErrorReportCreateResponse:
    """Rate-limit and submit a public error report for a published notice."""
    report_rate_limiter.check_and_record(client_ip)

    notice = await svc.get_notice(notice_id)
    if notice is None or notice.get("publication_status") != "published":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found.",
        )

    created = await svc.insert_error_report(
        {
            "notice_id": notice_id,
            "issue_type": payload.issue_type,
            "description": payload.description,
            "status": "open",
        }
    )
    return ErrorReportCreateResponse(
        report_id=str(created["id"]),
        status="received",
    )
