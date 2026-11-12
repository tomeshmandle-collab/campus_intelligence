# CAI Campus Intelligence — Technology Stack

**Version:** 1.0  
**Status:** Implementation baseline  
**Companion document:** `PRD.md`  
**Last updated:** 12 November 2026

> This document records the selected baseline and the constraints around it. It is not evidence that the repository, services, or deployment have already been configured. Inspect the existing repository and provider accounts before making changes.

---

## 1. Technical goals and constraints

The stack is intended for:
- a small student team with mixed technical experience;
- an MVP that can be developed and maintained without a large operations burden;
- code-assisted development, with human review of generated changes;
- a modest pilot using free or low-cost service tiers where practical;
- Gemini for AI-assisted extraction and question answering;
- a modular application that can evolve without premature microservices.

The stack should favor documented, widely used tools and minimize the number of services the team must operate.

## 2. Stack at a glance

| Layer | Baseline choice | Notes |
|---|---|---|
| Frontend | React + TypeScript + Vite | One frontend application for public and uploader routes |
| Styling | Tailwind CSS | Use a consistent component and token approach; avoid introducing multiple styling systems |
| Frontend hosting | Static hosting; choose one provider for the pilot | Vercel or Cloudflare Pages are candidates; confirm account, limits, and deployment workflow |
| Backend API | Python + FastAPI | Modular monolith; REST-style JSON API |
| Backend hosting | Render is the current candidate | Confirm free-tier behavior, runtime limits, and deployment settings before relying on it |
| Database | Supabase PostgreSQL | Relational source of truth for notices and workflow records |
| Authentication | Supabase Auth | Invite/admin-provisioned uploader accounts; public sign-up disabled |
| File storage | Supabase Storage | Private bucket for original files |
| PDF text extraction | PyMuPDF | Page-aware extraction for digital PDFs |
| OCR | Gemini multimodal processing as a limited, optional path | Best-effort for supported scanned pages; not a universal guarantee |
| AI provider | Gemini API, called from backend only | Structured extraction, summaries, and grounded answer generation |
| Keyword search | PostgreSQL full-text search plus exact metadata matching | Baseline MVP search |
| Semantic search | Not required for baseline | Consider pgvector and embeddings only after a measured need and a separate decision |
| Background processing | FastAPI background tasks with persisted database state for the pilot | Keep tasks bounded; document restart/recovery limitations |
| Tests | Pytest for backend; frontend test tooling selected from existing repo | Prefer existing repository tools over adding alternatives |
| Version control and collaboration | Git and GitHub | Issues, branches, pull requests, and reviewed integration |

Provider model names, pricing, quotas, and free-tier limits can change. Verify them when configuring the actual environment; do not hard-code a model name or quota assumption into general project documentation.

## 3. Application shape

Use a **modular monolith** for the MVP:

- one React + TypeScript frontend application;
- one FastAPI backend application;
- one Supabase PostgreSQL database;
- one private Supabase Storage bucket for original notice files;
- Supabase Auth for uploader identity;
- Gemini API calls made only by backend services.

The public and uploader experiences may be separate route groups within the same frontend. They do not need separate deployments for the MVP.

Do not introduce microservices, a message broker, a separate search platform, a cache, or container orchestration unless a measured requirement justifies the operational cost.

## 4. Frontend

### Baseline
- React
- TypeScript
- Vite
- Tailwind CSS

### Responsibilities
- Public home briefing, filters, notice list/detail, search, and Ask interface.
- Uploader sign-in experience, upload interface, processing status, review queue, and correction forms.
- Responsive and accessible user interactions.
- API communication through a shared typed API client.

### Rules
- Do not call Gemini from browser code.
- Do not put Supabase service-role credentials or other privileged secrets in frontend environment variables.
- The frontend may use the approved Supabase Auth client flow for sign-in/session handling, but all protected business actions must be authorized by the backend.
- Do not rely on hiding buttons or protected routes as a security control.
- Keep API request/response types in a shared, documented location and align them with `API_CONTRACTS.md`.
- Use mock fixtures only when clearly separated from production API code and shaped like the agreed contract.

## 5. Backend

### Baseline
- Python
- FastAPI
- Pydantic models for request validation and structured internal/API data.

### Responsibilities
- Expose the application API.
- Verify authentication and enforce authorization.
- Validate uploads and file metadata.
- Store and retrieve files through controlled storage access.
- Orchestrate text extraction, optional OCR, Gemini calls, validation, publication, and retry behavior.
- Maintain notice, processing, correction, and relationship records.
- Implement keyword search and grounded question answering.
- Apply rate limits and safe error handling.

