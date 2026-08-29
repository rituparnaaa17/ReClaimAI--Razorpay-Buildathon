"use client";
import { useState } from "react";
import { Save, ShieldCheck } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    maxRetries: 2, highValueThreshold: 50000, minProbability: 40,
    enableEmailNotifications: true, enableAutoRetry: true, testMode: true,
    merchantName: "My Store", email: "admin@store.com", businessType: "E-commerce",
  });
  const [saved, setSaved] = useState(false);

  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };

  const S = ({ label, desc, children }: { label: string; desc?: string; children: React.ReactNode }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "18px 0", borderBottom: "1px solid var(--border-subtle)" }}>
      <div>
        <div style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)", marginBottom: "2px" }}>{label}</div>
        {desc && <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{desc}</div>}
      </div>
      {children}
    </div>
  );

  return (
    <div>
      <div style={{ marginBottom: "28px", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Settings</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Configure your ReclaimAI policies</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={save} style={{ gap: "6px" }}>
          {saved ? "✓ Saved!" : <><Save size={14} /> Save Changes</>}
        </button>
      </div>

      {/* Merchant Info */}
      <div className="card" style={{ padding: "24px", marginBottom: "20px" }}>
        <h3 style={{ fontSize: "0.9rem", marginBottom: "4px" }}>Merchant Information</h3>
        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "20px" }}>Your business details</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
          {[
            { label: "Business Name", field: "merchantName" },
            { label: "Email", field: "email" },
            { label: "Business Type", field: "businessType" },
          ].map(({ label, field }) => (
            <div key={field}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>{label}</label>
              <input className="input" value={settings[field as keyof typeof settings] as string}
                onChange={(e) => setSettings((p) => ({ ...p, [field]: e.target.value }))} />
            </div>
          ))}
        </div>
      </div>

      {/* AI Policy */}
      <div className="card" style={{ padding: "24px", marginBottom: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <ShieldCheck size={16} color="var(--accent-green)" />
          <h3 style={{ fontSize: "0.9rem" }}>AI Recovery Policies</h3>
        </div>
        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>Guardrails that control AI behavior</p>

        <S label="Maximum Automatic Retries" desc="AI will stop and request human review after this many retries">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button onClick={() => setSettings((p) => ({ ...p, maxRetries: Math.max(1, p.maxRetries - 1) }))}
              style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", cursor: "pointer", fontSize: "1.1rem" }}>
              -
            </button>
            <span style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--text-primary)", minWidth: "20px", textAlign: "center" }}>{settings.maxRetries}</span>
            <button onClick={() => setSettings((p) => ({ ...p, maxRetries: Math.min(5, p.maxRetries + 1) }))}
              style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", cursor: "pointer", fontSize: "1.1rem" }}>
              +
            </button>
          </div>
        </S>

        <S label="High-Value Transaction Threshold (₹)" desc="Transactions above this amount require human approval">
          <input type="number" className="input" style={{ width: "160px" }}
            value={settings.highValueThreshold}
            onChange={(e) => setSettings((p) => ({ ...p, highValueThreshold: parseInt(e.target.value) || 0 }))} />
        </S>

        <S label="Minimum Recovery Probability (%)" desc="AI will not attempt recovery below this probability">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <input type="range" min="10" max="90" step="5"
              value={settings.minProbability}
              onChange={(e) => setSettings((p) => ({ ...p, minProbability: parseInt(e.target.value) }))}
              style={{ width: "120px", accentColor: "var(--accent-green)" }} />
            <span style={{ fontWeight: 700, color: "var(--accent-green)", minWidth: "36px" }}>{settings.minProbability}%</span>
          </div>
        </S>

        <S label="Automatic Smart Retry" desc="Enable AI to automatically retry failed payments">
          <button
            onClick={() => setSettings((p) => ({ ...p, enableAutoRetry: !p.enableAutoRetry }))}
            style={{
              width: "48px", height: "26px", borderRadius: "13px",
              background: settings.enableAutoRetry ? "var(--accent-green)" : "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)", cursor: "pointer",
              position: "relative", transition: "background 0.2s",
            }}
          >
            <div style={{
              position: "absolute", top: "3px",
              left: settings.enableAutoRetry ? "24px" : "3px",
              width: "18px", height: "18px", borderRadius: "50%",
              background: "white", transition: "left 0.2s",
            }} />
          </button>
        </S>

        <S label="Email Notifications" desc="Send recovery emails to customers">
          <button
            onClick={() => setSettings((p) => ({ ...p, enableEmailNotifications: !p.enableEmailNotifications }))}
            style={{
              width: "48px", height: "26px", borderRadius: "13px",
              background: settings.enableEmailNotifications ? "var(--accent-green)" : "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)", cursor: "pointer",
              position: "relative", transition: "background 0.2s",
            }}
          >
            <div style={{
              position: "absolute", top: "3px",
              left: settings.enableEmailNotifications ? "24px" : "3px",
              width: "18px", height: "18px", borderRadius: "50%",
              background: "white", transition: "left 0.2s",
            }} />
          </button>
        </S>

        <S label="Razorpay Test Mode" desc="Use test API keys — no real money involved">
          <div style={{
            display: "flex", alignItems: "center", gap: "6px",
            background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
            borderRadius: "8px", padding: "4px 12px",
          }}>
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--accent-green)" }} />
            <span style={{ fontSize: "0.75rem", color: "var(--accent-green)", fontWeight: 600 }}>Enabled</span>
          </div>
        </S>
      </div>
    </div>
  );
}
