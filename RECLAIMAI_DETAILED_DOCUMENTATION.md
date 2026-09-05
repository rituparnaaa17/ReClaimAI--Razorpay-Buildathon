# ReclaimAI — Detailed Technical Architecture & System Design
## Razorpay Buildathon Track 03: AI Revenue Recovery

---

## 1. Executive Summary & Vision

**ReclaimAI** is an autonomous, agentic revenue recovery platform engineered for **Track 03: AI Revenue Recovery**. It bridges modern generative AI (Google Gemini 2.5), state machine orchestration (LangGraph), and Razorpay’s payments engine to detect failed payments, diagnose root causes, enforce compliance guardrails, issue dynamic payment links, and authoritatively verify money won back.

### The Problem Domain
In Indian e-commerce, SaaS, and subscription businesses, **15% to 20% of revenue at risk is lost to payment drop-offs**. These failures stem from:
* **Transient Infrastructure Failures**: UPI session timeouts, NPCI bank server delays, gateway timeouts.
* **Customer-Side Soft Declines**: Insufficient funds, expired card tokens, daily UPI transfer limit breaches.
* **Checkout Abandonment**: Friction during payment flow or lack of alternative payment options.

---

## 2. Technology Stack & Component Architecture

```
                               ┌────────────────────────┐
                               │  Next.js 16 (App Router)│
                               │  TailwindCSS + Lucide  │
                               └───────────┬────────────┘
                                           │ HTTP / REST
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend (Python 3.11)                        │
│                                                                                │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────────┐ │
│  │   REST API Layer      │  │  Razorpay Service     │  │ Webhook Ingestion   │ │
│  │ (Cases/Agent/Links)   │  │  (SDK / PaymentLink)  │  │  (HMAC Validation)  │ │
│  └───────────┬───────────┘  └───────────┬───────────┘  └──────────┬──────────┘ │
│              │                          │                         │            │
│              └──────────────────────────┼─────────────────────────┘            │
│                                         │                                      │
│                                         ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                LangGraph + Gemini 2.5 Agent Workflow                    │  │
│  │   DETECT ➔ DIAGNOSE ➔ PREDICT ➔ DECIDE ➔ GUARDRAIL ➔ EXECUTE ➔ VERIFY    │  │
│  └──────────────────────────────────┬───────────────────────────────────────┘  │
└─────────────────────────────────────┼──────────────────────────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │    Supabase Relational    │             │    Razorpay Test Mode     │
   │  (Cases/Logs/Batches)     │             │    (Payment Link API)     │
   └───────────────────────────┘             └───────────────────────────┘
```

### Component Breakdown
1. **FastAPI (`backend/app/main.py`)**: Asynchronous Python Web framework serving REST APIs, CORS middleware, and health endpoints.
2. **LangGraph Agent (`backend/app/agents/recovery_agent.py`)**: Stateful multi-node workflow orchestrator executing the 7 recovery nodes.
3. **Google Gemini Client (`backend/app/services/gemini_client.py`)**: Uses `google-genai` with `gemini-2.5-flash` running blocking SDK calls asynchronously via thread executors.
4. **Razorpay Service (`backend/app/services/razorpay_service.py`)**: Real SDK integration for generating payment links, fetching payment statuses, and validating test mode execution constraints.
5. **State Machine (`backend/app/services/state_machine.py`)**: Centralized state transition table preventing invalid transitions (e.g., transitioning out of terminal states like `recovered` or `failed`).
6. **Measurement Engine (`backend/app/services/measurement.py`)**: Implements strict financial measurement rules with Python `Decimal` arithmetic.
7. **Webhook Service (`backend/app/services/webhook_service.py`)**: Validates HMAC SHA-256 signatures, deduplicates event IDs, and handles `payment.failed` and `payment.captured` events.

---

## 3. Database Schema & Relational Integrity

ReclaimAI uses a normalized **Supabase (PostgreSQL)** database:

