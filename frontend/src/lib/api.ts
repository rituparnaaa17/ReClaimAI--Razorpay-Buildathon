const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Analytics
  getAnalytics: () => request<Record<string, unknown>>("/api/analytics/overview"),
  getCharts: () => request<Record<string, unknown>>("/api/analytics/charts"),
  getInsight: () => request<Record<string, unknown>>("/api/analytics/insight"),

  // Transactions
  getTransactions: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<unknown[]>(`/api/transactions${qs}`);
  },

  // Recovery Cases
  getRecoveryCases: (status?: string) => {
    const qs = status && status !== "all" ? `?status=${status}` : "";
    return request<unknown[]>(`/api/recovery/cases${qs}`);
  },
  getRecoveryCase: (id: string) =>
    request<Record<string, unknown>>(`/api/recovery/cases/${id}`),
  analyzeCase: (id: string) =>
    request<Record<string, unknown>>(`/api/recovery/analyze/${id}`, { method: "POST" }),
  executeRecovery: (id: string) =>
    request<Record<string, unknown>>(`/api/recovery/execute/${id}`, { method: "POST" }),

  // Agent
  runAgent: (caseId: string) =>
    request<Record<string, unknown>>(`/api/agent/run/${caseId}`, { method: "POST" }),
  getAgentLogs: (caseId: string) =>
    request<unknown[]>(`/api/agent/logs/${caseId}`),
  getAllAgentLogs: () =>
    request<unknown[]>("/api/agent/logs"),
};
