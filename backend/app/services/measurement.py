"""
Measurement Service — Phase 1, Step 6.

Measures VERIFIED GROSS RECOVERED MONEY only.

Rules:
  RULE 1: Only Razorpay status == "captured" produces recovered money.
  RULE 2: Payment Link creation does NOT count.
  RULE 3: execute_recovery() result "executed" does NOT count.
  RULE 4: AI prediction does NOT count.
  RULE 5: case.amount_at_risk does NOT automatically count.
  RULE 6: Only the actual verified Razorpay payment amount is used.
  RULE 7: No incremental revenue calculation.

Monetary precision:
  Razorpay returns amounts in paise (integer smallest unit).
  We convert to rupees using integer division: paise // 100.
  We store as Decimal(12,2) to match the existing schema convention.
  We never use float for persisted monetary values.

This module DOES NOT:
  - Execute payments
  - Create Payment Links
  - Perform AI reasoning
  - Change guardrails
  - Handle webhooks
  - Bypass the state machine
  - Calculate incremental revenue or attribution
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Optional, TypedDict


# ── Measurement Result Contract ───────────────────────────────────────────────

class MeasurementResult(TypedDict):
    """
    Structured result of a single case measurement.

    status values:
      "measured"       — payment confirmed captured; amount is authoritative
      "not_recovered"  — payment status is terminal but not captured
      "unavailable"    — verification failed or payment ID missing; no amount
    """
    status: str                     # "measured" | "not_recovered" | "unavailable"
    amount_rupees: Optional[Decimal]  # Exact rupee value; None if not measured
    amount_paise: Optional[int]     # Raw Razorpay paise value; None if not measured
    currency: Optional[str]         # "INR" or as returned by Razorpay
    payment_id: Optional[str]       # Razorpay pay_xxx identifier
    razorpay_status: Optional[str]  # Razorpay payment status at time of measurement
    timestamp: str                  # ISO 8601 UTC


# ── Measurement Boundary ──────────────────────────────────────────────────────

def measure_recovered_amount(
    verification_result: dict,
    razorpay_payment: Optional[dict],
) -> MeasurementResult:
    """
    The single bounded measurement operation.

    Args:
        verification_result:
            The VerificationResult dict from verify_payment_status().
            Must contain at least {"status": str}.

        razorpay_payment:
            The raw payment object returned by Razorpay client.payment.fetch().
            Must contain {"status": str, "amount": int, "currency": str}
            when status == "captured".
            Pass None if payment could not be fetched.

    Returns:
        MeasurementResult with all fields populated.

    CRITICAL: Only returns status="measured" when BOTH conditions hold:
        1. verification_result["status"] == "recovered"
           (which requires razorpay_status == "captured" per Step 5)
        2. razorpay_payment is not None and its amount is available

    In all other cases, no money is measured.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    verify_status = verification_result.get("status", "")

    # ── Guard 1: Only proceed if Step 5 already confirmed "recovered" ──────────
    # "recovered" from verify_payment_status() means razorpay_status == "captured"
    if verify_status != "recovered":
        return MeasurementResult(
            status="not_recovered",
            amount_rupees=None,
            amount_paise=None,
            currency=None,
            payment_id=None,
            razorpay_status=verification_result.get("razorpay_status"),
            timestamp=timestamp,
        )

    # ── Guard 2: Payment object must be available ──────────────────────────────
    if razorpay_payment is None:
        return MeasurementResult(
            status="unavailable",
            amount_rupees=None,
            amount_paise=None,
            currency=None,
            payment_id=None,
            razorpay_status=verification_result.get("razorpay_status"),
            timestamp=timestamp,
        )

    # ── Guard 3: Payment object must itself confirm "captured" ─────────────────
    # Double-check against the live object — never trust only the cached status.
    actual_status = razorpay_payment.get("status", "")
    if actual_status != "captured":
        return MeasurementResult(
            status="not_recovered",
            amount_rupees=None,
            amount_paise=None,
            currency=None,
            payment_id=razorpay_payment.get("id"),
            razorpay_status=actual_status,
            timestamp=timestamp,
        )

    # ── Extract authoritative amount from Razorpay ─────────────────────────────
    # Razorpay returns amount in paise (integer, smallest currency unit).
    # We use integer arithmetic exclusively; never float.
    raw_amount = razorpay_payment.get("amount")
    if raw_amount is None:
        return MeasurementResult(
            status="unavailable",
            amount_rupees=None,
            amount_paise=None,
            currency=razorpay_payment.get("currency"),
            payment_id=razorpay_payment.get("id"),
            razorpay_status=actual_status,
            timestamp=timestamp,
        )

    paise: int = int(raw_amount)  # Must be integer; guard against float input
    currency: str = razorpay_payment.get("currency", "INR")
    payment_id: str = razorpay_payment.get("id", "")

    # Convert paise → rupees using integer division, then wrap in Decimal for
    # exact representation. This matches the DECIMAL(12,2) schema column.
    rupees_int = paise // 100
    paise_remainder = paise % 100
    # Build exact Decimal from parts without going through float
    amount_rupees = Decimal(rupees_int) + Decimal(paise_remainder) / Decimal(100)
    amount_rupees = amount_rupees.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    return MeasurementResult(
        status="measured",
        amount_rupees=amount_rupees,
        amount_paise=paise,
        currency=currency,
        payment_id=payment_id,
        razorpay_status=actual_status,
        timestamp=timestamp,
    )


# ── Payment Link Protection ────────────────────────────────────────────────────

def is_payment_link(razorpay_identifier: Optional[str]) -> bool:
    """
    Returns True if the identifier is a Payment Link (plink_xxx),
    NOT a Payment (pay_xxx).

    A Payment Link being created is NOT recovery.
    Only pay_xxx with status==captured counts.
    """
    if not razorpay_identifier:
        return False
    return str(razorpay_identifier).startswith("plink_")


def is_payment_id(razorpay_identifier: Optional[str]) -> bool:
    """Returns True if the identifier is a real Razorpay payment (pay_xxx)."""
    if not razorpay_identifier:
        return False
    return str(razorpay_identifier).startswith("pay_")
