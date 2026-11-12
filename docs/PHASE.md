# CAI Campus Intelligence — Phase & Progress Tracker

**Version:** 1.0  
**Status:** Working implementation tracker  
**Last updated:** 2026-11-12  
**Maintainer:** Project Lead / Technical Lead

> Tracks the current phase, intended outcome, and evidence required to move forward. Individual tasks belong in GitHub Issues / Projects.

## 1. Current position

| Field | Position |
|---|---|
| Current phase | Phase 0 — Project preparation and technical readiness |
| Current stage | Project Lead preparing the implementation foundation |
| Overall status | In progress |
| Phase owner | Project Lead / Technical Lead |
| Immediate objective | Complete minimum planning and repository preparation for Phase 1 |
| Next phase | Phase 1 — Technical foundation |

### Team working approach

This is a student project with beginner team members. Phase 0 is Project Lead-led; it is not a team-wide technical examination.

1. The Project Lead owns initial technical decisions, repository inspection, and the first working baseline.
2. Team members do **not** need to read or approve every architecture, database, API, or engineering document before development starts.
3. Bring members in gradually during Phase 1 through setup, verification, sample data, documentation, and small isolated tasks.
4. Keep ownership flexible as availability and confidence change. Preserve module boundaries and shared interfaces when reassigning work.
5. The Project Lead remains accountable for integration and higher-risk work such as authorization, database changes, file handling, AI processing, and deployment.

The goal is to give each person a clear, manageable next step—not to make everyone understand the whole system immediately.

### Canonical documentation set

Use these exact unprefixed filenames. Do not reintroduce older project-prefixed filename variants.

| # | File | Purpose |
|---:|---|---|
| 1 | `PRD.md` | Product requirements, MVP scope, workflows, and non-goals |
| 2 | `TECH_STACK.md` | Technology baseline |
| 3 | `SYSTEM_ARCHITECTURE.md` | Components and data flow |
| 4 | `DATABASE_SCHEMA.md` | Data model and persistence rules |
| 5 | `API_CONTRACTS.md` | Backend interfaces |
| 6 | `MODULES.md` | Module boundaries and dependencies |
| 7 | `DEVELOPMENT_OWNERSHIP.md` | Initial and flexible team responsibilities |
| 8 | `PHASE.md` | Phase outcomes and exit criteria |
| 9 | `GITHUB_ROADMAP.md` | Suggested GitHub epics and tasks |
| 10 | `CODING_GUIDELINES.md` | Coding conventions |
| 11 | `GIT_WORKFLOW.md` | Branch, commit, PR, and merge workflow |
| 12 | `TESTING_STRATEGY.md` | Test strategy and quality expectations |
| 13 | `AGENTS.md` | Instructions for AI coding agents |

Document preparation is not implementation status. Verify actual repository placement and commits separately.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Not started | Work has not begun |
| In progress | Work is active |
| Ready | Inputs and dependencies are clear |
| Blocked | A dependency or decision prevents progress |
| Complete | Expected result exists and has been checked |
| Deferred | Intentionally moved to a later phase |

Resolve decisions when the next implementation step depends on them; do not finalize every future detail before starting.

## 3. Overall phase roadmap

| Phase | Name | Main outcome |
|---|---|---|
| 0 | Project preparation and technical readiness | Project Lead is ready to begin implementation |
| 1 | Technical foundation | Reproducible frontend/backend setup, database, migrations, and authorization foundation |
| 2 | Manual upload and notice-processing pipeline | Uploaded notice is processed, validated, and published or held |
| 3 | Public notice experience | Public users browse and inspect published notices |
| 4 | Search and Ask | Search and evidence-grounded answers with citations |
| 5 | Integration, pilot, and quality hardening | End-to-end MVP tested with representative notices |

Phases 3 and 4 may overlap once data and public API foundations are stable. Parallel work must use agreed interfaces, not guessed contracts.

## 4. Phase 0 — Project preparation and technical readiness

