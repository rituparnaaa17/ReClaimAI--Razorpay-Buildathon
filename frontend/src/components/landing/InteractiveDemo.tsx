"use client";
import { useState } from "react";
import { Play, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { sleep } from "@/lib/utils";

type DemoState = "idle" | "analyzing" | "policy" | "retrying" | "recovered" | "failed";

const demoSteps: { state: DemoState; label: string; duration: number }[] = [
  { state: "analyzing", label: "Analyzing transaction failure signature...", duration: 1000 },
  { state: "policy", label: "Recovery policy validation passed ✓", duration: 800 },
  { state: "retrying", label: "Initiating smart retry via Razorpay API...", duration: 1200 },
  { state: "recovered", label: "✓ ₹4,999 Recovered Successfully", duration: 0 },
];

export default function InteractiveDemo() {
  const [demoState, setDemoState] = useState<DemoState>("idle");
  const [logs, setLogs] = useState<string[]>([]);

  const runDemo = async () => {
    if (demoState !== "idle" && demoState !== "recovered" && demoState !== "failed") return;
    setDemoState("analyzing");
    setLogs([]);

    for (let i = 0; i < demoSteps.length; i++) {
      const step = demoSteps[i];
      setDemoState(step.state);
      setLogs((prev) => [...prev, step.label]);
      if (step.duration > 0) await sleep(step.duration);
    }
  };

  const isRunning = !["idle", "recovered", "failed"].includes(demoState);
  const isRecovered = demoState === "recovered";

  return (
    <section className="section" id="recovery" style={{ background: "var(--bg-secondary)", borderTop: "1px solid var(--border-subtle)" }}>
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: "48px" }}>
          <h2>Interactive Recovery Simulator</h2>
          <p style={{ maxWidth: "520px", margin: "12px auto 0", color: "var(--text-muted)", fontSize: "0.95rem" }}>
            Click Run Recovery to see how ReclaimAI analyzes error codes and performs automated payment retries.
          </p>
        </div>

        <div className="responsive-grid-1" style={{
          maxWidth: "840px", margin: "0 auto",
          display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px",
        }}>
          {/* Left Side: Simulation Card */}
          <div style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "28px",
            boxShadow: "0 4px 6px -1px rgba(0,0,0,0.02)",
          }}>
            <div style={{ marginBottom: "20px" }}>
              <div style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "var(--error-dim)",
                borderRadius: "4px",
                padding: "2px 8px",
                marginBottom: "12px",
              }}>
                <AlertCircle size={12} color="var(--error)" />
                <span style={{ fontSize: "0.7rem", color: "var(--error)", fontWeight: 600 }}>Razorpay Timeout</span>
              </div>
              <div style={{ fontSize: "2.4rem", fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
                ₹4,999
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "4px" }}>
                UPI Gateway Timeout · TXN_10291
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "24px" }}>
              {[
                { label: "Recovery Success Chance", value: "91%", color: "var(--accent-green)" },
                { label: "Customer Payment History", value: "8 successful / 1 failed", color: "var(--text-secondary)" },
                { label: "Recommended Strategy", value: "Razorpay Smart Retry", color: "var(--accent-green)" },
              ].map(({ label, value, color }) => (
                <div key={label} style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 12px",
                  background: "var(--bg-secondary)",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border-subtle)",
                }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</span>
                  <span style={{ fontSize: "0.8rem", fontWeight: 600, color }}>{value}</span>
                </div>
              ))}
            </div>

            <button
              className="btn btn-primary"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={runDemo}
              disabled={isRunning}
            >
              {isRunning ? (
                <><Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> Running Recovery Agent...</>
              ) : isRecovered ? (
                "Reset Simulator"
              ) : (
                "Run Recovery Simulation"
              )}
            </button>
          </div>

          {/* Right Side: Execution Logs */}
          <div style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "28px",
            display: "flex",
            flexDirection: "column",
            boxShadow: "0 4px 6px -1px rgba(0,0,0,0.02)",
          }}>
            <div style={{
              fontSize: "0.72rem",
              fontWeight: 600,
              color: "var(--text-muted)",
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              marginBottom: "16px",
              borderBottom: "1px solid var(--border-subtle)",
              paddingBottom: "8px",
            }}>
              Execution Log Output
            </div>

            {demoState === "idle" && (
              <div style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-muted)",
                fontSize: "0.85rem",
                textAlign: "center",
                lineHeight: 1.5,
              }}>
                Click &quot;Run Recovery Simulation&quot;<br />to watch the recovery pipeline logs.
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
              {logs.map((log, i) => (
                <div key={i} className="timeline-step" style={{ paddingBottom: "2px" }}>
                  <div style={{
                    position: "absolute",
                    left: 0,
                    top: "4px",
                    width: "18px",
                    height: "18px",
                    borderRadius: "50%",
                    background: log.includes("✓") ? "var(--accent-green-dim)" : "var(--bg-secondary)",
                    border: `1px solid ${log.includes("✓") ? "var(--accent-green)" : "var(--border-subtle)"}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}>
                    {log.includes("✓") ? (
                      <CheckCircle size={10} color="var(--accent-green)" />
                    ) : (
                      <div style={{ width: "4px", height: "4px", borderRadius: "50%", background: "var(--accent-green)" }} />
                    )}
                  </div>
                  <span style={{
                    fontSize: "0.8rem",
                    color: log.includes("✓") ? "var(--accent-green)" : "var(--text-secondary)",
                    fontWeight: log.includes("✓") ? 600 : 400,
                  }}>
                    {log}
                  </span>
                </div>
              ))}

              {isRunning && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px", paddingLeft: "36px" }}>
                  <Loader2 size={12} color="var(--accent-green)" style={{ animation: "spin 1s linear infinite" }} />
                  <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Connecting to Razorpay gateway...</span>
                </div>
              )}
            </div>

            {isRecovered && (
              <div style={{
                marginTop: "16px",
                background: "var(--accent-green-dim)",
                borderRadius: "var(--radius-sm)",
                padding: "16px",
                textAlign: "center",
                border: "1px solid rgba(0, 82, 255, 0.1)",
              }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent-green)" }}>
                  ₹4,999 Recovered
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  Autonomous recovery completed in 3.0s
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </section>
  );
}
