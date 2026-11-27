from datetime import date
import json
import time
from types import SimpleNamespace
import uuid

import pytest

from app.core import config
from app.services.ai.gemini_extractor import (
    AIExtractionError,
    FieldEvidence,
    NoticeExtractionSchema,
    extract_and_update_notice,
    extract_notice_structured,
    format_page_indexed_text,
    process_notice_extraction,
    validate_extracted_notice,
)
from app.services.extraction.pdf_extractor import ExtractedPage
from app.services.supabase import SupabaseService


def _sample_pages() -> list[ExtractedPage]:
    return [
        ExtractedPage(
            page_number=1,
            extracted_text=(
                "Kirori Mal College, University of Delhi\n"
                "Notice Date: 01 November 2026\n"
                "Notice: Submission of Examination Forms for Semester III Students.\n"
                "All undergraduate students must submit their examination forms online."
            ),
            is_scanned=False,
            ocr_failed=False,
        ),
        ExtractedPage(
            page_number=2,
            extracted_text=(
                "The last date to submit the examination form without late fee is 20 November 2026.\n"
                "Contact the Examination Branch for assistance."
            ),
            is_scanned=False,
            ocr_failed=False,
        ),
    ]


def _sample_valid_payload(**overrides) -> dict:
    payload = {
        "title": "Submission of Examination Forms for Semester III Students",
        "notice_date": "2026-11-01",
        "deadline_date": "2026-11-20",
        "audience": "student",
        "category": "examination",
        "summary": "Undergraduate students must submit Semester III examination forms by 20 November 2026.",
        "confidence": 0.94,
        "field_evidence": {
            "title": {
                "page_number": 1,
                "quote": "Notice: Submission of Examination Forms for Semester III Students.",
            },
            "notice_date": {
                "page_number": 1,
                "quote": "Notice Date: 01 November 2026",
            },
            "deadline_date": {
                "page_number": 2,
                "quote": "The last date to submit the examination form without late fee is 20 November 2026.",
            },
            "audience": {
                "page_number": 1,
                "quote": "All undergraduate students must submit their examination forms online.",
            },
        },
    }
    payload.update(overrides)
    return payload


def _install_fake_gemini(monkeypatch, response_text: str, delay_seconds: float = 0.0):
    captured = {}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            captured["model"] = model
            captured["contents"] = contents
            captured["config"] = config
            return SimpleNamespace(text=response_text)

    class FakeClient:
        def __init__(self, *, api_key, http_options):
            captured["api_key"] = api_key
            captured["timeout_ms"] = http_options.timeout
            self.models = FakeModels()

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(config.settings, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr("app.services.ai.gemini_extractor.genai.Client", FakeClient)
    return captured


def test_format_page_indexed_text_orders_and_labels_pages():
    pages = [
        {"page_number": 2, "text": "Second page body"},
        ExtractedPage(page_number=1, extracted_text="First page body"),
    ]
    formatted = format_page_indexed_text(pages)
    assert "--- PAGE 1 ---\nFirst page body" in formatted
    assert "--- PAGE 2 ---\nSecond page body" in formatted
    assert formatted.index("PAGE 1") < formatted.index("PAGE 2")


def test_format_page_indexed_text_respects_max_chars():
    pages = [ExtractedPage(page_number=1, extracted_text="X" * 500)]
    formatted = format_page_indexed_text(pages, max_chars=80)
    assert len(formatted) <= 80
    assert formatted.endswith("...[TRUNCATED]")


def test_extract_notice_structured_calls_gemini_and_parses_schema(monkeypatch):
    payload = _sample_valid_payload()
    captured = _install_fake_gemini(monkeypatch, json.dumps(payload))

    result = extract_notice_structured(_sample_pages(), timeout_seconds=15.0)

    assert isinstance(result, NoticeExtractionSchema)
    assert result.title == "Submission of Examination Forms for Semester III Students"
    assert result.notice_date == date(2026, 11, 1)
    assert result.deadline_date == date(2026, 11, 20)
    assert result.audience == "student"
    assert result.category == "examination"
    assert result.confidence == pytest.approx(0.94)
    assert result.field_evidence["deadline_date"] == FieldEvidence(
        page_number=2,
        quote="The last date to submit the examination form without late fee is 20 November 2026.",
    )

    assert captured["api_key"] == "test-gemini-key"
    assert captured["model"] == "gemini-2.5-flash"
    assert captured["timeout_ms"] == 15000
    assert "--- PAGE 1 ---" in captured["contents"]
    assert "--- PAGE 2 ---" in captured["contents"]
    assert captured["config"].response_mime_type == "application/json"


def test_extract_notice_structured_handles_fenced_json(monkeypatch):
    fenced = f"```json\n{json.dumps(_sample_valid_payload())}\n```"
    _install_fake_gemini(monkeypatch, fenced)

    result = extract_notice_structured(_sample_pages())
    assert result.category == "examination"
    assert result.audience == "student"


def test_extract_notice_structured_rejects_malformed_or_invalid_schema(monkeypatch):
    _install_fake_gemini(monkeypatch, "{not valid json")
    with pytest.raises(AIExtractionError, match="malformed JSON"):
        extract_notice_structured(_sample_pages())

    bad_schema = _sample_valid_payload(category="not_a_valid_category")
    _install_fake_gemini(monkeypatch, json.dumps(bad_schema))
    with pytest.raises(AIExtractionError, match="schema validation"):
        extract_notice_structured(_sample_pages())


def test_extract_notice_structured_handles_missing_key_and_timeout(monkeypatch):
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "")
    with pytest.raises(AIExtractionError, match="GEMINI_API_KEY"):
        extract_notice_structured(_sample_pages())

    _install_fake_gemini(monkeypatch, json.dumps(_sample_valid_payload()), delay_seconds=0.3)
    with pytest.raises(AIExtractionError, match="timed out"):
        extract_notice_structured(_sample_pages(), timeout_seconds=0.05)


