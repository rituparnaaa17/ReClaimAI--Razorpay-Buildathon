# ReclaimAI — Technology Stack & Architecture Document

## Track 3: AI Revenue Recovery

**Product:** ReclaimAI  
**Purpose:** AI-powered revenue recovery platform for failed payments, abandoned checkouts, and failed subscriptions.

---

# 1. Technology Stack Overview

ReclaimAI will use a modern full-stack architecture focused on:

- Fast development
- AI/agent integration
- Secure financial workflows
- Real-time analytics
- Easy deployment
- Clear separation between frontend, backend, AI, and payment services

### Final Recommended Stack

```text
Frontend
Next.js + TypeScript + Tailwind CSS

Backend
Python + FastAPI

Database / Backend Services
Supabase

AI / LLM
Gemini API

AI Agent
LangGraph

Machine Learning
Python + Scikit-learn / XGBoost

Data Processing
Pandas + NumPy

Charts
Recharts

Payments
Razorpay Test APIs

Notifications
Resend

Deployment
Vercel + Render/Railway + Supabase

Version Control
Git + GitHub
```

---

# 2. High-Level Architecture

```text
                         RECLAIMAI
                             │
                             ↓
                    ┌─────────────────┐
                    │     Next.js     │
                    │   Web Dashboard │
                    └────────┬────────┘
                             │
                         REST API
                             │
                             ↓
                    ┌─────────────────┐
                    │     FastAPI     │
                    │    Backend      │
                    └────────┬────────┘
                             │
             ┌───────────────┼────────────────┐
             ↓               ↓                ↓
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │  Supabase   │ │  AI / ML    │ │  Razorpay   │
      │             │ │             │ │  Test APIs  │
      │ PostgreSQL  │ │ Gemini      │ │             │
      │ Auth        │ │ LangGraph   │ │ Payments    │
      │ Realtime    │ │ XGBoost     │ │ Subscriptions│
      └─────────────┘ └──────┬──────┘ └─────────────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │ Recovery Agent  │
                    └────────┬────────┘
                             ↓
                    Recovery Decision
                             ↓
                     Recovery Action
                             ↓
                    Payment Verification
                             ↓
                    Analytics / Audit Log
```

---

# 3. Frontend Technology

## 3.1 Next.js

**Purpose:** Build the merchant-facing web application.

### Why Next.js?

- React-based
- Fast development
- Good routing
- TypeScript support
- Easy Vercel deployment
- Excellent for dashboard applications

### Main frontend pages

```text
/login
/dashboard
/recovery-cases
/recovery-cases/[id]
/transactions
/agent-activity
/settings
```

---

## 3.2 TypeScript

**Purpose:** Type-safe frontend development.

Use TypeScript for:

- API responses
- Database models
- Form data
- Dashboard data
- Recovery case types
- Agent status

Example:

```typescript
interface RecoveryCase {
  id: string;
  transactionId: string;
  amountAtRisk: number;
  recoveryProbability: number;
  rootCause: string;
  recommendedAction: string;
  status: string;
}
```

---

## 3.3 Tailwind CSS

**Purpose:** Build the UI quickly.

Use Tailwind for:

- Dashboard
- Cards
- Tables
- Buttons
- Modals
- Status badges
- Responsive layouts

---

## 3.4 Recharts

**Purpose:** Data visualization.

Use it for:

- Revenue at risk
- Revenue recovered
- Recovery rate
- Failed payment trends
- Recovery by payment method
- Recovery by failure reason

---

# 4. Backend Technology

## 4.1 FastAPI

**Purpose:** Main backend API.

FastAPI will handle:

- Authentication verification
- Transaction APIs
- Recovery APIs
- AI orchestration
- Razorpay integration
- Database operations
- Agent execution
- Analytics

### Example API structure

```text
/api/auth
/api/transactions
/api/recovery
/api/agent
/api/analytics
/api/webhooks
```

---

## 4.2 Python

Python will be the main backend and AI language.

Use Python for:

- FastAPI
- Machine learning
- Data processing
- AI integration
- Agent workflows

This avoids maintaining separate backend languages.

---

# 5. Database & Backend Services

## 5.1 Supabase

Supabase will be the main backend platform.

### Services used

#### PostgreSQL

Stores:

