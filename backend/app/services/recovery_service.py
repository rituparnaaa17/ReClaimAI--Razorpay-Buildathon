"""
Recovery Service — orchestrates AI analysis + Razorpay actions + DB writes.
Uses real Gemini, real Razorpay, and writes all results to Supabase.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from app.config import get_settings
from app.services.db_service import db_update_recovery_case, db_save_agent_log
from app.services.razorpay_service import create_payment_link, retry_payment
from app.services.gemini_client import generate_text

settings = get_settings()


async def analyze_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Full AI analysis: probability + root cause + strategy selection."""
    # Use Gemini if key is available
    reasoning = _default_reasoning(case)
    if settings.gemini_api_key:
        try:
            reasoning = await _gemini_analyze(case)
        except Exception as e:
            print(f"[Gemini] analyze_case failed: {e}")

    return {
        "case_id": case["id"],
        "recovery_probability": case.get("recovery_probability", 0.5),
        "root_cause": case.get("root_cause", "Unknown failure"),
        "recommended_action": case.get("recommended_action", "Smart Retry"),
        "ai_reasoning": reasoning,
        "guardrail_passed": _check_guardrails(case)["passed"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


async def execute_recovery_action(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the recovery strategy for a case:
    1. Check guardrails
    2. Execute via Razorpay (retry or payment link)
    3. Write result to Supabase
    """
    guardrail = _check_guardrails(case)

    if not guardrail["passed"]:
        await db_update_recovery_case(case["id"], {"status": "human_review"})
        return {
            "case_id": case["id"],
            "status": "human_review",
            "reason": guardrail["reason"],
            "amount_recovered": None,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    action = case.get("recommended_action", "Smart Retry")

    # Execute based on recommended action
    if action in ["Smart Retry", "Delayed Retry"]:
        result = await retry_payment(case)
    elif action in ["Personalized Reminder", "Alt. Payment Method", "Alternative Payment Method"]:
        result = await create_payment_link(case)
        result["success"] = True  # link created = action successful
    else:
        result = await retry_payment(case)

    # Determine final status
    if result.get("success"):
        new_status = "recovered"
        amount_recovered = case["amount_at_risk"]
    else:
        retry_count = case.get("retry_count", 0) + 1
        new_status = "failed" if retry_count >= 2 else "at_risk"
        amount_recovered = None

    # Write to Supabase
    updates: Dict[str, Any] = {
        "status": new_status,
        "action_taken": action,
        "retry_count": case.get("retry_count", 0) + 1,
    }
    if amount_recovered is not None:
        updates["amount_recovered"] = amount_recovered

    await db_update_recovery_case(case["id"], updates)

    return {
        "case_id": case["id"],
        "status": new_status,
        "action_taken": action,
        "amount_recovered": amount_recovered,
        "razorpay_result": result,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }


def _check_guardrails(case: Dict[str, Any]) -> Dict[str, Any]:
    """Safety guardrails — must pass before any automated action."""
    retry_count = case.get("retry_count", 0)
    amount = case.get("amount_at_risk", 0)
    prob = case.get("recovery_probability", 0)

    if retry_count >= 2:
        return {"passed": False, "reason": "Maximum retry limit (2) reached — escalating to human review"}
    if amount > 50000:
        return {"passed": False, "reason": f"Amount ₹{amount:,.0f} exceeds ₹50,000 threshold — human approval required"}
    if prob < 0.3:
        return {"passed": False, "reason": f"Recovery probability {int(prob*100)}% below minimum threshold — no action taken"}

    return {"passed": True, "reason": f"All guardrails passed · Retry {retry_count}/2 · ₹{amount:,.0f} within limit · {int(prob*100)}% probability"}


def _default_reasoning(case: Dict[str, Any]) -> str:
    failure_map = {
        "UPI_TIMEOUT": "The UPI network experienced a temporary timeout. This is a transient failure with high retry success rates.",
        "BANK_DECLINE": "The issuing bank declined this transaction. An alternative payment method or a retry after 24 hours is recommended.",
        "INSUFFICIENT_BALANCE": "The customer's account had insufficient funds at the time of payment. A reminder with a payment link is the best approach.",
        "EXPIRED_CARD": "The customer's card has expired. Requesting updated card details via a secure link is the recommended recovery action.",
        "TECHNICAL_FAILURE": "A technical failure occurred on the gateway side. A smart retry typically resolves this within minutes.",
        "ABANDONED": "The customer left before completing payment. A personalized reminder with a direct payment link has a high conversion rate.",
        "SUBSCRIPTION_FAILURE": "The subscription renewal payment failed. Updating the payment method and retrying is the recommended approach.",
    }
    return failure_map.get(case.get("failure_reason", ""), "Analysis pending. A smart retry is recommended as the first recovery attempt.")


async def _gemini_analyze(case: Dict[str, Any]) -> str:
    """Gemini AI root cause analysis and recovery recommendation."""
    prompt = f"""You are ReclaimAI, an expert AI revenue recovery analyst for Indian e-commerce and SaaS businesses.

Analyze this failed payment and provide a precise recovery recommendation:

Transaction Amount: ₹{case.get('amount_at_risk', 0):,.0f}
Failure Code: {case.get('failure_reason', 'UNKNOWN')}
Payment Method: {case.get('payment_method', 'Unknown')}
Recovery Probability: {int(case.get('recovery_probability', 0.5) * 100)}%
Root Cause: {case.get('root_cause', 'Unknown')}
Retry Count: {case.get('retry_count', 0)}/2

Provide a 2-3 sentence analysis covering:
1. Exactly why the payment failed
2. Why recovery is or isn't likely at this probability
3. The specific action you recommend and why

Use precise, financial-grade language. Be concise and actionable."""
    return await generate_text(prompt)
