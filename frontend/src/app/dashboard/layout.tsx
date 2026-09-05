"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot, LayoutDashboard, FolderOpen, ArrowLeftRight,
  Activity, BarChart2, Users, Settings, LogOut, Bell, Link2,
} from "lucide-react";

const navItems = [
  { icon: LayoutDashboard, label: "Overview", href: "/dashboard" },
  { icon: FolderOpen, label: "Recovery Cases", href: "/dashboard/recovery-cases" },
  { icon: Link2, label: "Payment Links", href: "/dashboard/payment-links" },
  { icon: ArrowLeftRight, label: "Transactions", href: "/dashboard/transactions" },
  { icon: Activity, label: "AI Agent", href: "/dashboard/agent-activity" },
  { icon: BarChart2, label: "Analytics", href: "/dashboard/analytics" },
  { icon: Users, label: "Customers", href: "/dashboard/customers" },
  { icon: Settings, label: "Settings", href: "/dashboard/settings" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => setTime(new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }));
    update();
    const id = setInterval(update, 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-primary)" }}>
      {/* Sidebar */}
      <aside className="sidebar">
        {/* Logo */}
        <div style={{ padding: "0 20px 24px", borderBottom: "1px solid var(--border-subtle)", marginBottom: "12px" }}>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: "32px", height: "32px", borderRadius: "8px",
              background: "var(--accent-green)", display: "flex",
              alignItems: "center", justifyContent: "center",
            }}>
              <Bot size={18} color="#FFFFFF" strokeWidth={2.5} />
            </div>
            <span style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text-primary)" }}>ReclaimAI</span>
          </Link>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, paddingBottom: "16px" }}>
          {navItems.map(({ icon: Icon, label, href }) => {
            const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
            return (
              <Link key={href} href={href} className={`sidebar-link ${active ? "active" : ""}`}>
                <Icon size={16} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* AI Status */}
        <div style={{
          margin: "0 12px 16px",
          background: "var(--accent-green-dim)",
          border: "1px solid var(--border-green)",
          borderRadius: "12px",
          padding: "12px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
            <div className="ai-dot" style={{ width: "6px", height: "6px" }} />
            <span style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--accent-green)" }}>AI Agent Active</span>
          </div>
          <p style={{ fontSize: "0.7rem", color: "var(--accent-green-soft)" }}>Razorpay Test Mode</p>
        </div>

        {/* User */}
        <div style={{
          borderTop: "1px solid var(--border-subtle)",
          padding: "16px 20px 0",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}>
          <div style={{
            width: "32px", height: "32px", borderRadius: "8px",
            background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-green)",
          }}>
            M
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              Merchant
            </div>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>admin@store.com</div>
          </div>
          <Link href="/login" style={{ color: "var(--text-muted)", display: "flex" }}>
            <LogOut size={14} />
          </Link>
        </div>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Topbar */}
        <header style={{
          height: "60px", borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-secondary)",
          display: "flex", alignItems: "center", justifyContent: "flex-end",
          padding: "0 28px", gap: "16px", flexShrink: 0,
        }}>
          <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{time}</span>
          <button style={{
            width: "36px", height: "36px", borderRadius: "8px",
            background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--text-muted)", cursor: "pointer",
          }}>
            <Bell size={16} />
          </button>
          <div style={{
            width: "36px", height: "36px", borderRadius: "8px",
            background: "var(--accent-green-dim)", border: "1px solid var(--border-green)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.85rem", fontWeight: 700, color: "var(--accent-green)",
          }}>
            M
          </div>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, padding: "28px", overflowY: "auto" }}>
          {children}
        </main>
      </div>
    </div>
  );
}
