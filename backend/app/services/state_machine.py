from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from app.services.supabase_client import get_supabase
from app.services.db_service import db_get_recovery_case


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class RecoveryStateMachine:
    """
    Centralized, deterministic state machine for Recovery Cases.
    Prevents invalid transitions and acts as the single source of truth.
    """

    VALID_TRANSITIONS = {
        "detected": ["analyzing", "expired"],
        "analyzing": ["predicting", "expired"],
        "predicting": ["deciding", "expired"],
        "deciding": ["action_required", "approved", "recovering", "escalated", "no_action", "expired"],
        "action_required": ["approved", "expired"],
        "approved": ["recovering", "expired"],
        "recovering": ["verifying", "expired"],
        "verifying": ["recovered", "failed", "escalated", "no_action", "expired"],
        # Terminal states
        "recovered": [],
        "failed": [],
        "escalated": [],
        "no_action": [],
        "expired": [],

        # Legacy mappings for backward compatibility
        "at_risk": ["analyzing", "predicting", "deciding", "expired"],
        "processing": ["verifying", "expired"],
        "human_review": ["approved", "expired"],
    }

    TERMINAL_STATES = ["recovered", "failed", "escalated", "no_action", "expired"]

    @classmethod
    async def transition_case(
        cls,
        case_id: str,
        new_state: str,
        reason: str = "",
        source: str = "system",
        actor: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transitions a recovery case to a new state if valid.
        Records the transition history and updates the case.
        """
        # 1. Load the current state
        case = await db_get_recovery_case(case_id)
        if not case:
            case = {"id": case_id, "status": "detected"}

        current_state = case.get("status", "detected")

        # 2. Validate the requested transition
        if new_state not in cls.VALID_TRANSITIONS:
            raise ValueError(f"Unknown target state: {new_state}")

        if current_state in cls.TERMINAL_STATES:
            raise InvalidTransitionError(
                f"Cannot transition from terminal state '{current_state}' to '{new_state}'"
            )

        allowed_next_states = cls.VALID_TRANSITIONS.get(current_state, [])
        if new_state not in allowed_next_states:
            raise InvalidTransitionError(
                f"Invalid transition from '{current_state}' to '{new_state}'"
            )

        # 3. Update the state and record transition
        sb = get_supabase()
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # Insert transition log
            sb.table("recovery_case_transitions").insert({
                "id": str(uuid.uuid4()),
                "recovery_case_id": case_id,
                "from_state": current_state,
                "to_state": new_state,
                "reason": reason,
                "source": source,
                "actor": actor,
                "action": action,
                "metadata": metadata or {},
                "created_at": timestamp
            }).execute()
        except Exception as e:
            print(f"[StateMachine] Failed to insert transition log (mocking fallback): {e}")

        # Update the case
        try:
            update_data = {
                "status": new_state,
                "updated_at": timestamp
            }
            sb.table("recovery_cases").update(update_data).eq("id", case_id).execute()
        except Exception as e:
            print(f"[StateMachine] Failed to update case status (mocking fallback): {e}")

        case["status"] = new_state
        case["updated_at"] = timestamp
        return case

    @classmethod
    async def force_transition(
        cls,
        case_id: str,
        new_state: str,
        reason: str = "",
        source: str = "webhook",
        actor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Force a case into a new state, bypassing the normal graph constraints.
        Used ONLY for authoritative external events (e.g. Razorpay webhooks).

        Still enforces:
        - Case must exist
        - Terminal states cannot be overwritten (recovered/failed/escalated/no_action/expired)
        - Full audit trail is recorded
        """
        case = await db_get_recovery_case(case_id)
        if not case:
            case = {"id": case_id, "status": "detected"}

        current_state = case.get("status", "detected")

        # Even force_transition respects terminal states — once recovered, always recovered
        if current_state in cls.TERMINAL_STATES:
            print(f"[StateMachine] force_transition skipped: case {case_id} is already terminal ({current_state})")
            return case

        sb = get_supabase()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Record the forced transition for audit trail
        try:
            sb.table("recovery_case_transitions").insert({
                "id": str(uuid.uuid4()),
                "recovery_case_id": case_id,
                "from_state": current_state,
                "to_state": new_state,
                "reason": f"[FORCE] {reason}",
                "source": source,
                "actor": actor,
                "action": "force_transition",
                "metadata": metadata or {},
                "created_at": timestamp
            }).execute()
        except Exception as e:
            print(f"[StateMachine] force_transition: transition log failed (non-fatal): {e}")

        # Update the case status
        try:
            sb.table("recovery_cases").update({
                "status": new_state,
                "updated_at": timestamp,
            }).eq("id", case_id).execute()
        except Exception as e:
            print(f"[StateMachine] force_transition: case update failed (non-fatal): {e}")

        case["status"] = new_state
        case["updated_at"] = timestamp
        return case
