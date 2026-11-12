# CAI Campus Intelligence — Product Requirements Document

**Version:** 1.0  
**Status:** Implementation baseline  
**Prepared for:** Centre for Artificial Intelligence (CAI), Kirori Mal College  
**Last updated:** 12 November 2026

> This document defines the product and MVP requirements. It does not claim that any feature has already been implemented. Technical choices are documented in `TECH_STACK.md` and `SYSTEM_ARCHITECTURE.md`; detailed database and HTTP contracts are maintained in their respective documents.

---

## 1. Product summary

CAI Campus Intelligence turns official college notices into a structured, searchable public notice board.

A small group of verified CAI uploaders manually adds official notices. The system preserves each original file, extracts useful information, validates the extracted information, and publishes notices that pass the agreed checks. Notices that are incomplete, ambiguous, or unsuccessfully processed are held for human review.

Students, faculty, and staff can use the public site without signing in. They can see relevant updates, browse and filter notices, search notice content, and ask questions. Answers must be grounded in published notices and point back to the relevant notice and page.

The product supports official college communication; it does not replace the original notice or the institution's official channels. **The original notice is always authoritative.**

**One-line pitch:** Turn scattered college notices into a clear, searchable notice board.

## 2. Problem

Official college notices can be long, formally worded, spread across pages, and supplied in different file formats. Important dates, deadlines, required actions, and intended audiences may be difficult to identify quickly. Readers may also struggle to determine whether an older notice has been amended, replaced, extended, or cancelled.

The product should reduce the effort required to find and understand relevant information without presenting AI-generated content as more authoritative than the original notice.

## 3. Product principles

1. **Official source, assistive layer.** The original notice is the source of truth. Extracted fields, summaries, and answers are assistive representations.
2. **Open to read, controlled to write.** Public browsing does not require an account. Notice-management actions require an authenticated and authorized uploader.
3. **Automatic when safe, human review when uncertain.** Notices that pass the defined validation rules may publish automatically. Uncertain or failed cases are held for review.
4. **Traceable and honest.** Key extracted fields and answers should include source-page references where available. Missing information is represented as “Not specified”; the system must not invent it.
5. **Preserve source evidence.** Original uploaded files are retained unchanged. Corrections affect structured records and are recorded.
6. **Useful before conversational.** The home page should make important information discoverable without requiring a question to be asked.
7. **Simple pilot first.** Build a reliable, understandable MVP before adding advanced automation or infrastructure.

## 4. Users and permissions

### 4.1 Public viewers

Students, faculty, and staff who use the public site without signing in.

They can:
- view published public notices;
- browse the home briefing and notice lists;
- select an audience filter;
- filter by category and date;
- view notice details and the original source file;
- search published notice content;
- ask questions about published notices;
- submit an error report about a notice.

They cannot:
- upload or modify notices;
- access held, failed, or internal processing records;
- access uploader-only screens or source files that are not approved for public viewing.

### 4.2 Trusted uploaders

A small, administrator-approved group, initially from CAI, responsible for adding and maintaining notices.

They can, according to their assigned permissions:
- sign in;
- upload one or more notice files;
- view processing progress;
- access the exception/review queue;
- compare extracted information with the original;
- correct supported fields;
- retry processing where appropriate;
- publish a held notice after review;
- withdraw a notice;
- review public error reports.

An authenticated account is not automatically an authorized uploader. The backend must check the account's permission for every protected action.

### 4.3 Application roles and notice audiences are different

Application permissions describe what an account may do. Notice audiences describe who a notice applies to.

Initial application roles:
- `uploader`
- `admin`

Initial notice audience values:
- `student`
- `faculty`
- `staff`
- `all`
- `unspecified`

“Admin” is an application permission, not a notice audience. “Unspecified” means the source notice does not provide enough information to classify its audience. It must not be treated as “all.”

The public audience selector should use understandable labels such as Students, Faculty, Staff, and All. Choosing Students, Faculty, or Staff shows notices for that audience plus notices targeted to everyone. Choosing All, which is the default when no audience has been chosen, is the unfiltered view: it shows every eligible published notice. Notices with an unspecified audience appear in the All view (and not under Students, Faculty, or Staff), where they are labelled “Not specified”; they must not be silently represented as applying to every audience. The API also accepts an `unspecified` filter value that returns only those notices; the public selector is not required to offer it.

## 5. MVP scope

### 5.1 Included

**Notice intake**
- Manual upload by an authorized uploader.
- Single-file and small-batch upload.
- PDF files as the primary supported format.
- Common image files may be accepted when the configured extraction path supports them.
- Per-file validation and status; one failed file must not block other files in a batch.
- Preservation of the original uploaded file.

