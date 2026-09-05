import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
import razorpay

from app.services.razorpay_service import execute_recovery
from app.agents.recovery_agent import run_recovery_agent
from app.services.state_machine import RecoveryStateMachine
from app.services.batch_engine import BatchEngine

# ── Shared helpers ────────────────────────────────────────────────────────────

def _uuid(n: int) -> str:
    return f"00000000-0000-0000-0000-{n:012d}"

def _make_case(n: int, *, amount: int = 5000, prob: float = 0.75,
               retry_count: int = 0, status: str = "detected") -> dict:
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
    def __init__(self, case: dict):
        self._case = dict(case)
        self.calls: list[tuple[str, str]] = []

    def __call__(self, case_id, new_state, **kwargs):
        if case_id != self._case["id"]:
            raise ValueError(f"Unexpected case_id {case_id}")
        self.calls.append((case_id, new_state))
        self._case["status"] = new_state
        return dict(self._case)

    @property
    def states(self) -> list[str]:
        return [s for _, s in self.calls]

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ext_mocks():
    """Stubs everything the agent calls except the transition_case spy."""
    with (
        patch("app.agents.recovery_agent.generate_text", new_callable=AsyncMock) as m_gemini,
        patch("app.agents.recovery_agent.db_update_recovery_case", new_callable=AsyncMock) as m_db_upd,
        patch("app.agents.recovery_agent.db_save_agent_log", new_callable=AsyncMock) as m_db_log,
        patch("app.agents.recovery_agent.execute_recovery", new_callable=AsyncMock) as m_exec,
        patch("app.agents.recovery_agent.verify_payment_status", new_callable=AsyncMock) as m_verify,
    ):
        m_gemini.return_value = '{"recommended_action": "Personalized Reminder", "confidence_score": 0.85, "reasoning": "Standard failure."}'
        m_db_upd.return_value = True
        m_db_log.return_value = True
        m_verify.return_value = {
            "status": "verification_failed",
            "razorpay_status": None,
            "error_description": "Mocked",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        m_exec.return_value = {
            "status": "executed",
            "action_attempted": "Personalized Reminder",
            "razorpay_identifier": "plink_test_123",
            "error_code": None,
            "error_description": None,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        yield {
            "gemini": m_gemini,
            "db_upd": m_db_upd,
            "db_log": m_db_log,
            "exec": m_exec,
            "verify": m_verify
        }

@pytest.fixture
def mock_case():
    return _make_case(1, status="detected")


# ── Tests for execute_recovery (Unit) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_recovery_payment_link(mock_case):
    with patch('app.services.razorpay_service.create_payment_link', new_callable=AsyncMock) as mock_link:
        mock_link.return_value = {"success": True, "payment_link_id": "plink_123"}
        result = await execute_recovery("Personalized Reminder", mock_case)
        assert result["status"] == "executed"
        assert result["razorpay_identifier"] == "plink_123"

@pytest.mark.asyncio
async def test_execute_recovery_smart_retry(mock_case):
    with patch('app.services.razorpay_service.create_payment_link', new_callable=AsyncMock) as mock_link:
        mock_link.return_value = {"success": True, "payment_link_id": "plink_retry_123"}
        result = await execute_recovery("Smart Retry", mock_case)
        assert result["status"] == "executed"
        assert result["razorpay_identifier"] == "plink_retry_123"

@pytest.mark.asyncio
async def test_execute_recovery_wait(mock_case):
    result = await execute_recovery("Wait", mock_case)
    assert result["status"] == "skipped"

@pytest.mark.asyncio
async def test_execute_recovery_api_failure(mock_case):
    with patch('app.services.razorpay_service.create_payment_link', new_callable=AsyncMock) as mock_link:
        mock_link.side_effect = razorpay.errors.BadRequestError("Invalid amount")
        result = await execute_recovery("Personalized Reminder", mock_case)
        assert result["status"] == "failed"
        assert result["error_code"] == "BAD_REQUEST"


# ── Tests for Agent Integration (Step 4 Behavior) ─────────────────────────────

@pytest.mark.asyncio
async def test_agent_executable_action_stops_at_verifying(mock_case, ext_mocks):
    """Test 1: Executable action -> executed -> verifying, NOT recovered."""
    spy = TransitionSpy(mock_case)
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy) as tmock:
        res = await run_recovery_agent(mock_case)
    
    assert res["final_status"] == "verifying"
    assert "recovered" not in spy.states
    assert spy.states[-1] == "verifying"


@pytest.mark.asyncio
async def test_agent_razorpay_execution_failure(mock_case, ext_mocks):
    """Test 2: Razorpay execution failure -> failed."""
    ext_mocks["exec"].return_value = {
        "status": "failed",
        "action_attempted": "Personalized Reminder",
        "error_description": "API Error"
    }
    spy = TransitionSpy(mock_case)
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy) as tmock:
        res = await run_recovery_agent(mock_case)
    
    assert res["final_status"] == "failed"
    assert spy.states[-2:] == ["verifying", "failed"]


