# Coding Guidelines

## 1. Purpose

These guidelines help the CAI Campus Intelligence team write code that is understandable, testable, and safe to integrate.

The team has mixed technical experience. Prefer clear, predictable code over clever abstractions. These guidelines describe the intended working style; they do not prove that a particular folder, file, or tool already exists. Inspect the repository before changing it.

## 2. Technology baseline

Follow `TECH_STACK.md`:

| Area | Baseline |
|---|---|
| Frontend | React + TypeScript + Vite |
| Styling | Tailwind CSS |
| Backend | Python + FastAPI |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| File storage | Private Supabase Storage bucket |
| AI | Gemini API, called from the backend only |
| PDF text extraction | PyMuPDF |
| Backend tests | Pytest |
| Version control | Git + GitHub |

Use the tools already configured in the repository. Do not add a second framework, formatter, test runner, or styling system without a reason and approval.

## 3. General coding principles

1. **Read before editing.** Inspect the relevant files and nearby patterns before changing code.
2. **Keep changes scoped.** Work only on the assigned issue and module unless a cross-module change is necessary.
3. **Prefer readable names.** Names should explain what a value, function, component, or module represents.
4. **Keep functions focused.** A function should have one clear responsibility.
5. **Avoid duplication, but do not over-abstract.** Extract shared logic when it is genuinely reused or clarifies a boundary.
6. **Handle failure explicitly.** Do not hide errors or return success-shaped data after a failure.
7. **Validate untrusted input.** Browser input, uploaded files, AI output, and external responses must be treated as untrusted.
8. **Do not invent contracts.** Use `API_CONTRACTS.md` and `DATABASE_SCHEMA.md`; coordinate any proposed changes.
9. **Test behaviour.** A successful build is not proof that a feature works.
10. **Document non-obvious decisions.** Explain why a constraint exists when the reason is not clear from the code.

## 4. Repository and project structure

- Follow the existing repository structure unless the Project Lead approves a change.
- Do not create folders simply because a document lists a logical module.
- The M01–M13 module map in `MODULES.md` describes responsibilities, not mandatory package names.
- Keep frontend and backend responsibilities separate.
- Keep provider-specific code behind a small, understandable boundary where practical.
- Avoid circular imports and hidden cross-module dependencies.
- Do not move or rename large parts of the repository as part of an unrelated feature.

Before creating a file, search for an existing file that already serves the same purpose.

## 5. Frontend guidelines

### React and TypeScript

- Use TypeScript types for component props, API responses, and important application data.
- Avoid `any`; if unavoidable at an external boundary, validate or narrow the value before using it.
- Keep components focused on one screen section or interaction.
- Move reusable data transformations into small utility functions.
- Keep API calls out of deeply nested presentation components where a shared API layer already exists.
- Use stable keys when rendering lists.
- Handle loading, empty, success, and error states.
- Do not assume an API request always succeeds.
- Do not put secrets in frontend environment variables. Anything bundled into browser code must be treated as public.

### API usage

- Use the agreed `/api/v1` application API contract.
- Keep request and response types aligned with `API_CONTRACTS.md`.
- Do not read or write application tables directly from the browser; all application data goes through the backend API. The only direct browser-to-Supabase use is the approved Supabase Auth sign-in flow.
- Do not treat hidden buttons or hidden routes as authorization.
- Display backend validation messages in a useful, safe way.
- Avoid duplicating business rules in the frontend. The backend remains authoritative.

### UI behaviour

- Make the main action clear.
- Prevent accidental repeated submission where appropriate.
- Show upload progress and processing state honestly.
- Confirm consequential actions such as publication or withdrawal.
- Ensure mobile layouts remain usable.
- Use accessible labels, keyboard-operable controls, and meaningful focus states.

## 6. Backend guidelines

### FastAPI and Python

