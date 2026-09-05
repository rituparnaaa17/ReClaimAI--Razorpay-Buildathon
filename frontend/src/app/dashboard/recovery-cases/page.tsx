"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Search, ArrowRight, RefreshCw, FolderOpen } from "lucide-react";
import { api } from "@/lib/api";
import { getStatusColor, getStatusLabel, getFailureLabel } from "@/lib/utils";

interface RecoveryCase {
  id: string;
  customer_name: string;
  customer_email: string;
  amount_at_risk: number;
  failure_reason: string;
  recovery_probability: number;
  recommended_action: string;
  status: string;
  payment_method: string;
  created_at: string;
}

const STATUS_FILTERS = [
  "all", "detected", "analyzing", "predicting", "deciding",
  "action_required", "approved", "recovering", "verifying",
  "recovered", "failed", "escalated", "no_action", "expired",
];

export default function RecoveryCasesPage() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const load = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    try {
      const data = await api.getRecoveryCases("all") as RecoveryCase[];
      if (Array.isArray(data)) setCases(data);
    } catch {
      // keep current data
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleReset = () => {
    setFilter("all");
    setSearch("");
    load(true);
  };

  const filtered = cases.filter((c) => {
    const statusMatch = filter === "all" || c.status === filter;
    if (!statusMatch) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (c.id ?? "").toLowerCase().includes(q) ||
      (c.customer_name ?? "").toLowerCase().includes(q) ||
      getFailureLabel(c.failure_reason).toLowerCase().includes(q)
    );
  });

  const counts = STATUS_FILTERS.reduce<Record<string, number>>((acc, f) => {
    acc[f] = f === "all" ? cases.length : cases.filter((c) => c.status === f).length;
    return acc;
  }, {});

  const recovered = cases.filter((c) => c.status === "recovered").length;
  const actionRequired = cases.filter((c) => ["action_required", "escalated"].includes(c.status)).length;

  return (
    <div>
      {/* Header */}
      <div className="responsive-flex-col" style={{ marginBottom: "24px", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Recovery Cases</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {loading ? "Loading…" : `${cases.length} total · ${recovered} recovered`}
            {actionRequired > 0 && (
              <span style={{ color: "var(--warning)", marginLeft: "8px", fontWeight: 600 }}>
                · {actionRequired} awaiting human review
              </span>
            )}
          </p>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => load(true)}
          disabled={refreshing}
          style={{ gap: "6px" }}
        >
          <RefreshCw size={14} className={refreshing ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Filter + Search */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
        <div style={{
          display: "flex", alignItems: "center",
          background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
          borderRadius: "10px", padding: "0 14px",
        }}>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              background: "var(--bg-primary)", border: "none", color: "var(--text-primary)",
              padding: "10px 0", fontSize: "0.85rem", outline: "none", cursor: "pointer"
            }}
          >
            {STATUS_FILTERS.map((f) => (
              <option key={f} value={f} style={{ background: "var(--bg-primary)", color: "var(--text-primary)" }}>
                {getStatusLabel(f) || "All"} ({counts[f]})
              </option>
            ))}
          </select>
        </div>

        <div style={{
          display: "flex", alignItems: "center", gap: "8px",
          flex: 1, maxWidth: "320px",
          background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
          borderRadius: "10px", padding: "0 14px",
        }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            className="input"
            style={{ background: "transparent", border: "none", padding: "10px 0", boxShadow: "none" }}
            placeholder="Search cases, customers…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <button className="btn btn-secondary btn-sm" onClick={handleReset} style={{ gap: "6px" }}>
          <RefreshCw size={14} /> Reset
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="card" style={{ padding: "60px", textAlign: "center", color: "var(--text-muted)" }}>
          <div className="ai-dot" style={{ margin: "0 auto 12px", width: 10, height: 10 }} />
          Loading recovery cases…
        </div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: "60px", textAlign: "center" }}>
          <FolderOpen size={32} color="var(--text-muted)" style={{ margin: "0 auto 16px", display: "block" }} />
          <div style={{ color: "var(--text-primary)", fontWeight: 600, marginBottom: "8px" }}>
            {cases.length === 0 ? "No recovery cases yet" : "No cases match your filter"}
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: 420, margin: "0 auto" }}>
            {cases.length === 0
              ? "Cases appear here automatically when Razorpay webhooks report failed payments. Make sure your webhook URL is configured and ngrok is running."
              : "Try a different filter or search term."}
          </p>
        </div>
      ) : (
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
                <tr key={c.id} style={["action_required", "escalated"].includes(c.status) ? { background: "rgba(245,184,75,0.04)" } : undefined}>
                  <td>
                    <span style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--accent-green-soft)" }}>
                      {c.id}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.875rem" }}>{c.customer_name || "—"}</div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{c.customer_email || ""}</div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>
                      ₹{(c.amount_at_risk ?? 0).toLocaleString()}
                    </span>
                  </td>
                  <td style={{ fontSize: "0.825rem" }}>{getFailureLabel(c.failure_reason)}</td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{c.payment_method || "—"}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div className="progress-bar" style={{ width: "60px" }}>
                        <div className="progress-fill" style={{
                          width: `${Math.round((c.recovery_probability ?? 0) * 100)}%`,
                          background: (c.recovery_probability ?? 0) > 0.7 ? "var(--accent-green)" : (c.recovery_probability ?? 0) > 0.5 ? "var(--warning)" : "var(--error)",
                        }} />
                      </div>
                      <span style={{
                        fontSize: "0.8rem", fontWeight: 700,
                        color: (c.recovery_probability ?? 0) > 0.7 ? "var(--accent-green)" : (c.recovery_probability ?? 0) > 0.5 ? "var(--warning)" : "var(--error)",
                      }}>
                        {Math.round((c.recovery_probability ?? 0) * 100)}%
                      </span>
                    </div>
                  </td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{c.recommended_action || "—"}</td>
                  <td>
                    <span className={`badge ${getStatusColor(c.status)}`}>{getStatusLabel(c.status)}</span>
                    {["action_required", "escalated"].includes(c.status) && (
                      <span style={{ fontSize: "0.65rem", color: "var(--warning)", display: "block", marginTop: "2px" }}>
                        ⚠ Needs review
                      </span>
                    )}
                  </td>
                  <td>
                    <Link href={`/dashboard/recovery-cases/${c.id}`} style={{ color: "var(--text-muted)", display: "flex", alignItems: "center" }}>
                      <ArrowRight size={15} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
