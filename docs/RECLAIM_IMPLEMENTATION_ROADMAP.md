# RECLAIM — AUTHORITATIVE IMPLEMENTATION ROADMAP

> **THIS FILE IS THE PROJECT'S MEMORY — IMPLEMENTATION ORDER**
>
> ROADMAP = What we are building, and in what order.
>
> If any future prompt, conversation message, old document, or
> previously generated list conflicts with this file:
> DO NOT silently choose one. Identify the conflict first.
> This file is the canonical implementation order unless the
> project owner explicitly modifies it.

---

## Project Objective

ReclaimAI is an AI-powered revenue recovery platform built
specifically for the Razorpay AI Buildathon 2026, Track 03
— AI Revenue Recovery.

The product detects revenue at risk from failed payments,
abandoned checkouts, and failed subscriptions. It then
diagnoses the failure cause, predicts recovery likelihood,
decides the best intervention, applies deterministic
guardrails, executes the recovery action, verifies the
actual Razorpay payment state, measures recovered revenue,
and learns from outcomes.

**Core product promise:**
> We do not optimize for retries.
> We optimize for recovered revenue.

**Core principle:**

```
AI proposes.
↓
Policy constrains.
↓
Executor acts.
↓
Razorpay state verifies.
↓
Reclaim measures.
↓
Reclaim learns.
```

**Core workflow:**

```
Detect → Diagnose → Predict → Decide →
Apply Guardrails → Execute → Verify →
Measure → Learn
```

---

## Building Philosophy

The implementation order follows this strict hierarchy:

```
MAKE IT WORK
↓
MAKE IT SAFE
↓
MAKE IT INTELLIGENT
↓
MAKE IT RAZORPAY-SPECIFIC
↓
PROVE THE MONEY
↓
MAKE IT EXPLAINABLE
↓
MAKE IT RELIABLE
↓
MAKE IT BEAUTIFUL
```

**This is not a suggestion. This is the order.**

Do NOT skip ahead merely because a later feature looks
interesting or impressive.

- Do NOT build advanced dashboard polish before the underlying
  recovery measurement works.
- Do NOT build advanced AI explanations before the decision
  engine exists.
- Do NOT build baseline comparison before actual recovery
  measurement exists.
- Do NOT build sophisticated Razorpay downtime recovery before
  the basic recovery engine is reliable.
- Do NOT add additional recovery scenarios simply to increase
  feature count.

Depth > breadth.

---

## Phase Dependency Rule

A phase should normally be considered complete before the
next phase begins.

A step may be considered complete ONLY when:

1. Implementation exists.
2. Integration works end-to-end.
3. Relevant tests pass.
4. Existing functionality has not regressed.
5. Acceptance criteria for that step are satisfied.
6. The corresponding checklist item has been checked.
7. The implementation has been verified — not merely written.

---

## Razorpay Scope Rule

Reclaim is built specifically for:

**Razorpay AI Buildathon 2026, Track 03 — AI Revenue Recovery**

The system must optimize for **RECOVERED REVENUE**, not
number of retries.

When implementing Razorpay-related functionality:

1. Inspect current official Razorpay documentation when the
   implementation depends on current Razorpay behavior.
2. Do NOT invent Razorpay APIs, webhook events, payment
   states, parameters, or capabilities.
3. Do NOT assume `payment.failed` means the transaction can
   never succeed later.
4. Handle payment state transitions correctly.
5. Use actual Razorpay-supported capabilities wherever possible.
6. Keep test/sandbox behavior clearly separated from claims
   about production behavior.

---

## Scenario Scope

**Three primary recovery scenarios (implement first):**

1. Failed Payment Recovery
2. Checkout Abandonment Recovery
3. Failed Subscription Recovery

**Strong additional scenarios:**

4. Payment Downtime Recovery
5. Alternative Payment Recovery

**Do NOT prioritize yet:**

- B2B Receivables
- Mandate Retry Sequencing
- Promise-to-Pay
- Hinglish Voice Recovery

---

## Existing Architecture (as of project start)

The existing Reclaim implementation already contains the
following. Do NOT assume these are perfect — inspect them.
If a roadmap step requires strengthening an existing feature,
extend or refactor rather than blindly duplicating.

**Frontend:**
- Next.js 16 + React + TypeScript
- Tailwind CSS + Custom CSS + Recharts
- Dashboard, Recovery Cases, Agent Activity, Analytics pages

**Backend:**
- FastAPI + Python
- LangGraph agent (7-node workflow)
- Gemini 2.5 Flash integration
- Scikit-learn recovery probability model

**Database:**
- Supabase PostgreSQL (recovery_cases, agent_logs tables)
- Supabase Auth + Realtime + RLS

**Integrations:**
- Razorpay Test APIs
- Resend (email notifications)

