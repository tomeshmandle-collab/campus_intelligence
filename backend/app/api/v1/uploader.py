from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status

from app.core.auth import require_uploader
from app.core.config import settings
from app.schemas.uploader import (
    ErrorReportListResponse,
    ManagementNoticeListResponse,
    NoticeFieldsPatchRequest,
    NoticeFieldsPatchResponse,
    ProcessingStatus,
    PublicationStatus,
    PublishNoticeRequest,
    PublishNoticeResponse,
    RelationshipActionRequest,
    RelationshipActionResponse,
    ReportStatus,
    ResolveErrorReportRequest,
    ResolveErrorReportResponse,
    RetryNoticeRequest,
    RetryNoticeResponse,
    ReviewDetailResponse,
    ReviewQueueResponse,
    UploadResponse,
    WithdrawNoticeRequest,
    WithdrawNoticeResponse,
)
from app.services.review_service import (
    get_review_detail,
    get_review_queue,
    handle_relationship_action,
    list_management_notices,
    list_uploader_reports,
    patch_notice_fields,
    publish_reviewed_notice,
    resolve_or_dismiss_report,
    retry_notice_processing,
    withdraw_notice,
)
from app.services.supabase import SupabaseService, get_supabase_service

router = APIRouter()

PDF_MAGIC_BYTES = b"%PDF-"


