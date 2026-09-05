-- ReclaimAI Migration: Batch Recovery Engine
-- Run this in the Supabase SQL editor AFTER 002_state_machine.sql

-- ── Recovery Batches ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recovery_batches (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id   UUID        REFERENCES merchants(id),
  status        TEXT        NOT NULL
                CHECK (status IN ('created','running','completed','partial_failure','failed'))
                DEFAULT 'created',
  -- Case counters (updated atomically as batch progresses)
  total_cases       INT     NOT NULL DEFAULT 0,
  processed_cases   INT     NOT NULL DEFAULT 0,
  successful_cases  INT     NOT NULL DEFAULT 0,
  failed_cases      INT     NOT NULL DEFAULT 0,
  skipped_cases     INT     NOT NULL DEFAULT 0,
  -- Batch-level failure message (only set when status = 'failed')
  error_message TEXT,
  -- Timestamps
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at    TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ
);

-- Row Level Security
ALTER TABLE recovery_batches ENABLE ROW LEVEL SECURITY;

-- Indexes for common access patterns
CREATE INDEX IF NOT EXISTS idx_recovery_batches_merchant
  ON recovery_batches(merchant_id);

CREATE INDEX IF NOT EXISTS idx_recovery_batches_status
  ON recovery_batches(status);

CREATE INDEX IF NOT EXISTS idx_recovery_batches_created_at
  ON recovery_batches(created_at DESC);
