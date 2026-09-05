import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
import razorpay

from app.services.razorpay_service import verify_payment_status, execute_recovery
from app.agents.recovery_agent import run_recovery_agent
from app.services.state_machine import RecoveryStateMachine
from app.services.batch_engine import BatchEngine

def _uuid(n: int) -> str:
    return f"00000000-0000-0000-0000-{n:012d}"

def _make_case(n: int, status: str = "detected", razorpay_payment_id: str = "pay_test_123") -> dict:
    return {
        "id": _uuid(n),
        "merchant_id": "merchant-test",
        "status": status,
        "amount_at_risk": 5000,
        "recovery_probability": 0.75,
        "failure_reason": "UPI_TIMEOUT",
        "payment_method": "UPI",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "retry_count": 0,
        "razorpay_payment_id": razorpay_payment_id,
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

@pytest.fixture
def base_ext():
    with (
        patch("app.agents.recovery_agent.generate_text", new_callable=AsyncMock) as m_gemini,
        patch("app.agents.recovery_agent.db_update_recovery_case", new_callable=AsyncMock) as m_db_upd,
        patch("app.agents.recovery_agent.db_save_agent_log", new_callable=AsyncMock) as m_db_log,
        patch("app.agents.recovery_agent.execute_recovery", new_callable=AsyncMock) as m_exec,
        patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory,
    ):
        m_gemini.return_value = '{"recommended_action": "Personalized Reminder", "confidence_score": 0.85, "reasoning": "Standard failure."}'
        m_db_upd.return_value = True
        m_db_log.return_value = True
        
        # Default execute to success so we reach verify
        m_exec.return_value = {
            "status": "executed",
            "action_attempted": "Personalized Reminder",
            "razorpay_identifier": "plink_test_123",
            "error_code": None,
            "error_description": None,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        m_client_factory.return_value.payment_link.fetch.return_value = {
            "status": "paid",
            "payments": [{"status": "captured", "amount": 50000, "currency": "INR"}],
        }
        m_client_factory.return_value.payment.fetch.return_value = {
            "status": "captured",
            "amount": 50000,
            "currency": "INR",
        }
        
        yield {
            "gemini": m_gemini,
            "db_upd": m_db_upd,
            "db_log": m_db_log,
            "exec": m_exec,
            "client_factory": m_client_factory
        }

# ── Tests for Razorpay verification mapping ───────────────────────────────────

@pytest.mark.asyncio
async def test_verification_captured():
    """Test 1 - Captured payment -> recovered"""
    case = _make_case(1)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.return_value = {"status": "captured"}
        
        result = await verify_payment_status(case)
        assert result["status"] == "recovered"
        assert result["razorpay_status"] == "captured"

@pytest.mark.asyncio
async def test_verification_failed():
    """Test 2 - Failed payment -> not_recovered/failed"""
    case = _make_case(2)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.return_value = {"status": "failed"}
        
        result = await verify_payment_status(case)
        assert result["status"] == "not_recovered"
        assert result["razorpay_status"] == "failed"

@pytest.mark.asyncio
async def test_verification_authorized():
    """Test 3 - Authorized payment -> not recovered (stays verifying)"""
    case = _make_case(3)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.return_value = {"status": "authorized"}
        
        result = await verify_payment_status(case)
        assert result["status"] == "not_recovered"
        assert result["razorpay_status"] == "authorized"

@pytest.mark.asyncio
async def test_verification_created():
    """Test 4 - Created payment -> not recovered (stays verifying)"""
    case = _make_case(4)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.return_value = {"status": "created"}
        
        result = await verify_payment_status(case)
        assert result["status"] == "not_recovered"
        assert result["razorpay_status"] == "created"

@pytest.mark.asyncio
async def test_verification_refunded():
    """Test 5 - Refunded payment -> not recovered (stays verifying)"""
    case = _make_case(5)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.return_value = {"status": "refunded"}
        
        result = await verify_payment_status(case)
        assert result["status"] == "not_recovered"
        assert result["razorpay_status"] == "refunded"

@pytest.mark.asyncio
async def test_verification_api_error():
    """Test 6 - Razorpay API error -> verification_failed"""
    case = _make_case(6)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.side_effect = razorpay.errors.BadRequestError("Invalid payment ID")
        
        result = await verify_payment_status(case)
        assert result["status"] == "verification_failed"
        assert result["razorpay_status"] is None

@pytest.mark.asyncio
async def test_verification_network_error():
    """Test 7 - Timeout/Network error -> verification_failed"""
    case = _make_case(7)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        m_client = m_client_factory.return_value
        m_client.payment.fetch.side_effect = Exception("Connection timeout")
        
        result = await verify_payment_status(case)
        assert result["status"] == "verification_failed"
        assert result["razorpay_status"] is None

@pytest.mark.asyncio
async def test_verification_missing_id():
    """Test 8 - Missing payment ID -> verification_failed (stays verifying)"""
    case = _make_case(8, razorpay_payment_id=None)
    with patch("app.services.razorpay_service.get_razorpay_client") as m_client_factory:
        result = await verify_payment_status(case)
        
        # Razorpay should not be called
        m_client_factory.assert_not_called()
        
        assert result["status"] == "verification_failed"
        assert result["razorpay_status"] is None

# ── Tests for Agent Integration with Verification ─────────────────────────────

@pytest.mark.asyncio
async def test_agent_current_state_override(base_ext):
    """
    Test 9 - Current-state override:
    Starts as failed payment in DB, but Razorpay fetch returns captured.
    Agent must use Razorpay state and transition to recovered.
    """
    case = _make_case(9, status="failed") # Start as a failed payment
    spy = TransitionSpy(case)
    
    m_client = base_ext["client_factory"].return_value
    m_client.payment.fetch.return_value = {"status": "captured"}
    
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy):
        res = await run_recovery_agent(case)
        
    # The agent successfully verified it as captured
    assert res["final_status"] == "recovered"
    # State transitions: analyzing -> predicting -> deciding -> approved -> recovering -> verifying -> recovered
    assert "recovering" in spy.states
    assert "verifying" in spy.states
    assert spy.states[-1] == "recovered"

@pytest.mark.asyncio
async def test_agent_execution_success_does_not_bypass(base_ext):
    """
    Test 10 - Execution success does not bypass verification:
    If execute returns 'executed', but verify fails (API error),
    it stays in verifying, never reaching 'recovered'.
    """
    case = _make_case(10)
    spy = TransitionSpy(case)
    
    # execute_recovery returns success (via fixture)
    # But verification fails:
    m_client = base_ext["client_factory"].return_value
    m_client.payment_link.fetch.side_effect = Exception("API Down")
    m_client.payment.fetch.side_effect = Exception("API Down")
    
    with patch.object(RecoveryStateMachine, "transition_case", new_callable=AsyncMock, side_effect=spy):
        res = await run_recovery_agent(case)
        
    assert res["final_status"] == "verifying"
    assert "recovered" not in spy.states
    assert spy.states[-1] == "verifying"

@pytest.mark.asyncio
async def test_agent_batch_integration(base_ext):
    """
    Test 11 - Batch integration:
    Batch engine should run and respect the new verification flow, mapping to success processing,
    and final business state is 'recovered' if verified captured.
    """
    case = _make_case(11, status="detected")
    spy = TransitionSpy(case)
    
    m_client = base_ext["client_factory"].return_value
    m_client.payment_link.fetch.return_value = {
        "status": "paid",
        "payments": [{"status": "captured", "amount": 50000, "currency": "INR"}],
    }
    
    with (
        patch("app.services.batch_engine.db_get_recovery_cases", new_callable=AsyncMock) as m_cases,
        patch("app.services.batch_engine.db_get_recovery_case", new_callable=AsyncMock) as m_case,
        patch("app.services.batch_engine.db_create_batch", new_callable=AsyncMock) as m_create,
        patch("app.services.batch_engine.db_update_batch", new_callable=AsyncMock) as m_update,
        patch.object(RecoveryStateMachine, "transition_case", side_effect=spy) as tmock,
    ):
        m_cases.return_value = [case]
        m_case.return_value = case
        m_create.return_value = "batch_456"
        
        res = await BatchEngine.run_batch("merchant-test")
        
        assert res.status == "completed"
        assert res.successful_cases == 1
        assert res.case_results[0].final_state == "recovered"
        
        # Verify it went through the full flow
        base_ext["exec"].assert_called_once()
        m_client.payment_link.fetch.assert_called_once_with("plink_test_123")
