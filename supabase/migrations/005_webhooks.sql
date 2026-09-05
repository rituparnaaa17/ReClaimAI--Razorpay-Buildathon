-- ReclaimAI Migration: Razorpay Webhook Integration (Phase 2, Step 7)
-- Run this in your Supabase SQL editor AFTER 004_measure_money.sql

-- ── 1. Webhook event deduplication table ────────────────────────────────────
-- Stores IDs of processed events to prevent duplicate handling.
-- Note: This is simple within-batch deduplication.
-- Full distributed idempotency is reserved for Step 8.
CREATE TABLE IF NOT EXISTS processed_webhook_events (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  razorpay_event_id   TEXT        UNIQUE NOT NULL,
  event_type          TEXT        NOT NULL,
  processed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE processed_webhook_events ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_processed_webhook_events_event_id
  ON processed_webhook_events(razorpay_event_id);

CREATE INDEX IF NOT EXISTS idx_processed_webhook_events_processed_at
  ON processed_webhook_events(processed_at);

-- ── 2. Add razorpay_payment_id to recovery_cases ────────────────────────────
-- Enables lookup of a recovery case by Razorpay payment ID.
ALTER TABLE recovery_cases
  ADD COLUMN IF NOT EXISTS razorpay_payment_id TEXT;

CREATE INDEX IF NOT EXISTS idx_recovery_cases_razorpay_payment_id
  ON recovery_cases(razorpay_payment_id);

-- ── 3. Add customer_email to recovery_cases (webhook-sourced) ───────────────
ALTER TABLE recovery_cases
  ADD COLUMN IF NOT EXISTS customer_email TEXT;

-- ── 4. Add customer_name to recovery_cases (webhook-sourced) ────────────────
ALTER TABLE recovery_cases
  ADD COLUMN IF NOT EXISTS customer_name TEXT;

-- ── 5. Add failure_reason to recovery_cases ─────────────────────────────────
ALTER TABLE recovery_cases
  ADD COLUMN IF NOT EXISTS failure_reason TEXT;

-- ── 6. Add payment_method to recovery_cases ─────────────────────────────────
ALTER TABLE recovery_cases
  ADD COLUMN IF NOT EXISTS payment_method TEXT;
