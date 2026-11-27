from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.schemas.uploader import (
    FieldSourceItem,
    NoticeEditAuditItem,
    NoticeFieldsPatchRequest,
    NoticeFieldsPatchResponse,
    NoticePageItem,
    PaginationMeta,
    PublishNoticeResponse,
    RelationItem,
    RelationshipActionResponse,
    RetryNoticeResponse,
    ReviewDetailResponse,
    ReviewNoticeSummary,
    ReviewQueueItem,
    ReviewQueueResponse,
    SourceFilePreview,
    ValidationIssue,
    ValidationSummary,
)
from app.services.supabase import SupabaseService

REASON_MESSAGES: Dict[str, tuple[str, str]] = {
    "deadline_prior_to_notice_date": (
        "deadline_date",
        "Deadline date is earlier than the notice issue date.",
    ),
    "missing_notice_date": (
        "notice_date",
        "Notice issue date is missing and must be verified.",
    ),
    "unreliable_ocr": (
        "ocr",
        "OCR failed or produced unreliable text on one or more pages.",
    ),
    "ocr_uncertain_or_unreadable": (
        "ocr",
        "OCR failed or produced unreliable text on one or more pages.",
    ),
    "low_extraction_confidence": (
        "extraction",
        "AI extraction confidence is below the automatic publication threshold.",
    ),
    "missing_title": ("title", "Notice title is missing."),
    "missing_category": ("category", "Notice category is missing."),
    "missing_summary": ("summary", "Notice summary is missing."),
    "missing_field_evidence": (
        "field_evidence",
        "One or more critical fields lack supporting source evidence.",
    ),
    "invalid_evidence_page": (
        "field_evidence",
        "Extracted evidence references an invalid page number.",
    ),
    "unverified_field_evidence": (
        "field_evidence",
        "Extracted evidence quote could not be verified against page text.",
    ),
    "ai_extraction_failed": (
        "extraction",
        "Automated AI extraction failed and requires manual review or retry.",
    ),
    "empty_extracted_text": (
        "pages",
        "No extractable text was found in the uploaded document.",
    ),
}

RELATION_TO_STATUS: Dict[str, str] = {
    "amends": "amended",
    "replaces": "superseded",
    "extends": "extended",
    "cancels": "cancelled",
}

EDITABLE_FIELDS = (
    "title",
    "notice_date",
    "deadline_date",
    "audience",
    "category",
    "summary",
)


def _format_hold_reason(review_reasons: List[str]) -> Optional[str]:
    if not review_reasons:
        return None
    messages = [
        REASON_MESSAGES.get(reason, (reason, reason.replace("_", " ").capitalize()))[1]
        for reason in review_reasons
    ]
    return " ".join(messages)


def _parse_iso_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        return date.fromisoformat(value.strip()[:10])
    return None


def _compute_objective_blocking_reasons(notice: Dict[str, Any]) -> List[str]:
    """Evaluate objective field/date blocking checks against a notice record."""
    reasons: List[str] = []
    title = (notice.get("title") or "").strip() if isinstance(notice.get("title"), str) else ""
    if not title:
        reasons.append("missing_title")

    notice_date = _parse_iso_date(notice.get("notice_date"))
    deadline_date = _parse_iso_date(notice.get("deadline_date"))

    if notice_date is None:
        reasons.append("missing_notice_date")

    if notice_date is not None and deadline_date is not None and deadline_date < notice_date:
        reasons.append("deadline_prior_to_notice_date")

    if not notice.get("category"):
        reasons.append("missing_category")

    return reasons


def _to_notice_summary(notice: Dict[str, Any]) -> ReviewNoticeSummary:
    audience = notice.get("audience") or "unspecified"
    return ReviewNoticeSummary(
        id=str(notice["id"]),
        title=notice.get("title"),
        notice_date=(
            notice["notice_date"].isoformat()
            if isinstance(notice.get("notice_date"), date)
            else notice.get("notice_date")
        ),
        deadline_date=(
            notice["deadline_date"].isoformat()
            if isinstance(notice.get("deadline_date"), date)
            else notice.get("deadline_date")
        ),
        audience=audience,
        audiences=[audience],
        category=notice.get("category"),
        summary=notice.get("summary"),
        processing_status=notice.get("processing_status", "pending"),
        publication_status=notice.get("publication_status", "held"),
        relationship_status=notice.get("relationship_status", "current"),
        review_reasons=list(notice.get("review_reasons") or []),
        created_at=notice.get("created_at"),
        updated_at=notice.get("updated_at"),
    )


