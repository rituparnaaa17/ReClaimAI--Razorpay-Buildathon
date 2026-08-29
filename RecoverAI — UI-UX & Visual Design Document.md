# ReclaimAI
### AI Revenue Recovery Platform
### UI/UX & Visual Design Document

---

## 1. Design Direction

### Design inspiration

The primary visual reference is Ramotion's HackerRank SaaS landing page concept.

Reference characteristics we want to retain:

- Dark premium background
- Large editorial typography
- Minimal navigation
- Strong visual hero
- AI-focused storytelling
- High contrast
- Subtle glow effects
- Clean cards
- Strong CTA
- Enterprise/SaaS feel

The reference uses a dark `#010303` base with muted green and bright green accents.

### What changes for ReclaimAI

Instead of a developer/AI visual, ReclaimAI should communicate:

> **Revenue is leaking → ReclaimAI finds it → AI decides what to do → revenue comes back.**

The product should feel:

**Financial + Intelligent + Reliable + Premium + Trustworthy**

---

# 2. Brand Personality

ReclaimAI should feel:

### Intelligent
The product understands why revenue is being lost.

### Reliable
Financial products cannot feel experimental.

### Fast
The AI identifies and responds to revenue leakage quickly.

### Transparent
Every AI decision should be explainable.

### Premium
The interface should look like a serious fintech product.

---

# 3. Visual Theme

## Primary theme

### Dark mode first

Use a near-black background instead of pure black.

```text
Background:
#080A09

Secondary background:
#0E1210

Card:
#111713

Card hover:
#151C17
```

---

# 4. Accent Colors

Instead of copying HackerRank's exact green, adapt the idea to ReclaimAI.

### Primary AI green

```text
#19D879
```

Used for:

- Primary CTA
- Successful recovery
- Positive metrics
- AI indicators
- Important highlights

### Soft green

```text
#67C99A
```

Used for:

- Secondary highlights
- Graphs
- AI explanation elements

### Warning

```text
#F5B84B
```

Used for:

- Revenue at risk
- Pending recovery
- Medium-risk actions

### Error

```text
#FF6262
```

Used sparingly for:

- Failed payments
- Recovery failures
- Critical alerts

### Text

```text
Primary:
#F4F1E8

Secondary:
#A7ADA8

Muted:
#6D746F
```

---

# 5. Typography

Use a modern sans-serif.

Recommended:

### Primary

**Inter**

or

**Geist**

### Hero

Use a large, slightly tighter-weight font.

Example:

```text
Your lost revenue
doesn't have to stay lost.
```

"lost revenue" can use the green accent.

---

# 6. Navigation

Keep navigation extremely simple.

### Desktop

```text
ReclaimAI

Product
How it works
Recovery
AI Agent
Insights

                         Login
                    [ Get Started ]
```

### Design

- Transparent background
- Slight blur
- Sticky on scroll
- Thin bottom border
- Minimal links

Do not overcrowd the navbar.

---

# 7. Hero Section

This is the most important section.

Instead of the HackerRank visual showing a person interacting with AI, ReclaimAI should show a **visual representation of money flowing through the AI recovery system**.

## Hero headline

### Option A — Recommended

> **Turn failed payments into recovered revenue.**

Subheading:

> ReclaimAI finds revenue slipping away, understands why it happened, and autonomously chooses the safest way to win it back.

CTA:

**[ See ReclaimAI in action ]**

Secondary:

**[ Explore the platform ]**

---

# 8. Hero Visual

The hero should contain a large floating AI recovery dashboard.

### Visual concept

```text
        REVENUE AT RISK

           ₹25.4L
              ↓

       ┌───────────────┐
       │ AI ANALYZING  │
       │ 2,431 CASES   │
       └───────┬───────┘
               ↓
      ┌──────────────────┐
      │ Recovery Agent   │
      │                  │
      │ Diagnose         │
      │ Predict          │
      │ Decide           │
      │ Recover          │
      └────────┬─────────┘
               ↓

        ₹16.8L RECOVERED
```

Add subtle animated green particles moving from:

**Revenue at Risk → AI Agent → Revenue Recovered**

This becomes the visual identity of the product.

---

# 9. Hero Micro-animation

The hero should feel alive.

### Animation sequence

```text
Payment Failed
      ↓
AI Detecting
      ↓
Root Cause Found
      ↓
Recovery Strategy Selected
      ↓
Payment Retried
      ↓
✓ ₹4,999 Recovered
```

Each stage appears progressively.

This is much more relevant to ReclaimAI than a generic AI animation.

---

# 10. Hero Metric Strip

Immediately below the hero:

```text
₹25.4L
Revenue at Risk

₹16.8L
Revenue Recovered

66.1%
Recovery Rate

2,431
Cases Resolved
```

These numbers can initially be demo/synthetic data.

The purpose is to communicate **business impact immediately**.

---

# 11. Problem Section

Headline:

> **Revenue doesn't disappear. It slips through the cracks.**

Three large cards:

### Failed Payments

> Customers want to pay, but something goes wrong.

### Abandoned Checkout

