# CAI Campus Intelligence — GitHub Roadmap

**Version:** 1.0  
**Status:** Working planning guide  
**Last updated:** 2026-11-12  
**Maintainer:** Project Lead / Technical Lead

> This roadmap translates the phase plan into suggested GitHub epics, issues, ownership, dependencies, and acceptance criteria. It is a planning guide—not evidence that issues have already been created or work completed.

## 1. Purpose

- `PHASE.md` tracks project-level outcomes and phase gates.
- `GITHUB_ROADMAP.md` suggests how to organize the work.
- GitHub Issues track individual tasks, owners, blockers, and acceptance criteria.
- Pull requests record implementation and review evidence.

Keep the board lightweight and adapt ownership to team availability and confidence.

## 2. Working assumptions

- The Project Lead establishes the technical foundation and remains accountable for integration.
- Team members are beginners; broad technical-document review is not a prerequisite for implementation.
- Tasks should be small, concrete, and independently verifiable.
- Owners are initial assignments, not permanent role locks.
- Frontend work may use contract-aligned mock data while backend work proceeds.
- Do not create issues for out-of-scope features without an explicit scope decision.

## 3. Suggested GitHub Project setup

| Field | Suggested values |
|---|---|
| Status | Backlog, Ready, In Progress, In Review, Done, Blocked |
| Priority | P0, P1, P2, P3 |
| Phase | Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, Phase 5 |
| Module | M01–M13 or short module name |
| Owner | GitHub assignee |
| Due date | Only when a real date is agreed |

Suggested views: Board by Status; Roadmap by Phase; My tasks by assignee; Blocked; Ready to start.

Suggested labels:
- Type: `type: feature`, `type: bug`, `type: docs`, `type: research`, `type: chore`, `type: decision`
- Area: `area: frontend`, `area: backend`, `area: ai`, `area: database`, `area: testing`, `area: infrastructure`
- Workflow: `needs-decision`, `good-first-task`, `blocked`, `security`

Prefer Project fields for Phase and Module rather than dozens of labels.

## 4. Canonical documentation references

Use these exact filenames. Do not refer to older project-prefixed filename variants.

1. `PRD.md`
2. `TECH_STACK.md`
3. `SYSTEM_ARCHITECTURE.md`
4. `DATABASE_SCHEMA.md`
5. `API_CONTRACTS.md`
6. `MODULES.md`
7. `DEVELOPMENT_OWNERSHIP.md`
8. `PHASE.md`
9. `GITHUB_ROADMAP.md`
10. `CODING_GUIDELINES.md`
11. `GIT_WORKFLOW.md`
12. `TESTING_STRATEGY.md`
13. `AGENTS.md`

If the repository currently uses another layout, inspect it first and update references deliberately.

## 5. Roadmap overview

The phase sequence follows `PHASE.md`. Update status only against actual repository and issue evidence.

| Phase | Name | Main outcome |
|---|---|---|
| 0 | Project preparation and technical readiness | Project Lead is ready to begin the technical foundation |
| 1 | Technical foundation | Reproducible app, backend, database, migrations, and authorization foundation |
| 2 | Manual upload and notice-processing pipeline | Uploaded notice becomes published or held for review |
| 3 | Public notice experience | Public users browse and inspect published notices |
| 4 | Search and Ask | Users search and ask grounded questions with citations |
| 5 | Integration, pilot, and quality hardening | MVP validated using representative notices |

## 6. Phase 0 — Project preparation and technical readiness

**Goal:** Give the Project Lead enough clarity and a safe starting plan. Phase 0 is Project Lead-led. It does not require all beginner team members to read, understand, or approve every technical document.

### Suggested epic: `EPIC-0 — Project Readiness`

| Suggested task | Owner | Priority | Dependencies | Acceptance evidence |
|---|---|---:|---|---|
| Check MVP boundary and non-goals against `PRD.md` | Project Lead | P0 | PRD | Lead can state scope consistently |
| Check stack and architecture consistency | Project Lead | P0 | `TECH_STACK.md`, `SYSTEM_ARCHITECTURE.md` | No contradiction blocks Phase 1 |
| Check database and API baselines | Project Lead | P0 | `DATABASE_SCHEMA.md`, `API_CONTRACTS.md` | Initial contracts are usable references |
| Confirm module boundaries and flexible ownership | Project Lead | P1 | `MODULES.md`, `DEVELOPMENT_OWNERSHIP.md` | Initial owners/dependencies recorded |
| Confirm coding, Git, and testing conventions | Project Lead | P1 | `CODING_GUIDELINES.md`, `GIT_WORKFLOW.md`, `TESTING_STRATEGY.md` | Conventions available for first slice |
| Prepare/check `AGENTS.md` | Project Lead | P1 | Canonical docs | Exact filenames and approved scope referenced |
| Inspect existing repository before changing it | Project Lead | P0 | Repository access | Existing branch, code, structure, deployment understood |
| Place canonical docs in sensible repository location | Project Lead | P0 | Repository inspection | Docs placed without overwriting existing work |
| Create small Phase 1 starter issues | Project Lead | P0 | Repository inspection and baseline | Issues have owner, dependency, acceptance and verification |
| Configure GitHub Project if useful | Project Lead | P1 | Repository access | Board usable; omit if overhead outweighs benefit |
| Prepare short team orientation | Project Lead | P2 | Phase 1 starter plan | Members understand purpose and first small task |

