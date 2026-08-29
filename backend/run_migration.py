"""
Directly execute SQL on Supabase using the Management API.
Run: python run_migration.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import httpx
from app.config import get_settings

settings = get_settings()

project_ref = settings.supabase_url.replace("https://", "").split(".")[0]
print(f"[*] Project: {project_ref}")

SQL = open(os.path.join(os.path.dirname(__file__), "..", "supabase", "migrations", "001_initial_schema.sql"), encoding="utf-8").read()

url = f"https://{project_ref}.supabase.co/rest/v1/rpc/exec"

# Use the service role key to POST raw SQL via the Supabase REST API
# We'll use the Postgres REST endpoint
headers = {
    "apikey": settings.supabase_service_role_key,
    "Authorization": f"Bearer {settings.supabase_service_role_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# The correct endpoint for running SQL is via /rest/v1/ with a function
# Most reliable: use httpx to hit the Supabase SQL API directly
sql_url = f"https://{project_ref}.supabase.co/rest/v1/"

print("Using Supabase client to run schema...")

try:
    from supabase import create_client
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

    # Test connection first
    test = sb.table("merchants").select("count", count="exact").execute()
    print(f"[OK] Tables already exist! Merchants count: {test.count}")
    print("Running seed instead...")
    import seed
    seed.main()

except Exception as e:
    error_str = str(e)
    if "PGRST205" in error_str or "schema cache" in error_str.lower():
        print("\n[!] Tables do not exist yet.")
        print("\nPlease run the schema in Supabase Dashboard:")
        print(f"  1. Go to: https://supabase.com/dashboard/project/{project_ref}/sql")
        print(f"  2. Open: supabase/migrations/001_initial_schema.sql")
        print("  3. Copy all the SQL and click 'Run'")
        print("\nThen run: python seed.py")
    else:
        print(f"[!] Error: {e}")
