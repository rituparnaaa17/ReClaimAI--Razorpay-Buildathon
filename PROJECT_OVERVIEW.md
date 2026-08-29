# ReclaimAI — Project Overview & Working

**AI-Powered Revenue Recovery for Indian Businesses**
*Built for RazorPay*

---

## 🌟 What We Have Built
ReclaimAI is a full-stack, production-ready application that autonomously detects, analyzes, and recovers failed payments. It replaces static, rule-based retry systems with an intelligent **AI Agent** powered by Gemini 2.5 Flash and LangGraph.

The system features a **Next.js frontend dashboard** styled like Razorpay (crisp white and blue) and a **FastAPI Python backend** that handles the complex AI workflows, communicating with a **Supabase PostgreSQL database** for persistence.

---

## 🏗️ Architecture & Tech Stack

### Frontend (Next.js 16 + React)
* **Visuals:** Razorpay-inspired light theme (`globals.css`), Recharts for analytics, responsive Tailwind/Custom CSS.
* **Dashboard Pages:**
  * `/dashboard`: High-level KPIs, 14-day revenue trend chart, real-time Gemini AI insights.
  * `/dashboard/recovery-cases`: Filterable table of all detected payment failures.
  * `/dashboard/recovery-cases/[id]`: A deep-dive into a specific case, featuring a "Run Agent" button and an animated, real-time agent timeline.
  * `/dashboard/analytics`: In-depth breakdown of failures (by reason, payment method) and AI insights.
  * `/dashboard/agent-activity`: An audit trail showing every decision the AI has made.

### Backend (FastAPI + Python)
* **Core Engine:** Connects the UI to the AI workflow and database.
* **LangGraph Agent:** A 7-node autonomous workflow that processes failed payments (see below).
* **AI Integration:** Uses `google.genai` SDK to connect to **Gemini 2.5 Flash** for diagnosing errors and generating human-like reasoning.
* **Integrations:** Razorpay API (for payment retries & links), Supabase (PostgreSQL schema `recovery_cases`, `agent_logs`).

---

## 🤖 The LangGraph Agent (How it Works)

When a payment fails, the backend triggers a 7-step autonomous AI workflow (`backend/app/agents/recovery_agent.py`):

1. **DETECT:** A payment failure is registered (e.g., via a Razorpay webhook).
2. **DIAGNOSE:** Gemini AI analyzes the error code (e.g., `UPI_TIMEOUT`, `BANK_DECLINE`) and determines the root cause.
3. **PREDICT:** A probability score (0% - 100%) is calculated to determine the likelihood of recovering the payment.
4. **DECIDE:** Gemini chooses the best action: *Smart Retry* (wait 5 mins and try again) or *Alternative Payment Link* (email customer).
5. **GUARDRAIL:** The system ensures the AI obeys business rules (e.g., Max 2 retries, Amount < ₹50,000, Probability > 30%).
6. **EXECUTE:** The backend actually makes the call to the Razorpay API to retry the payment or create a link.
7. **VERIFY:** The system checks if the recovery was successful and saves all logs to the Supabase database.

---

## 💻 How to Run the Project Locally

We created a one-click startup script to make running the project effortless.

### Option 1: One-Click Start
Double click the `start.ps1` file in the root directory, or run it in PowerShell:
```powershell
.\start.ps1
```
This script will check your environment, verify the database, boot up both the backend and frontend on separate ports, and automatically open your browser.

### Option 2: Manual Start
**Terminal 1 (Backend):**
```powershell
cd backend
$env:PYTHONIOENCODING="utf-8"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
```

---

## 🗄️ Database Setup (Supabase)

The app works seamlessly out-of-the-box with mock data so the UI never breaks. However, to use the real database:
1. Open the [Supabase SQL Editor](https://supabase.com/dashboard/project/jonbnnyxfrovdaptvklr/sql/new) for your project.
2. Paste and run the schema found in `supabase/migrations/001_initial_schema.sql`.
3. In your backend terminal, run: `python seed.py` to populate the real database with demo cases.

---

## 🚀 Key Files to Explore
- **The Agent Workflow:** `backend/app/agents/recovery_agent.py`
- **Gemini AI Integration:** `backend/app/services/gemini_client.py`
- **Frontend Dashboard:** `frontend/src/app/dashboard/page.tsx`
- **Theme & CSS:** `frontend/src/app/globals.css`
