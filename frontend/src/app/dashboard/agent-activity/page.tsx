"use client";
import { useEffect, useState } from "react";
import { CheckCircle, Clock, Loader2, Brain, AlertTriangle, ShieldCheck, Play } from "lucide-react";
import { api } from "@/lib/api";
import { getFailureLabel } from "@/lib/utils";

const MOCK_LOGS = [
  {
    case_id: "RC_10001", case_amount: 4999, case_failure: "UPI_TIMEOUT",
    logs: [
      { step: "DETECT", decision: "Payment failure detected", reason: "Webhook received from Razorpay", confidence: 0.99, timestamp: new Date(Date.now() - 1000 * 60 * 28).toISOString(), result: "success" },
      { step: "DIAGNOSE", decision: "UPI Timeout identified", reason: "Error code: UPI_TIMEOUT", confidence: 0.94, timestamp: new Date(Date.now() - 1000 * 60 * 27).toISOString(), result: "success" },
      { step: "PREDICT", decision: "Recovery probability: 91%", reason: "ML model prediction", confidence: 0.91, timestamp: new Date(Date.now() - 1000 * 60 * 27).toISOString(), result: "success" },
      { step: "DECIDE", decision: "Smart Retry selected", reason: "High recovery probability", confidence: 0.91, timestamp: new Date(Date.now() - 1000 * 60 * 26).toISOString(), result: "success" },
      { step: "GUARDRAIL", decision: "Policy validation passed", reason: "Retry count: 0/2. Amount within limit.", confidence: 0.99, timestamp: new Date(Date.now() - 1000 * 60 * 26).toISOString(), result: "success" },
      { step: "EXECUTE", decision: "Smart retry initiated", reason: "Razorpay test API called", confidence: 0.95, timestamp: new Date(Date.now() - 1000 * 60 * 24).toISOString(), result: "success" },
      { step: "VERIFY", decision: "₹4,999 recovered successfully", reason: "Payment status: captured", confidence: 0.99, timestamp: new Date(Date.now() - 1000 * 60 * 23).toISOString(), result: "success" },
    ],
  },
  {
    case_id: "RC_10002", case_amount: 8200, case_failure: "BANK_DECLINE",
    logs: [
      { step: "DETECT", decision: "Payment failure detected", reason: "Webhook received from Razorpay", confidence: 0.99, timestamp: new Date(Date.now() - 1000 * 60 * 18).toISOString(), result: "success" },
      { step: "DIAGNOSE", decision: "Bank decline identified", reason: "Error code: BANK_DECLINE", confidence: 0.88, timestamp: new Date(Date.now() - 1000 * 60 * 17).toISOString(), result: "success" },
      { step: "PREDICT", decision: "Recovery probability: 68%", reason: "ML model prediction", confidence: 0.68, timestamp: new Date(Date.now() - 1000 * 60 * 17).toISOString(), result: "success" },
      { step: "DECIDE", decision: "Alternative payment method suggested", reason: "Bank decline — retry unlikely to succeed", confidence: 0.78, timestamp: new Date(Date.now() - 1000 * 60 * 16).toISOString(), result: "success" },
      { step: "GUARDRAIL", decision: "Policy validation passed", reason: "Within automatic recovery limits.", confidence: 0.99, timestamp: new Date(Date.now() - 1000 * 60 * 16).toISOString(), result: "success" },
      { step: "EXECUTE", decision: "Customer notified with alt. payment link", reason: "Personalized email sent via Resend", confidence: 0.88, timestamp: new Date(Date.now() - 1000 * 60 * 14).toISOString(), result: "pending" },
    ],
  },
];

const stepIcons: Record<string, React.ElementType> = {
  DETECT: AlertTriangle, DIAGNOSE: Brain, PREDICT: CheckCircle,
  DECIDE: Play, GUARDRAIL: ShieldCheck, EXECUTE: Play, VERIFY: CheckCircle,
};

const stepColors: Record<string, string> = {
  DETECT: "#3366FF", DIAGNOSE: "var(--accent-green-soft)",
  PREDICT: "var(--accent-green)", DECIDE: "#805AD5",
  GUARDRAIL: "var(--warning)", EXECUTE: "var(--accent-green)",
  VERIFY: "var(--accent-green)",
};

