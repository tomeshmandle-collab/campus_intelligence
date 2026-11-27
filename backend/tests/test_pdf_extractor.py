import time
from types import SimpleNamespace
import uuid

import pytest
import pymupdf as fitz

from app.core import config
from app.services.extraction.pdf_extractor import (
    ExtractedPage,
    PDFExtractionError,
    extract_and_store_pdf_pages,
    extract_pdf_pages,
)
from app.services.supabase import SupabaseService


def _make_pdf_bytes(page_texts: list[str]) -> bytes:
    """Create an in-memory PDF document with one page per text entry."""
    doc = fitz.open()
    for text in page_texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_single_page_digital_pdf(monkeypatch):
    """Digital PDF with >= 50 chars extracts text without invoking Gemini OCR."""
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("OCR should not be called for digital pages")

    monkeypatch.setattr(
        "app.services.extraction.pdf_extractor._ocr_page_with_gemini",
        fail_if_called,
    )

    text = (
        "Kirori Mal College, University of Delhi: Examination form deadline is 15 December 2026."
    )
    pdf_bytes = _make_pdf_bytes([text])

    pages = extract_pdf_pages(pdf_bytes)

    assert len(pages) == 1
    assert isinstance(pages[0], ExtractedPage)
    assert pages[0].page_number == 1
    assert "Kirori Mal College" in pages[0].extracted_text
    assert pages[0].is_scanned is False
    assert pages[0].ocr_failed is False
    assert called is False


def test_extract_multipage_digital_pdf_preserves_page_numbers():
    """Multi-page digital PDF preserves 1-based page numbers and per-page text."""
    page_1 = "Page One: Notice regarding undergraduate internal assessment schedule for semester V."
    page_2 = "Page Two: Students must submit practical files to the Department of Computer Science."
    page_3 = "Page Three: Late submissions after 20 November 2026 will not be entertained."
    pdf_bytes = _make_pdf_bytes([page_1, page_2, page_3])

    pages = extract_pdf_pages(pdf_bytes)

    assert [p.page_number for p in pages] == [1, 2, 3]
    assert "Page One:" in pages[0].extracted_text
    assert "Page Two:" in pages[1].extracted_text
    assert "Page Three:" in pages[2].extracted_text
    assert all(not p.is_scanned and not p.ocr_failed for p in pages)


def test_threshold_49_vs_50_chars(monkeypatch):
    """Pages with < 50 chars are marked scanned; pages with >= 50 chars are digital."""
    monkeypatch.setattr(
        "app.services.extraction.pdf_extractor._ocr_page_with_gemini",
        lambda image_bytes, *, page_number, timeout_seconds: "OCR fallback text",
    )

    text_49 = "A" * 49
    text_50 = "B" * 50
    pdf_bytes = _make_pdf_bytes([text_49, text_50])

    pages = extract_pdf_pages(pdf_bytes)

    assert pages[0].page_number == 1
    assert pages[0].is_scanned is True
    assert pages[0].extracted_text == "OCR fallback text"
    assert pages[0].ocr_failed is False

    assert pages[1].page_number == 2
    assert pages[1].is_scanned is False
    assert pages[1].extracted_text == text_50
    assert pages[1].ocr_failed is False


def test_scanned_page_calls_gemini_multimodal_ocr(monkeypatch):
    """Scanned page renders PNG and calls Gemini multimodal vision endpoint."""
    captured = {}

    class FakeModels:
        def generate_content(self, *, model, contents):
            captured["model"] = model
            captured["contents"] = contents
            return SimpleNamespace(text="  Transcribed scanned circular text  ")

    class FakeClient:
        def __init__(self, *, api_key, http_options):
            captured["api_key"] = api_key
            captured["timeout_ms"] = http_options.timeout
            self.models = FakeModels()

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(config.settings, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr("app.services.extraction.pdf_extractor.genai.Client", FakeClient)

    pdf_bytes = _make_pdf_bytes([""])  # Empty digital text -> scanned page

    pages = extract_pdf_pages(pdf_bytes, ocr_timeout_seconds=12.0)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].is_scanned is True
    assert pages[0].ocr_failed is False
    assert pages[0].extracted_text == "Transcribed scanned circular text"

    assert captured["api_key"] == "test-gemini-key"
    assert captured["model"] == "gemini-2.5-flash"
    assert captured["timeout_ms"] == 12000
    image_part = captured["contents"][0]
    assert image_part.inline_data.mime_type == "image/png"
    assert image_part.inline_data.data.startswith(b"\x89PNG")


def test_mixed_digital_and_scanned_pages(monkeypatch):
    """Mixed PDF runs OCR only for scanned pages while keeping digital pages intact."""
    ocr_pages_called = []

    def fake_ocr(image_bytes, *, page_number, timeout_seconds):
        ocr_pages_called.append(page_number)
        return f"OCR text for page {page_number}"

    monkeypatch.setattr("app.services.extraction.pdf_extractor._ocr_page_with_gemini", fake_ocr)

    digital_text = "Official Notice: College library timing extended until 8:00 PM during exams."
    pdf_bytes = _make_pdf_bytes([digital_text, "Short"])

    pages = extract_pdf_pages(pdf_bytes)

    assert ocr_pages_called == [2]
    assert pages[0].is_scanned is False
    assert "Official Notice" in pages[0].extracted_text
    assert pages[1].is_scanned is True
    assert pages[1].extracted_text == "OCR text for page 2"
    assert pages[1].ocr_failed is False


