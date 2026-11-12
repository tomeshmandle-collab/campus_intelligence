# Development Ownership

## 1. Purpose

This document explains who is responsible for each part of CAI Campus Intelligence, what each person is expected to deliver, and how the team should work together.

The team is still learning. Ownership is therefore about having one person accountable for moving a module forward—not about expecting that person to work without help or already know everything.

## 2. Working principles

1. **One accountable owner per task.** Others may contribute, but one person tracks completion.
2. **The Project Lead owns the foundation.** Architecture, backend foundations, integrations, security decisions, and Phase 0 sign-off stay with the Project Lead.
3. **Work from small, clear tasks.** Break work into tasks that can be understood and checked independently.
4. **Do not block on broad team reviews.** The Project Lead can complete and verify Phase 0 while teammates prepare low-risk work using the agreed contracts.
5. **Ask early when blocked.** A short question is better than silently guessing and building the wrong thing.
6. **Demonstrate working output.** A task is not complete merely because code was written; it must meet its acceptance criteria.

## 3. Roles

### Project Lead

**Primary responsibility:** Technical direction, foundation, backend, integration, and delivery coordination.

Owns:
- Confirming the repository structure and development workflow.
- Maintaining the product and architecture decisions.
- Phase 0 implementation and sign-off.
- Backend foundation and API integration.
- Supabase configuration, schema, migrations, authentication, and authorization.
- File upload/storage and the notice-processing pipeline.
- OCR and AI extraction integration, validation, and publication rules.
- Cross-module integration, security review, and release readiness.
- Assigning tasks, resolving dependencies, and keeping documentation current.

Expected outputs:
- A working local development environment.
- A documented and reproducible database setup.
- A tested backend/API foundation.
- A working vertical slice of notice ingestion through publication.
- Clear task descriptions and review feedback.

The Project Lead should avoid taking over every UI or test task. Once interfaces are stable, delegate bounded work.

### P1 — Quality and Test Assets

**Primary responsibility:** Help the team know whether the product behaves correctly.

Owns:
- Collecting representative sample notices that can legally and safely be used for testing.
- Organizing test files by type, quality, and expected difficulty.
- Recording expected facts from each sample notice.
- Preparing manual test scenarios for upload, extraction, search, and question answering.
- Recording bugs with clear reproduction steps and evidence.
- Retesting fixes and maintaining a simple regression checklist.

Expected outputs:
- A small, organized sample-notice collection.
- Expected-output notes for each test notice.
- A test-case checklist covering normal cases and common failures.
- Clear bug reports and retest results.

Not responsible for:
- Deciding the database architecture.
- Changing extraction or publication rules independently.
- Marking a notice as correct without checking the source document.

A useful test case records: input, steps, expected result, actual result, and pass/fail.

### P2 — Search and Question Answering

**Primary responsibility:** Help users find notices and get answers grounded in published notice content.

Owns:
- Understanding the agreed search and Q&A API contracts.
- Preparing search queries and expected matching notices.
- Preparing questions whose answers can be found in notice text.
- Implementing or coordinating the search/Q&A module once the backend contract is available.
- Checking that answers cite or identify supporting notices and do not invent unsupported details.
- Reporting cases where search misses relevant notices or returns irrelevant ones.

Expected outputs:
- Search test queries and expected results.
- Q&A test questions with evidence locations.
- Search/Q&A implementation or clearly scoped contributions to it.
- A short evaluation report describing misses, incorrect matches, and unsupported answers.

Baseline:
- PostgreSQL keyword/full-text search is the initial search method.
- Semantic/vector search is not part of the baseline.
- Q&A must be grounded in retrieved published notice content.
- If evidence is insufficient, the system should say so rather than guess.

### P3 — Public Frontend

**Primary responsibility:** Build the public-facing experience for discovering and understanding notices.

Owns:
- Public home/discovery page.
- Notice list and notice detail views.
- Keyword search interface.
- Ask interface with citation display, including not-found and uncertain answers.
- Public error-report form on the notice detail page.
- Filters and clear empty/loading/error states.
- Notice source links or original-file access where permitted by the API.
- Responsive layout and basic accessibility.
- Connecting the frontend to the agreed public API.

