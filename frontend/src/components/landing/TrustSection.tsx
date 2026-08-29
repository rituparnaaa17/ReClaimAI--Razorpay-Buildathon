"use client";
import { ShieldCheck, Lock, Eye, AlertTriangle } from "lucide-react";

const controls = [
  { icon: AlertTriangle, title: "Max Retry Limit", value: "2 retries", description: "AI will never attempt more than 2 automatic retries per transaction." },
  { icon: Lock, title: "High-Value Threshold", value: "> ₹50,000", description: "Transactions above this threshold require human approval before action." },
  { icon: ShieldCheck, title: "Probability Threshold", value: "> 40%", description: "Only cases with sufficient recovery probability receive automated action." },
  { icon: Eye, title: "Full Audit Trail", value: "Every action", description: "Every AI decision, reason, and confidence score is logged for review." },
];

export default function TrustSection() {
  return (
    <section className="section" id="insights" style={{ background: "var(--bg-secondary)" }}>
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "80px", alignItems: "center" }}>
          {/* Left */}
          <div>
            <div style={{
              display: "inline-flex", alignItems: "center", gap: "8px",
              background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
              borderRadius: "20px", padding: "5px 16px", marginBottom: "24px",
            }}>
              <ShieldCheck size={14} color="var(--accent-green)" />
              <span style={{ fontSize: "0.78rem", color: "var(--accent-green)", fontWeight: 600 }}>Trust & Safety</span>
            </div>

            <h2 style={{ marginBottom: "20px" }}>
              AI that acts<br /><span className="text-green">within boundaries.</span>
            </h2>

            <p style={{ fontSize: "1rem", lineHeight: 1.7, marginBottom: "32px" }}>
              ReclaimAI is built for financial environments where every action matters. Before any recovery action is taken, it passes through a strict guardrail layer — ensuring the AI never acts beyond its defined boundaries.
            </p>

            {/* Policy flow */}
            <div style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "16px",
              padding: "24px",
            }}>
              {["AI Decision", "Policy Check", "Guardrail Validation", "Approved ✓", "Action Executed"].map((step, i, arr) => (
                <div key={step} style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: "12px",
                    padding: "8px 0",
                  }}>
                    <div style={{
                      width: "28px", height: "28px", borderRadius: "8px",
                      background: step.includes("✓") || step === "Action Executed" ? "var(--accent-green-dim)" : "var(--bg-secondary)",
                      border: `1px solid ${step.includes("✓") || step === "Action Executed" ? "var(--border-green)" : "var(--border-subtle)"}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: "0.7rem", fontWeight: 700,
                      color: step.includes("✓") || step === "Action Executed" ? "var(--accent-green)" : "var(--text-muted)",
                    }}>
                      {i + 1}
                    </div>
                    <span style={{
                      fontSize: "0.875rem",
                      color: step.includes("✓") ? "var(--accent-green)" : "var(--text-secondary)",
                      fontWeight: step.includes("✓") ? 700 : 400,
                    }}>
                      {step}
                    </span>
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ width: "1px", height: "12px", background: "var(--border-subtle)", marginLeft: "14px" }} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right: Controls */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {controls.map(({ icon: Icon, title, value, description }) => (
              <div key={title} className="card" style={{ padding: "20px 24px", display: "flex", gap: "16px", alignItems: "flex-start" }}>
                <div style={{
                  width: "40px", height: "40px", borderRadius: "10px",
                  background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
                  display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                }}>
                  <Icon size={18} color="var(--accent-green)" />
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                    <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)" }}>{title}</span>
                    <span style={{
                      background: "var(--accent-green-dim)", color: "var(--accent-green)",
                      border: "1px solid var(--border-green)", borderRadius: "6px",
                      padding: "2px 8px", fontSize: "0.7rem", fontWeight: 700,
                    }}>
                      {value}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.8rem", lineHeight: 1.5, color: "var(--text-muted)" }}>{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
