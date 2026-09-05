-- Add razorpay_payment_link_id to recovery_cases table
ALTER TABLE recovery_cases ADD COLUMN IF NOT EXISTS razorpay_payment_link_id TEXT;
