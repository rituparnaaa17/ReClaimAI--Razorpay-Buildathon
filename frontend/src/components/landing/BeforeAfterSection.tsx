"use client";
import { X, CheckCircle, ArrowRight } from "lucide-react";

const withoutSteps = [
  { text: "Payment fails", icon: X, color: "var(--error)" },
  { text: "Merchant gets notification", icon: X, color: "var(--text-muted)" },
  { text: "Merchant investigates manually", icon: X, color: "var(--text-muted)" },
  { text: "Manual follow-up (days later)", icon: X, color: "var(--text-muted)" },
  { text: "Revenue potentially lost forever", icon: X, color: "var(--error)" },
];

const withSteps = [
  { text: "Payment fails", icon: CheckCircle, color: "var(--text-muted)" },
  { text: "AI detects in milliseconds", icon: CheckCircle, color: "var(--accent-green)" },
  { text: "AI diagnoses root cause", icon: CheckCircle, color: "var(--accent-green)" },
  { text: "ML predicts 91% recovery chance", icon: CheckCircle, color: "var(--accent-green)" },
  { text: "Smart retry executed automatically", icon: CheckCircle, color: "var(--accent-green)" },
  { text: "✓ ₹4,999 recovered", icon: CheckCircle, color: "var(--accent-green)" },
];

function FlowList({ steps, label, accent }: { steps: typeof withoutSteps; label: string; accent: string }) {
  return (
    <div style={{
      flex: 1,
      background: "var(--bg-card)",
      border: `1px solid ${accent}25`,
      borderRadius: "20px",
      padding: "32px",
    }}>
      <div style={{
        display: "inline-block",
        background: `${accent}18`,
        border: `1px solid ${accent}30`,
        borderRadius: "8px",
        padding: "4px 12px",
        marginBottom: "24px",
        fontSize: "0.75rem",
        fontWeight: 600,
        color: accent,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
      }}>
        {label}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {steps.map((step, i) => {
          const Icon = step.icon;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <Icon size={16} color={step.color} style={{ flexShrink: 0 }} />
              <span style={{
                fontSize: "0.9rem",
                color: step.color === "var(--text-muted)" ? "var(--text-secondary)" : step.color,
                fontWeight: step.text.includes("₹") || step.text.includes("91%") ? 700 : 400,
              }}>
                {step.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function BeforeAfterSection() {
  return (
    <section className="section" style={{ background: "var(--bg-secondary)" }}>
      <div className="container">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "64px" }}>
          <h2>Before vs. <span className="text-green">ReclaimAI</span></h2>
          <p style={{ maxWidth: "480px", margin: "16px auto 0" }}>
            See how ReclaimAI transforms a revenue loss event into a recovery opportunity — automatically.
          </p>
        </div>

        {/* Split screen */}
        <div style={{ display: "flex", gap: "24px", alignItems: "stretch" }}>
          <FlowList steps={withoutSteps} label="Without ReclaimAI" accent="var(--error)" />

          {/* Arrow divider */}
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            <div style={{
              width: "48px", height: "48px", borderRadius: "50%",
              background: "var(--accent-green-dim)",
              border: "1px solid var(--border-green)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <ArrowRight size={20} color="var(--accent-green)" />
            </div>
          </div>

          <FlowList steps={withSteps} label="With ReclaimAI" accent="var(--accent-green)" />
        </div>

        {/* Result banner */}
        <div style={{
          marginTop: "40px",
          background: "var(--accent-green-dim)",
          border: "1px solid var(--border-green)",
          borderRadius: "16px",
          padding: "20px 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <div>
            <div style={{ fontSize: "0.78rem", color: "var(--accent-green)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>
              Average Result
            </div>
            <div style={{ fontSize: "1rem", color: "var(--text-primary)", fontWeight: 500 }}>
              66.1% of at-risk revenue recovered — fully autonomously, with zero manual effort
            </div>
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 900, color: "var(--accent-green)", letterSpacing: "-0.03em", flexShrink: 0 }}>
            66.1%
          </div>
        </div>
      </div>
    </section>
  );
}