> Customers leave before completing the purchase.

### Failed Subscriptions

> Recurring revenue silently disappears.

Each card should contain:

- Small icon
- Short description
- Example ₹ amount
- Subtle animation

---

# 12. "Before vs ReclaimAI" Section

This should be one of the strongest sections.

### Traditional approach

```text
Payment Failed
      ↓
Merchant gets notification
      ↓
Merchant investigates
      ↓
Manual follow-up
      ↓
Revenue potentially lost
```

### ReclaimAI

```text
Payment Failed
      ↓
AI detects
      ↓
AI diagnoses
      ↓
AI predicts
      ↓
AI chooses action
      ↓
Recovery
      ↓
Revenue recovered
```

Use a split-screen design.

Left:

**Without ReclaimAI**

Right:

**With ReclaimAI**

---

# 13. AI Agent Section

This is where you explain the intelligence.

Headline:

> **An AI agent that doesn't just detect the problem. It closes the loop.**

Show the workflow horizontally:

```text
01
Detect

02
Diagnose

03
Predict

04
Decide

05
Recover

06
Verify
```

Each step expands when hovered.

---

# 14. Agent Visualization

Create a large central circular AI visualization.

Center:

```text
RECLAIMAI
AGENT
```

Around it:

```text
Payments
Customers
Checkout
Subscriptions
History
Risk
```

Then show actions coming out:

```text
Retry
Notify
Recover
Escalate
Stop
```

This gives the site an "agentic" feel without making it look like a generic chatbot.

---

# 15. Interactive Recovery Case

This should be the main product demonstration.

Display:

### Payment Recovery

```text
₹4,999
Payment Failed

UPI Timeout
```

Then:

### AI Analysis

```text
Recovery probability
91%

Customer payment history
8 successful / 1 failed

Recommended action
Smart Retry
```

CTA:

**[ Run Recovery ]**

When clicked:

```text
Analyzing...
      ↓
Policy verified
      ↓
Retry initiated
      ↓
Payment successful
```

Then:

### ✓ ₹4,999 Recovered

This should be an actual working demo connected to your backend/Razorpay test mode.

---

# 16. Dashboard Preview

The landing page should include a large product screenshot/interactive mockup.

### Dashboard layout

```text
┌──────────────────────────────────────────────┐
│ ReclaimAI                         Merchant ▼ │
├─────────────┬────────────────────────────────┤
│             │                                │
│ Dashboard   │ Revenue Overview               │
│             │                                │
│ Recovery    │ ₹25.4L     ₹16.8L             │
│ Cases       │ At Risk    Recovered           │
│             │                                │
│ Customers   │ ───────── Revenue Chart ────   │
│             │                                │
│ Agent       │ Recovery Cases                 │
│ Activity    │                                │
│             │ TXN001  ₹4,999  Recovered     │
│ Settings    │ TXN002  ₹8,200  Processing    │
│             │ TXN003  ₹1,299  Failed        │
└─────────────┴────────────────────────────────┘
```

---

# 17. Main Application Navigation

After login:

```text
Overview
Recovery Cases
Transactions
AI Agent
Analytics
Customers
Settings
```

### Most important:

**Overview**

**Recovery Cases**

**AI Agent**

These should receive the most design attention.

---

# 18. Recovery Cases Page

Display cases in a clean table.

Columns:

```text
Transaction
Customer
Amount
Problem
Recovery Probability
Recommended Action
Status
```

Example:

```text
TXN_10291
₹4,999
UPI Timeout
91%
Smart Retry
✓ Recovered
```

Use filters:

- All
- At Risk
- Processing
- Recovered
- Failed
- Human Review

---

# 19. Case Details Page

This is where judges should see the intelligence.

### Header

```text
Recovery Case #RC_10291

₹4,999
Payment Failed
```

### AI Decision

```text
Recovery Probability
91%

Root Cause
Temporary UPI timeout

Recommended Action
Smart Retry
```

### Why?

```text
✓ Customer has 8 successful payments
✓ Failure appears temporary
✓ Only 1 previous retry
✓ Transaction value is within recovery policy
```

---

# 20. Agent Activity Timeline

Below the AI decision:

```text
10:30:01
Payment failure detected

10:30:02
Customer history analyzed

10:30:03
Root cause identified

10:30:03
Recovery probability calculated: 91%

10:30:04
Smart Retry selected

10:30:04
Policy validation passed

10:30:05
Recovery initiated

10:30:07
✓ Payment recovered
```

This gives judges a clear view of the agent's reasoning and execution.

---

# 21. Analytics Page

The analytics page should focus on **money**, not vanity metrics.

### Primary metrics

```text
Revenue at Risk
₹25.4L

Revenue Recovered
₹16.8L

Recovery Rate
66.1%

Avg Recovery Time
4m 32s
```

### Charts

1. Revenue at risk vs recovered
2. Recovery by failure type
3. Recovery by payment method
4. Recovery success rate
5. Recovery trend

---

# 22. AI Insights

Add an AI-generated insight card.

Example:

> **AI Insight**

