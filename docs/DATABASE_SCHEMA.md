# DATABASE_SCHEMA.md

**Project:** CAI Campus Intelligence  
**Version:** 1.0  
**Status:** Implementation baseline — migration-ready after repository inspection  
**Database:** Supabase PostgreSQL  
**Companion documents:** `PRD.md`, `TECH_STACK.md`, `SYSTEM_ARCHITECTURE.md`, `API_CONTRACTS.md`, `MODULES.md`

> This document defines the intended relational data model. It is not evidence that these tables or migrations already exist. Before implementation, inspect the current Supabase project, repository migrations, and existing application queries. Do not apply this schema blindly over an existing database.

---

## 1. Design goals

The database must support the product requirements in `PRD.md` while keeping the pilot understandable and maintainable.

Core principles:

1. **Original source preservation.** Store the original notice in private storage and never overwrite it when extracted fields are corrected.
2. **Separate lifecycle dimensions.** Processing, publication, and relationship status are independent.
3. **Page-aware evidence.** Preserve page numbers and supporting passages for extracted information and search results.
4. **AI and human provenance.** Distinguish AI-extracted values from human-corrected values and record consequential edits.
5. **Public/private separation.** Public users can read only published, public-safe data. Internal processing and review data remain private.
6. **Manual intake.** The schema does not implement automatic website scraping or ERP integration.
7. **Keyword-search baseline.** PostgreSQL full-text search is required. Vector embeddings are not part of the baseline schema.
8. **No calendar feature.** There are no calendar-export tables or requirements in this baseline.

## 2. Status and controlled vocabularies

### 2.1 Processing status

Describes pipeline execution only:

- `pending`
- `processing`
- `completed`
- `failed`

### 2.2 Publication status

Describes public visibility:

- `held`
- `published`
- `withdrawn`

### 2.3 Relationship status

Describes the notice's current relationship/lifecycle state:

- `current`
- `superseded`
- `amended`
- `extended`
- `cancelled`

### 2.4 Audience role

- `student`
- `faculty`
- `staff`
- `all`
- `unspecified`

`unspecified` is not equivalent to `all`. It means the source does not support a reliable audience classification.

### 2.5 Notice date kind

- `event`
- `deadline`

Issue date remains a field on the notice. Do not store issue date as an event/deadline row.

### 2.6 Relationship type

- `amends`
- `replaces`
- `extends`
- `cancels`

### 2.7 Other controlled values

Notice categories:
- `academic`
- `examination`
- `admissions`
- `events_workshops`
- `faculty`
- `administration`
- `general`
- `other`

Error report status:
- `open`
- `resolved`
- `dismissed`

Processing event outcome:
- `started`
- `ok`
- `failed`

## 3. Tables at a glance

| Table | Purpose |
|---|---|
| `departments` | Optional descriptive department vocabulary |
| `profiles` | Application roles linked to Supabase Auth users |
| `notices` | One record per uploaded official notice |
| `notice_targets` | Audience roles and optional descriptive targeting detail |
| `notice_dates` | Event dates and deadlines |
| `action_items` | Actions requested by a notice |
| `notice_relations` | Evidence-backed links between earlier and later notices |
| `notice_chunks` | Page-aware extracted text for keyword search and Ask retrieval |
| `field_sources` | Evidence and provenance for extracted/corrected fields |
| `extraction_runs` | AI output and validation results |
| `notice_edits` | Audit trail of human corrections |
| `error_reports` | Public reports requiring uploader review |
| `processing_events` | Step-by-step processing history |

## 4. Proposed SQL schema

The SQL below is a starting migration definition. Review names, constraints, and existing migrations before applying it. Run migrations through the repository's agreed migration workflow, not by manually changing production tables.

