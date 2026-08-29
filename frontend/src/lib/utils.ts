import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency = "INR"): string {
  if (currency === "INR") {
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
    if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
    return `₹${amount.toFixed(0)}`;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatCurrencyFull(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    recovered: "badge-recovered",
    at_risk: "badge-at-risk",
    failed: "badge-failed",
    processing: "badge-processing",
    human_review: "badge-human-review",
  };
  return map[status] ?? "badge-processing";
}

export function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    recovered: "Recovered",
    at_risk: "At Risk",
    failed: "Failed",
    processing: "Processing",
    human_review: "Human Review",
  };
  return map[status] ?? status;
}

export function getFailureLabel(reason: string): string {
  const map: Record<string, string> = {
    UPI_TIMEOUT: "UPI Timeout",
    BANK_DECLINE: "Bank Decline",
    INSUFFICIENT_BALANCE: "Insufficient Balance",
    EXPIRED_CARD: "Expired Card",
    TECHNICAL_FAILURE: "Technical Failure",
    ABANDONED: "Checkout Abandoned",
    SUBSCRIPTION_FAILURE: "Subscription Failure",
  };
  return map[reason] ?? reason;
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