> UPI timeout failures increased 18% this week. Customers with previous successful UPI payments have an 84% recovery probability after a delayed retry.

CTA:

**[ View affected cases ]**

This makes the dashboard feel intelligent rather than simply analytical.

---

# 23. Trust & Safety Section

Because this is a fintech product, trust should be visible.

Headline:

> **AI that acts within boundaries.**

Show:

### Policy Controls

- Maximum retry limit
- Transaction limits
- Human approval
- Audit trail
- Test-mode payments

Visual:

```text
AI Decision
     ↓
Policy Check
     ↓
Approved ✓
     ↓
Action
```

This is especially important because the buildathon expects bounded, explainable money actions.

---

# 24. "Built for Real Revenue" Section

Use a large dark section with four cards:

```text
01
Failed Payments

02
Abandoned Checkout

03
Failed Subscriptions

04
Overdue Revenue
```

Each card can show:

**Problem → AI Action → Result**

---

# 25. Final CTA

Large closing section:

> **Stop watching revenue disappear.**

Subheading:

> Let AI find it, recover it, and show you exactly what it saved.

CTA:

### **[ Start Recovering Revenue → ]**

Secondary:

**View live demo**

---

# 26. Footer

Minimal footer:

```text
ReclaimAI

AI-powered revenue recovery

Product
How it Works
Dashboard
AI Agent
Analytics

Resources
Documentation
API
Security

Built for Razorpay Buildathon
```

---

# 27. UI Component System

## Buttons

### Primary

Green filled button.

```text
[ Start Recovery → ]
```

### Secondary

Dark transparent button with border.

```text
[ View Demo ]
```

### Destructive

Red only when genuinely necessary.

---

# 28. Cards

Cards should have:

- 16–20px radius
- Very subtle border
- Dark surface
- Minimal shadow
- Small hover movement

Avoid excessive glassmorphism.

Use:

**solid dark cards + subtle borders + controlled glow**

instead of making every element glassy.

---

# 29. Icons

Use:

**Lucide React**

Icons should be:

- Thin
- Minimal
- Consistent

Examples:

- `CreditCard`
- `Wallet`
- `Bot`
- `RefreshCw`
- `TrendingUp`
- `AlertTriangle`
- `CheckCircle`
- `ShieldCheck`

---

# 30. Motion Design

Animations should communicate product behavior.

### Use

- Fade-in
- Slide-up
- Number counters
- Chart animations
- Progress animations
- AI processing pulse
- Timeline progression
- Subtle card hover

### Avoid

- Excessive bouncing
- Random particles everywhere
- Huge 3D animations
- Long loading animations

The product is fintech, so motion should feel **controlled and trustworthy**.

---

# 31. Responsive Design

### Desktop

Primary experience:

**1440px / 1280px**

### Tablet

Collapse dashboard navigation.

### Mobile

Use:

```text
Bottom Navigation

Home
Cases
Agent
Analytics
```

Cards stack vertically.

---

# 32. Design System Summary

| Element | Direction |
|---|---|
| Theme | Dark fintech |
| Background | Near-black |
| Accent | AI green |
| Typography | Inter / Geist |
| Border | Subtle |
| Radius | 16–20px |
| Cards | Dark solid |
| Buttons | Green primary |
| Charts | Minimal |
| Icons | Lucide |
| Animation | Subtle + purposeful |
| Visual style | Premium SaaS |
| Mood | Intelligent + trustworthy |

---

# 33. Landing Page Structure

The final page should follow:

```text
NAVBAR
   ↓
HERO
"Turn failed payments into recovered revenue."
   ↓
LIVE REVENUE METRICS
   ↓
THE PROBLEM
"Revenue slips through the cracks."
   ↓
BEFORE vs RECLAIMAI
   ↓
AI AGENT
Detect → Diagnose → Predict → Decide → Recover
   ↓
INTERACTIVE RECOVERY DEMO
   ↓
PRODUCT DASHBOARD
   ↓
AI INSIGHTS
   ↓
TRUST & SAFETY
   ↓
USE CASES
   ↓
FINAL CTA
   ↓
FOOTER
```

---

# 34. Key Design Principle

The most important design decision is:

> **Don't make ReclaimAI look like an AI chatbot.**

Make it look like a **financial operating system powered by AI**.

The AI should appear inside:

- Recovery decisions
- Analytics
- Case investigation
- Agent timeline
- Recommendations

rather than having a giant chatbot window everywhere.

---

# 35. Final Visual Concept

The overall visual story should be:

```text
              MONEY LEAKING
                   ↓
          ┌─────────────────┐
          │   RECLAIMAI     │
          │                 │
          │  AI AGENT       │
          │                 │
          │ Detect          │
          │ Diagnose        │
          │ Predict         │
          │ Decide          │
          │ Recover         │
          └────────┬────────┘
                   ↓
              MONEY SAVED
                   ↓
                ₹₹₹
```

### The emotional message

**Before ReclaimAI:**

> "We lost the payment."

**After ReclaimAI:**

> "ReclaimAI got it back."

That should be the central visual and product story throughout the entire website.