```sql
-- Required extension for UUID generation.
create extension if not exists pgcrypto;

-- -------------------------------------------------------------------
-- ENUMS
-- -------------------------------------------------------------------

create type processing_status as enum (
  'pending', 'processing', 'completed', 'failed'
);

create type publication_status as enum (
  'held', 'published', 'withdrawn'
);

create type relationship_status as enum (
  'current', 'superseded', 'amended', 'extended', 'cancelled'
);

create type audience_role as enum (
  'student', 'faculty', 'staff', 'all', 'unspecified'
);

create type date_kind as enum ('event', 'deadline');

create type relation_type as enum (
  'amends', 'replaces', 'extends', 'cancels'
);

create type report_status as enum ('open', 'resolved', 'dismissed');

create type notice_category as enum (
  'academic',
  'examination',
  'admissions',
  'events_workshops',
  'faculty',
  'administration',
  'general',
  'other'
);

create type processing_event_outcome as enum (
  'started', 'ok', 'failed'
);

-- -------------------------------------------------------------------
-- DEPARTMENTS
-- -------------------------------------------------------------------

create table departments (
  id          smallint generated always as identity primary key,
  name        text not null unique,
  short_code  text unique,
  active      boolean not null default true,
  created_at  timestamptz not null default now()
);

-- -------------------------------------------------------------------
-- APPLICATION PROFILES
-- -------------------------------------------------------------------

-- A profile row is created only through the approved administrator
-- process, with an explicit role. There is deliberately no default role:
-- a signed-in user with no profile row has no application role and is
-- not authorized.

create table profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  full_name   text,
  role        text not null
              check (role in ('uploader', 'admin')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- -------------------------------------------------------------------
-- NOTICES
-- -------------------------------------------------------------------

create table notices (
  id                   uuid primary key default gen_random_uuid(),
  title                text,
  reference_number     text,
  source_url           text,
  storage_path         text not null unique,
  original_filename    text not null,
  mime_type            text not null,
  file_size_bytes      bigint check (file_size_bytes > 0),
  page_count           integer check (page_count > 0),
  summary              text,
  category             notice_category,
  issuing_authority    text,
  issue_date           date,

  processing_status    processing_status not null default 'pending',
  publication_status   publication_status not null default 'held',
  relationship_status  relationship_status not null default 'current',

  overall_confidence   numeric(3,2)
                       check (overall_confidence between 0 and 1),
  hold_reason          text,
  needs_attention      boolean not null default false,

  uploaded_by          uuid references profiles(id) on delete set null,
  uploaded_at          timestamptz not null default now(),
  published_at         timestamptz,
  published_by         uuid references profiles(id) on delete set null,
  withdrawn_at         timestamptz,
  withdrawn_by         uuid references profiles(id) on delete set null,
  withdrawal_reason    text,
  updated_at           timestamptz not null default now(),

  search_tsv tsvector generated always as (
    to_tsvector(
      'english',
      coalesce(title, '') || ' ' ||
      coalesce(reference_number, '') || ' ' ||
      coalesce(summary, '') || ' ' ||
      coalesce(issuing_authority, '')
    )
  ) stored
);

-- published_by is null when a notice was published automatically by the
-- processing workflow; it holds the reviewer when a held notice is
-- published by a human.

create index notices_publication_status_idx
  on notices (publication_status, relationship_status);

create index notices_published_at_idx
  on notices (published_at desc);

create index notices_issue_date_idx
  on notices (issue_date desc);

create index notices_category_idx
  on notices (category);

create index notices_reference_number_idx
  on notices (reference_number);

create index notices_search_tsv_idx
  on notices using gin (search_tsv);

-- -------------------------------------------------------------------
-- NOTICE AUDIENCE TARGETS
-- -------------------------------------------------------------------

-- Each row describes one audience target.
-- Department/year are descriptive filters only in the initial MVP.
-- A null department/year means no narrower value was specified.
-- An 'all' role means the notice applies to every audience.
-- 'unspecified' must not be interpreted as 'all'.

create table notice_targets (
  id             bigint generated always as identity primary key,
  notice_id      uuid not null references notices(id) on delete cascade,
  role           audience_role not null,
  department_id  smallint references departments(id) on delete set null,
  year           smallint check (year between 1 and 6),
  detail         text,
  created_at     timestamptz not null default now()
);

create index notice_targets_notice_idx
  on notice_targets (notice_id);

create index notice_targets_filter_idx
  on notice_targets (role, department_id, year);

-- -------------------------------------------------------------------
-- NOTICE DATES
-- -------------------------------------------------------------------

create table notice_dates (
  id            bigint generated always as identity primary key,
  notice_id     uuid not null references notices(id) on delete cascade,
  kind          date_kind not null,
  label         text,
  starts_on     date not null,
  ends_on       date,
  starts_time   time,
  original_text text,
  source_page   integer check (source_page > 0),
  created_at    timestamptz not null default now(),
  check (ends_on is null or ends_on >= starts_on)
);

create index notice_dates_notice_idx
  on notice_dates (notice_id);

create index notice_dates_upcoming_idx
  on notice_dates (kind, starts_on);

-- -------------------------------------------------------------------
-- ACTION ITEMS
-- -------------------------------------------------------------------

create table action_items (
  id             bigint generated always as identity primary key,
  notice_id      uuid not null references notices(id) on delete cascade,
  description    text not null,
  role           audience_role,
  department_id  smallint references departments(id) on delete set null,
  year           smallint check (year between 1 and 6),
  due_date       date,
  source_page    integer check (source_page > 0),
  created_at     timestamptz not null default now()
);

create index action_items_notice_idx
  on action_items (notice_id);

create index action_items_due_date_idx
  on action_items (due_date);

-- -------------------------------------------------------------------
-- NOTICE RELATIONSHIPS
-- -------------------------------------------------------------------

create table notice_relations (
  id            bigint generated always as identity primary key,
  earlier_id    uuid not null references notices(id) on delete cascade,
  later_id      uuid not null references notices(id) on delete cascade,
  relation      relation_type not null,
  basis         text not null
                check (basis in ('explicit_reference', 'human_confirmed')),
  evidence_page integer check (evidence_page > 0),
  evidence_text text,
  confidence    numeric(3,2) check (confidence between 0 and 1),
  confirmed     boolean not null default false,
  confirmed_by  uuid references profiles(id) on delete set null,
  created_at    timestamptz not null default now(),
  check (earlier_id <> later_id),
  unique (earlier_id, later_id, relation)
);

create index notice_relations_earlier_idx
  on notice_relations (earlier_id);

create index notice_relations_later_idx
  on notice_relations (later_id);

-- -------------------------------------------------------------------
-- PAGE-AWARE TEXT CHUNKS
-- -------------------------------------------------------------------

-- Baseline uses PostgreSQL full-text search only.
-- No embedding/vector column is included in this version.

create table notice_chunks (
  id           bigint generated always as identity primary key,
  notice_id    uuid not null references notices(id) on delete cascade,
  page_number  integer not null check (page_number > 0),
  chunk_index  integer not null check (chunk_index >= 0),
  chunk_text   text not null,
  tsv          tsvector generated always as (
    to_tsvector('english', chunk_text)
  ) stored,
  created_at   timestamptz not null default now(),
  unique (notice_id, page_number, chunk_index)
);

create index notice_chunks_notice_page_idx
  on notice_chunks (notice_id, page_number);

create index notice_chunks_tsv_idx
  on notice_chunks using gin (tsv);

-- -------------------------------------------------------------------
-- FIELD SOURCE / PROVENANCE
-- -------------------------------------------------------------------

create table field_sources (
  id             bigint generated always as identity primary key,
  notice_id      uuid not null references notices(id) on delete cascade,
  field_name     text not null,
  value_text     text,
  source_page    integer check (source_page > 0),
  source_quote   text,
  extraction_method text not null default 'ai'
                   check (extraction_method in ('ai', 'human')),
  confidence     numeric(3,2) check (confidence between 0 and 1),
  verified       boolean not null default false,
  human_edited   boolean not null default false,
  created_at     timestamptz not null default now()
);

create index field_sources_notice_idx
  on field_sources (notice_id);

create index field_sources_field_idx
  on field_sources (notice_id, field_name);

-- -------------------------------------------------------------------
-- EXTRACTION RUNS
-- -------------------------------------------------------------------

create table extraction_runs (
  id                 bigint generated always as identity primary key,
  notice_id          uuid not null references notices(id) on delete cascade,
  provider           text not null default 'gemini',
  model              text not null,
  raw_output         jsonb,
  validation_errors  jsonb,
  passed             boolean not null default false,
  created_at         timestamptz not null default now()
);

create index extraction_runs_notice_idx
  on extraction_runs (notice_id, created_at desc);

-- -------------------------------------------------------------------
-- HUMAN EDIT HISTORY
-- -------------------------------------------------------------------

create table notice_edits (
  id          bigint generated always as identity primary key,
  notice_id   uuid not null references notices(id) on delete cascade,
  edited_by   uuid not null references profiles(id),
  field_name  text not null,
  old_value   text,
  new_value   text,
  note        text,
  edited_at   timestamptz not null default now()
);

create index notice_edits_notice_idx
  on notice_edits (notice_id, edited_at desc);

-- -------------------------------------------------------------------
-- PUBLIC ERROR REPORTS
-- -------------------------------------------------------------------

create table error_reports (
  id               bigint generated always as identity primary key,
  notice_id        uuid not null references notices(id) on delete cascade,
  issue_type       text not null,
  description      text,
  status           report_status not null default 'open',
  created_at       timestamptz not null default now(),
  resolved_by      uuid references profiles(id) on delete set null,
  resolved_at      timestamptz,
  resolution_note  text
);

create index error_reports_open_idx
  on error_reports (status, created_at);

-- -------------------------------------------------------------------
-- PROCESSING EVENTS
-- -------------------------------------------------------------------

create table processing_events (
  id          bigint generated always as identity primary key,
  notice_id   uuid not null references notices(id) on delete cascade,
  step        text not null,
  outcome     processing_event_outcome not null,
  message     text,
  created_at  timestamptz not null default now()
);

create index processing_events_notice_idx
  on processing_events (notice_id, created_at);
```

