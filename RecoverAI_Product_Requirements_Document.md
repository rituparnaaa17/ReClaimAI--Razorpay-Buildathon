# ReclaimAI — Product Requirements Document

## Track 3: AI Revenue Recovery

**Product Name:** ReclaimAI  
**Tagline:** *Turn failed payments into recovered revenue.*

---

## 1. Product Overview

ReclaimAI is an AI-powered revenue recovery platform for merchants.

It identifies revenue that is at risk because of:

- Failed payments
- Abandoned checkouts
- Failed subscriptions
- Repeated payment failures

The system analyzes the problem, predicts the probability of recovery, selects the most suitable recovery action, executes a safe recovery workflow, and measures the revenue recovered.

### Core Flow

```text
Detect → Diagnose → Predict → Decide → Recover → Verify → Measure
```

---

## 2. Problem Statement

Merchants lose potential revenue when:

- A customer's payment fails.
- A customer abandons checkout.
- A subscription payment fails.
- A temporary bank/UPI issue prevents payment.
- Customers repeatedly fail to complete payments.

Traditional payment systems often only show:

> Payment Failed

ReclaimAI answers:

> Why did it fail?

> Can this customer be recovered?

> What is the best recovery action?

> How much revenue can be recovered?

> Did the recovery actually work?

---

## 3. Product Goal

### Primary Goal

Maximize revenue recovered from failed or abandoned payment opportunities while minimizing unnecessary recovery attempts.

### Secondary Goals

- Automate repetitive recovery operations.
- Provide explainable AI decisions.
- Reduce unnecessary payment retries.
- Give merchants clear revenue recovery analytics.
- Maintain an audit trail for every AI decision.

---

## 4. Target Users

### Primary Users

**Online Merchants**

Examples:

- E-commerce businesses
- SaaS companies
- EdTech platforms
- Subscription businesses
- D2C brands

### Secondary Users

**Finance and Operations Teams**

They use the platform to monitor:

- Failed payments
- Revenue leakage
- Recovery performance
- AI actions
- Revenue recovered

---

# 5. Core Product Workflow

```text
Payment / Checkout Data
          ↓
Revenue Risk Detection
          ↓
Root Cause Analysis
          ↓
Recovery Probability
          ↓
AI Recovery Agent
          ↓
Policy & Safety Check
          ↓
Recovery Action
          ↓
Payment Verification
          ↓
Revenue Recovered
          ↓
Analytics & Audit Log
```

---

# 6. MVP Features

## 6.1 Merchant Dashboard

The dashboard provides a real-time overview of revenue recovery.

### Key Metrics

- Revenue at Risk
- Revenue Recovered
- Recovery Rate
- Failed Payments
- Abandoned Checkouts
- Recovery Attempts
- Successful Recoveries

### Example

```text
Revenue at Risk       ₹25.4L
Revenue Recovered     ₹16.8L
Recovery Rate          66.1%
Failed Payments        2,431
```

### Visualizations

- Revenue at risk over time
- Revenue recovered over time
- Recovery by failure reason
- Recovery by payment method
- Recovery success rate

**Technology:** Recharts

---

# 7. Revenue Risk Detection

ReclaimAI identifies transactions that may result in lost revenue.

### Detect

- Failed payments
- Abandoned checkouts
- Failed subscriptions
- Repeated payment failures
- High-value failed transactions

Each recovery case receives a recovery probability.

### Example

```text
Transaction: TXN_10291
Amount: ₹4,999

Status: Failed
Recovery Probability: 91%
Priority: HIGH
```

---

# 8. AI Root Cause Analysis

The AI determines why the revenue opportunity was lost.

### Possible Causes

- Temporary payment failure
- UPI timeout
- Bank decline
- Insufficient balance
- Expired card
- Checkout abandonment
- Subscription failure
- Too many retries

### Example

```text
Transaction: ₹4,999

Failure:
UPI Timeout

Customer History:
8 successful payments
1 failed payment

AI Conclusion:
Likely temporary payment failure.

Recovery Probability:
91%
```

---

# 9. AI Recovery Decision Engine

The system determines the most appropriate recovery strategy.