**Document processing**
- Page-aware text extraction from digital PDFs.
- AI-assisted extraction of notice metadata and a concise summary.
- Extraction of dates, audiences, action items, and explicit relationships to other notices when present.
- Evidence/source references for key extracted fields.
- Backend validation before publication.
- Best-effort OCR for scanned pages only when the selected provider and current usage limits support it. Scanned-document support is limited and must not be promised as universal. If OCR is unavailable or unreliable, the notice is held for human review.
- Clear processing failure and retry behavior.

**Notice publication and review**
- Automatic publication for notices that pass all required checks.
- Exception queue for notices that fail checks or contain unresolved ambiguity.
- Human correction and explicit publication for held notices.
- Withdrawal of notices without erasing their audit history.
- Visible status for current, amended, superseded, extended, or cancelled notices.

**Public experience**
- Home briefing with recently posted, upcoming, action-oriented, and changed notices.
- Audience and category filters.
- Notice list and detail pages.
- Access to the public original source file.
- Keyword search with relevant excerpts and page references.
- Question answering grounded only in eligible published notice content.
- Public error reporting.

### 5.2 Not included in this MVP

- Automatic fetching, scraping, crawling, or synchronization from college websites.
- College ERP or student-information-system integration.
- Push notifications or automated messaging.
- Personal accounts or individualized feeds.
- Department-level application permissions.
- Native Android or iOS applications.
- Custom model training or fine-tuning.
- Guaranteed extraction from handwriting, damaged files, or poor-quality scans.
- Mandatory semantic/vector search. It may be evaluated as a later enhancement after keyword search is working and tested.
- Any feature not listed in the MVP unless the Project Lead explicitly approves a scope change.

## 6. Core user workflows

### A. Upload and automatic processing

1. An authorized uploader signs in.
2. The uploader selects one or more notice files.
3. The backend authenticates and authorizes the uploader and validates each file.
4. Each accepted original is stored unchanged, and a notice/processing record is created.
5. The system extracts page-aware text. OCR is attempted only if the configured and approved path supports it.
6. Gemini assists with structured extraction and summarization.
7. Backend validation checks the structure, dates, supporting evidence, and other publication rules.
8. A notice that passes all required checks is published automatically.
9. A notice with a blocking issue is held for review with a clear reason.
10. The uploader can see the outcome for each file.

A successful upload does not mean that a notice has been published.

### B. Exception review

1. An authorized uploader opens the review queue.
2. The uploader sees why the notice was held and can inspect the original.
3. The uploader compares the extracted fields with the source.
4. The uploader corrects supported fields where necessary.
5. The backend records the correction and reviewer.
6. The uploader explicitly publishes the notice when it is ready, or retries processing / leaves it held.

Human corrections must be distinguishable from AI-extracted values.

### C. Public browsing

1. A viewer opens the site without signing in.
2. The home page displays a briefing based on published notices.
3. The viewer selects an audience and/or category.
4. The viewer opens a notice to inspect its summary, key fields, dates, action items, related notices, and original source.
5. The interface clearly labels AI-extracted and human-corrected information.

### D. Search

1. A viewer enters a keyword or phrase.
2. The backend searches eligible published notice content and applies the selected filters.
3. Results show the notice, a relevant excerpt, and a page reference when available.
4. Superseded or cancelled notices are clearly labelled and do not appear as current upcoming actions.

### E. Ask a question

1. A viewer submits a question and optional audience filter.
2. The backend retrieves relevant passages from eligible published notices.
3. Gemini receives only the retrieved evidence needed to formulate an answer.
4. The backend validates that returned citations refer to retrieved evidence.
5. The answer includes notice and page references where available.
6. If evidence is missing, conflicting, or insufficient, the system says it cannot find a reliable answer.

The system must not answer college-notice questions using unsupported general model knowledge.

### F. Changed notices

1. A newly processed notice is checked for explicit references to earlier notices and clear amendment/replacement/extension/cancellation language.
2. A relationship is recorded only when supported by evidence.
3. If the relationship is uncertain, the new notice is held for human review rather than automatically changing the earlier notice.
4. Confirmed relationships are visible from both relevant notice records.
5. Superseded or cancelled notices remain available for historical reference but are excluded from current upcoming/action views as appropriate.

### G. Error report

1. A viewer submits an error report from a notice detail page.
2. The notice remains visible; the report does not directly change the notice.
3. The report enters the uploader review queue.
4. An authorized uploader reviews and resolves or dismisses it.
5. The system records the resolution.

