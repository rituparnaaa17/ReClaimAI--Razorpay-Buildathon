"use client";
import { use, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft, CheckCircle, Clock, Loader2, Brain,
  ShieldCheck, Play, AlertTriangle, XCircle, Zap, RefreshCw,
  UserCheck, ExternalLink, AlertOctagon,
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
  guardrail_reason?: string;
  razorpay_payment_link_id?: string;
  razorpay_payment_id?: string;
  human_review_note?: string;
  created_at: string; updated_at: string;
  agent_logs: AgentLog[];
};

type ExecState = "idle" | "analyzing" | "running" | "done" | "error";

const STEP_ICONS: Record<string, React.ElementType> = {
  DETECT: AlertTriangle, DIAGNOSE: Brain, PREDICT: CheckCircle,
  DECIDE: Play, GUARDRAIL: ShieldCheck, EXECUTE: Zap, VERIFY: CheckCircle,
};

const HUMAN_STATES = new Set(["action_required", "escalated", "human_review"]);
const TERMINAL_STATES = new Set(["recovered", "failed", "no_action", "expired"]);

export default function RecoveryCaseDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [execState, setExecState] = useState<ExecState>("idle");
  const [runningStep, setRunningStep] = useState(-1);
  const [resultMsg, setResultMsg] = useState("");
  const [notFound, setNotFound] = useState(false);

  // Human review state
  const [reviewNote, setReviewNote] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [reviewResult, setReviewResult] = useState("");

  const loadCase = useCallback(async () => {
    try {
      const data = await api.getRecoveryCase(id) as Record<string, unknown>;
      if (data?.id) setCaseData(data as unknown as CaseData);
      else setNotFound(true);
    } catch {
      setNotFound(true);
    }
  }, [id]);

  useEffect(() => { loadCase(); }, [loadCase]);

  // ── Agent run ────────────────────────────────────────────────────────────────
  const handleRunAgent = async () => {
    if (!caseData || execState === "running" || execState === "analyzing") return;
    setExecState("analyzing");
    setRunningStep(-1);
    setResultMsg("");

    try {
      await sleep(600);
      setExecState("running");
      for (let i = 0; i < caseData.agent_logs.length; i++) {
        setRunningStep(i);
        await sleep(700);
      }
      const result = await api.runAgent(id) as Record<string, unknown>;
      await loadCase();
      const finalStatus = result?.final_status as string;
      const amtRecovered = result?.amount_recovered as number | null;
      setResultMsg(
        finalStatus === "recovered"
          ? `₹${amtRecovered ? amtRecovered.toLocaleString() : Number(caseData.amount_at_risk).toLocaleString()} recovered successfully`
          : finalStatus === "escalated" || finalStatus === "action_required"
          ? "Escalated — awaiting human review"
          : finalStatus === "no_action"
          ? "No action — probability below threshold"
          : finalStatus === "verifying"
          ? "Recovery attempted — awaiting Razorpay confirmation"
          : "Recovery attempted — monitoring result"
      );
      setExecState("done");
    } catch (err: unknown) {
      setExecState("error");
      setResultMsg(`Agent error: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  };

  // ── Human review ────────────────────────────────────────────────────────────
  const handleHumanReview = async (decision: "approve" | "reject" | "escalate") => {
    if (!caseData || reviewing) return;
    setReviewing(true);
    setReviewResult("");
    try {
      const res = await api.humanReview(id, decision, reviewNote || undefined) as Record<string, unknown>;
      await loadCase();
      setReviewResult(
        decision === "approve"
          ? "✓ Approved — agent executed recovery action"
          : decision === "reject"
          ? "✗ Rejected — case closed with no action"
          : "↑ Escalated for senior review"
      );
    } catch (err: unknown) {
      setReviewResult(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setReviewing(false);
    }
  };

  if (notFound) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "12px" }}>
      <XCircle size={40} color="var(--error)" />
      <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>Case not found</span>
      <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Case ID &ldquo;{id}&rdquo; does not exist in the database.</span>
      <button className="btn btn-ghost btn-sm" onClick={() => router.back()} style={{ marginTop: "8px" }}>← Go back</button>
    </div>
  );

  if (!caseData) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "12px" }}>
      <Loader2 size={24} color="var(--accent-green)" style={{ animation: "spin 1s linear infinite" }} />
      <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>Loading case data…</span>
      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
    </div>
  );

  const prob = caseData.recovery_probability ?? 0;
  const probColor = prob > 0.7 ? "var(--accent-green)" : prob > 0.5 ? "var(--warning)" : "var(--error)";
  const isHumanReview = HUMAN_STATES.has(caseData.status);
  const isTerminal = TERMINAL_STATES.has(caseData.status) || caseData.status === "escalated";
  const canExecute = !isTerminal && !isHumanReview && execState === "idle";
  const hasPaymentLink = !!caseData.razorpay_payment_link_id;

  return (
    <div>
      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>

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
              {isHumanReview && (
                <span style={{ fontSize: "0.72rem", color: "#805AD5", background: "rgba(196,181,253,0.15)", border: "1px solid rgba(196,181,253,0.3)", padding: "2px 8px", borderRadius: "6px", fontWeight: 600 }}>
                  ⚠ Awaiting Human Review
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

            {/* Agent-created payment link indicator */}
            {hasPaymentLink && (
              <div style={{
                display: "inline-flex", alignItems: "center", gap: "6px", marginTop: "12px",
                background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
                borderRadius: "8px", padding: "5px 12px",
              }}>
                <div className="ai-dot" style={{ width: 6, height: 6 }} />
                <span style={{ fontSize: "0.75rem", color: "var(--accent-green)", fontWeight: 600 }}>
                  Agent created payment link: {caseData.razorpay_payment_link_id}
                </span>
              </div>
            )}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", alignItems: "flex-end" }}>
            <button className="btn btn-ghost btn-sm" onClick={loadCase} style={{ gap: "5px", fontSize: "0.75rem" }}>
              <RefreshCw size={12} /> Refresh
            </button>

            {caseData.status === "recovered" ? (
              <div style={{ background: "var(--accent-green-dim)", border: "1px solid var(--border-green)", borderRadius: "12px", padding: "12px 20px", textAlign: "center" }}>
                <div style={{ fontSize: "0.72rem", color: "var(--accent-green-soft)", marginBottom: "2px" }}>Recovered</div>
                <div style={{ fontSize: "1.3rem", fontWeight: 800, color: "var(--accent-green)" }}>
                  ₹{caseData.amount_recovered ? Number(caseData.amount_recovered).toLocaleString() : Number(caseData.amount_at_risk).toLocaleString()}
                </div>
              </div>
            ) : isHumanReview ? (
              <div style={{ background: "rgba(196,181,253,0.08)", border: "1px solid rgba(196,181,253,0.25)", borderRadius: "12px", padding: "10px 16px", textAlign: "center" }}>
                <div style={{ fontSize: "0.72rem", color: "#805AD5", marginBottom: "2px" }}>Human Review Required</div>
                <div style={{ fontSize: "0.78rem", color: "#805AD5" }}>See review panel below</div>
              </div>
            ) : (
              <button
                id="execute-recovery-btn"
                className="btn btn-primary"
                onClick={handleRunAgent}
                disabled={!canExecute}
                style={{ gap: "8px" }}
              >
                {execState === "analyzing" ? <><Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> Analyzing…</> :
                 execState === "running"   ? <><Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> Agent Running…</> :
                 execState === "done"      ? <><CheckCircle size={15} /> Complete</> :
                 execState === "error"     ? <><XCircle size={15} /> Error — Retry</> :
                 <><Play size={15} /> Run AI Recovery Agent</>}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Human Review Panel (only when action_required / escalated) ── */}
      {isHumanReview && (
        <div style={{
          background: "rgba(196,181,253,0.06)",
          border: "1px solid rgba(196,181,253,0.3)",
          borderRadius: "16px",
          padding: "28px",
          marginBottom: "20px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <AlertOctagon size={20} color="#805AD5" />
            <div>
              <h3 style={{ fontSize: "1rem", color: "#805AD5", marginBottom: "2px" }}>Human Review Required</h3>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                {caseData.status === "escalated"
                  ? "This case was escalated by the AI agent (retry limit or guardrail rule). Review and decide."
                  : `This case exceeds the ₹50,000 auto-recovery limit (₹${Number(caseData.amount_at_risk).toLocaleString()}). Manual approval required.`}
              </p>
            </div>
          </div>

          {caseData.guardrail_reason && (
            <div style={{ background: "var(--bg-secondary)", borderRadius: "8px", padding: "10px 14px", marginBottom: "16px", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              <strong>Agent reason:</strong> {caseData.guardrail_reason}
            </div>
          )}

          <div style={{ marginBottom: "16px" }}>
            <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
              Reviewer note (optional)
            </label>
            <textarea
              className="input"
              rows={2}
              placeholder="Add a review note, e.g. 'Verified with customer — safe to proceed'"
              value={reviewNote}
              onChange={(e) => setReviewNote(e.target.value)}
              style={{ resize: "vertical", width: "100%" }}
            />
          </div>

          {reviewResult && (
            <div style={{
              padding: "10px 14px", marginBottom: "14px", borderRadius: "8px", fontSize: "0.85rem", fontWeight: 600,
              background: reviewResult.startsWith("✓") ? "var(--accent-green-dim)" : reviewResult.startsWith("✗") ? "rgba(255,98,98,0.1)" : "rgba(196,181,253,0.1)",
              color: reviewResult.startsWith("✓") ? "var(--accent-green)" : reviewResult.startsWith("✗") ? "var(--error)" : "#805AD5",
              border: `1px solid ${reviewResult.startsWith("✓") ? "var(--border-green)" : reviewResult.startsWith("✗") ? "rgba(255,98,98,0.2)" : "rgba(196,181,253,0.3)"}`,
            }}>
              {reviewResult}
            </div>
          )}

          <div style={{ display: "flex", gap: "10px" }}>
            <button
              className="btn btn-primary"
              onClick={() => handleHumanReview("approve")}
              disabled={reviewing}
              style={{ gap: "6px", flex: 1 }}
            >
              <UserCheck size={15} />
              {reviewing ? "Processing…" : "✓ Approve & Execute"}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => handleHumanReview("escalate")}
              disabled={reviewing}
              style={{ gap: "6px" }}
            >
              ↑ Re-escalate
            </button>
            <button
              onClick={() => handleHumanReview("reject")}
              disabled={reviewing}
              style={{
                padding: "8px 16px", borderRadius: "8px", cursor: "pointer",
                background: "rgba(255,98,98,0.1)", border: "1px solid rgba(255,98,98,0.2)",
                color: "var(--error)", fontSize: "0.85rem", fontWeight: 600,
              }}
            >
              ✗ Reject
            </button>
          </div>
        </div>
      )}

      {/* Main 2-col layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Left: AI Decision + Reasoning */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
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
              { label: "Root Cause", value: caseData.root_cause || "Pending diagnosis" },
              { label: "Recommended Action", value: caseData.recommended_action || "—", highlight: true },
              { label: "Payment Method", value: caseData.payment_method || "—" },
              {
                label: "Guardrail",
                value: caseData.guardrail_passed ? "✓ Auto-recovery approved" : "⚠ Human review required",
                color: caseData.guardrail_passed ? "var(--accent-green)" : "var(--warning)",
              },
              ...(hasPaymentLink ? [{
                label: "Payment Link",
                value: caseData.razorpay_payment_link_id!,
                isLink: true,
              }] : []),
            ].map(({ label, value, highlight, color, isLink }: { label: string; value: string; highlight?: boolean; color?: string; isLink?: boolean }) => (
              <div key={label} style={{
                display: "flex", justifyContent: "space-between", alignItems: "flex-start",
                padding: "10px 12px", background: "var(--bg-secondary)", borderRadius: "8px", marginBottom: "8px", gap: "12px",
              }}>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", flexShrink: 0 }}>{label}</span>
                {isLink ? (
                  <a
                    href={`https://dashboard.razorpay.com/app/payment-links/${value}`}
                    target="_blank" rel="noreferrer"
                    style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "var(--accent-green)", display: "flex", alignItems: "center", gap: "4px" }}
                  >
                    {value.slice(0, 24)}… <ExternalLink size={11} />
                  </a>
                ) : (
                  <span style={{ fontSize: "0.8rem", fontWeight: highlight ? 700 : 500, color: color || (highlight ? "#3366FF" : "var(--text-primary)"), textAlign: "right" }}>
                    {value}
                  </span>
                )}
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
            {caseData.agent_logs.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                {isHumanReview
                  ? "Agent stopped at GUARDRAIL — awaiting human decision above."
                  : "No agent steps yet. Run the AI Recovery Agent to begin."}
              </div>
            ) : caseData.agent_logs.map((log, i) => {
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
                        {Math.round((log.confidence ?? 0) * 100)}%
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
                background: resultMsg.includes("recovered") ? "var(--accent-green-dim)" : "rgba(147,197,253,0.1)",
                border: `1px solid ${resultMsg.includes("recovered") ? "var(--border-green)" : "rgba(147,197,253,0.2)"}`,
                borderRadius: "12px", padding: "16px", textAlign: "center", marginTop: "8px",
              }}>
                <CheckCircle size={22} color={resultMsg.includes("recovered") ? "var(--accent-green)" : "#3366FF"} style={{ marginBottom: "6px" }} />
                <div style={{ fontSize: "1rem", fontWeight: 700, color: resultMsg.includes("recovered") ? "var(--accent-green)" : "#3366FF" }}>
                  {resultMsg}
                </div>
              </div>
            )}
            {execState === "error" && (
              <div style={{ background: "var(--error-dim, rgba(255,98,98,0.1))", border: "1px solid rgba(255,98,98,0.2)", borderRadius: "12px", padding: "16px", textAlign: "center", marginTop: "8px" }}>
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
