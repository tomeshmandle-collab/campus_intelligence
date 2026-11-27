from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.schemas.notices import (
    BriefingResponse,
    ErrorReportCreateRequest,
    ErrorReportCreateResponse,
    FilterOptionsResponse,
    PublicNoticeDetailResponse,
    PublicNoticeListResponse,
)
from app.services.public_notices_service import (
    get_filter_options,
    get_public_briefing,
    get_public_notice_detail,
    list_public_notices,
    submit_public_error_report,
)
from app.services.supabase import SupabaseService, get_supabase_service

router = APIRouter()

AudienceFilterParam = Literal["student", "faculty", "staff", "all", "unspecified"]
SortOptionParam = Literal["newest", "deadline_asc", "notice_date_desc"]


@router.get(
    "/filters",
    response_model=FilterOptionsResponse,
    summary="List audience and category filter options",
    description="Return controlled audience and category filter options per API_CONTRACTS.md §7.2.",
)
async def get_filters_endpoint() -> FilterOptionsResponse:
    """Public filter vocabulary endpoint."""
    return get_filter_options()


@router.get(
    "/notices",
    response_model=PublicNoticeListResponse,
    summary="List published public notices",
    description="Paginated list of published notices supporting audience and category filters per API_CONTRACTS.md §7.4.",
)
async def list_notices_endpoint(
    audience: Optional[AudienceFilterParam] = Query(default=None),
    category: Optional[str] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=200),
    sort: Optional[SortOptionParam] = Query(default="newest"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    page: Optional[int] = Query(default=None, ge=1),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> PublicNoticeListResponse:
    """Return published notices only; held and withdrawn notices are strictly excluded."""
    resolved_offset = offset if offset is not None else ((page - 1) * limit if page is not None else 0)
    return await list_public_notices(
        supabase_service,
        audience=audience,
        category=category,
        from_date=from_date,
        to_date=to_date,
        q=q,
        sort=sort,
        limit=limit,
        offset=resolved_offset,
    )


@router.get(
    "/notices/briefing",
    response_model=BriefingResponse,
    summary="Home briefing of upcoming deadlines and newest published notices",
    description="Return top upcoming deadlines and newest published notices from stored data per API_CONTRACTS.md §7.3.",
)
@router.get(
    "/briefing",
    response_model=BriefingResponse,
    include_in_schema=False,
)
async def get_briefing_endpoint(
    audience: Optional[AudienceFilterParam] = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> BriefingResponse:
    """Public home briefing derived from published notices only."""
    return await get_public_briefing(
        supabase_service,
        audience=audience,
        limit=limit,
    )


@router.get(
    "/notices/{notice_id}",
    response_model=PublicNoticeDetailResponse,
    summary="Get published notice detail",
    description="Return published notice details, structured summary, and 15-minute signed download URL per API_CONTRACTS.md §7.5. Returns 404 if held or withdrawn.",
)
async def get_notice_detail_endpoint(
    notice_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> PublicNoticeDetailResponse:
    """Return published notice detail; return 404 for held, withdrawn, or missing notices."""
    return await get_public_notice_detail(supabase_service, notice_id)


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first_ip = forwarded.split(",", 1)[0].strip()
        if first_ip:
            return first_ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.post(
    "/notices/{notice_id}/reports",
    status_code=status.HTTP_201_CREATED,
    response_model=ErrorReportCreateResponse,
    summary="Submit public error report",
    description="Submit an error report for a publicly visible notice with IP rate limiting per API_CONTRACTS.md §7.8.",
)
async def submit_error_report_endpoint(
    notice_id: str,
    payload: ErrorReportCreateRequest,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ErrorReportCreateResponse:
    """Submit a public error report without modifying the underlying notice."""
    client_ip = _extract_client_ip(request)
    return await submit_public_error_report(
        supabase_service,
        notice_id,
        payload,
        client_ip=client_ip,
    )