- Merchants
- Customers
- Transactions
- Recovery cases
- Recovery actions
- Agent logs
- Notifications

#### Supabase Auth

Handles:

- Merchant signup
- Merchant login
- Sessions
- Password management

#### Row Level Security

Ensures merchants can only access their own data.

#### Realtime

Used for:

- Live dashboard updates
- Recovery status updates
- Agent activity updates

---

# 6. Supabase Database

### Main tables

```text
merchants
customers
transactions
recovery_cases
recovery_actions
agent_logs
notifications
```

### Relationships

```text
Merchant
   │
   ├── Customers
   │      │
   │      └── Transactions
   │
   ├── Transactions
   │      │
   │      └── Recovery Cases
   │
   └── Recovery Cases
          │
          ├── Recovery Actions
          └── Agent Logs
```

---

# 7. AI Technology

## 7.1 Gemini API

**Purpose:** Large Language Model.

Gemini will be used for:

- Root-cause explanations
- Recovery recommendations
- AI-generated customer messages
- Natural-language explanations
- Merchant-facing AI insights

### Example

Input:

```text
Payment:
₹4,999

Failure:
UPI timeout

Previous successful payments:
8

Retry count:
0
```

AI output:

```text
The payment appears to have failed because of a
temporary UPI issue. The customer has a strong
payment history, so a delayed retry is recommended.
```

---

# 8. AI Agent Technology

## 8.1 LangGraph

**Purpose:** Build the ReclaimAI agent workflow.

The agent will use a controlled state-based workflow.

```text
Transaction Event
       ↓
Detect
       ↓
Diagnose
       ↓
Predict
       ↓
Decide
       ↓
Guardrail Check
       ↓
Execute
       ↓
Verify
       ↓
Log Result
```

### Why LangGraph?

- Good for multi-step workflows
- Supports state
- Supports conditional decisions
- Easier to add human approval
- Suitable for agentic workflows

---

# 9. Machine Learning

## 9.1 Scikit-learn

Use Scikit-learn for the initial ML model.

Possible models:

- Logistic Regression
- Random Forest
- Gradient Boosting

Purpose:

> Predict recovery probability.

Example:

```text
Input:
Amount = ₹4,999
Failure = UPI timeout
Previous success rate = 89%
Retry count = 0

Output:
Recovery Probability = 91%
```

---

## 9.2 XGBoost

XGBoost can be used if a stronger tabular prediction model is needed.

### Use XGBoost for:

- Recovery probability
- Customer recovery likelihood
- Action success prediction

For the MVP, start with **Logistic Regression or Random Forest**, then upgrade to XGBoost if needed.

---

# 10. Data Processing

## Pandas

Used for:

- Dataset creation
- Data cleaning
- Feature engineering
- Analytics
- ML preparation

## NumPy

Used for:

- Numerical operations
- Feature calculations
- ML preprocessing

---

# 11. Payment Integration

## Razorpay Test APIs

Razorpay will be used for the payment workflow.

### Use Test Mode for:

- Orders
- Payments
- Payment failures
- Payment retries
- Subscriptions

### Example flow

```text
ReclaimAI
    ↓
Create/Test Payment
    ↓
Payment Failure
    ↓
AI Recovery Agent
    ↓
Recovery Action
    ↓
Test Retry
    ↓
Payment Success
```

No real money should be involved in the MVP.

---

# 12. Notifications

## Resend

Use Resend for email notifications.

Example:

```text
Payment failed
      ↓
AI determines recovery opportunity
      ↓
Generate message
      ↓
Send recovery email
      ↓
Customer returns
      ↓
Payment completed
```

For the MVP, email simulation can also be used if time is limited.

---

# 13. Authentication Flow

Use Supabase Auth.

```text
Merchant
    ↓
Login
    ↓
Supabase Auth
    ↓
JWT / Session
    ↓
Next.js
    ↓
FastAPI
    ↓
Verify authenticated merchant
    ↓
Access merchant-specific data
```

---

# 14. API Architecture

## Authentication

```text
POST /api/auth/session
GET  /api/auth/me
```

## Transactions

```text
GET  /api/transactions
GET  /api/transactions/{id}
POST /api/transactions
```

## Recovery

```text
GET  /api/recovery/cases
GET  /api/recovery/cases/{id}
POST /api/recovery/analyze/{id}
POST /api/recovery/execute/{id}
```

