-- ReclaimAI Migration: Measure Actual Money (Phase 1, Step 6)
-- Run this in your Supabase SQL editor AFTER 003_batch_engine.sql

-- ── Add recovered_amount to recovery_batches ─────────────────────────────────
-- Tracks the sum of verified captured Razorpay payment amounts for the batch.
-- Only genuinely captured (status = 'captured') payments contribute.
-- Payment Link creation does NOT contribute.
-- Uses DECIMAL(14,2) to match the existing amount column convention (rupees).

ALTER TABLE recovery_batches
  ADD COLUMN IF NOT EXISTS recovered_amount DECIMAL(14,2) NOT NULL DEFAULT 0;

-- Index for querying high-value batches
CREATE INDEX IF NOT EXISTS idx_recovery_batches_recovered_amount
  ON recovery_batches(recovered_amount);