Create only issues useful for the actual repository and team.

### Phase 0 exit gate

- [ ] Project Lead confirms MVP scope and non-goals.
- [ ] Project Lead confirms stack, architecture, database, and API baselines are consistent enough to begin.
- [ ] Module boundaries and flexible ownership are documented.
- [ ] Coding, Git, testing, and AI-agent instructions are available.
- [ ] Existing repository has been inspected before structural changes.
- [ ] Canonical docs are placed appropriately, or a deliberate placement plan is recorded.
- [ ] First Phase 1 tasks are small, ordered, owned, and verifiable.
- [ ] Project Lead is ready to start Phase 1 without waiting for full-team technical review.

**Not a Phase 0 requirement:** all members reviewing/approving technical docs, understanding the full architecture, or independently owning subsystems. Team orientation and beginner-friendly onboarding happen gradually in Phase 1.

## 7. Phase 1 — Technical foundation

**Goal:** Make the application runnable and establish a safe foundation.

### Suggested epic: `EPIC-1 — Technical Foundation`

| Suggested task | Owner | Collaborators | Dependencies |
|---|---|---|---|
| Inspect current repository and document structure | Project Lead | — | Phase 0 |
| Confirm frontend/backend project structure | Project Lead | P3, P4 | Repository inspection |
| Configure React + TypeScript + Vite frontend | Project Lead | P3 | Structure decision |
| Configure FastAPI backend skeleton | Project Lead | P2 | Structure decision |
| Add health endpoint and basic API error handling | Project Lead | P1 | Backend skeleton |
| Configure environment variables and `.env.example` | Project Lead | Relevant contributors | App skeleton |
| Set up Supabase development project | Project Lead | — | Environment plan |
| Establish/apply initial database migrations, with RLS enabled and `anon`/`authenticated` grants revoked on application tables | Project Lead | P1 | Schema baseline |
| Configure storage buckets and access rules | Project Lead | P4 | Supabase setup |
| Configure uploader authentication and role-check foundation | Project Lead | P4 | Auth baseline |
| Connect frontend to backend API base URL | Project Lead | P3, P4 | Health endpoint |
| Add lint, format, and test commands | Project Lead | P1, P3, P4 | Repository structure |
| Write and verify local setup instructions | Project Lead | P1, P3, P4 | Working local setup |
| Give each participating member one small starter task | Project Lead | Relevant member | Working baseline |

### Phase 1 exit gate

- [ ] Frontend and backend run locally using documented steps.
- [ ] New contributor can follow setup with reasonable support.
- [ ] Frontend reaches backend health endpoint.
- [ ] Supabase development connection works.
- [ ] Initial migrations are repeatable and reviewed.
- [ ] Secrets are excluded from Git.
- [ ] Basic checks can be run by contributors.
- [ ] Uploader authorization foundation is tested before protected features depend on it.

## 8. Phase 2 — Manual upload and notice-processing pipeline

**Goal:** Complete the workflow from manual submission to publication or review.

### Suggested epic: `EPIC-2 — Notice Ingestion and Processing`

| Suggested task | Owner | Collaborators | Dependencies |
|---|---|---|---|
| Prepare representative test notices and expected outputs | P1 | Project Lead | Approved samples |
| Implement authorized manual upload endpoint | Project Lead | P4 | Auth, API contract |
| Implement file type/size validation | Project Lead | P1 | Upload endpoint; limits confirmed |
| Store original files safely | Project Lead | — | Supabase Storage |
| Create notice and processing records | Project Lead | — | Migrations |
| Implement processing status tracking | Project Lead | P4 | Processing records |
| Implement PDF text extraction with page references | Project Lead | P1 | Stored files |
| Implement limited best-effort OCR for supported scanned inputs | Project Lead | P1 | Extraction pipeline/configuration |
| Record OCR failure/uncertainty and route cases to review | Project Lead | P1 | OCR path |
| Implement Gemini structured extraction | Project Lead | P1 | Text extraction/schema |
| Implement extraction validation and review reasons | Project Lead | P1 | Extraction output |
| Persist field evidence and processing history | Project Lead | P1 | Schema/extraction |
| Implement publish/hold workflow | Project Lead | P4 | Validation/authorization |
| Create page-aware text chunks and keyword-search data for published notices | Project Lead | P2 | Text extraction, publish/hold workflow, schema |
| Implement correction and audit behavior | Project Lead | P4, P1 | Review workflow |
| Implement relationship confirm/reject action | Project Lead | P4, P1 | Review workflow, schema |
| Implement retry behavior | Project Lead | P1 | State model |
| Implement notice-management list and withdraw endpoints | Project Lead | P4 | Publish/hold workflow, authorization |
| Build uploader upload interface | P4 | Project Lead | API contract; mocks allowed |
| Build processing status UI | P4 | Project Lead | Status response |
| Build review queue/detail UI | P4 | Project Lead | Review APIs |
| Build correction, relationship confirm/reject, and publish/retry controls | P4 | Project Lead | Review APIs |
| Build notice-management list and withdrawal confirmation UI | P4 | Project Lead | Management and withdraw APIs |
| Run end-to-end upload-to-publication tests | P1 | Project Lead, P4 | Complete pipeline |

