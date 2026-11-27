from datetime import date
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

AudienceRole = Literal["student", "faculty", "staff", "all", "unspecified"]
NoticeCategory = Literal[
    "academic",
    "examination",
    "admissions",
    "events_workshops",
    "faculty",
    "administration",
    "general",
    "other",
]
ProcessingStatus = Literal["pending", "processing", "completed", "failed"]
PublicationStatus = Literal["held", "published", "withdrawn"]
RelationshipStatus = Literal["current", "superseded", "amended", "extended", "cancelled"]


class UploadResponse(BaseModel):
    """Schema for successful notice upload response."""

    notice_id: str = Field(description="Unique identifier for the created notice record")
    status: str = Field(default="pending", description="Initial processing status")


class PaginationMeta(BaseModel):
    """Standard pagination metadata per API_CONTRACTS.md §3.5."""

    limit: int
    offset: int
    total: int
    has_more: bool


class ReviewQueueItem(BaseModel):
    """Single held/failed notice entry in the uploader review queue."""

    notice_id: str
    title: Optional[str] = None
    processing_status: str
    publication_status: str
    hold_reason: Optional[str] = None
    review_reasons: List[str] = Field(default_factory=list)
    updated_at: Optional[str] = None


class ReviewQueueResponse(BaseModel):
    """Paginated response for GET /api/v1/uploader/review-queue."""

    items: List[ReviewQueueItem]
    pagination: PaginationMeta


class NoticePageItem(BaseModel):
    """Extracted page text entry for uploader review detail."""

    page_number: int
    extracted_text: str = ""
    is_scanned: bool = False


class FieldSourceItem(BaseModel):
    """Provenance record for an extracted or human-corrected field."""

    field_name: str
    value_text: Optional[str] = None
    source_page: Optional[int] = None
    source_quote: Optional[str] = None
    extraction_method: str = "ai"
    verified: bool = False
    human_edited: bool = False


class RelationItem(BaseModel):
    """Detected relationship candidate or confirmed relationship."""

    relation_id: int
    relation: str
    earlier_notice_id: str
    later_notice_id: str
    evidence_page: Optional[int] = None
    evidence_text: Optional[str] = None
    confirmed: bool = False


class ValidationIssue(BaseModel):
    """Structured validation issue for review display."""

    field: str
    message: str
    source_page: Optional[int] = None


class ValidationSummary(BaseModel):
    """Validation issues and raw review reason codes."""

    issues: List[ValidationIssue] = Field(default_factory=list)
    review_reasons: List[str] = Field(default_factory=list)


class SourceFilePreview(BaseModel):
    """Controlled preview metadata (never exposes private storage_path)."""

    filename: str
    page_count: int
    preview_url: Optional[str] = None


class ReviewNoticeSummary(BaseModel):
    """Notice detail fields shown in uploader review detail."""

    id: str
    title: Optional[str] = None
    notice_date: Optional[str] = None
    deadline_date: Optional[str] = None
    audience: str = "unspecified"
    audiences: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    summary: Optional[str] = None
    processing_status: str
    publication_status: str
    relationship_status: str = "current"
    review_reasons: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReviewDetailResponse(BaseModel):
    """Full review payload per API_CONTRACTS.md §8.4 plus page text and evidence."""

    notice: ReviewNoticeSummary
    validation: ValidationSummary
    source: SourceFilePreview
    pages: List[NoticePageItem] = Field(default_factory=list)
    field_sources: List[FieldSourceItem] = Field(default_factory=list)
    field_evidence: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    relations: List[RelationItem] = Field(default_factory=list)
    processing_history: List[Dict[str, Any]] = Field(default_factory=list)
    edit_history: List[Dict[str, Any]] = Field(default_factory=list)


