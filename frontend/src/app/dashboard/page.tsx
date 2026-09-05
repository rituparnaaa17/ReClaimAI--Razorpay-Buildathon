"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  TrendingUp, DollarSign, AlertCircle,
  ShoppingCart, CheckCircle, ArrowRight, Brain, RefreshCw,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import { formatCurrency, getStatusColor, getStatusLabel, getFailureLabel } from "@/lib/utils";

// ── Fallback data ─────────────────────────────────────────────────────────────
const FALLBACK_OVERVIEW = {
  revenue_at_risk: 2540000,
  revenue_recovered: 1680000,
  recovery_rate: 66.1,
  failed_payments: 1640,
  abandoned_checkouts: 791,
  recovery_attempts: 1820,
  successful_recoveries: 1204,
  avg_recovery_time_seconds: 287,
};

const FALLBACK_TREND = Array.from({ length: 14 }, (_, i) => {
  const d = new Date(); d.setDate(d.getDate() - (13 - i));
  const at_risk = 40000 + (i * 6000) + (Math.sin(i) * 20000);
  return {
    date: d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
    at_risk: Math.round(at_risk),
    recovered: Math.round(at_risk * 0.62),
  };
});

const COLORS = ["#3366FF", "#67C99A", "#F5B84B", "#FF6262", "#805AD5"];

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { color: string; name: string; value: number }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "12px 16px", fontSize: "0.8rem" }}>
      <div style={{ color: "var(--text-muted)", marginBottom: "6px" }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.color, fontWeight: 600 }}>{p.name}: {formatCurrency(p.value)}</div>
      ))}
    </div>
  );
};

