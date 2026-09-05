"use client";
import { useEffect, useState, useCallback } from "react";
import {
  CheckCircle, Clock, Brain, AlertTriangle, ShieldCheck, Play, RefreshCw, Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import { getFailureLabel } from "@/lib/utils";

interface AgentLog {
  step: string;
  decision: string;
  reason: string;
  confidence: number;
  timestamp: string;
  result: string;
}

interface CaseLogs {
  case_id: string;
  case_amount: number;
  case_failure: string;
  logs: AgentLog[];
}

const stepIcons: Record<string, React.ElementType> = {
  DETECT: AlertTriangle,
  DIAGNOSE: Brain,
  PREDICT: CheckCircle,
  DECIDE: Play,
  GUARDRAIL: ShieldCheck,
  EXECUTE: Play,
  VERIFY: CheckCircle,
};

const stepColors: Record<string, string> = {
  DETECT: "#3366FF",
  DIAGNOSE: "var(--accent-green-soft)",
  PREDICT: "var(--accent-green)",
  DECIDE: "#805AD5",
  GUARDRAIL: "var(--warning)",
  EXECUTE: "var(--accent-green)",
  VERIFY: "var(--accent-green)",
};

export default function AgentActivityPage() {
  const [data, setData] = useState<CaseLogs[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    try {
      const logs = await api.getAllAgentLogs() as CaseLogs[];
      if (Array.isArray(logs) && logs.length > 0) {
        setData(logs);
        if (!expanded) setExpanded(logs[0].case_id);
      }
    } catch {
      // keep empty state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [expanded]);

  useEffect(() => { load(); }, []);

  const totalSteps = data.reduce((a, d) => a + d.logs.length, 0);
  const successSteps = data.reduce((a, d) => a + d.logs.filter((l) => l.result === "success").length, 0);
  const avgConfidence = totalSteps > 0
    ? Math.round(
        data.reduce((a, d) => a + d.logs.reduce((b, l) => b + (l.confidence ?? 0), 0), 0) / totalSteps * 100
      )
    : 0;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "24px", display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>AI Agent Activity</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Full audit trail of every agent decision</p>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => load(true)}
          disabled={refreshing}
          style={{ gap: "6px" }}
        >
          <RefreshCw size={14} className={refreshing ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "28px" }}>
        {[
          { label: "Cases Processed", value: loading ? "…" : data.length, color: "var(--accent-green)" },
          { label: "Total Agent Steps", value: loading ? "…" : totalSteps, color: "#3366FF" },
          { label: "Successful Actions", value: loading ? "…" : successSteps, color: "var(--accent-green)" },
          { label: "Avg Confidence", value: loading ? "…" : `${avgConfidence}%`, color: "var(--accent-green-soft)" },
        ].map(({ label, value, color }) => (
          <div key={label} className="kpi-card" style={{ padding: "18px 22px" }}>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color, letterSpacing: "-0.02em", lineHeight: 1, marginBottom: "4px" }}>{value}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Timeline */}
      {loading ? (
        <div className="card" style={{ padding: "60px", textAlign: "center", color: "var(--text-muted)" }}>
          <div className="ai-dot" style={{ margin: "0 auto 12px", width: 10, height: 10 }} />
          Loading agent logs…
        </div>
      ) : data.length === 0 ? (
        <div className="card" style={{ padding: "60px", textAlign: "center" }}>
          <Brain size={32} color="var(--text-muted)" style={{ margin: "0 auto 16px", display: "block" }} />
          <div style={{ color: "var(--text-primary)", fontWeight: 600, marginBottom: "8px" }}>No agent activity yet</div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: 400, margin: "0 auto" }}>
            Run the AI Recovery Agent on a recovery case to see a full step-by-step audit trail here.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {data.map((caseData) => (
            <div key={caseData.case_id} className="card" style={{ overflow: "hidden" }}>
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
                    ₹{(caseData.case_amount ?? 0).toLocaleString()}
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
                              fontWeight: 600,
                              background: log.result === "success" ? "var(--accent-green-dim)" : "var(--warning-dim)",
                              padding: "1px 6px", borderRadius: "4px",
                            }}>
                              {log.result}
                            </span>
                          </div>
                          <div style={{ fontSize: "0.82rem", color: "var(--text-primary)", fontWeight: 500, marginBottom: "2px" }}>
                            {log.decision}
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{log.reason}</span>
                            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                              Confidence: {Math.round((log.confidence ?? 0) * 100)}%
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
      )}
    </div>
  );
}
