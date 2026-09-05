"""
Payment Links API — create and list Razorpay payment links aligned with recovery cases.

POST /api/payment-links          → create a new payment link (optionally tied to a recovery case)
GET  /api/payment-links          → list all payment links from Razorpay
GET  /api/payment-links/{id}     → fetch a single payment link
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import razorpay
from datetime import datetime, timezone

from app.config import get_settings
from app.services.razorpay_service import get_razorpay_client
from app.services.db_service import db_get_recovery_case

router = APIRouter()
settings = get_settings()


class CreatePaymentLinkRequest(BaseModel):
    amount: float                         # rupees
    customer_name: str
    customer_email: str
    customer_contact: Optional[str] = None
    description: Optional[str] = "ReclaimAI — Complete your payment"
    case_id: Optional[str] = None         # tie to a recovery case


@router.post("")
async def create_payment_link(body: CreatePaymentLinkRequest):
    """
    Create a real Razorpay payment link.
    If case_id is provided, the link is tagged to that recovery case.
    """
    client = get_razorpay_client()
    amount_paise = int(body.amount * 100)

    customer: dict = {"name": body.customer_name, "email": body.customer_email}
    if body.customer_contact:
        customer["contact"] = body.customer_contact

    notes: dict = {}
    if body.case_id:
        case = await db_get_recovery_case(body.case_id)
        if case:
            notes["recovery_case_id"] = body.case_id
            notes["failure_reason"] = case.get("failure_reason", "")
            notes["original_amount"] = str(case.get("amount_at_risk", ""))

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": body.description,
        "customer": customer,
        "notify": {"sms": False, "email": bool(body.customer_email)},
        "reminder_enable": True,
        "notes": notes,
        "callback_url": f"{settings.frontend_url}/payment/success",
        "callback_method": "get",
    }

    try:
        link = client.payment_link.create(payload)
        return {
            "id": link["id"],
            "short_url": link["short_url"],
            "amount": body.amount,
            "amount_paise": amount_paise,
            "status": link.get("status", "created"),
            "customer_name": body.customer_name,
            "customer_email": body.customer_email,
            "description": body.description,
            "case_id": body.case_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Razorpay error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_payment_links(count: int = 20):
    """List recent Razorpay payment links."""
    client = get_razorpay_client()
    try:
        result = client.payment_link.all({"count": count})
        items = result.get("items", [])
        return [
            {
                "id": lnk["id"],
                "short_url": lnk.get("short_url", ""),
                "amount": lnk.get("amount", 0) / 100,
                "amount_paise": lnk.get("amount", 0),
                "status": lnk.get("status", ""),
                "description": lnk.get("description", ""),
                "customer_name": lnk.get("customer", {}).get("name", ""),
                "customer_email": lnk.get("customer", {}).get("email", ""),
                "created_at": (
                    datetime.fromtimestamp(lnk["created_at"], tz=timezone.utc).isoformat()
                    if lnk.get("created_at") else None
                ),
                "payments_count": lnk.get("payments_count", 0),
                "notes": lnk.get("notes", {}),
            }
            for lnk in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{link_id}")
async def get_payment_link(link_id: str):
    """Fetch a single Razorpay payment link by ID."""
    client = get_razorpay_client()
    try:
        lnk = client.payment_link.fetch(link_id)
        return {
            "id": lnk["id"],
            "short_url": lnk.get("short_url", ""),
            "amount": lnk.get("amount", 0) / 100,
            "status": lnk.get("status", ""),
            "description": lnk.get("description", ""),
            "customer": lnk.get("customer", {}),
            "notes": lnk.get("notes", {}),
            "payments": lnk.get("payments", []),
            "created_at": (
                datetime.fromtimestamp(lnk["created_at"], tz=timezone.utc).isoformat()
                if lnk.get("created_at") else None
            ),
        }
    except razorpay.errors.BadRequestError:
        raise HTTPException(status_code=404, detail="Payment link not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
