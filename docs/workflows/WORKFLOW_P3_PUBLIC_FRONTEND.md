# Team Workflow & AI Prompting Playbook — P3: Public Frontend

**Role:** P3 — Public Frontend  
**Primary Focus:** Public browsing UI, notice feed, notice detail view, search presentation, public error reporting modal, and Ask Q&A interface with citations.  
**Boundaries:** Work strictly within `frontend/src/` (public routes & components). Do not invent new fields outside `docs/API_CONTRACTS.md`. Do not touch backend Python code or Supabase auth policies.  
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
3. Never work directly on `main`. Never commit `.env` or `node_modules/`.
4. When finished, push your branch and open a Pull Request (PR) on GitHub tagging `@ProjectLead`.

---

## 2. Complete Issue Sequence & Step-by-Step AI Prompts for P3

---

### Issue P3-1 (Phase 1): Public Layout Shell, Institutional Navbar & Responsive Footer
- **Branch Name:** `feat/public-layout-shell`
- **Working Directory:** `frontend/src/`
- **Scope:** Create responsive main navigation header, footer, and container layout for public users.

#### 🔹 Prompt 1: Public Layout & Navigation Bar
> "I am working as P3 (Public Frontend) on CAI Campus Intelligence using React, TypeScript, Vite, and Tailwind CSS. Read `docs/PRD.md` Section on Public Experience (M01). Create `src/components/layout/PublicLayout.tsx` and `src/components/layout/Navbar.tsx`. The Navbar should have:
> - College/App branding: 'CAI Campus Intelligence — Kirori Mal College'
> - Links: 'Notices', 'Search & Ask', 'About'
> - Secondary top-right action button: 'Staff Login' linking to `/login`
> Use Tailwind CSS classes. Make it fully responsive with a clean mobile drawer."

#### 🔹 Prompt 2: Institutional Footer & Disclaimers
> "In `src/components/layout/Footer.tsx`, create an institutional footer showing:
> - 'Centre for Artificial Intelligence, Kirori Mal College'
> - Official disclaimer: 'Extracted notice information is derived from official college notices. Always verify with the original document.'
> - Current year copyright and link to report an issue.
> Use academic slate/indigo theme styling."

---

### Issue P3-2 (Phase 2): Public Notice Feed, Audience/Category Filters & Loading Skeletons
- **Branch Name:** `feat/public-notice-feed`
- **Working Directory:** `frontend/src/`
- **Scope:** Build the notice feed that public students browse, including filter chips, loading skeletons, and empty state.

#### 🔹 Prompt 1: TypeScript Models & Contract Mock Data
> "Read `docs/API_CONTRACTS.md` Section 7.4 (GET `/api/v1/notices`).
> 1. In `src/types/notice.ts`, create the TypeScript interface `Notice` matching the contract: `id`, `title`, `category`, `publication_date`, `deadline_date`, `audience` ('student'|'faculty'|'staff'|'all'|'unspecified'), `summary_snippet`, `is_urgent`, `source_page_count`.
> 2. In `src/mocks/mockNotices.ts`, export 6 realistic mock notices covering Admissions, Exams, General, and urgent deadlines."

#### 🔹 Prompt 2: Notice Card Component
> "Create `src/components/notices/NoticeCard.tsx`.
> - Display title with prominent readable typography.
> - Category badge (blue for Admissions, amber for Exams, emerald for General).
> - Audience pill and publication date formatted nicely (e.g. 'Nov 12, 2026').
> - If `deadline_date` exists, show an urgent/calendar badge 'Deadline: YYYY-MM-DD'.
> - Summary snippet (clamped to 2 lines).
> - Clickable link navigating to `/notices/:id`."

#### 🔹 Prompt 3: Feed Assembly & Filter Controls
> "Create `src/components/notices/NoticeFeed.tsx`.
> - Add a filter bar: Audience chips ('All', 'Student', 'Faculty', 'Staff') and Category select dropdown.
> - Show 4 animated skeleton placeholders while loading.
> - Display an empty state if no notices match: 'No notices found for the selected filter.'
> - Fetch from `/api/v1/notices` with fallback to `mockNotices` when backend is offline."

---

### Issue P3-3 (Phase 3): Notice Detail View, Evidence Provenance & PDF Document Viewer Link
- **Branch Name:** `feat/notice-detail-view`
- **Working Directory:** `frontend/src/`
- **Scope:** Complete notice detail page showing full summary, dates, provenance, and PDF download link.

