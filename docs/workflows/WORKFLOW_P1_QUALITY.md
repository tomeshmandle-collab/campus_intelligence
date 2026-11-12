# Team Workflow & AI Prompting Playbook — P1: Quality & Test Assets

**Role:** P1 — Quality and Test Assets  
**Primary Focus:** Test dataset creation, notice sample collection, test verification scripts, security isolation testing, bug reporting, and pilot regression validation.  
**Boundaries:** Work strictly within `tests/` and test asset documentation. Do not alter backend production code, Supabase policies, or frontend UI components.  
**Reference Document:** Refer to [docs/MASTER_PROJECT_ISSUES.md](file:///c:/Users/tomes/OneDrive/Desktop/campus_intelligence/docs/MASTER_PROJECT_ISSUES.md) for full issue specifications.

---

## 1. General Rules for Working with Git

Before you begin any task:
1. Make sure your local repository is on `main` and up to date:
   ```bash
   git switch main
   git pull origin main
   ```
2. Create your dedicated branch for the issue:
   ```bash
   git switch -c <branch-name>
   ```
3. Never work directly on `main`. Never commit `.env` or sensitive personal information.
4. When finished, push your branch and open a Pull Request (PR) on GitHub tagging `@ProjectLead`.

---

## 2. Complete Issue Sequence & Step-by-Step AI Prompts for P1

---

### Issue P1-1 (Phase 1): Representative College Notice Test Dataset & Ground Truth Manifest
- **Branch Name:** `test/sample-notices-dataset`
- **Working Directory:** `tests/fixtures/sample_notices/`
- **Prerequisites:** Git setup, repository cloned.
- **Scope:** Collect 15–20 representative college notice PDFs and create the ground truth manifest.

#### 🔹 Prompt 1: Manifest Structure & Schema Validator
> "I am working as P1 (Quality and Test Assets) on CAI Campus Intelligence. Read `docs/MODULES.md` (M12 Quality & Test Assets) and `docs/TESTING_STRATEGY.md`. 
> In `tests/fixtures/sample_notices/manifest.json`, create a ground-truth JSON structure for a benchmark dataset of 15–20 college notices. Each item must specify:
> - `filename`: e.g., 'notice_01_admissions_deadline.pdf'
> - `notice_type`: 'digital' | 'scanned' | 'mixed'
> - `page_count`: integer
> - `expected_title`: string
> - `expected_notice_date`: 'YYYY-MM-DD'
> - `expected_deadline_date`: 'YYYY-MM-DD' or null
> - `expected_audience`: 'student' | 'faculty' | 'staff' | 'all' | 'unspecified'
> - `expected_category`: 'Admissions' | 'Exams' | 'General' | 'Scholarships'
> - `edge_case_notes`: notes on tables, multiple dates, or amendments.
> Ensure no sensitive personal student data (phones, roll numbers) is included."

#### 🔹 Prompt 2: Manifest Verification Script
> "In `tests/scripts/verify_manifest.py`, write a standalone Python script to validate `tests/fixtures/sample_notices/manifest.json`.
> The script should:
> 1. Check that every `filename` listed in the manifest actually exists inside `tests/fixtures/sample_notices/`.
> 2. Validate that `expected_notice_date` adheres to 'YYYY-MM-DD' ISO format.
> 3. Verify that `expected_audience` is strictly one of ['student', 'faculty', 'staff', 'all', 'unspecified'].
> 4. Print a clean summary table of total digital vs scanned notices and return exit code 0 on success, 1 on failure."

---

### Issue P1-2 (Phase 2): Automated Text Extraction & OCR Benchmark Evaluation Suite
- **Branch Name:** `test/extraction-ocr-benchmarks`
- **Working Directory:** `tests/`
- **Prerequisites:** Issue P1-1 merged; backend PDF extractor service implemented.
- **Scope:** Benchmark extraction accuracy and OCR recall on digital and scanned notices.

#### 🔹 Prompt 1: Extraction Evaluation Script
> "Read `docs/TESTING_STRATEGY.md`. In `tests/scripts/eval_extraction.py`, create a benchmark script that runs the backend PDF extraction service against each sample notice in `tests/fixtures/sample_notices/manifest.json`.
> - Check page count preservation (did 3-page PDF yield exactly 3 page records?).
> - Check scanned notice detection (is `is_scanned` accurately flagged for scanned samples?).
> - Check text completeness: verify that key expected keywords from `expected_title` appear in extracted text.
> - Output results to `tests/reports/extraction_benchmark.json` with overall pass/fail metrics."

---

### Issue P1-3 (Phase 2): End-to-End Ingestion Pipeline Verification & Failure Simulation
- **Branch Name:** `test/ingestion-pipeline-e2e`
- **Working Directory:** `tests/e2e/`
- **Prerequisites:** Backend ingestion pipeline running.
- **Scope:** Pytest test suite asserting pipeline hold/publish criteria on edge cases.

#### 🔹 Prompt 1: Pipeline E2E Test Suite
> "Read `docs/SYSTEM_ARCHITECTURE.md` Section 4 and `docs/MODULES.md` M06. In `tests/e2e/test_notice_ingestion.py`, write Pytest tests using `TestClient` from FastAPI to simulate:
> 1. Valid digital notice upload: verify it is processed and published (or held for review if confidence low).
> 2. Edge Case A (Conflicting dates): Notice where deadline is before notice date. Assert that notice is placed in `held` status with `review_reasons` containing 'deadline_prior_to_notice_date'.
> 3. Edge Case B (Corrupted file): Upload a file with `.pdf` extension but random binary content. Assert backend returns 400 Bad Request indicating invalid PDF header.
> 4. Edge Case C (Oversized file): Upload a file > 10MB. Assert backend returns 413 Payload Too Large."

---

### Issue P1-4 (Phase 3): Public Data Leakage & Security Boundary Test Suite
- **Branch Name:** `test/public-data-isolation`
- **Working Directory:** `tests/security/`
- **Prerequisites:** Public notice and uploader endpoints implemented.
- **Scope:** Security test suite asserting that held, draft, and withdrawn notices never leak to public visitors.

#### 🔹 Prompt 1: Public Isolation Security Tests
> "Read `docs/API_CONTRACTS.md` Section 4 and `AGENTS.md` Section 8. In `tests/security/test_public_isolation.py`, write automated security tests verifying:
> 1. Direct ID access to held notice: `GET /api/v1/notices/{held_id}` must return 404 Not Found.
> 2. Direct ID access to withdrawn notice: `GET /api/v1/notices/{withdrawn_id}` must return 404 Not Found.
> 3. Public notice feed: `GET /api/v1/notices` must never contain any notice with `publication_status != 'published'`.
> 4. Response field sanitization: Assert public notice JSON omits `storage_path`, `review_reasons`, and uploader profile details.
> 5. Uploader route protection: Requesting `GET /api/v1/uploader/review-queue` without auth token returns 401 Unauthorized."

---

### Issue P1-5 (Phase 5): Pilot Validation Dataset, Defect Log & Release Acceptance Checklist
- **Branch Name:** `test/pilot-release-checklist`
- **Working Directory:** `tests/reports/`
- **Prerequisites:** All phases integrated.
- **Scope:** Full pilot evaluation report and release readiness checklist.

#### 🔹 Prompt 1: Pilot Evaluation Report Generator & Checklist
> "Read `docs/PHASE.md` Phase 5 Exit Gate. In `tests/reports/PILOT_EVALUATION_REPORT.md`, create an evaluation report template documenting:
> 1. Evaluation summary: Total notices tested, extraction success rate, OCR pass rate, auto-publish accuracy.
> 2. Grounded Q&A evaluation: Number of answerable queries answered accurately with valid page citations; number of out-of-scope queries flagged as 'not_found' (zero hallucinations).
> 3. Defect severity tracking table (P0 Blocker, P1 Critical, P2 Moderate, P3 Minor).
> 4. Step-by-step manual demo script for project presentation day."

---

## 3. Pre-PR Submission Checklist for P1
- [ ] Run test scripts locally:
  ```bash
  python tests/scripts/verify_manifest.py
  pytest tests/
  ```
- [ ] Verify zero `.env` or personal data committed: `git status`
- [ ] Push branch: `git push -u origin <branch-name>`
- [ ] Open PR tagging `@ProjectLead`.