* **`customers`**: Holds customer identity (`id`, `name`, `email`, `phone`).
* **`transactions`**: Stores transaction records (`id`, `merchant_id`, `amount`, `payment_method`, `razorpay_payment_id`, `status`).
* **`recovery_cases`**: Core entity linking transaction and customer data:
  * Foreign Keys: `transaction_id` $\rightarrow$ `transactions.id`, `customer_id` $\rightarrow$ `customers.id`.
  * Tracking Fields: `status`, `amount_at_risk`, `amount_recovered`, `recovery_probability`, `root_cause`, `action_taken`, `retry_count`, `razorpay_payment_link_id`.
* **`agent_logs`**: Full audit log for every step executed by the agent (`step`, `decision`, `reason`, `confidence`, `result`, `timestamp`).
* **`batches`**: Tracks batch execution runs across multiple cases (`batch_id`, `total_cases`, `successful_cases`, `total_recovered_amount`).
* **`webhook_events`**: Idempotency ledger tracking processed webhook event IDs to prevent duplicate processing.

---

## 4. The 7-Node Autonomous Agent Workflow

Every recovery case moves through 7 strict nodes:

```
[1. DETECT] ──> [2. DIAGNOSE] ──> [3. PREDICT] ──> [4. DECIDE]
                                                        │
[7. VERIFY] <── [6. EXECUTE] <── [5. GUARDRAIL] <───────┘
```

1. **`DETECT`**: Ingests failed transaction events from webhooks or API requests. Verifies case presence and initializes state.
2. **`DIAGNOSE`**: Queries Gemini 2.5 Flash to analyze the failure reason (e.g. mapping `UPI_TIMEOUT` to transient network congestion or `BANK_DECLINE` to issuing bank rejection).
3. **`PREDICT`**: Computes recovery probability (e.g. 85% for UPI timeouts, 40% for bank declines) based on payment method and customer retry count.
4. **`DECIDE`**: Selects the optimal recovery strategy (`Smart Retry`, `Personalized Reminder`, `Card Update Request`, or `Wait`).
5. **`GUARDRAIL`**: Evaluates business safety rules:
   * *Threshold Check*: Amount $> \text{₹}50,000 \rightarrow$ Blocked (`action_required`).
   * *Retry Limit Check*: Retry Count $\ge 2 \rightarrow$ Blocked (`escalated`).
   * *Probability Threshold*: Probability $< 30\% \rightarrow$ Blocked (`no_action`).
6. **`EXECUTE`**: Generates a dynamic Razorpay Payment Link (`plink_xxx`) configured with customer details, case metadata, and callback URLs. Stores `razorpay_payment_link_id` in Supabase.
7. **`VERIFY`**: Queries Razorpay API/webhooks to check if status is `paid` / `captured`. Measures exact rupees recovered using Decimal arithmetic.

---

## 5. Financial Measurement & "The Bar"

Track 03 demands strict proof of actual money won back:

### Key Measurement Rules
1. **Authoritative Gateway Truth**: A case is marked `recovered` **ONLY** when Razorpay returns `status == "captured"`.
2. **Payment Link Protection**: Creating a Payment Link (`plink_xxx`) does **NOT** count as money recovered. It transitions the case to `verifying` state and waits for payment capture.
3. **Zero Float Precision**: Converts Razorpay paise (integers) to Indian Rupees (`INR`) using `Decimal("paise") / Decimal("100")` to eliminate floating-point inaccuracies.
4. **Batch Aggregation**: When running batch recovery across multiple cases, only verified captured payments are summed into `total_recovered_amount`.

---

## 6. Frontend Dashboard & User Experience

The Next.js frontend (`frontend/src/`) provides a real-time command center:

* **Dashboard Overview (`/dashboard`)**: Displays Total Revenue at Risk, Verified Recovered Money, Active Cases, and Strategy Conversion Chart.
* **Recovery Cases (`/dashboard/recovery-cases`)**: Filterable table showing case statuses, amounts, AI reasoning, and direct "Run Agent" trigger buttons.
* **Payment Links Panel (`/dashboard/payment-links`)**: Real-time listing of generated Razorpay payment links, short URLs, customer details, and live statuses (`created`, `paid`, `expired`).
* **Agent Activity Log (`/dashboard/agent-activity`)**: Audit trail displaying step-by-step decision logs, confidence scores, and safety guardrail checks.
* **Analytics (`/dashboard/analytics`)**: Win-rate trends, recovery probability distributions, and failure reason breakdowns.
