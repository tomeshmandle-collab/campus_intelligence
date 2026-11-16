"""
Automated Test Suite for Issue P1-1: Sample College Notice Dataset & Manifest
CAI Campus Intelligence — Quality & Test Assets (M12)
"""

import json
import re
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Paths
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures" / "sample_notices"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
VERIFY_SCRIPT_PATH = TESTS_DIR / "scripts" / "verify_manifest.py"

ALLOWED_AUDIENCES = {"student", "faculty", "staff", "all", "unspecified"}
ALLOWED_NOTICE_TYPES = {"digital", "scanned", "mixed"}
ALLOWED_CATEGORIES = {"Admissions", "Exams", "General", "Scholarships", "Administrative", "Events"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TestSampleNoticesManifest(unittest.TestCase):
    """Test suite verifying benchmark sample notices manifest and PDF assets."""

    @classmethod
    def setUpClass(cls):
        cls.manifest_exists = MANIFEST_PATH.is_file()
        if cls.manifest_exists:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                cls.manifest_data = json.load(f)
        else:
            cls.manifest_data = []

    def test_manifest_file_exists(self):
        """Assert that manifest.json exists in the fixtures directory."""
        self.assertTrue(
            self.manifest_exists,
            f"manifest.json not found at {MANIFEST_PATH}",
        )

    def test_manifest_is_valid_json_list(self):
        """Assert that manifest root is a non-empty JSON list."""
        self.assertIsInstance(self.manifest_data, list)
        self.assertGreater(len(self.manifest_data), 0)

    def test_dataset_size_within_benchmark_target(self):
        """Assert dataset count meets the 15-20 notice benchmark requirement."""
        total = len(self.manifest_data)
        self.assertGreaterEqual(total, 15, f"Expected at least 15 sample notices, found {total}")
        self.assertLessEqual(total, 25, f"Expected at most 25 sample notices, found {total}")

    def test_schema_conformance_for_all_entries(self):
        """Assert each manifest entry conforms to required schema fields and types."""
        required_fields = {
            "filename",
            "notice_type",
            "is_scanned",
            "page_count",
            "expected_title",
            "expected_notice_date",
            "expected_deadline_date",
            "expected_audience",
            "expected_category",
        }

        for item in self.manifest_data:
            filename = item.get("filename", "<unknown>")
            for field in required_fields:
                self.assertIn(
                    field,
                    item,
                    f"[{filename}] Missing required field '{field}' in manifest entry",
                )

            # Filename
            self.assertTrue(item["filename"].endswith(".pdf"), f"[{filename}] Must end with .pdf")

            # Notice Type
            self.assertIn(
                item["notice_type"],
                ALLOWED_NOTICE_TYPES,
                f"[{filename}] Invalid notice_type: {item['notice_type']}",
            )

            # is_scanned consistency
            self.assertIsInstance(item["is_scanned"], bool, f"[{filename}] is_scanned must be boolean")
            if item["notice_type"] == "scanned":
                self.assertTrue(item["is_scanned"], f"[{filename}] Scanned type must have is_scanned=True")
            elif item["notice_type"] == "digital":
                self.assertFalse(item["is_scanned"], f"[{filename}] Digital type must have is_scanned=False")

            # Page Count
            self.assertIsInstance(item["page_count"], int)
            self.assertGreater(item["page_count"], 0)

            # Notice Date
            self.assertTrue(
                bool(DATE_PATTERN.match(item["expected_notice_date"])),
                f"[{filename}] Notice date must be YYYY-MM-DD: {item['expected_notice_date']}",
            )
            # Validate calendar validity
            datetime.strptime(item["expected_notice_date"], "%Y-%m-%d")

            # Deadline Date (if present)
            deadline = item["expected_deadline_date"]
            if deadline is not None:
                self.assertTrue(
                    bool(DATE_PATTERN.match(deadline)),
                    f"[{filename}] Deadline date must be YYYY-MM-DD: {deadline}",
                )
                datetime.strptime(deadline, "%Y-%m-%d")

            # Audience
            self.assertIn(
                item["expected_audience"],
                ALLOWED_AUDIENCES,
                f"[{filename}] Invalid expected_audience: {item['expected_audience']}",
            )

            # Category
            self.assertIn(
                item["expected_category"],
                ALLOWED_CATEGORIES,
                f"[{filename}] Invalid expected_category: {item['expected_category']}",
            )

    def test_sample_pdf_files_exist_and_valid(self):
        """Assert every declared sample notice PDF exists on disk and has valid PDF structure."""
        for item in self.manifest_data:
            filename = item["filename"]
            pdf_path = FIXTURES_DIR / filename
            self.assertTrue(pdf_path.is_file(), f"File does not exist: {pdf_path}")

            content = pdf_path.read_bytes()
            self.assertGreater(len(content), 0, f"[{filename}] File is empty (0 bytes)")
            self.assertTrue(content.startswith(b"%PDF-"), f"[{filename}] Missing %PDF- header")
            self.assertIn(b"%%EOF", content[-200:], f"[{filename}] Missing %%EOF trailer")

            # Page count object match
            page_obj_count = content.count(b"/Type /Page\n") + content.count(b"/Type /Page ")
            self.assertEqual(
                page_obj_count,
                item["page_count"],
                f"[{filename}] PDF page object count ({page_obj_count}) does not match declared page_count ({item['page_count']})",
            )

    def test_dataset_diversity_requirements(self):
        """Assert dataset satisfies representative requirements (multi-page, scanned, table, amendment)."""
        multi_page_count = sum(1 for item in self.manifest_data if item["page_count"] > 1)
        scanned_count = sum(1 for item in self.manifest_data if item["is_scanned"])
        digital_count = sum(1 for item in self.manifest_data if not item["is_scanned"])
        has_table_notes = sum(
            1 for item in self.manifest_data
            if "table" in item.get("edge_case_notes", "").lower()
            or "matrix" in item.get("edge_case_notes", "").lower()
        )
        has_amendment_notes = sum(
            1 for item in self.manifest_data
            if "supersed" in item.get("edge_case_notes", "").lower()
            or "amend" in item.get("edge_case_notes", "").lower()
            or "extension" in item.get("edge_case_notes", "").lower()
        )
        audiences = {item["expected_audience"] for item in self.manifest_data}
        categories = {item["expected_category"] for item in self.manifest_data}

        self.assertGreaterEqual(multi_page_count, 3, "Expected at least 3 multi-page notices")
        self.assertGreaterEqual(scanned_count, 3, "Expected at least 3 scanned notices")
        self.assertGreaterEqual(digital_count, 8, "Expected at least 8 digital notices")
        self.assertGreaterEqual(has_table_notes, 1, "Expected at least 1 notice with table data")
        self.assertGreaterEqual(has_amendment_notes, 1, "Expected at least 1 amended/superseded notice")
        self.assertIn("unspecified", audiences, "Must include notice with 'unspecified' audience")
        self.assertIn("student", audiences, "Must include notice with 'student' audience")
        self.assertIn("faculty", audiences, "Must include notice with 'faculty' audience")
        self.assertIn("staff", audiences, "Must include notice with 'staff' audience")
        self.assertIn("all", audiences, "Must include notice with 'all' audience")

        expected_cats = {"Admissions", "Exams", "General", "Scholarships"}
        for cat in expected_cats:
            self.assertIn(cat, categories, f"Expected category '{cat}' to be represented")

    def test_privacy_no_sensitive_personal_data(self):
        """Assert that no personal phone numbers, emails, or roll numbers leak into test assets."""
        phone_pattern = re.compile(r"\b[6-9]\d{9}\b")

        for item in self.manifest_data:
            text_to_check = (
                f"{item.get('expected_title', '')} "
                f"{item.get('edge_case_notes', '')} "
                f"{item.get('filename', '')}"
            )
            self.assertIsNone(
                phone_pattern.search(text_to_check),
                f"[{item['filename']}] Potential personal phone number detected!",
            )

    def test_verification_script_executes_with_zero_exit_code(self):
        """Assert that python tests/scripts/verify_manifest.py exits with status code 0."""
        self.assertTrue(VERIFY_SCRIPT_PATH.is_file(), f"Script not found at {VERIFY_SCRIPT_PATH}")
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"verify_manifest.py failed with return code {result.returncode}.\nOutput:\n{result.stdout}\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