async def get_review_queue(
    svc: SupabaseService, *, limit: int, offset: int
) -> ReviewQueueResponse:
    """Fetch paginated held/failed notices for the uploader review queue."""
    rows, total = await svc.list_review_queue(limit=limit, offset=offset)
    items: List[ReviewQueueItem] = []
    for row in rows:
        reasons = list(row.get("review_reasons") or [])
        items.append(
            ReviewQueueItem(
                notice_id=str(row["id"]),
                title=row.get("title"),
                processing_status=row.get("processing_status", "pending"),
                publication_status=row.get("publication_status", "held"),
                hold_reason=_format_hold_reason(reasons),
                review_reasons=reasons,
                updated_at=row.get("updated_at") or row.get("created_at"),
            )
        )
    return ReviewQueueResponse(
        items=items,
        pagination=PaginationMeta(
            limit=limit,
            offset=offset,
            total=total,
            has_more=(offset + len(items)) < total,
        ),
    )


async def get_review_detail(svc: SupabaseService, notice_id: str) -> ReviewDetailResponse:
    """Assemble notice details, field evidence, extracted pages, relations, and audit history."""
    notice = await svc.get_notice(notice_id)
    if notice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found.",
        )

    pages_raw = await svc.get_notice_pages(notice_id)
    field_sources_raw = await svc.get_field_sources(notice_id)
    relations_raw = await svc.get_notice_relationships(notice_id)
    edits_raw = await svc.get_notice_edits(notice_id)
    events_raw = await svc.get_processing_events(notice_id)

    storage_path = notice.get("storage_path") or ""
    preview_url = await svc.create_signed_url(
        "notice-originals", storage_path, expires_in=900
    )
    filename = notice.get("original_filename") or (
        storage_path.rsplit("/", 1)[-1] if storage_path else f"{notice_id}.pdf"
    )

    pages = [
        NoticePageItem(
            page_number=int(p["page_number"]),
            extracted_text=p.get("extracted_text") or "",
            is_scanned=bool(p.get("is_scanned", False)),
        )
        for p in pages_raw
    ]

    field_sources: List[FieldSourceItem] = []
    field_evidence: Dict[str, Dict[str, Any]] = {}
    source_page_by_field: Dict[str, int] = {}

    for src in field_sources_raw:
        item = FieldSourceItem(
            field_name=src["field_name"],
            value_text=src.get("value_text"),
            source_page=src.get("source_page"),
            source_quote=src.get("source_quote"),
            extraction_method=src.get("extraction_method", "ai"),
            verified=bool(src.get("verified", False)),
            human_edited=bool(src.get("human_edited", False)),
        )
        field_sources.append(item)
        if item.source_page is not None:
            source_page_by_field[item.field_name] = item.source_page
        field_evidence[item.field_name] = {
            "page_number": item.source_page,
            "quote": item.source_quote,
            "value_text": item.value_text,
            "extraction_method": item.extraction_method,
            "verified": item.verified,
            "human_edited": item.human_edited,
        }

    review_reasons = list(notice.get("review_reasons") or [])
    issues: List[ValidationIssue] = []
    for reason in review_reasons:
        field_name, message = REASON_MESSAGES.get(
            reason, (reason, reason.replace("_", " ").capitalize())
        )
        issues.append(
            ValidationIssue(
                field=field_name,
                message=message,
                source_page=source_page_by_field.get(field_name),
            )
        )

    relations = [
        RelationItem(
            relation_id=int(rel["id"]),
            relation=rel["relation"],
            earlier_notice_id=str(rel["earlier_id"]),
            later_notice_id=str(rel["later_id"]),
            evidence_page=rel.get("evidence_page"),
            evidence_text=rel.get("evidence_text"),
            confirmed=bool(rel.get("confirmed", False)),
        )
        for rel in relations_raw
    ]

    return ReviewDetailResponse(
        notice=_to_notice_summary(notice),
        validation=ValidationSummary(issues=issues, review_reasons=review_reasons),
        source=SourceFilePreview(
            filename=filename,
            page_count=len(pages),
            preview_url=preview_url,
        ),
        pages=pages,
        field_sources=field_sources,
        field_evidence=field_evidence,
        relations=relations,
        processing_history=events_raw,
        edit_history=edits_raw,
    )