export default function DashboardPage() {
  const [overview, setOverview] = useState(FALLBACK_OVERVIEW);
  const [cases, setCases] = useState<Record<string, unknown>[]>([]);
  const [insight, setInsight] = useState({ title: "AI Insight Loading...", insight: "Fetching real-time pattern analysis from Gemini AI...", recommendation: "" });
  const [insightLoaded, setInsightLoaded] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    setRefreshing(true);
    try {
      // Fetch analytics overview — API returns flat object directly
      const ov = await api.getAnalytics() as Record<string, unknown>;
      if (ov?.recovery_rate !== undefined) setOverview(ov as typeof FALLBACK_OVERVIEW);
    } catch { /* use fallback */ }

    try {
      const data = await api.getRecoveryCases() as Record<string, unknown>[];
      if (Array.isArray(data) && data.length) setCases(data.slice(0, 6));
    } catch { /* use fallback */ }

    // Fetch Gemini AI insight
    if (!insightLoaded) {
      try {
        const ins = await api.getInsight() as Record<string, unknown>;
        if (ins?.title) { setInsight(ins as typeof insight); setInsightLoaded(true); }
      } catch { /* keep default */ }
    }
    setRefreshing(false);
  }, [insightLoaded]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const kpis = [
    { icon: AlertCircle, label: "Revenue at Risk", value: formatCurrency(overview.revenue_at_risk), sub: "Across active cases", color: "var(--warning)", trend: "+12% vs last week" },
    { icon: DollarSign, label: "Revenue Recovered", value: formatCurrency(overview.revenue_recovered), sub: "Successfully recovered", color: "var(--accent-green)", trend: `+${overview.recovery_rate}%` },
    { icon: TrendingUp, label: "Recovery Rate", value: `${overview.recovery_rate}%`, sub: "Of at-risk revenue", color: "var(--accent-green)" },
    { icon: AlertCircle, label: "Failed Payments", value: overview.failed_payments.toLocaleString(), sub: `+ ${overview.abandoned_checkouts} abandoned`, color: "var(--error)" },
    { icon: ShoppingCart, label: "Recovery Attempts", value: overview.recovery_attempts.toLocaleString(), sub: "Automated + manual", color: "#3366FF" },
    { icon: CheckCircle, label: "Successful", value: overview.successful_recoveries.toLocaleString(), sub: `Avg ${Math.floor(overview.avg_recovery_time_seconds / 60)}m ${overview.avg_recovery_time_seconds % 60}s`, color: "var(--accent-green)" },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "28px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Revenue Overview</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Real-time AI recovery analytics</p>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {/* Live Gemini insight pill */}
          <div style={{
            display: "flex", alignItems: "center", gap: "8px", maxWidth: "340px",
            background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
            borderRadius: "10px", padding: "8px 14px",
          }}>
            <Brain size={13} color="var(--accent-green)" style={{ flexShrink: 0 }} />
            <span style={{ fontSize: "0.75rem", color: "var(--accent-green-soft)", lineHeight: 1.4 }}>
              <strong style={{ color: "var(--accent-green)" }}>{insight.title}</strong>
              {" — "}{insight.recommendation || insight.insight.slice(0, 80)}
            </span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchData} disabled={refreshing} style={{ gap: "6px" }}>
            <RefreshCw size={13} style={{ animation: refreshing ? "spin 1s linear infinite" : "none" }} />
            {refreshing ? "Refreshing" : "Refresh"}
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "28px" }}>
        {kpis.map((k) => {
          const Icon = k.icon;
          return (
            <div key={k.label} className="kpi-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: `${k.color}18`, border: `1px solid ${k.color}30`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon size={18} color={k.color} />
                </div>
                {k.trend && <span style={{ fontSize: "0.72rem", color: "var(--accent-green)", background: "var(--accent-green-dim)", padding: "2px 8px", borderRadius: "6px", fontWeight: 600 }}>{k.trend}</span>}
              </div>
              <div style={{ fontSize: "1.8rem", fontWeight: 800, letterSpacing: "-0.03em", color: k.color, marginBottom: "4px", lineHeight: 1 }}>{k.value}</div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 500 }}>{k.label}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>{k.sub}</div>
            </div>
          );
        })}
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px", marginBottom: "28px" }}>
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "4px" }}>Revenue Trend</h3>
          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "20px" }}>At-risk vs recovered (14 days)</p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={FALLBACK_TREND} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F5B84B" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#F5B84B" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="recovGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3366FF" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#3366FF" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#718096" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#718096" }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="at_risk" name="At Risk" stroke="#F5B84B" fill="url(#riskGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="recovered" name="Recovered" stroke="#3366FF" fill="url(#recovGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "4px" }}>By Failure Reason</h3>
          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "20px" }}>Recovery rate per type (live)</p>
          {(() => {
            // Derive breakdown from live cases
            const REASON_LABELS: Record<string, string> = {
              UPI_TIMEOUT: "UPI Timeout", BANK_DECLINE: "Bank Decline",
              ABANDONED: "Abandoned", INSUFFICIENT_BALANCE: "Insuf. Balance",
              EXPIRED_CARD: "Expired Card", TECHNICAL_FAILURE: "Technical",
            };
            const counts: Record<string, { total: number; recovered: number }> = {};
            cases.forEach((c) => {
              const r = (c.failure_reason as string) || "OTHER";
              if (!counts[r]) counts[r] = { total: 0, recovered: 0 };
              counts[r].total++;
              if (c.status === "recovered") counts[r].recovered++;
            });
            const breakdown = Object.entries(counts)
              .map(([r, v]) => ({ reason: REASON_LABELS[r] || r, rate: v.total > 0 ? Math.round((v.recovered / v.total) * 100) : 0 }))
              .sort((a, b) => b.rate - a.rate)
              .slice(0, 5);
            if (!breakdown.length) {
              return <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", textAlign: "center", padding: "20px 0" }}>No cases yet</p>;
            }
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {breakdown.map((d, i) => (
                  <div key={d.reason}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "5px" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{d.reason}</span>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: COLORS[i] }}>{d.rate}%</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${d.rate}%`, background: COLORS[i] }} />
                    </div>
                  </div>
                ))}
              </div>
            );
          })()}
        </div>
      </div>

      {/* Recent Cases */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 style={{ fontSize: "1rem", marginBottom: "2px" }}>Recent Recovery Cases</h3>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Live cases from the recovery engine</p>
          </div>
          <Link href="/dashboard/recovery-cases" className="btn btn-secondary btn-sm" style={{ gap: "6px", fontSize: "0.78rem" }}>
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="table-container" style={{ border: "none", borderRadius: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID</th><th>Customer</th><th>Amount</th><th>Problem</th><th>Probability</th><th>Action</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px", fontSize: "0.85rem" }}>
                    No recovery cases yet. Cases appear here once failed payments are detected.
                  </td>
                </tr>
              ) : cases.map((c) => {
                const prob = Number(c.recovery_probability);
                return (
                  <tr key={c.id as string} style={{ cursor: "pointer" }} onClick={() => window.location.href = `/dashboard/recovery-cases/${c.id}`}>
                    <td style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--accent-green-soft)" }}>{c.id as string}</td>
                    <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>{c.customer_name as string}</td>
                    <td style={{ fontWeight: 700, color: "var(--text-primary)" }}>₹{Number(c.amount_at_risk).toLocaleString()}</td>
                    <td style={{ fontSize: "0.8rem" }}>{getFailureLabel(c.failure_reason as string)}</td>
                    <td>
                      <span style={{ fontWeight: 700, color: prob > 0.7 ? "var(--accent-green)" : prob > 0.5 ? "var(--warning)" : "var(--error)" }}>
                        {Math.round(prob * 100)}%
                      </span>
                    </td>
                    <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{c.recommended_action as string}</td>
                    <td><span className={`badge ${getStatusColor(c.status as string)}`}>{getStatusLabel(c.status as string)}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}
