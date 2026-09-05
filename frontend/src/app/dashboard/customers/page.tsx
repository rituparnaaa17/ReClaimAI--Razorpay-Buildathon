"use client";
import { useEffect, useState } from "react";
import { Users, TrendingUp, AlertTriangle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

type Customer = {
  id: string;
  name: string;
  email: string;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_spent: number;
  recovery_cases: number;
};

function deriveCustomers(transactions: Record<string, unknown>[], cases: Record<string, unknown>[]): Customer[] {
  const map = new Map<string, Customer>();

  for (const txn of transactions) {
    const email = (txn.customer_email as string) || (txn.email as string) || "unknown@example.com";
    const name = (txn.customer_name as string) || (txn.customer as string) || email.split("@")[0];
    const id = email;

    if (!map.has(id)) {
      map.set(id, {
        id,
        name,
        email,
        total_transactions: 0,
        successful_transactions: 0,
        failed_transactions: 0,
        total_spent: 0,
        recovery_cases: 0,
      });
    }

    const c = map.get(id)!;
    c.total_transactions += 1;
    const status = txn.status as string;
    if (status === "captured" || status === "success") {
      c.successful_transactions += 1;
      c.total_spent += Number(txn.amount || 0);
    } else if (status === "failed" || status === "abandoned") {
      c.failed_transactions += 1;
    }
  }

  for (const rc of cases) {
    const email = (rc.customer_email as string) || "";
    if (email && map.has(email)) {
      map.get(email)!.recovery_cases += 1;
    }
  }

  return Array.from(map.values()).sort((a, b) => b.total_spent - a.total_spent);
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [txns, cases] = await Promise.all([
          api.getTransactions() as Promise<Record<string, unknown>[]>,
          api.getRecoveryCases() as Promise<Record<string, unknown>[]>,
        ]);
        const derived = deriveCustomers(txns || [], cases || []);
        setCustomers(derived);
      } catch (e) {
        setError("Failed to load customer data.");
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "12px" }}>
        <Loader2 size={24} color="var(--accent-green)" style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>Loading customers...</span>
        <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "300px" }}>
        <div style={{ color: "var(--error)", fontSize: "0.875rem" }}>{error}</div>
      </div>
    );
  }

  const totalSpent = customers.reduce((s, c) => s + c.total_spent, 0);
  const totalFailed = customers.reduce((s, c) => s + c.failed_transactions, 0);
  const totalTxns = customers.reduce((s, c) => s + c.total_transactions, 0);
  const overallRate = totalTxns > 0 ? Math.round((customers.reduce((s, c) => s + c.successful_transactions, 0) / totalTxns) * 100) : 0;

  return (
    <div>
      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>

      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Customers</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {customers.length} unique customers · derived from live transaction data
          </p>
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" }}>
        {[
          { label: "Total Customers", value: customers.length, icon: Users, color: "var(--accent-green)" },
          { label: "Total Revenue", value: `₹${totalSpent.toLocaleString()}`, icon: TrendingUp, color: "#3366FF" },
          { label: "Failed Payments", value: totalFailed, icon: AlertTriangle, color: "var(--error)" },
          { label: "Overall Success Rate", value: `${overallRate}%`, icon: TrendingUp, color: overallRate > 80 ? "var(--accent-green)" : "var(--warning)" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card" style={{ padding: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <Icon size={16} color={color} />
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</span>
            </div>
            <div style={{ fontSize: "1.75rem", fontWeight: 800, color }}>{value}</div>
          </div>
        ))}
      </div>

      {customers.length === 0 ? (
        <div className="card" style={{ padding: "48px", textAlign: "center" }}>
          <Users size={40} color="var(--text-muted)" style={{ marginBottom: "16px" }} />
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            No customer data yet. Transactions will appear here once your Supabase DB has data.
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Email</th>
                <th>Total Txns</th>
                <th>Successful</th>
                <th>Failed</th>
                <th>Success Rate</th>
                <th>Total Spent</th>
                <th>Recovery Cases</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => {
                const rate = c.total_transactions > 0
                  ? Math.round((c.successful_transactions / c.total_transactions) * 100)
                  : 0;
                return (
                  <tr key={c.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div style={{
                          width: "32px", height: "32px", borderRadius: "8px",
                          background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-green)",
                          flexShrink: 0,
                        }}>
                          {c.name[0]?.toUpperCase()}
                        </div>
                        <span style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.875rem" }}>{c.name}</span>
                      </div>
                    </td>
                    <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{c.email}</td>
                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{c.total_transactions}</td>
                    <td style={{ color: "var(--accent-green)", fontWeight: 600 }}>{c.successful_transactions}</td>
                    <td style={{ color: c.failed_transactions > 0 ? "var(--error)" : "var(--text-muted)", fontWeight: 600 }}>
                      {c.failed_transactions}
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <div className="progress-bar" style={{ width: "60px" }}>
                          <div className="progress-fill" style={{ width: `${Math.min(rate, 100)}%` }} />
                        </div>
                        <span style={{ fontSize: "0.8rem", fontWeight: 600, color: rate > 80 ? "var(--accent-green)" : rate > 50 ? "var(--warning)" : "var(--error)" }}>
                          {rate}%
                        </span>
                      </div>
                    </td>
                    <td style={{ fontWeight: 700, color: "var(--text-primary)" }}>₹{c.total_spent.toLocaleString()}</td>
                    <td>
                      {c.recovery_cases > 0 ? (
                        <span style={{
                          fontSize: "0.72rem", fontWeight: 700,
                          background: "rgba(245,184,75,0.15)", color: "var(--warning)",
                          padding: "2px 8px", borderRadius: "6px"
                        }}>
                          {c.recovery_cases} case{c.recovery_cases > 1 ? "s" : ""}
                        </span>
                      ) : (
                        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>—</span>
                      )}
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
