import pytest
import asyncio
from app.services.state_machine import RecoveryStateMachine, InvalidTransitionError
from unittest.mock import patch, MagicMock

# A simple mock case
MOCK_CASE = {
    "id": "test_case_1",
    "status": "detected"
}

@pytest.fixture
def mock_db_get():
    with patch("app.services.state_machine.db_get_recovery_case") as mock_get:
        mock_get.return_value = MOCK_CASE.copy()
        yield mock_get

@pytest.fixture
def mock_supabase():
    with patch("app.services.state_machine.get_supabase") as mock_sb:
        mock_client = MagicMock()
        mock_sb.return_value = mock_client
        yield mock_client

@pytest.mark.asyncio
async def test_valid_transitions(mock_db_get, mock_supabase):
    """Test a full valid workflow transition path."""
    # DETECTED -> ANALYZING
    mock_db_get.return_value = {"id": "test_case_1", "status": "detected"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "analyzing")
    assert res["status"] == "analyzing"

    # ANALYZING -> PREDICTING
    mock_db_get.return_value = {"id": "test_case_1", "status": "analyzing"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "predicting")
    assert res["status"] == "predicting"

    # PREDICTING -> DECIDING
    mock_db_get.return_value = {"id": "test_case_1", "status": "predicting"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "deciding")
    assert res["status"] == "deciding"

    # DECIDING -> RECOVERING
    mock_db_get.return_value = {"id": "test_case_1", "status": "deciding"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "recovering")
    assert res["status"] == "recovering"
    
    # RECOVERING -> VERIFYING
    mock_db_get.return_value = {"id": "test_case_1", "status": "recovering"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "verifying")
    assert res["status"] == "verifying"

    # VERIFYING -> RECOVERED
    mock_db_get.return_value = {"id": "test_case_1", "status": "verifying"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "recovered")
    assert res["status"] == "recovered"


@pytest.mark.asyncio
async def test_invalid_transitions(mock_db_get, mock_supabase):
    """Test that invalid jumps are explicitly rejected."""
    # RECOVERED -> RECOVERING (Terminal state violation)
    mock_db_get.return_value = {"id": "test_case_1", "status": "recovered"}
    with pytest.raises(InvalidTransitionError):
        await RecoveryStateMachine.transition_case("test_case_1", "recovering")

    # RECOVERED -> DECIDING
    with pytest.raises(InvalidTransitionError):
        await RecoveryStateMachine.transition_case("test_case_1", "deciding")

    # FAILED -> RECOVERING
    mock_db_get.return_value = {"id": "test_case_1", "status": "failed"}
    with pytest.raises(InvalidTransitionError):
        await RecoveryStateMachine.transition_case("test_case_1", "recovering")
        
    # EXPIRED -> DECIDING
    mock_db_get.return_value = {"id": "test_case_1", "status": "expired"}
    with pytest.raises(InvalidTransitionError):
        await RecoveryStateMachine.transition_case("test_case_1", "deciding")
        
    # ACTION_REQUIRED -> RECOVERING (Cannot bypass approval)
    mock_db_get.return_value = {"id": "test_case_1", "status": "action_required"}
    with pytest.raises(InvalidTransitionError):
        await RecoveryStateMachine.transition_case("test_case_1", "recovering")


@pytest.mark.asyncio
async def test_approval_flow(mock_db_get, mock_supabase):
    """Test that approval flow correctly sequences ACTION_REQUIRED -> APPROVED -> RECOVERING."""
    # DECIDING -> ACTION_REQUIRED
    mock_db_get.return_value = {"id": "test_case_1", "status": "deciding"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "action_required")
    assert res["status"] == "action_required"

    # ACTION_REQUIRED -> APPROVED
    mock_db_get.return_value = {"id": "test_case_1", "status": "action_required"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "approved")
    assert res["status"] == "approved"

    # APPROVED -> RECOVERING
    mock_db_get.return_value = {"id": "test_case_1", "status": "approved"}
    res = await RecoveryStateMachine.transition_case("test_case_1", "recovering")
    assert res["status"] == "recovering"


@pytest.mark.asyncio
async def test_persistence(mock_db_get, mock_supabase):
    """Verify that transition history is recorded."""
    mock_db_get.return_value = {"id": "test_case_1", "status": "detected"}
    
    await RecoveryStateMachine.transition_case("test_case_1", "analyzing", reason="Testing persistence", source="pytest")
    
    # Check that Supabase insert was called for transitions table
    mock_supabase.table.assert_any_call("recovery_case_transitions")
    # Check that Supabase update was called for recovery_cases table
    mock_supabase.table.assert_any_call("recovery_cases")