#### 🔹 Prompt 1: Notice Detail Page
> "Read `docs/API_CONTRACTS.md` Section 7.5 (GET `/api/v1/notices/{id}`).
> In `src/pages/public/NoticeDetailPage.tsx`:
> - Header: Full title, publication date, category, and audience badge.
> - Key Dates Card: Notice Date, Deadline Date (with countdown tag if upcoming).
> - Summary Section: Full structured summary.
> - Document Provenance Box: 'Official Document: PDF (X pages)'. Button: 'Download Official Notice' opening signed download URL in new tab.
> - Superseded/Amended Alert: If notice has relationship status 'superseded' or 'amended', show warning banner linking to active notice.
> - 'Report an Issue with this Notice' button that triggers the report modal."

---

### Issue P3-4 (Phase 3): Public Error-Report Form Modal
- **Branch Name:** `feat/public-error-report-form`
- **Working Directory:** `frontend/src/`
- **Scope:** Error reporting modal allowing students to report incorrect facts or typos.

#### 🔹 Prompt 1: Error Report Modal Component
> "Read `docs/API_CONTRACTS.md` Section 7.8 (POST `/api/v1/notices/{id}/reports`).
> In `src/components/notices/ErrorReportModal.tsx`:
> - Modal dialog with title: 'Report an Issue with this Notice'.
> - Reason selector dropdown: ['Incorrect Date', 'Wrong Audience', 'Typo in Summary', 'Document Unreadable', 'Other'].
> - Explanation textarea: min 10 chars, max 500 chars with character counter.
> - Optional reporter email field.
> - Submit button with spinner. On success: display 'Thank you! Your report has been submitted to the college editorial team.'
> - Handle API errors gracefully."

---

### Issue P3-5 (Phase 4): Keyword Search Bar & Ask Q&A Interface with Citation Cards
- **Branch Name:** `feat/search-and-ask-ui`
- **Working Directory:** `frontend/src/`
- **Scope:** Search & grounded Q&A interface with expandable citation previews.

#### 🔹 Prompt 1: Search and Ask Tabs
> "Read `docs/API_CONTRACTS.md` Sections 7.6 and 7.7. In `src/pages/public/SearchAndAskPage.tsx`:
> - Toggle switch: 'Search Notices' vs 'Ask a Question'.
> - Search Tab: Search input bar; on submit, queries `/api/v1/search?q=...` and renders matching notice cards with highlighted text snippets and page numbers.
> - Ask Tab: Question input ('e.g., What is the last date to submit the exam form?').
>   - Displays generated answer card.
>   - Shows confidence badge ('high' = green, 'uncertain' = amber, 'not_found' = gray).
>   - Renders expandable citation cards: Notice Title, Page Number, and exact excerpt quote.
>   - Institutional AI disclaimer: 'AI answers are strictly derived from official college notices. Always refer to cited documents for formal verification.'"

---

### Issue P3-6 (Phase 3): Public Frontend–Backend Contract Alignment & Live Integration Polish
- **Branch Name:** `fix/p3-backend-contract-alignment`
- **Working Directory:** `frontend/src/`
- **Scope:** Align all P3 public types, components, filters, routes, and error handling with the completed Lead backend (`L-1`–`L-9`) so zero contract or runtime conflicts remain.

#### 🔹 Prompt 1: Align Notice Feed Types, Mapper & `NoticeCard` with `GET /api/v1/notices`
> "Read `backend/app/schemas/notices.py` (`PublicNoticeListItem`, `PublicImportantDate`) and `docs/API_CONTRACTS.md` Section 7.4.
> Currently `frontend/src/types/notice.ts` (`Notice`) and `frontend/src/components/notices/NoticeCard.tsx` expect `summary_snippet`, `audience`, `publication_date`, `deadline_date`, `is_urgent`, and `source_page_count`, whereas the live backend returns `summary`, `audiences: string[]`, `important_dates`, `published_at`, `reference_number`, and `relationship_status`.
> Update `src/types/notice.ts`, `src/services/api.ts` (add a clean response normalizer/mapper if helpful), `src/components/notices/NoticeCard.tsx`, and `src/mocks/mockNotices.ts` so:
> 1. `NoticeCard` works identically with live `GET /api/v1/notices` responses and mock data.
> 2. Deadlines and urgency are derived from `important_dates` (`kind === 'deadline'`).
> 3. Nullable backend fields (`title`, `category`, `summary`, `published_at`) have safe null guards (no `.toLowerCase()` crash when `category` is `null`)."