| Situation | Recommended Action |
|---|---|
| Temporary payment failure | Smart retry |
| Checkout abandoned | Personalized reminder |
| Subscription failure | Smart retry + notification |
| High-value customer | Alternative payment option |
| Multiple failures | Human review |
| Very low recovery probability | No action |

The system should **not blindly retry every failed transaction**.

The decision should consider:

- Failure reason
- Transaction amount
- Customer history
- Previous retry count
- Recovery probability
- Merchant-defined rules

---

# 10. AI Recovery Agent

The recovery agent manages the complete workflow.

```text
DETECT
   ↓
DIAGNOSE
   ↓
PREDICT
   ↓
DECIDE
   ↓
VALIDATE
   ↓
ACT
   ↓
VERIFY
```

### Example

```text
Payment Failed
      ↓
Analyze transaction
      ↓
Recovery Probability = 87%
      ↓
Temporary failure detected
      ↓
Recommend retry after 10 minutes
      ↓
Policy check
      ↓
Execute retry
      ↓
Payment successful
      ↓
₹4,999 recovered
```

---

# 11. Recovery Scenarios

The MVP should focus on three major scenarios.

## Scenario 1 — Failed Payment

```text
Payment fails
    ↓
AI analyzes failure
    ↓
Calculate recovery probability
    ↓
Select retry strategy
    ↓
Execute test retry
    ↓
Verify result
```

## Scenario 2 — Abandoned Checkout

```text
Customer starts checkout
        ↓
Customer abandons checkout
        ↓
AI analyzes customer behavior
        ↓
High recovery probability
        ↓
Generate personalized reminder
        ↓
Customer returns
        ↓
Payment completed
```

## Scenario 3 — Failed Subscription

```text
Subscription payment fails
        ↓
Analyze customer history
        ↓
Predict recovery probability
        ↓
Select retry strategy
        ↓
Notify customer if required
        ↓
Retry payment
        ↓
Record result
```

---

# 12. Supabase Architecture

Supabase will be the primary backend data platform.

### Supabase Responsibilities

- PostgreSQL database
- Authentication
- Row Level Security
- Realtime updates
- Database management

### Architecture

```text
                 ┌──────────────────┐
                 │    Next.js UI    │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │     FastAPI      │
                 │     Backend      │
                 └────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ↓            ↓            ↓
       ┌───────────┐ ┌──────────┐ ┌─────────────┐
       │ Supabase  │ │ AI / ML  │ │  Razorpay   │
       │           │ │          │ │  Test API   │
       │ PostgreSQL│ │ Gemini   │ │             │
       │ Auth      │ │ XGBoost  │ │ Payments    │
       │ Realtime  │ │ LangGraph│ │             │
       └───────────┘ └──────────┘ └─────────────┘
                          ↓
                  ┌───────────────┐
                  │ Recovery Agent│
                  └───────────────┘
```

---

# 13. Database Schema

## 13.1 `merchants`

```text
id
name
email
business_type
created_at
```

## 13.2 `customers`

```text
id
merchant_id
name
email
total_transactions
successful_transactions
failed_transactions
total_spent
average_transaction_value
created_at
```

## 13.3 `transactions`

```text
id
merchant_id
customer_id
razorpay_payment_id
amount
currency
payment_method
status
failure_reason
created_at
```

### Example

```text
TXN001
Customer: CUST102
Amount: ₹4,999
Method: UPI
Status: Failed
Reason: UPI_TIMEOUT
```

## 13.4 `recovery_cases`

```text
id
transaction_id
merchant_id
risk_score
recovery_probability
root_cause
recommended_action
action_taken
status
amount_at_risk
amount_recovered
created_at
updated_at
```

## 13.5 `agent_logs`

```text
id
recovery_case_id
step
decision
reason
confidence
timestamp
result
```

## 13.6 `recovery_actions`

```text
id
recovery_case_id
action_type
scheduled_at
executed_at
status
result
amount_recovered
```

## 13.7 `notifications`

```text
id
customer_id
recovery_case_id
channel
message
status
sent_at
```

---

# 14. Authentication

