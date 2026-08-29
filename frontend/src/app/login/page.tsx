"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bot, Eye, EyeOff, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@reclaimai.com");
  const [password, setPassword] = useState("demo1234");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    // Simulate auth — replace with Supabase auth
    await new Promise((r) => setTimeout(r, 1200));
    if (email && password) {
      router.push("/dashboard");
    } else {
      setError("Invalid credentials. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--bg-primary)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Background glow */}
      <div style={{
        position: "absolute", top: "30%", left: "50%", transform: "translateX(-50%)",
        width: "500px", height: "400px",
        background: "radial-gradient(ellipse, rgba(25,216,121,0.07) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div style={{ width: "100%", maxWidth: "420px", position: "relative" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "44px", height: "44px", borderRadius: "12px",
              background: "var(--accent-green)", display: "flex",
              alignItems: "center", justifyContent: "center",
            }}>
              <Bot size={24} color="#FFFFFF" strokeWidth={2.5} />
            </div>
            <span style={{ fontWeight: 800, fontSize: "1.4rem", letterSpacing: "-0.02em", color: "var(--text-primary)" }}>
              ReclaimAI
            </span>
          </Link>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginTop: "12px" }}>
            Sign in to your merchant dashboard
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "20px",
          padding: "36px",
          boxShadow: "0 24px 60px rgba(0,0,0,0.4), 0 0 40px var(--accent-green-dim)",
        }}>
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Email */}
            <div>
              <label style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "8px" }}>
                Email address
              </label>
              <input
                id="email-input"
                type="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                autoComplete="email"
              />
            </div>

            {/* Password */}
            <div>
              <label style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "8px" }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <input
                  id="password-input"
                  type={showPwd ? "text" : "password"}
                  className="input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                  style={{ paddingRight: "44px" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  style={{
                    position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)",
                    background: "transparent", border: "none", cursor: "pointer",
                    color: "var(--text-muted)",
                  }}
                >
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div style={{
                background: "var(--error-dim)", border: "1px solid rgba(255,98,98,0.2)",
                borderRadius: "8px", padding: "10px 14px", fontSize: "0.8rem", color: "var(--error)",
              }}>
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%", justifyContent: "center", marginTop: "4px" }}
              disabled={loading}
              id="login-btn"
            >
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ display: "inline-block", width: "16px", height: "16px", border: "2px solid #FFFFFF", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
                  Signing in...
                </span>
              ) : (
                <>Sign in <ArrowRight size={16} /></>
              )}
            </button>
          </form>

          {/* Demo hint */}
          <div style={{
            marginTop: "24px",
            padding: "14px",
            background: "var(--bg-secondary)",
            borderRadius: "10px",
            border: "1px solid var(--border-subtle)",
            textAlign: "center",
          }}>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "4px" }}>Demo credentials pre-filled</div>
            <div style={{ fontSize: "0.78rem", color: "var(--accent-green-soft)" }}>demo@reclaimai.com · demo1234</div>
          </div>
        </div>

        {/* Footer */}
        <p style={{ textAlign: "center", marginTop: "24px", fontSize: "0.75rem", color: "var(--text-muted)" }}>
          <Link href="/" style={{ color: "var(--accent-green-soft)" }}>← Back to homepage</Link>
        </p>
      </div>

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}
