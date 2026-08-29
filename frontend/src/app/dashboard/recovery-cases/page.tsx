"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Filter, ArrowRight, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { getStatusColor, getStatusLabel, getFailureLabel } from "@/lib/utils";

const FILTERS = ["all", "at_risk", "processing", "recovered", "failed", "human_review"];

const MOCK_CASES = Array.from({ length: 25 }, (_, i) => ({
  id: `RC_${10001 + i}`,
  customer_name: ["Arjun Sharma","Priya Patel","Rahul Gupta","Sneha Mehta","Vikram Singh","Ananya Reddy","Karthik Iyer","Divya Nair"][i % 8],
  customer_email: `customer${i}@example.com`,
  amount_at_risk: Math.round(Math.random() * 48000 + 999),
  failure_reason: ["UPI_TIMEOUT","BANK_DECLINE","INSUFFICIENT_BALANCE","EXPIRED_CARD","TECHNICAL_FAILURE","ABANDONED","SUBSCRIPTION_FAILURE"][i % 7],
  recovery_probability: parseFloat((Math.random() * 0.7 + 0.2).toFixed(2)),
  recommended_action: ["Smart Retry","Personalized Reminder","Alt. Payment Method","Card Update Request","Smart Retry + Notify"][i % 5],
  status: ["recovered","at_risk","processing","failed","human_review"][i % 5],
  payment_method: ["UPI","CARD","NETBANKING","WALLET"][i % 4],
  created_at: new Date(Date.now() - i * 3600000 * (1 + Math.random() * 5)).toISOString(),
}));

export default function RecoveryCasesPage() {
  const [cases, setCases] = useState(MOCK_CASES);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getRecoveryCases(filter)
      .then((data) => { if (Array.isArray(data) && data.length) setCases(data as typeof MOCK_CASES); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  const filtered = cases.filter((c) => {
    const matchFilter = filter === "all" || c.status === filter;
    const matchSearch = !search ||
      c.id.toLowerCase().includes(search.toLowerCase()) ||
      c.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      getFailureLabel(c.failure_reason).toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const counts = FILTERS.reduce((acc, f) => {
    acc[f] = f === "all" ? cases.length : cases.filter((c) => c.status === f).length;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Recovery Cases</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
          {cases.length} cases · {cases.filter((c) => c.status === "recovered").length} recovered
        </p>
      </div>

      {/* Filter + Search bar */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
        {/* Filters */}
        <div style={{ display: "flex", gap: "6px", background: "var(--bg-card)", padding: "4px", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`filter-tab ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
              id={`filter-${f}`}
            >
              {getStatusLabel(f) || "All"} <span style={{ opacity: 0.6 }}>({counts[f]})</span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, maxWidth: "320px", background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "0 14px" }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            className="input"
            style={{ background: "transparent", border: "none", padding: "10px 0", boxShadow: "none" }}
            placeholder="Search cases, customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <button className="btn btn-secondary btn-sm" onClick={() => { setFilter("all"); setSearch(""); }} style={{ gap: "6px" }}>
          <RefreshCw size={14} /> Reset
        </button>
      </div>

      {/* Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Customer</th>
              <th>Amount at Risk</th>
              <th>Problem</th>
              <th>Method</th>
              <th>Recovery Prob.</th>
              <th>Recommended Action</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id}>
                <td>
                  <span style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--accent-green-soft)" }}>
                    {c.id}
                  </span>
                </td>
                <td>
                  <div style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.875rem" }}>{c.customer_name}</div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{c.customer_email}</div>
                </td>
                <td>
                  <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>
                    ₹{c.amount_at_risk.toLocaleString()}
                  </span>
                </td>
                <td style={{ fontSize: "0.825rem" }}>{getFailureLabel(c.failure_reason)}</td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{c.payment_method}</td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div className="progress-bar" style={{ width: "60px" }}>
                      <div className="progress-fill" style={{
                        width: `${Math.round(c.recovery_probability * 100)}%`,
                        background: c.recovery_probability > 0.7 ? "var(--accent-green)" : c.recovery_probability > 0.5 ? "var(--warning)" : "var(--error)",
                      }} />
                    </div>
                    <span style={{
                      fontSize: "0.8rem", fontWeight: 700,
                      color: c.recovery_probability > 0.7 ? "var(--accent-green)" : c.recovery_probability > 0.5 ? "var(--warning)" : "var(--error)",
                    }}>
                      {Math.round(c.recovery_probability * 100)}%
                    </span>
                  </div>
                </td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{c.recommended_action}</td>
                <td><span className={`badge ${getStatusColor(c.status)}`}>{getStatusLabel(c.status)}</span></td>
                <td>
                  <Link href={`/dashboard/recovery-cases/${c.id}`} style={{ color: "var(--text-muted)", display: "flex", alignItems: "center" }}>
                    <ArrowRight size={15} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div style={{ padding: "48px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
            No cases found for the selected filter.
          </div>
        )}
      </div>
    </div>
  );
}