@router.post(
    "/notices/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=UploadResponse,
    summary="Upload official notice PDF",
    description="Accept a notice PDF, validate magic bytes and size, store in Supabase Storage, and create a pending notice record.",
)
@router.post(
    "/uploader/notices",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=UploadResponse,
    include_in_schema=False,
)
async def upload_notice(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> UploadResponse:
    """Handle authenticated notice upload per API_CONTRACTS.md §8.1 and MODULES.md M04."""
    # 1. Read initial 5 bytes to verify PDF magic bytes
    header = await file.read(5)
    if len(header) < 5 or header != PDF_MAGIC_BYTES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid file format. Uploaded file must be a valid PDF starting with '%PDF-'.",
        )

    # 2. Read remaining content and check size bounds
    rest = await file.read()
    content = header + rest
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        http_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
        raise HTTPException(
            status_code=http_413,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES} bytes (10MB).",
        )

    # 3. Generate UUID storage path: originals/{uuid}.pdf
    notice_id = str(uuid.uuid4())
    storage_path = f"originals/{notice_id}.pdf"

    # 4. Upload to Supabase Storage private bucket 'notice-originals'
    await supabase_service.upload_file(
        bucket="notice-originals",
        path=storage_path,
        content=content,
        content_type="application/pdf",
    )

    # 5. Insert row into 'notices' table with status 'pending', 'held'
    now_iso = datetime.now(timezone.utc).isoformat()
    notice_record = {
        "id": notice_id,
        "title": file.filename or f"Notice {notice_id[:8]}",
        "storage_path": storage_path,
        "processing_status": "pending",
        "publication_status": "held",
        "relationship_status": "current",
        "audience": "unspecified",
        "review_reasons": [],
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await supabase_service.insert_notice(notice_record)

    # 6. Return 202 Accepted with notice_id and status: pending
    return UploadResponse(
        notice_id=notice_id,
        status="pending",
    )


@router.get(
    "/uploader/review-queue",
    response_model=ReviewQueueResponse,
    summary="List held or failed notices for review",
    description="Return paginated held and failed notices with review reasons per API_CONTRACTS.md §8.3.",
)
@router.get(
    "/review-queue",
    response_model=ReviewQueueResponse,
    include_in_schema=False,
)
async def list_review_queue_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ReviewQueueResponse:
    """List notices awaiting human review."""
    return await get_review_queue(supabase_service, limit=limit, offset=offset)


@router.get(
    "/uploader/notices/{notice_id}",
    response_model=ReviewDetailResponse,
    summary="Get notice review detail",
    description="Return notice metadata, extracted field evidence, extracted page text, and relationships per API_CONTRACTS.md §8.4.",
)
@router.get(
    "/notices/{notice_id}/review",
    response_model=ReviewDetailResponse,
    include_in_schema=False,
)
async def get_notice_review_endpoint(
    notice_id: str,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ReviewDetailResponse:
    """Return full review context for an authorized uploader."""
    return await get_review_detail(supabase_service, notice_id)


@router.patch(
    "/uploader/notices/{notice_id}",
    response_model=NoticeFieldsPatchResponse,
    summary="Correct notice fields with audit logging",
    description="Update supported notice fields, log old/new values to notice_edits, and re-run blocking checks per API_CONTRACTS.md §8.5.",
)
@router.patch(
    "/notices/{notice_id}/fields",
    response_model=NoticeFieldsPatchResponse,
    include_in_schema=False,
)
async def patch_notice_fields_endpoint(
    notice_id: str,
    payload: NoticeFieldsPatchRequest,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> NoticeFieldsPatchResponse:
    """Update editable fields and persist an audit trail without auto-publishing."""
    return await patch_notice_fields(
        supabase_service,
        notice_id,
        payload,
        editor_id=str(current_user["id"]),
    )


@router.post(
    "/uploader/notices/{notice_id}/publish",
    response_model=PublishNoticeResponse,
    summary="Publish a reviewed notice",
    description="Validate all blocking review reasons are cleared and set publication_status='published' per API_CONTRACTS.md §8.6.",
)
async def publish_notice_contract_endpoint(
    notice_id: str,
    payload: PublishNoticeRequest,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> PublishNoticeResponse:
    """Publish a reviewed notice requiring explicit confirmation."""
    return await publish_reviewed_notice(
        supabase_service,
        notice_id,
        actor_id=str(current_user["id"]),
        confirmation=payload.confirmation,
    )


@router.post(
    "/notices/{notice_id}/publish",
    response_model=PublishNoticeResponse,
    include_in_schema=False,
)
async def publish_notice_alias_endpoint(
    notice_id: str,
    payload: Optional[PublishNoticeRequest] = Body(default=None),
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> PublishNoticeResponse:
    """Alias route for publishing a reviewed notice."""
    confirmed = True if payload is None else payload.confirmation
    return await publish_reviewed_notice(
        supabase_service,
        notice_id,
        actor_id=str(current_user["id"]),
        confirmation=confirmed,
    )


@router.post(
    "/uploader/notices/{notice_id}/retry",
    response_model=RetryNoticeResponse,
    summary="Retry processing for a held or failed notice",
    description="Re-queue an eligible failed or held notice for processing per API_CONTRACTS.md §8.7.",
)
@router.post(
    "/notices/{notice_id}/retry",
    response_model=RetryNoticeResponse,
    include_in_schema=False,
)
async def retry_notice_endpoint(
    notice_id: str,
    payload: RetryNoticeRequest,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> RetryNoticeResponse:
    """Retry processing for an eligible notice."""
    return await retry_notice_processing(
        supabase_service,
        notice_id,
        actor_id=str(current_user["id"]),
        confirmation=payload.confirmation,
    )


@router.patch(
    "/uploader/relations/{relation_id}",
    response_model=RelationshipActionResponse,
    summary="Confirm or reject a detected relationship",
    description="Confirm or reject a notice relationship per API_CONTRACTS.md §8.12 without altering unapproved notices.",
)
async def relation_action_endpoint(
    relation_id: int,
    payload: RelationshipActionRequest,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> RelationshipActionResponse:
    """Confirm or reject a relationship via §8.12 route."""
    return await handle_relationship_action(
        supabase_service,
        relation_id,
        action=payload.action,
        actor_id=str(current_user["id"]),
    )


@router.post(
    "/notices/{notice_id}/relationships/{rel_id}/confirm",
    response_model=RelationshipActionResponse,
    include_in_schema=False,
)
async def confirm_notice_relationship_alias_endpoint(
    notice_id: str,
    rel_id: int,
    payload: Optional[RelationshipActionRequest] = Body(default=None),
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> RelationshipActionResponse:
    """Alias route to confirm a notice relationship without modifying unapproved notices."""
    action = "confirm" if payload is None else payload.action
    return await handle_relationship_action(
        supabase_service,
        rel_id,
        action=action,
        actor_id=str(current_user["id"]),
        expected_notice_id=notice_id,
    )


@router.get(
    "/uploader/notices",
    response_model=ManagementNoticeListResponse,
    summary="List all notices for staff management",
    description="Return paginated notices across all publication and processing statuses per API_CONTRACTS.md §8.10.",
)
async def list_management_notices_endpoint(
    publication_status: Optional[PublicationStatus] = Query(default=None),
    processing_status: Optional[ProcessingStatus] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ManagementNoticeListResponse:
    """Staff notice management list regardless of publication status."""
    return await list_management_notices(
        supabase_service,
        publication_status=publication_status,
        processing_status=processing_status,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/uploader/notices/{notice_id}/withdraw",
    response_model=WithdrawNoticeResponse,
    summary="Withdraw a notice",
    description="Set publication_status='withdrawn' and record withdrawal_reason per API_CONTRACTS.md §8.8.",
)
async def withdraw_notice_endpoint(
    notice_id: str,
    payload: WithdrawNoticeRequest,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> WithdrawNoticeResponse:
    """Withdraw a notice from public visibility while preserving audit history."""
    return await withdraw_notice(
        supabase_service,
        notice_id,
        actor_id=str(current_user["id"]),
        reason=payload.reason,
    )


@router.get(
    "/uploader/reports",
    response_model=ErrorReportListResponse,
    summary="List public error reports",
    description="Return paginated public error reports filtered by status per API_CONTRACTS.md §8.11.",
)
async def list_uploader_reports_endpoint(
    status_filter: Optional[ReportStatus] = Query(default="open", alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ErrorReportListResponse:
    """List error reports for authorized uploader review."""
    return await list_uploader_reports(
        supabase_service,
        report_status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/uploader/reports/{report_id}",
    response_model=ResolveErrorReportResponse,
    summary="Resolve or dismiss an error report",
    description="Mark an open error report as resolved or dismissed with optional note per API_CONTRACTS.md §8.9.",
)
async def resolve_report_endpoint(
    report_id: int,
    payload: ResolveErrorReportRequest,
    current_user: Dict[str, Any] = Depends(require_uploader),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ResolveErrorReportResponse:
    """Resolve or dismiss an error report without altering the notice itself."""
    return await resolve_or_dismiss_report(
        supabase_service,
        report_id,
        new_status=payload.status,
        actor_id=str(current_user["id"]),
        resolution_note=payload.resolution_note,
    )
