#!/usr/bin/env python
"""
Apply Supabase schema via direct PostgreSQL connection.

The DB password is NOT the same as the service role JWT.
Find it in: Supabase Dashboard > Settings > Database > Connection string

Usage:
  python db_connect.py <db-password>

Or set SUPABASE_DB_PASSWORD in .env and just run:
  python db_connect.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.config import get_settings
settings = get_settings()

# Try to get DB password from args or env
db_password = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SUPABASE_DB_PASSWORD", "")

if not db_password:
    print("""
[!] No DB password provided.

To apply the schema:
1. Go to: https://supabase.com/dashboard/project/jonbnnyxfrovdaptvklr/settings/database
2. Copy the database password (shown when you reset it)
3. Run: python db_connect.py <your-db-password>

Alternatively, run the SQL directly:
1. Go to: https://supabase.com/dashboard/project/jonbnnyxfrovdaptvklr/sql/new
2. Paste the contents of: supabase/migrations/001_initial_schema.sql
3. Click Run

After schema is applied, run: python seed.py
""")
    sys.exit(0)

import psycopg2

project_ref = "jonbnnyxfrovdaptvklr"
SQL_FILE = os.path.join(os.path.dirname(__file__), "..", "supabase", "migrations", "001_initial_schema.sql")

print(f"[*] Connecting to Supabase project: {project_ref}")

conn_params = [
    # Direct connection
    {"host": f"db.{project_ref}.supabase.co", "port": 5432, "user": "postgres", "password": db_password},
    # Transaction pooler
    {"host": "aws-0-ap-south-1.pooler.supabase.com", "port": 5432, "user": f"postgres.{project_ref}", "password": db_password},
    {"host": "aws-0-ap-southeast-1.pooler.supabase.com", "port": 5432, "user": f"postgres.{project_ref}", "password": db_password},
]

for params in conn_params:
    try:
        print(f"    Trying: {params['host']}")
        conn = psycopg2.connect(
            host=params["host"], port=params["port"],
            dbname="postgres", user=params["user"],
            password=params["password"],
            connect_timeout=10, sslmode="require",
        )
        print(f"[+] Connected!")

        with open(SQL_FILE, encoding="utf-8") as f:
            sql = f.read()

        cur = conn.cursor()
        # Execute statement by statement
        import re
        statements = [s.strip() for s in re.split(r";(?=\s*(?:CREATE|ALTER|DROP|INSERT|--|\Z))", sql) if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            if stmt.strip():
                try:
                    cur.execute(stmt)
                    print(f"  OK: {stmt[:60].strip()}...")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"  SKIP (exists): {stmt[:40].strip()}")
                    else:
                        print(f"  WARN: {str(e)[:80]}")

        conn.commit()
        cur.close()
        conn.close()
        print("\n[OK] Schema applied!")

        # Run seeder
        print("\n[*] Running seeder...")
        import seed
        seed.main()
        break

    except Exception as e:
        print(f"    Failed: {str(e)[:100]}")
        continue