**Existing Agent Nodes:**
DETECT → DIAGNOSE → PREDICT → DECIDE → GUARDRAIL → EXECUTE → VERIFY → LOG

**Existing Guardrails:**
- Transactions above ₹50,000 require human approval
- Maximum 2 automatic retries

---

---

# PHASE 1 — CORE RECOVERY ENGINE

**Goal:** Build the actual end-to-end recovery loop so that
Reclaim can process a real failed payment, execute a real
recovery action, verify it with Razorpay, and measure whether
real money was recovered.

**Why first:** Nothing else is meaningful until the core
recovery loop works end-to-end. Every subsequent phase
builds on this foundation. A beautiful dashboard showing
fake numbers is worse than no dashboard.

---

## STEP 1 — Recovery Case State Machine

**Purpose:**
Define a rigorous, explicit state machine for every
recovery case so that every case has a deterministic,
unambiguous state at all times.

**Required states:**
- `DETECTED` — failure registered, not yet analyzed
- `ANALYZING` — diagnosis and prediction in progress
- `WAITING` — agent decided to wait before acting
- `APPROVED` — human approved a restricted action
- `EXECUTING` — recovery action in progress
- `VERIFYING` — checking Razorpay for actual outcome
- `RECOVERED` — payment confirmed successful
- `FAILED_RECOVERY` — recovery attempted, payment still failed
- `SUPPRESSED` — guardrail stopped action (e.g., too many retries)
- `ESCALATED` — sent to human review queue
- `EXPIRED` — recovery window closed without success

**Acceptance criteria:**
- State transitions are explicit and validated
- Invalid transitions are rejected
- State is persisted in database
- Every state change is timestamped and logged

**Dependencies:**
- Supabase schema must support all states

---

## STEP 2 — Batch Recovery Engine

**Purpose:**
Enable Reclaim to process hundreds or thousands of
revenue-at-risk cases in a single batch run, rather than
only processing one case at a time.

**Required capabilities:**
- Accept a list of recovery cases
- Run the complete recovery workflow on each case
- Process cases concurrently where safe
- Produce batch-level metrics (total attempted, recovered,
  failed, suppressed)
- Handle individual case failures gracefully without
  crashing the batch

**Acceptance criteria:**
- A batch of 100+ cases can be processed
- Batch-level metrics are produced
- Individual case failures do not abort the batch
- Results are persisted per case

---

## STEP 3 — Connect Existing LangGraph Agent

**Purpose:**
Verify that the existing LangGraph agent (DETECT →
DIAGNOSE → PREDICT → DECIDE → GUARDRAIL → EXECUTE →
VERIFY → LOG) is actually connected end-to-end and
produces correct outputs for real cases.

**Do NOT rebuild the agent.**
Inspect, verify, and fix the existing one.

**Acceptance criteria:**
- Agent receives a real recovery case
- Every node executes in correct order
- Agent state is passed correctly between nodes
- Agent produces a final decision
- Agent logs are persisted to database

---

## STEP 4 — Real Recovery Execution

**Purpose:**
Ensure that when the agent decides to execute a recovery
action, the backend actually makes the correct Razorpay
API call — not a mock or simulation.

**Required actions (must actually execute):**
- Smart Retry — call Razorpay to retry payment
- Payment Link — use Razorpay to generate a payment link
- Wait — schedule a future retry, no immediate API call

**Acceptance criteria:**
- Recovery actions call actual Razorpay Test APIs
- API responses are captured and stored
- Failures to execute are logged and handled gracefully
- No recovery action is double-executed

---

## STEP 5 — Real Payment Verification

**Purpose:**
After executing a recovery action, verify the actual
Razorpay payment state to confirm whether the payment
succeeded. Never treat an API request itself as recovery.

**Critical rule:**
- The execution of an API call does NOT count as recovery
- Only a confirmed `captured` or `paid` payment state counts
- Query Razorpay directly after a delay to check actual state

**Acceptance criteria:**
- Post-execution, Razorpay payment state is queried
- Payment status is `captured` or `paid` before marking recovered
- Failed payments are correctly identified as not recovered
- Verification results are persisted

---

## STEP 6 — Measure Actual Money

**Purpose:**
Track and measure real recovered revenue with correct
accounting. This is the core business metric of Reclaim.

**Required measurements:**
- Revenue at Risk (total amount in failed/at-risk cases)
- Recoverable Revenue (estimated from recovery probability)
- Recovery Attempted (amount for cases where action was taken)
- Revenue Recovered (amount from confirmed successful payments)
- Revenue Lost (amount from cases where recovery failed)
- Recovery Rate (Revenue Recovered ÷ Revenue Attempted)

**Critical rule:**
- Only verified successful payments count as recovered
- Do NOT count recovery actions as recovered revenue
- Do NOT count estimated probabilities as recovered revenue

