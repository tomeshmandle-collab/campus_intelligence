-- Migration 001: Initial Schema
-- CAI Campus Intelligence - Centre for Artificial Intelligence, Kirori Mal College
-- Implements baseline tables, types, constraints, indexes, and Row Level Security (RLS).
-- All application data access is mediated through FastAPI using the service role key.

-- Required extension for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- ENUMS & TYPES
-- -----------------------------------------------------------------------------

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_status') THEN
    CREATE TYPE processing_status AS ENUM (
      'pending', 'processing', 'completed', 'failed'
    );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'publication_status') THEN
    CREATE TYPE publication_status AS ENUM (
      'held', 'published', 'withdrawn'
    );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audience_role') THEN
    CREATE TYPE audience_role AS ENUM (
      'student', 'faculty', 'staff', 'all', 'unspecified'
    );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notice_category') THEN
    CREATE TYPE notice_category AS ENUM (
      'academic',
      'examination',
      'admissions',
      'events_workshops',
      'faculty',
      'administration',
      'general',
      'other'
    );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relation_type') THEN
    CREATE TYPE relation_type AS ENUM (
      'amends', 'replaces', 'extends', 'cancels'
    );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relationship_status') THEN
    CREATE TYPE relationship_status AS ENUM (
      'current', 'superseded', 'amended', 'extended', 'cancelled'
    );
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_status') THEN
    CREATE TYPE report_status AS ENUM (
      'open', 'resolved', 'dismissed'
    );
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 1. PROFILES TABLE
-- -----------------------------------------------------------------------------
-- Application roles linked to Supabase Auth users.
-- A signed-in user without a profile row has no application role and is not authorized.

