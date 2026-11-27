-- Migration 002: Review Audit Logging, Field Sources, and Lifecycle Columns
-- CAI Campus Intelligence - Centre for Artificial Intelligence, Kirori Mal College
-- Adds audit trail (notice_edits), field evidence (field_sources), processing history
-- (processing_events), and lifecycle columns on notices (relationship_status, published_at, published_by).

-- -----------------------------------------------------------------------------
-- 1. EXTEND NOTICES TABLE WITH LIFECYCLE & PUBLICATION AUDIT COLUMNS
-- -----------------------------------------------------------------------------

ALTER TABLE notices
  ADD COLUMN IF NOT EXISTS relationship_status relationship_status NOT NULL DEFAULT 'current',
  ADD COLUMN IF NOT EXISTS published_at timestamptz,
  ADD COLUMN IF NOT EXISTS published_by uuid REFERENCES profiles(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS notices_pub_rel_status_idx
  ON notices (publication_status, relationship_status);

CREATE INDEX IF NOT EXISTS notices_published_at_idx
  ON notices (published_at DESC);

-- -----------------------------------------------------------------------------
-- 2. FIELD_SOURCES TABLE
-- -----------------------------------------------------------------------------
-- Evidence and provenance for AI-extracted and human-corrected fields.

CREATE TABLE IF NOT EXISTS field_sources (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  notice_id         uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  field_name        text NOT NULL,
  value_text        text,
  source_page       integer CHECK (source_page > 0),
  source_quote      text,
  extraction_method text NOT NULL DEFAULT 'ai'
                    CHECK (extraction_method IN ('ai', 'human')),
  confidence        numeric(3,2) CHECK (confidence BETWEEN 0 AND 1),
  verified          boolean NOT NULL DEFAULT false,
  human_edited      boolean NOT NULL DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS field_sources_notice_idx
  ON field_sources (notice_id);

CREATE INDEX IF NOT EXISTS field_sources_field_idx
  ON field_sources (notice_id, field_name);

-- -----------------------------------------------------------------------------
-- 3. NOTICE_EDITS TABLE
-- -----------------------------------------------------------------------------
-- Immutable audit trail of human field corrections during review.

CREATE TABLE IF NOT EXISTS notice_edits (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  notice_id   uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  edited_by   uuid NOT NULL REFERENCES profiles(id),
  field_name  text NOT NULL,
  old_value   text,
  new_value   text,
  note        text,
  edited_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notice_edits_notice_idx
  ON notice_edits (notice_id, edited_at DESC);

-- -----------------------------------------------------------------------------
-- 4. PROCESSING_EVENTS TABLE
-- -----------------------------------------------------------------------------
-- Step-by-step processing, retry, relationship, and publication history.

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_event_outcome') THEN
    CREATE TYPE processing_event_outcome AS ENUM (
      'started', 'ok', 'failed'
    );
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS processing_events (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  notice_id   uuid NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
  step        text NOT NULL,
  outcome     processing_event_outcome NOT NULL,
  message     text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS processing_events_notice_idx
  ON processing_events (notice_id, created_at);

-- -----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) & GRANTS REVOCATION
-- -----------------------------------------------------------------------------
-- Internal audit and provenance tables must never be publicly readable.

ALTER TABLE field_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE notice_edits ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated;

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
    GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;
  END IF;
END $$;
