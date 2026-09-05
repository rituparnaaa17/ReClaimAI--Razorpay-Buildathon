"use client";
import { useState, useEffect } from "react";
import { Search, ExternalLink, RefreshCw } from "lucide-react";
import { getFailureLabel, formatDateTime } from "@/lib/utils";
import { api } from "@/lib/api";

interface Transaction {
  id: string;
  customer_name: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  failure_reason: string | null;
  created_at: string;
  razorpay_payment_id: string | null;
}

const statusBg = (s: string) =>
  ({ success: "badge-recovered", failed: "badge-failed", abandoned: "badge-at-risk", pending: "badge-processing" }[s] ?? "badge-processing");

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [refreshing, setRefreshing] = useState(false);

  const load = async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    try {
      const data = await api.getTransactions() as Transaction[];
      if (Array.isArray(data)) setTransactions(data);
    } catch {
      // keep whatever we already have
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = transactions.filter((t) => {
    const mS = statusFilter === "all" || t.status === statusFilter;
    const q = search.toLowerCase();
    const mQ =
      !q ||
      (t.id ?? "").toLowerCase().includes(q) ||
      (t.customer_name ?? "").toLowerCase().includes(q) ||
      (t.razorpay_payment_id ?? "").toLowerCase().includes(q);
    return mS && mQ;
  });

  return (
    <div>
      <div style={{ marginBottom: "24px", display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Transactions</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {loading ? "Loading..." : `${transactions.length} total transactions`}
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

      {/* Filters */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", background: "var(--bg-card)", borderRadius: "10px", border: "1px solid var(--border-subtle)", padding: "0 14px" }}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              background: "var(--bg-primary)", border: "none", color: "var(--text-primary)",
              padding: "8px 0", fontSize: "0.85rem", outline: "none", cursor: "pointer"
            }}
          >
            {["all", "success", "failed", "abandoned"].map((s) => (
              <option key={s} value={s} style={{ background: "var(--bg-primary)", color: "var(--text-primary)" }}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, maxWidth: "280px", background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "0 14px" }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            className="input"
            style={{ background: "transparent", border: "none", padding: "8px 0", boxShadow: "none" }}
            placeholder="Search ID, customer, payment ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="card" style={{ padding: "60px", textAlign: "center", color: "var(--text-muted)" }}>
          <div className="ai-dot" style={{ margin: "0 auto 12px", width: 10, height: 10 }} />
          Loading transactions...
        </div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: "60px", textAlign: "center", color: "var(--text-muted)" }}>
          {transactions.length === 0
            ? "No transactions found. Transactions appear here once payments are processed via Razorpay."
            : "No transactions match your filters."}
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Failure Reason</th>
                <th>Date</th>
                <th>Razorpay ID</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td><span style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--accent-green-soft)" }}>{t.id}</span></td>
                  <td style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.875rem" }}>{t.customer_name || "—"}</td>
                  <td style={{ fontWeight: 700, color: "var(--text-primary)" }}>₹{(t.amount ?? 0).toLocaleString()}</td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{t.payment_method || "—"}</td>
                  <td><span className={`badge ${statusBg(t.status)}`}>{t.status}</span></td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {t.failure_reason ? getFailureLabel(t.failure_reason) : "—"}
                  </td>
                  <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{formatDateTime(t.created_at)}</td>
                  <td>
                    {t.razorpay_payment_id ? (
                      <span style={{ fontFamily: "monospace", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        {t.razorpay_payment_id.slice(0, 18)}…
                      </span>
                    ) : "—"}
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
