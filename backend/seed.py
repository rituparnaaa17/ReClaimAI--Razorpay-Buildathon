"""
Supabase Seeder — populates the database with realistic mock data for demo/testing.
Run once: python seed.py
"""
import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from supabase import create_client

# ── Config ─────────────────────────────────────────────────────────────────
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.config import get_settings

settings = get_settings()
sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

# ── Data ────────────────────────────────────────────────────────────────────
MERCHANTS = [
    {"id": str(uuid.uuid4()), "name": "TechGadgets India", "email": "admin@techgadgets.in", "business_type": "E-commerce"},
]

CUSTOMERS = [
    "Arjun Sharma", "Priya Patel", "Rahul Gupta", "Sneha Mehta",
    "Vikram Singh", "Ananya Reddy", "Karthik Iyer", "Divya Nair",
    "Suresh Kumar", "Pooja Joshi", "Amit Verma", "Nisha Agarwal",
]

FAILURE_REASONS = ["UPI_TIMEOUT", "BANK_DECLINE", "INSUFFICIENT_BALANCE", "EXPIRED_CARD", "TECHNICAL_FAILURE", "ABANDONED", "SUBSCRIPTION_FAILURE"]
PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET", "EMI"]
STATUSES = ["recovered", "at_risk", "processing", "failed", "human_review"]
ACTIONS = ["Smart Retry", "Personalized Reminder", "Alt. Payment Method", "Card Update Request"]

RECOVERY_PROB = {
    "UPI_TIMEOUT": 0.87, "BANK_DECLINE": 0.55, "INSUFFICIENT_BALANCE": 0.42,
    "EXPIRED_CARD": 0.38, "TECHNICAL_FAILURE": 0.81, "ABANDONED": 0.68, "SUBSCRIPTION_FAILURE": 0.61,
}

ROOT_CAUSES = {
    "UPI_TIMEOUT": "Temporary UPI network congestion caused session expiry before payment confirmation.",
    "BANK_DECLINE": "Issuing bank rejected due to risk scoring or daily transaction limit breach.",
    "INSUFFICIENT_BALANCE": "Customer account had insufficient funds at time of debit attempt.",
    "EXPIRED_CARD": "Card expiry date in payment token does not match bank records.",
    "TECHNICAL_FAILURE": "Gateway-side technical error — not customer-initiated.",
    "ABANDONED": "Customer reached payment page but did not complete checkout flow.",
    "SUBSCRIPTION_FAILURE": "Recurring mandate debit failed — mandate may be paused or cancelled.",
}


def rand_date(days_back: int = 30) -> str:
    dt = datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return dt.isoformat()


def seed_merchants():
    print("Seeding merchants...")
    for m in MERCHANTS:
        try:
            sb.table("merchants").upsert(m).execute()
        except Exception as e:
            print(f"  Merchant error: {e}")
    print(f"  ✓ {len(MERCHANTS)} merchants")
    return MERCHANTS[0]["id"]


def seed_customers(merchant_id: str) -> list:
    print("Seeding customers...")
    customers = []
    for name in CUSTOMERS:
        cid = str(uuid.uuid4())
        total = random.randint(5, 40)
        success = random.randint(int(total * 0.7), total)
        failed = total - success
        spent = random.randint(5000, 200000)
        customers.append({
            "id": cid,
            "merchant_id": merchant_id,
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "total_transactions": total,
            "successful_transactions": success,
            "failed_transactions": failed,
            "total_spent": spent,
            "average_transaction_value": spent // total,
        })
    try:
        sb.table("customers").upsert(customers).execute()
        print(f"  ✓ {len(customers)} customers")
    except Exception as e:
        print(f"  Customer error: {e}")
    return customers


def seed_transactions(merchant_id: str, customers: list) -> list:
    print("Seeding transactions...")
    transactions = []
    for i in range(60):
        customer = random.choice(customers)
        failure = random.choice(FAILURE_REASONS)
        method = random.choice(PAYMENT_METHODS)
        status = "failed" if i < 40 else ("abandoned" if i < 50 else "success")
        amount = round(random.uniform(299, 49999), 2)

        transactions.append({
            "id": str(uuid.uuid4()),
            "merchant_id": merchant_id,
            "customer_id": customer["id"],
            "razorpay_payment_id": f"pay_test_{uuid.uuid4().hex[:14]}",
            "amount": amount,
            "currency": "INR",
            "payment_method": method,
            "status": status,
            "failure_reason": failure if status != "success" else None,
            "created_at": rand_date(30),
        })

    try:
        sb.table("transactions").upsert(transactions).execute()
        print(f"  ✓ {len(transactions)} transactions")
    except Exception as e:
        print(f"  Transaction error: {e}")
    return transactions


