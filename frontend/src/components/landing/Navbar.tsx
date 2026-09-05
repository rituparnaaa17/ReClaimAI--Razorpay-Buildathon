"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Shield, Menu, X } from "lucide-react";

const navLinks = [
  { label: "Platform Overview", href: "#" },
  { label: "Features", href: "#" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <nav className={`navbar ${scrolled ? "scrolled" : ""}`}>
      <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
        {/* Logo */}
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "30px", height: "30px", borderRadius: "8px",
            background: "linear-gradient(135deg, #2563EB 0%, #4F46E5 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 10px rgba(37, 99, 235, 0.4)"
          }}>
            <Shield size={16} color="#FFFFFF" strokeWidth={2.5} />
          </div>
          <span style={{ fontWeight: 800, fontSize: "1.15rem", color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
            ReclaimAI
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="navbar-desktop" style={{ display: "flex", alignItems: "center", gap: "32px" }}>
          {navLinks.map((link) => (
            <a key={link.label} href={link.href} style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 500, transition: "color 0.2s" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}>
              {link.label}
            </a>
          ))}
        </div>

        {/* CTA */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link href="/login" className="btn btn-ghost btn-sm" style={{ fontSize: "0.85rem" }}>
            Sign In
          </Link>
          <button
            className="navbar-mobile-btn btn btn-ghost"
            onClick={() => setMobileOpen(!mobileOpen)}
            style={{ display: "none" }}
            id="mobile-menu-btn"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div style={{
          position: "absolute", top: "72px", left: 0, right: 0,
          background: "var(--bg-secondary)",
          borderBottom: "1px solid var(--border-subtle)", padding: "20px 24px",
          display: "flex", flexDirection: "column", gap: "8px",
          boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
        }}>
          {navLinks.map((link) => (
            <a key={link.label} href={link.href} className="btn btn-ghost" onClick={() => setMobileOpen(false)}>
              {link.label}
            </a>
          ))}
          <Link href="/login" className="btn btn-primary" style={{ marginTop: "12px" }}>
            Sign In
          </Link>
        </div>
      )}
    </nav>
  );
}