## 5. Important modeling rules

### 5.1 Dates

- `notices.issue_date` stores the issue date.
- `notice_dates.kind = 'event'` stores an event date or date range.
- `notice_dates.kind = 'deadline'` stores a deadline.
- `action_items.due_date` stores the due date of a specific action only when the source supports it.
- Do not infer a deadline from an event date.
- Preserve `original_text` when the date wording is ambiguous or needs source context.

### 5.2 Audience

The initial audience role is one of `student`, `faculty`, `staff`, `all`, or `unspecified`.

- `all` means the source notice applies to all audience groups.
- `unspecified` means the source does not establish the audience.
- Do not convert `unspecified` to `all`.
- Department/year/detail values retain descriptive wording. Department/year filtering is not an application permission system.
- Audience matching for a selected audience follows the PRD:
  - `student`, `faculty`, or `staff`: notices with a matching target role, plus notices targeted to `all`;
  - `unspecified`: only notices whose audience is `unspecified`;
  - no filter (the selector's "All" view): every eligible published notice, with `unspecified` notices shown as "Not specified".
- A notice with an `unspecified` audience never matches `student`, `faculty`, or `staff`, and is never displayed as if it applies to everyone.

### 5.3 Provenance

For every critical extracted field, store a source record where evidence is available:
- field name;
- extracted/corrected value;
- source page;
- supporting quote;
- extraction method;
- confidence metadata where supplied;
- whether backend verification found the quote in extracted text;
- whether the value was human-edited.

A source quote being present in extracted text is useful validation, but it does not prove that the model interpreted the quote correctly. Critical values still require type, date, and semantic checks.

### 5.4 Status separation

Never use one generic `status` field to represent all workflow states.

| Dimension | Column | Values |
|---|---|---|
| Processing | `processing_status` | pending, processing, completed, failed |
| Publication | `publication_status` | held, published, withdrawn |
| Relationship | `relationship_status` | current, superseded, amended, extended, cancelled |

### 5.5 Original file and privacy

- `storage_path` points to a private storage object.
- The path itself must not be exposed publicly.
- The original object must not be overwritten when corrections are made.
- Public access should be issued only after publication and through the approved signed-link or backend-mediated mechanism.
- Notices containing personal/sensitive information require a separate handling decision before upload/publication.

### 5.6 Publication and withdrawal audit

- `published_at` and `published_by` record when and by whom a notice was published. `published_by` is null for automatic publication by the processing workflow.
- `withdrawn_at`, `withdrawn_by`, and `withdrawal_reason` record a withdrawal. Withdrawal never deletes the notice.
- Content corrections are recorded in `notice_edits`.
- Resolution or dismissal of public reports records the resolving uploader (`resolved_by`), timestamp (`resolved_at`), and optional explanation (`resolution_note`) in `error_reports`.

### 5.7 Status transitions

The backend validates every transition; the database does not enforce them by itself. An invalid transition returns `409` (`API_CONTRACTS.md` §9). The rules below are derived from the routes and rules in `API_CONTRACTS.md` and the PRD.

**Processing status**

| From | To | Trigger |
|---|---|---|
| (new) | `pending` | Upload accepted and original stored |
| `pending` | `processing` | Pipeline starts |
| `processing` | `completed` | Pipeline finishes |
| `processing` | `failed` | A step fails, or a stale record is recovered |
| `failed`, or `completed` with `held` publication | `pending` | Authorized retry |

**Publication status**

| From | To | Trigger |
|---|---|---|
| (new) | `held` | Upload accepted |
| `held` | `published` | Automatic publication after all blocking checks pass, or explicit authorized publish after review |
| `held` | `withdrawn` | Authorized withdrawal |
| `published` | `withdrawn` | Authorized withdrawal |

No route in this baseline moves a notice out of `withdrawn`.

**Relationship status** applies to the earlier notice when a relationship is confirmed. The later notice stays `current`.

| Confirmed relation | Earlier notice becomes |
|---|---|
| `amends` | `amended` |
| `replaces` | `superseded` |
| `extends` | `extended` |
| `cancels` | `cancelled` |

Rejecting a relationship leaves both notices' statuses unchanged. An unconfirmed relationship never changes any notice's status.

### 5.8 Database to API mapping conventions

When transforming database rows into the JSON payloads defined in `API_CONTRACTS.md`:
- **Departments:** `notice_targets.department_id` and `action_items.department_id` reference `departments(id)`. When serializing API responses (`API_CONTRACTS.md` §5.4, §5.6), the backend resolves this relationship to output the string department name or `null`, rather than the raw database integer key.
- **Text excerpts and source evidence:**
  - `notice_dates.original_text` stores the raw date snippet from the notice; in corrections (`API_CONTRACTS.md` §8.5), it is passed as `source_quote`.
  - `field_sources.source_quote` stores field extraction provenance.
  - `notice_relations.evidence_text` stores text justifying a relationship.
  - `notice_chunks.chunk_text` stores searchable text chunks, projected as `matched_text` in keyword search results (`API_CONTRACTS.md` §7.6) and `excerpt` in Ask citations (`API_CONTRACTS.md` §7.7).

## 6. Access control and RLS

Application data is read and written only through the FastAPI backend (see `SYSTEM_ARCHITECTURE.md` §4 and `API_CONTRACTS.md`). The browser does not query application tables directly, so Supabase's `anon` and `authenticated` roles must have no direct grants on application tables.

RLS must still be enabled for every application table exposed through Supabase APIs. The policies below are defence in depth: they define the intended public-safe boundary in case a table is ever exposed. They are a policy design guide, not a complete production security audit. Confirm effective grants and test with public and uploader identities.

### 6.1 Tables that must not be publicly readable

At minimum:
- `profiles`
- `field_sources`
- `extraction_runs`
- `notice_edits`
- `error_reports`
- `processing_events`

Public error reports must be inserted by the backend after validation and rate limiting. Do not grant anonymous clients unrestricted insert access to `error_reports`.

### 6.2 Public read policy shape

Public reads should be restricted to published notices and child rows whose parent notice is published. Relationships must additionally be confirmed.

Example policy pattern:

```sql
alter table notices enable row level security;
alter table notice_targets enable row level security;
alter table notice_dates enable row level security;
alter table action_items enable row level security;
alter table notice_relations enable row level security;
alter table notice_chunks enable row level security;
alter table departments enable row level security;

-- Internal tables also have RLS enabled. No anonymous/public policies
-- are created for these tables; privileged access is handled by the backend.
alter table profiles enable row level security;
alter table field_sources enable row level security;
alter table extraction_runs enable row level security;
alter table notice_edits enable row level security;
alter table error_reports enable row level security;
alter table processing_events enable row level security;

create policy public_read_published_notices
on notices for select
using (publication_status = 'published');

create policy public_read_published_targets
on notice_targets for select
using (
  exists (
    select 1 from notices n
    where n.id = notice_targets.notice_id
      and n.publication_status = 'published'
  )
);

create policy public_read_published_dates
on notice_dates for select
using (
  exists (
    select 1 from notices n
    where n.id = notice_dates.notice_id
      and n.publication_status = 'published'
  )
);

create policy public_read_published_actions
on action_items for select
using (
  exists (
    select 1 from notices n
    where n.id = action_items.notice_id
      and n.publication_status = 'published'
  )
);

create policy public_read_published_chunks
on notice_chunks for select
using (
  exists (
    select 1 from notices n
    where n.id = notice_chunks.notice_id
      and n.publication_status = 'published'
  )
);

create policy public_read_published_relations
on notice_relations for select
using (
  confirmed = true
  and exists (
    select 1 from notices n
    where n.id = notice_relations.earlier_id
      and n.publication_status = 'published'
  )
  and exists (
    select 1 from notices n
    where n.id = notice_relations.later_id
      and n.publication_status = 'published'
  )
);

create policy public_read_active_departments
on departments for select
using (active = true);
```

Important:
- The policy examples do not replace a complete grant review.
- Row-level policies cannot hide individual columns. If direct public reads of `notices` were ever approved, grant `SELECT` only on public-safe columns and exclude at least `storage_path`, `source_url`, `hold_reason`, `needs_attention`, `overall_confidence`, `uploaded_by`, `published_by`, `withdrawn_by`, and `withdrawal_reason`.
- Do not add anonymous `INSERT`, `UPDATE`, or `DELETE` policies to application tables.
- All privileged writes are performed by the backend after authorization.
- Test that relationships do not expose a private notice through the other side of a relationship, and that unconfirmed relationships are never readable publicly.
- If the backend uses the service-role key, it bypasses RLS; therefore backend authorization and query filters remain mandatory.

## 7. Key query patterns

### 7.1 Upcoming dates

The query must filter to published notices, exclude cancelled/superseded records, and apply the audience rules agreed in the PRD (§7.5) and `API_CONTRACTS.md` (§5.1).

Conceptual SQL:

```sql
select
  n.id,
  n.title,
  n.relationship_status,
  d.kind,
  d.label,
  d.starts_on,
  d.source_page
from notice_dates d
join notices n on n.id = d.notice_id
where n.publication_status = 'published'
  and n.relationship_status not in ('superseded', 'cancelled')
  and d.starts_on >= current_date
order by d.starts_on asc;
```

Audience matching is applied through `notice_targets` using the selected audience and any approved descriptive filters. Do not assume that an `unspecified` target matches every audience.

`current_date` uses the database time zone (UTC by default on Supabase). Evaluate “today” and “this week” in the college's local time zone, which is an open decision in `API_CONTRACTS.md` §13, so that day boundaries are correct for users.

### 7.2 Recently posted

Order published notices by `published_at desc`, with a bounded result count.

### 7.3 Recent changes

Use confirmed `notice_relations` where the later notice is published. Show the relationship type and link both notices where both are publicly visible.

### 7.4 Keyword search

Search `notices.search_tsv` and `notice_chunks.tsv`, applying publication and audience eligibility filters before returning results. Preserve the chunk's `page_number` in the response.

### 7.5 Exception queue

The uploader queue includes:
- notices with `publication_status = 'held'`;
- notices with `needs_attention = true`;
- failed processing records requiring action;
- open error reports (served through `GET /api/v1/uploader/reports` and presented alongside the notice queue).

The backend must return only records the requesting uploader is authorized to review.

## 8. Indexing and performance notes

- Use indexes for common publication, category, date, reference-number, audience, and notice-relationship lookups.
- Keep full-text indexes on notice metadata and page-aware text chunks.
- Add or change indexes only when supported by query patterns and measured needs.
- Do not add vector indexes or an embedding column to the baseline migration.
- If semantic search is later approved, create a separate migration after the embedding model and vector dimension are confirmed.

## 9. Seed and configuration data

- Department rows are populated from an approved college department list.
- Public sign-up is disabled in Supabase Auth.
- Uploader accounts are provisioned through the approved administrator process and linked to `profiles` with an explicit role. A signed-in user without a `profiles` row has no application role and is not authorized.
- The original-file storage bucket is private.
- File-size, page-count, and batch limits are application configuration values; they are not silently inferred from this schema.

## 10. Migration and implementation checklist

Before applying the schema:

- [ ] Inspect existing migrations and database objects.
- [ ] Confirm that enum/table names do not already exist.
- [ ] Reconcile this document with `API_CONTRACTS.md`.
- [ ] Confirm Supabase Auth profile creation and role provisioning.
- [ ] Confirm RLS and effective grants for every table.
- [ ] Confirm private storage bucket and object access policy.
- [ ] Test public access using an anonymous client.
- [ ] Test uploader access using a normal uploader account.
- [ ] Test admin-only operations using an admin account.
- [ ] Test that held and withdrawn records never appear in public search or Ask.
- [ ] Test that an unpublished notice cannot leak through relationship queries.
- [ ] Run migrations against a disposable development project before any shared environment.

## 11. Open implementation decisions

The following require explicit decisions before production use:

1. Final department list and whether postgraduate year ranges need to be represented.
2. Final file-size, page-count, and bulk-upload limits.
3. Retention rules for raw AI output and processing logs.
4. Whether public error reports need an issue-type enum or a controlled text vocabulary.
5. Whether notice body text is exposed publicly or only excerpts and the original source are shown.
6. Whether multilingual search needs a different PostgreSQL text-search configuration.
7. Whether semantic search is later justified; if so, model, dimension, and migration are a separate decision.
8. Which relationship status applies when several confirmed relationships affect the same earlier notice.
9. Whether the earlier notice's status changes at the moment a relationship is confirmed, or only once the later notice is published.

**Maintenance:** The Project Lead maintains this document. Every schema change must be reflected in migrations, API contracts, tests, and any affected module documentation.