#### 🔹 Prompt 2: Wire `GET /api/v1/filters` into `NoticeFeed`
> "Read `backend/app/services/public_notices_service.py` (`AUDIENCE_OPTIONS`, `CATEGORY_OPTIONS`) and `docs/API_CONTRACTS.md` Section 7.2 (`GET /api/v1/filters`).
> In `src/services/api.ts`, add `fetchFilters()` calling `GET /api/v1/filters`.
> In `src/components/notices/NoticeFeed.tsx`, populate the Category dropdown and Audience filter chips from `fetchFilters()` (keeping the current controlled options as an offline fallback when the backend is unreachable) so unsupported categories like `Scholarships` are not sent and backend categories (`Academic`, `Examination`, `Admissions`, `Events and workshops`, `Administration`, `General`, `Other`) work seamlessly."

#### 🔹 Prompt 3: Fix `NoticeDetailPage` Contract Mismatches (`action_items`, `related_notices`, Null Guards)
> "Read `backend/app/schemas/notices.py` (`PublicNoticeDetail`, `PublicRelatedNotice`, `PublicSourceFile`) and `src/pages/public/NoticeDetailPage.tsx`.
> Fix three compatibility issues in `src/types/notice.ts` and `src/pages/public/NoticeDetailPage.tsx`:
> 1. `action_items`: Backend returns `List[Dict]` (not `string[]`). Update `NoticeDetailPage.tsx` so each `action_items` entry renders safely whether it is a `string` or a structured object (never pass a raw object directly as a React child).
> 2. `related_notices`: Backend `PublicRelatedNotice` returns `{ notice_id, title, relation, direction: 'earlier' | 'later' }` instead of `relationship_type` / `publication_date`. Update `RelatedNotice` in `src/types/notice.ts` and its rendering in `NoticeDetailPage.tsx` to use `relation` and `direction`.
> 3. Add safe fallbacks for `source_file.page_count` (backend returns `{ available, download_url }`) and nullable fields (`title`, `category`, `summary`, `published_at`)."

#### 🔹 Prompt 4: Add `/about` Route & Wire Home Briefing (`GET /api/v1/notices/briefing`)
> "Inspect `src/App.tsx`, `src/components/layout/Navbar.tsx`, and `backend/app/schemas/notices.py` (`BriefingResponse`).
> 1. `Navbar.tsx` links to `/about`, which currently falls through to `NoticeFeed` in `src/App.tsx`. Add a clean institutional About view at `/about` explaining CAI Campus Intelligence (Kirori Mal College), how official notices are extracted with source provenance, and the disclaimer. Leave `/login` for P4-1.
> 2. In `src/services/api.ts`, add `fetchBriefing(audience?)` for `GET /api/v1/notices/briefing`, and surface a compact briefing strip (upcoming deadlines / recent changes) above the feed on the public home view when live data is available."

#### 🔹 Prompt 5: Verify `ErrorReportModal` Rate-Limit & Error Handling
> "Inspect `src/components/notices/ErrorReportModal.tsx` and `backend/app/services/public_notices_service.py` (`submit_public_error_report`).
> Ensure `ErrorReportModal.tsx`:
> 1. Displays a clear, user-friendly message when the backend returns `429 RATE_LIMITED` (5 requests / 60s per IP).
> 2. Only falls back to `mockSubmitErrorReport` on network/unreachable errors, never on `4xx` validation/not-found/rate-limit responses."

---

## 3. Pre-PR Submission Checklist for P3
- [ ] Run build test:
  ```bash
  cd frontend
  npm run build
  ```
  Verify zero TypeScript (`tsc -b`) or Vite build errors.
- [ ] Run live integration smoke test (backend `uvicorn app.main:app --reload` + frontend `npm run dev`, **not** mock mode):
  - [ ] **Notice Feed:** `GET /api/v1/notices` and `GET /api/v1/filters` load and filter by audience & category without console errors.
  - [ ] **Notice Detail:** `/notices/:id` renders summary, dates, `action_items`, `related_notices`, and **Download Official Notice** signed URL cleanly; withdrawn/held notices show the 404/not-available state.
  - [ ] **Error Report Modal:** Valid submission returns `201` success state; `<10` chars shows validation error; `429` shows rate-limit message.
  - [ ] **Routes & Responsive Layout:** `Notices`, `Search & Ask`, `About`, and mobile menu work cleanly at `375px` and `1440px`.
- [ ] Check Git status: verify zero `.env` or untracked build artifacts.
- [ ] Push branch: `git push -u origin <branch-name>`
- [ ] Open PR tagging `@ProjectLead` with the verification results and UI screenshots.