## Agent

```text
POST /api/agent/run/{case_id}
GET  /api/agent/logs/{case_id}
```

## Analytics

```text
GET /api/analytics/overview
GET /api/analytics/recovery
GET /api/analytics/failure-reasons
```

## Webhooks

```text
POST /api/webhooks/razorpay
```

---

# 15. AI Agent Architecture

The agent should not directly control everything.

Use separate components:

```text
                 Transaction
                      ↓
              ┌───────────────┐
              │    Detector   │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │  ML Predictor │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │  LLM Analysis │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Action Planner│
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │  Guardrails   │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │ Action Executor│
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │    Verify     │
              └───────────────┘
```

---

# 16. Guardrail Layer

The guardrail layer is mandatory for financial actions.

### Rules

```text
Maximum automatic retries = 2
```

```text
Transaction > ₹50,000
        ↓
Human approval
```

```text
Recovery probability < threshold
        ↓
No automatic action
```

```text
Repeated failures
        ↓
Stop recovery
        ↓
Human review
```

---

# 17. Security Stack

### Frontend

- HTTPS
- Secure authentication
- Input validation

### Backend

- JWT verification
- Pydantic validation
- Rate limiting
- CORS configuration
- Environment variables

### Database

- Supabase Row Level Security
- Restricted database access
- No service keys in frontend

### Secrets

Store in environment variables:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
GEMINI_API_KEY
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RESEND_API_KEY
```

Never commit `.env` files to GitHub.

---

# 18. Project Structure

Recommended repository structure:

```text
reclaimai/
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── recovery-cases/
│   │   ├── transactions/
│   │   └── agent-activity/
│   │
│   ├── components/
│   ├── lib/
│   ├── types/
│   └── hooks/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── ml/
│   │   └── utils/
│   │
│   ├── requirements.txt
│   └── .env
│
├── ml/
│   ├── data/
│   ├── notebooks/
│   ├── models/
│   └── training/
│
├── supabase/
│   ├── migrations/
│   └── seed.sql
│
├── docs/
│
├── .gitignore
└── README.md
```

---

# 19. Deployment Architecture

```text
                GitHub Repository
                       │
            ┌──────────┴──────────┐
            ↓                     ↓
       Vercel                  Render
            ↓                     ↓
       Next.js                FastAPI
                                  │
                                  ↓
                             Supabase
                                  │
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
                PostgreSQL                   Auth
                    │
                    ↓
              AI / Agent APIs
                    │
              ┌─────┴─────┐
              ↓           ↓
           Gemini      Razorpay
```

### Frontend

Deploy on:

**Vercel**

### Backend

Deploy on:

**Render or Railway**

### Database

Use:

**Supabase**

---

# 20. Development Tools

### Code Editor

VS Code

### API Testing

Postman / Thunder Client

### Database

Supabase Dashboard

### Version Control

Git + GitHub

### Containerization

Docker — optional

### API Documentation

FastAPI automatically provides:

```text
/docs
/redoc
```

---

# 21. Development Environment

### Frontend

```bash
Node.js
npm / pnpm
Next.js
TypeScript
```

### Backend

```bash
Python 3.11+
FastAPI
Uvicorn
```

### ML

```bash
pandas
numpy
scikit-learn
xgboost
```

### AI

```bash
google-generativeai / Gemini SDK
LangGraph
LangChain
```

---

# 22. Recommended Python Dependencies

```text
fastapi
uvicorn
pydantic
python-dotenv
supabase
httpx
pandas
numpy
scikit-learn
xgboost
langgraph
langchain
google-generativeai
razorpay
```

Only install packages that are actually required by the implemented features.

---

# 23. Recommended Frontend Dependencies

```text
next
react
typescript
tailwindcss
@supabase/supabase-js
recharts
lucide-react
```

Optional:

```text
zod
react-hook-form
```

---

# 24. Data Flow

### Normal Transaction

```text
Razorpay
   ↓
Payment Event
   ↓
FastAPI
   ↓
Supabase
   ↓
Transaction Stored
```

### Failed Transaction

```text
Razorpay
   ↓
Payment Failed
   ↓
FastAPI
   ↓
Supabase
   ↓
Recovery Case Created
   ↓
