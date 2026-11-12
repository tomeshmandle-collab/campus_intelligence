# Team Workflow & AI Prompting Playbook — P4: Uploader & Admin Frontend

**Role:** P4 — Uploader & Admin Frontend  
**Primary Focus:** Staff authentication/login, notice PDF upload dropzone, review & exception queue workbench, field correction & publish actions, notice management table, and error report inbox.  
**Boundaries:** Work strictly within `frontend/src/` (admin/uploader routes & components). Do not invent new fields outside `docs/API_CONTRACTS.md`. Do not modify backend code or database RLS policies.  
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
3. Never work directly on `main`. Never store real passwords or tokens in code.
4. When finished, push your branch and open a Pull Request (PR) on GitHub tagging `@ProjectLead`.

---

## 2. Complete Issue Sequence & Step-by-Step AI Prompts for P4

---

### Issue P4-1 (Phase 1): Staff Login Page, Auth Context & Protected Route Guard
- **Branch Name:** `feat/admin-login-ui`
- **Working Directory:** `frontend/src/`
- **Scope:** Create staff authentication provider, login card, and route protector.

#### 🔹 Prompt 1: Auth State Context
> "I am working as P4 (Uploader Frontend) on CAI Campus Intelligence using React, TypeScript, and Vite. Read `docs/MODULES.md` (M03 Authentication & Authorization). In `src/context/AuthContext.tsx`, create an authentication context provider. It should manage: `user`, `sessionToken`, `isAuthenticated`, `isLoading`, `login(email, password)`, and `logout()`. Provide mock implementation with fallback to backend API `/api/v1/auth/login`."

#### 🔹 Prompt 2: Login Component & Route Guard
> "In `src/pages/admin/LoginPage.tsx`, create a clean login form:
> - Header: 'CAI Campus Intelligence — Staff Portal'
> - Email and password inputs with validation and password visibility toggle.
> - Error banner for invalid credentials.
> - 'Sign In' button with loading state.
> In `src/components/auth/ProtectedRoute.tsx`, create a wrapper that redirects to `/login` if `isAuthenticated` is false."

---

### Issue P4-2 (Phase 2): Notice PDF Upload Dropzone & Processing Status Indicator
- **Branch Name:** `feat/upload-dropzone-ui`
- **Working Directory:** `frontend/src/`
- **Scope:** Drag-and-drop file upload with client-side validation and multi-step progress modal.

#### 🔹 Prompt 1: Dropzone Component & Client Validation
> "Read `docs/API_CONTRACTS.md` Section 8.1 (POST `/api/v1/notices/upload`). Create `src/components/uploader/FileDropzone.tsx`.
> - Drag-and-drop zone with clear visual drag-over indicator and file picker button.
> - Strictly validate that file is `.pdf` and <= 10MB.
> - Display error message if user selects non-PDF or file > 10MB.
> - Display selected file name, file size (in KB/MB), and a 'Remove' button."

#### 🔹 Prompt 2: Multi-step Processing Stepper
> "In `src/components/uploader/ProcessingStatusModal.tsx`:
> - Step 1: Uploading (animated progress bar 0 to 100%).
> - Step 2: Processing ('Extracting text & validating notice with AI...').
> - Step 3: Success ('Notice ready for review' with button to open review screen).
> - Step 4: Error ('Processing failed' displaying reason from backend with 'Try Again' button)."

---

### Issue P4-3 (Phase 2): Review & Exception Queue Screen (Side-by-Side PDF vs Data)
- **Branch Name:** `feat/review-queue-editor`
- **Working Directory:** `frontend/src/`
- **Scope:** Review table of held notices and side-by-side inspection workbench.

#### 🔹 Prompt 1: Review Queue Table
> "Read `docs/API_CONTRACTS.md` Section 8.3 (GET `/api/v1/uploader/review-queue`).
> Create `src/pages/admin/ReviewQueuePage.tsx`:
> - Table of notices awaiting review.
> - Columns: Title, Notice Date, Review Reasons (badges e.g., 'OCR Uncertain', 'Conflicting Dates', 'Low Confidence'), Uploaded At, Actions.
> - 'Review Notice' button navigating to `/admin/review/:id`."