def test_scanned_page_ocr_exception_marks_ocr_failed(monkeypatch):
    """When Gemini OCR raises an error, text is empty and ocr_failed=True."""

    class FailingModels:
        def generate_content(self, *, model, contents):
            raise RuntimeError("Upstream Gemini 503 error")

    class FailingClient:
        def __init__(self, *, api_key, http_options):
            self.models = FailingModels()

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr("app.services.extraction.pdf_extractor.genai.Client", FailingClient)

    pdf_bytes = _make_pdf_bytes([""])
    pages = extract_pdf_pages(pdf_bytes)

    assert len(pages) == 1
    assert pages[0].is_scanned is True
    assert pages[0].ocr_failed is True
    assert pages[0].extracted_text == ""


def test_scanned_page_ocr_timeout_marks_ocr_failed(monkeypatch):
    """When Gemini OCR exceeds timeout, timeout is caught and ocr_failed=True."""

    class SlowModels:
        def generate_content(self, *, model, contents):
            time.sleep(0.5)
            return SimpleNamespace(text="Too late")

    class SlowClient:
        def __init__(self, *, api_key, http_options):
            self.models = SlowModels()

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr("app.services.extraction.pdf_extractor.genai.Client", SlowClient)

    pdf_bytes = _make_pdf_bytes([""])
    pages = extract_pdf_pages(pdf_bytes, ocr_timeout_seconds=0.05)

    assert len(pages) == 1
    assert pages[0].is_scanned is True
    assert pages[0].ocr_failed is True
    assert pages[0].extracted_text == ""


def test_scanned_page_without_api_key_marks_ocr_failed(monkeypatch):
    """Missing GEMINI_API_KEY safely triggers OCR failure without crashing."""
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "")

    pdf_bytes = _make_pdf_bytes([""])
    pages = extract_pdf_pages(pdf_bytes)

    assert len(pages) == 1
    assert pages[0].is_scanned is True
    assert pages[0].ocr_failed is True
    assert pages[0].extracted_text == ""


def test_invalid_or_empty_pdf_raises_extraction_error():
    """Empty bytes or corrupt PDF content raises PDFExtractionError."""
    with pytest.raises(PDFExtractionError):
        extract_pdf_pages(b"")

    with pytest.raises(PDFExtractionError):
        extract_pdf_pages(b"not a valid pdf binary")


def test_exceeding_max_page_count_raises_error(monkeypatch):
    """PDF exceeding MAX_PAGE_COUNT raises PDFExtractionError."""
    monkeypatch.setattr(config.settings, "MAX_PAGE_COUNT", 2)
    pdf_bytes = _make_pdf_bytes(["Page 1 text", "Page 2 text", "Page 3 text"])

    with pytest.raises(PDFExtractionError, match="exceeds maximum allowed"):
        extract_pdf_pages(pdf_bytes)


def test_save_records_into_notice_pages_table(monkeypatch):
    """Extracted pages are saved to notice_pages and OCR failures flag notice for review."""
    svc = SupabaseService(is_mock=True)
    notice_id = str(uuid.uuid4())
    svc._in_memory_notices[notice_id] = {
        "id": notice_id,
        "processing_status": "processing",
        "publication_status": "held",
        "review_reasons": [],
    }

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "")  # force OCR fail on page 2

    digital_text = "Digital Notice Text: Scholarship portal is open until 30 November 2026."
    pdf_bytes = _make_pdf_bytes([digital_text, ""])

    pages = extract_pdf_pages(pdf_bytes, notice_id=notice_id, supabase_service=svc)

    assert len(pages) == 2
    saved_rows = svc._in_memory_notice_pages.get(notice_id)
    assert saved_rows is not None
    assert len(saved_rows) == 2

    assert saved_rows[0] == {
        "notice_id": notice_id,
        "page_number": 1,
        "extracted_text": digital_text,
        "is_scanned": False,
    }
    assert saved_rows[1] == {
        "notice_id": notice_id,
        "page_number": 2,
        "extracted_text": "",
        "is_scanned": True,
    }
    assert svc._in_memory_notices[notice_id]["publication_status"] == "held"
    assert "ocr_uncertain_or_unreadable" in svc._in_memory_notices[notice_id]["review_reasons"]


@pytest.mark.anyio
async def test_extract_and_store_pdf_pages_async(monkeypatch):
    """Async wrapper extracts pages and stores records into notice_pages."""
    svc = SupabaseService(is_mock=True)
    notice_id = str(uuid.uuid4())

    monkeypatch.setattr(
        "app.services.extraction.pdf_extractor._ocr_page_with_gemini",
        lambda image_bytes, *, page_number, timeout_seconds: "Async OCR Result",
    )

    pdf_bytes = _make_pdf_bytes([""])
    pages = await extract_and_store_pdf_pages(notice_id, pdf_bytes, supabase_service=svc)

    assert len(pages) == 1
    assert pages[0].extracted_text == "Async OCR Result"
    assert svc._in_memory_notice_pages[notice_id] == [
        {
            "notice_id": notice_id,
            "page_number": 1,
            "extracted_text": "Async OCR Result",
            "is_scanned": True,
        }
    ]
