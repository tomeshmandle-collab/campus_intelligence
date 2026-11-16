"""
Manifest Verification Script for CAI Campus Intelligence (P1 Quality & Test Assets)

Validates tests/fixtures/sample_notices/manifest.json against benchmark standards:
1. Every listed filename exists in tests/fixtures/sample_notices/
2. expected_notice_date adheres to 'YYYY-MM-DD' ISO format.
3. expected_deadline_date adheres to 'YYYY-MM-DD' or null.
4. expected_audience is strictly one of ['student', 'faculty', 'staff', 'all', 'unspecified'].
5. notice_type is one of ['digital', 'scanned', 'mixed'].
6. Prints a summary table and returns exit code 0 on success, 1 on failure.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Allowed enum constants per project specifications
ALLOWED_AUDIENCES = {"student", "faculty", "staff", "all", "unspecified"}
ALLOWED_NOTICE_TYPES = {"digital", "scanned", "mixed"}
ALLOWED_CATEGORIES = {"Admissions", "Exams", "General", "Scholarships", "Administrative", "Events"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_iso_date(date_str: str) -> bool:
    """Check if date matches YYYY-MM-DD and is a calendar-valid date."""
    if not date_str or not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def verify_manifest() -> bool:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures" / "sample_notices"
    manifest_path = fixtures_dir / "manifest.json"

    print("=" * 80)
    print("CAI Campus Intelligence — P1 Benchmark Manifest Verification")
    print(f"Manifest Path: {manifest_path}")
    print("=" * 80)

    if not manifest_path.is_file():
        print(f"[ERROR] Manifest file not found at: {manifest_path}")
        return False

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON in manifest: {e}")
        return False

    if not isinstance(manifest, list):
        print("[ERROR] Manifest root must be a JSON array of notice records.")
        return False

    if len(manifest) == 0:
        print("[ERROR] Manifest is empty! Expected 15-20 notice items.")
        return False

    errors = []
    digital_count = 0
    scanned_count = 0
    mixed_count = 0

    print(f"\nVerifying {len(manifest)} notice manifest entries...\n")
    print(f"{'#':<3} | {'Filename':<38} | {'Type':<8} | {'Pages':<5} | {'Date':<10} | {'Status'}")
    print("-" * 80)

    for idx, item in enumerate(manifest, 1):
        item_errors = []
        filename = item.get("filename")

        if not filename:
            item_errors.append("Missing 'filename' field")
            filename = f"<Item {idx} Unknown>"
        else:
            file_path = fixtures_dir / filename
            if not file_path.is_file():
                item_errors.append(f"File not found on disk: {filename}")
            else:
                try:
                    content = file_path.read_bytes()
                    if len(content) == 0:
                        item_errors.append(f"File is empty (0 bytes): {filename}")
                    elif not content.startswith(b"%PDF-"):
                        item_errors.append(f"File missing %PDF- header: {filename}")
                    elif b"%%EOF" not in content[-200:]:
                        item_errors.append(f"File missing %%EOF trailer marker: {filename}")
                    else:
                        actual_pages = content.count(b"/Type /Page\n") + content.count(b"/Type /Page ")
                        expected_pages = item.get("page_count")
                        if isinstance(expected_pages, int) and actual_pages != expected_pages:
                            item_errors.append(f"Page count mismatch: manifest says {expected_pages}, PDF has {actual_pages} page(s)")
                except Exception as e:
                    item_errors.append(f"Error reading file {filename}: {e}")

        # Privacy verification: Check title and notes for sensitive phone numbers
        notes_and_title = f"{item.get('expected_title', '')} {item.get('edge_case_notes', '')}"
        if re.search(r"\b[6-9]\d{9}\b", notes_and_title):
            item_errors.append("Potential sensitive personal phone number detected!")

        notice_type = item.get("notice_type")
        if notice_type not in ALLOWED_NOTICE_TYPES:
            item_errors.append(f"Invalid notice_type '{notice_type}'. Must be one of {ALLOWED_NOTICE_TYPES}")
        else:
            if notice_type == "digital":
                digital_count += 1
            elif notice_type == "scanned":
                scanned_count += 1
            elif notice_type == "mixed":
                mixed_count += 1

        is_scanned = item.get("is_scanned")
        if not isinstance(is_scanned, bool):
            item_errors.append(f"Missing or invalid is_scanned: '{is_scanned}'. Must be boolean.")
        elif notice_type == "scanned" and not is_scanned:
            item_errors.append("Inconsistent is_scanned: notice_type is 'scanned' but is_scanned is False.")
        elif notice_type == "digital" and is_scanned:
            item_errors.append("Inconsistent is_scanned: notice_type is 'digital' but is_scanned is True.")

        category = item.get("expected_category")
        if not category or category not in ALLOWED_CATEGORIES:
            item_errors.append(f"Invalid expected_category '{category}'. Must be one of {ALLOWED_CATEGORIES}")

        notice_date = item.get("expected_notice_date")
        if not notice_date or not validate_iso_date(str(notice_date)):
            item_errors.append(f"Invalid expected_notice_date: '{notice_date}'. Must be valid YYYY-MM-DD.")

        deadline = item.get("expected_deadline_date")
        if deadline is not None and not validate_iso_date(str(deadline)):
            item_errors.append(f"Invalid expected_deadline_date: '{deadline}'. Must be valid YYYY-MM-DD or null.")

        audience = item.get("expected_audience")
        if audience not in ALLOWED_AUDIENCES:
            item_errors.append(f"Invalid expected_audience: '{audience}'. Must be one of {ALLOWED_AUDIENCES}")

        page_count = item.get("page_count")
        if not isinstance(page_count, int) or page_count <= 0:
            item_errors.append(f"Invalid page_count: '{page_count}'. Must be positive integer.")

        expected_title = item.get("expected_title")
        if not expected_title or not isinstance(expected_title, str):
            item_errors.append("Missing or empty expected_title")

        status_str = "OK" if not item_errors else f"FAIL ({len(item_errors)} issue(s))"
        print(f"{idx:<3} | {filename:<38} | {str(notice_type):<8} | {str(page_count):<5} | {str(notice_date):<10} | {status_str}")

        if item_errors:
            for err in item_errors:
                print(f"      -> [FAIL] {err}")
            errors.extend([f"[{filename}] {e}" for e in item_errors])

    print("-" * 80)
    print("\nBenchmark Dataset Summary:")
    print(f"  • Total notices in manifest : {len(manifest)}")
    print(f"  • Digital notices           : {digital_count}")
    print(f"  • Scanned notices           : {scanned_count}")
    print(f"  • Mixed notices             : {mixed_count}")
    print(f"  • Target range (15-20)      : {'PASS' if 15 <= len(manifest) <= 25 else 'WARNING: Should be 15-20'}")

    if errors:
        print("\n" + "!" * 80)
        print(f"[FAILED] Verification failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        print("!" * 80)
        return False

    print("\n[SUCCESS] Manifest schema and all files verified successfully!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = verify_manifest()
    sys.exit(0 if success else 1)