## 7. Functional requirements

Priority labels:
- **Must:** required for the MVP.
- **Should:** desirable for the MVP if it does not threaten core delivery.
- **Later:** outside the MVP.

### 7.1 Access and security

- **Must:** Public browsing, filtering, notice details, search, and Ask work without login.
- **Must:** Upload, correction, publication, withdrawal, and review-queue access require authentication and backend authorization.
- **Must:** Public endpoints expose only published and public-safe records.
- **Must:** Service credentials and Gemini credentials remain server-side.
- **Must:** Public Ask and error-report endpoints have basic abuse protection and rate limiting.
- **Must:** Original files are stored privately; public access is granted only through an approved controlled-access mechanism after publication.

### 7.2 Upload and extraction

- **Must:** Accept the approved PDF format and configured image formats.
- **Must:** Validate actual file content/type, size, and batch limits on the backend.
- **Must:** Preserve original files unchanged.
- **Must:** Track the outcome of each file independently.
- **Must:** Preserve page boundaries and page numbers during text extraction.
- **Must:** Keep issue dates, event dates, and deadlines as separate concepts.
- **Must:** Never invent a missing field or treat an event date as a deadline.
- **Must:** Hold for review any notice with a page that has no usable extracted text and cannot be reliably OCR'd. Such a notice is never published on incomplete extraction.
- **Should:** Provide limited OCR for scanned pages where the configured provider can process them reliably and within approved usage limits.

Fields to extract when supported by the source:

| Field | Requirement |
|---|---|
| Title | Extract from the source; required for a useful public record |
| Reference number | Only when stated |
| Summary | Concise, faithful summary; clearly AI-generated |
| Category | One of the controlled categories below |
| Issuing authority | Only when stated |
| Issue date | Separate from event dates and deadlines |
| Event date(s) | Keep separate from deadlines |
| Deadline(s) | Keep separate from event dates |
| Audience | Student, Faculty, Staff, All, or Unspecified |
| Audience detail | Course, department, year, or other wording when stated |
| Action items | Include responsible group and due date only when supported |
| Related notices | Explicit relation and source evidence |
| Source references | Page and supporting passage for key fields |
| Confidence / validation evidence | Used as supporting validation metadata, not as sole proof |

Initial categories:
- Academic
- Examination
- Admissions
- Events and workshops
- Faculty
- Administration
- General
- Other

### 7.3 Validation and publication

A notice may publish automatically only when all applicable blocking checks pass.

Required checks:
- The extraction output conforms to the agreed structured schema.
- The title and category are usable and supported by the source.
- Every extracted critical date is a real, normalized date and is supported by the relevant source passage.
- A deadline is not before the issue date when both are known, unless the source explicitly explains an exceptional case that a reviewer resolves.
- Critical audience classification is supported. If the audience is absent or unclear, use `unspecified`; do not guess.
- Supporting passages/page references exist for key fields where the source provides them.
- No unresolved contradiction or high-impact ambiguity remains.
- Any detected relationship that would change the status of an earlier notice is sufficiently supported; uncertain relationships require review.

The model's self-reported confidence must not be the sole publication gate. Backend validation and source evidence are authoritative. Numeric thresholds may be calibrated against the pilot test set and documented before they are relied upon.

If a notice fails a blocking check, it is held with a human-readable reason. Held notices must not expose extracted fields through public endpoints. A public-facing held notice may be represented only if the product owner later approves a safe source-only behavior; the MVP default is to keep held notices out of public listings and retrieval.

### 7.4 Home briefing

The home page should work without a search query and provide:

- **This week:** supported deadlines and events in the next seven days.
- **Coming up:** later supported deadlines and events.
- **Recently posted:** newest published notices with a short summary.
- **Action items:** actions relevant to the selected audience, with due dates when stated.
- **Recent changes:** published notices that amend, replace, extend, or cancel earlier notices.

The backend should provide the briefing from stored data. The home page must not wait for a live Gemini call.

### 7.5 Audience and filters

- A persistent audience selector applies consistently to the home page, notice list, search, and Ask.
- A notice targeted to `all` appears for every selected audience.
- A notice with a specific audience appears for matching viewers.
- Selecting Students, Faculty, or Staff shows notices targeted to that audience plus notices targeted to `all`.
- Selecting All (the default) is the unfiltered view and shows every eligible published notice, including those with an `unspecified` audience, which are labelled “Not specified”.
- `unspecified` is not equivalent to `all`, and `unspecified` notices do not appear under Students, Faculty, or Staff. The API's optional `unspecified` filter (`API_CONTRACTS.md` §5.1) returns only those notices.
- Category and date filters are available.
- Department/year details may be retained as descriptive targeting metadata, but department-level application permissions are outside the MVP.
- A viewer's selected audience may be remembered locally in the browser; no personal account is required.