---

---

# PHASE 2 — SAFETY, GUARDRAILS & CONTROL

**Goal:** Ensure Reclaim cannot take incorrect, dangerous,
or duplicate financial actions. The AI may propose, but
deterministic policy must constrain.

**Why second:** Recovery actions involve real money. A system
that works but is unsafe is more dangerous than one that
doesn't work. Safety infrastructure must exist before the
engine is used at scale.

---

## STEP 7 — Razorpay Webhook Integration

**Purpose:**
Process real Razorpay webhook events to detect payment
failures, payment captures, and subscription events in
real-time rather than relying only on polling.

**Required events to handle:**
- `payment.failed` — trigger recovery case creation
- `payment.captured` — mark recovery as successful
- `payment.authorized` — update payment state
- `subscription.charged` — subscription payment success
- `subscription.halted` — subscription payment failure

**Acceptance criteria:**
- Webhook endpoint exists and validates Razorpay signature
- Payment failure creates a recovery case
- Payment capture updates recovery case status
- Duplicate webhook events are safely handled (idempotent)

---

## STEP 8 — Idempotency

**Purpose:**
Ensure that duplicate events, double-clicks, API retries,
and concurrent requests never cause the same recovery
action to execute twice.

**Required protections:**
- Duplicate webhook events → ignored after first processing
- Duplicate agent execution for same case → rejected
- Double-click on "Run Agent" → second click rejected
- Concurrent recovery attempts for same case → only one proceeds
- API retries → safe to retry without side effects

**Acceptance criteria:**
- Same webhook event processed twice → second is a no-op
- Same recovery case run twice concurrently → one wins, one rejects
- No duplicate Razorpay API calls for same action

---

## STEP 9 — Payment State-Race Protection

**Purpose:**
Protect against race conditions between Reclaim's recovery
actions and real payment state changes on Razorpay's side.

**Required protections:**
- Do not permanently mark a payment as lost immediately after
  failure — there may be a delayed authorization
- Re-check actual Razorpay state before executing recovery
- Prevent recovery of an already-successful payment
- Handle late capture events that arrive after recovery started

**Acceptance criteria:**
- Already-successful payment detected before recovery action
- Recovery action is cancelled if payment already captured
- Late authorization events update case state correctly

---

## STEP 10 — Hard Stopping Rules

**Purpose:**
Define and enforce non-negotiable stopping conditions that
no AI decision can override. These are deterministic rules,
not AI suggestions.

**Required hard stops:**
- Maximum retry limit reached (default: 2)
- Recovery window expired
- Case already recovered
- Recovery probability below minimum threshold
- Customer contacted too recently
- Case flagged as high-risk
- Razorpay API returning persistent errors
- No infinite recovery loops under any circumstance

**Acceptance criteria:**
- Each stopping rule is explicitly checked before every action
- Stopping reason is logged
- Stopped cases are moved to `SUPPRESSED` state
- No case can be retried after hitting a hard stop

---

## STEP 11 — Configurable Policy Engine

**Purpose:**
Allow recovery policies to be configured without code
changes. The policy engine is the layer between the AI
recommendation and the executor.

**Required configurable parameters:**
- Maximum automatic retries (default: 2)
- Maximum automatic recovery amount (default: ₹50,000)
- Minimum recovery probability to act (default: 30%)
- Maximum customer contact frequency
- High-value transaction threshold requiring human approval
- Recovery window duration
- Whether human approval is required by default

**Acceptance criteria:**
- All policies are stored in configuration (not hardcoded)
- Policy engine evaluates every agent decision
- Policy violations block execution
- Policy evaluation is logged in audit trail

---

## STEP 12 — Human Approval

**Purpose:**
Implement a human approval workflow for cases that the
policy engine flags as requiring review before action.

**Required functionality:**
- Cases above ₹50,000 automatically enter human review queue
- Cases with low probability but high value enter queue
- Cases with repeated failures enter queue
- Dashboard shows pending approvals
- Approver can approve or reject with a reason
- Approved cases proceed to execution
- Rejected cases are moved to `SUPPRESSED`

**Acceptance criteria:**
- Human review queue exists in dashboard
- Approval/rejection is persisted
- Approval logs show who approved and when
- Approved case proceeds to execution automatically
- Rejected case does not execute

---

## STEP 13 — Complete Audit Trail

**Purpose:**
Record every single event, decision, and action so that
any recovery case can be fully reconstructed after the fact.

**Every audit record must contain:**
- Timestamp
- Event type (webhook received, diagnosis, prediction,
  decision, policy evaluation, approval, execution,
  verification, final outcome)
- Actor (AI, policy engine, human approver, system)
- Inputs at that moment
- Output/decision
- Reasoning (for AI decisions)
- Result

