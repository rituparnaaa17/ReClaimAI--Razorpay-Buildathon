-- ReclaimAI Supabase Schema Migration: Recovery Case State Machine
-- Run this in your Supabase SQL editor

-- 1. Drop existing check constraint and add the expanded one
ALTER TABLE recovery_cases DROP CONSTRAINT IF EXISTS recovery_cases_status_check;

ALTER TABLE recovery_cases ADD CONSTRAINT recovery_cases_status_check
CHECK (status IN (
  -- Legacy states (kept for backward compatibility)
  'at_risk', 'processing', 'human_review',
  -- New semantic states
  'detected', 'analyzing', 'predicting', 'deciding',
  'action_required', 'approved', 'recovering', 'verifying',
  'recovered', 'failed', 'escalated', 'no_action', 'expired'
));

-- 2. Create the recovery_case_transitions table for audit logs
CREATE TABLE IF NOT EXISTS recovery_case_transitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recovery_case_id UUID REFERENCES recovery_cases(id) ON DELETE CASCADE,
  from_state TEXT,
  to_state TEXT NOT NULL,
  reason TEXT,
  source TEXT,
  actor TEXT,
  action TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Row Level Security for new table
ALTER TABLE recovery_case_transitions ENABLE ROW LEVEL SECURITY;

-- 4. Indexes for new table
CREATE INDEX IF NOT EXISTS idx_recovery_case_transitions_case ON recovery_case_transitions(recovery_case_id);
CREATE INDEX IF NOT EXISTS idx_recovery_case_transitions_created_at ON recovery_case_transitions(created_at);
