from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.db_service import db_get_recovery_case, db_get_agent_logs, db_get_recovery_cases, db_update_recovery_case
from app.services.state_machine import RecoveryStateMachine
from app.agents.recovery_agent import run_recovery_agent

router = APIRouter()


@router.post("/run/{case_id}")
async def run_agent(case_id: str):
    case = await db_get_recovery_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    result = await run_recovery_agent(case)
    return result


@router.get("/logs/{case_id}")
async def get_agent_logs(case_id: str):
    logs = await db_get_agent_logs(case_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No agent logs found for this case")
    return logs


@router.get("/logs")
async def get_all_agent_logs():
    cases = await db_get_recovery_cases()
    result = []
    for case in cases[:20]:
        logs = await db_get_agent_logs(case["id"])
        if logs:
            result.append({
                "case_id": case["id"],
                "case_amount": case.get("amount_at_risk", 0),
                "case_failure": case.get("failure_reason", ""),
                "logs": logs,
            })
    return result


# ── Human Review Endpoints ────────────────────────────────────────────────────

class HumanReviewDecision(BaseModel):
    decision: str            # "approve" | "reject" | "escalate"
    reviewer_note: Optional[str] = None


@router.post("/human-review/{case_id}")
async def human_review(case_id: str, body: HumanReviewDecision):
    """
    Human reviewer manually approves, rejects, or escalates a case
    that is in action_required or escalated state.

    approve  → transitions to recovering and runs the agent to execute
    reject   → transitions to no_action
    escalate → stays in escalated, records note
    """
    case = await db_get_recovery_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    allowed_states = {"action_required", "escalated", "human_review"}
    if case.get("status") not in allowed_states:
        raise HTTPException(
            status_code=400,
            detail=f"Case is in '{case['status']}' state — human review only applies to: {', '.join(allowed_states)}"
        )

    if body.decision == "approve":
        # Human approves → override guardrail, mark approved, run agent
        await db_update_recovery_case(case_id, {
            "guardrail_passed": True,
            "human_review_note": body.reviewer_note or "Human approved",
            "human_reviewed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
        # Transition to approved so agent can execute
        await RecoveryStateMachine.force_transition(
            case_id, "approved",
            reason=f"Human approved: {body.reviewer_note or 'Manual approval'}",
            source="human",
        )
        # Re-fetch and run agent
        updated_case = await db_get_recovery_case(case_id)
        # Set guardrail_passed so agent skips the guardrail block
        updated_case["guardrail_passed"] = True
        result = await run_recovery_agent(updated_case)
        return {"decision": "approved", "agent_result": result}

    elif body.decision == "reject":
        await db_update_recovery_case(case_id, {
            "human_review_note": body.reviewer_note or "Human rejected",
            "human_reviewed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
        await RecoveryStateMachine.force_transition(
            case_id, "no_action",
            reason=f"Human rejected: {body.reviewer_note or 'Manual rejection'}",
            source="human",
        )
        return {"decision": "rejected", "status": "no_action"}

    elif body.decision == "escalate":
        await db_update_recovery_case(case_id, {
            "human_review_note": body.reviewer_note or "Escalated for further review",
            "human_reviewed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
        await RecoveryStateMachine.force_transition(
            case_id, "escalated",
            reason=f"Human escalated: {body.reviewer_note or 'Manual escalation'}",
            source="human",
        )
        return {"decision": "escalated", "status": "escalated"}

    else:
        raise HTTPException(status_code=400, detail="decision must be 'approve', 'reject', or 'escalate'")