def seed_recovery_cases(merchant_id: str, transactions: list, customers: list) -> list:
    print("Seeding recovery cases...")
    cases = []
    failed_txns = [t for t in transactions if t["status"] in ("failed", "abandoned")]

    for txn in failed_txns[:30]:
        failure = txn["failure_reason"] or "UPI_TIMEOUT"
        prob = RECOVERY_PROB.get(failure, 0.5) + random.uniform(-0.1, 0.1)
        prob = max(0.1, min(0.97, prob))
        status = random.choice(STATUSES)
        action = ACTIONS[list(FAILURE_REASONS).index(failure) % len(ACTIONS)]
        customer = next((c for c in customers if c["id"] == txn["customer_id"]), customers[0])

        case = {
            "id": str(uuid.uuid4()),
            "transaction_id": txn["id"],
            "merchant_id": merchant_id,
            "risk_score": round(1.0 - prob, 3),
            "recovery_probability": round(prob, 3),
            "root_cause": ROOT_CAUSES.get(failure, "Unknown"),
            "recommended_action": action,
            "action_taken": action if status in ("recovered", "failed") else None,
            "status": status,
            "amount_at_risk": txn["amount"],
            "amount_recovered": txn["amount"] if status == "recovered" else None,
            "ai_reasoning": f"Based on {failure.replace('_', ' ').lower()} pattern, a {action.lower()} has {int(prob*100)}% probability of recovering ₹{txn['amount']:,.0f}.",
            "retry_count": random.randint(0, 2) if status == "failed" else 0,
            "guardrail_passed": txn["amount"] <= 50000 and prob >= 0.3,
            "created_at": txn["created_at"],
            "updated_at": rand_date(5),
            # Flatten customer fields for easy display
            "customer_name": customer["name"],
            "customer_email": customer["email"],
            "payment_method": txn["payment_method"],
            "failure_reason": failure,
            "razorpay_payment_id": txn["razorpay_payment_id"],
        }
        cases.append(case)

    try:
        sb.table("recovery_cases").upsert(cases).execute()
        print(f"  ✓ {len(cases)} recovery cases")
    except Exception as e:
        print(f"  Recovery case error: {e}")
    return cases


def seed_agent_logs(cases: list):
    print("Seeding agent logs...")
    logs = []
    STEPS = [
        ("DETECT", "Payment failure detected", "Webhook received from Razorpay", 0.99),
        ("DIAGNOSE", "Root cause identified", "Gateway error code analyzed", 0.93),
        ("PREDICT", "Recovery probability calculated", "ML model prediction", 0.88),
        ("DECIDE", "Recovery strategy selected", "Gemini AI decision", 0.91),
        ("GUARDRAIL", "Policy validation passed", "All safety checks passed", 0.99),
        ("EXECUTE", "Action executed", "Razorpay API call made", 0.94),
        ("VERIFY", "Outcome verified", "Payment status confirmed", 0.97),
    ]

    for case in cases[:15]:
        base_time = datetime.fromisoformat(case["created_at"].replace("Z", "+00:00"))
        num_steps = 7 if case["status"] in ("recovered", "failed") else random.randint(3, 6)

        for i, (step, decision, reason, conf) in enumerate(STEPS[:num_steps]):
            result = "success" if step != "VERIFY" or case["status"] == "recovered" else "failed"
            if step == "GUARDRAIL" and not case["guardrail_passed"]:
                result = "blocked"

            logs.append({
                "id": str(uuid.uuid4()),
                "recovery_case_id": case["id"],
                "step": step,
                "decision": f"{decision}: {case.get('failure_reason', '')}",
                "reason": reason,
                "confidence": conf + random.uniform(-0.05, 0.05),
                "timestamp": (base_time + timedelta(seconds=i * 45 + random.randint(0, 30))).isoformat(),
                "result": result,
            })

    try:
        sb.table("agent_logs").upsert(logs).execute()
        print(f"  ✓ {len(logs)} agent logs")
    except Exception as e:
        print(f"  Agent log error: {e}")


def main():
    print("\n[*] ReclaimAI -- Seeding Supabase\n")
    merchant_id = seed_merchants()
    customers = seed_customers(merchant_id)
    transactions = seed_transactions(merchant_id, customers)
    cases = seed_recovery_cases(merchant_id, transactions, customers)
    seed_agent_logs(cases)
    print("\n[OK] Seeding complete! ReclaimAI database is ready.\n")


if __name__ == "__main__":
    main()
