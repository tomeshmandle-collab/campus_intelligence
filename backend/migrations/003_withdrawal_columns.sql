-- Migration 003: Notice Withdrawal Audit Columns
-- CAI Campus Intelligence - Centre for Artificial Intelligence, Kirori Mal College
-- Adds withdrawn_at, withdrawn_by, and withdrawal_reason columns to notices
-- per DATABASE_SCHEMA.md §4 and API_CONTRACTS.md §8.8.

ALTER TABLE notices
  ADD COLUMN IF NOT EXISTS withdrawn_at timestamptz,
  ADD COLUMN IF NOT EXISTS withdrawn_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS withdrawal_reason text;
