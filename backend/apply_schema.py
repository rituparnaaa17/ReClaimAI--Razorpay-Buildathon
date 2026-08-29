"""
Apply the ReclaimAI schema to Supabase by running it directly via the PostgREST RPC
or the Supabase Management API.

Run: python apply_schema.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.config import get_settings
settings = get_settings()

import httpx

SCHEMA_SQL = """
-- Merchants
CREATE TABLE IF NOT EXISTS merchants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  business_type TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
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

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id),
  razorpay_payment_id TEXT,
  amount DECIMAL(12,2) NOT NULL,
  currency TEXT DEFAULT 'INR',
  payment_method TEXT,
  status TEXT DEFAULT 'pending',
  failure_reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recovery Cases (denormalized with customer/transaction fields for performance)
CREATE TABLE IF NOT EXISTS recovery_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id UUID REFERENCES transactions(id),
  merchant_id UUID REFERENCES merchants(id),
  customer_name TEXT,
  customer_email TEXT,
  payment_method TEXT,
  failure_reason TEXT,
  razorpay_payment_id TEXT,
  risk_score DECIMAL(4,3),
  recovery_probability DECIMAL(4,3),
  root_cause TEXT,
  recommended_action TEXT,
  action_taken TEXT,
  status TEXT DEFAULT 'at_risk',
  amount_at_risk DECIMAL(12,2),
  amount_recovered DECIMAL(12,2),
  ai_reasoning TEXT,
  retry_count INT DEFAULT 0,
  guardrail_passed BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Logs
CREATE TABLE IF NOT EXISTS agent_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recovery_case_id UUID REFERENCES recovery_cases(id) ON DELETE CASCADE,
  step TEXT NOT NULL,
  decision TEXT,
  reason TEXT,
  confidence DECIMAL(4,3),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  result TEXT
);

-- Recovery Actions
CREATE TABLE IF NOT EXISTS recovery_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recovery_case_id UUID REFERENCES recovery_cases(id),
  action_type TEXT,
  scheduled_at TIMESTAMPTZ,
  executed_at TIMESTAMPTZ,
  status TEXT DEFAULT 'pending',
  result TEXT,
  amount_recovered DECIMAL(12,2)
);
"""


def apply_schema():
    """Apply schema via Supabase SQL editor endpoint (requires service role key)."""
    project_ref = settings.supabase_url.split("//")[1].split(".")[0]
    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"

    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }

    print(f"[*] Applying schema to project: {project_ref}")

    # Split and run each statement separately
    statements = [s.strip() for s in SCHEMA_SQL.split(";") if s.strip() and not s.strip().startswith("--")]

    # Use Supabase service role to call postgres directly via RPC
    from supabase import create_client
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

    for stmt in statements:
        if not stmt.strip():
            continue
        try:
            # Call postgres via rpc - using direct REST
            result = sb.rpc("exec_sql", {"sql": stmt + ";"}).execute()
            print(f"  OK: {stmt[:60]}...")
        except Exception as e:
            print(f"  WARN: {str(e)[:100]}")

    print("\n[+] Schema application attempted")
    print("    If tables were not created, run the SQL manually in Supabase Dashboard > SQL Editor")
    print(f"    SQL file: {os.path.abspath('../supabase/migrations/001_initial_schema.sql')}")


if __name__ == "__main__":
    apply_schema()