CREATE TABLE IF NOT EXISTS profiles (
  id          uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name   text,
  role        text NOT NULL CHECK (role IN ('uploader', 'admin')),
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2. NOTICES TABLE
-- -----------------------------------------------------------------------------
-- Canonical notice records with separate status dimensions.

CREATE TABLE IF NOT EXISTS notices (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title               text,
  notice_date         date,
  deadline_date       date,
  audience            audience_role NOT NULL DEFAULT 'unspecified',
  category            notice_category,
  summary             text,
  storage_path        text NOT NULL UNIQUE,
  processing_status   processing_status NOT NULL DEFAULT 'pending',
  publication_status  publication_status NOT NULL DEFAULT 'held',
  review_reasons      jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notices_publication_status_idx
  ON notices (publication_status);

CREATE INDEX IF NOT EXISTS notices_notice_date_idx
  ON notices (notice_date DESC);

CREATE INDEX IF NOT EXISTS notices_deadline_date_idx
  ON notices (deadline_date ASC);

CREATE INDEX IF NOT EXISTS notices_audience_idx
  ON notices (audience);

CREATE INDEX IF NOT EXISTS notices_category_idx
  ON notices (category);

-- -----------------------------------------------------------------------------
-- 3. NOTICE_PAGES TABLE
-- -----------------------------------------------------------------------------
-- Page-aware extracted text and scanned status per page.

CREATE TABLE IF NOT EXISTS notice_pages (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  notice_id       uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  page_number     integer NOT NULL CHECK (page_number > 0),
  extracted_text  text,
  is_scanned      boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT notice_pages_notice_page_uniq UNIQUE (notice_id, page_number)
);

CREATE INDEX IF NOT EXISTS notice_pages_notice_id_idx
  ON notice_pages (notice_id);

CREATE INDEX IF NOT EXISTS notice_pages_page_number_idx
  ON notice_pages (notice_id, page_number);

-- -----------------------------------------------------------------------------
-- 4. NOTICE_CHUNKS TABLE
-- -----------------------------------------------------------------------------
-- Page-aware extracted text chunks for keyword search and Ask retrieval.

CREATE TABLE IF NOT EXISTS notice_chunks (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  notice_id       uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  page_number     integer NOT NULL CHECK (page_number > 0),
  chunk_text      text NOT NULL,
  search_vector   tsvector GENERATED ALWAYS AS (
    to_tsvector('english', chunk_text)
  ) STORED,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notice_chunks_notice_id_idx
  ON notice_chunks (notice_id);

CREATE INDEX IF NOT EXISTS notice_chunks_notice_page_idx
  ON notice_chunks (notice_id, page_number);

CREATE INDEX IF NOT EXISTS notice_chunks_search_vector_idx
  ON notice_chunks USING gin (search_vector);

-- -----------------------------------------------------------------------------
-- 5. NOTICE_RELATIONSHIPS TABLE
-- -----------------------------------------------------------------------------
-- Evidence-backed links between earlier and later notices.

CREATE TABLE IF NOT EXISTS notice_relationships (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  earlier_id      uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  later_id        uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  relation        relation_type NOT NULL,
  basis           text NOT NULL DEFAULT 'explicit_reference'
                  CHECK (basis IN ('explicit_reference', 'human_confirmed')),
  evidence_page   integer CHECK (evidence_page > 0),
  evidence_text   text,
  confidence      numeric(3,2) CHECK (confidence BETWEEN 0 AND 1),
  confirmed       boolean NOT NULL DEFAULT false,
  confirmed_by    uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT notice_relationships_diff_notices CHECK (earlier_id <> later_id),
  CONSTRAINT notice_relationships_uniq UNIQUE (earlier_id, later_id, relation)
);

CREATE INDEX IF NOT EXISTS notice_relationships_earlier_idx
  ON notice_relationships (earlier_id);

CREATE INDEX IF NOT EXISTS notice_relationships_later_idx
  ON notice_relationships (later_id);

CREATE INDEX IF NOT EXISTS notice_relationships_confirmed_idx
  ON notice_relationships (confirmed);

-- -----------------------------------------------------------------------------
-- 6. ERROR_REPORTS TABLE
-- -----------------------------------------------------------------------------
-- Public error reports requiring uploader review.

CREATE TABLE IF NOT EXISTS error_reports (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  notice_id        uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  issue_type       text NOT NULL,
  description      text,
  status           report_status NOT NULL DEFAULT 'open',
  created_at       timestamptz NOT NULL DEFAULT now(),
  resolved_by      uuid REFERENCES profiles(id) ON DELETE SET NULL,
  resolved_at      timestamptz,
  resolution_note  text
);

CREATE INDEX IF NOT EXISTS error_reports_notice_id_idx
  ON error_reports (notice_id);

CREATE INDEX IF NOT EXISTS error_reports_status_idx
  ON error_reports (status, created_at);

-- -----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) - CRITICAL SECURITY REQUIREMENT
-- -----------------------------------------------------------------------------
-- Enable RLS on every single table.

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE notices ENABLE ROW LEVEL SECURITY;
ALTER TABLE notice_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notice_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE notice_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_reports ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- DIRECT TABLE GRANTS REVOCATION - CRITICAL SECURITY REQUIREMENT
-- -----------------------------------------------------------------------------
-- Application data is read and written exclusively through the FastAPI backend
-- using the service role key. The browser never queries tables directly, so
-- anon and authenticated roles hold zero grants on any public tables or routines.

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated;

-- Ensure default privileges revoke access on future tables in schema public
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON ROUTINES FROM anon, authenticated;

-- Ensure service_role has full access for backend API operations
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
    GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO service_role;
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- DEFENSE-IN-DEPTH RLS POLICIES
-- -----------------------------------------------------------------------------
-- Policies define the public-safe boundary if direct table access is ever exposed.
-- Internal tables (profiles, error_reports) have NO public policies (default-deny).

DROP POLICY IF EXISTS public_read_published_notices ON notices;
CREATE POLICY public_read_published_notices
  ON notices FOR SELECT
  USING (publication_status = 'published');

DROP POLICY IF EXISTS public_read_published_pages ON notice_pages;
CREATE POLICY public_read_published_pages
  ON notice_pages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM notices n
      WHERE n.id = notice_pages.notice_id
        AND n.publication_status = 'published'
    )
  );

DROP POLICY IF EXISTS public_read_published_chunks ON notice_chunks;
CREATE POLICY public_read_published_chunks
  ON notice_chunks FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM notices n
      WHERE n.id = notice_chunks.notice_id
        AND n.publication_status = 'published'
    )
  );

DROP POLICY IF EXISTS public_read_published_relationships ON notice_relationships;
CREATE POLICY public_read_published_relationships
  ON notice_relationships FOR SELECT
  USING (
    confirmed = true
    AND EXISTS (
      SELECT 1 FROM notices n
      WHERE n.id = notice_relationships.earlier_id
        AND n.publication_status = 'published'
    )
    AND EXISTS (
      SELECT 1 FROM notices n
      WHERE n.id = notice_relationships.later_id
        AND n.publication_status = 'published'
    )
  );
