-- ReclaimAI Supabase Schema
-- Run this in your Supabase SQL editor

-- ── Merchants ──────────────────────────────────────────────────────────────
CREATE TABLE merchants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  business_type TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Customers ──────────────────────────────────────────────────────────────
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  email TEXT,
  total_transactions INT DEFAULT 0,
  successful_transactions INT DEFAULT 0,
  failed_transactions INT DEFAULT 0,
  total_spent DECIMAL(12,2) DEFAULT 0,
  average_transaction_value DECIMAL(12,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Transactions ────────────────────────────────────────────────────────────
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id),
  razorpay_payment_id TEXT,
  amount DECIMAL(12,2) NOT NULL,
  currency TEXT DEFAULT 'INR',
  payment_method TEXT,
  status TEXT CHECK (status IN ('success','failed','pending','abandoned')) DEFAULT 'pending',
  failure_reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Recovery Cases ──────────────────────────────────────────────────────────
CREATE TABLE recovery_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id UUID REFERENCES transactions(id),
  merchant_id UUID REFERENCES merchants(id),
  risk_score DECIMAL(4,3),
  recovery_probability DECIMAL(4,3),
  root_cause TEXT,
  recommended_action TEXT,
  action_taken TEXT,
  status TEXT CHECK (status IN ('at_risk','processing','recovered','failed','human_review')) DEFAULT 'at_risk',
  amount_at_risk DECIMAL(12,2),
  amount_recovered DECIMAL(12,2),
  ai_reasoning TEXT,
  retry_count INT DEFAULT 0,
  guardrail_passed BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Agent Logs ──────────────────────────────────────────────────────────────
CREATE TABLE agent_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recovery_case_id UUID REFERENCES recovery_cases(id) ON DELETE CASCADE,
  step TEXT NOT NULL,
  decision TEXT,
  reason TEXT,
  confidence DECIMAL(4,3),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  result TEXT
);

-- ── Recovery Actions ────────────────────────────────────────────────────────
CREATE TABLE recovery_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recovery_case_id UUID REFERENCES recovery_cases(id),
  action_type TEXT,
  scheduled_at TIMESTAMPTZ,
  executed_at TIMESTAMPTZ,
  status TEXT DEFAULT 'pending',
  result TEXT,
  amount_recovered DECIMAL(12,2)
);

-- ── Notifications ───────────────────────────────────────────────────────────
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES customers(id),
  recovery_case_id UUID REFERENCES recovery_cases(id),
  channel TEXT CHECK (channel IN ('email','sms','whatsapp')),
  message TEXT,
  status TEXT DEFAULT 'pending',
  sent_at TIMESTAMPTZ
);

-- ── Row Level Security ──────────────────────────────────────────────────────
ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- ── Indexes ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_transactions_merchant ON transactions(merchant_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_recovery_cases_merchant ON recovery_cases(merchant_id);
CREATE INDEX idx_recovery_cases_status ON recovery_cases(status);
CREATE INDEX idx_agent_logs_case ON agent_logs(recovery_case_id);

-- ── Updated_at trigger ───────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER update_recovery_cases_updated_at
  BEFORE UPDATE ON recovery_cases
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