@pytest.mark.asyncio
async def test_agent_unsupported_smart_retry(mock_case, ext_mocks):
    """Test 3: Unsupported Smart Retry -> not_executable -> no_action."""
    ext_mocks["exec"].return_value = {
        "status": "not_executable",
        "error_description": "Cannot be retried"
    }
    spy = TransitionSpy(mock_case)
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy) as tmock:
        res = await run_recovery_agent(mock_case)
    
    assert res["final_status"] == "no_action"
    assert spy.states[-2:] == ["verifying", "no_action"]


@pytest.mark.asyncio
async def test_agent_wait_skipped(mock_case, ext_mocks):
    """Test 4: WAIT/skipped -> skipped -> no_action."""
    ext_mocks["exec"].return_value = {
        "status": "skipped",
        "error_description": "Scheduled for later"
    }
    spy = TransitionSpy(mock_case)
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy) as tmock:
        res = await run_recovery_agent(mock_case)
    
    assert res["final_status"] == "no_action"
    assert spy.states[-2:] == ["verifying", "no_action"]


@pytest.mark.asyncio
async def test_agent_approval_no_action_escalation_block(mock_case, ext_mocks):
    """Test 5: Approval / no_action / escalation block execution."""
    # Force agent to decide "Escalate" by hitting the retry guardrail
    mock_case["retry_count"] = 2
    
    spy = TransitionSpy(mock_case)
    with patch.object(RecoveryStateMachine, "transition_case", side_effect=spy) as tmock:
        res = await run_recovery_agent(mock_case)
    
    assert res["final_status"] == "escalated"
    assert "recovering" not in spy.states
    ext_mocks["exec"].assert_not_called()


@pytest.mark.asyncio
async def test_agent_unexpected_exception(mock_case, ext_mocks):
    """Test 6: Unexpected exception -> structured execution failure."""
    # We test this by making execute_recovery throw directly, which _node_execute should catch.
    ext_mocks["exec"].side_effect = Exception("Random crash")
    
    spy = TransitionSpy(mock_case)
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy) as tmock:
        res = await run_recovery_agent(mock_case)
    
    assert res["final_status"] == "failed"
    assert spy.states[-2:] == ["verifying", "failed"]


@pytest.mark.asyncio
async def test_batch_engine_uses_same_execution_path(mock_case, ext_mocks):
    """Test 7: Batch engine still uses same execution path and handles 'verifying' output."""
    spy = TransitionSpy(mock_case)
    
    with (
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock) as m_cases,
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock) as m_case,
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock) as m_create,
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock) as m_update,
        patch.object(RecoveryStateMachine, "transition_case", side_effect=spy) as tmock,
    ):
        m_cases.return_value = [mock_case]
        m_case.return_value = mock_case
        m_create.return_value = "batch_123"
        
        res = await BatchEngine.run_batch("merchant-test")
        
        assert res.status == "completed"
        assert res.successful_cases == 1
        assert res.case_results[0].final_state == "verifying"
        ext_mocks["exec"].assert_called_once()