### Rules
- Keep provider-specific code behind service functions/modules.
- Configure FastAPI custom exception handlers (`RequestValidationError`, `StarletteHTTPException`) to format all validation errors and HTTP exceptions using the standardized `{ "error": { "code", "message", "details", "request_id" } }` schema defined in `API_CONTRACTS.md` §3.6.
- Validate all AI-generated structured output before persistence or publication.
- Never trust role, publication status, or other privileged fields supplied by the browser.
- Return safe error messages; log diagnostic details server-side without logging secrets or unnecessary personal information.
- Make processing steps idempotent where practical so a retry does not create duplicate notices or corrupt history.

## 6. Database and authentication

### Supabase PostgreSQL
Use PostgreSQL as the source of truth for:
- notice metadata and lifecycle state;
- audience targets, dates, action items, and relationships;
- page-aware text chunks and keyword-search data;
- field-source evidence;
- processing runs/events;
- human corrections and public error reports.

The detailed schema belongs in `DATABASE_SCHEMA.md`. Do not independently invent tables or columns in a feature branch; propose schema changes and update the schema/API documents together.

### Supabase Auth
- Public viewers do not need accounts.
- Uploader accounts are provisioned by an administrator or approved invite process.
- Public self-registration is disabled for the pilot.
- The backend verifies the Supabase access token and then checks the user's application role/permission.
- Authentication and authorization are separate checks.

### Row-level security and grants
- All application data access goes through the FastAPI backend; the browser does not query application tables directly, so Supabase `anon` and `authenticated` roles hold no direct grants on application tables.
- Enable RLS on every application table exposed through Supabase APIs.
- Define explicit policies for the intended access paths (see `DATABASE_SCHEMA.md`).
- Internal processing, audit, profile, and correction data must not be publicly readable.
- Review effective table grants as well as RLS policies; the absence of an RLS policy alone is not a complete security design.
- Use the service-role key only on the backend, in a controlled environment.
- Do not expose the service-role key to the frontend.

## 7. File handling and document extraction

### Original-file storage
- Store originals in a private Supabase Storage bucket.
- Keep a stable storage path and metadata in the database.
- Do not overwrite the original when extracted fields are corrected.
- Public access to an original is granted only after publication and only through the approved access mechanism, such as a short-lived signed URL or backend-mediated download.
- Validate file size, declared MIME type, actual file signature where practical, and allowed extensions.
- Define file-size, page-count, and batch limits in configuration before the pilot.

### Digital PDF extraction
Use PyMuPDF to:
- read PDF pages;
- extract text page by page;
- preserve page numbers;
- identify pages with little or no extractable text;
- report malformed or unreadable files.

Do not flatten the entire PDF into one undifferentiated string. Page context is required for evidence and citations.

### OCR
OCR is a limited pilot capability, not a promise that all scanned files will work.

- Attempt OCR only for pages that lack usable text and only when the configured Gemini model/API supports the required input.
- Keep page identity and source association.
- Apply size/page limits and provider quota handling.
- Treat OCR output as extracted text that still requires validation.
- If OCR is unavailable, fails, or produces uncertain text, hold the notice for review.
- Do not silently publish a notice based on incomplete OCR.

A dedicated local OCR engine is not part of the baseline. It may be evaluated later if the pilot demonstrates a need and the hosting environment can support it reliably.

## 8. AI provider integration

Use Gemini through backend-only service modules using the official Google GenAI SDK (`google-genai`). Pin dependencies and configuration explicitly.

Initial use cases:
1. Extract structured notice fields from page-aware text.
2. Produce a concise summary.
3. Generate an answer from retrieved published notice passages.

### Required controls
- Keep API keys in backend environment variables or the approved secret manager.
- Use structured output/schema validation where supported.
- Treat model output as untrusted.
- Validate every date, category, audience, relationship, and source reference in backend logic.
- Require supporting source evidence for critical extracted fields.
- Never use model-reported confidence as the only publication decision.
- Bound input size and output size.
- Handle rate limits, timeouts, malformed responses, and provider outages.
- Do not send unpublished or held notice content to public Ask requests.
- Keep prompts and provider-specific request logic out of frontend code.

Model names, supported input formats, rate limits, and pricing must be checked during implementation. Record the selected model and relevant configuration in the project environment documentation or a decision record.

## 9. Search and question answering

### Baseline keyword search
Use PostgreSQL full-text search over relevant notice metadata and extracted text, with exact matching for fields such as reference numbers where useful.

Search must:
- return only published, public-safe notices;
- apply audience/category/date filters consistently;
- provide relevant excerpts and page references when available;
- label changed notices accurately, including superseded and cancelled ones, and never present them as current;
- exclude withdrawn notices entirely.

### Semantic search
Semantic/vector search is not required to complete the baseline MVP. Do not make embeddings or pgvector a prerequisite for the first keyword-search implementation.

