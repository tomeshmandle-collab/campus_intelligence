import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.auth import require_uploader
from app.core.config import settings
from app.schemas.uploader import UploadResponse
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
    notice_record = {
        "id": notice_id,
        "title": file.filename or f"Notice {notice_id[:8]}",
        "storage_path": storage_path,
        "processing_status": "pending",
        "publication_status": "held",
        "audience": "unspecified",
        "review_reasons": [],
    }
    await supabase_service.insert_notice(notice_record)

    # 6. Return 202 Accepted with notice_id and status: pending
    return UploadResponse(
        notice_id=notice_id,
        status="pending",
    )
