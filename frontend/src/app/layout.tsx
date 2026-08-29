import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ReclaimAI — Turn Failed Payments into Recovered Revenue",
  description:
    "ReclaimAI is an AI-powered revenue recovery platform that identifies failed payments, abandoned checkouts, and failed subscriptions, then autonomously recovers revenue using intelligent retry strategies.",
  keywords: ["revenue recovery", "AI payments", "failed payments", "Razorpay", "fintech"],
  openGraph: {
    title: "ReclaimAI — AI Revenue Recovery Platform",
    description: "Turn failed payments into recovered revenue with AI.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
