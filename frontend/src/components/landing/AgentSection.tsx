"use client";
import { useState } from "react";
import { Search, Activity, TrendingUp, BrainCircuit, RefreshCw, ShieldCheck, CheckCircle } from "lucide-react";

const steps = [
  {
    num: "01", key: "detect",
    icon: Search,
    title: "Detect",
    description: "ReclaimAI monitors every payment event in real-time. The moment a payment fails or a checkout is abandoned, it's flagged immediately for analysis.",
    detail: "Monitors payment webhooks, subscription events, and checkout sessions 24/7.",
  },
  {
    num: "02", key: "diagnose",
    icon: Activity,
    title: "Diagnose",
    description: "The AI analyzes the failure — UPI timeout, bank decline, insufficient balance, expired card, or technical glitch — to find the true root cause.",
    detail: "Combines gateway error codes, payment method metadata, and transaction history.",
  },
  {
    num: "03", key: "predict",
    icon: TrendingUp,
    title: "Predict",
    description: "An ML model calculates the exact probability this transaction can be recovered, based on amount, customer history, failure type, and retry count.",
    detail: "XGBoost model trained on thousands of historical recovery outcomes.",
  },
  {
    num: "04", key: "decide",
    icon: BrainCircuit,
    title: "Decide",
    description: "Gemini AI selects the optimal recovery strategy — smart retry, personalized reminder, alternative payment method, or human escalation.",
    detail: "Decision considers merchant policies, customer value, and probability threshold.",
  },
  {
    num: "05", key: "recover",
    icon: RefreshCw,
    title: "Recover",
    description: "The LangGraph agent executes the chosen recovery action — retrying the payment via Razorpay, sending a customer notification, or updating payment details.",
    detail: "All actions pass through guardrail checks before execution.",
  },
  {
    num: "06", key: "verify",
    icon: CheckCircle,
    title: "Verify",
    description: "The system verifies the outcome, updates the recovery case status, logs every decision in the audit trail, and reflects recovered revenue in the dashboard.",
    detail: "Full traceability: every AI decision is logged with reason and confidence score.",
  },
];

export default function AgentSection() {
  const [activeStep, setActiveStep] = useState<string | null>(null);

  return (
    <section className="section" id="how-it-works" style={{ position: "relative", overflow: "hidden" }}>
      {/* Background */}
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)",
        width: "600px", height: "600px",
        background: "radial-gradient(circle, rgba(25,216,121,0.04) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div className="container" style={{ position: "relative" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "64px" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
            borderRadius: "20px", padding: "5px 16px", marginBottom: "20px",
          }}>
            <ShieldCheck size={14} color="var(--accent-green)" />
            <span style={{ fontSize: "0.78rem", color: "var(--accent-green)", fontWeight: 600 }}>
              AI Agent
            </span>
          </div>
          <h2>
            An AI agent that doesn&apos;t just detect<br />
            the problem. <span className="text-green">It closes the loop.</span>
          </h2>
          <p style={{ maxWidth: "520px", margin: "16px auto 0" }}>
            Six stages, fully automated. The ReclaimAI agent orchestrates every step from failure detection to verified revenue recovery.
          </p>
        </div>

        {/* Steps grid */}
        <div className="responsive-grid-1" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "2px", position: "relative" }}>
          {steps.map((step, i) => {
            const Icon = step.icon;
            const isActive = activeStep === step.key;
            return (
              <div
                key={step.key}
                onMouseEnter={() => setActiveStep(step.key)}
                onMouseLeave={() => setActiveStep(null)}
                style={{
                  background: isActive ? "var(--bg-card-hover)" : "var(--bg-card)",
                  border: `1px solid ${isActive ? "var(--border-green)" : "var(--border-subtle)"}`,
                  borderRadius: "16px",
                  padding: "28px",
                  cursor: "default",
                  transition: "all 0.25s ease",
                  margin: "1px",
                  boxShadow: isActive ? "0 0 30px var(--accent-green-dim)" : "none",
                }}
              >
                {/* Number + Icon */}
                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
                  <span style={{
                    fontSize: "0.7rem", fontWeight: 700,
                    color: isActive ? "var(--accent-green)" : "var(--text-muted)",
                    letterSpacing: "0.08em", transition: "color 0.2s",
                  }}>
                    {step.num}
                  </span>
                  <div style={{
                    width: "36px", height: "36px", borderRadius: "10px",
                    background: isActive ? "var(--accent-green-dim)" : "var(--bg-secondary)",
                    border: `1px solid ${isActive ? "var(--border-green)" : "var(--border-subtle)"}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    transition: "all 0.2s",
                  }}>
                    <Icon size={16} color={isActive ? "var(--accent-green)" : "var(--text-muted)"} />
                  </div>
                </div>

                <h3 style={{ fontSize: "1.05rem", marginBottom: "10px", transition: "color 0.2s", color: isActive ? "var(--text-primary)" : "var(--text-primary)" }}>
                  {step.title}
                </h3>
                <p style={{ fontSize: "0.83rem", lineHeight: 1.6, color: "var(--text-muted)" }}>
                  {step.description}
                </p>

                {/* Expanded detail */}
                <div style={{
                  marginTop: "14px",
                  maxHeight: isActive ? "80px" : "0",
                  overflow: "hidden",
                  transition: "max-height 0.3s ease",
                }}>
                  <div style={{
                    borderTop: "1px solid var(--border-green)",
                    paddingTop: "12px",
                    fontSize: "0.78rem",
                    color: "var(--accent-green-soft)",
                    lineHeight: 1.5,
                  }}>
                    {step.detail}
                  </div>
                </div>

                {/* Connector arrow (except last column) */}
                {i % 3 !== 2 && (
                  <div style={{
                    position: "absolute",
                    right: "-14px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    fontSize: "1rem",
                    color: "var(--border-subtle)",
                    zIndex: 1,
                  }} />
                )}
              </div>
            );
          })}
        </div>

        {/* Flow connector */}
        <div style={{
          marginTop: "40px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0",
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          padding: "16px 24px",
          overflowX: "auto",
        }}>
          {steps.map((step, i) => (
            <div key={step.key} style={{ display: "flex", alignItems: "center" }}>
              <span style={{
                fontSize: "0.78rem",
                fontWeight: 600,
                color: "var(--accent-green)",
                whiteSpace: "nowrap",
              }}>
                {step.title}
              </span>
              {i < steps.length - 1 && (
                <span style={{
                  margin: "0 12px",
                  color: "var(--border-subtle)",
                  fontSize: "0.9rem",
                }}>→</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