#### 🔹 Prompt 2: Side-by-Side Review Workbench
> "Create `src/pages/admin/NoticeReviewDetailPage.tsx`:
> - Split-screen layout (50/50 desktop, stacked on mobile).
> - Left Pane: Embedded PDF viewer displaying original uploaded document.
> - Right Pane: Form with extracted fields (Title, Notice Date, Deadline Date, Category, Audience, Summary).
> - Top Banner: Highlight review reasons requiring staff attention."

---

### Issue P4-4 (Phase 2): Field Correction Form, Relationship Confirm/Reject & Publish Controls
- **Branch Name:** `feat/review-actions-controls`
- **Working Directory:** `frontend/src/`
- **Scope:** Inline editing, relationship confirm/reject buttons, and publication action toolbar.

#### 🔹 Prompt 1: Field Evidence & Editing Controls
> "In `src/pages/admin/NoticeReviewDetailPage.tsx`:
> - Add editable form inputs for Title, Dates, Audience, Category, and Summary.
> - Field Evidence Tag: Display small tag next to each field (e.g. 'Found on Page 1: \"The last date is 15th Nov...\"').
> - Detected Relationships Card: If AI detected a link (e.g., 'Amends Notice #104'), show two buttons: 'Confirm Relationship' and 'Reject Relationship' calling `POST /api/v1/uploader/notices/:id/relationships/:rel_id/confirm` (or reject)."

#### 🔹 Prompt 2: Action Toolbar & Publish Flow
> "Add review action bar at bottom of `NoticeReviewDetailPage.tsx`:
> - Button 1: 'Save Changes' (calls PATCH `/api/v1/uploader/notices/{id}/fields`).
> - Button 2: 'Approve & Publish' (calls POST `/api/v1/uploader/notices/{id}/publish`). Show confirmation modal.
> - Button 3: 'Retry Processing' (calls POST `/api/v1/uploader/notices/{id}/retry`).
> Handle loading spinners and success toast notifications."

---

### Issue P4-5 (Phase 3): Notice Management Table, Withdrawal Confirmation & Report Inbox
- **Branch Name:** `feat/notice-management-list`
- **Working Directory:** `frontend/src/`
- **Scope:** All-notices management dashboard, notice withdrawal modal, and user report resolution.

#### 🔹 Prompt 1: Management Dashboard Table & Withdrawal Modal
> "Read `docs/API_CONTRACTS.md` Sections 8.8 and 8.10.
> In `src/pages/admin/NoticeManagementPage.tsx`:
> - Tabs: 'All Notices', 'Published', 'Held', 'Withdrawn'.
> - Search bar and category filter.
> - Action button: 'Withdraw Notice'. Opens confirmation dialog:
>   - Requires entering a withdrawal reason (e.g., 'Postponed by Principal').
>   - Submits `POST /api/v1/uploader/notices/{id}/withdraw`.
>   - Updates local notice badge to 'withdrawn'."

#### 🔹 Prompt 2: User Error Report Inbox
> "Read `docs/API_CONTRACTS.md` Sections 8.9 and 8.11.
> In `src/components/admin/ErrorReportInbox.tsx`:
> - Display list of error reports submitted by students.
> - Show: Notice Title, Issue Category, Student Comment, Date Submitted.
> - Action buttons: 'Mark Resolved' or 'Dismiss Report' with comment.
> - Submits `PATCH /api/v1/uploader/reports/{report_id}`."

---

## 3. Pre-PR Submission Checklist for P4
- [ ] Run build test:
  ```bash
  cd frontend
  npm run build
  ```
- [ ] Check Git status: verify zero secrets or `.env` files staged.
- [ ] Push branch: `git push -u origin <branch-name>`
- [ ] Open PR tagging `@ProjectLead` with screenshots of admin screens.
