"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ShieldCheck, CreditCard, Zap, Activity } from "lucide-react";

function AnimatedMockup() {
  const [activeBar, setActiveBar] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveBar((prev) => (prev + 1) % 4);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="animate-float" style={{
      width: "100%", maxWidth: "560px",
      position: "relative",
    }}>
      {/* Glow Behind Mockup */}
      <div style={{
        position: "absolute", top: "10%", left: "10%", right: "10%", bottom: "10%",
        background: "var(--accent-green)", filter: "blur(60px)", opacity: 0.2, zIndex: -1
      }} />

      {/* Main Glass Card */}
      <div className="glass-card" style={{ padding: "28px", position: "relative", overflow: "hidden" }}>
        
        {/* Mockup Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "rgba(59, 130, 246, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid rgba(59, 130, 246, 0.3)" }}>
              <Zap size={18} color="#3B82F6" />
            </div>
            <div>
              <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-primary)" }}>Recovery Pipeline</div>
              <div style={{ fontSize: "0.75rem", color: "var(--accent-green)", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--accent-green)", boxShadow: "0 0 10px var(--accent-green)" }} />
                Live Analysis
              </div>
            </div>
          </div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
            ₹1,45,290 <span style={{ fontSize: "0.75rem", color: "#34D399", fontWeight: 600 }}>+12%</span>
          </div>
        </div>

        {/* Animated Bar Chart */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: "16px", height: "140px", marginBottom: "32px" }}>
          {[60, 45, 80, 50, 95, 70, 85].map((height, i) => (
            <div key={i} style={{
              flex: 1,
              background: i === activeBar ? "linear-gradient(to top, #3B82F6, #6366F1)" : "rgba(255,255,255,0.05)",
              height: `${i === activeBar ? height + 10 : height}%`,
              borderRadius: "4px 4px 0 0",
              transition: "all 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
              boxShadow: i === activeBar ? "0 0 20px rgba(59, 130, 246, 0.4)" : "none",
            }} />
          ))}
        </div>

        {/* Action Items */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {[
            { label: "Payment Decline: Insufficient Funds", amount: "₹4,999", status: "Retrying..." },
            { label: "UPI Gateway Timeout detected", amount: "₹1,250", status: "Recovered" }
          ].map((item, i) => (
            <div key={i} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "16px", background: "rgba(255,255,255,0.02)",
              borderRadius: "12px", border: "1px solid var(--border-subtle)",
              transform: i === 0 ? "scale(1.02)" : "scale(1)",
              borderColor: i === 0 ? "rgba(59, 130, 246, 0.3)" : "var(--border-subtle)",
              transition: "all 0.3s"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <CreditCard size={16} color="var(--text-muted)" />
                <div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", fontWeight: 500 }}>{item.label}</div>
                  <div style={{ fontSize: "0.7rem", color: i === 0 ? "var(--warning)" : "var(--accent-green)", fontWeight: 600, marginTop: "2px" }}>{item.status}</div>
                </div>
              </div>
              <div style={{ fontSize: "0.9rem", fontWeight: 700 }}>{item.amount}</div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}

export default function HeroSection() {
  return (
    <section
      style={{
        minHeight: "95vh",
        display: "flex",
        alignItems: "center",
        paddingTop: "120px",
        paddingBottom: "80px",
        position: "relative",
      }}
    >
      <div className="container responsive-grid-1" style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "40px",
        alignItems: "center",
      }}>
        {/* Left Side (Text content) */}
        <div>
          {/* Animated Badge */}
          <div className="animate-in delay-1" style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            background: "rgba(59, 130, 246, 0.1)", border: "1px solid rgba(59, 130, 246, 0.2)",
            borderRadius: "100px", padding: "6px 14px", marginBottom: "32px",
            boxShadow: "0 0 20px rgba(59, 130, 246, 0.15)"
          }}>
            <ShieldCheck size={14} color="#60A5FA" />
            <span style={{ fontSize: "0.75rem", color: "#60A5FA", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Enterprise Revenue Protection
            </span>
          </div>

          {/* Title */}
          <h1 className="animate-in delay-2" style={{ marginBottom: "24px", letterSpacing: "-0.04em", lineHeight: 1.1 }}>
            Turn payment failures into <span className="text-gradient">recovered revenue</span>.
          </h1>

          {/* Subtitle */}
          <p className="animate-in delay-3" style={{ fontSize: "1.15rem", color: "var(--text-secondary)", marginBottom: "40px", maxWidth: "520px" }}>
            ReclaimAI autonomously diagnoses Gateway timeouts and card declines, executing highly precise, policy-bounded retries to recover lost transactions instantly.
          </p>

          {/* CTAs */}
          <div className="animate-in delay-3" style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "48px" }}>
            <Link href="/login" className="btn btn-primary btn-lg">
              Sign In <ArrowRight size={18} style={{ marginLeft: "4px" }} />
            </Link>
          </div>

          {/* Metrics */}
          <div className="animate-in delay-3" style={{
            display: "flex", gap: "40px", paddingTop: "32px",
            borderTop: "1px solid var(--border-subtle)",
          }}>
            {[
              { value: "66.1%", label: "Avg. Recovery Rate" },
              { value: "Under 5m", label: "Recovery Speed" },
              { value: "100%", label: "Autonomous Pipeline" },
            ].map((metric) => (
              <div key={metric.label}>
                <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "4px" }}>{metric.value}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>{metric.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Side (Visual) */}
        <div className="animate-in delay-2" style={{ display: "flex", justifyContent: "center" }}>
          <AnimatedMockup />
        </div>
      </div>
    </section>
  );
}
