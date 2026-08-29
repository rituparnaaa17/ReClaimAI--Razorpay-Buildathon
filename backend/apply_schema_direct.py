"""
Apply ReclaimAI schema via direct PostgreSQL connection to Supabase.
Run: python apply_schema_direct.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from app.config import get_settings

settings = get_settings()

# Supabase direct DB connection (pooler)
project_ref = settings.supabase_url.replace("https://", "").split(".")[0]
DB_HOST = f"aws-0-ap-south-1.pooler.supabase.com"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = f"postgres.{project_ref}"
DB_PASSWORD = settings.supabase_service_role_key  # Service role = postgres password

# Try both pooler and direct
CONNECTIONS = [
    {"host": f"db.{project_ref}.supabase.co", "port": 5432, "user": "postgres", "password": DB_PASSWORD},
    {"host": f"aws-0-ap-south-1.pooler.supabase.com", "port": 5432, "user": f"postgres.{project_ref}", "password": DB_PASSWORD},
    {"host": f"aws-0-ap-southeast-1.pooler.supabase.com", "port": 5432, "user": f"postgres.{project_ref}", "password": DB_PASSWORD},
]

SQL = """
CREATE TABLE IF NOT EXISTS merchants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  business_type TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

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

def apply():
    print(f"[*] Connecting to Supabase project: {project_ref}")
    
    for conn_info in CONNECTIONS:
        try:
            print(f"    Trying: {conn_info['host']}:{conn_info['port']}")
            conn = psycopg2.connect(
                host=conn_info["host"],
                port=conn_info["port"],
                dbname=DB_NAME,
                user=conn_info["user"],
                password=conn_info["password"],
                connect_timeout=10,
                sslmode="require",
            )
            cur = conn.cursor()
            cur.execute(SQL)
            conn.commit()
            print("[OK] Schema applied successfully!")
            cur.close()
            conn.close()
            
            # Now seed
            print("\n[*] Running seeder...")
            import seed
            seed.main()
            return True
            
        except Exception as e:
            print(f"    Failed: {str(e)[:100]}")
    
    print("\n[!] Could not connect directly. The service role key is not the DB password.")
    print("\nPlease apply the schema manually:")
    print(f"  1. Open: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print(f"  2. Copy and paste the contents of: supabase/migrations/001_initial_schema.sql")
    print(f"  3. Click 'Run'")
    print(f"  4. Then run: python seed.py")
    return False

if __name__ == "__main__":
    apply()
