# Sample College Notices Test Dataset (Benchmark M12)

This directory contains the representative college notice benchmark dataset for **CAI Campus Intelligence**, maintained by **P1 (Quality & Test Assets)** under Module **M12**.

## Dataset Specifications

- **Total Notices:** 16
- **Digital PDFs:** 12 (single-page, multi-page, tables, amended deadlines)
- **Scanned PDFs:** 4 (official orders, circulars, tenders)
- **Target Audiences:** `student`, `faculty`, `staff`, `all`, `unspecified`
- **Categories:** `Admissions`, `Exams`, `General`, `Scholarships`

## Privacy & Ethics Compliance

As required by `AGENTS.md` and `TESTING_STRATEGY.md`:
- **Zero Sensitive Personal Data:** No student personal phone numbers, Aadhaar numbers, personal emails, or home addresses are contained in these test fixtures.
- All samples represent official college administrative announcements.

## Manifest Structure

Ground truth facts for all sample notices are recorded in `manifest.json`. Each entry defines:
- `filename`: PDF filename
- `notice_type`: `'digital'` | `'scanned'` | `'mixed'`
- `is_scanned`: boolean flag
- `page_count`: total pages
- `expected_title`: ground truth title
- `expected_notice_date`: ISO format `YYYY-MM-DD`
- `expected_deadline_date`: ISO format `YYYY-MM-DD` or `null`
- `expected_audience`: strictly one of `['student', 'faculty', 'staff', 'all', 'unspecified']`
- `expected_category`: category classification
- `edge_case_notes`: specific testing nuances (e.g. multi-page tables, amended deadlines)

## Verification

To verify the integrity of the manifest and sample files:

```bash
python tests/scripts/verify_manifest.py
```
Exit code `0` indicates 100% compliance with benchmark criteria.