**Goal:** Prepare a clear, safe starting point. The Project Lead owns this phase; full-team technical review is not a prerequisite.

### Stage tracker

| Stage | Expected result | Planning snapshot | Notes |
|---|---|---|---|
| 0.1 Product scope | MVP and non-goals documented | Complete | Protect agreed MVP boundary |
| 0.2 Initial ownership | Responsibilities and module boundaries documented | Complete | Assignments remain flexible |
| 0.3 Architecture baseline | Components and data flow documented | Complete | Refine when implementation gives a real reason |
| 0.4 Initial contracts | API and data expectations documented | Complete | Finalize each interface before dependent work |
| 0.5 Module breakdown | Scope and dependencies documented | Complete | Delegation reference |
| 0.6 Implementation roadmap | First tasks identified | In progress | Prepare small Phase 1 issues |
| 0.7 Working conventions | Coding, Git, and testing practices documented | Complete | Introduce when relevant |
| 0.8 Agent instructions | `AGENTS.md` prepared | Complete | Verify root placement |
| 0.9 Repository preparation | Existing repository inspected and docs placed safely | Not verified | Do not overwrite existing work |
| 0.10 Phase 1 starter plan | First tasks and checks ready | In progress | Lead establishes baseline, then delegates |

These are planning statuses, not claims about the current repository. Verify before updating them.

### Milestones

| Milestone | Completion evidence |
|---|---|
| M0-A — Project plan drafted | Canonical 13-document set exists and has been checked |
| M0-B — Technical direction established | Project Lead understands baseline and records remaining implementation-specific unknowns |
| M0-C — Repository prepared | Existing repo inspected; docs and `AGENTS.md` placed appropriately |
| M0-D — Phase 1 tasks prepared | Small, ordered, owned tasks with verification steps |
| M0-E — Phase 1 ready | Project Lead confirms exit criteria |

### Phase 0 exit criteria

- [ ] MVP purpose, workflows, and non-goals are documented.
- [ ] Manual upload by a verified person is the MVP ingestion boundary; scraping/crawling is out of scope.
- [ ] Initial module boundaries and flexible ownership are documented.
- [ ] Architecture, stack, database, and API baselines are available and sufficiently consistent.
- [ ] Coding, Git, testing, and AI-agent instructions exist.
- [ ] Existing repository has been inspected before structural changes.
- [ ] Canonical documents are placed sensibly and committed, or a deliberate placement plan is recorded.
- [ ] First Phase 1 tasks are ordered, scoped, owned, and verifiable.
- [ ] Project Lead can begin the foundation without waiting for a full-team technical review.

**Not required:** every member reading all documents; team-wide approval of technical designs; every future decision being finalized; or every member already knowing the stack.

Team onboarding happens gradually during Phase 1 through a short overview and manageable, task-specific instructions.

### Settled MVP baselines (not open Phase 0 decisions)

- **Search:** PostgreSQL keyword/full-text search with metadata filtering is the MVP baseline. Semantic/vector retrieval is deferred; revisit only if measured quality shows a need and the Project Lead approves the added complexity.
- **OCR:** A limited, best-effort OCR path is in scope for supported scanned documents. OCR is not guaranteed for every scan, layout, language, or image quality. Unsupported, failed, or uncertain cases must be visible and held for review—not silently treated as successfully extracted.
- **Ingestion:** Authorized people manually upload notices. Automatic college-site scraping/crawling and ERP integration are out of MVP scope.
- **AI:** Gemini calls remain backend-only. Model selection, provider limits, retry policy, and exact configuration are implementation details to confirm before integration.

### Resolve only when needed

- Exact frontend/backend repository layout and deployment arrangement.
- Final schema details and migration conventions.
- Exact API fields for each feature as it is implemented.
- OCR model/provider configuration, supported-input limits, and failure handling.
- Upload limits, retention, and storage access rules.
- Publication thresholds and mandatory human-review cases.
- Gemini model selection and operational limits.

## 5. Phase 1 — Technical foundation

