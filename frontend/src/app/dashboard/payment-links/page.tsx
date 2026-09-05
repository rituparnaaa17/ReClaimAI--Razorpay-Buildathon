"use client";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ExternalLink, Plus, RefreshCw, Link as LinkIcon, CheckCircle, Clock, XCircle, Brain, User } from "lucide-react";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

interface PaymentLink {
  id: string;
  short_url: string;
  amount: number;
  status: string;
  description: string;
  customer_name: string;
  customer_email: string;
  created_at: string | null;
  payments_count: number;
  notes: Record<string, string>;
}

interface CreateForm {
  amount: string;
  customer_name: string;
  customer_email: string;
  customer_contact: string;
  description: string;
  case_id: string;
}

const statusIcon = (s: string) => {
  if (s === "paid") return <CheckCircle size={13} color="var(--accent-green)" />;
  if (s === "cancelled" || s === "expired") return <XCircle size={13} color="var(--error)" />;
  return <Clock size={13} color="var(--warning)" />;
};

const statusBadge = (s: string) => {
  if (s === "paid") return "badge-recovered";
  if (s === "cancelled" || s === "expired") return "badge-failed";
  return "badge-processing";
};

export default function PaymentLinksPage() {
  const [links, setLinks] = useState<PaymentLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [form, setForm] = useState<CreateForm>({
    amount: "",
    customer_name: "",
    customer_email: "",
    customer_contact: "",
    description: "ReclaimAI — Complete your payment",
    case_id: "",
  });

  const load = useCallback(async (spinner = false) => {
    if (spinner) setRefreshing(true);
    try {
      const data = await api.getPaymentLinks() as PaymentLink[];
      if (Array.isArray(data)) setLinks(data);
    } catch {
      // keep current state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    setCreateError("");
    if (!form.amount || !form.customer_name || !form.customer_email) {
      setCreateError("Amount, customer name and email are required.");
      return;
    }
    const amount = parseFloat(form.amount);
    if (isNaN(amount) || amount <= 0) {
      setCreateError("Enter a valid amount in ₹.");
      return;
    }
    setCreating(true);
    try {
      await api.createPaymentLink({
        amount,
        customer_name: form.customer_name,
        customer_email: form.customer_email,
        customer_contact: form.customer_contact || undefined,
        description: form.description,
        case_id: form.case_id || undefined,
      });
      setShowCreate(false);
      setForm({ amount: "", customer_name: "", customer_email: "", customer_contact: "", description: "ReclaimAI — Complete your payment", case_id: "" });
      await load(true);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to create payment link";
      setCreateError(msg);
    } finally {
      setCreating(false);
    }
  };

  const paid = links.filter((l) => l.status === "paid").length;
  const agentCreated = links.filter((l) => !!l.notes?.recovery_case_id).length;
  const totalCollected = links.filter((l) => l.status === "paid").reduce((a, l) => a + l.amount, 0);

  return (
    <div>
      {/* Header */}
      <div className="responsive-flex-col" style={{ marginBottom: "24px", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Payment Links</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Razorpay payment links created for recovery — live from your account
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="btn btn-secondary btn-sm" onClick={() => load(true)} disabled={refreshing} style={{ gap: "6px" }}>
            <RefreshCw size={14} className={refreshing ? "spin" : ""} />
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)} style={{ gap: "6px" }}>
            <Plus size={14} />
            Create Link
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="responsive-grid-2" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "28px" }}>
        {[
          { label: "Total Links", value: loading ? "…" : links.length, color: "#3366FF" },
          { label: "Agent Created", value: loading ? "…" : agentCreated, color: "var(--accent-green-soft)" },
          { label: "Paid", value: loading ? "…" : paid, color: "var(--accent-green)" },
          { label: "Amount Collected", value: loading ? "…" : `₹${totalCollected.toLocaleString()}`, color: "var(--accent-green)" },
        ].map(({ label, value, color }) => (
          <div key={label} className="kpi-card" style={{ padding: "18px 22px" }}>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color, letterSpacing: "-0.02em", lineHeight: 1, marginBottom: "4px" }}>{value}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Create modal */}
      {showCreate && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 1000,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <div className="card" style={{ width: "100%", maxWidth: 480, padding: "32px", position: "relative", background: "var(--bg-primary)", border: "1px solid var(--border-subtle)", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)" }}>
            <h3 style={{ fontSize: "1.1rem", marginBottom: "20px" }}>Create Payment Link</h3>

            {createError && (
              <div style={{ background: "var(--error-dim, rgba(255,98,98,0.15))", border: "1px solid rgba(255,98,98,0.3)", color: "var(--error)", borderRadius: "8px", padding: "10px 14px", marginBottom: "16px", fontSize: "0.82rem" }}>
                {createError}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {[
                { label: "Amount (₹) *", key: "amount", type: "number", placeholder: "e.g. 4999" },
                { label: "Customer Name *", key: "customer_name", type: "text", placeholder: "Arjun Sharma" },
                { label: "Customer Email *", key: "customer_email", type: "email", placeholder: "arjun@example.com" },
                { label: "Customer Phone", key: "customer_contact", type: "tel", placeholder: "+919876543210" },
                { label: "Recovery Case ID (optional)", key: "case_id", type: "text", placeholder: "uuid of the case" },
              ].map(({ label, key, type, placeholder }) => (
                <div key={key}>
                  <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>{label}</label>
                  <input
                    className="input"
                    type={type}
                    placeholder={placeholder}
                    value={form[key as keyof CreateForm]}
                    onChange={(e) => setForm((p) => ({ ...p, [key]: e.target.value }))}
                  />
                </div>
              ))}
              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>Description</label>
                <input
                  className="input"
                  type="text"
                  value={form.description}
                  onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px", marginTop: "24px" }}>
              <button className="btn btn-primary" onClick={handleCreate} disabled={creating} style={{ flex: 1 }}>
                {creating ? "Creating…" : "Create Link"}
              </button>
              <button className="btn btn-secondary" onClick={() => { setShowCreate(false); setCreateError(""); }} style={{ flex: 1 }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="card" style={{ padding: "60px", textAlign: "center", color: "var(--text-muted)" }}>
          <div className="ai-dot" style={{ margin: "0 auto 12px", width: 10, height: 10 }} />
          Loading payment links from Razorpay…
        </div>
      ) : links.length === 0 ? (
        <div className="card" style={{ padding: "60px", textAlign: "center" }}>
          <LinkIcon size={32} color="var(--text-muted)" style={{ margin: "0 auto 16px", display: "block" }} />
          <div style={{ color: "var(--text-primary)", fontWeight: 600, marginBottom: "8px" }}>No payment links yet</div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: 400, margin: "0 auto 20px" }}>
            Create your first payment link to send to customers for recovery.
          </p>
          <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)} style={{ gap: "6px" }}>
            <Plus size={14} />
            Create Link
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Recovery Case</th>
                <th>Created</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              {links.map((l) => {
                const isAgentCreated = !!l.notes?.recovery_case_id;
                const caseId = l.notes?.recovery_case_id;
                return (
                  <tr key={l.id}>
                    <td>
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: "4px",
                        fontSize: "0.7rem", fontWeight: 600, padding: "2px 8px", borderRadius: "6px",
                        background: isAgentCreated ? "var(--accent-green-dim)" : "var(--bg-secondary)",
                        color: isAgentCreated ? "var(--accent-green)" : "var(--text-muted)",
                        border: `1px solid ${isAgentCreated ? "var(--border-green)" : "var(--border-subtle)"}`,
                      }}>
                        {isAgentCreated ? <><Brain size={10} /> Agent</> : <><User size={10} /> Manual</>}
                      </span>
                    </td>
                    <td><span style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "var(--accent-green-soft)" }}>{l.id.slice(0, 18)}…</span></td>
                    <td>
                      <div style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.85rem" }}>{l.customer_name || "—"}</div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{l.customer_email || ""}</div>
                    </td>
                    <td style={{ fontWeight: 700, color: "var(--text-primary)" }}>₹{(l.amount ?? 0).toLocaleString()}</td>
                    <td>
                      <span className={`badge ${statusBadge(l.status)}`} style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                        {statusIcon(l.status)}
                        {l.status}
                      </span>
                    </td>
                    <td>
                      {caseId ? (
                        <Link
                          href={`/dashboard/recovery-cases/${caseId}`}
                          style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "var(--accent-green)", textDecoration: "none" }}
                        >
                          {caseId.slice(0, 14)}…
                        </Link>
                      ) : "—"}
                    </td>
                    <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{l.created_at ? formatDateTime(l.created_at) : "—"}</td>
                    <td>
                      {l.short_url ? (
                        <a href={l.short_url} target="_blank" rel="noreferrer"
                          style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: "var(--accent-green)", fontSize: "0.8rem", fontWeight: 600, textDecoration: "none" }}>
                          Open <ExternalLink size={12} />
                        </a>
                      ) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
