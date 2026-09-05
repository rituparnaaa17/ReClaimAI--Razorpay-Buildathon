"""
Razorpay client service — handles payment retries, order creation, and payment links.
Uses the official razorpay Python SDK with test keys.
"""
import razorpay
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, TypedDict
from app.config import get_settings

settings = get_settings()


def get_razorpay_client() -> razorpay.Client:
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


async def create_payment_link(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Razorpay Payment Link for recovery.
    Sends a link to the customer to complete payment with an alternative method.
    """
    client = get_razorpay_client()
    amount_paise = int(case["amount_at_risk"] * 100)

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": f"ReclaimAI — Complete your pending payment",
        "customer": {
            "name": case.get("customer_name", "Customer"),
            "email": case.get("customer_email", ""),
        },
        "notify": {
            "sms": False,
            "email": bool(case.get("customer_email")),
        },
        "reminder_enable": True,
        "notes": {
            "recovery_case_id": case["id"],
            "original_failure_reason": case.get("failure_reason", ""),
        },
        "callback_url": f"{settings.frontend_url}/payment/callback",
        "callback_method": "get",
    }

    link = client.payment_link.create(payload)
    return {
        "success": True,
        "payment_link_id": link["id"],
        "payment_link_url": link["short_url"],
        "amount": case["amount_at_risk"],
    }


async def retry_payment(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a smart retry by fetching the original payment and checking its state.
    In production, this would trigger a UPI collect request or card retry.
    """
    try:
        client = get_razorpay_client()
        razorpay_payment_id = case.get("razorpay_payment_id", "")

        if razorpay_payment_id and razorpay_payment_id.startswith("pay_"):
            payment = client.payment.fetch(razorpay_payment_id)
            status = payment.get("status", "failed")
            return {
                "success": status == "captured",
                "razorpay_payment_id": razorpay_payment_id,
                "status": status,
            }
    except Exception as e:
        print(f"[Razorpay] retry_payment failed: {e}")

    return {
        "success": False,
        "razorpay_payment_id": None,
        "status": "failed",
        "error": "Standard checkout payments cannot be retried via API without customer interaction",
    }


async def fetch_payment(payment_id: str) -> Optional[Dict]:
    """Fetch a payment object from Razorpay."""
    try:
        client = get_razorpay_client()
        return dict(client.payment.fetch(payment_id))
    except Exception as e:
        print(f"[Razorpay] fetch_payment failed: {e}")
        return None

class ExecutionResult(TypedDict):
    status: str
    action_attempted: str
    razorpay_identifier: Optional[str]
    error_code: Optional[str]
    error_description: Optional[str]
    timestamp: str

async def execute_recovery(action: str, case: Dict[str, Any]) -> ExecutionResult:
    """
    The strict execution boundary. Attempts to map an approved AI action
    to a legitimate Razorpay Test Mode operation.
    """
    if not settings.is_test_mode:
        raise RuntimeError("Reclaim execution is restricted to Razorpay Test Mode only.")

    timestamp = datetime.now(timezone.utc).isoformat()
    
    if action in ["Alt. Payment Method", "Personalized Reminder", "Card Update Request"]:
        try:
            result = await create_payment_link(case)
            return {
                "status": "executed",
                "action_attempted": action,
                "razorpay_identifier": result.get("payment_link_id"),
                "error_code": None,
                "error_description": None,
                "timestamp": timestamp,
            }
        except razorpay.errors.BadRequestError as e:
            return {
                "status": "failed",
                "action_attempted": action,
                "razorpay_identifier": None,
                "error_code": "BAD_REQUEST",
                "error_description": str(e),
                "timestamp": timestamp,
            }
        except razorpay.errors.ServerError as e:
            return {
                "status": "failed",
                "action_attempted": action,
                "razorpay_identifier": None,
                "error_code": "SERVER_ERROR",
                "error_description": str(e),
                "timestamp": timestamp,
            }
        except Exception as e:
            return {
                "status": "failed",
                "action_attempted": action,
                "razorpay_identifier": None,
                "error_code": "UNEXPECTED_ERROR",
                "error_description": str(e),
                "timestamp": timestamp,
            }
    elif action == "Smart Retry":
        return {
            "status": "not_executable",
            "action_attempted": action,
            "razorpay_identifier": None,
            "error_code": None,
            "error_description": "Standard checkout payments cannot be retried via API without customer interaction",
            "timestamp": timestamp,
        }
    elif action in ["Delayed Retry", "Wait", "WAIT"]:
        return {
            "status": "skipped",
            "action_attempted": action,
            "razorpay_identifier": None,
            "error_code": None,
            "error_description": "Execution intentionally scheduled for later (skipped for now)",
            "timestamp": timestamp,
        }
    else:
        return {
            "status": "not_executable",
            "action_attempted": action,
            "razorpay_identifier": None,
            "error_code": None,
            "error_description": f"Unsupported action: {action}",
            "timestamp": timestamp,
        }

class VerificationResult(TypedDict):
    status: str
    razorpay_status: Optional[str]
    error_description: Optional[str]
    timestamp: str

async def verify_payment_status(case: Dict[str, Any]) -> VerificationResult:
    """
    Step 5 strict verification boundary.
    Fetches the current Razorpay payment state to determine authoritative business outcome.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    payment_id = case.get("razorpay_payment_id")
    
    if not payment_id or not payment_id.startswith("pay_"):
        return {
            "status": "verification_failed",
            "razorpay_status": None,
            "error_description": "Missing or invalid Razorpay payment identifier",
            "timestamp": timestamp
        }
        
    try:
        client = get_razorpay_client()
        payment = client.payment.fetch(payment_id)
        razorpay_status = payment.get("status")
        
        if razorpay_status == "captured":
            return {
                "status": "recovered",
                "razorpay_status": razorpay_status,
                "error_description": None,
                "timestamp": timestamp
            }
        else:
            return {
                "status": "not_recovered",
                "razorpay_status": razorpay_status,
                "error_description": f"Payment is currently in '{razorpay_status}' state",
                "timestamp": timestamp
            }
            
    except Exception as e:
        return {
            "status": "verification_failed",
            "razorpay_status": None,
            "error_description": str(e),
            "timestamp": timestamp
        }
