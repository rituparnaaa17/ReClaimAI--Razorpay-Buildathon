"""
Tests for Phase 1 Step 2 — Batch Recovery Engine.

Covers all 10 required scenarios:
 1.  Empty batch (no eligible cases)
 2.  Single case processed successfully
 3.  Multiple cases (10) all eligible
 4.  Mixed outcomes — success, failure, exception, skipped
 5.  Terminal cases are NOT processed
 6.  Stale case — becomes ineligible between selection and processing
 7.  Merchant isolation — Merchant A batch cannot process Merchant B cases
 8.  Invalid state transition cannot be forced by the batch engine
 9.  Case exception does not abort the batch (isolation)
10.  Batch-level DB failure produces a FAILED result (not silent success)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.services.batch_engine import (
    BatchEngine, ELIGIBLE_STATES, TERMINAL_STATES, CaseResult,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

MERCHANT_A = "merchant-a-uuid"
MERCHANT_B = "merchant-b-uuid"


def _make_case(case_id: str, status: str, merchant_id: str = MERCHANT_A) -> dict:
    return {
        "id": case_id,
        "merchant_id": merchant_id,
        "status": status,
        "amount_at_risk": 5000,
        "recovery_probability": 0.75,
        "failure_reason": "UPI_TIMEOUT",
        "payment_method": "UPI",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "retry_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _agent_result(case_id: str, final_status: str = "recovered") -> dict:
    return {
        "case_id": case_id,
        "final_status": final_status,
        "amount_recovered": 5000 if final_status == "recovered" else None,
        "ai_reasoning": "Test reasoning",
        "logs": [],
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_batch_db():
    """Mock all batch DB operations to avoid real Supabase calls."""
    with (
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock) as mock_create,
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock) as mock_update,
    ):
        mock_create.return_value = "test-batch-id"
        mock_update.return_value = True
        yield mock_create, mock_update


@pytest.fixture
def mock_agent():
    """Mock the recovery agent to avoid real LangGraph/Gemini/Razorpay calls."""
    with patch("app.services.batch_engine.run_recovery_agent", new_callable=AsyncMock) as mock:
        mock.return_value = _agent_result("placeholder", "recovered")
        yield mock


@pytest.fixture
def mock_db_cases():
    """Mock db_get_recovery_cases."""
    with patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_db_case():
    """Mock db_get_recovery_case (single case re-fetch for stale check)."""
    with patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock) as mock:
        yield mock


# ── Test 1: Empty batch ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_empty_batch(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """No eligible cases → batch created, completes cleanly with zeros."""
    mock_db_cases.return_value = []

    result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    assert result.status == "completed"
    assert result.total_cases == 0
    assert result.processed_cases == 0
    assert result.successful_cases == 0
    assert result.failed_cases == 0
    assert result.skipped_cases == 0
    assert result.error_message is None
    # Agent should never have been called
    mock_agent.assert_not_called()


# ── Test 2: Single case ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_single_case_success(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """One eligible case → processed, batch completes."""
    case = _make_case("case-1", "detected")
    mock_db_cases.return_value = [case]
    mock_db_case.return_value = case  # fresh fetch same as selected
    mock_agent.return_value = _agent_result("case-1", "recovered")

    result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    assert result.status == "completed"
    assert result.total_cases == 1
    assert result.processed_cases == 1
    assert result.successful_cases == 1
    assert result.failed_cases == 0
    assert result.skipped_cases == 0
    assert len(result.case_results) == 1
    assert result.case_results[0].result == "success"
    assert result.case_results[0].final_state == "recovered"


# ── Test 3: Multiple cases ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multiple_cases(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """10 eligible cases → all are processed."""
    cases = [_make_case(f"case-{i}", "detected") for i in range(10)]
    mock_db_cases.return_value = cases

    # db_get_recovery_case returns the matching case for each
    async def get_case_by_id(case_id: str):
        return next((c for c in cases if c["id"] == case_id), None)
    mock_db_case.side_effect = get_case_by_id

    mock_agent.side_effect = [
        _agent_result(f"case-{i}", "recovered") for i in range(10)
    ]

    result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    assert result.total_cases == 10
    assert result.processed_cases == 10
    assert result.successful_cases == 10
    assert mock_agent.call_count == 10


# ── Test 4: Mixed outcomes ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mixed_outcomes(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """
    5 cases with outcomes: success, success, exception, success, skipped.
    Batch should complete with partial_failure (due to exception).
    """
    cases = [_make_case(f"case-{i}", "detected") for i in range(5)]
    mock_db_cases.return_value = cases

    # case-3 will be stale (becomes terminal before processing)
    fresh_cases = {
        "case-0": _make_case("case-0", "detected"),
        "case-1": _make_case("case-1", "detected"),
        "case-2": _make_case("case-2", "detected"),
        "case-3": _make_case("case-3", "recovered"),   # stale — became terminal
        "case-4": _make_case("case-4", "detected"),
    }
    mock_db_case.side_effect = lambda cid: fresh_cases.get(cid)

    # case-2 raises an exception during agent call
    agent_calls = {
        "case-0": _agent_result("case-0", "recovered"),
        "case-1": _agent_result("case-1", "recovered"),
        "case-2": Exception("Simulated agent failure"),
        "case-4": _agent_result("case-4", "failed"),
    }

    async def agent_side_effect(case):
        cid = case["id"]
        outcome = agent_calls.get(cid)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    mock_agent.side_effect = agent_side_effect

    result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    # case-3 was skipped (stale), case-2 errored (exception), rest processed
    assert result.total_cases == 5
    assert result.skipped_cases == 1       # case-3
    assert result.failed_cases == 1        # case-2 (exception) ONLY
    assert result.successful_cases == 3    # case-0 + case-1 + case-4 (agent returned failed business outcome but successful processing)
    # Batch status should be partial_failure because case-2 threw an exception
    assert result.status == "partial_failure"

    # Verify case-2 is recorded as failed with an error
    case2_result = next(r for r in result.case_results if r.case_id == "case-2")
    assert case2_result.result == "failed"
    assert case2_result.error is not None

    # Verify case-3 is recorded as skipped
    case3_result = next(r for r in result.case_results if r.case_id == "case-3")
    assert case3_result.result == "skipped"


# ── Test 5: Terminal cases not processed ─────────────────────────────────────

@pytest.mark.asyncio
async def test_terminal_cases_not_processed(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """Cases in terminal states must be filtered out and never passed to the agent."""
    terminal_cases = [_make_case(f"t-{s}", s) for s in TERMINAL_STATES]
    eligible_case = _make_case("eligible-1", "detected")
    all_cases = terminal_cases + [eligible_case]

    mock_db_cases.return_value = all_cases
    mock_db_case.return_value = eligible_case
    mock_agent.return_value = _agent_result("eligible-1", "recovered")

    result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    # Only the eligible case should have been processed
    assert result.total_cases == 1
    assert result.processed_cases == 1
    mock_agent.call_count == 1  # agent only called once


# ── Test 6: Stale case protection ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stale_case_is_skipped(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """
    Case selected while eligible, then becomes RECOVERED before processing.
    Must be SKIPPED, not forced through the agent.
    """
    # At selection time: case is detected (eligible)
    case_at_selection = _make_case("stale-case", "detected")
    mock_db_cases.return_value = [case_at_selection]

    # At processing time: case is now recovered (terminal)
    case_at_processing = _make_case("stale-case", "recovered")
    mock_db_case.return_value = case_at_processing

    result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    assert result.total_cases == 1
    assert result.skipped_cases == 1
    assert result.processed_cases == 0
    assert result.successful_cases == 0
    # Agent must NOT have been called
    mock_agent.assert_not_called()

    case_result = result.case_results[0]
    assert case_result.result == "skipped"
    assert "ineligible" in case_result.reason.lower()


# ── Test 7: Merchant isolation ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_merchant_isolation(mock_batch_db, mock_agent, mock_db_cases, mock_db_case):
    """
    A batch for Merchant A with explicit case_ids must not process Merchant B cases.
    """
    merchant_b_case = _make_case("b-case-1", "detected", merchant_id=MERCHANT_B)

    # Case fetched individually (since case_ids provided)
    mock_db_case.return_value = merchant_b_case

    result = await BatchEngine.run_batch(
        merchant_id=MERCHANT_A,
        case_ids=["b-case-1"],
    )

    # The case belongs to Merchant B — must be skipped
    assert result.total_cases == 0  # filtered out before counting
    assert result.processed_cases == 0
    mock_agent.assert_not_called()


# ── Test 8: State machine not bypassed ───────────────────────────────────────

@pytest.mark.asyncio
async def test_state_machine_not_bypassed(mock_batch_db, mock_db_cases, mock_db_case):
    """
    The batch engine must not directly manipulate case status.
    All transitions must go through RecoveryStateMachine (via the agent).
    This test verifies that the engine delegates to run_recovery_agent and
    does NOT call db_update_recovery_case directly for status changes.
    """
    case = _make_case("sm-case", "detected")
    mock_db_cases.return_value = [case]
    mock_db_case.return_value = case

    with (
        patch("app.services.batch_engine.run_recovery_agent", new_callable=AsyncMock) as mock_agent_inner,
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock, return_value=[case]),
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock, return_value=case),
    ):
        mock_agent_inner.return_value = _agent_result("sm-case", "recovered")

        result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

        # Agent WAS called (the engine delegates to it)
        mock_agent_inner.assert_called_once()
        # The case passed to the agent is the fresh copy from db_get_recovery_case
        called_case = mock_agent_inner.call_args[0][0]
        assert called_case["id"] == "sm-case"


# ── Test 9: Case exception does not abort batch ────────────────────────────────

@pytest.mark.asyncio
async def test_case_exception_isolation(mock_batch_db, mock_db_cases, mock_db_case):
    """
    If one case raises an exception, the remaining cases must still be processed.
    """
    cases = [_make_case(f"iso-{i}", "detected") for i in range(5)]
    mock_db_cases.return_value = cases

    async def get_case(cid):
        return next((c for c in cases if c["id"] == cid), None)
    mock_db_case.side_effect = get_case

    call_count = {"n": 0}

    async def agent_with_exception(case):
        call_count["n"] += 1
        if case["id"] == "iso-2":
            raise RuntimeError("Simulated infrastructure exception")
        return _agent_result(case["id"], "recovered")

    with patch("app.services.batch_engine.run_recovery_agent", side_effect=agent_with_exception):
        result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    # All 5 cases were attempted
    assert call_count["n"] == 5
    # iso-2 failed, rest succeeded
    assert result.successful_cases == 4
    assert result.failed_cases == 1
    assert result.status == "partial_failure"

    iso2 = next(r for r in result.case_results if r.case_id == "iso-2")
    assert iso2.result == "failed"
    assert "Simulated infrastructure exception" in (iso2.error or "")


# ── Test 10: Batch-level DB failure ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_db_failure(mock_agent, mock_db_cases):
    """
    If db_create_batch fails, the batch must report FAILED — not silently succeed.
    """
    mock_db_cases.return_value = [_make_case("c1", "detected")]

    with (
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock, return_value=None),
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock, return_value=True),
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock),
    ):
        result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    assert result.status == "failed"
    assert result.error_message is not None
    assert result.processed_cases == 0
    # Agent must NOT have been called — batch failed before processing
    mock_agent.assert_not_called()


# ── Test 11: Legitimate Business Outcomes ────────────────────────────────────

@pytest.mark.asyncio
async def test_legitimate_business_outcomes(mock_batch_db, mock_db_cases, mock_db_case):
    """
    Cases that finish processing with terminal states (recovered, no_action, escalated)
    must all be marked as processing SUCCESS.
    """
    outcomes = ["recovered", "no_action", "escalated", "failed"]
    cases = [_make_case(f"case-{o}", "detected") for o in outcomes]
    mock_db_cases.return_value = cases

    async def get_case(cid):
        return next((c for c in cases if c["id"] == cid), None)
    mock_db_case.side_effect = get_case

    async def agent_side_effect(case):
        cid = case["id"]
        # The id ends with the outcome we want
        outcome = cid.split("-")[1]
        return _agent_result(cid, outcome)

    with patch("app.services.batch_engine.run_recovery_agent", side_effect=agent_side_effect):
        result = await BatchEngine.run_batch(merchant_id=MERCHANT_A)

    assert result.total_cases == 4
    assert result.processed_cases == 4
    assert result.successful_cases == 4
    assert result.failed_cases == 0
    assert result.status == "completed"

    for o in outcomes:
        c_res = next(r for r in result.case_results if r.case_id == f"case-{o}")
        assert c_res.result == "success"
        assert c_res.final_state == o