**Goal:** Build the initial working software foundation under the Project Lead. Members join progressively.

### Recommended sequence

**A. Project Lead establishes the baseline**
- Inspect repository, branch, existing code, and deployment arrangement.
- Set up React + TypeScript + Vite frontend and Python + FastAPI backend.
- Configure environment variables and safe `.env.example` files.
- Connect backend to development Supabase database.
- Establish version-controlled migrations.
- Add health endpoint and frontend/backend connectivity.
- Add basic linting and test commands.

**B. Verify before delegating**
- Start frontend and backend from a clean setup.
- Verify database connection and migrations.
- Check that secrets are not committed.
- Confirm reproducible run/test steps.
- Fix confusing setup instructions before asking beginners to use them.

**C. Introduce small team tasks**
- Clone repository and follow setup with support.
- Run app and report errors.
- Check a page against a checklist.
- Prepare sample notices and expected metadata.
- Improve small UI text/layout.
- Add or verify a simple supplied test.
- Update README/task documentation.
- Build a small component after seeing a working example.

Do not assign a beginner an entire subsystem merely because it appears in `MODULES.md`.

### Phase 1 exit criteria

- [ ] Frontend and backend run locally using documented steps.
- [ ] A new contributor can run the project with reasonable support.
- [ ] Frontend reaches backend health endpoint.
- [ ] Supabase development connection works.
- [ ] Migrations are repeatable and reviewed.
- [ ] Secrets are excluded from Git.
- [ ] Basic quality checks run.
- [ ] Uploader authorization foundation is tested before protected features depend on it.
- [ ] Team can contribute through separate branches and PRs, with support.
- [ ] At least one small team task is integrated, if participation is available.

## 6. Phase 2 — Manual upload and notice-processing pipeline

**Goal:** A verified person manually uploads a notice; backend stores and processes it into a validated published notice or a held review item.

### Product boundary
- Manual upload by a verified, logged-in uploader.
- No automatic college-site scraping/crawling in MVP.
- Gemini is called by the backend only.
- Original notice remains authoritative.
- Failed, uncertain, invalid, or unsupported outcomes must not be silently published as reliable information.

### Main work
- Implement uploader authentication and server-side authorization.
- Implement manual upload and file validation.
- Store original file and create notice/processing records.
- Extract digital PDF text with page references.
- Implement limited best-effort OCR for supported scanned inputs.
- Record OCR/extraction failures and uncertainty; route cases needing judgment to review.
- Use Gemini for approved structured extraction, summary, and classification.
- Validate structured output and preserve evidence/provenance.
- Implement publish/hold workflow, uploader status, review reasons, retry, and correction.
- Implement withdrawal and the notice-management list for uploaders.
- Implement confirm/reject of detected relationships.
- Create page-aware text chunks and keyword-search data when a notice is published.

### Phase 2 exit criteria
- [ ] Verified uploader can submit a representative notice.
- [ ] Original file is preserved and linked to the notice.
- [ ] Supported digital documents produce traceable text and page references.
- [ ] Limited OCR is attempted only for supported inputs; limitations and failures are visible.
- [ ] AI output is schema-validated and cannot bypass backend validation.
- [ ] Publish/hold policy is enforced.
- [ ] Authorized review, correction, and relationship confirm/reject work.
- [ ] Publish and withdraw actions enforce backend authorization.
- [ ] Representative test notices pass pipeline checks.
- [ ] Failed, uncertain, and unsupported cases are handled safely.
- [ ] Tests cover success, validation failure, OCR failure, and processing failure.
- [ ] No automatic website ingestion or scraping is introduced.

## 7. Phase 3 — Public notice experience

**Goal:** Public viewers can discover and inspect published notices without an account.

### Main work
- Build public home and notice listing.
- Display recent/relevant published notices.
- Add audience/category filters.
- Build notice detail pages with key information and dates/actions.
- Provide access to original source through approved storage/access rules.
- Handle loading, empty, error, and responsive states.
- Accept public error reports on notice detail and route them to uploader review, if included in the pilot.
- Never expose held or internal processing information publicly.