def _serialize_field_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


async def patch_notice_fields(
    svc: SupabaseService,
    notice_id: str,
    payload: NoticeFieldsPatchRequest,
    *,
    editor_id: str,
) -> NoticeFieldsPatchResponse:
    """Update editable fields, record audit entries, and re-run blocking checks."""
    notice = await svc.get_notice(notice_id)
    if notice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found.",
        )

    if notice.get("publication_status") == "withdrawn":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Withdrawn notices cannot be edited.",
        )

    provided_fields = [f for f in EDITABLE_FIELDS if f in payload.model_fields_set]
    if not provided_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one editable field must be provided.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    update_data: Dict[str, Any] = {}
    audit_entries: List[Dict[str, Any]] = []
    human_edited_values: Dict[str, Optional[str]] = {}

    for field_name in provided_fields:
        raw_new = getattr(payload, field_name)
        if field_name == "audience" and raw_new is None:
            raw_new = "unspecified"

        serialized_new = _serialize_field_value(raw_new)
        serialized_old = _serialize_field_value(notice.get(field_name))

        update_data[field_name] = serialized_new
        human_edited_values[field_name] = serialized_new

        if serialized_old != serialized_new:
            audit_entries.append(
                {
                    "notice_id": notice_id,
                    "edited_by": editor_id,
                    "field_name": field_name,
                    "old_value": serialized_old,
                    "new_value": serialized_new,
                    "note": payload.correction_note,
                    "edited_at": now_iso,
                }
            )

    merged_notice = {**notice, **update_data}
    recomputed_reasons = _compute_objective_blocking_reasons(merged_notice)
    update_data["review_reasons"] = recomputed_reasons
    update_data["updated_at"] = now_iso

    updated_notice = await svc.update_notice(notice_id, update_data)
    recorded_edits = await svc.insert_notice_edits(audit_entries)
    await svc.mark_fields_human_edited(notice_id, human_edited_values)

    return NoticeFieldsPatchResponse(
        notice=_to_notice_summary(updated_notice),
        edits_recorded=[
            NoticeEditAuditItem(
                field_name=entry["field_name"],
                old_value=entry.get("old_value"),
                new_value=entry.get("new_value"),
                edited_by=str(entry["edited_by"]),
                note=entry.get("note"),
                edited_at=str(entry.get("edited_at") or now_iso),
            )
            for entry in recorded_edits
        ],
        review_reasons=recomputed_reasons,
    )


async def publish_reviewed_notice(
    svc: SupabaseService,
    notice_id: str,
    *,
    actor_id: str,
    confirmation: bool,
) -> PublishNoticeResponse:
    """Verify all blocking review reasons are cleared and publish a held notice."""
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation (confirmation=true) is required to publish.",
        )

    notice = await svc.get_notice(notice_id)
    if notice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found.",
        )

    pub_status = notice.get("publication_status")
    if pub_status == "withdrawn":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Withdrawn notices cannot be published.",
        )
    if pub_status == "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Notice is already published.",
        )

    if notice.get("processing_status") in ("pending", "processing"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Notice is still processing and cannot be published yet.",
        )

    existing_reasons = list(notice.get("review_reasons") or [])
    objective_reasons = _compute_objective_blocking_reasons(notice)
    blocking_reasons = list(dict.fromkeys(existing_reasons + objective_reasons))

    if blocking_reasons:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cannot publish notice while blocking review reasons remain: "
                + ", ".join(blocking_reasons)
            ),
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    await svc.update_notice(
        notice_id,
        {
            "publication_status": "published",
            "published_at": now_iso,
            "published_by": actor_id,
            "review_reasons": [],
            "updated_at": now_iso,
        },
    )
    await svc.insert_processing_event(
        notice_id,
        step="publication",
        outcome="ok",
        message=f"Published by reviewer {actor_id}.",
    )

    return PublishNoticeResponse(
        notice_id=notice_id,
        publication_status="published",
        published_at=now_iso,
    )


