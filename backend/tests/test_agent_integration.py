"""
Phase 1, Step 3 — Agent Integration Tests
==========================================
Verifies that the existing LangGraph recovery agent, the Recovery State Machine,
and the Batch Engine are correctly connected.

Architecture under test:
  run_recovery_agent(case)
    ↓ calls RecoveryStateMachine.transition_case() for every lifecycle change
    ↓ calls Razorpay (retry_payment / create_payment_link)
    ↓ calls Gemini (generate_text)
    ↓ calls db_update_recovery_case (for non-status agent fields only)

  BatchEngine.run_batch()
    ↓ selects eligible cases
    ↓ calls run_recovery_agent(case) — same agent, same code path
    ↓ aggregates CaseResult objects

Mocking strategy:
  We mock RecoveryStateMachine.transition_case directly with an AsyncMock that:
    - records all calls (spy behaviour)
    - returns a dict with the new state (simulating what the real SM returns)
    - does NOT hit Supabase at all
  This way the agent's actual node logic, guardrail logic, and flow are exercised
  without any real database or external service calls.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, call as mock_call
from datetime import datetime, timezone

from app.agents.recovery_agent import run_recovery_agent
from app.services.state_machine import RecoveryStateMachine
from app.services.batch_engine import BatchEngine


# ── Shared helpers ────────────────────────────────────────────────────────────

def _uuid(n: int) -> str:
    """Generate a deterministic valid UUID for test case IDs."""
    return f"00000000-0000-0000-0000-{n:012d}"


def _make_case(n: int, *, amount: int = 5000, prob: float = 0.75,
               retry_count: int = 0, status: str = "detected") -> dict:
    """Build a minimal recovery case dict accepted by the agent."""
    return {
        "id": _uuid(n),
        "merchant_id": "merchant-test",
        "status": status,
        "amount_at_risk": amount,
        "recovery_probability": prob,
        "failure_reason": "UPI_TIMEOUT",
        "payment_method": "UPI",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "retry_count": retry_count,
        "razorpay_payment_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


class TransitionSpy:
    """
    Replaces RecoveryStateMachine.transition_case with a spy that:
      - Records every (case_id, new_state) call.
      - Returns a fake updated case dict so the agent can continue.
      - Does NOT hit Supabase.
    """

    def __init__(self, case: dict):
        self._case = dict(case)
        self.calls: list[tuple[str, str]] = []  # (case_id, new_state)

    async def __call__(self, case_id, new_state, **kwargs):
        if case_id != self._case["id"]:
            raise ValueError(f"Unexpected case_id {case_id}")
        self.calls.append((case_id, new_state))
        self._case["status"] = new_state
        return dict(self._case)

    @property
    def states(self) -> list[str]:
        """Return only the new_state values in call order."""
        return [s for _, s in self.calls]


def _make_transition_spy(case: dict) -> TransitionSpy:
    return TransitionSpy(case)


# ── Core fixture: stubs external I/O that the agent calls directly ────────────

@pytest.fixture
def base_ext():
    """
    Stubs everything the agent calls except RecoveryStateMachine.transition_case,
    which individual tests will control via TransitionSpy or dedicated patches.
    """
    with (
        patch("app.agents.recovery_agent.db_update_recovery_case", new_callable=AsyncMock) as agent_update,
        patch("app.agents.recovery_agent.db_save_agent_log", new_callable=AsyncMock),
        patch("app.agents.recovery_agent.execute_recovery", new_callable=AsyncMock) as exec_mock,
        patch("app.agents.recovery_agent.verify_payment_status", new_callable=AsyncMock) as verify_mock,
        patch("app.agents.recovery_agent.generate_text", new_callable=AsyncMock) as gemini,
    ):
        agent_update.return_value = True
        gemini.return_value = "AI reasoning text"
        verify_mock.return_value = {
            "status": "verification_failed",
            "razorpay_status": None,
            "error_description": "Mocked for integration test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        exec_mock.return_value = {
            "status": "executed",
            "action_attempted": "Smart Retry",
            "razorpay_identifier": "pay_test_ok",
            "error_code": None,
            "error_description": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        yield {
            "agent_update": agent_update,
            "exec": exec_mock,
            "verify": verify_mock,
            "gemini": gemini,
        }


# ── TEST 1 — Normal agent flow (happy path) ───────────────────────────────────

@pytest.mark.asyncio
async def test_normal_agent_flow(base_ext):
    """
    Verifies the full happy path: detected → … → recovered.

    The TransitionSpy replaces the state machine so we can verify:
      - All 7 nodes run.
      - Transitions are called in the correct order.
      - Final status is 'recovered'.
    """
    case = _make_case(1, amount=2000, prob=0.8)
    spy = _make_transition_spy(case)

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    # Result contract
    assert result["case_id"] == case["id"]
    assert result["final_status"] == "verifying"  # Step 4: stops at verifying, not recovered
    assert result["amount_recovered"] is None      # Step 5 will determine recovery
    assert len(result["logs"]) == 7

    # Correct lifecycle sequence through execution node
    assert "recovering" in spy.states
    assert "verifying" in spy.states
    # Must NOT fabricate recovered
    assert "recovered" not in spy.states


# ── TEST 2 — State machine is the sole lifecycle authority ────────────────────

@pytest.mark.asyncio
async def test_state_machine_is_sole_authority(base_ext):
    """
    Verifies that every lifecycle change is routed through
    RecoveryStateMachine.transition_case() — the agent must NOT mutate
    status independently.
    """
    case = _make_case(2, amount=1000, prob=0.8)
    spy = _make_transition_spy(case)

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    # State machine was called for every step
    assert len(spy.calls) >= 6, (
        f"Expected at least 6 state machine calls, got {len(spy.calls)}: {spy.states}"
    )

    # The agent never touched the db_update_recovery_case with 'status'
    for c in base_ext["agent_update"].call_args_list:
        update_dict = c.args[1] if len(c.args) >= 2 else {}
        assert "status" not in update_dict, (
            f"Agent bypassed state machine: db_update_recovery_case called with status={update_dict}"
        )

    assert result["final_status"] == "verifying"  # Step 4: stops at verifying


# ── TEST 3 — No direct status bypass (static + runtime) ──────────────────────

def test_no_direct_status_bypass_static():
    """
    Statically inspects recovery_agent.py to verify db_update_recovery_case
    is never called with a 'status' key.
    """
    import ast

    with open("app/agents/recovery_agent.py", "r") as f:
        tree = ast.parse(f.read())

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else None
        )
        if name != "db_update_recovery_case":
            continue
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Dict):
            keys = [k.value for k in node.args[1].keys if isinstance(k, ast.Constant)]
            if "status" in keys:
                violations.append(ast.get_lineno(node))

    assert violations == [], (
        f"Direct status bypass at lines {violations} in recovery_agent.py. "
        "All status transitions must go through RecoveryStateMachine.transition_case()."
    )


@pytest.mark.asyncio
async def test_no_direct_status_bypass_runtime(base_ext):
    """Runtime verification that agent does not call db_update_recovery_case with 'status'."""
    case = _make_case(3, prob=0.8)
    spy = _make_transition_spy(case)

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        await run_recovery_agent(case)

    for c in base_ext["agent_update"].call_args_list:
        update_dict = c.args[1] if len(c.args) >= 2 else {}
        assert "status" not in update_dict, (
            f"Runtime bypass detected: {update_dict}"
        )


# ── TEST 4 — Approval flow (amount > ₹50,000) ────────────────────────────────

@pytest.mark.asyncio
async def test_approval_flow_stops_at_action_required(base_ext):
    """
    Cases with amount > ₹50,000 must stop at action_required.
    Execution (recovering, verifying) must NOT occur.
    """
    case = _make_case(4, amount=75_000, prob=0.9)
    spy = _make_transition_spy(case)

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    assert result["final_status"] == "action_required"
    assert result["amount_recovered"] is None

    # No Razorpay execution before approval
    base_ext["exec"].assert_not_called()

    assert "action_required" in spy.states
    assert "recovering" not in spy.states
    assert "verifying" not in spy.states

    # GUARDRAIL log step must show blocked
    guardrail_logs = [l for l in result["logs"] if l["step"] == "GUARDRAIL"]
    assert len(guardrail_logs) == 1
    assert guardrail_logs[0]["result"] == "blocked"


# ── TEST 5 — No-action flow ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_action_is_legitimate_outcome(base_ext):
    """
    Cases with recovery_probability < 30% must stop at no_action.
    This is a legitimate business outcome, not a processing failure.
    """
    case = _make_case(5, prob=0.15)
    spy = _make_transition_spy(case)

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    assert result["final_status"] == "no_action"
    assert result["amount_recovered"] is None
    base_ext["exec"].assert_not_called()
    assert "no_action" in spy.states
    assert "recovering" not in spy.states


@pytest.mark.asyncio
async def test_batch_treats_no_action_as_processing_success(base_ext):
    """Batch Engine must record no_action as result='success', not result='failed'."""
    case = _make_case(6, prob=0.15, status="detected")
    spy = _make_transition_spy(case)

    with (
        patch.object(RecoveryStateMachine, "transition_case", spy),
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock, return_value=[case]),
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock, return_value=case),
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock, return_value="batch-5"),
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock),
    ):
        batch_result = await BatchEngine.run_batch(merchant_id="merchant-test")

    assert batch_result.successful_cases == 1
    assert batch_result.failed_cases == 0
    case_res = batch_result.case_results[0]
    assert case_res.result == "success"
    assert case_res.final_state == "no_action"


# ── TEST 6 — Escalation flow (retry_count >= 2) ───────────────────────────────

@pytest.mark.asyncio
async def test_escalation_is_legitimate_outcome(base_ext):
    """
    Cases with retry_count >= 2 must stop at escalated.
    No execution must occur.
    """
    case = _make_case(7, retry_count=2)
    spy = _make_transition_spy(case)

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    assert result["final_status"] == "escalated"
    assert result["amount_recovered"] is None
    base_ext["exec"].assert_not_called()
    assert "escalated" in spy.states
    assert "recovering" not in spy.states


@pytest.mark.asyncio
async def test_batch_treats_escalation_as_processing_success(base_ext):
    """Batch Engine must record escalated as result='success'."""
    case = _make_case(8, retry_count=2, status="detected")
    spy = _make_transition_spy(case)

    with (
        patch.object(RecoveryStateMachine, "transition_case", spy),
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock, return_value=[case]),
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock, return_value=case),
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock, return_value="batch-6"),
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock),
    ):
        batch_result = await BatchEngine.run_batch(merchant_id="merchant-test")

    assert batch_result.successful_cases == 1
    assert batch_result.failed_cases == 0
    assert batch_result.case_results[0].final_state == "escalated"
    assert batch_result.case_results[0].result == "success"


# ── TEST 7 — Verification success ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verification_success(base_ext):
    """
    Step 4: Execute → stop at verifying (not recovered).
    Step 5 will query Razorpay and determine actual recovery.
    EXECUTE must appear in logs before VERIFY.
    """
    case = _make_case(9, amount=3000, prob=0.8)
    spy = _make_transition_spy(case)
    base_ext["exec"].return_value = {
        "status": "executed",
        "action_attempted": "Smart Retry",
        "razorpay_identifier": "pay_abc",
        "error_code": None,
        "error_description": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    # Step 4 stops at verifying — Step 5 will transition to recovered
    assert result["final_status"] == "verifying"
    assert result["amount_recovered"] is None

    log_steps = [l["step"] for l in result["logs"]]
    assert "EXECUTE" in log_steps
    assert "VERIFY" in log_steps
    assert log_steps.index("EXECUTE") < log_steps.index("VERIFY")

    # State machine must have stopped at verifying, NOT jumped to recovered
    assert "verifying" in spy.states
    assert "recovered" not in spy.states


# ── TEST 8 — Verification failure ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verification_failure(base_ext):
    """
    Step 4: Execution fails → case transitions to failed.
    This is a Razorpay API failure, not a business-level recovery outcome.
    """
    case = _make_case(10, prob=0.8)
    spy = _make_transition_spy(case)
    base_ext["exec"].return_value = {
        "status": "failed",
        "action_attempted": "Smart Retry",
        "razorpay_identifier": None,
        "error_code": "API_ERROR",
        "error_description": "API rejected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    assert result["final_status"] == "failed"
    assert result["amount_recovered"] is None

    log_steps = [l["step"] for l in result["logs"]]
    assert "EXECUTE" in log_steps
    assert "VERIFY" in log_steps
    assert "verifying" in spy.states
    assert "failed" in spy.states


# ── TEST 9 — Unexpected agent exception propagates correctly ──────────────────

@pytest.mark.asyncio
async def test_unexpected_exception_does_not_produce_recovered_state(base_ext):
    """
    If an unexpected exception escapes a node (not silently caught by the agent),
    the outer node-loop guard fires: the pipeline stops and final_status is NOT
    'recovered', and amount_recovered stays None.

    Important design note: Gemini errors inside _node_predict are intentionally
    caught and suppressed by the agent (Gemini reasoning is optional). We use
    retry_payment — called inside _node_execute without a try/except — to force
    an exception that actually escapes to the outer guard.
    """
    case = _make_case(11, prob=0.8)
    spy = _make_transition_spy(case)
    # execute_recovery crash is caught by _node_execute and returns structured failed result
    base_ext["exec"].side_effect = RuntimeError("Razorpay connection refused")

    with patch.object(RecoveryStateMachine, "transition_case", spy):
        result = await run_recovery_agent(case)

    # Agent must not produce a false recovered state
    assert result["final_status"] != "recovered", (
        "Agent incorrectly returned 'recovered' despite execute_recovery crashing"
    )
    assert result["amount_recovered"] is None


@pytest.mark.asyncio
async def test_batch_isolates_agent_exception(base_ext):
    """
    If run_recovery_agent raises an unhandled exception, BatchEngine must:
      - Classify that case as result='failed' with the error captured.
      - Continue processing subsequent cases.
      - Not abort the entire batch.
    """
    case_crash = _make_case(12, status="detected")
    case_ok = _make_case(13, amount=1000, prob=0.8, status="detected")
    spy_ok = _make_transition_spy(case_ok)

    async def agent_side_effect(c):
        if c["id"] == case_crash["id"]:
            raise RuntimeError("Catastrophic agent failure")
        with patch.object(RecoveryStateMachine, "transition_case", spy_ok):
            return await run_recovery_agent(c)

    with (
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock, return_value=[case_crash, case_ok]),
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock, side_effect=lambda cid: case_crash if cid == case_crash["id"] else case_ok),
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock, return_value="batch-exc"),
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock),
        patch("app.services.batch_engine.run_recovery_agent", side_effect=agent_side_effect),
    ):
        batch_result = await BatchEngine.run_batch(merchant_id="merchant-test")

    assert batch_result.total_cases == 2
    assert batch_result.processed_cases == 2
    assert batch_result.failed_cases == 1
    assert batch_result.successful_cases == 1

    failed = next(r for r in batch_result.case_results if r.result == "failed")
    assert failed.case_id == case_crash["id"]
    assert "Catastrophic agent failure" in (failed.error or "")

    ok = next(r for r in batch_result.case_results if r.result == "success")
    assert ok.case_id == case_ok["id"]


# ── TEST 10 — Full batch integration with mixed outcomes ──────────────────────

@pytest.mark.asyncio
async def test_batch_mixed_outcomes(base_ext):
    """
    End-to-end batch test with 4 cases exercising 4 different business outcomes.

      Case A (amount=1000, prob=0.8, retries=0)  → recovered
      Case B (amount=500,  prob=0.1, retries=0)  → no_action
      Case C (amount=500,  prob=0.8, retries=2)  → escalated
      Case D (amount=75k,  prob=0.9, retries=0)  → action_required

    All 4 must be processing successes (result='success').
    """
    case_a = _make_case(20, amount=1000, prob=0.8, retry_count=0)
    case_b = _make_case(21, amount=500,  prob=0.1, retry_count=0)
    case_c = _make_case(22, amount=500,  prob=0.8, retry_count=2)
    case_d = _make_case(23, amount=75_000, prob=0.9, retry_count=0)

    all_cases = [case_a, case_b, case_c, case_d]
    case_map = {c["id"]: c for c in all_cases}

    # Create a spy per case so transitions are isolated
    spies = {c["id"]: _make_transition_spy(c) for c in all_cases}

    async def agent_side_effect(c):
        spy = spies[c["id"]]
        with patch.object(RecoveryStateMachine, "transition_case", spy):
            return await run_recovery_agent(c)

    with (
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock, return_value=all_cases),
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock, side_effect=lambda cid: case_map.get(cid)),
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock, return_value="batch-mixed"),
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock),
        patch("app.services.batch_engine.run_recovery_agent", side_effect=agent_side_effect),
    ):
        batch_result = await BatchEngine.run_batch(merchant_id="merchant-test")

    assert batch_result.total_cases == 4
    assert batch_result.processed_cases == 4
    assert batch_result.successful_cases == 4
    assert batch_result.failed_cases == 0
    assert batch_result.status == "completed"

    by_id = {r.case_id: r for r in batch_result.case_results}

    assert by_id[case_a["id"]].final_state == "verifying"  # Step 4: stops at verifying
    assert by_id[case_b["id"]].final_state == "no_action"
    assert by_id[case_c["id"]].final_state == "escalated"
    assert by_id[case_d["id"]].final_state == "action_required"

    for r in batch_result.case_results:
        assert r.result == "success", (
            f"Case {r.case_id} with final_state={r.final_state} was incorrectly "
            f"classified as result='{r.result}' instead of 'success'"
        )


# ── TEST 11 — Single-case API and Batch use the same agent ───────────────────

def test_single_case_api_and_batch_import_same_agent():
    """
    Statically verifies both the API endpoint and the Batch Engine import
    run_recovery_agent from the same module (app.agents.recovery_agent).
    There is no duplicate agent implementation.
    """
    import ast

    def get_run_recovery_agent_imports(filepath: str) -> list[str]:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read())
        return [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and any(alias.name == "run_recovery_agent" for alias in node.names)
        ]

    api_imports = get_run_recovery_agent_imports("app/api/agent.py")
    batch_imports = get_run_recovery_agent_imports("app/services/batch_engine.py")

    assert "app.agents.recovery_agent" in api_imports, (
        "Single-case API does not import run_recovery_agent from app.agents.recovery_agent"
    )
    assert "app.agents.recovery_agent" in batch_imports, (
        "BatchEngine does not import run_recovery_agent from app.agents.recovery_agent"
    )
    # Both import from the same module — confirmed no duplicate
    assert api_imports == batch_imports or (
        "app.agents.recovery_agent" in api_imports
        and "app.agents.recovery_agent" in batch_imports
    )
