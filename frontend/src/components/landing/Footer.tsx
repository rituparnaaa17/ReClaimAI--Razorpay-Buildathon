"use client";
import Link from "next/link";
import { Shield, ArrowRight, ExternalLink } from "lucide-react";

const footerLinks = {
  Product: ["Dashboard", "Recovery Cases", "AI Agent", "Analytics"],
  "How It Works": ["Detection", "Diagnosis", "Recovery", "Verification"],
  Resources: ["Documentation", "API Reference", "Security", "Changelog"],
};

export default function Footer() {
  return (
    <>
      {/* Final CTA */}
      <section style={{
        background: "var(--bg-primary)",
        padding: "120px 0",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          width: "600px", height: "400px",
          background: "radial-gradient(ellipse, rgba(25,216,121,0.07) 0%, transparent 70%)",
          pointerEvents: "none",
        }} />
        <div className="container" style={{ position: "relative" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
            borderRadius: "20px", padding: "5px 16px", marginBottom: "32px",
          }}>
            <div className="ai-dot" style={{ width: "6px", height: "6px" }} />
            <span style={{ fontSize: "0.78rem", color: "var(--accent-green)", fontWeight: 600 }}>
              Built for RazorPay
            </span>
          </div>

          <h2 style={{ marginBottom: "20px", fontSize: "clamp(2rem, 5vw, 3.5rem)" }}>
            Stop watching<br /><span className="glow-text">revenue disappear.</span>
          </h2>

          <p style={{ fontSize: "1.1rem", maxWidth: "500px", margin: "0 auto 40px" }}>
            Let AI find it, recover it, and show you exactly what it saved.
          </p>

          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/dashboard" className="btn btn-primary btn-lg">
              Start Recovering Revenue <ArrowRight size={18} />
            </Link>
            <Link href="/login" className="btn btn-secondary btn-lg">
              View live demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        background: "var(--bg-secondary)",
        borderTop: "1px solid var(--border-subtle)",
        padding: "60px 0 32px",
      }}>
        <div className="container">
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "48px", marginBottom: "48px" }}>
            {/* Brand */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                <div style={{
                  width: "32px", height: "32px", borderRadius: "8px",
                  background: "var(--accent-green)", display: "flex",
                  alignItems: "center", justifyContent: "center",
                }}>
                  <Shield size={18} color="#FFFFFF" strokeWidth={2.5} />
                </div>
                <span style={{ fontWeight: 700, fontSize: "1.05rem", color: "var(--text-primary)" }}>ReclaimAI</span>
              </div>
              <p style={{ fontSize: "0.875rem", lineHeight: 1.7, maxWidth: "260px", color: "var(--text-muted)" }}>
                AI-powered revenue recovery platform. Detect, diagnose, and recover failed payments autonomously.
              </p>
              <div style={{ marginTop: "16px", display: "flex", gap: "8px" }}>
                <a href="https://github.com" target="_blank" rel="noopener noreferrer"
                  style={{
                    width: "36px", height: "36px", borderRadius: "8px",
                    background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "var(--text-muted)", transition: "all 0.2s",
                  }}
                >
                  <ExternalLink size={16} />
                </a>
              </div>
            </div>

            {/* Links */}
            {Object.entries(footerLinks).map(([section, links]) => (
              <div key={section}>
                <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "16px" }}>
                  {section}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {links.map((link) => (
                    <a key={link} href="#" style={{ fontSize: "0.875rem", color: "var(--text-muted)", transition: "color 0.15s" }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}>
                      {link}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Bottom */}
          <div style={{
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              © 2026 ReclaimAI · Built for RazorPay
            </span>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Powered by <span className="text-green">Gemini AI</span> + <span style={{ color: "#3366FF" }}>LangGraph</span>
            </span>
          </div>
        </div>
      </footer>
    </>
  );
}
