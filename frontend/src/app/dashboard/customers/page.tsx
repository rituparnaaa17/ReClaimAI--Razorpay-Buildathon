"use client";
export default function CustomersPage() {
  const customers = Array.from({ length: 20 }, (_, i) => ({
    id: `CUST_${100 + i}`,
    name: ["Arjun Sharma","Priya Patel","Rahul Gupta","Sneha Mehta","Vikram Singh","Ananya Reddy","Karthik Iyer","Divya Nair","Suresh Kumar","Pooja Joshi"][i % 10],
    email: `customer${i}@example.com`,
    total_transactions: Math.floor(Math.random() * 40 + 5),
    successful_transactions: Math.floor(Math.random() * 35 + 4),
    failed_transactions: Math.floor(Math.random() * 5),
    total_spent: Math.round(Math.random() * 180000 + 5000),
  }));

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "4px" }}>Customers</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{customers.length} customers with recovery history</p>
      </div>
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
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => {
              const rate = Math.round((c.successful_transactions / c.total_transactions) * 100);
              return (
                <tr key={c.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{
                        width: "32px", height: "32px", borderRadius: "8px",
                        background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-green)",
                      }}>
                        {c.name[0]}
                      </div>
                      <span style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.875rem" }}>{c.name}</span>
                    </div>
                  </td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{c.email}</td>
                  <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{c.total_transactions}</td>
                  <td style={{ color: "var(--accent-green)", fontWeight: 600 }}>{c.successful_transactions}</td>
                  <td style={{ color: c.failed_transactions > 0 ? "var(--error)" : "var(--text-muted)", fontWeight: 600 }}>{c.failed_transactions}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div className="progress-bar" style={{ width: "60px" }}>
                        <div className="progress-fill" style={{ width: `${rate}%` }} />
                      </div>
                      <span style={{ fontSize: "0.8rem", fontWeight: 600, color: rate > 80 ? "var(--accent-green)" : "var(--warning)" }}>{rate}%</span>
                    </div>
                  </td>
                  <td style={{ fontWeight: 700, color: "var(--text-primary)" }}>₹{c.total_spent.toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