class NoticeFieldsPatchRequest(BaseModel):
    """Editable notice fields accepted by PATCH /notices/{id}/fields & /uploader/notices/{id}."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    notice_date: Optional[date] = None
    deadline_date: Optional[date] = None
    audience: Optional[AudienceRole] = None
    category: Optional[NoticeCategory] = None
    summary: Optional[str] = None
    correction_note: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("title", "summary", "correction_note", mode="before")
    @classmethod
    def strip_text_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class NoticeEditAuditItem(BaseModel):
    """Audit log entry returned after field corrections."""

    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    edited_by: str
    note: Optional[str] = None
    edited_at: str


class NoticeFieldsPatchResponse(BaseModel):
    """Response returned after correcting notice fields."""

    notice: ReviewNoticeSummary
    edits_recorded: List[NoticeEditAuditItem] = Field(default_factory=list)
    review_reasons: List[str] = Field(default_factory=list)


class PublishNoticeRequest(BaseModel):
    """Explicit confirmation payload per API_CONTRACTS.md §8.6."""

    confirmation: bool


class PublishNoticeResponse(BaseModel):
    """Response returned after publishing a reviewed notice."""

    notice_id: str
    publication_status: PublicationStatus
    published_at: str


class RetryNoticeRequest(BaseModel):
    """Explicit confirmation payload per API_CONTRACTS.md §8.7."""

    confirmation: bool


class RetryNoticeResponse(BaseModel):
    """Response returned after retrying processing."""

    notice_id: str
    processing_status: ProcessingStatus


class RelationshipActionRequest(BaseModel):
    """Confirm or reject payload per API_CONTRACTS.md §8.12."""

    action: Literal["confirm", "reject"] = "confirm"


class RelationshipActionResponse(BaseModel):
    """Outcome of confirming or rejecting a detected relationship."""

    relation_id: int
    outcome: Literal["confirmed", "rejected"]
    earlier_notice_id: Optional[str] = None
    earlier_relationship_status: Optional[str] = None


class ManagementNoticeItem(BaseModel):
    """Staff management list entry per API_CONTRACTS.md §8.10."""

    notice_id: str
    title: Optional[str] = None
    processing_status: str
    publication_status: str
    relationship_status: str = "current"
    uploaded_at: Optional[str] = None
    published_at: Optional[str] = None


class ManagementNoticeListResponse(BaseModel):
    """Paginated response for GET /api/v1/uploader/notices."""

    items: List[ManagementNoticeItem]
    pagination: PaginationMeta


class WithdrawNoticeRequest(BaseModel):
    """Withdrawal payload per API_CONTRACTS.md §8.8."""

    reason: str = Field(..., min_length=3, max_length=1000)

    @field_validator("reason", mode="before")
    @classmethod
    def strip_reason(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class WithdrawNoticeResponse(BaseModel):
    """Response for POST /api/v1/uploader/notices/{notice_id}/withdraw."""

    notice_id: str
    publication_status: PublicationStatus
    withdrawn_at: str


ReportStatus = Literal["open", "resolved", "dismissed"]


class ErrorReportItem(BaseModel):
    """Uploader-facing error report record per API_CONTRACTS.md §8.11."""

    report_id: str
    notice_id: str
    notice_title: Optional[str] = None
    issue_type: str
    description: Optional[str] = None
    status: ReportStatus
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_note: Optional[str] = None


class ErrorReportListResponse(BaseModel):
    """Paginated response for GET /api/v1/uploader/reports."""

    items: List[ErrorReportItem]
    pagination: PaginationMeta


class ResolveErrorReportRequest(BaseModel):
    """Resolution/dismissal payload per API_CONTRACTS.md §8.9."""

    status: Literal["resolved", "dismissed"]
    resolution_note: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("resolution_note", mode="before")
    @classmethod
    def strip_note(cls, value: Any) -> Any:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class ResolveErrorReportResponse(BaseModel):
    """Response for PATCH /api/v1/uploader/reports/{report_id}."""

    report_id: str
    status: Literal["resolved", "dismissed"]
    resolved_at: str
