# Project Lead Workflow & Foundation Playbook

**Role:** Project Lead / Technical Lead  
**Primary Focus:** Project scaffolding, technical baseline, Supabase configuration, database migrations, backend API pipeline, AI orchestration, security/secrets enforcement, and PR integration.  
**Boundaries:** You maintain the architecture, security policies, and merge reviews. Avoid building all UI yourself—delegate bounded tasks to teammates.  
**Reference Document:** Refer to [docs/MASTER_PROJECT_ISSUES.md](file:///c:/Users/tomes/OneDrive/Desktop/campus_intelligence/docs/MASTER_PROJECT_ISSUES.md) for full issue prerequisites and deliverables.

---

## 1. Local Git & Project Scaffolding Baseline (Phase 0 & 1)

### Step A: Initialize Git Repository
```bash
git init
git branch -M main
```

### Step B: Standard `.gitignore`
Create a clean `.gitignore` at the root ignoring:
- `.env`, `.env.local`, `*.env`
- `node_modules/`, `dist/`, `.vite/`
- `__pycache__/`, `*.pyc`, `.pytest_cache/`, `venv/`, `.venv/`
- `.DS_Store`, `Thumbs.db`

### Step C: Directory Scaffolding Structure
```
campus_intelligence/
├── docs/                      # Canonical project documentation
│   ├── MASTER_PROJECT_ISSUES.md # Complete 28-issue catalog
│   └── workflows/             # Teammate prompt & workflow playbooks
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints (health, notices, uploader, search, ask)
│   │   ├── core/              # Config, security, logging
│   │   ├── models/            # SQLAlchemy / Supabase models
│   │   ├── schemas/           # Pydantic schemas matching API_CONTRACTS.md
│   │   └── services/          # Extraction, OCR, AI validation, search, QA
│   ├── migrations/            # SQL migration scripts
│   ├── tests/                 # Pytest test cases
│   ├── requirements.txt       # Python dependencies
│   └── main.py                # FastAPI entrypoint
├── frontend/                  # React + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── components/        # Layout, NoticeCard, Dropzone, Search, Modals
│   │   ├── pages/             # Public & Admin pages
│   │   ├── context/           # Auth and App contexts
│   │   ├── types/             # Shared TypeScript models
│   │   └── mocks/             # Contract-aligned mock data
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   ├── fixtures/              # Sample notices & QA evaluation sets
│   ├── reports/               # Test benchmark and release reports
│   └── scripts/               # Validation and check scripts
└── README.md
```

---

## 2. Complete Issue Sequence & Step-by-Step AI Prompts for Project Lead

---

### Issue L-1 (Phase 1): Project Scaffolding, Base Config & Health Check API
- **Branch:** `setup/project-scaffold`
- **Requirements:** FastAPI backend on port 8000 + React/Vite on port 5173 + root `.gitignore`.

#### 🔹 Prompt 1: FastAPI Base Skeleton
> "Read `docs/TECH_STACK.md` and `docs/API_CONTRACTS.md`. In `backend/`, create a clean FastAPI application skeleton. In `backend/app/main.py`, configure CORS for `http://localhost:5173`, request validation error handlers, and a GET `/api/v1/health` endpoint returning `{\"status\": \"healthy\", \"timestamp\": \"...\", \"version\": \"1.0.0\"}`. Provide `backend/requirements.txt` with fastapi, uvicorn, pydantic, python-dotenv, and pytest."

#### 🔹 Prompt 2: Vite React Tailwind Frontend Setup
> "In `frontend/`, configure a minimal React 18 + TypeScript + Vite project with Tailwind CSS installed. Ensure `vite.config.ts` has path aliases (`@/` -> `src/`). Add an Axios/Fetch API client in `src/services/api.ts` configured with `VITE_API_BASE_URL` pointing to `http://localhost:8000/api/v1`."

---

### Issue L-2 (Phase 1): Environment Variables, Secrets & Configuration Loader
- **Branch:** `setup/env-config-baseline`
- **Requirements:** Safe `.env.example` templates + Pydantic settings loader. No secrets committed.

#### 🔹 Prompt 1: Backend Environment Configuration Loader
> "Read `docs/CODING_GUIDELINES.md` and `AGENTS.md` Section 8. In `backend/app/core/config.py`, create a `pydantic-settings` `Settings` class that loads:
> - `PROJECT_NAME`, `ENVIRONMENT` (development/production)
> - `SUPABASE_URL`, `SUPABASE_KEY` (service role key for backend operations)
> - `GEMINI_API_KEY`
> - `MAX_UPLOAD_SIZE_BYTES` (default 10485760 = 10MB)
> - `MAX_PAGE_COUNT` (default 10)
> In `backend/.env.example`, write template dummy keys. Ensure `.env` is never tracked by git."

---

### Issue L-3 (Phase 1): Supabase Database Schema, Migrations & Row Level Security
- **Branch:** `feat/db-migrations-schema`
- **Requirements:** All 5 core tables created + RLS enabled + public direct grants revoked.

#### 🔹 Prompt 1: Initial SQL Migration DDL
> "Read `docs/DATABASE_SCHEMA.md` carefully. In `backend/migrations/001_initial_schema.sql`, write PostgreSQL DDL statements for:
> 1. `profiles` table (id references auth.users, role 'uploader'|'admin', full_name, created_at).
> 2. `notices` table with columns: `id`, `title`, `notice_date`, `deadline_date`, `audience` ('student'|'faculty'|'staff'|'all'|'unspecified'), `category`, `summary`, `storage_path`, `processing_status` ('pending'|'processing'|'completed'|'failed'), `publication_status` ('held'|'published'|'withdrawn'), `review_reasons` (jsonb), `created_at`, `updated_at`.
> 3. `notice_pages` (notice_id, page_number, extracted_text, is_scanned, created_at).
> 4. `notice_chunks` (notice_id, page_number, chunk_text, search_vector tsvector).
> 5. `notice_relationships` and `error_reports`.
> CRITICAL SECURITY: Include `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` on every single table. Include `REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;` because the browser never queries tables directly; all access is via FastAPI service role."

---

### Issue L-4 (Phase 2): File Storage Bucket & Authorized Upload Endpoint
- **Branch:** `feat/upload-endpoint-storage`
- **Requirements:** Supabase Storage private bucket + `POST /api/v1/notices/upload` validation.

#### 🔹 Prompt 1: File Upload Handler & Magic Byte Validator
> "Read `docs/API_CONTRACTS.md` Section 8.1 and `docs/MODULES.md` M04. In `backend/app/api/v1/uploader.py`, implement `POST /api/v1/notices/upload`.
> 1. Enforce uploader authentication dependency.
> 2. Accept `file: UploadFile`. Check magic bytes: the first 5 bytes must be `%PDF-`.
> 3. Check file size (max 10MB).
> 4. Generate a UUID storage path: `originals/{uuid}.pdf`.
> 5. Upload to Supabase Storage private bucket `notice-originals`.
> 6. Insert row into `notices` with status `pending`, `held`.
> 7. Return `202 Accepted` with `{ "notice_id": "...", "status": "pending" }`."

---

### Issue L-5 (Phase 2): Page-Aware Digital PDF Extraction & Scanned Notice OCR Path
- **Phase:** Phase 2
- **Branch:** `feat/text-extraction-ocr`
- **Requirements:** PyMuPDF page-by-page extraction + fallback OCR for scanned pages.

#### 🔹 Prompt 1: PDF Extractor Service
> "Read `docs/SYSTEM_ARCHITECTURE.md` Section 4. In `backend/app/services/extraction/pdf_extractor.py`, implement `extract_pdf_pages(file_bytes: bytes) -> list[ExtractedPage]`.
> - Use PyMuPDF (`fitz`).
> - Loop through each page, recording `page_number` (starting at 1) and raw text.
> - If a page has < 50 characters, mark `is_scanned = True`.
> - For scanned pages, call Gemini multimodal vision endpoint to perform OCR. If OCR fails or exceeds timeout, catch exception, mark text as empty, and set `ocr_failed = True`.
> - Save records into `notice_pages` table."

---

### Issue L-6 (Phase 2): Gemini Structured Extraction & Publication Rules Engine
- **Branch:** `feat/gemini-ai-extraction`
- **Requirements:** Gemini backend prompt with structured Pydantic schema + business rule validation.

#### 🔹 Prompt 1: Structured AI Extractor & Rules Engine
> "Read `docs/MODULES.md` M06. In `backend/app/services/ai/gemini_extractor.py`, implement structured notice extraction using the Gemini API.
> - Pass page-indexed text to Gemini.
> - Output Schema: Pydantic model with `title`, `notice_date`, `deadline_date`, `audience`, `category`, `summary`, and `field_evidence` (mapping field name to page number and quoted sentence).
> - Implement validation rules:
>   - Rule 1: If `deadline_date < notice_date`, hold notice (`reason: "deadline_prior_to_notice_date"`).
>   - Rule 2: If `notice_date` is missing, hold notice (`reason: "missing_notice_date"`).
>   - Rule 3: If `ocr_failed`, hold notice (`reason: "unreliable_ocr"`).
>   - Rule 4: If all pass and confidence is high, set `publication_status = 'published'`, otherwise `held`.
> Update the database notice record accordingly."

---

### Issue L-7 (Phase 2): Review Queue, Field Correction, Relationship & Publication Actions
- **Branch:** `feat/review-publication-apis`
- **Requirements:** Staff review queue + field patching + manual publish/retry endpoints.

#### 🔹 Prompt 1: Uploader Review APIs
> "Read `docs/API_CONTRACTS.md` Sections 8.3 through 8.7 and 8.12. In `backend/app/api/v1/uploader.py`, implement:
> 1. `GET /review-queue`: returns held notices with their `review_reasons`.
> 2. `GET /notices/{id}/review`: returns notice details, extracted field evidence, and page text.
> 3. `PATCH /notices/{id}/fields`: updates title, dates, audience, category with audit logging.
> 4. `POST /notices/{id}/publish`: validates that all blocking review reasons are cleared, then sets `publication_status = 'published'`.
> 5. `POST /notices/{id}/relationships/{rel_id}/confirm`: confirms relationship without modifying unapproved notices."

---

### Issue L-8 (Phase 3): Public Notice Feed, Home Briefing & Secure Original File Access
- **Branch:** `feat/public-notices-api`
- **Requirements:** Public `/notices` and `/notices/briefing` endpoints + signed URL generator. Zero held notice leaks.

#### 🔹 Prompt 1: Public Endpoints with Strict Isolation
> "Read `docs/API_CONTRACTS.md` Sections 7.2 through 7.5. In `backend/app/api/v1/notices.py`, implement:
> 1. `GET /notices`: paginated public list. Filter: strictly WHERE `publication_status = 'published'`. Support `audience` and `category` query filters.
> 2. `GET /notices/briefing`: returns top 5 upcoming deadlines and 5 newest published notices.
> 3. `GET /notices/{id}`: returns notice details, structured summary, and a short-lived Supabase Storage signed download URL (15-minute expiry). Return 404 if notice is held or withdrawn."

---

### Issue L-9 (Phase 3): Notice Management List, Withdrawal & Error-Report Resolution
- **Branch:** `feat/management-and-reports-api`
- **Requirements:** Management table endpoint + withdrawal action + error report endpoints.

#### 🔹 Prompt 1: Management & Report Handling
> "Read `docs/API_CONTRACTS.md` Sections 7.8, 8.8, 8.9, 8.10, 8.11.
> 1. `GET /api/v1/uploader/notices`: staff management list returning all notices regardless of publication status.
> 2. `POST /api/v1/uploader/notices/{id}/withdraw`: sets `publication_status = 'withdrawn'` and records `withdrawal_reason`.
> 3. `POST /api/v1/notices/{id}/reports`: public error report submission with IP rate limit.
> 4. `GET /api/v1/uploader/reports` and `PATCH /api/v1/uploader/reports/{id}`: list and resolve/dismiss error reports."

---

## 3. Pull Request Review Protocol (How you review teammates' PRs)

When any member opens a PR:
1. **Branch Hygiene & File Check:**
   - Did they stay within their designated folder boundaries?
   - Are there any `.env`, passwords, or API keys committed? Reject immediately if found!
   - Are there unapproved external libraries in `package.json` or `requirements.txt`?
2. **Local Test Execution:**
   ```bash
   git switch main
   git fetch origin
   git switch <teammate-branch>
   # If frontend:
   cd frontend && npm run build
   # If backend/tests:
   pytest
   ```
3. **Contract Adherence:** Ensure field names and payload shapes match `API_CONTRACTS.md`.
4. **Merge & Delete:** Click **Merge pull request** on GitHub, delete the remote branch, and notify the member to switch to `main` and pull.
