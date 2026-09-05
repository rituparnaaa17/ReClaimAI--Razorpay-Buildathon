"""
webhook_service.py — Business logic for Razorpay webhook events.

Handlers:
  - handle_payment_failed   → creates recovery case, triggers agent async
  - handle_payment_captured → transitions to recovered, measures amount
  - handle_payment_authorized → transitions to verifying

Helpers (exported for testing):
  - is_duplicate_event
  - mark_event_processed
  - _paise_to_rupees
  - _map_failure_reason
  - _find_case_for_payment
  - _resolve_merchant_id
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from app.config import get_settings
from app.services.db_service import (
    db_create_recovery_case,
    db_get_recovery_cases,
    db_update_recovery_case,
)
from app.services.measurement import measure_recovered_amount
from app.services.state_machine import RecoveryStateMachine, InvalidTransitionError
from app.services.supabase_client import get_supabase

settings = get_settings()
logger = logging.getLogger("reclaimai.webhooks")


# ── Amount helpers ─────────────────────────────────────────────────────────────

def _paise_to_rupees(paise: int) -> Decimal:
    """Convert integer paise to exact Decimal rupees. No float arithmetic."""
    rupees = Decimal(paise // 100)
    remainder = Decimal(paise % 100)
    return rupees + remainder / Decimal(100)


# ── Failure reason mapping ─────────────────────────────────────────────────────

_FAILURE_MAP: Dict[str, Dict[str, str]] = {
    "GATEWAY_ERROR": {"__default__": "TECHNICAL_FAILURE"},
    "SERVER_ERROR":  {"__default__": "TECHNICAL_FAILURE"},
    "BAD_REQUEST_ERROR": {
        "insufficient_funds": "INSUFFICIENT_BALANCE",
        "invalid_card":       "EXPIRED_CARD",
        "expired_card":       "EXPIRED_CARD",
        "payment_timeout":    "UPI_TIMEOUT",
        "upi_timeout":        "UPI_TIMEOUT",
        "__default__":        "BANK_DECLINE",
    },
}


def _map_failure_reason(error_code: Optional[str], error_description: Optional[str]) -> str:
    if not error_code:
        return "BANK_DECLINE"
    code_map = _FAILURE_MAP.get(error_code)
    if not code_map:
        return "BANK_DECLINE"
    desc_key = (error_description or "").lower().replace(" ", "_")
    return code_map.get(desc_key) or code_map.get("__default__", "BANK_DECLINE")


# ── Deduplication ──────────────────────────────────────────────────────────────

async def is_duplicate_event(event_id: str) -> bool:
    """Returns True if this event_id has already been processed."""
    try:
        sb = get_supabase()
        result = (
            sb.table("processed_webhook_events")
            .select("id")
            .eq("razorpay_event_id", event_id)
            .limit(1)
            .execute()
        )
        return bool(result.data)
    except Exception as e:
        logger.warning(f"[Webhook] Duplicate check failed for {event_id}: {e}")
        return False  # Fail-open: process the event, log the warning


async def mark_event_processed(event_id: str, event_type: str) -> None:
    """Persists event_id to deduplicate future retries."""
    try:
        sb = get_supabase()
        sb.table("processed_webhook_events").insert({
            "razorpay_event_id": event_id,
            "event_type": event_type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning(f"[Webhook] Failed to mark event {event_id} as processed: {e}")


# ── Case lookup ────────────────────────────────────────────────────────────────

async def _find_case_for_payment(payment: Dict[str, Any]) -> Optional[Dict]:
    """Find a recovery case using notes.recovery_case_id or razorpay_payment_id."""
    try:
        sb = get_supabase()
        
        # 1. Try to find by explicit recovery_case_id tagged in the payment link notes
        case_id = payment.get("notes", {}).get("recovery_case_id")
        if case_id:
            result = sb.table("recovery_cases").select("*").eq("id", case_id).limit(1).execute()
            if result.data:
                return result.data[0]
                
        # 2. Fallback to finding by original razorpay_payment_id
        payment_id = payment.get("id")
        if payment_id:
            result = sb.table("recovery_cases").select("*").eq("razorpay_payment_id", payment_id).limit(1).execute()
            if result.data:
                return result.data[0]

        # 3. Fallback to finding by razorpay_payment_link_id
        link_id = payment.get("payment_link_id")
        if link_id:
            result = sb.table("recovery_cases").select("*").eq("razorpay_payment_link_id", link_id).limit(1).execute()
            if result.data:
                return result.data[0]
                
    except Exception as e:
        logger.warning(f"[Webhook] _find_case_for_payment failed: {e}")
    return None


async def _resolve_merchant_id() -> Optional[str]:
    """Resolve the merchant ID. For MVP: returns the first merchant in DB."""
    try:
        cases = await db_get_recovery_cases()
        if cases:
            mid = cases[0].get("merchant_id")
            if mid:
                return mid
    except Exception:
        pass
    logger.warning("[Webhook] Could not resolve merchant_id — case will have merchant_id=None")
    return None


# ── Event handlers ─────────────────────────────────────────────────────────────

async def handle_payment_failed(payment: Dict[str, Any], event_id: str) -> Dict[str, Any]:
    """
    payment.failed → if for an existing recovery case (e.g. payment link attempt), update status to failed.
    Otherwise create a new recovery case and trigger the LangGraph agent.
    """
    payment_id    = payment.get("id", "")
    amount_paise  = int(payment.get("amount") or 0)
    amount_rupees = _paise_to_rupees(amount_paise)
    error_code    = payment.get("error_code")
    error_desc    = payment.get("error_description")
    failure_reason = _map_failure_reason(error_code, error_desc)

    # 1. Check if this payment failure belongs to an existing recovery case (e.g. payment link attempt)
    existing_case = await _find_case_for_payment(payment)
    if existing_case:
        case_id = existing_case["id"]
        terminal = {"recovered", "failed", "escalated", "no_action", "expired"}
        if existing_case.get("status") not in terminal:
            await RecoveryStateMachine.force_transition(
                case_id, "failed",
                reason=f"Razorpay webhook: payment.failed (payment_id={payment_id}, reason={failure_reason})",
                source="webhook",
            )
            await db_update_recovery_case(case_id, {"status": "failed"})
            logger.info(f"[Webhook] payment.failed → updated existing case {case_id} status to failed")
            return {
                "event": "payment.failed",
                "payment_id": payment_id,
                "case_id": case_id,
                "status": "failed",
                "updated_existing": True,
            }

    # 2. Otherwise create a new recovery case (fresh failure event)
    from app.agents.recovery_agent import run_recovery_agent  # lazy import
    merchant_id   = await _resolve_merchant_id()

    case_data = {
        "status":              "detected",
        "merchant_id":         merchant_id,
        "razorpay_payment_id": payment_id,
        "amount_at_risk":      float(amount_rupees),
        "failure_reason":      failure_reason,
        "payment_method":      (payment.get("method") or "UNKNOWN").upper(),
        "customer_email":      payment.get("email"),
        "customer_name":       payment.get("customer") or payment.get("email", "").split("@")[0] or "Unknown",
        "recovery_probability": 0.65,
        "retry_count":         0,
        "guardrail_passed":    False,
    }

    case_id = await db_create_recovery_case(case_data)
    logger.info(f"[Webhook] payment.failed → case {case_id} created (payment={payment_id}, ₹{amount_rupees})")

    if case_id:
        case_data["id"] = case_id
        asyncio.create_task(run_recovery_agent(case_data))
        logger.info(f"[Webhook] Recovery agent triggered for case {case_id}")

    return {
        "event":         "payment.failed",
        "payment_id":    payment_id,
        "case_id":       case_id,
        "amount_at_risk": float(amount_rupees),
        "failure_reason": failure_reason,
    }


async def handle_payment_captured(payment: Dict[str, Any], event_id: str) -> Dict[str, Any]:
    """
    payment.captured → find recovery case, force-transition to recovered, measure amount.
    This is an authoritative event — uses force_transition.
    """
    payment_id   = payment.get("id", "")
    amount_paise = int(payment.get("amount") or 0)
    amount_rupees = _paise_to_rupees(amount_paise)

    case = await _find_case_for_payment(payment)
    if not case:
        logger.info(f"[Webhook] payment.captured: no case for payment {payment_id} — ignoring")
        return {"event": "payment.captured", "payment_id": payment_id, "status": "no_case"}

    case_id      = case["id"]
    case_status  = case.get("status", "")

    # Skip terminal cases silently
    terminal = {"recovered", "failed", "escalated", "no_action", "expired"}
    if case_status in terminal:
        logger.info(f"[Webhook] payment.captured: case {case_id} already terminal ({case_status}), skipping")
        return {"event": "payment.captured", "payment_id": payment_id, "status": case_status}

    # Force-transition to recovered
    await RecoveryStateMachine.force_transition(
        case_id, "recovered",
        reason=f"Razorpay webhook: payment.captured (payment_id={payment_id})",
        source="webhook",
    )

    # Build a synthetic verify_result so measure_recovered_amount can work
    verify_result = {
        "status":           "recovered",
        "razorpay_status":  "captured",
        "payment_id":       payment_id,
        "razorpay_payment": {
            "id":     payment_id,
            "amount": amount_paise,
            "status": "captured",
        },
    }
    measurement = measure_recovered_amount(
        verification_result=verify_result,
        razorpay_payment=verify_result["razorpay_payment"],
    )

    updates: Dict[str, Any] = {"status": "recovered"}
    if measurement["status"] == "measured" and measurement["amount_rupees"] is not None:
        updates["amount_recovered"] = float(measurement["amount_rupees"])
        logger.info(f"[Webhook] payment.captured → case {case_id} recovered ₹{measurement['amount_rupees']}")

    await db_update_recovery_case(case_id, updates)

    return {
        "event":            "payment.captured",
        "payment_id":       payment_id,
        "case_id":          case_id,
        "status":           "recovered",
        "amount_recovered": float(amount_rupees),
    }


async def handle_payment_authorized(payment: Dict[str, Any], event_id: str) -> Dict[str, Any]:
    """
    payment.authorized → find recovery case, force-transition to verifying.
    Authorized ≠ captured; do NOT mark as recovered.
    """
    payment_id = payment.get("id", "")

    case = await _find_case_for_payment(payment)
    if not case:
        return {"event": "payment.authorized", "payment_id": payment_id, "status": "no_case"}

    case_id = case["id"]
    terminal = {"recovered", "failed", "escalated", "no_action", "expired"}
    if case.get("status") in terminal:
        return {"event": "payment.authorized", "payment_id": payment_id, "status": case["status"]}

    await RecoveryStateMachine.force_transition(
        case_id, "verifying",
        reason=f"Razorpay webhook: payment.authorized (payment_id={payment_id})",
        source="webhook",
    )

    return {
        "event":      "payment.authorized",
        "payment_id": payment_id,
        "case_id":    case_id,
        "status":     "verifying",
    }


async def handle_payment_link_failed(link_entity: Dict[str, Any], event_id: str) -> Dict[str, Any]:
    """
    payment_link.cancelled or payment_link.expired → find recovery case, force-transition to failed.
    """
    link_id = link_entity.get("id", "")
    
    # Check notes for recovery_case_id or lookup by razorpay_payment_link_id
    case_id = link_entity.get("notes", {}).get("recovery_case_id")
    case = None
    try:
        sb = get_supabase()
        if case_id:
            res = sb.table("recovery_cases").select("*").eq("id", case_id).limit(1).execute()
            if res.data:
                case = res.data[0]
        if not case and link_id:
            res = sb.table("recovery_cases").select("*").eq("razorpay_payment_link_id", link_id).limit(1).execute()
            if res.data:
                case = res.data[0]
    except Exception as e:
        logger.warning(f"[Webhook] Failed to lookup case for link {link_id}: {e}")
        return {"event": "payment_link.failed", "link_id": link_id, "status": "error"}

    if not case:
        logger.info(f"[Webhook] payment_link failed: no case found for link {link_id} — ignoring")
        return {"event": "payment_link.failed", "link_id": link_id, "status": "no_case"}

    case_id = case["id"]

    terminal = {"recovered", "failed", "escalated", "no_action", "expired"}
    if case.get("status") in terminal:
        return {"event": "payment_link.failed", "link_id": link_id, "status": case["status"]}

    await RecoveryStateMachine.force_transition(
        case_id, "failed",
        reason=f"Razorpay webhook: payment link failed/expired (link_id={link_id})",
        source="webhook",
    )

    return {
        "event":      "payment_link.failed",
        "link_id":    link_id,
        "case_id":    case_id,
        "status":     "failed",
    }
