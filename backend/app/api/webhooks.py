"""
Razorpay Webhook API — Phase 2, Step 7.

Endpoint: POST /api/webhooks/razorpay

Processing pipeline:
  1. Read raw body bytes (required for signature validation)
  2. Validate X-Razorpay-Signature using RAZORPAY_WEBHOOK_SECRET (400 if invalid)
  3. Parse body as JSON
  4. Extract razorpay_event_id — check for duplicate (200 duplicate if seen)
  5. Mark event as processed
  6. Route to handler in webhook_service.py
  7. Return 200 for all processed / ignored events

Rules:
  - HTTP 400 ONLY for invalid signatures
  - HTTP 200 for all business outcomes (success, no_case, ignored, duplicate)
  - Unknown event types are acknowledged, not errored
  - Handler always returns before agent completes (async task)
"""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.services.webhook_service import (
    handle_payment_authorized,
    handle_payment_captured,
    handle_payment_failed,
    handle_payment_link_failed,
    is_duplicate_event,
    mark_event_processed,
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("reclaimai.webhooks")


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """
    Receive and process Razorpay webhook events.
    Returns HTTP 200 for all business outcomes.
    Returns HTTP 400 only for invalid signatures.
    """
    # ── 1. Read raw body (must happen before any parsing) ─────────────────────
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # ── 2. Validate signature ──────────────────────────────────────────────────
    webhook_secret = settings.razorpay_webhook_secret
    if webhook_secret:
        expected = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            logger.warning("[Webhook] Invalid signature — rejecting request")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    else:
        logger.warning("[Webhook] No RAZORPAY_WEBHOOK_SECRET set — skipping signature validation (dev mode)")

    # ── 3. Parse JSON ──────────────────────────────────────────────────────────
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event     = payload.get("event", "")
    event_id  = payload.get("id", "")

    # ── 4. Deduplication check ─────────────────────────────────────────────────
    if event_id and await is_duplicate_event(event_id):
        logger.info(f"[Webhook] Duplicate event {event_id} — skipping")
        return {"status": "duplicate", "event": event, "event_id": event_id}

    # ── 5. Mark as processed (idempotency) ────────────────────────────────────
    if event_id:
        await mark_event_processed(event_id, event)

    # ── 6. Route to handler ───────────────────────────────────────────────────
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    link_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})

    try:
        if event == "payment.failed":
            result = await handle_payment_failed(payment_entity, event_id)
        elif event == "payment.captured":
            result = await handle_payment_captured(payment_entity, event_id)
        elif event == "payment.authorized":
            result = await handle_payment_authorized(payment_entity, event_id)
        elif event in ["payment_link.cancelled", "payment_link.expired"]:
            result = await handle_payment_link_failed(link_entity, event_id)
        else:
            logger.info(f"[Webhook] Unhandled event type: {event}")
            return {"status": "ignored", "event": event}
    except Exception as e:
        # Return 200 to prevent Razorpay retries — log the error for investigation
        logger.error(f"[Webhook] Handler error for event {event} ({event_id}): {e}", exc_info=True)
        return {"status": "error", "event": event, "detail": str(e)}

    # ── 7. Return 200 ─────────────────────────────────────────────────────────
    return {"status": "processed", "event": event, **result}