def test_rule_1_deadline_prior_to_notice_date_holds_notice():
    extraction = NoticeExtractionSchema.model_validate(
        _sample_valid_payload(notice_date="2026-11-20", deadline_date="2026-11-01")
    )
    pages = [
        ExtractedPage(
            page_number=1,
            extracted_text=(
                "Notice: Submission of Examination Forms for Semester III Students. "
                "Notice Date: 01 November 2026."
            ),
        ),
        ExtractedPage(
            page_number=2,
            extracted_text="The last date to submit the examination form without late fee is 20 November 2026.",
        ),
    ]
    validation = validate_extracted_notice(extraction, pages)
    assert validation.publication_status == "held"
    assert validation.passed is False
    assert "deadline_prior_to_notice_date" in validation.review_reasons


def test_rule_2_missing_notice_date_holds_notice():
    payload = _sample_valid_payload(notice_date=None)
    payload["field_evidence"].pop("notice_date", None)
    extraction = NoticeExtractionSchema.model_validate(payload)

    validation = validate_extracted_notice(extraction, _sample_pages())
    assert validation.publication_status == "held"
    assert "missing_notice_date" in validation.review_reasons


def test_rule_3_ocr_failed_holds_notice():
    extraction = NoticeExtractionSchema.model_validate(_sample_valid_payload())
    pages = _sample_pages()
    pages[1] = ExtractedPage(
        page_number=2,
        extracted_text="The last date to submit the examination form without late fee is 20 November 2026.",
        is_scanned=True,
        ocr_failed=True,
    )

    validation = validate_extracted_notice(extraction, pages)
    assert validation.publication_status == "held"
    assert "unreliable_ocr" in validation.review_reasons


def test_rule_4_high_confidence_and_all_checks_pass_publishes():
    extraction = NoticeExtractionSchema.model_validate(_sample_valid_payload(confidence=0.92))
    validation = validate_extracted_notice(extraction, _sample_pages(), confidence_threshold=0.85)
    assert validation.publication_status == "published"
    assert validation.passed is True
    assert validation.review_reasons == []


def test_rule_4_low_confidence_holds_notice():
    extraction = NoticeExtractionSchema.model_validate(_sample_valid_payload(confidence=0.60))
    validation = validate_extracted_notice(extraction, _sample_pages(), confidence_threshold=0.85)
    assert validation.publication_status == "held"
    assert validation.passed is False
    assert "low_extraction_confidence" in validation.review_reasons


def test_missing_or_ungrounded_field_evidence_holds_notice():
    # Missing evidence for deadline_date when deadline_date is set
    payload_missing_ev = _sample_valid_payload()
    del payload_missing_ev["field_evidence"]["deadline_date"]
    validation = validate_extracted_notice(
        NoticeExtractionSchema.model_validate(payload_missing_ev), _sample_pages()
    )
    assert validation.publication_status == "held"
    assert "missing_field_evidence" in validation.review_reasons

    # Out-of-bounds page number
    payload_bad_page = _sample_valid_payload()
    payload_bad_page["field_evidence"]["title"]["page_number"] = 9
    validation = validate_extracted_notice(
        NoticeExtractionSchema.model_validate(payload_bad_page), _sample_pages()
    )
    assert validation.publication_status == "held"
    assert "invalid_evidence_page" in validation.review_reasons

    # Fabricated quote not in cited page text
    payload_bad_quote = _sample_valid_payload()
    payload_bad_quote["field_evidence"]["title"]["quote"] = (
        "Completely fabricated sentence that never appeared in the source PDF."
    )
    validation = validate_extracted_notice(
        NoticeExtractionSchema.model_validate(payload_bad_quote), _sample_pages()
    )
    assert validation.publication_status == "held"
    assert "unverified_field_evidence" in validation.review_reasons