Use **Supabase Auth** for merchant authentication.

```text
Merchant
   ↓
Email + Password
   ↓
Supabase Auth
   ↓
Authenticated Session
   ↓
Merchant Dashboard
```

Use **Row Level Security (RLS)** so that one merchant cannot access another merchant's transactions.

---

# 15. AI/ML Architecture

The AI system will have three main layers.

## Layer 1 — ML Prediction

Predict the probability that a revenue opportunity can be recovered.

Possible models:

- Logistic Regression
- Random Forest
- XGBoost

### Input Features

```text
amount
failure_reason
payment_method
previous_success_rate
retry_count
customer_value
time_since_failure
```

### Output

```text
Recovery Probability = 0.91
```

## Layer 2 — LLM

Use Gemini/OpenAI for:

- Root-cause explanation
- AI reasoning
- Recovery recommendations
- Personalized customer messages
- Human-readable explanations

## Layer 3 — Agent

Use LangGraph to orchestrate the recovery process.

```text
Transaction
    ↓
Analyze
    ↓
ML Prediction
    ↓
LLM Explanation
    ↓
Choose Action
    ↓
Guardrail Check
    ↓
Execute
    ↓
Verify
```

---

# 16. Razorpay Integration

Use **Razorpay Test Mode** for the hackathon.

The system should simulate:

- Payment creation
- Payment failure
- Payment retry
- Successful payment
- Subscription payment failure

### Example

```text
₹4,999 Payment
       ↓
Payment Failed
       ↓
ReclaimAI
       ↓
Smart Retry
       ↓
Payment Successful
       ↓
₹4,999 Recovered
```

No real financial transactions are required for the MVP.

---

# 17. Guardrails and Safety

Because this is a financial system, AI actions must be controlled.

### Maximum Retry Limit

```text
Maximum automatic retries = 2
```

### High-Value Transactions

```text
Amount > ₹50,000
        ↓
Human Approval Required
```

### Repeated Failures

```text
3 failures
    ↓
Stop automatic recovery
    ↓
Human Review
```

### Auditability

Every AI decision and action must be recorded in `agent_logs`.

---

# 18. Frontend Pages

## 18.1 Login

```text
ReclaimAI

Email
Password

[ Login ]
```

## 18.2 Dashboard

Displays:

- Revenue at Risk
- Revenue Recovered
- Recovery Rate
- Failed Payments
- Recovery Charts
- Recent Recovery Cases

## 18.3 Recovery Cases

Display:

```text
Transaction
Amount
Failure Reason
Recovery Probability
AI Recommendation
Status
```

## 18.4 Recovery Case Details

```text
₹4,999

Payment Failed

AI Analysis
-------------------------
Temporary UPI failure

Recovery Probability
91%

Recommended Action
Smart Retry

Reason
Customer has 8 successful
previous transactions.

[ Execute Recovery ]
```

## 18.5 Agent Activity

```text
✓ Transaction detected
✓ Root cause analyzed
✓ Recovery probability calculated
✓ Recovery strategy selected
✓ Policy verified
✓ Retry executed
✓ Payment recovered
```

---

# 19. Recommended Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Backend | FastAPI |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Realtime | Supabase Realtime |
| AI | Gemini / OpenAI |
| Agent | LangGraph |
| ML | Scikit-learn / XGBoost |
| Data Processing | Pandas / NumPy |
| Charts | Recharts |
| Payments | Razorpay Test APIs |
| Email | Resend |
| Frontend Deployment | Vercel |
| Backend Deployment | Render / Railway |
| Version Control | GitHub |

---

# 20. Synthetic Dataset

For the hackathon MVP, generate approximately **10,000 synthetic transactions**.

### Example Distribution

```text
Successful Payments       7,000
Failed Payments           2,000
Abandoned Checkouts       1,000
```

### Failed Payment Categories

```text
UPI Timeout
Bank Decline
Insufficient Balance
Expired Card
Technical Failure
Other
```

The dataset will be used for:

- ML training
- AI testing
- Dashboard analytics
- Demo scenarios

---

# 21. Success Metrics

## Business Metrics

