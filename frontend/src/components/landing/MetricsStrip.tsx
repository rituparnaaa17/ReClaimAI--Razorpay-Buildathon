"use client";
import { useEffect, useRef, useState } from "react";

const metrics = [
  { value: 2540000, display: "₹25.4L", label: "Revenue at Risk", color: "var(--warning)" },
  { value: 1680000, display: "₹16.8L", label: "Revenue Recovered", color: "var(--accent-green)" },
  { value: 66.1, display: "66.1%", label: "Recovery Rate", color: "var(--accent-green-soft)" },
  { value: 2431, display: "2,431", label: "Cases Resolved", color: "var(--text-primary)" },
];

export default function MetricsStrip() {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setVisible(true); observer.disconnect(); }
    }, { threshold: 0.3 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} style={{
      borderTop: "1px solid var(--border-subtle)",
      borderBottom: "1px solid var(--border-subtle)",
      background: "rgba(255, 255, 255, 0.01)",
      padding: "40px 0",
      position: "relative",
    }}>
      <div className="container">
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "1px",
          background: "var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          overflow: "hidden",
          boxShadow: "0 20px 40px rgba(0,0,0,0.4)"
        }}>
          {metrics.map((m, i) => (
            <div
              key={m.label}
              style={{
                background: "var(--bg-secondary)",
                padding: "32px 24px",
                textAlign: "center",
                opacity: visible ? 1 : 0,
                transform: visible ? "translateY(0)" : "translateY(20px)",
                transition: `all 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${i * 0.1}s`,
              }}
            >
              <div style={{
                fontSize: "2.5rem",
                fontWeight: 800,
                color: m.color,
                letterSpacing: "-0.04em",
                lineHeight: 1,
                marginBottom: "12px",
                fontFamily: "var(--font-display)",
              }}>
                {m.display}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                {m.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