### 7.6 Changed-notice behavior

- Detect relationships using explicit references and clear source language.
- Supported relationship types: `amends`, `replaces`, `extends`, `cancels`.
- Keep both notices and their relationship history.
- Do not delete an earlier notice when it is changed.
- Show status and links on notice lists, details, search results, and Ask answers when relevant.
- Exclude cancelled and superseded deadlines from current upcoming/action views.
- Uncertain relationships go to human review.

### 7.7 Notice list and detail

A notice list item should show:
- title;
- category;
- audience;
- relevant key dates;
- current/changed status;
- publication date.

A notice detail should show, when available:
- summary;
- extracted fields;
- action items;
- audience;
- dates;
- related notices and relationship type;
- correction/status history appropriate for public display;
- supporting source passages and page references;
- link or controlled access to the original source file;
- labels distinguishing AI-extracted and human-corrected fields;
- error-report action.

### 7.8 Search

- **Must:** Keyword search over published notice metadata and extracted text.
- **Must:** Support category and audience filters.
- **Must:** Return useful excerpts and page references when available.
- **Must:** Prefer current notices and clearly label superseded/cancelled notices.
- **Later/optional:** Semantic/vector retrieval may be added after keyword search has been tested and a measurable need is established.

### 7.9 Question answering

- Answers must use only retrieved passages from published notices.
- Audience and publication filters must apply before evidence is sent to the model.
- Answers should cite the notice and page, where available.
- The backend must verify that each citation corresponds to retrieved evidence.
- If the evidence is absent, contradictory, or insufficient, return a clear not-found/uncertain response.
- Do not let a model invent deadlines, dates, audiences, or citations.
- Do not expose internal prompts, secrets, or unpublished content.

### 7.10 Error reporting

- **Should:** Provide a report action on each public notice.
- Accept a controlled issue type and optional description.
- Validate and rate-limit submissions.
- Keep the notice visible until an authorized uploader takes a separate action.
- Route reports to the review queue and record their resolution.

### 7.11 Exception queue

- **Must:** List notices held due to validation issues, processing failures, uncertain relationships, or other review triggers.
- Show the reason, source file, extracted values, and supporting evidence.
- Support correction, retry, publication after review, and withdrawal where authorized.
- Record who changed what and when.

## 8. Non-functional requirements

### Trust and correctness
- Clearly label AI-generated content.
- State that the original notice is authoritative.
- Preserve source references for key fields and answers.
- Do not claim an accuracy rate until it has been measured on a documented test set.

### Reliability
- Processing failures must be visible and recoverable.
- A failed processing step must not damage or replace the original.
- One failed file must not block other files in a batch.
- Public browsing must remain usable while processing is underway.
- The home briefing must use stored data, not synchronous AI generation.

### Security and privacy
- Enforce uploader authorization on the backend.
- Apply database access controls and storage permissions.
- Keep secrets out of source control and browser bundles.
- Treat uploaded files and extracted content as untrusted.
- Define a handling rule before uploading notices containing personal or sensitive information. Do not publish such notices by default until the rule is approved.

### Usability and accessibility
- Mobile-first, responsive interface.
- Plain-language error and status messages.
- Keyboard-accessible controls and sufficient contrast.
- Clear distinction between official source text and AI-generated summaries.
- Professional institutional interface, not a generic chatbot-first design.

### Cost and operational limits
- Define pilot file-size, page-count, and batch limits before deployment.
- Apply request limits to public AI-backed features.
- Monitor provider quotas and storage/database usage.
- Avoid adding paid services or infrastructure without explicit approval.

## 9. Conceptual data

The detailed schema is maintained in `DATABASE_SCHEMA.md`. At product level, the system needs:

- **Notice:** original-file reference, title, category, summary, issuing authority, issue date, publication and processing states.
- **Audience target:** role and optional descriptive detail such as department/year.
- **Notice date:** event or deadline with label and source reference.
- **Action item:** requested action, responsible group, due date when stated, and source reference.
- **Notice relationship:** earlier/later notice, relation type, evidence, and review state.
- **Text chunk:** notice, page, text, and search metadata.
- **Field source:** field, source page/passage, extraction method, and confidence/evidence metadata.
- **Processing run/event:** pipeline stage, outcome, error, and timestamps.
- **Human edit:** field change, actor, time, and correction note.
- **Error report:** notice, issue type, description, status, and resolution.