### Phase 3 exit criteria
- [ ] Public browsing works without sign-in.
- [ ] Only published notices appear in public endpoints/UI.
- [ ] Filters work according to agreed vocabulary.
- [ ] Detail pages show approved structured information and source.
- [ ] Loading, empty, error, and mobile layouts are usable.
- [ ] Private uploader/internal data is not exposed.

## 8. Phase 4 — Search and Ask

**Goal:** Public users find relevant notices and ask questions grounded in notice sources.

The MVP search implementation is **PostgreSQL keyword/full-text search with metadata filtering**. This is settled, not an unresolved choice between keyword, semantic, or hybrid search.

Semantic/vector retrieval is deferred. It is not a Phase 4 MVP gate. Revisit only if evaluation shows the baseline is insufficient and the Project Lead explicitly approves the extra model, indexing, operational, and maintenance complexity.

### Main work
- Implement PostgreSQL full-text search over published notice content and metadata.
- Apply publication and audience visibility rules.
- Retrieve relevant passages and source references.
- Implement backend Ask orchestration using Gemini.
- Ground answers in retrieved published evidence.
- Show citations linking to notices and pages/sections where available.
- Provide safe not-found and uncertainty behavior.
- Evaluate using representative queries.

### Phase 4 exit criteria
- [ ] Search returns relevant published notices for the test set.
- [ ] Audience/category and publication filters are respected.
- [ ] Ask answers are grounded in retrieved sources.
- [ ] Citations identify real notices/pages where available.
- [ ] Not-found/uncertain behavior is safe and clear.
- [ ] Held/withdrawn notices cannot be retrieved.
- [ ] UI handles loading, no-result, and error states.
- [ ] Limitations are documented.
- [ ] Semantic/vector retrieval remains deferred unless separately approved.

## 9. Phase 5 — Integration, pilot, and quality hardening

**Goal:** Validate the MVP with representative notices and fix reliability/safety issues.

### Main work
- Prepare representative end-to-end dataset.
- Test uploader-to-processing-to-publication-to-public-discovery.
- Test authorization, private-data exposure, and storage access.
- Evaluate extraction, OCR limitations, AI output, search relevance, and citations.
- Test mobile usability/accessibility basics.
- Fix critical bugs and regressions.
- Validate logs, error handling, and provider failures.
- Confirm backup/recovery and source-file access approach.
- Prepare demo/fallback materials.
- Record known limitations and deferred features.

### Phase 5 exit criteria
- [ ] End-to-end workflow succeeds on representative dataset.
- [ ] No unresolved critical security/data-integrity issue remains.
- [ ] Public exposure and uploader permissions are tested.
- [ ] Extraction, publication, search, and citations meet acceptance criteria.
- [ ] Critical defects are fixed or explicitly accepted.
- [ ] Demo/pilot procedure and fallback materials are ready.
- [ ] Known limitations and future work are recorded.

## 10. Cross-phase rules

- Public listing, search, and Ask use published, public-safe notice data only.
- Processing, publication, and relationship states are separate concepts.
- `unspecified` audience is not equivalent to `all`.
- Backend authorization is authoritative; frontend visibility is not a security boundary.
- Preserve original files, provenance, page references, and audit history.
- Keep Gemini credentials/calls on the backend.
- Do not add calendar export, scraping/crawling, ERP integration, or semantic/vector search to MVP without explicit scope change.
- Update affected docs and GitHub issues when shared contracts change.

## 11. Maintenance

The Project Lead maintains this document; issue owners update task status in GitHub.

Update this file when the phase/stage changes, a milestone is accepted, exit criteria are met, a major blocker changes the roadmap, or a phase-level decision is resolved/deferred.

At each phase review:
1. Check actual issues and merged PRs.
2. Confirm exit criteria with evidence.
3. Update phase, stage, status, and next milestone.
4. Record important decisions/blockers.
5. Never mark a phase complete only because a target date passed.

**End of document.**
