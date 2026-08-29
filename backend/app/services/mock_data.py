"""
Synthetic mock data for ReclaimAI — used when Supabase is not yet connected.
This gives the demo realistic data instantly.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid


FAILURE_REASONS = [
    "UPI_TIMEOUT", "BANK_DECLINE", "INSUFFICIENT_BALANCE",
    "EXPIRED_CARD", "TECHNICAL_FAILURE", "ABANDONED", "SUBSCRIPTION_FAILURE"
]

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET", "EMI"]

RECOVERY_ACTIONS = {
    "UPI_TIMEOUT": "Smart Retry",
    "BANK_DECLINE": "Alternative Payment Method",
    "INSUFFICIENT_BALANCE": "Personalized Reminder",
    "EXPIRED_CARD": "Card Update Request",
    "TECHNICAL_FAILURE": "Smart Retry",
    "ABANDONED": "Personalized Reminder",
    "SUBSCRIPTION_FAILURE": "Smart Retry + Notification",
}

CUSTOMER_NAMES = [
    "Arjun Sharma", "Priya Patel", "Rahul Gupta", "Sneha Mehta",
    "Vikram Singh", "Ananya Reddy", "Karthik Iyer", "Divya Nair",
    "Suresh Kumar", "Pooja Joshi", "Ravi Verma", "Neha Agarwal",
    "Amit Tiwari", "Sunita Rao", "Manoj Mishra", "Kavita Dubey",
]


def _random_date(days_back: int = 30) -> datetime:
    return datetime.now() - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def _recovery_probability(failure_reason: str, success_rate: float, retry_count: int) -> float:
    base = {
        "UPI_TIMEOUT": 0.88,
        "TECHNICAL_FAILURE": 0.82,
        "ABANDONED": 0.71,
        "SUBSCRIPTION_FAILURE": 0.75,
        "BANK_DECLINE": 0.55,
        "INSUFFICIENT_BALANCE": 0.40,
        "EXPIRED_CARD": 0.35,
    }.get(failure_reason, 0.60)

    prob = base * (0.5 + success_rate * 0.5) * (1.0 - retry_count * 0.15)
    return round(max(0.1, min(0.99, prob)), 2)


def generate_customers(n: int = 30) -> List[Dict[str, Any]]:
    customers = []
    for i in range(n):
        total = random.randint(5, 50)
        failed = random.randint(0, max(1, total // 8))
        customers.append({
            "id": f"CUST_{i+100:04d}",
            "name": random.choice(CUSTOMER_NAMES),
            "email": f"customer{i}@example.com",
            "total_transactions": total,
            "successful_transactions": total - failed,
            "failed_transactions": failed,
            "total_spent": round(random.uniform(5000, 200000), 2),
            "average_transaction_value": round(random.uniform(500, 15000), 2),
        })
    return customers


def generate_transactions(customers: List[Dict], n: int = 50) -> List[Dict[str, Any]]:
    transactions = []
    for i in range(n):
        customer = random.choice(customers)
        status = random.choices(
            ["success", "failed", "abandoned"],
            weights=[60, 28, 12]
        )[0]
        failure_reason = None
        if status in ("failed", "abandoned"):
            failure_reason = random.choice(FAILURE_REASONS)
            if status == "abandoned":
                failure_reason = "ABANDONED"

        amount = round(random.choices(
            [random.uniform(199, 1999), random.uniform(2000, 9999), random.uniform(10000, 50000)],
            weights=[50, 35, 15]
        )[0], 2)

        transactions.append({
            "id": f"TXN_{10000 + i:05d}",
            "merchant_id": "MERCHANT_001",
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "customer_email": customer["email"],
            "razorpay_payment_id": f"pay_{uuid.uuid4().hex[:16]}",
            "amount": amount,
            "currency": "INR",
            "payment_method": random.choice(PAYMENT_METHODS),
            "status": status,
            "failure_reason": failure_reason,
            "created_at": _random_date(30),
        })
    return transactions


def generate_recovery_cases(transactions: List[Dict]) -> List[Dict[str, Any]]:
    cases = []
    failed_txns = [t for t in transactions if t["status"] in ("failed", "abandoned")]

    for i, txn in enumerate(failed_txns):
        customer_success_rate = random.uniform(0.5, 1.0)
        retry_count = random.randint(0, 2)
        prob = _recovery_probability(txn["failure_reason"], customer_success_rate, retry_count)

        status = random.choices(
            ["at_risk", "processing", "recovered", "failed", "human_review"],
            weights=[20, 10, 50, 12, 8]
        )[0]

        amount_recovered = txn["amount"] if status == "recovered" else None

        created_at = txn["created_at"]
        updated_at = created_at + timedelta(minutes=random.randint(1, 30))

        cases.append({
            "id": f"RC_{10000 + i:05d}",
            "transaction_id": txn["id"],
            "merchant_id": txn["merchant_id"],
            "customer_name": txn["customer_name"],
            "customer_email": txn["customer_email"],
            "amount_at_risk": txn["amount"],
            "amount_recovered": amount_recovered,
            "risk_score": round(1.0 - prob + random.uniform(-0.05, 0.05), 2),
            "recovery_probability": prob,
            "root_cause": _root_cause_text(txn["failure_reason"]),
            "recommended_action": RECOVERY_ACTIONS.get(txn["failure_reason"], "Smart Retry"),
            "action_taken": RECOVERY_ACTIONS.get(txn["failure_reason"]) if status != "at_risk" else None,
            "status": status,
            "payment_method": txn["payment_method"],
            "failure_reason": txn["failure_reason"],
            "retry_count": retry_count,
            "ai_reasoning": _ai_reasoning(txn["failure_reason"], prob, customer_success_rate),
            "guardrail_passed": status != "human_review",
            "created_at": created_at,
            "updated_at": updated_at,
        })
    return cases


def _root_cause_text(failure_reason: str) -> str:
    texts = {
        "UPI_TIMEOUT": "Temporary UPI network timeout",
        "BANK_DECLINE": "Bank declined the transaction",
        "INSUFFICIENT_BALANCE": "Insufficient account balance",
        "EXPIRED_CARD": "Customer's card has expired",
        "TECHNICAL_FAILURE": "Temporary technical failure in payment gateway",
        "ABANDONED": "Customer abandoned checkout before completing payment",
        "SUBSCRIPTION_FAILURE": "Subscription renewal payment failed",
    }
    return texts.get(failure_reason, "Unknown failure reason")


def _ai_reasoning(failure_reason: str, prob: float, success_rate: float) -> str:
    histories = int(success_rate * 10)
    texts = {
        "UPI_TIMEOUT": f"The payment failed due to a temporary UPI network timeout. The customer has {histories} previous successful payments, indicating reliable payment behavior. A delayed retry after 5–10 minutes has a high probability of success.",
        "BANK_DECLINE": f"The bank declined this transaction. With a {int(prob*100)}% recovery probability, suggesting an alternative payment method (e.g., UPI or wallet) may be more effective than retrying the same method.",
        "INSUFFICIENT_BALANCE": f"Customer had insufficient balance at the time of payment. Sending a gentle reminder in 24–48 hours when funds may be available could recover this payment.",
        "EXPIRED_CARD": f"The customer's saved card has expired. A card update notification should be sent to allow them to update payment details and complete the transaction.",
        "TECHNICAL_FAILURE": f"A temporary gateway technical failure caused this payment to fail. An automatic retry should resolve this — the customer likely still intends to complete the purchase.",
        "ABANDONED": f"The customer started checkout but abandoned it. With {histories} previous successful transactions, a personalized reminder message has a strong chance of bringing them back.",
        "SUBSCRIPTION_FAILURE": f"Subscription renewal failed, likely due to a temporary issue. The customer has {histories} previous successful payments, making a smart retry the recommended approach.",
    }
    return texts.get(failure_reason, f"Recovery probability: {int(prob*100)}%. A recovery action is recommended.")


def generate_agent_logs(recovery_case: Dict) -> List[Dict[str, Any]]:
    base_time = recovery_case["created_at"]
    steps = [
        ("DETECT", "Payment failure detected and flagged for review", "Failure event received from payment gateway", 0.99),
        ("DIAGNOSE", f"Root cause identified: {recovery_case['failure_reason']}", recovery_case["root_cause"], 0.94),
        ("PREDICT", f"Recovery probability: {int(recovery_case['recovery_probability']*100)}%", "ML model prediction based on transaction features and customer history", recovery_case["recovery_probability"]),
        ("DECIDE", f"Action selected: {recovery_case['recommended_action']}", recovery_case["ai_reasoning"][:80] + "...", 0.91),
        ("GUARDRAIL", "Policy validation passed" if recovery_case["guardrail_passed"] else "Escalated for human review", "Retry count within limit. Amount below human approval threshold.", 0.99),
        ("EXECUTE", f"Executing: {recovery_case['recommended_action']}", "Recovery action initiated via Razorpay test mode", 0.95),
        ("VERIFY", "Recovery verified" if recovery_case["status"] == "recovered" else "Recovery pending verification", "Payment status confirmed via Razorpay API", 0.97),
    ]

    logs = []
    offset = 0
    for step_name, decision, reason, confidence in steps:
        if recovery_case["status"] == "at_risk" and step_name not in ("DETECT", "DIAGNOSE", "PREDICT"):
            break
        logs.append({
            "id": str(uuid.uuid4()),
            "recovery_case_id": recovery_case["id"],
            "step": step_name,
            "decision": decision,
            "reason": reason,
            "confidence": confidence,
            "timestamp": base_time + timedelta(seconds=offset),
            "result": "success" if recovery_case["status"] == "recovered" else "pending",
        })
        offset += random.randint(1, 3)
    return logs


# ─── Pre-generate data ─────────────────────────────────────────────────────────

_customers = generate_customers(40)
_transactions = generate_transactions(_customers, 80)
_recovery_cases = generate_recovery_cases(_transactions)
_agent_logs: Dict[str, List] = {
    case["id"]: generate_agent_logs(case) for case in _recovery_cases
}


def get_mock_transactions():
    return _transactions


def get_mock_recovery_cases():
    return _recovery_cases


def get_mock_recovery_case(case_id: str):
    return next((c for c in _recovery_cases if c["id"] == case_id), None)


def get_mock_agent_logs(case_id: str):
    return _agent_logs.get(case_id, [])


def get_mock_analytics():
    cases = _recovery_cases
    recovered = [c for c in cases if c["status"] == "recovered"]
    total_at_risk = sum(c["amount_at_risk"] for c in cases)
    total_recovered = sum(c["amount_at_risk"] for c in recovered)

    # Revenue trend (last 14 days)
    trend = []
    for i in range(14):
        day = datetime.now() - timedelta(days=13 - i)
        day_cases = [c for c in cases if c["created_at"].date() == day.date()]
        day_recovered = [c for c in day_cases if c["status"] == "recovered"]
        trend.append({
            "date": day.strftime("%b %d"),
            "at_risk": sum(c["amount_at_risk"] for c in day_cases),
            "recovered": sum(c["amount_at_risk"] for c in day_recovered),
        })

    # By failure reason
    reason_map: Dict[str, Dict] = {}
    for c in cases:
        r = c["failure_reason"] or "UNKNOWN"
        if r not in reason_map:
            reason_map[r] = {"reason": r, "total": 0, "recovered": 0}
        reason_map[r]["total"] += 1
        if c["status"] == "recovered":
            reason_map[r]["recovered"] += 1

    # By payment method
    method_map: Dict[str, Dict] = {}
    for t in _transactions:
        if t["status"] == "failed":
            m = t["payment_method"]
            if m not in method_map:
                method_map[m] = {"method": m, "failed": 0, "recovered": 0}
            method_map[m]["failed"] += 1
    for c in cases:
        m = c["payment_method"]
        if m in method_map and c["status"] == "recovered":
            method_map[m]["recovered"] += 1

    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0

    return {
        "overview": {
            "revenue_at_risk": round(total_at_risk, 2),
            "revenue_recovered": round(total_recovered, 2),
            "recovery_rate": round(recovery_rate, 1),
            "failed_payments": len([t for t in _transactions if t["status"] == "failed"]),
            "abandoned_checkouts": len([t for t in _transactions if t["status"] == "abandoned"]),
            "recovery_attempts": len([c for c in cases if c["status"] != "at_risk"]),
            "successful_recoveries": len(recovered),
            "avg_recovery_time_seconds": 287.4,
            "cases_by_status": {
                s: len([c for c in cases if c["status"] == s])
                for s in ["at_risk", "processing", "recovered", "failed", "human_review"]
            },
            "cases_by_failure_reason": {r: v["total"] for r, v in reason_map.items()},
            "cases_by_payment_method": {m: v["failed"] for m, v in method_map.items()},
        },
        "charts": {
            "revenue_trend": trend,
            "recovery_by_failure": list(reason_map.values()),
            "recovery_by_method": list(method_map.values()),
        }
    }