def test_unspecified_audience_preserved_not_defaulted_to_all():
    extraction = NoticeExtractionSchema.model_validate(_sample_valid_payload(audience=None))
    assert extraction.audience == "unspecified"


def test_process_notice_extraction_updates_database_on_publish(monkeypatch):
    _install_fake_gemini(monkeypatch, json.dumps(_sample_valid_payload(confidence=0.95)))
    svc = SupabaseService(is_mock=True)
    notice_id = str(uuid.uuid4())
    svc._in_memory_notices[notice_id] = {
        "id": notice_id,
        "title": "uploaded.pdf",
        "processing_status": "processing",
        "publication_status": "held",
        "review_reasons": [],
    }

    outcome = process_notice_extraction(
        notice_id,
        _sample_pages(),
        supabase_service=svc,
    )

    assert outcome.processing_status == "completed"
    assert outcome.publication_status == "published"
    assert outcome.review_reasons == []

    stored = svc._in_memory_notices[notice_id]
    assert stored["title"] == "Submission of Examination Forms for Semester III Students"
    assert stored["notice_date"] == "2026-11-01"
    assert stored["deadline_date"] == "2026-11-20"
    assert stored["audience"] == "student"
    assert stored["category"] == "examination"
    assert stored["processing_status"] == "completed"
    assert stored["publication_status"] == "published"
    assert stored["review_reasons"] == []


def test_process_notice_extraction_inherits_existing_ocr_hold_from_db(monkeypatch):
    _install_fake_gemini(monkeypatch, json.dumps(_sample_valid_payload(confidence=0.95)))
    svc = SupabaseService(is_mock=True)
    notice_id = str(uuid.uuid4())
    svc._in_memory_notices[notice_id] = {
        "id": notice_id,
        "processing_status": "processing",
        "publication_status": "held",
        "review_reasons": ["ocr_uncertain_or_unreadable"],
    }

    outcome = process_notice_extraction(notice_id, _sample_pages(), supabase_service=svc)

    assert outcome.publication_status == "held"
    assert "unreliable_ocr" in outcome.review_reasons
    assert svc._in_memory_notices[notice_id]["publication_status"] == "held"
    assert "unreliable_ocr" in svc._in_memory_notices[notice_id]["review_reasons"]


def test_process_notice_extraction_handles_provider_failure_safely(monkeypatch):
    class FailingModels:
        def generate_content(self, *, model, contents, config):
            raise RuntimeError("Gemini 503 Unavailable")

    class FailingClient:
        def __init__(self, *, api_key, http_options):
            self.models = FailingModels()

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai.gemini_extractor.genai.Client", FailingClient)

    svc = SupabaseService(is_mock=True)
    notice_id = str(uuid.uuid4())
    svc._in_memory_notices[notice_id] = {
        "id": notice_id,
        "processing_status": "processing",
        "publication_status": "held",
        "review_reasons": [],
    }

    outcome = process_notice_extraction(notice_id, _sample_pages(), supabase_service=svc)

    assert outcome.processing_status == "failed"
    assert outcome.publication_status == "held"
    assert "ai_extraction_failed" in outcome.review_reasons
    assert svc._in_memory_notices[notice_id]["processing_status"] == "failed"
    assert svc._in_memory_notices[notice_id]["publication_status"] == "held"
    assert "ai_extraction_failed" in svc._in_memory_notices[notice_id]["review_reasons"]


@pytest.mark.anyio
async def test_extract_and_update_notice_async(monkeypatch):
    _install_fake_gemini(
        monkeypatch,
        json.dumps(
            _sample_valid_payload(
                notice_date="2026-11-25",
                deadline_date="2026-11-20",
                confidence=0.95,
            )
        ),
    )
    svc = SupabaseService(is_mock=True)
    notice_id = str(uuid.uuid4())
    svc._in_memory_notices[notice_id] = {
        "id": notice_id,
        "processing_status": "processing",
        "publication_status": "held",
        "review_reasons": [],
    }

    outcome = await extract_and_update_notice(notice_id, _sample_pages(), supabase_service=svc)

    assert outcome.processing_status == "completed"
    assert outcome.publication_status == "held"
    assert "deadline_prior_to_notice_date" in outcome.review_reasons
    assert svc._in_memory_notices[notice_id]["publication_status"] == "held"
    assert "deadline_prior_to_notice_date" in svc._in_memory_notices[notice_id]["review_reasons"]