The Project Lead owns the initial backend pipeline. Delegate later when a contributor is ready; preserve interfaces.

### Phase 2 exit gate

- [ ] Authorized uploader can submit a supported notice.
- [ ] Original file is stored and linked to the notice.
- [ ] Text extraction preserves page references where possible.
- [ ] Limited OCR is attempted only for supported inputs; limitations/failures are visible.
- [ ] AI output matches the agreed schema and is validated.
- [ ] Invalid/uncertain cases are held with useful reasons.
- [ ] Authorized review/correction works.
- [ ] Publish/withdraw behavior enforces backend authorization.
- [ ] Representative test notices pass pipeline checks.
- [ ] No scraping or automatic external notice ingestion is introduced.

## 9. Phase 3 — Public notice experience

**Goal:** Public visitors browse and inspect published notices without logging in.

### Suggested epic: `EPIC-3 — Public Notice Experience`

| Suggested task | Owner | Collaborators | Dependencies |
|---|---|---|---|
| Confirm public user journeys and page content | P3 | Project Lead | `PRD.md` |
| Build public layout/navigation | P3 | P4 | Frontend foundation |
| Implement briefing API | Project Lead | P3, P1 | Published notice data |
| Implement briefing/home UI | P3 | Project Lead | Briefing contract |
| Implement audience/category filter options | Project Lead | P3 | Filter vocabulary |
| Implement notice list API/UI | Project Lead / P3 | P3 / Project Lead | Published data/contract |
| Implement notice detail API/UI, source references, and controlled original-file access | Project Lead / P3 | P3 / Project Lead | Notice data/contract |
| Implement error-report endpoints (public submit with rate limiting, uploader list, resolve/dismiss) | Project Lead | P4 | Published notice data, authorization |
| Build public error-report form on notice detail | P3 | Project Lead | Report submit API |
| Build uploader error-report review UI | P4 | Project Lead | Report list/resolve APIs |
| Add responsive layouts and UI states | P3 | P1 | Public screens |
| Test public access and private-data exclusion | P1 | Project Lead, P3 | Public APIs |

### Phase 3 exit gate

- [ ] Public browsing works without sign-in.
- [ ] Briefing and notice list show only published public records.
- [ ] Filters follow agreed vocabulary.
- [ ] Detail shows available dates, actions, and source references.
- [ ] Mobile/desktop layouts are usable.
- [ ] Loading, empty, and error states work.
- [ ] Held, draft, and withdrawn notices are not exposed.
- [ ] If error reporting is included in the pilot, a submitted report reaches the uploader review list without changing the notice.

## 10. Phase 4 — Search and Ask

**Goal:** Help users find notice information and receive grounded answers with citations.

### Agreed MVP search baseline

Implement **PostgreSQL keyword/full-text search with metadata filtering**. Do not create an MVP decision issue asking whether search should be keyword, semantic, or hybrid; the baseline is already settled.

Semantic/vector retrieval is deferred. It is not a Phase 4 MVP dependency or exit gate. Revisit only if measured search relevance demonstrates a concrete gap and the Project Lead approves the added complexity.

### Suggested epic: `EPIC-4 — Search and Grounded Q&A`

| Suggested task | Owner | Collaborators | Dependencies |
|---|---|---|---|
| Confirm page-aware chunk format and metadata | Project Lead + P2 | P1 | Extraction output |
| Implement PostgreSQL full-text keyword search | P2 | Project Lead | Published notice data/schema |
| Apply audience/publication filters to retrieval | P2 | Project Lead, P1 | Search service |
| Define retrieval response and citation shape | P2 | Project Lead, P3 | API contract |
| Implement backend Ask orchestration | P2 | Project Lead | Retrieval |
| Implement citation, not-found, and uncertain behavior | P2 | P1 | Ask service |
| Build public search UI | P3 | P2 | Search API |
| Build Ask UI and citation display | P3 | P2 | Ask API |
| Test retrieval relevance and traceability | P1 | P2 | Test set |
| Test unsupported questions and provider failures | P1 | P2, Project Lead | Ask service |
| Record baseline limitations and evaluation results | P1 | P2, Project Lead | Test results |

