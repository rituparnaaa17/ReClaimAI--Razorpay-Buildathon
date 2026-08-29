"use client";
import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, Legend,
} from "recharts";
import { TrendingUp, DollarSign, Clock, CheckCircle, Brain } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

const trend = Array.from({ length: 14 }, (_, i) => {
  const d = new Date(); d.setDate(d.getDate() - (13 - i));
  const r = Math.random() * 120000 + 30000;
  return {
    date: d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
    at_risk: Math.round(r), recovered: Math.round(r * (0.5 + Math.random() * 0.3)),
  };
});

const byFailure = [
  { name: "UPI Timeout", total: 580, recovered: 520, rate: 89 },
  { name: "Bank Decline", total: 390, recovered: 215, rate: 55 },
  { name: "Insuf. Balance", total: 280, recovered: 112, rate: 40 },
  { name: "Expired Card", total: 195, recovered: 68, rate: 35 },
  { name: "Tech Failure", total: 145, recovered: 119, rate: 82 },
  { name: "Abandoned", total: 791, recovered: 563, rate: 71 },
];

const byMethod = [
  { name: "UPI", failed: 640, recovered: 571 },
  { name: "Card", failed: 380, recovered: 209 },
  { name: "Netbanking", failed: 195, recovered: 136 },
  { name: "Wallet", failed: 89, recovered: 60 },
  { name: "EMI", failed: 47, recovered: 29 },
];

const pieData = [
  { name: "Recovered", value: 1204, color: "#3366FF" },
  { name: "At Risk", value: 380, color: "#F5B84B" },
  { name: "Failed", value: 247, color: "#FF6262" },
  { name: "Human Review", value: 129, color: "#805AD5" },
];

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { color: string; name: string; value: number }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "12px 16px", fontSize: "0.8rem" }}>
      <div style={{ color: "var(--text-muted)", marginBottom: "6px" }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {typeof p.value === "number" && p.value > 1000 ? formatCurrency(p.value) : p.value}
        </div>
      ))}
    </div>
  );
};

const kpis = [
  { icon: DollarSign, label: "Revenue at Risk", value: "₹25.4L", sub: "Across all cases", color: "var(--warning)" },
  { icon: TrendingUp, label: "Revenue Recovered", value: "₹16.8L", sub: "Successfully closed", color: "var(--accent-green)" },
  { icon: CheckCircle, label: "Recovery Rate", value: "66.1%", sub: "Of at-risk revenue", color: "var(--accent-green)" },
  { icon: Clock, label: "Avg Recovery Time", value: "4m 47s", sub: "Per case", color: "#3366FF" },
];

export default function AnalyticsPage() {
  const [aiInsight, setAiInsight] = useState({
    title: "AI Insight",
    insight: "UPI timeout failures increased 18% this week. Customers with previous successful UPI payments have an 84% recovery probability after a delayed retry of 5–10 minutes.",
    recommendation: "Enable automatic delayed retry for UPI timeout failures in your recovery policy.",
  });

  useEffect(() => {
    import("@/lib/api").then(({ api }) => {
      api.getInsight()
        .then((data) => { if (data?.title) setAiInsight(data as typeof aiInsight); })
        .catch(() => {});
    });
  }, []);

  return (
    <div>
      <div style={{ marginBottom: "28px" }}>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Analytics</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Revenue recovery performance metrics</p>
      </div>

      {/* KPIs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "28px" }}>
        {kpis.map(({ icon: Icon, label, value, sub, color }) => (
          <div key={label} className="kpi-card">
            <div style={{
              width: "40px", height: "40px", borderRadius: "10px",
              background: `${color}18`, border: `1px solid ${color}30`,
              display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "14px",
            }}>
              <Icon size={18} color={color} />
            </div>
            <div style={{ fontSize: "1.7rem", fontWeight: 800, letterSpacing: "-0.03em", color, lineHeight: 1, marginBottom: "4px" }}>{value}</div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 500 }}>{label}</div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* AI Insight */}
      <div style={{
        background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
        borderRadius: "14px", padding: "16px 24px", marginBottom: "24px",
        display: "flex", alignItems: "flex-start", gap: "12px",
      }}>
        <Brain size={20} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: "2px" }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--accent-green)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>
            Gemini AI Insight — {aiInsight.title}
          </div>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
            {aiInsight.insight}
          </p>
          {aiInsight.recommendation && (
            <div style={{ marginTop: "8px", fontSize: "0.8rem", color: "var(--accent-green-soft)", fontStyle: "italic" }}>
              Recommendation: {aiInsight.recommendation}
            </div>
          )}
        </div>
      </div>

      {/* Revenue Trend */}
      <div className="card" style={{ padding: "24px", marginBottom: "20px" }}>
        <div style={{ marginBottom: "20px" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "4px" }}>Revenue at Risk vs Recovered</h3>
          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>14-day trend</p>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={trend} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="rG" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F5B84B" stopOpacity={0.2} /><stop offset="95%" stopColor="#F5B84B" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="recG" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3366FF" stopOpacity={0.2} /><stop offset="95%" stopColor="#3366FF" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#718096" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#718096" }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="at_risk" name="At Risk" stroke="#F5B84B" fill="url(#rG)" strokeWidth={2} />
            <Area type="monotone" dataKey="recovered" name="Recovered" stroke="#3366FF" fill="url(#recG)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px" }}>
        {/* By Failure Reason */}
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: "0.9rem", marginBottom: "16px" }}>Recovery by Failure Reason</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {byFailure.map((d, i) => (
              <div key={d.name}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{d.name}</span>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: d.rate > 70 ? "var(--accent-green)" : d.rate > 50 ? "var(--warning)" : "var(--error)" }}>
                    {d.rate}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{
                    width: `${d.rate}%`,
                    background: d.rate > 70 ? "var(--accent-green)" : d.rate > 50 ? "var(--warning)" : "var(--error)",
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By Payment Method */}
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: "0.9rem", marginBottom: "4px" }}>By Payment Method</h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "16px" }}>Failed vs recovered</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={byMethod} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#718096" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#718096" }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="failed" name="Failed" fill="#FF6262" opacity={0.7} radius={[3, 3, 0, 0]} />
              <Bar dataKey="recovered" name="Recovered" fill="#3366FF" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status breakdown */}
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: "0.9rem", marginBottom: "4px" }}>Case Status Breakdown</h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "8px" }}>Total cases by outcome</p>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                {pieData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip formatter={(v: number, name: string) => [v, name]} contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "8px" }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", justifyContent: "center" }}>
            {pieData.map((d) => (
              <div key={d.name} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <div style={{ width: "8px", height: "8px", borderRadius: "2px", background: d.color }} />
                <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