If keyword search is insufficient after testing:
1. document the observed limitation;
2. propose a semantic-search enhancement;
3. select and verify an embedding model and vector dimension;
4. update the schema and API contracts;
5. implement and evaluate it against the same test set.

### Ask
- Retrieve evidence from published notices using the baseline search/retrieval layer.
- Pass only the relevant evidence and question to Gemini.
- Require the answer to stay within the supplied evidence.
- Verify citations against the retrieved passages.
- Return a clear not-found/uncertain response when evidence is insufficient.

## 10. Background processing and recovery

For the pilot, FastAPI background tasks may be used to start bounded processing after a successful upload, with each job's state persisted in PostgreSQL.

This is a deliberately simple pilot approach, not a durable distributed job queue. In-process tasks can be interrupted if the web process restarts or is recycled.

Minimum safeguards:
- Create the notice and processing record before reporting the upload as accepted.
- Persist processing status and stage changes.
- Make processing steps safe to retry where practical.
- Record errors and timestamps.
- On service startup or through an explicit recovery operation, identify records left in a stale `processing` state and mark them failed/retryable or return them to a controlled queue.
- Expose processing status to authorized uploaders.
- Do not claim that a job completed unless its final database update succeeded.

If pilot volume or reliability requirements exceed this approach, evaluate a durable worker/queue separately. Do not add it pre-emptively.

## 11. Security baseline

- Store secrets only in backend environment variables or an approved secret store.
- Commit `.env.example` with variable names and safe placeholders, never real values.
- Keep `.env` and local credential files out of Git.
- Enforce authorization on every protected backend route.
- Enable and test RLS and effective grants for all relevant database tables.
- Keep original files private by default.
- Use short-lived access links or backend-mediated access for published originals.
- Validate uploads and treat documents as untrusted input.
- Escape extracted text before rendering.
- Protect public Ask and report routes with rate limits and input limits.
- Avoid logging access tokens, API keys, or unnecessary personal data.
- Separate development and production credentials and data where practical.

## 12. Environments and deployment

Maintain, at minimum:
- **Local development:** local frontend/backend with development credentials and test data.
- **Pilot/production:** deployed frontend/backend with restricted credentials and approved notice data.

The hosting candidates are:
- Frontend: Vercel or Cloudflare Pages.
- Backend: Render.

These are candidates until the Project Lead confirms the actual provider, account ownership, environment variables, build commands, CORS configuration, and deployment process.

Before the public pilot:
- verify provider free-tier limits and sleeping/idle behavior;
- test cold-start and error behavior;
- confirm database and storage limits;
- configure allowed frontend origins;
- verify secret handling;
- test migrations and backup/recovery expectations;
- run the acceptance test set against the deployed environment.

Do not depend on an undocumented keep-alive workaround to make the service appear continuously available.

## 13. Suggested repository layout

Adapt this layout to the repository that actually exists. Do not reorganize an existing codebase merely to match this example.

```text
/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   └── types/
│   └── ...
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── pipeline/
│   └── tests/
├── supabase/
│   └── migrations/
├── docs/
│   ├── PRD.md
│   ├── TECH_STACK.md
│   ├── SYSTEM_ARCHITECTURE.md
│   └── ...
├── testdata/
├── .env.example
└── README.md
```

The actual directory names may differ. The important rule is to keep API routes, business logic, provider integrations, and document-processing steps understandable and separated.

## 14. Dependencies and version policy

- Use supported stable releases at implementation time.
- Prefer the package manager and lockfile already present in the repository.
- Commit dependency lockfiles.
- Avoid adding a package for functionality already provided by the selected stack.
- Pin or constrain versions according to the ecosystem's standard practice.
- Record major dependency changes in the relevant pull request.
- Do not copy outdated model names, API parameters, or free-tier limits from this document into code without checking current provider documentation.

## 15. Technical decisions that require a recorded update

The baseline stack is established, but these operational details must be recorded when selected:

- exact Gemini model names and generation settings;
- provider quotas and rate limits relevant to the pilot;
- frontend and backend hosting providers;
- file-size, page-count, and batch limits;
- exact OCR enablement and supported formats;
- whether semantic search is justified after keyword-search evaluation;
- embedding model/dimension if semantic search is later approved;
- background-job recovery behavior in the deployed environment;
- production secret ownership and backup/recovery process.

A decision that changes the database, API, security model, or user-visible behavior must update the corresponding documents in the same planned change.

## 16. Maintenance

**Technical owner:** Project Lead / Technical Lead, with input from contributors responsible for affected modules.

Update this document when the selected stack, provider, deployment topology, processing approach, security model, or major dependency changes.

**End of document.**