- Use request and response models for API boundaries.
- Validate incoming data before business logic uses it.
- Keep route handlers thin: parse/validate, call the appropriate service, return a response.
- Put reusable business logic in focused functions or service modules consistent with the repository.
- Use explicit return types for important functions where they improve clarity.
- Avoid broad `except Exception` handlers unless they are at a deliberate application boundary and log/translate the failure safely.
- Do not return internal stack traces or secrets to clients.
- Keep error responses consistent with `API_CONTRACTS.md`. Configure custom exception handlers for `RequestValidationError` and `StarletteHTTPException` to output the `{ "error": { "code", "message", "details", "request_id" } }` envelope rather than FastAPI's default `{"detail": [...]}` format.

### Database access

- Treat PostgreSQL as the source of truth for notice and workflow records.
- Use migrations for schema changes.
- Do not rely on undocumented manual dashboard changes.
- Use parameterized queries or the repository's safe database client patterns.
- Enforce permissions on the backend/database, not only in UI code.
- Join `departments` in queries to output the string department name or `null` for API responses rather than exposing internal `department_id` foreign keys.
- Keep processing state, publication state, and notice relationship state separate.
- Keep `unspecified` audience distinct from `all`.
- Do not add vector columns or a vector database as part of the baseline without an approved decision.

### File handling

- Validate file type, size, and content as appropriate.
- Do not trust the filename or browser-provided MIME type by itself.
- Keep original notice files in private storage.
- Use generated storage keys rather than trusting user-supplied paths.
- Do not expose private storage credentials or service-role keys.
- Preserve the original source file and provenance.

## 7. AI and OCR guidelines

- Call Gemini only from backend code.
- Keep API keys in server-side environment configuration.
- Treat model output as an untrusted candidate, not as verified fact.
- Validate structured output against an explicit schema.
- Preserve page/source evidence where available.
- Do not invent missing dates, times, audiences, or facts.
- If extraction is uncertain or evidence is missing, hold the record or mark the field as uncertain according to the agreed validation rules.
- Keep the original notice authoritative.
- Do not let a generated summary replace source content.
- Record model/provider errors without logging secrets or unnecessary personal data.

## 8. Security and privacy

- Never commit `.env` files, API keys, access tokens, service-role keys, or credentials.
- Keep a safe `.env.example` containing variable names and placeholder values only.
- Do not log passwords, tokens, private file URLs, or full sensitive payloads.
- Apply least privilege to database and storage access.
- Validate authorization for every protected backend action.
- Avoid collecting personal information that the product does not need.
- Do not expose held, failed, or withdrawn notices through public endpoints.
- Review file access and public responses before release.

## 9. Naming and formatting

Follow established repository conventions first. If a convention is not established:

- Use descriptive `snake_case` for Python variables and functions.
- Use `PascalCase` for React components and TypeScript types/interfaces.
- Use descriptive `camelCase` for JavaScript/TypeScript variables and functions.
- Use uppercase names for environment-variable keys.
- Avoid cryptic abbreviations.
- Keep filenames consistent with the surrounding folder.
- Let the configured formatter/linter decide mechanical formatting; do not fight it with manual style differences.

## 10. Comments and documentation

Comments should explain intent, constraints, or non-obvious behaviour—not narrate every line.

Good comment:
> Keep this bucket private because original notices may contain information that should not be publicly accessible before publication.

Avoid comments that merely restate code.

Update the relevant project document when an approved change affects:
- product scope;
- module ownership or boundaries;
- API request/response shapes;
- database schema or status values;
- security or publication rules;
- setup or deployment instructions.

## 11. What not to do

- Do not rewrite unrelated files to match personal preferences.
- Do not add dependencies without checking whether the repository already has an equivalent.
- Do not silently change API response fields or database columns.
- Do not hard-code secrets, provider credentials, or environment-specific URLs.
- Do not trust AI output without validation.
- Do not use frontend-only permission checks for protected actions.
- Do not create speculative microservices or abstractions.
- Do not add unapproved MVP features.
- Do not claim a test passed if it was not run.

## 12. Before opening a pull request

- [ ] The change matches the issue.
- [ ] Only relevant files were changed.
- [ ] Existing conventions were followed.
- [ ] Input and error cases were considered.
- [ ] Relevant tests were run.
- [ ] No secrets or local files were committed.
- [ ] Shared contracts were not changed silently.
- [ ] Documentation was updated if needed.
- [ ] The pull request explains what changed and how it was verified.
