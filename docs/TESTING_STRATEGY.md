# Testing Strategy

## 1. Purpose

This document defines how the CAI Campus Intelligence team should check that the product works correctly.

Testing is not only a final phase. Each feature should be checked while it is being built. The strategy is intentionally practical for a small student team.

## 2. Testing principles

1. Test the behaviour users depend on, not just whether code runs.
2. Test important failure paths as well as successful paths.
3. Use the original notice as the source of truth for extraction checks.
4. Keep test data separate from real operational data.
5. Make tests repeatable and record what was actually tested.
6. Fix security and data-integrity failures before visual polish.
7. Do not claim that an untested feature works.
8. Start with a small reliable test set and expand it as real failures are found.

## 3. Testing layers

| Layer | What it checks | Examples |
|---|---|---|
| Unit tests | Small functions in isolation | Date parsing, validation helpers, text normalization |
| API tests | Request/response and backend rules | Upload validation, authorization, search response |
| Integration tests | Multiple components working together | Backend + database, backend + private storage |
| Frontend component tests | UI behaviour in isolation | Form validation, loading and error states |
| End-to-end tests | Complete user journeys | Upload notice through publication; browse and search |
| Manual exploratory tests | Issues that scripted tests may miss | Mobile layout, confusing messages, unusual scans |
| AI/OCR evaluation | Quality of extraction and generated answers | Field accuracy, evidence coverage, unsupported questions |

Use Pytest for backend tests as specified in `TECH_STACK.md`. For frontend tests, inspect the existing repository and use its configured tooling; do not introduce a second test stack without approval.

## 4. Test environments and data

Keep environments separate:

- **Local development:** individual developer work and local tests.
- **Shared development/test environment:** team integration checks using non-production test data.
- **Production:** real users and operational data.

Rules:
- Never use production credentials in local test files.
- Never commit real secrets.
- Do not upload confidential or personal documents as sample fixtures without permission.
- Prefer public or deliberately sanitized sample notices.
- Keep a record of where test files came from and whether they may be shared.
- Clean up test records and files when safe and appropriate.
- Do not assume that a test database can be reset without checking who else is using it.

## 5. Core test assets

P1 maintains a small test collection that includes:

1. A clean digital PDF with selectable text.
2. A scanned or image-based notice.
3. A multi-page notice.
4. A notice with a clear date and deadline.
5. A notice with multiple audiences or an unclear audience.
6. A notice with a table or complex layout.
7. A low-quality or rotated scan.
8. A notice with incomplete or ambiguous information.

For each sample, record:
- sample ID and filename;
- file type and page count;
- source/provenance and permission to use;
- expected title and important metadata where present;
- expected dates, with date type distinguished;
- expected audience, including `unspecified` when the source does not say;
- page references for key facts;
- known ambiguities or extraction challenges.

Do not force an expected value where the notice itself is ambiguous. Record the ambiguity.

## 6. Test lifecycle and status rules

Tests must preserve the separation between these dimensions.

### Processing status
- `pending`
- `processing`
- `completed`
- `failed`

### Publication status
- `held`
- `published`
- `withdrawn`

### Notice relationship status
- `current`
- `superseded`
- `amended`
- `extended`
- `cancelled`

Do not treat one status dimension as a substitute for another. For example, a processing-completed record is not automatically public; publication status determines public visibility.

Audience values:
- `student`
- `faculty`
- `staff`
- `all`
- `unspecified`

`unspecified` must not be converted to `all` by a default or UI assumption.

## 7. Functional test coverage

### 7.1 Authentication and authorization

Test:
- Anonymous visitor can access permitted public endpoints.
- Anonymous visitor cannot upload or review notices.
- Authenticated user without uploader permission cannot perform uploader actions.
- Authorized uploader can access permitted uploader endpoints.
- A user cannot access another user's restricted resources by changing an ID.
- Revoked or invalid credentials are rejected.

### 7.2 Upload and file management

Test:
- Supported file type is accepted.
- Unsupported file type is rejected.
- File exceeding the configured size limit is rejected.
- Empty or corrupt file is handled safely.
- Duplicate submission behaviour is defined and tested.
- Original file is stored privately.
- Unauthorized access to original files is denied.
- Storage failure produces a clear processing or upload error.
- User-supplied filenames and paths cannot escape the intended storage location.

### 7.3 OCR and text extraction

Test:
- Digital PDF text is extracted with page references.
- Scanned input follows the intended OCR path where supported.
- Multi-page documents preserve page boundaries.
- Empty extraction is detected.
- Rotated or poor-quality scans are handled without fabricated text.
- Extraction failures are recorded.
- Original file remains available for comparison.

OCR quality should be evaluated against the source, not by whether the extraction service returned a non-empty string.

### 7.4 AI extraction and validation

Test:
- Model output matches the required structured schema.
- Missing fields remain missing or uncertain rather than being invented.
- Dates are not confused across issue date, event date, and deadline.
- Audience is extracted conservatively.
- `unspecified` remains distinct from `all`.
- Evidence references point to the correct page or source passage where available.
- Invalid or malformed model output is rejected or held.
- Provider timeout/rate-limit errors are handled.
- A model-generated summary does not replace the original source.

### 7.5 Publication and notice relationships

Test:
- A validated passing record can be published under the agreed rules.
- An uncertain record is held for review.
- A held notice is not returned publicly.
- A withdrawn notice is not returned as an active public notice.
- A superseded/amended/extended/cancelled relationship is represented distinctly.
- Consequential edits are recorded.
- Public endpoints return only eligible published data.

### 7.6 Search and discovery

