# ReclaimAI — One-click startup script
# Double-click this file or run: .\start.ps1

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "  ██████╗ ███████╗ ██████╗ ██████╗ ██╗   ██╗███████╗██████╗  █████╗ ██╗" -ForegroundColor Green
Write-Host "  ██╔══██╗██╔════╝██╔════╝██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██║" -ForegroundColor Green
Write-Host "  ██████╔╝█████╗  ██║     ██║   ██║██║   ██║█████╗  ██████╔╝███████║██║" -ForegroundColor Green
Write-Host "  ██╔══██╗██╔══╝  ██║     ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██╔══██║██║" -ForegroundColor Green
Write-Host "  ██║  ██║███████╗╚██████╗╚██████╔╝ ╚████╔╝ ███████╗██║  ██║██║  ██║██║" -ForegroundColor Green
Write-Host "  AI-Powered Revenue Recovery  --  Razorpay Buildathon 2026" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check Python ────────────────────────────────────────────────────
Write-Host "[1/4] Checking environment..." -ForegroundColor Yellow
$py = python --version 2>&1
$node = node --version 2>&1
Write-Host "  Python: $py  |  Node: $node"

# ── Step 2: Apply Supabase schema (if needed) ───────────────────────────────
Write-Host ""
Write-Host "[2/4] Supabase schema check..." -ForegroundColor Yellow
$schemaCheck = python -c "
import sys; sys.path.insert(0, 'backend')
from supabase import create_client
from backend.app.config import get_settings
s = get_settings()
sb = create_client(s.supabase_url, s.supabase_service_role_key)
try:
    sb.table('recovery_cases').select('id').limit(1).execute()
    print('EXISTS')
except:
    print('MISSING')
" 2>&1

if ($schemaCheck -notlike "*EXISTS*") {
    Write-Host "  Tables not found. Opening Supabase SQL Editor..." -ForegroundColor Yellow
    $sqlPath = Resolve-Path "supabase\migrations\001_initial_schema.sql"
    $sqlContent = Get-Content $sqlPath -Raw
    Set-Clipboard -Value $sqlContent
    Write-Host "  SQL copied to clipboard!" -ForegroundColor Green
    Start-Process "https://supabase.com/dashboard/project/jonbnnyxfrovdaptvklr/sql/new"
    Write-Host ""
    Write-Host "  >> PASTE the SQL in the Supabase editor and click RUN" -ForegroundColor Cyan
    Write-Host "  >> Then press ENTER here to continue..." -ForegroundColor Cyan
    Read-Host
    
    # Seed the database
    Write-Host "  Seeding database..." -ForegroundColor Yellow
    Set-Location backend
    $env:PYTHONIOENCODING = "utf-8"
    python seed.py
    Set-Location ..
} else {
    Write-Host "  Tables exist." -ForegroundColor Green
}

# ── Step 3: Start FastAPI backend ────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Starting FastAPI backend on :8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD\backend'; `$env:PYTHONIOENCODING='utf-8'; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`"" -WindowStyle Normal

Start-Sleep 3
Write-Host "  Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green

# ── Step 4: Start Next.js frontend ──────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Starting Next.js frontend on :3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD\frontend'; npm run dev`"" -WindowStyle Normal

Start-Sleep 5

# ── Open browser ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  All systems operational!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:   http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Dashboard:  http://localhost:3000/dashboard" -ForegroundColor Cyan
Write-Host "  API:        http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:3000"