export default function AgentActivityPage() {
  const [data, setData] = useState(MOCK_LOGS);
  const [expanded, setExpanded] = useState<string | null>("RC_10001");

  useEffect(() => {
    api.getAllAgentLogs()
      .then((logs) => { if (Array.isArray(logs) && logs.length) setData(logs as typeof MOCK_LOGS); })
      .catch(() => {});
  }, []);

  const totalSteps = data.reduce((acc, d) => acc + d.logs.length, 0);
  const successSteps = data.reduce((acc, d) => acc + d.logs.filter((l) => l.result === "success").length, 0);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>AI Agent Activity</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Full audit trail of every agent decision</p>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "28px" }}>
        {[
          { label: "Cases Processed", value: data.length, color: "var(--accent-green)" },
          { label: "Total Agent Steps", value: totalSteps, color: "#3366FF" },
          { label: "Successful Actions", value: successSteps, color: "var(--accent-green)" },
          { label: "Avg Confidence", value: "93%", color: "var(--accent-green-soft)" },
        ].map(({ label, value, color }) => (
          <div key={label} className="kpi-card" style={{ padding: "18px 22px" }}>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color, letterSpacing: "-0.02em", lineHeight: 1, marginBottom: "4px" }}>{value}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {data.map((caseData) => (
          <div key={caseData.case_id} className="card" style={{ overflow: "hidden" }}>
            {/* Case Header */}
            <button
              onClick={() => setExpanded(expanded === caseData.case_id ? null : caseData.case_id)}
              style={{
                width: "100%", padding: "18px 24px",
                display: "flex", alignItems: "center", justifyContent: "space-between",
                background: "transparent", border: "none", cursor: "pointer", textAlign: "left",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div className="ai-dot" style={{ width: "6px", height: "6px" }} />
                  <span style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "var(--accent-green-soft)" }}>
                    {caseData.case_id}
                  </span>
                </div>
                <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  ₹{caseData.case_amount.toLocaleString()}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {getFailureLabel(caseData.case_failure)}
                </span>
                <span style={{
                  fontSize: "0.72rem", fontWeight: 600,
                  background: "var(--accent-green-dim)", color: "var(--accent-green)",
                  border: "1px solid var(--border-green)", borderRadius: "6px", padding: "2px 8px",
                }}>
                  {caseData.logs.length} steps
                </span>
              </div>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                {expanded === caseData.case_id ? "▲" : "▼"}
              </span>
            </button>

            {/* Steps */}
            {expanded === caseData.case_id && (
              <div style={{ padding: "0 24px 24px", borderTop: "1px solid var(--border-subtle)" }}>
                <div style={{ paddingTop: "20px", display: "flex", flexDirection: "column", gap: "0" }}>
                  {caseData.logs.map((log, i) => {
                    const Icon = stepIcons[log.step] || CheckCircle;
                    const color = stepColors[log.step] || "var(--accent-green)";
                    return (
                      <div key={i} className="timeline-step" style={{ paddingBottom: "18px" }}>
                        <div style={{
                          position: "absolute", left: 0, top: "3px",
                          width: "22px", height: "22px", borderRadius: "50%",
                          background: log.result === "success" ? "var(--accent-green-dim)" : "var(--warning-dim)",
                          border: `1px solid ${log.result === "success" ? "var(--border-green)" : "rgba(245,184,75,0.3)"}`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                        }}>
                          <Icon size={11} color={color} />
                        </div>
                        <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "3px" }}>
                          <span style={{
                            fontSize: "0.68rem", fontWeight: 700, letterSpacing: "0.08em",
                            textTransform: "uppercase", color,
                          }}>
                            {log.step}
                          </span>
                          <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                            {new Date(log.timestamp).toLocaleTimeString("en-IN")}
                          </span>
                          <span style={{
                            marginLeft: "auto", fontSize: "0.65rem",
                            color: log.result === "success" ? "var(--accent-green)" : "var(--warning)",
                            fontWeight: 600, background: log.result === "success" ? "var(--accent-green-dim)" : "var(--warning-dim)",
                            padding: "1px 6px", borderRadius: "4px",
                          }}>
                            {log.result}
                          </span>
                        </div>
                        <div style={{ fontSize: "0.82rem", color: "var(--text-primary)", fontWeight: 500, marginBottom: "2px" }}>{log.decision}</div>
                        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{log.reason}</span>
                          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                            Confidence: {Math.round(log.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