ML Prediction
   ↓
LLM Analysis
   ↓
LangGraph Agent
   ↓
Guardrail
   ↓
Recovery Action
   ↓
Razorpay Test API
   ↓
Payment Result
   ↓
Supabase
   ↓
Dashboard Updated
```

---

# 25. Realtime Dashboard Flow

Supabase Realtime can update the dashboard after recovery.

```text
Recovery Action
      ↓
Database Updated
      ↓
Supabase Realtime
      ↓
Next.js Listener
      ↓
Dashboard Updates
```

Example:

```text
Before:

Revenue Recovered
₹16,80,000

After successful recovery:

Revenue Recovered
₹16,84,999
```

No manual page refresh is required.

---

# 26. MVP Technology Priorities

## Must Use

1. Next.js
2. TypeScript
3. Tailwind CSS
4. FastAPI
5. Supabase
6. Gemini/OpenAI
7. LangGraph
8. Razorpay Test API
9. Recharts

## Optional

10. XGBoost
11. Resend
12. Supabase Realtime
13. Docker

---

# 27. Recommended Implementation Strategy

Do not start with the ML model or agent.

Build in this order:

### Phase 1 — Foundation

```text
Next.js
+
Supabase
+
FastAPI
```

Build:

- Login
- Database
- Dashboard
- Transaction list

### Phase 2 — Revenue Detection

Build:

- Failed payment detection
- Recovery cases
- Revenue-at-risk calculation

### Phase 3 — AI

Add:

- Gemini
- Root-cause analysis
- Recovery recommendations

### Phase 4 — ML

Add:

- Recovery probability model
- Feature engineering
- Evaluation metrics

### Phase 5 — Agent

Add:

```text
Detect
→ Diagnose
→ Predict
→ Decide
→ Guardrail
→ Recover
→ Verify
```

### Phase 6 — Razorpay

Connect:

- Test payments
- Payment status
- Test retries
- Subscription scenarios

### Phase 7 — Polish

Add:

- Charts
- Agent timeline
- Realtime updates
- Animations
- Error handling
- Loading states

---

# 28. Final Recommended Stack

```text
┌─────────────────────────────────────────────┐
│                 FRONTEND                    │
│ Next.js + TypeScript + Tailwind + Recharts │
└──────────────────────┬──────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────┐
│                  BACKEND                    │
│              FastAPI + Python               │
└───────────────┬───────────────┬─────────────┘
                │               │
                ↓               ↓
┌─────────────────────┐  ┌────────────────────┐
│      SUPABASE       │  │      AI LAYER      │
│                     │  │                    │
│ PostgreSQL          │  │ Gemini              │
│ Authentication      │  │ LangGraph           │
│ Row Level Security  │  │ Scikit-learn        │
│ Realtime            │  │ XGBoost (optional)  │
└─────────────────────┘  └─────────┬──────────┘
                                   │
                                   ↓
                         ┌────────────────────┐
                         │  RECOVERY AGENT    │
                         └─────────┬──────────┘
                                   ↓
                         ┌────────────────────┐
                         │ RAZORPAY TEST API  │
                         └────────────────────┘
```

---

# 29. Why This Stack?

### Next.js

Fast, modern merchant dashboard.

### FastAPI

Excellent for Python AI/ML integration.

### Supabase

Provides database, authentication, RLS, and realtime features in one platform.

### Gemini

Provides LLM reasoning and explanations.

### LangGraph

Provides structured agent workflows and controlled state transitions.

### Scikit-learn/XGBoost

Provides measurable recovery prediction instead of relying entirely on an LLM.

### Razorpay Test APIs

Provides realistic payment/recovery demonstrations without real money.

### Vercel + Render/Railway

Simple deployment for a hackathon.

---

# 30. Final Architecture Principle

The system should **not** be:

```text
Payment → LLM → Action
```

Instead, build:

```text
Payment
   ↓
Data
   ↓
ML Prediction
   ↓
LLM Reasoning
   ↓
Agent Decision
   ↓
Guardrails
   ↓
Action
   ↓
Verification
   ↓
Measurement
```

This gives ReclaimAI a stronger combination of:

**Full-Stack + AI + ML + Agentic AI + Payments + Analytics + Safety**

which is the intended technical direction of the project.
