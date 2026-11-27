from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.uploader import PaginationMeta


class FilterOption(BaseModel):
    """Controlled filter option item per API_CONTRACTS.md §7.2."""

    id: str
    label: str


class FilterOptionsResponse(BaseModel):
    """Response for GET /api/v1/filters."""

    audiences: List[FilterOption]
    categories: List[FilterOption]


class PublicImportantDate(BaseModel):
    """Important event or deadline date per API_CONTRACTS.md §5.6."""

    kind: Literal["event", "deadline"]
    label: str
    starts_on: str
    ends_on: Optional[str] = None
    starts_time: Optional[str] = None
    source_page: Optional[int] = None


class PublicAudienceTarget(BaseModel):
    """Audience target detail per API_CONTRACTS.md §5.4."""

    role: str
    department: Optional[str] = None
    year: Optional[str] = None
    detail: Optional[str] = None


class PublicRelatedNotice(BaseModel):
    """Confirmed publicly visible related notice per API_CONTRACTS.md §5.6."""

    notice_id: str
    title: Optional[str] = None
    relation: str
    direction: Literal["earlier", "later"]


class PublicSourceFile(BaseModel):
    """Controlled public download link without raw storage_path per API_CONTRACTS.md §5.4."""

    available: bool
    download_url: Optional[str] = None


class PublicNoticeListItem(BaseModel):
    """Public notice card item per API_CONTRACTS.md §5.3."""

    id: str
    title: Optional[str] = None
    reference_number: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    audiences: List[str] = Field(default_factory=list)
    important_dates: List[PublicImportantDate] = Field(default_factory=list)
    relationship_status: str = "current"
    published_at: Optional[str] = None


class PublicNoticeListResponse(BaseModel):
    """Paginated response for GET /api/v1/notices."""

    items: List[PublicNoticeListItem]
    pagination: PaginationMeta


class PublicNoticeDetail(BaseModel):
    """Public notice detail payload per API_CONTRACTS.md §5.4."""

    id: str
    title: Optional[str] = None
    reference_number: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[str] = None
    audiences: List[str] = Field(default_factory=list)
    audience_targets: List[PublicAudienceTarget] = Field(default_factory=list)
    important_dates: List[PublicImportantDate] = Field(default_factory=list)
    action_items: List[Dict] = Field(default_factory=list)
    relationship_status: str = "current"
    related_notices: List[PublicRelatedNotice] = Field(default_factory=list)
    field_labels: Dict[str, Literal["ai_extracted", "human_corrected"]] = Field(
        default_factory=dict
    )
    source_file: PublicSourceFile
    published_at: Optional[str] = None
    updated_at: Optional[str] = None


class PublicNoticeDetailResponse(BaseModel):
    """Envelope for GET /api/v1/notices/{notice_id} per API_CONTRACTS.md §5.4."""

    notice: PublicNoticeDetail


class BriefingDateItem(BaseModel):
    """Upcoming event/deadline item in briefing sections per API_CONTRACTS.md §7.3."""

    notice_id: str
    title: Optional[str] = None
    kind: Literal["event", "deadline"]
    label: str
    starts_on: str
    ends_on: Optional[str] = None
    starts_time: Optional[str] = None
    source_page: Optional[int] = None
    relationship_status: str = "current"


class BriefingRelatedNoticeRef(BaseModel):
    """Minimal reference to an earlier published notice in recent_changes."""

    notice_id: str
    title: Optional[str] = None


class BriefingRecentChangeItem(BaseModel):
    """Confirmed relationship change item per API_CONTRACTS.md §7.3."""

    notice_id: str
    title: Optional[str] = None
    relation: str
    related_notice: Optional[BriefingRelatedNoticeRef] = None
    published_at: Optional[str] = None


class BriefingSections(BaseModel):
    """Sections defined by API_CONTRACTS.md §7.3."""

    this_week: List[BriefingDateItem] = Field(default_factory=list)
    coming_up: List[BriefingDateItem] = Field(default_factory=list)
    recently_posted: List[PublicNoticeListItem] = Field(default_factory=list)
    action_items: List[Dict] = Field(default_factory=list)
    recent_changes: List[BriefingRecentChangeItem] = Field(default_factory=list)


class BriefingResponse(BaseModel):
    """Response for GET /api/v1/notices/briefing and GET /api/v1/briefing."""

    generated_at: str
    audience: str
    sections: BriefingSections
    upcoming_deadlines: List[BriefingDateItem] = Field(default_factory=list)
    newest_notices: List[PublicNoticeListItem] = Field(default_factory=list)