async def retry_notice_processing(
    svc: SupabaseService,
    notice_id: str,
    *,
    actor_id: str,
    confirmation: bool,
) -> RetryNoticeResponse:
    """Re-queue an eligible failed or held notice for processing."""
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation (confirmation=true) is required to retry processing.",
        )

    notice = await svc.get_notice(notice_id)
    if notice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found.",
        )

    proc_status = notice.get("processing_status")
    pub_status = notice.get("publication_status")

    eligible = proc_status == "failed" or (
        proc_status == "completed" and pub_status == "held"
    )
    if not eligible or pub_status == "withdrawn":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Notice in state (processing={proc_status}, publication={pub_status}) "
                "is not eligible for retry."
            ),
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    await svc.update_notice(
        notice_id,
        {
            "processing_status": "pending",
            "publication_status": "held",
            "updated_at": now_iso,
        },
    )
    await svc.insert_processing_event(
        notice_id,
        step="retry",
        outcome="started",
        message=f"Processing retry requested by {actor_id}.",
    )

    return RetryNoticeResponse(
        notice_id=notice_id,
        processing_status="pending",
    )


async def handle_relationship_action(
    svc: SupabaseService,
    relation_id: int,
    *,
    action: str,
    actor_id: str,
    expected_notice_id: Optional[str] = None,
) -> RelationshipActionResponse:
    """Confirm or reject a detected relationship without modifying unapproved notices."""
    rel = await svc.get_relationship_by_id(relation_id)
    if rel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found.",
        )

    earlier_id = str(rel["earlier_id"])
    later_id = str(rel["later_id"])
    if expected_notice_id is not None and expected_notice_id not in (earlier_id, later_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship does not belong to the specified notice.",
        )

    if action == "reject":
        if rel.get("confirmed"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot reject an already confirmed relationship.",
            )
        await svc.delete_relationship(relation_id)
        await svc.insert_processing_event(
            later_id,
            step="relationship_rejected",
            outcome="ok",
            message=f"Relationship {relation_id} rejected by {actor_id}.",
        )
        return RelationshipActionResponse(
            relation_id=relation_id,
            outcome="rejected",
            earlier_notice_id=earlier_id,
            earlier_relationship_status=None,
        )

    # action == "confirm"
    if rel.get("confirmed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Relationship is already confirmed.",
        )

    await svc.update_relationship(
        relation_id,
        {
            "confirmed": True,
            "confirmed_by": actor_id,
            "basis": "human_confirmed",
        },
    )

    earlier_notice = await svc.get_notice(earlier_id)
    earlier_rel_status: Optional[str] = (
        earlier_notice.get("relationship_status", "current") if earlier_notice else None
    )

    # Critical boundary: never modify unapproved (held/withdrawn) notices.
    if earlier_notice and earlier_notice.get("publication_status") == "published":
        new_rel_status = RELATION_TO_STATUS.get(rel["relation"])
        if new_rel_status:
            await svc.update_notice(
                earlier_id,
                {
                    "relationship_status": new_rel_status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            earlier_rel_status = new_rel_status

    await svc.insert_processing_event(
        later_id,
        step="relationship_confirmed",
        outcome="ok",
        message=f"Relationship {relation_id} ({rel['relation']}) confirmed by {actor_id}.",
    )

    return RelationshipActionResponse(
        relation_id=relation_id,
        outcome="confirmed",
        earlier_notice_id=earlier_id,
        earlier_relationship_status=earlier_rel_status,
    )