Processing status, publication status, and relationship status are separate concepts and must not be collapsed into one status value.

## 10. Screens

### Public experience
- Home / briefing
- Notices list
- Notice detail
- Search
- Ask

### Uploader experience
- Sign-in
- Upload
- Upload/processing status
- Exception/review queue
- Notice review and correction
- Notice management

The public and uploader experiences may be routes within one frontend application. The architecture does not require separate frontend deployments.

## 11. Testing and success criteria

Use a representative pilot set of approximately 15–20 official notices, subject to permission to use them. Include:
- multi-page notices;
- multiple dates in one notice;
- notices with no deadline;
- different audiences;
- ambiguous or missing dates;
- tables and varied layouts;
- scanned examples only if OCR is included;
- at least two amendment/replacement examples;
- examples that should be held for review.

Record expected values and source pages for the test set. Measure actual field correctness, automatic-publication rate, review rate, false-publication cases, citation correctness, and search/Ask behavior. Do not report unmeasured accuracy.

The MVP is demonstration-ready when:

- [ ] Public viewers can use the site without signing in.
- [ ] Only authorized uploaders can perform management actions.
- [ ] Upload accepts valid files and reports each file's outcome independently.
- [ ] Original files remain unchanged and access follows the approved policy.
- [ ] Digital PDF text is extracted with page references.
- [ ] Eligible notices publish automatically under the approved validation rules.
- [ ] Notices with blocking issues are held with understandable reasons.
- [ ] Reviewers can correct, retry, and publish held notices.
- [ ] The home briefing and audience/category filters work.
- [ ] Notice changes are represented and linked without deleting history.
- [ ] Keyword search returns useful results and source references.
- [ ] Ask answers from published notice evidence and correctly declines unsupported questions.
- [ ] AI-generated and human-corrected fields are distinguishable.
- [ ] Error reports enter the review workflow if that feature is included in the pilot.
- [ ] The pilot is deployed with approved sample notices and a prepared demonstration flow.

## 12. Demonstration flow

1. Open the site on a phone without signing in.
2. Show the home briefing and switch the audience filter.
3. Open a notice and inspect its extracted fields and original source.
4. Sign in as an authorized uploader.
5. Upload a small batch and show per-file processing outcomes.
6. Show an automatically published notice.
7. Show a held notice, its validation reason, and the correction/review process.
8. Show a changed notice and its relationship to the earlier notice.
9. Search for a relevant phrase and open the matching source page.
10. Ask an answerable question, inspect citations, then ask an unsupported question and show the not-found response.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Incorrect date published automatically | Require source evidence and backend date validation; hold ambiguous critical dates; retain original link and error reporting |
| Missed or false change detection | Prefer explicit references; hold uncertain relationships; preserve history |
| Public Ask abuse or high provider usage | Rate limits, bounded retrieval, usage monitoring, and clear limits |
| Personal information exposed in notices | Approve handling rules before upload; default to withholding uncertain cases |
| Poor-quality scans | Limit OCR promises; expose failure state; route unsupported cases to review |
| AI summary mistaken for official text | Clear labels and prominent original-source access |
| Small uploader group becomes a bottleneck | Keep review tools simple; allow additional authorized uploaders without redesign |
| Free-tier service limits | Set pilot limits, monitor quotas, and verify hosting behavior before demonstration |

## 14. Future possibilities

These are not MVP commitments and must not be implemented without a separate scope decision:
- automated intake from approved official sources;
- improved OCR and table extraction;
- semantic search if keyword search proves insufficient;
- audience-specific notifications;
- additional campus workflows and analytics;
- broader institutional integrations.

## 15. Product decisions and change control

The following decisions are established for this implementation baseline:

- MVP notice intake is manual.
- The original notice remains authoritative and is preserved unchanged.
- Public reading does not require login.
- Management actions require authenticated, server-authorized uploaders.
- Passing notices may publish automatically; uncertain or failed notices are held.
- Keyword search is the baseline search capability.
- OCR is limited, best-effort pilot support and is not guaranteed.
- Semantic/vector search is optional and not a baseline dependency.
- Withdrawal is preferred to permanent deletion for ordinary notice lifecycle management; history is retained.

A proposed product change must be recorded in a GitHub issue or decision record, reviewed by the Project Lead, and reflected in every affected document before implementation. Do not let the PRD, API contract, schema, and code silently diverge.

## 16. Maintenance

**Product owner:** Project Lead, with input from the CAI team.  
**Update this document when:** user journeys, MVP scope, audience behavior, publication rules, product priorities, or acceptance criteria change.

**End of document.**
