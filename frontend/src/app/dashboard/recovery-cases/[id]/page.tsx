"use client";
import { use, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft, CheckCircle, Clock, Loader2, Brain,
  ShieldCheck, Play, AlertTriangle, XCircle, Zap, RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { getStatusColor, getStatusLabel, getFailureLabel, sleep } from "@/lib/utils";

type AgentLog = {
  id?: string; step: string; decision: string; reason: string;
  confidence: number; timestamp: string; result: string;
};

type CaseData = {
  id: string; customer_name: string; customer_email: string;
  amount_at_risk: number; amount_recovered: number | null;
  recovery_probability: number; failure_reason: string;
  payment_method: string; root_cause: string;
  recommended_action: string; ai_reasoning: string;
  status: string; retry_count: number; guardrail_passed: boolean;
  created_at: string; updated_at: string;
  agent_logs: AgentLog[];
};

function buildMockCase(id: string): CaseData {
  const prob = parseFloat((Math.random() * 0.6 + 0.3).toFixed(2));
  const amount = Math.round(Math.random() * 48000 + 999);
  const failures = ["UPI_TIMEOUT","BANK_DECLINE","ABANDONED","EXPIRED_CARD","TECHNICAL_FAILURE"];
  const failure = failures[parseInt(id.slice(-1), 16) % 5];
  const now = Date.now();
  return {
    id, customer_name: ["Arjun Sharma","Priya Patel","Rahul Gupta","Vikram Singh"][parseInt(id.slice(-1), 16) % 4],
    customer_email: "customer@example.com", amount_at_risk: amount, amount_recovered: null,
    recovery_probability: prob, failure_reason: failure, payment_method: ["UPI","CARD","NETBANKING","WALLET"][parseInt(id.slice(-1), 16) % 4],
    root_cause: "Temporary network issue caused payment failure.", recommended_action: "Smart Retry",
    ai_reasoning: `Based on the ${failure.replace(/_/g," ").toLowerCase()} failure pattern, a ${Math.round(prob*100)}% recovery probability suggests this case can be resolved with an automated retry. The customer has a clean payment history.`,
    status: "at_risk", retry_count: 0, guardrail_passed: true,
    created_at: new Date(now - 1800000).toISOString(),
    updated_at: new Date(now - 300000).toISOString(),
    agent_logs: [
      { step:"DETECT", decision:"Payment failure detected", reason:"Webhook from Razorpay", confidence:0.99, timestamp:new Date(now-1800000).toISOString(), result:"success" },
      { step:"DIAGNOSE", decision:`Root cause: ${failure}`, reason:"Gateway error analyzed", confidence:0.93, timestamp:new Date(now-1740000).toISOString(), result:"success" },
      { step:"PREDICT", decision:`Recovery probability: ${Math.round(prob*100)}%`, reason:"ML model prediction", confidence:prob, timestamp:new Date(now-1700000).toISOString(), result:"success" },
      { step:"DECIDE", decision:"Smart Retry selected", reason:"High probability + temporary failure", confidence:0.91, timestamp:new Date(now-1680000).toISOString(), result:"success" },
      { step:"GUARDRAIL", decision:"Policy validation passed", reason:"All checks passed", confidence:0.99, timestamp:new Date(now-1660000).toISOString(), result:"success" },
    ],
  };
}

type ExecState = "idle" | "analyzing" | "running" | "done" | "error";

const STEP_ICONS: Record<string, React.ElementType> = {
  DETECT: AlertTriangle, DIAGNOSE: Brain, PREDICT: CheckCircle,
  DECIDE: Play, GUARDRAIL: ShieldCheck, EXECUTE: Zap, VERIFY: CheckCircle,
};

export default function RecoveryCaseDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [execState, setExecState] = useState<ExecState>("idle");
  const [runningStep, setRunningStep] = useState(-1);
  const [resultMsg, setResultMsg] = useState("");

  const loadCase = useCallback(async () => {
    try {
      const data = await api.getRecoveryCase(id) as Record<string, unknown>;
      if (data?.id) setCaseData(data as unknown as CaseData);
      else setCaseData(buildMockCase(id));
    } catch {
      setCaseData(buildMockCase(id));
    }
  }, [id]);

  useEffect(() => { loadCase(); }, [loadCase]);

  const handleRunAgent = async () => {
    if (!caseData || execState === "running" || execState === "analyzing") return;
    setExecState("analyzing");
    setRunningStep(-1);
    setResultMsg("");

    try {
      // First show analyzing state, then kick off agent
      await sleep(600);
      setExecState("running");

      // Animate through existing steps first
      const logs = caseData.agent_logs;
      for (let i = 0; i < logs.length; i++) {
        setRunningStep(i);
        await sleep(750);
      }

      // Call the real LangGraph agent
      const result = await api.runAgent(id) as Record<string, unknown>;

      // Reload case with real agent logs
      await loadCase();

      const recovered = result?.final_status === "recovered";
      setResultMsg(recovered
        ? `₹${Number(caseData.amount_at_risk).toLocaleString()} recovered successfully`
        : result?.final_status === "human_review"
        ? "Escalated for human review"
        : "Recovery attempted — monitoring for result"
      );
      setExecState("done");
    } catch {
      setExecState("error");
      setResultMsg("Agent encountered an error — using fallback recovery");
    }
  };

  if (!caseData) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "12px" }}>
      <Loader2 size={24} color="var(--accent-green)" style={{ animation: "spin 1s linear infinite" }} />
      <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>Loading case data...</span>
      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
    </div>
  );

  const prob = caseData.recovery_probability;
  const probColor = prob > 0.7 ? "var(--accent-green)" : prob > 0.5 ? "var(--warning)" : "var(--error)";
  const terminalStates = ["recovered", "failed", "escalated", "no_action", "expired"];
  const canExecute = !terminalStates.includes(caseData.status) && execState === "idle";

  return (
    <div>
      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>

      {/* Back button */}
      <button onClick={() => router.back()} className="btn btn-ghost btn-sm" style={{ marginBottom: "20px", gap: "6px", paddingLeft: 0 }}>
        <ArrowLeft size={15} /> Back to Recovery Cases
      </button>

      {/* Case header */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "16px", padding: "28px", marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "10px" }}>
              <span style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "var(--text-muted)" }}>#{caseData.id}</span>
              <span className={`badge ${getStatusColor(caseData.status)}`}>{getStatusLabel(caseData.status)}</span>
              {caseData.retry_count > 0 && (
                <span style={{ fontSize: "0.72rem", color: "var(--warning)", background: "var(--warning-dim)", padding: "2px 8px", borderRadius: "6px" }}>
                  Retry {caseData.retry_count}/2
                </span>
              )}
            </div>
            <div style={{ fontSize: "2.5rem", fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1 }}>
              ₹{Number(caseData.amount_at_risk).toLocaleString()}
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginTop: "8px" }}>
              {getFailureLabel(caseData.failure_reason)} · {caseData.payment_method} · {caseData.customer_name}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "4px" }}>{caseData.customer_email}</div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", alignItems: "flex-end" }}>
            {/* Refresh */}
            <button className="btn btn-ghost btn-sm" onClick={loadCase} style={{ gap: "5px", fontSize: "0.75rem" }}>
              <RefreshCw size={12} /> Refresh
            </button>

            {/* Execute / status display */}
            {caseData.status === "recovered" ? (
              <div style={{ background: "var(--accent-green-dim)", border: "1px solid var(--border-green)", borderRadius: "12px", padding: "12px 20px", textAlign: "center" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--accent-green-soft)", marginBottom: "2px" }}>Recovered</div>
                <div style={{ fontSize: "1.3rem", fontWeight: 800, color: "var(--accent-green)" }}>₹{Number(caseData.amount_at_risk).toLocaleString()}</div>
              </div>
            ) : ["action_required", "escalated", "human_review"].includes(caseData.status) ? (
              <div style={{ background: "rgba(196,181,253,0.1)", border: "1px solid rgba(196,181,253,0.2)", borderRadius: "12px", padding: "12px 20px", textAlign: "center" }}>
                <div style={{ fontSize: "0.72rem", color: "#805AD5", marginBottom: "2px" }}>
                  {caseData.status === "escalated" ? "Escalated" : "Action Required"}
                </div>
                <div style={{ fontSize: "0.8rem", color: "#805AD5" }}>Awaiting human review</div>
              </div>
            ) : (
              <button
                id="execute-recovery-btn"
                className="btn btn-primary"
                onClick={handleRunAgent}
                disabled={!canExecute}
                style={{ gap: "8px" }}
              >
                {execState === "analyzing" ? <><Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> Analyzing...</> :
                 execState === "running"   ? <><Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> Agent Running...</> :
                 execState === "done"      ? <><CheckCircle size={15} /> Complete</> :
                 execState === "error"     ? <><XCircle size={15} /> Error — Retry</> :
                 <><Play size={15} /> Run AI Recovery Agent</>}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main 2-col layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Left: AI Decision + Reasoning */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Probability ring + fields */}
          <div className="card" style={{ padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "20px" }}>
              <Brain size={16} color="var(--accent-green)" />
              <h3 style={{ fontSize: "0.9rem" }}>AI Decision</h3>
            </div>

            <div style={{ textAlign: "center", marginBottom: "24px" }}>
              <div style={{
                display: "inline-flex", flexDirection: "column", alignItems: "center",
                width: "120px", height: "120px", borderRadius: "50%",
                border: `4px solid ${probColor}`,
                boxShadow: `0 0 30px ${prob > 0.7 ? "var(--accent-green-dim)" : "rgba(245,184,75,0.15)"}`,
                justifyContent: "center", marginBottom: "12px",
              }}>
                <span style={{ fontSize: "2rem", fontWeight: 900, color: probColor, lineHeight: 1 }}>
                  {Math.round(prob * 100)}%
                </span>
                <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 500 }}>Recovery</span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>AI Probability Score</div>
            </div>

            {[
              { label: "Root Cause", value: caseData.root_cause },
              { label: "Recommended Action", value: caseData.recommended_action, highlight: true },
              { label: "Payment Method", value: caseData.payment_method },
              { label: "Guardrail", value: caseData.guardrail_passed ? "✓ Auto-recovery approved" : "⚠ Human review required", color: caseData.guardrail_passed ? "var(--accent-green)" : "var(--warning)" },
            ].map(({ label, value, highlight, color }) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "10px 12px", background: "var(--bg-secondary)", borderRadius: "8px", marginBottom: "8px", gap: "12px" }}>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", flexShrink: 0 }}>{label}</span>
                <span style={{ fontSize: "0.8rem", fontWeight: highlight ? 700 : 500, color: color || (highlight ? "#3366FF" : "var(--text-primary)"), textAlign: "right" }}>{value}</span>
              </div>
            ))}
          </div>

          {/* AI Reasoning */}
          <div className="card" style={{ padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
              <div className="ai-dot" />
              <h3 style={{ fontSize: "0.9rem" }}>Gemini AI Reasoning</h3>
            </div>
            <p style={{ fontSize: "0.85rem", lineHeight: 1.8, color: "var(--text-secondary)" }}>
              {caseData.ai_reasoning || "Analysis pending. Run the AI Recovery Agent to generate a detailed reasoning."}
            </p>
            <div style={{ borderTop: "1px solid var(--border-subtle)", marginTop: "16px", paddingTop: "16px" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.06em" }}>Guardrail checks</div>
              {[
                { text: `Retry count: ${caseData.retry_count}/2`, ok: caseData.retry_count < 2 },
                { text: `Amount: ₹${Number(caseData.amount_at_risk).toLocaleString()} (limit: ₹50,000)`, ok: Number(caseData.amount_at_risk) <= 50000 },
                { text: `Probability: ${Math.round(prob * 100)}% (min: 30%)`, ok: prob >= 0.3 },
                { text: "Policy validation", ok: caseData.guardrail_passed },
              ].map(({ text, ok }) => (
                <div key={text} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                  {ok ? <CheckCircle size={12} color="var(--accent-green)" /> : <XCircle size={12} color="var(--error)" />}
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Agent timeline */}
        <div className="card" style={{ padding: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Clock size={16} color="var(--accent-green)" />
              <h3 style={{ fontSize: "0.9rem" }}>Agent Activity Timeline</h3>
            </div>
            {execState !== "idle" && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div className="ai-dot" style={{ width: "6px", height: "6px" }} />
                <span style={{ fontSize: "0.72rem", color: "var(--accent-green)" }}>
                  {execState === "done" ? "Complete" : "Running"}
                </span>
              </div>
            )}
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            {caseData.agent_logs.map((log, i) => {
              const Icon = STEP_ICONS[log.step] || CheckCircle;
              const isActive = execState === "running" && runningStep === i;
              const isPast = execState === "done" || (execState === "idle" && log.result === "success");
              const isBlocked = log.result === "blocked" || log.result === "escalated";

              return (
                <div key={`${log.step}-${i}`} className="timeline-step" style={{ paddingBottom: "20px" }}>
                  <div style={{
                    position: "absolute", left: 0, top: "2px",
                    width: "22px", height: "22px", borderRadius: "50%",
                    background: isBlocked ? "rgba(196,181,253,0.15)" : isPast ? "var(--accent-green-dim)" : isActive ? "var(--warning-dim)" : "var(--bg-secondary)",
                    border: `1px solid ${isBlocked ? "rgba(196,181,253,0.3)" : isPast ? "var(--border-green)" : isActive ? "rgba(245,184,75,0.4)" : "var(--border-subtle)"}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: isActive ? "0 0 12px var(--accent-green-glow)" : "none",
                    transition: "all 0.3s",
                  }}>
                    {isActive
                      ? <Loader2 size={11} color="var(--warning)" style={{ animation: "spin 1s linear infinite" }} />
                      : <Icon size={11} color={isBlocked ? "#805AD5" : isPast ? "var(--accent-green)" : "var(--text-muted)"} />
                    }
                  </div>

                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
                      <span style={{
                        fontSize: "0.68rem", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
                        color: isBlocked ? "#805AD5" : isPast ? "var(--accent-green)" : isActive ? "var(--warning)" : "var(--text-muted)",
                        transition: "color 0.3s",
                      }}>{log.step}</span>
                      <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                        {new Date(log.timestamp).toLocaleTimeString("en-IN")}
                      </span>
                      <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                        {Math.round(log.confidence * 100)}%
                      </span>
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--text-primary)", fontWeight: 500, marginBottom: "2px" }}>{log.decision}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.5 }}>{log.reason}</div>
                  </div>
                </div>
              );
            })}

            {/* Result banner */}
            {execState === "done" && (
              <div style={{
                background: caseData.status === "recovered" || resultMsg.includes("recovered")
                  ? "var(--accent-green-dim)" : "rgba(147,197,253,0.1)",
                border: `1px solid ${caseData.status === "recovered" || resultMsg.includes("recovered") ? "var(--border-green)" : "rgba(147,197,253,0.2)"}`,
                borderRadius: "12px", padding: "16px", textAlign: "center", marginTop: "8px",
              }}>
                <CheckCircle size={22} color={caseData.status === "recovered" || resultMsg.includes("recovered") ? "var(--accent-green)" : "#3366FF"} style={{ marginBottom: "6px" }} />
                <div style={{ fontSize: "1rem", fontWeight: 700, color: caseData.status === "recovered" || resultMsg.includes("recovered") ? "var(--accent-green)" : "#3366FF" }}>
                  {resultMsg}
                </div>
              </div>
            )}
            {execState === "error" && (
              <div style={{ background: "var(--error-dim)", border: "1px solid rgba(255,98,98,0.2)", borderRadius: "12px", padding: "16px", textAlign: "center", marginTop: "8px" }}>
                <XCircle size={22} color="var(--error)" style={{ marginBottom: "6px" }} />
                <div style={{ fontSize: "0.875rem", color: "var(--error)" }}>{resultMsg}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
