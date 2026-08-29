from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# ─── Auth ───────────────────────────────────────────────────────────────────

class MerchantLogin(BaseModel):
    email: str
    password: str


class MerchantOut(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    business_type: Optional[str] = None


# ─── Transactions ────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id: str
    merchant_id: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    payment_method: str
    status: Literal["success", "failed", "pending", "abandoned"]
    failure_reason: Optional[str] = None
    created_at: datetime


# ─── Recovery Cases ──────────────────────────────────────────────────────────

class RecoveryCaseOut(BaseModel):
    id: str
    transaction_id: str
    merchant_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    amount_at_risk: float
    amount_recovered: Optional[float] = None
    risk_score: float
    recovery_probability: float
    root_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    action_taken: Optional[str] = None
    status: Literal["at_risk", "processing", "recovered", "failed", "human_review"]
    payment_method: str
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RecoveryCaseDetail(RecoveryCaseOut):
    ai_reasoning: Optional[str] = None
    guardrail_passed: Optional[bool] = None
    retry_count: int = 0
    agent_logs: list = []


class ExecuteRecoveryRequest(BaseModel):
    case_id: str
    action: Optional[str] = None


# ─── Agent Logs ──────────────────────────────────────────────────────────────

class AgentLogOut(BaseModel):
    id: str
    recovery_case_id: str
    step: str
    decision: str
    reason: str
    confidence: float
    timestamp: datetime
    result: Optional[str] = None


# ─── Analytics ───────────────────────────────────────────────────────────────

class AnalyticsOverview(BaseModel):
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    failed_payments: int
    abandoned_checkouts: int
    recovery_attempts: int
    successful_recoveries: int
    avg_recovery_time_seconds: float
    cases_by_status: dict
    cases_by_failure_reason: dict
    cases_by_payment_method: dict


class RevenueDataPoint(BaseModel):
    date: str
    at_risk: float
    recovered: float


class AnalyticsCharts(BaseModel):
    revenue_trend: list[RevenueDataPoint]
    recovery_by_failure: list[dict]
    recovery_by_method: list[dict]
    recovery_success_rate: list[dict]


# ─── AI Insight ──────────────────────────────────────────────────────────────

class AIInsight(BaseModel):
    title: str
    insight: str
    affected_cases: int
    recommendation: str
