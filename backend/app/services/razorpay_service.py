"""
Razorpay client service — handles payment retries, order creation, and payment links.
Uses the official razorpay Python SDK with test keys.
"""
import razorpay
import asyncio
from typing import Dict, Any, Optional
from app.config import get_settings
import uuid

settings = get_settings()


def get_razorpay_client() -> razorpay.Client:
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


async def create_payment_link(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Razorpay Payment Link for recovery.
    Sends a link to the customer to complete payment with an alternative method.
    """
    try:
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
    except Exception as e:
        print(f"[Razorpay] create_payment_link failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "payment_link_url": f"https://razorpay.com/payment-link/demo_{case['id'][-8:]}",
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

    # Test mode simulation
    import random
    success = random.random() < case.get("recovery_probability", 0.5)
    return {
        "success": success,
        "razorpay_payment_id": f"pay_test_{str(uuid.uuid4())[:12]}",
        "status": "captured" if success else "failed",
        "simulated": True,
    }


async def fetch_payment(payment_id: str) -> Optional[Dict]:
    """Fetch a payment object from Razorpay."""
    try:
        client = get_razorpay_client()
        return dict(client.payment.fetch(payment_id))
    except Exception as e:
        print(f"[Razorpay] fetch_payment failed: {e}")
        return None