Test:
- Search finds exact title matches.
- Search finds relevant body-text matches.
- Metadata filters behave as documented.
- Empty query behaviour is defined.
- No-result response is clear.
- Pagination is stable and correct.
- Held and withdrawn notices are excluded from public results.
- Search results link to the correct notice.
- PostgreSQL keyword/full-text search remains the baseline unless a later decision changes it.

### 7.7 Question answering

Test:
- Answerable question receives a response grounded in retrieved notices.
- Answer identifies supporting notice and page/source evidence when available.
- Question with no relevant evidence receives an insufficient-evidence response.
- Conflicting notices are not silently collapsed into one answer.
- Dates and deadlines are reported accurately.
- The system does not invent facts, audiences, or dates.
- Only published notice content is used for public Q&A.
- Provider failures produce a safe error response.

### 7.8 Frontend

Test:
- Main pages render at mobile and desktop widths.
- Loading states appear while requests are pending.
- Empty states are understandable.
- Errors are visible and actionable.
- Forms validate required inputs.
- Repeated submission is prevented or safely handled.
- Keyboard navigation and labels are usable.
- UI status labels match backend values and meanings.
- Destructive or consequential actions require clear confirmation.

### 7.9 Error reporting and review

Test:
- Public submission of a report for a published notice succeeds.
- Submission against an unpublished or non-existent notice returns 404.
- Report submission does not directly alter notice publication status.
- Rate limiting prevents report spam.
- Authorized uploaders can list open reports.
- Resolving or dismissing a report updates status, records the resolving user, timestamp, and stores the optional resolution note.
- Unauthorized users cannot view or resolve reports.

## 8. AI/OCR evaluation method

AI and OCR systems are probabilistic. A single successful example is not enough.

For each sample notice:

1. Run extraction using the same documented process.
2. Compare each extracted field against the source.
3. Record correct, incorrect, missing, and uncertain values.
4. Check evidence/page references.
5. Record whether validation correctly accepted or held the notice.
6. Repeat after changing prompts, models, parsing, or validation rules.
7. Compare the new result with the previous result.

Track at least:
- field-level correctness for important metadata;
- date accuracy;
- audience accuracy;
- evidence/page-reference correctness;
- false acceptance of incorrect data;
- false rejection of valid data;
- processing failure rate.

For this project, a false acceptance that publishes incorrect information is more serious than a valid notice being held for human review.

Do not set numeric quality targets until a representative baseline has been measured and the Project Lead has approved targets.

## 9. Bug report format

Use this template:

```markdown
## Summary
One sentence describing the problem.

## Environment
Local / shared test / production
Browser or device, if relevant.

## Steps to reproduce
1.
2.
3.

## Expected result

## Actual result

## Evidence
Screenshots, request ID, sanitized logs, or sample ID.

## Severity
Critical / High / Medium / Low

## Frequency
Always / Sometimes / Once

## Related issue or module
```

Never attach API keys, passwords, access tokens, private file URLs, or unnecessary personal information to a bug report.

## 10. Severity guidance

| Severity | Meaning | Example |
|---|---|---|
| Critical | Security exposure, data loss, or serious incorrect public information | Private notice files publicly accessible |
| High | Core journey is blocked or materially incorrect | Valid notices cannot be uploaded or published |
| Medium | Important feature is unreliable but workaround exists | Search misses a class of expected matches |
| Low | Minor issue with limited impact | Small spacing or wording inconsistency |

The Project Lead decides release-blocking status after considering impact and evidence.

## 11. Regression testing

When a bug is fixed:
1. Add a test that reproduces the failure where practical.
2. Verify the fix.
3. Run nearby tests that could be affected.
4. Add the case to the regression checklist.
5. Record any remaining limitation.

Do not rely on memory to repeat old tests. Keep a written checklist.

## 12. Minimum checks by phase

Phase numbers match `PHASE.md`.

### Phase 1 — Technical foundation
- Local startup and health endpoint.
- Database migration reproducibility.
- Authorization allow/deny tests.
- Private storage access tests.
- OCR/extraction proof of concept compared with source.
- Basic CI/test command.

### Phase 2 — Manual upload and notice-processing pipeline
- Upload validation.
- Processing state transitions.
- OCR and AI schema validation.
- Hold versus publish rules.
- Failure and retry behaviour.
- Original-file preservation.
- Review and correction permissions.
- Audit trail checks.

### Phase 3 — Public notice experience
- Public-only visibility.
- Notice detail correctness.
- Mobile/desktop and empty/error states.

### Phase 4 — Search and Ask
- Search relevance against the prepared query set.
- Evidence-grounded Q&A.
- Insufficient-evidence behaviour.

### Phase 5 — Integration, pilot, and quality hardening
- End-to-end regression.
- Security and storage review.
- Duplicate/retry behaviour.
- Deployment verification.
- Controlled pilot checks.

## 13. Definition of tested

A task may be described as tested only when:
- the relevant test or manual procedure was actually run;
- the environment and test data are identifiable;
- the result is recorded;
- failures are reported rather than hidden;
- important limitations are stated.

A task is not fully verified merely because it compiles, builds, or renders once.

## 14. Ownership

- **P1:** Maintains test assets, expected outputs, manual scenarios, bug reports, and regression evidence.
- **P2:** Supplies search and Q&A evaluation cases and investigates relevance/grounding failures.
- **P3:** Verifies public frontend behaviour and responsive states.
- **P4:** Verifies uploader/admin workflows and visible processing/review states.
- **Project Lead:** Owns backend test strategy, authorization/data-integrity checks, integration testing, and release sign-off.

Everyone is responsible for testing their own change before opening a pull request.