**Acceptance criteria:**
- Every node of the agent writes an audit record
- Every policy evaluation writes an audit record
- Every human approval/rejection writes an audit record
- Every Razorpay API call and response is logged
- Audit trail is queryable by case ID

---

---

# PHASE 3 — RECOVERY DECISION ENGINE

**Goal:** Make the recovery decision more intelligent.
The agent should not just choose between "retry" and "send link"
— it should evaluate multiple interventions, rank them, and
choose the best one based on expected recovery value.

---

## STEP 14 — Razorpay Failure Classification

**Purpose:**
Classify Razorpay failure reasons into categories that
drive different recovery strategies.

**Required classification categories:**
- `TEMPORARY_NETWORK` — UPI timeout, connection issue → retry likely works
- `BANK_DECLINE` — bank rejected, insufficient funds → retry may not work
- `CARD_ISSUE` — expired card, wrong CVV → need alternative payment
- `FRAUD_BLOCK` — bank blocked for suspected fraud → escalate
- `SUBSCRIPTION_HALT` — subscription billing failed → notify + retry
- `ABANDONMENT` — customer left checkout → reminder needed
- `UNKNOWN` — unclassified

**Acceptance criteria:**
- All common Razorpay error codes are classified
- Classification drives intervention selection
- Classification is stored on recovery case

---

## STEP 15 — Recovery Probability

**Purpose:**
Calculate a calibrated probability score (0–100%) for
each recovery case representing the likelihood that a
recovery action will result in actual payment.

**Input features:**
- Failure reason category
- Transaction amount
- Customer's historical success rate
- Number of previous retries
- Time since failure
- Payment method
- Customer value tier

**Acceptance criteria:**
- Probability is calculated for every recovery case
- Probability is a calibrated percentage (not just a heuristic)
- High-probability cases are distinguishable from low-probability ones
- Probability is stored and displayed

---

## STEP 16 — Expected Recovery Value

**Purpose:**
Calculate the expected monetary value of a recovery
attempt for each case: `Recovery Probability × Amount at Risk`.

This is the primary metric for prioritization.

**Acceptance criteria:**
- Expected Recovery Value is calculated for every case
- It uses the calibrated probability from Step 15
- It is stored and displayed
- Dashboard shows total expected recovery value

---

## STEP 17 — Recovery Priority Score

**Purpose:**
Combine Expected Recovery Value with urgency (time
remaining in recovery window) and customer value to
produce a single priority score for ranking cases.

**Acceptance criteria:**
- Priority score combines value, urgency, and customer tier
- Cases are rankable by priority score
- Priority score drives batch processing order

---

## STEP 18 — Intervention Ranking

**Purpose:**
For each recovery case, evaluate multiple possible
interventions (retry, payment link, wait, escalate, stop)
and rank them by expected outcome. The AI selects the
highest-ranked intervention that passes guardrails.

**Acceptance criteria:**
- Multiple interventions are evaluated per case
- Each intervention has an estimated probability of success
- The agent selects the top-ranked intervention
- Ranking is logged in the audit trail

---

## STEP 19 — Recovery Window

**Purpose:**
Define and enforce a maximum time window after failure
during which recovery is still viable. After this window
expires, further attempts are unlikely to succeed and
may annoy the customer.

**Default recovery windows:**
- Failed payment: 24 hours
- Abandoned checkout: 48 hours
- Failed subscription: 72 hours

**Acceptance criteria:**
- Recovery window is tracked per case
- Cases past their window are moved to `EXPIRED`
- Expired cases are not retried

---

## STEP 20 — Recovery Suppression

**Purpose:**
Suppress recovery attempts for cases where the system
determines that attempting recovery would be harmful or
pointless (e.g., confirmed fraud, permanently blocked card,
customer has opted out).

**Acceptance criteria:**
- Suppression reasons are explicitly categorized
- Suppressed cases are not re-attempted
- Suppression is logged

---

## STEP 21 — Customer Fatigue Protection

**Purpose:**
Prevent over-contacting a customer with recovery attempts
or messages. Too many contacts damage trust and may
violate regulations.

**Required rules:**
- Maximum N contacts per customer per time window
- Minimum time between contacts
- Opt-out honored immediately

**Acceptance criteria:**
- Contact frequency is tracked per customer
- Attempts exceeding frequency limit are blocked
- Opt-out stops all further contact

---

---

# PHASE 4 — RAZORPAY-SPECIFIC INTELLIGENCE

**Goal:** Add intelligence specific to Razorpay's behavior,
including awareness of Razorpay system downtime and the
ability to route customers to alternative payment methods.

---

## STEP 22 — Razorpay Downtime Intelligence

**Purpose:**
Detect when Razorpay or a specific payment method
(UPI, cards, netbanking) is experiencing elevated failure
rates that indicate a systemic issue rather than individual
customer problems. In these cases, Reclaim should WAIT
rather than retry.

