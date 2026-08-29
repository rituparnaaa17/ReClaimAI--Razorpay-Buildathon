"use client";
import { useState } from "react";
import { Search, Filter } from "lucide-react";
import { getFailureLabel, formatDateTime } from "@/lib/utils";

const TRANSACTIONS = Array.from({ length: 40 }, (_, i) => ({
  id: `TXN_${10000 + i}`,
  customer_name: ["Arjun Sharma","Priya Patel","Rahul Gupta","Sneha Mehta","Vikram Singh","Ananya Reddy","Karthik Iyer","Divya Nair"][i % 8],
  amount: Math.round(Math.random() * 48000 + 199),
  currency: "INR",
  payment_method: ["UPI","CARD","NETBANKING","WALLET","EMI"][i % 5],
  status: ["success","failed","abandoned","success","success","failed"][i % 6],
  failure_reason: i % 6 === 1 ? ["UPI_TIMEOUT","BANK_DECLINE","INSUFFICIENT_BALANCE","EXPIRED_CARD","TECHNICAL_FAILURE"][i % 5]
    : i % 6 === 5 ? "ABANDONED" : null,
  created_at: new Date(Date.now() - i * 3600000 * 2).toISOString(),
  razorpay_payment_id: `pay_${Math.random().toString(36).substr(2, 16)}`,
}));

const statusColor = (s: string) => ({
  success: "var(--accent-green)", failed: "var(--error)", abandoned: "var(--warning)", pending: "#3366FF",
}[s] || "var(--text-muted)");

const statusBg = (s: string) => ({
  success: "badge-recovered", failed: "badge-failed", abandoned: "badge-at-risk", pending: "badge-processing",
}[s] || "badge-processing");

export default function TransactionsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = TRANSACTIONS.filter((t) => {
    const mS = statusFilter === "all" || t.status === statusFilter;
    const mQ = !search || t.id.toLowerCase().includes(search.toLowerCase()) || t.customer_name.toLowerCase().includes(search.toLowerCase());
    return mS && mQ;
  });

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Transactions</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{TRANSACTIONS.length} total transactions</p>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
        <div style={{ display: "flex", gap: "6px", background: "var(--bg-card)", padding: "4px", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
          {["all", "success", "failed", "abandoned"].map((s) => (
            <button key={s} className={`filter-tab ${statusFilter === s ? "active" : ""}`} onClick={() => setStatusFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, maxWidth: "280px", background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "10px", padding: "0 14px" }}>
          <Search size={15} color="var(--text-muted)" />
          <input className="input" style={{ background: "transparent", border: "none", padding: "8px 0", boxShadow: "none" }} placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

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
                <td style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.875rem" }}>{t.customer_name}</td>
                <td style={{ fontWeight: 700, color: "var(--text-primary)" }}>₹{t.amount.toLocaleString()}</td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{t.payment_method}</td>
                <td><span className={`badge ${statusBg(t.status)}`}>{t.status}</span></td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{t.failure_reason ? getFailureLabel(t.failure_reason) : "—"}</td>
                <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{formatDateTime(t.created_at)}</td>
                <td><span style={{ fontFamily: "monospace", fontSize: "0.72rem", color: "var(--text-muted)" }}>{t.razorpay_payment_id.slice(0, 16)}...</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
