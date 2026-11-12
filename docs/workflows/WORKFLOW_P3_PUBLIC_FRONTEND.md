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

## 3. Pre-PR Submission Checklist for P3
- [ ] Run build test:
  ```bash
  cd frontend
  npm run build
  ```
- [ ] Check Git status: verify zero `.env` or untracked build artifacts.
- [ ] Push branch: `git push -u origin <branch-name>`
- [ ] Open PR tagging `@ProjectLead` with UI screenshots.