### Phase 4 exit gate

- [ ] Search returns relevant published notices for test set.
- [ ] Audience/category filters are respected.
- [ ] Ask answers are grounded in retrieved source content.
- [ ] Citations identify real notices/pages where available.
- [ ] Not-found/uncertain behavior is safe and clear.
- [ ] Held/withdrawn notices cannot be retrieved.
- [ ] UI handles loading, no-result, and error states.
- [ ] Limitations are documented.
- [ ] Semantic/vector retrieval remains deferred unless separately approved.

## 11. Phase 5 — Integration, pilot, and quality hardening

**Goal:** Validate the full MVP with representative notices and fix reliability/safety issues.

### Suggested epic: `EPIC-5 — MVP Pilot and Stabilisation`

| Suggested task | Owner | Collaborators | Dependencies |
|---|---|---|---|
| Prepare end-to-end pilot dataset | P1 | Project Lead | Approved samples |
| Run uploader-to-public experience workflow | P1 | All owners | Phases 2–4 |
| Test authorization and public data exposure | Project Lead + P1 | P4, P3 | Integrated app |
| Test extraction, OCR limitations, and AI output quality | P1 | Project Lead | Processing pipeline |
| Test search relevance and citations | P1 | P2 | Search/Ask |
| Test mobile usability/accessibility basics | P3 + P1 | P4 | UI |
| Fix critical bugs/regressions | Relevant module owner | P1 | Defect reports |
| Validate logs, errors, and provider failures | Project Lead | P1, P2 | Integrated backend |
| Confirm backup/recovery and source-file access | Project Lead | — | Storage/deployment |
| Prepare demo script and fallback materials | P1 | All owners | Stable pilot |
| Record limitations and deferred features | Project Lead | All owners | Pilot review |
| Approve MVP pilot readiness | Project Lead | P1 | Exit evidence |

### Phase 5 exit gate

- [ ] End-to-end workflow succeeds on representative dataset.
- [ ] No unresolved critical security/data-integrity issue remains.
- [ ] Public exposure and uploader permissions are tested.
- [ ] Extraction, publication, search, and citations meet acceptance criteria.
- [ ] Critical defects are fixed or explicitly accepted.
- [ ] Demo/pilot procedure and fallback materials are ready.
- [ ] Limitations and future work are recorded.

## 12. Parallel work and dependencies

Parallel work is encouraged when boundaries are clear.

- P1 prepares test notices and expected results while Project Lead establishes backend foundation.
- P3 builds public screens with contract-aligned mock data.
- P4 builds uploader screens with contract-aligned mock data.
- P2 prepares search test cases and evaluates the agreed PostgreSQL keyword-search baseline.
- Documentation, fixtures, and UI sketches can progress alongside implementation.

Wait for dependencies where necessary:
- Semantic/vector retrieval remains deferred and requires explicit approval.
- OCR follows limited best-effort scope and supported-input configuration; do not promise universal OCR.
- Frontend integration uses agreed API shapes.
- Public display consumes published data only.
- Frontend visibility is never a substitute for backend authorization.
- Deployment work waits for confirmed hosting and environment ownership.

Coordinate changes to API shapes, schema/migrations, authorization, processing states, evidence/chunk representation, publication visibility, and shared frontend routing/components. Update the relevant docs and issue/PR.

## 13. Lightweight team rhythm

**Start of week:** review phase/milestone, choose a small set of Ready issues, confirm owners/dependencies.  
**During week:** update issue status, raise blockers, record decisions in GitHub, and use small PRs.  
**End of week:** review merged work and test evidence, check blockers, update `PHASE.md` if needed, and choose the next useful milestone.

No fixed daily meeting is required; adapt to the team's timetable.

## 14. Definition of done

- [ ] Requested behavior/deliverable exists.
- [ ] Acceptance criteria are met.
- [ ] Relevant tests/manual verification are complete.
- [ ] No unrelated module behavior was knowingly broken.
- [ ] Documentation/examples are updated where needed.
- [ ] PR is reviewed and merged, or non-code work is reviewed and accepted.
- [ ] Remaining limitations are recorded.

For documentation tasks, verification includes filenames, links, consistency, and whether instructions match the actual repository.

## 15. Maintenance

`PHASE.md` tracks project-level progress; GitHub tracks individual tasks. At phase review, check actual issues and merged PRs, verify exit criteria with evidence, update the phase/stage/status, and record blockers or decisions. Never mark a phase complete only because a target date passed.

**End of document.**