**Acceptance criteria:**
- Failure rate by payment method is monitored
- Elevated failure rate triggers a "possible downtime" alert
- Recovery cases are moved to WAIT during suspected downtime
- Cases are re-evaluated when failure rates normalize

---

## STEP 23 — WAIT Action

**Purpose:**
Implement a WAIT intervention where Reclaim explicitly
decides to wait before acting (e.g., for network issues
to resolve or for Razorpay downtime to pass). This is a
first-class action, not an absence of action.

**Acceptance criteria:**
- WAIT is a selectable action in the agent
- WAIT schedules a future re-evaluation at a specific time
- Waiting cases are tracked in the system
- Re-evaluation automatically triggers at the scheduled time

---

## STEP 24 — Alternative Payment Method

**Purpose:**
When the original payment method is unlikely to work
(e.g., expired card, bank-specific issue), recommend and
generate a Razorpay payment link for an alternative method.

**Acceptance criteria:**
- Alternative payment link is generated via Razorpay API
- Link is sent to customer via email (Resend)
- Link is tracked to determine if customer used it
- Payment via link is detected and counted as recovered

---

## STEP 25 — Re-evaluation

**Purpose:**
Allow a recovery case to be re-evaluated after an
initial WAIT or after a new event (e.g., customer
visited the site again, Razorpay status changed).
Re-evaluation runs the decision engine again on fresh data.

**Acceptance criteria:**
- Re-evaluation is triggered by time, event, or manual action
- Re-evaluation uses the latest case state and payment state
- Re-evaluation result may differ from initial decision
- Both evaluations are recorded in the audit trail

---

---

# PHASE 5 — PROVE RECLAIM ACTUALLY WORKS

**Goal:** Demonstrate with data that Reclaim recovers
more revenue than a naive baseline approach. This is the
core business proof required by the hackathon.

---

## STEP 26 — Baseline Strategy

**Purpose:**
Define and implement a simple baseline recovery strategy
that represents what a merchant would do without Reclaim:
retry every failed payment once after a fixed delay.

**Acceptance criteria:**
- Baseline strategy is implemented as a separate mode
- Baseline processes the same dataset as Reclaim
- Baseline produces recovery metrics

---

## STEP 27 — Reclaim Strategy

**Purpose:**
Ensure Reclaim's full intelligence stack (classification,
probability, intervention ranking, guardrails) runs on
the same dataset as the baseline for fair comparison.

**Acceptance criteria:**
- Reclaim strategy processes the same test dataset
- All intelligence features are active
- Reclaim produces recovery metrics in the same format
  as baseline

---

## STEP 28 — Run Same Dataset

**Purpose:**
Run both the baseline and Reclaim strategies on the
exact same set of recovery cases so results are comparable.

**Acceptance criteria:**
- Same case IDs processed by both strategies
- Results stored separately but linked to cases
- Comparison is reproducible

---

## STEP 29 — Compare Results

**Purpose:**
Produce a side-by-side comparison of baseline vs.
Reclaim on all key metrics.

**Metrics to compare:**
- Revenue Recovered
- Recovery Rate
- Cases Attempted
- Cases Recovered
- False Positives (retried but payment already failed permanently)
- Customer Contacts Made

**Acceptance criteria:**
- Comparison table exists in dashboard
- Difference (absolute and percentage) is calculated
- Comparison is explainable

---

## STEP 30 — Incremental Revenue

**Purpose:**
Calculate the incremental revenue recovered by Reclaim
above and beyond what the baseline would have recovered.
This is Reclaim's core value proposition.

**Formula:**
`Incremental Revenue = Reclaim Recovered - Baseline Recovered`

**Acceptance criteria:**
- Incremental revenue is calculated
- It is displayed prominently in dashboard
- Methodology is transparent

---

## STEP 31 — Recovery Attribution