Expected outputs:
- Public pages that work with realistic API responses.
- Clear loading, empty, and error states.
- Responsive layouts for mobile and desktop.
- A short walkthrough demonstrating the main public journey.

Not responsible for:
- Creating a separate data model in the frontend.
- Implementing authentication or privileged backend rules.
- Adding unapproved features outside the MVP.

### P4 — Uploader and Admin Frontend

**Primary responsibility:** Build the interface used by authorized people to upload and manage notices.

Owns:
- Sign-in experience for authorized users.
- Notice upload form and upload progress.
- Processing status and clear failure messages.
- Review/exception screens where required.
- Notice correction or metadata editing screens permitted by the API.
- Relationship confirm/reject controls in the review screen.
- Notice-management list for finding and withdrawing notices.
- Error-report list with resolve/dismiss actions.
- Publication and withdrawal actions exposed by the API.
- Clear confirmation before consequential actions.

Expected outputs:
- A working authorized upload journey.
- Visible processing states and actionable error messages.
- Review screens that display extracted information alongside source evidence.
- A walkthrough demonstrating upload through review/publication.

Not responsible for:
- Defining role permissions independently.
- Bypassing backend authorization.
- Publishing records by directly modifying the database.

## 4. Module ownership map

The module IDs below match `MODULES.md`.

| Module | Primary owner | Supporting role |
|---|---|---|
| M01 Public Experience | P3 | Project Lead |
| M02 Uploader Experience | P4 | Project Lead |
| M03 Authentication & Authorization | Project Lead | P4 |
| M04 Upload & File Management | Project Lead | P4, P1 |
| M05 Text Extraction & OCR | Project Lead | P1 |
| M06 AI Extraction & Validation | Project Lead | P1, P2 |
| M07 Notice Data & Publication | Project Lead | P4, P1 |
| M08 Search & Retrieval | P2 | Project Lead, P3 |
| M09 Question Answering | P2 | Project Lead |
| M10 Briefing & Notice Discovery | Project Lead | P3, P2 |
| M11 Error Reporting & Review Support | Project Lead (backend) | P4 (interface), P1 |
| M12 Quality & Test Assets | P1 | All |
| M13 Shared Platform & Integration | Project Lead | All |

A supporting role contributes to the work but does not become a second accountable owner.

## 5. How tasks should be assigned

Every task should state:

- **Goal:** What outcome is needed?
- **Owner:** Who is accountable?
- **Starting point:** Which document, screen, endpoint, or file should they use?
- **Steps:** What are the small actions?
- **Acceptance criteria:** How will the team know it is done?
- **Dependencies:** What must exist first?
- **Evidence:** What should be shown in the pull request or demo?

Avoid tasks such as “finish frontend” or “do AI”. Prefer tasks such as “build the notice detail page using the sample API response and display the original source filename”.

## 6. Team communication and review

- Keep task updates short: **Done / Next / Blocked**.
- Raise a blocker as soon as it is discovered.
- Do not make silent changes to shared API fields, database columns, status values, or role rules.
- Discuss a proposed contract change with the Project Lead before implementing it.
- Use pull requests for changes that will be merged into the shared branch.
- Review for correctness and clarity, not cleverness.
- If a teammate cannot review code confidently, they can still check the visible behaviour against acceptance criteria and report what they observe.

## 7. Definition of done

A task is complete when:
- The requested behaviour exists.
- Acceptance criteria have been checked.
- Relevant tests or a manual verification have been performed.
- Errors and edge cases are handled to the level stated in the task.
- The change is committed and, where applicable, merged through a pull request.
- Any affected documentation is updated.
- The owner can explain what changed and how it was verified.

## 8. Scope and escalation

If a task requires changing the data model, API contract, authentication, authorization, publication lifecycle, or processing lifecycle, pause and coordinate with the Project Lead.

If the task is a visual or content-level change within an agreed interface, the assigned frontend owner can generally proceed independently.

The aim is not to create bureaucracy. It is to prevent beginner-friendly parallel work from turning into incompatible pieces that are difficult to integrate.
