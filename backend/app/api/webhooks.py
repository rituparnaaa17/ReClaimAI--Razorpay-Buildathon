from fastapi import APIRouter, Request, HTTPException
from app.config import get_settings
import hmac, hashlib

router = APIRouter()
settings = get_settings()


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """
    Razorpay webhook handler.
    Verifies signature and processes payment events.
    """
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")

    if settings.razorpay_key_secret:
        expected = hmac.new(
            settings.razorpay_key_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event", "")

    # Handle payment events
    if event == "payment.failed":
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        print(f"[Webhook] Payment failed: {payment.get('id')} — ₹{payment.get('amount', 0) / 100}")
        # In production: trigger recovery case creation

    elif event == "payment.captured":
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        print(f"[Webhook] Payment captured: {payment.get('id')} — ₹{payment.get('amount', 0) / 100}")
        # In production: update recovery case status to recovered

    return {"status": "processed", "event": event}