**Purpose:**
For each recovered payment, attribute the recovery to
the specific intervention that caused it (e.g., "Smart
Retry at 5 min recovered ₹4,999 for case #TXN001").

**Acceptance criteria:**
- Every recovered payment is attributed to an intervention
- Attribution is stored in the database
- Attribution is visible in case detail view

---

## STEP 32 — Recovery Funnel

**Purpose:**
Track and visualize the full recovery funnel from
detection to final outcome, showing how many cases
pass through each stage.

**Funnel stages:**
1. Detected
2. Analyzed
3. Eligible for Recovery (passed guardrails)
4. Action Executed
5. Verified Successful

**Acceptance criteria:**
- Funnel metrics are calculated
- Funnel is visualized in dashboard
- Conversion rates between stages are shown

---

## STEP 33 — Revenue-at-Risk Aging

**Purpose:**
Show how revenue at risk ages over time — cases that
are older are less likely to be recovered. This drives
urgency in the dashboard.

**Acceptance criteria:**
- Cases are bucketed by age (0–6 hrs, 6–24 hrs, 1–3 days, 3+ days)
- Revenue at risk per bucket is calculated
- Aging visualization exists in dashboard

---

## STEP 34 — Recovery Analytics

**Purpose:**
Provide comprehensive analytics on recovery performance
across all dimensions.

**Required breakdowns:**
- Recovery rate by failure reason
- Recovery rate by payment method
- Recovery rate by intervention type
- Recovery rate by customer value tier
- Revenue recovered over time (trend)
- Average time to recovery

**Acceptance criteria:**
- All breakdowns are calculated from real data
- Analytics are displayed in dashboard
- Analytics update when new recoveries happen

---

---

# PHASE 6 — AI INTELLIGENCE & EXPLAINABILITY

**Goal:** Make Reclaim's AI decisions transparent and
understandable. Every decision must be explainable —
not just to engineers, but in a way that a merchant
can read and understand.

---

## STEP 35 — Decision Trace

**Purpose:**
For every recovery case, produce a complete record of
every input, intermediate value, and output that led
to the final decision.

**Acceptance criteria:**
- Decision trace is persisted per case
- Trace includes: failure classification, probability,
  expected value, interventions considered, guardrail
  evaluations, final decision
- Trace is viewable in the case detail page

---

## STEP 36 — "WHY THIS ACTION?"

**Purpose:**
Generate a human-readable explanation for why Reclaim
chose the action it did. This should be readable by
a non-technical merchant.

**Example output:**
> "We chose Smart Retry because this is a UPI timeout
> failure. This customer has completed 8 previous
> payments successfully. The recovery probability is 91%.
> Retrying after 5 minutes has a high success rate for
> this failure type."

**Acceptance criteria:**
- Explanation is generated by Gemini AI
- Explanation is stored per case
- Explanation is shown in case detail view

---

## STEP 37 — "WHY NOT OTHER ACTIONS?"

**Purpose:**
Explain why Reclaim rejected the alternative actions
that were considered.

**Example output:**
> "We did not send a payment link because the customer
> has a high prior success rate with UPI and the failure
> appears temporary. Sending a payment link may cause
> unnecessary friction."

**Acceptance criteria:**
- Rejected alternatives and reasons are stored
- Explanation is shown alongside the chosen action

---

## STEP 38 — AI vs Policy

**Purpose:**
Clearly distinguish in the audit trail and UI between
what the AI recommended and what the policy engine
permitted. When the policy overrides the AI, this must
be visible.

**Example scenarios:**
- AI recommended retry, but policy blocked (max retries reached)
- AI recommended immediate action, policy moved to human queue
- AI recommended no action, but case is high-value so escalated

**Acceptance criteria:**
- AI recommendation is stored separately from final action
- Policy evaluation outcome is stored
- When they differ, both are shown in the audit trail

---

## STEP 39 — Recovery Timing Optimization

**Purpose:**
Use historical data to determine the optimal time to
execute a recovery action for different failure types.

**Example:**
- UPI timeouts: retry after 5 minutes
- Bank declines: retry after 2 hours (bank cooling period)
- Abandoned checkouts: reminder after 30 minutes

**Acceptance criteria:**
- Timing recommendations are based on data
- Timing is used in the WAIT action scheduler
- Timing is logged in the audit trail

---

## STEP 40 — Customer Recovery Memory

**Purpose:**
Track what interventions have previously been attempted
for a specific customer, and use this to avoid repeating
failed approaches.

**Acceptance criteria:**
- Customer's recovery history is retrieved before deciding
- Previously failed interventions are deprioritized
- History is used in the intervention ranking step

---

## STEP 41 — Intervention Outcome Learning

**Purpose:**
Track which interventions succeeded and which failed
across all customers, and use this to improve future
intervention ranking.

**Acceptance criteria:**
- Outcome of each intervention is recorded
- Aggregate success rates by intervention type are calculated
- Intervention ranking uses historical success rates

---

---

# PHASE 7 — ML VALIDATION

**Goal:** Ensure the recovery probability model is
actually calibrated and trustworthy.

---

## STEP 42 — Dataset Split

**Purpose:**
Properly split the synthetic/historical dataset into
training and test sets to prevent data leakage in
model evaluation.

**Acceptance criteria:**
- Dataset is split (e.g., 80/20 train/test)
- Test set is not used during training
- Split is reproducible

---

## STEP 43 — Model Evaluation

**Purpose:**
Evaluate the recovery probability model on held-out
test data with proper metrics.

**Required metrics:**
- AUC-ROC
- Precision-Recall at different thresholds
- F1 Score
- Accuracy

**Acceptance criteria:**
- Model is evaluated on test set only
- Metrics are calculated and stored
- Model performance is acceptable before deployment

---

## STEP 44 — Probability Calibration

**Purpose:**
Ensure that when the model outputs "70% recovery
probability", the actual observed recovery rate for
cases in that bucket is close to 70%.

**Acceptance criteria:**
- Calibration curve is plotted
- Model is re-calibrated if poorly calibrated
- Calibrated probabilities are used in production

---

---

# PHASE 8 — RELIABILITY & FAILURE HANDLING

**Goal:** Ensure Reclaim handles all failure modes
gracefully — API errors, webhook failures, out-of-order
events, timeouts, and database inconsistencies.

---

## STEP 45 — API Failure Handling

**Purpose:**
Handle Razorpay and other external API failures
gracefully without corrupting case state or leaving
cases in undefined states.

**Acceptance criteria:**
- API timeouts are retried with exponential backoff
- Permanent API failures move case to a safe state
- All API errors are logged with full context

---

## STEP 46 — Webhook Failure Handling

**Purpose:**
Handle failures in webhook processing, including
failed delivery, processing errors, and out-of-order
arrival.

**Acceptance criteria:**
- Failed webhook processing is retried
- Permanently failed webhooks are queued for manual review
- Webhook processing failures are logged

---

## STEP 47 — Out-of-Order Events

**Purpose:**
Handle Razorpay webhook events that arrive in the
wrong order (e.g., `payment.captured` arrives before
`payment.failed` for the same payment).

**Acceptance criteria:**
- Out-of-order events are detected
- Case state is reconciled correctly
- Final state reflects the correct current state

---

## STEP 48 — Agent Timeout Handling

**Purpose:**
Handle cases where the LangGraph agent takes too long
to complete, preventing cases from being stuck in
`ANALYZING` or `EXECUTING` state indefinitely.

**Acceptance criteria:**
- Agent execution has a maximum timeout
- Timed-out cases are moved to a safe state
- Timeout is logged in the audit trail
- Timed-out cases can be re-triggered manually

---

## STEP 49 — AI Failure Fallback

**Purpose:**
Handle failures in the Gemini AI API (rate limits,
errors, timeouts) without crashing the recovery workflow.
The system must degrade gracefully to rule-based decisions.

**Acceptance criteria:**
- AI API failures fall back to rule-based classification
- Fallback decisions are logged and labeled as "rule-based"
- Fallback does not crash the agent
- Recovery can still proceed without AI

---

## STEP 50 — Database Consistency

**Purpose:**
Ensure that all database operations related to recovery
are atomic and consistent. No partial updates that leave
a case in a corrupt state.

**Acceptance criteria:**
- Multi-step operations use database transactions
- Failed transactions are rolled back
- No case is left in an intermediate/undefined state

---

## STEP 51 — Recovery Job Retry

**Purpose:**
Implement reliable retry for background recovery jobs
that fail mid-execution.

**Acceptance criteria:**
- Failed background jobs are retried
- Jobs that have already partially executed are not re-executed
  from the beginning (idempotent retry)
- Maximum retry attempts before marking as permanently failed

---

## STEP 52 — Structured Observability

**Purpose:**
Implement structured logging and error tracking so
that failures can be quickly diagnosed in production.

**Acceptance criteria:**
- All errors are logged with structured context (case ID,
  step, inputs, error message, stack trace)
- Log levels are used correctly (DEBUG, INFO, WARNING, ERROR)
- Critical errors are distinguishable from expected errors

---

---

# PHASE 9 — RAZORPAY SCENARIO COVERAGE

**Goal:** Ensure each of the five recovery scenarios
works correctly end-to-end.

---

## STEP 53 — Failed Payment Recovery

**Purpose:**
Test and verify the complete end-to-end flow for
a single failed payment recovery:
detect → diagnose → probability → decide → guardrail →
execute retry → verify → measure.

---

## STEP 54 — Checkout Abandonment Recovery

**Purpose:**
Test and verify the complete end-to-end flow for
abandoned checkout recovery:
detect abandonment → analyze behavior → generate
personalized reminder → send email → track if customer
returns → measure recovery.

---

## STEP 55 — Failed Subscription Recovery

**Purpose:**
Test and verify the complete end-to-end flow for
failed subscription payment recovery:
detect subscription failure → analyze → notify customer →
retry → verify → measure.

---

## STEP 56 — Payment Downtime Recovery

**Purpose:**
Test and verify the Razorpay downtime intelligence
scenario: detect elevated failure rate → classify as
likely downtime → WAIT → re-evaluate when rates normalize →
recover cases that can be recovered.

---

## STEP 57 — Alternative Payment Recovery

**Purpose:**
Test and verify the alternative payment method scenario:
original method fails permanently → generate payment
link → customer uses link → payment captured → measure
recovery.

---

---

# PHASE 10 — COMMAND CENTER / DASHBOARD

**Goal:** Build a dashboard that shows real recovery
data in a way that clearly communicates Reclaim's
value to a merchant. Money first. Numbers that matter.

---

## STEP 58 — Money-First Dashboard

**Purpose:**
The main dashboard must lead with the most important
financial metrics. No vanity metrics.

**Required top-level KPIs:**
- Revenue at Risk (total ₹)
- Revenue Recovered (total ₹)
- Expected Recovery (total ₹)
- Recovery Rate (%)

---

## STEP 59 — Batch Recovery

**Purpose:**
Add a dashboard button to trigger a batch recovery
run. Show progress and results as the batch processes.

---

## STEP 60 — Recovery Funnel

**Purpose:**
Visualize the recovery funnel from detection to
recovery.

---

## STEP 61 — Recovery Cases

**Purpose:**
A filterable, sortable table of all recovery cases
showing key fields.

---

## STEP 62 — Human Review Queue

**Purpose:**
Dashboard view showing all cases awaiting human
approval. Allow approving or rejecting with a reason.

---

## STEP 63 — Live Agent Timeline

**Purpose:**
When a recovery case is being processed, show a
live, animated timeline of the agent's steps in
real-time.

---

## STEP 64 — Decision Trace

**Purpose:**
Case detail page showing the complete decision trace
for a specific recovery case.

---

## STEP 65 — Recovery Attribution

**Purpose:**
Show which interventions caused which recoveries.

---

## STEP 66 — Aging

**Purpose:**
Visualize revenue-at-risk aging by time bucket.

---

---

# PHASE 11 — FINAL DEMO

**Goal:** Prepare a 5-minute end-to-end demonstration
that proves Reclaim works and delivers value.

---

## STEP 67 — Prepare Demonstration Dataset

**Purpose:**
Create a curated seed dataset that covers all major
recovery scenarios for demonstration purposes.

---

## STEP 68 — Batch Run

**Purpose:**
Demonstrate running Reclaim on the full demo dataset
and producing results.

---

## STEP 69 — Show Intelligence

**Purpose:**
Demonstrate that Reclaim makes different decisions for
different failure types, not blind retries.

---

## STEP 70 — Show Safety

**Purpose:**
Demonstrate that guardrails work: show a case that
triggers human approval, a case that is suppressed,
and a case that hits the hard stop.

---

## STEP 71 — Show Recovery

**Purpose:**
Demonstrate an actual end-to-end recovery with
Razorpay payment state verification.

---

## STEP 72 — Show Audit

**Purpose:**
Demonstrate the complete audit trail for a recovered case.

---

## STEP 73 — Show Business Impact

**Purpose:**
Show the incremental revenue comparison: Reclaim vs.
baseline. Show the final recovered revenue number.

---

---

# PHASE 12 — FINAL POLISH

**Goal:** Polish the product to feel premium and production-ready
for the demo. This phase comes LAST.

---

## STEP 74 — Real-Time Money Counter

**Purpose:**
A live counter on the dashboard showing revenue being
recovered in real-time during a batch run.

---

## STEP 75 — Real-Time Agent Timeline

**Purpose:**
Ensure the live agent timeline animates smoothly and
correctly as steps complete.

---

## STEP 76 — Recovery Funnel Visualization

**Purpose:**
Final polish of the recovery funnel chart.

---

## STEP 77 — Loading / Error / Empty States

**Purpose:**
Every dashboard page and component must have proper
loading, error, and empty states. No blank screens or
unhandled errors.

---

## STEP 78 — Chart Polish

**Purpose:**
All charts must be polished, labeled, and readable.

---

## STEP 79 — UI Polish

**Purpose:**
Final UI review — spacing, typography, colors, and
responsiveness.

---

## STEP 80 — Demo Seed Data

**Purpose:**
Final verification that the demo seed data produces
impressive and correct results for all scenarios.

---

## STEP 81 — Final End-to-End Test

**Purpose:**
Run a complete end-to-end test of the entire system
from webhook receipt to recovered revenue measurement.
Every part of the system must work together.

---

---

# Final Completion Criteria

Reclaim is complete when ALL of the following are true:

1. The full 81-step roadmap is implemented and verified.
2. All checklist items in RECLAIM_IMPLEMENTATION_CHECKLIST.md
   are marked `[x]`.
3. The Mandatory Final Demo Checklist in the checklist file
   is fully checked.
4. A 5-minute demo runs cleanly end-to-end.
5. Reclaim provably recovers more revenue than the baseline.
6. Every AI decision is explainable.
7. No recovery action executes without passing guardrails.
8. Audit trail is complete for every processed case.

---

*This file is the authoritative implementation order for Reclaim.*
*Last updated: 2026-09-04*
*Do not modify phases or steps without project-owner approval.*
