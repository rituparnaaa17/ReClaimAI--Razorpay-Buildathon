"use client";
import { CreditCard, ShoppingCart, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const problems = [
  {
    icon: CreditCard,
    title: "Failed Payments",
    description: "Customers want to pay, but something goes wrong — UPI timeouts, bank declines, expired cards. The revenue disappears silently.",
    amount: "₹8.2L",
    amountLabel: "lost per month on average",
    color: "var(--error)",
  },
  {
    icon: ShoppingCart,
    title: "Abandoned Checkout",
    description: "Customers fill their cart, reach the payment page, and then leave. Every abandoned checkout is recoverable revenue.",
    amount: "₹5.1L",
    amountLabel: "abandoned checkout value",
    color: "var(--warning)",
  },
  {
    icon: RefreshCw,
    title: "Failed Subscriptions",
    description: "Recurring revenue silently disappears when subscription payments fail. Without action, customers churn without even knowing.",
    amount: "₹3.8L",
    amountLabel: "subscription revenue at risk",
    color: "#805AD5",
  },
];

export default function ProblemSection() {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setVisible(true); observer.disconnect(); }
    }, { threshold: 0.2 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="section" id="product" ref={ref}>
      <div className="container">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "64px" }}>
          <div style={{
            display: "inline-block",
            background: "var(--error-dim)",
            border: "1px solid rgba(255,98,98,0.2)",
            borderRadius: "20px",
            padding: "5px 16px",
            marginBottom: "20px",
          }}>
            <span style={{ fontSize: "0.78rem", color: "var(--error)", fontWeight: 600, letterSpacing: "0.04em", textTransform: "uppercase" }}>
              The Problem
            </span>
          </div>
          <h2>Revenue doesn&apos;t disappear.<br />It slips through the cracks.</h2>
          <p style={{ maxWidth: "560px", margin: "16px auto 0", fontSize: "1.05rem" }}>
            Every failed payment, abandoned checkout, and missed subscription is revenue that can still be recovered — if you act fast enough with the right strategy.
          </p>
        </div>

        {/* Cards */}
        <div className="responsive-grid-1" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "24px" }}>
          {problems.map((problem, i) => {
            const Icon = problem.icon;
            return (
              <div
                key={problem.title}
                className="card"
                style={{
                  padding: "32px",
                  opacity: visible ? 1 : 0,
                  transform: visible ? "translateY(0)" : "translateY(30px)",
                  transition: `all 0.5s ease ${i * 0.15}s`,
                }}
              >
                {/* Icon */}
                <div style={{
                  width: "48px", height: "48px", borderRadius: "12px",
                  background: `${problem.color}18`,
                  border: `1px solid ${problem.color}30`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  marginBottom: "20px",
                }}>
                  <Icon size={22} color={problem.color} />
                </div>

                <h3 style={{ fontSize: "1.2rem", marginBottom: "12px" }}>{problem.title}</h3>
                <p style={{ fontSize: "0.875rem", lineHeight: 1.7, marginBottom: "24px" }}>
                  {problem.description}
                </p>

                {/* Amount */}
                <div style={{
                  borderTop: "1px solid var(--border-subtle)",
                  paddingTop: "20px",
                  display: "flex", alignItems: "baseline", gap: "8px",
                }}>
                  <span style={{ fontSize: "1.6rem", fontWeight: 800, color: problem.color, letterSpacing: "-0.02em" }}>
                    {problem.amount}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{problem.amountLabel}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