- Revenue at Risk
- Revenue Recovered
- Recovery Rate
- Average Recovery Time

### Recovery Rate

```text
Revenue Recovered
----------------- × 100
Revenue at Risk
```

## AI Metrics

- Prediction Accuracy
- Precision
- Recall
- F1 Score
- False Positive Rate

## Agent Metrics

- Successful Recovery Actions
- Failed Recovery Actions
- Average Recovery Time
- Human Escalation Rate

---

# 22. MVP Scope

## Must Have

- [ ] Merchant authentication
- [ ] Supabase database
- [ ] Transaction management
- [ ] Revenue risk detection
- [ ] AI root-cause analysis
- [ ] Recovery probability
- [ ] AI recovery recommendation
- [ ] Failed payment recovery
- [ ] Abandoned checkout recovery
- [ ] Subscription recovery
- [ ] Razorpay test-mode integration
- [ ] Recovery analytics
- [ ] Agent activity logs
- [ ] Guardrails

## Nice to Have

- [ ] Real-time webhook processing
- [ ] Email notifications
- [ ] Advanced ML model
- [ ] Customer segmentation
- [ ] A/B testing
- [ ] Multi-channel notifications

---

# 23. Final Demo Flow

### Step 1 — Dashboard

Show:

```text
₹25.4L Revenue at Risk
₹16.8L Revenue Recovered
66.1% Recovery Rate
```

### Step 2 — Select Failed Payment

```text
Transaction: TXN_10291
Amount: ₹4,999
Status: Failed
```

### Step 3 — AI Analysis

```text
Root Cause:
Temporary UPI failure

Recovery Probability:
91%
```

### Step 4 — AI Decision

```text
Recommended Action:
Smart Retry

Reason:
Customer has a strong payment history.
```

### Step 5 — Guardrail

```text
Retry Count: 0/2
Amount: Within automatic recovery limit

✓ Approved
```

### Step 6 — Execute

```text
Payment Processing...
       ↓
✓ Payment Successful
```

### Step 7 — Dashboard Update

```text
Revenue Recovered

₹16,80,000
      ↓
₹16,84,999
```

### Step 8 — Agent Timeline

```text
Detect
  ↓
Diagnose
  ↓
Predict
  ↓
Decide
  ↓
Recover
  ↓
Verify
```

---

# 24. Future Enhancements

- Real-time payment webhooks
- Merchant-specific recovery models
- Advanced customer segmentation
- Dynamic recovery strategies
- A/B testing
- Multi-channel communication
- Intelligent retry timing
- Payment-method optimization
- Revenue forecasting
- Automated campaign optimization

---

# 25. Final Product Architecture

```text
                         RECLAIMAI
                             │
                             ↓
                    ┌─────────────────┐
                    │    Next.js      │
                    │    Dashboard    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │     FastAPI     │
                    │     Backend     │
                    └────────┬────────┘
                             │
             ┌───────────────┼────────────────┐
             ↓               ↓                ↓
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │  Supabase   │ │  AI / ML    │ │  Razorpay   │
      │             │ │             │ │  Test API   │
      │ PostgreSQL  │ │ Gemini      │ │             │
      │ Auth        │ │ XGBoost     │ │ Payments    │
      │ Realtime    │ │ LangGraph   │ │             │
      └─────────────┘ └──────┬──────┘ └─────────────┘
                             ↓
                    ┌─────────────────┐
                    │ Recovery Agent  │
                    └────────┬────────┘
                             ↓
                 Detect → Diagnose → Predict
                             ↓
                    Decide → Recover
                             ↓
                         Verify
                             ↓
                   ₹ REVENUE RECOVERED
```

---

# 26. Product Pitch

> **ReclaimAI is an autonomous AI revenue recovery agent that detects failed and abandoned payment opportunities, understands their root cause, predicts recovery probability, selects a safe recovery strategy, executes the recovery workflow through Razorpay's test infrastructure, and measures the actual revenue recovered.**

### Core Differentiator

**Most payment systems tell merchants that money was lost.**

**ReclaimAI tells them why it was lost, what to do about it, does it safely, and shows exactly how much money was recovered.**
