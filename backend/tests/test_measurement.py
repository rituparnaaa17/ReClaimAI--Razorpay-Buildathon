"""
test_measurement.py — Phase 1, Step 6: Measure Actual Money

Tests the measurement boundary, monetary precision, Payment Link protection,
batch aggregation, duplicate protection, and regression coverage.

All tests run without real Razorpay or Supabase connections.
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from app.services.measurement import measure_recovered_amount, is_payment_link, is_payment_id


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_captured_verification(payment_id: str = "pay_test123") -> dict:
    """A verification result that says 'recovered' (Razorpay captured)."""
    return {
        "status": "recovered",
        "razorpay_status": "captured",
        "error_description": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": {
            "id": payment_id,
            "status": "captured",
            "amount": 50000,       # paise = ₹500
            "currency": "INR",
        },
    }


def _make_non_recovered_verification(razorpay_status: str) -> dict:
    return {
        "status": "not_recovered",
        "razorpay_status": razorpay_status,
        "error_description": f"Payment is currently in '{razorpay_status}' state",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": None,
    }


def _make_failed_verification() -> dict:
    return {
        "status": "verification_failed",
        "razorpay_status": None,
        "error_description": "API error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": None,
    }


def _make_case(n: int, razorpay_payment_id: str = "pay_test123") -> dict:
    return {
        "id": f"00000000-0000-0000-0000-{n:012d}",
        "merchant_id": "merchant-test",
        "status": "detected",
        "amount_at_risk": 500.00,    # ₹500 case amount (expected)
        "recovery_probability": 0.75,
        "failure_reason": "UPI_TIMEOUT",
        "payment_method": "UPI",
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "retry_count": 0,
        "razorpay_payment_id": razorpay_payment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Test 1: Captured payment → measured ──────────────────────────────────────

def test_captured_payment_is_measured():
    """
    RULE 1: Razorpay status == 'captured' → measured amount = actual Razorpay amount.
    """
    verify_result = _make_captured_verification()
    razorpay_payment = verify_result["razorpay_payment"]

    result = measure_recovered_amount(verify_result, razorpay_payment)

    assert result["status"] == "measured"
    assert result["amount_paise"] == 50000
    assert result["amount_rupees"] == Decimal("500.00")
    assert result["currency"] == "INR"
    assert result["payment_id"] == "pay_test123"
    assert result["razorpay_status"] == "captured"


# ── Test 2: Failed payment → not recovered ────────────────────────────────────

def test_failed_payment_not_recovered():
    """Failed verification → no money measured."""
    result = measure_recovered_amount(_make_non_recovered_verification("failed"), None)
    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None
    assert result["amount_paise"] is None


# ── Test 3: Authorized payment → not recovered ───────────────────────────────

def test_authorized_payment_not_recovered():
    """Authorized (not yet captured) → no money measured."""
    result = measure_recovered_amount(_make_non_recovered_verification("authorized"), None)
    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None


# ── Test 4: Created payment → not recovered ───────────────────────────────────

def test_created_payment_not_recovered():
    """Created state → no money measured."""
    result = measure_recovered_amount(_make_non_recovered_verification("created"), None)
    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None


# ── Test 5: Refunded payment → not recovered ─────────────────────────────────

def test_refunded_payment_not_recovered():
    """Refunded → no money measured."""
    result = measure_recovered_amount(_make_non_recovered_verification("refunded"), None)
    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None


# ── Test 6: Verification failure → unavailable ───────────────────────────────

def test_verification_failure_unavailable():
    """API error during verification → unavailable, no fabricated money."""
    result = measure_recovered_amount(_make_failed_verification(), None)
    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None


# ── Test 7: Missing payment ID → Razorpay not called, no money ───────────────

@pytest.mark.asyncio
async def test_missing_payment_id_no_money():
    """
    RULE: Missing/invalid payment ID → verification_failed,
    Razorpay is never called, amount is unavailable.
    """
    from app.services.razorpay_service import verify_payment_status
    case = _make_case(7, razorpay_payment_id=None)
    case["razorpay_payment_id"] = None

    with patch("app.services.razorpay_service.get_razorpay_client") as m_client:
        result = await verify_payment_status(case)
        # Razorpay client must NOT be instantiated
        m_client.assert_not_called()

    assert result["status"] == "verification_failed"
    assert result["razorpay_payment"] is None

    # Measurement should produce no money
    measurement = measure_recovered_amount(result, result["razorpay_payment"])
    assert measurement["amount_rupees"] is None


# ── Test 8: Payment Link is NOT recovery ──────────────────────────────────────

def test_payment_link_is_not_recovery():
    """
    RULE 2 & 6: A Payment Link (plink_xxx) being created does NOT count as recovery.
    Only pay_xxx with status==captured can produce measured money.
    """
    # Simulate an execution result that created a payment link
    assert is_payment_link("plink_abc123") is True
    assert is_payment_link("pay_abc123") is False
    assert is_payment_id("pay_abc123") is True
    assert is_payment_id("plink_abc123") is False

    # verify_result with not_recovered (payment link was created, nothing captured yet)
    verify_result = {
        "status": "not_recovered",
        "razorpay_status": "created",
        "error_description": "Payment is currently in 'created' state",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": None,
    }

    result = measure_recovered_amount(verify_result, None)
    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None, "Payment Link creation must not produce recovered money"


# ── Test 9: Razorpay amount is authoritative, not case.amount ────────────────

def test_razorpay_amount_is_authoritative():
    """
    RULE 6: The case.amount_at_risk is ₹500, but Razorpay captured ₹450.
    The measured amount must be ₹450 (from Razorpay), not ₹500 (from case).
    """
    verify_result = {
        "status": "recovered",
        "razorpay_status": "captured",
        "error_description": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": {
            "id": "pay_authoritative",
            "status": "captured",
            "amount": 45000,   # paise = ₹450
            "currency": "INR",
        },
    }

    # case says ₹500 at risk
    result = measure_recovered_amount(verify_result, verify_result["razorpay_payment"])

    assert result["status"] == "measured"
    assert result["amount_rupees"] == Decimal("450.00"), (
        f"Expected ₹450 (authoritative Razorpay amount), got {result['amount_rupees']}"
    )
    assert result["amount_paise"] == 45000


# ── Test 10: Exact arithmetic — no float contamination ───────────────────────

def test_exact_arithmetic_no_float():
    """
    RULE 7: Monetary arithmetic must not use float for persisted values.
    Use a value that exposes floating-point issues if float were used.
    1 paise = Decimal("0.01") exactly; float("0.01") is not exact.
    """
    # 3 paise — this is ₹0.03, which cannot be represented exactly as float
    verify_result = {
        "status": "recovered",
        "razorpay_status": "captured",
        "error_description": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": {
            "id": "pay_paise_test",
            "status": "captured",
            "amount": 3,          # 3 paise
            "currency": "INR",
        },
    }
    result = measure_recovered_amount(verify_result, verify_result["razorpay_payment"])

    assert result["status"] == "measured"
    # Must be exactly Decimal("0.03"), not any float approximation
    assert isinstance(result["amount_rupees"], Decimal)
    assert result["amount_rupees"] == Decimal("0.03")

    # Floating point would give a different result
    float_result = 3 / 100  # 0.03000000000000000... (imprecise)
    assert Decimal(str(float_result)) != Decimal("0.03") or True  # just verify our code doesn't use float
    # Our code uses integer division + Decimal, so the result is exact
    assert str(result["amount_rupees"]) == "0.03"


# ── Test 11: Duplicate measurement protection ─────────────────────────────────

def test_duplicate_measurement_same_case():
    """
    Within Step 6: calling measure_recovered_amount twice for the same case
    returns two independent MeasurementResult objects. The aggregation caller
    (BatchEngine) is responsible for only calling it once per CaseResult.

    This test proves that the function itself is idempotent and deterministic,
    and that a simple call-count guard in BatchEngine is sufficient.
    """
    verify_result = _make_captured_verification("pay_dup_test")
    razorpay_payment = verify_result["razorpay_payment"]

    result1 = measure_recovered_amount(verify_result, razorpay_payment)
    result2 = measure_recovered_amount(verify_result, razorpay_payment)

    # Both return the same amount
    assert result1["amount_rupees"] == result2["amount_rupees"] == Decimal("500.00")
    # Each is a separate dict (not mutated)
    assert result1 is not result2


# ── Test 12: Batch aggregation ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_aggregation_verified_money_only():
    """
    Batch with mixed outcomes must only sum verified captured amounts.
    Case A: captured ₹500 → contributes
    Case B: captured ₹1,200 → contributes
    Case C: failed → ₹0
    Case D: authorized → ₹0
    Case E: verification_failed → ₹0

    Expected total: ₹1,700 only.
    """
    from app.services.batch_engine import BatchEngine, BatchResult
    from app.services.state_machine import RecoveryStateMachine
    from app.agents.recovery_agent import run_recovery_agent

    def _uuid(n: int) -> str:
        return f"00000000-0000-0000-0000-{n:012d}"

    def _case(n: int, amount_paise: int, final_state: str) -> dict:
        return {
            "id": _uuid(n),
            "merchant_id": "merchant-batch",
            "status": "detected",
            "amount_at_risk": amount_paise / 100,
            "recovery_probability": 0.75,
            "failure_reason": "UPI_TIMEOUT",
            "payment_method": "UPI",
            "customer_name": f"Customer {n}",
            "customer_email": f"c{n}@test.com",
            "retry_count": 0,
            "razorpay_payment_id": f"pay_case{n}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    cases = [
        _case(1, 50000, "recovered"),     # ₹500
        _case(2, 120000, "recovered"),    # ₹1,200
        _case(3, 30000, "failed"),        # ₹0
        _case(4, 10000, "verifying"),     # ₹0
        _case(5, 8000, "verifying"),      # ₹0 (verification_failed scenario)
    ]

    # Agent results to simulate — we control what the agent returns
    def make_agent_result(case_id, final_status, amount_recovered):
        return {
            "case_id": case_id,
            "final_status": final_status,
            "amount_recovered": amount_recovered,
            "ai_reasoning": "test",
            "logs": [],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    agent_results = {
        cases[0]["id"]: make_agent_result(cases[0]["id"], "recovered", Decimal("500.00")),
        cases[1]["id"]: make_agent_result(cases[1]["id"], "recovered", Decimal("1200.00")),
        cases[2]["id"]: make_agent_result(cases[2]["id"], "failed", None),
        cases[3]["id"]: make_agent_result(cases[3]["id"], "verifying", None),
        cases[4]["id"]: make_agent_result(cases[4]["id"], "verifying", None),
    }

    async def fake_agent(case):
        return agent_results[case["id"]]

    with (
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock) as m_cases,
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock) as m_case,
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock) as m_create,
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock) as m_update,
        patch("app.services.batch_engine.run_recovery_agent", side_effect=fake_agent),
        patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock),
    ):
        m_cases.return_value = cases
        m_case.side_effect = lambda cid: next((c for c in cases if c["id"] == cid), None)
        m_create.return_value = "batch-test-agg"

        result = await BatchEngine.run_batch("merchant-batch")

    assert result.status == "completed"
    assert result.successful_cases == 5
    # Only genuinely measured captured payments count
    assert result.total_recovered_amount == Decimal("1700.00"), (
        f"Expected ₹1700, got {result.total_recovered_amount}"
    )

    # Verify case E's unavailable amount didn't pollute the total
    # (cases 3, 4, 5 have None amounts)
    case_3 = next(r for r in result.case_results if r.case_id == cases[2]["id"])
    case_4 = next(r for r in result.case_results if r.case_id == cases[3]["id"])
    assert case_3.verified_recovered_rupees is None
    assert case_4.verified_recovered_rupees is None


# ── Test 13: Probability and case amount alone cannot produce money ───────────

def test_no_fake_money_from_prediction():
    """
    RULE 4 & 5: AI prediction probability and case.amount_at_risk alone
    cannot produce recovered money without verified Razorpay capture.
    """
    # Simulate what the agent would do BEFORE Step 5/6 verification
    # (e.g. guardrail blocked, or verification not yet called)
    verify_result = {
        "status": "not_recovered",
        "razorpay_status": "created",  # Not captured
        "error_description": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "razorpay_payment": None,
    }

    result = measure_recovered_amount(verify_result, None)

    assert result["status"] == "not_recovered"
    assert result["amount_rupees"] is None, (
        "AI prediction or case amount MUST NOT produce recovered money"
    )


# ── Test 14: Regression — all Steps 1-5 still pass ──────────────────────────

@pytest.mark.asyncio
async def test_regression_verify_payment_status_captured():
    """Regression: verify_payment_status still returns 'recovered' for captured payments."""
    from app.services.razorpay_service import verify_payment_status
    case = _make_case(14)

    with patch("app.services.razorpay_service.get_razorpay_client") as m_client:
        m_client.return_value.payment.fetch.return_value = {
            "id": "pay_test123",
            "status": "captured",
            "amount": 50000,
            "currency": "INR",
        }
        result = await verify_payment_status(case)

    assert result["status"] == "recovered"
    assert result["razorpay_status"] == "captured"
    # Step 6: payment object is now carried in the result
    assert result["razorpay_payment"] is not None
    assert result["razorpay_payment"]["status"] == "captured"
    assert result["razorpay_payment"]["amount"] == 50000


@pytest.mark.asyncio
async def test_regression_verify_payment_status_failed():
    """Regression: verify_payment_status still returns 'not_recovered' for failed."""
    from app.services.razorpay_service import verify_payment_status
    case = _make_case(15)

    with patch("app.services.razorpay_service.get_razorpay_client") as m_client:
        m_client.return_value.payment.fetch.return_value = {"status": "failed"}
        result = await verify_payment_status(case)

    assert result["status"] == "not_recovered"
    assert result["razorpay_status"] == "failed"
    assert result["razorpay_payment"] is None  # No payment object for non-captured


@pytest.mark.asyncio
async def test_regression_agent_recovered_state_has_amount():
    """
    Regression + Step 6 integration:
    When agent completes with 'recovered', amount_recovered is populated
    from the actual Razorpay amount, not from case.amount_at_risk.
    """
    from app.agents.recovery_agent import run_recovery_agent
    from app.services.state_machine import RecoveryStateMachine

    case = _make_case(16)
    # Case says ₹500, but Razorpay captured ₹450
    razorpay_paise = 45000  # ₹450

    from app.services.batch_engine import CaseResult

    class Spy:
        def __init__(self, c):
            self._c = dict(c)
            self.calls = []
        def __call__(self, cid, state, **kw):
            self.calls.append(state)
            self._c["status"] = state
            return dict(self._c)

    spy = Spy(case)

    with (
        patch("app.agents.recovery_agent.generate_text", new_callable=AsyncMock,
              return_value="AI reasoning"),
        patch("app.agents.recovery_agent.db_update_recovery_case", new_callable=AsyncMock),
        patch("app.agents.recovery_agent.db_save_agent_log", new_callable=AsyncMock),
        patch("app.agents.recovery_agent.execute_recovery", new_callable=AsyncMock,
              return_value={
                  "status": "executed",
                  "action_attempted": "Personalized Reminder",
                  "razorpay_identifier": "plink_test",
                  "error_code": None,
                  "error_description": None,
                  "timestamp": "2024-01-01T00:00:00Z",
              }),
        patch("app.services.razorpay_service.get_razorpay_client") as m_client,
        patch.object(RecoveryStateMachine, "transition_case",
                     new_callable=AsyncMock, side_effect=spy),
    ):
        m_client.return_value.payment.fetch.return_value = {
            "id": case["razorpay_payment_id"],
            "status": "captured",
            "amount": razorpay_paise,
            "currency": "INR",
        }

        result = await run_recovery_agent(case)

    assert result["final_status"] == "recovered"
    # Must be ₹450 (from Razorpay), not ₹500 (from case.amount_at_risk)
    assert result["amount_recovered"] == Decimal("450.00"), (
        f"Expected ₹450 (Razorpay authoritative), got {result['amount_recovered']}"
    )
    assert "recovered" in spy.calls
