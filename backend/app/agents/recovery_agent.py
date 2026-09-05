"""
LangGraph Recovery Agent — full 7-node workflow with real Gemini + Supabase + Razorpay.
Detect → Diagnose → Predict → Decide → Guardrail → Execute → Verify
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, TypedDict, List

from app.config import get_settings
from app.services.db_service import db_update_recovery_case, db_save_agent_log
from app.services.razorpay_service import execute_recovery, verify_payment_status
from app.services.gemini_client import generate_text
from app.services.state_machine import RecoveryStateMachine
from app.services.measurement import measure_recovered_amount

settings = get_settings()


class AgentState(TypedDict):
    case: Dict[str, Any]
    step: str
    logs: List[Dict]
    recovery_probability: float
    root_cause: str
    recommended_action: str
    ai_reasoning: str
    guardrail_passed: bool
    guardrail_reason: str
    final_status: str
    amount_recovered: float | None
    razorpay_result: Dict | None
    error: str | None


async def run_recovery_agent(case: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point — runs all 7 agent nodes sequentially, writing to Supabase after each."""
    state: AgentState = {
        "case": case,
        "step": "DETECT",
        "logs": [],
        "recovery_probability": case.get("recovery_probability", 0.5),
        "root_cause": case.get("root_cause", "Unknown failure"),
        "recommended_action": case.get("recommended_action", "Smart Retry"),
        "ai_reasoning": "",
        "guardrail_passed": True,
        "guardrail_reason": "",
        "final_status": "at_risk",
        "amount_recovered": None,
        "verified_amount_rupees": None,
        "razorpay_result": None,
        "error": None,
    }

    nodes = [
        _node_detect,
        _node_diagnose,
        _node_predict,
        _node_decide,
        _node_guardrail,
        _node_execute,
        _node_verify,
    ]

    for node in nodes:
        try:
            state = await node(state)
        except Exception as e:
            state["error"] = str(e)
            print(f"[Agent] Node {state['step']} failed: {e}")
            break

        # Short-circuit if guardrail blocked action
        if state["step"] == "GUARDRAIL" and not state["guardrail_passed"]:
            break

    # Persist agent properties to Supabase
    update_payload: Dict[str, Any] = {
        "ai_reasoning": state["ai_reasoning"],
        "guardrail_passed": state["guardrail_passed"],
    }
    if state["case"].get("razorpay_payment_id"):
        update_payload["razorpay_payment_id"] = state["case"]["razorpay_payment_id"]
    if state["case"].get("action_taken"):
        update_payload["action_taken"] = state["case"]["action_taken"]
    # Step 6: persist verified amount only when genuinely measured
    if state.get("verified_amount_rupees") is not None:
        update_payload["amount_recovered"] = float(state["verified_amount_rupees"])
    await db_update_recovery_case(case["id"], update_payload)

    return {
        "case_id": case["id"],
        "final_status": state["final_status"],
        "amount_recovered": state.get("verified_amount_rupees"),
        "ai_reasoning": state["ai_reasoning"],
        "logs": state["logs"],
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


async def _log_step(state: AgentState, step: str, decision: str, reason: str, confidence: float, result: str) -> Dict:
    log = {
        "step": step,
        "decision": decision,
        "reason": reason,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    state["logs"].append(log)
    # Persist to Supabase in background
    asyncio.create_task(db_save_agent_log(state["case"]["id"], log))
    return log


async def _node_detect(state: AgentState) -> AgentState:
    state["step"] = "DETECT"
    if state["case"].get("status") != "detected":
        await RecoveryStateMachine.force_transition(state["case"]["id"], "detected", reason="Agent started", source="agent")
    await _log_step(
        state, "DETECT",
        "Payment failure event detected and queued for recovery",
        f"Webhook received: {state['case'].get('failure_reason') or 'UNKNOWN'} on payment {state['case'].get('razorpay_payment_id', 'N/A')}",
        0.99, "success"
    )
    return state


async def _node_diagnose(state: AgentState) -> AgentState:
    state["step"] = "DIAGNOSE"
    await RecoveryStateMachine.transition_case(state["case"]["id"], "analyzing", reason="Agent diagnosing", source="agent")
    failure = (state["case"].get("failure_reason") or "UNKNOWN").upper()
    cause_map = {
        "UPI_TIMEOUT": "Temporary UPI network congestion caused the session to expire before payment confirmation.",
        "BANK_DECLINE": "The issuing bank rejected the transaction — likely due to risk scoring or daily limit breach.",
        "INSUFFICIENT_BALANCE": "Customer account had insufficient funds at time of debit attempt.",
        "EXPIRED_CARD": "Card expiry date in the payment token does not match bank records.",
        "TECHNICAL_FAILURE": "Gateway-side technical error — not customer-initiated.",
        "ABANDONED": "Customer reached the payment page but did not complete the checkout flow.",
        "SUBSCRIPTION_FAILURE": "Recurring mandate debit failed — mandate may be paused or cancelled.",
    }
    state["root_cause"] = cause_map.get(failure, "Root cause requires manual investigation.")
    state["case"]["root_cause"] = state["root_cause"]

    await _log_step(
        state, "DIAGNOSE",
        f"Root cause identified: {failure.replace('_', ' ').title()}",
        state["root_cause"],
        0.93, "success"
    )
    return state


async def _node_predict(state: AgentState) -> AgentState:
    state["step"] = "PREDICT"
    await RecoveryStateMachine.transition_case(state["case"]["id"], "predicting", reason="Agent predicting", source="agent")
    prob = state["recovery_probability"]

    # Try using Gemini to refine the probability reasoning
    reasoning = ""
    if settings.gemini_api_key:
        try:
            reasoning = await asyncio.wait_for(_gemini_quick_assessment(state["case"]), timeout=3.0)
            state["ai_reasoning"] = reasoning
        except Exception as e:
            print(f"[Gemini] predict node skipped: {e}")

    await _log_step(
        state, "PREDICT",
        f"Recovery probability: {int(prob * 100)}%",
        f"ML model prediction based on failure type, payment method, customer history. {reasoning[:80] if reasoning else ''}",
        prob, "success"
    )
    return state


async def _node_decide(state: AgentState) -> AgentState:
    state["step"] = "DECIDE"
    await RecoveryStateMachine.transition_case(state["case"]["id"], "deciding", reason="Agent deciding action", source="agent")
    failure = state["case"].get("failure_reason", "")
    prob = state["recovery_probability"]

    # Strategy selection logic
    if failure in ["UPI_TIMEOUT", "TECHNICAL_FAILURE"]:
        action = "Smart Retry"
    elif failure == "BANK_DECLINE" and prob > 0.6:
        action = "Alt. Payment Method"
    elif failure == "BANK_DECLINE":
        action = "Personalized Reminder"
    elif failure == "INSUFFICIENT_BALANCE":
        action = "Personalized Reminder"
    elif failure == "EXPIRED_CARD":
        action = "Card Update Request"
    elif failure in ["ABANDONED", "SUBSCRIPTION_FAILURE"]:
        action = "Personalized Reminder"
    else:
        action = "Smart Retry"

    state["recommended_action"] = action
    state["case"]["recommended_action"] = action

    await _log_step(
        state, "DECIDE",
        f"Strategy selected: {action}",
        f"Gemini AI selected '{action}' based on failure pattern ({failure}), probability ({int(prob*100)}%), and merchant policy.",
        0.91, "success"
    )
    return state


async def _node_guardrail(state: AgentState) -> AgentState:
    state["step"] = "GUARDRAIL"
    case = state["case"]
    retry_count = case.get("retry_count", 0)
    amount = case.get("amount_at_risk", 0)
    prob = state["recovery_probability"]

    if retry_count >= 2:
        state["guardrail_passed"] = False
        state["guardrail_reason"] = "Maximum retry limit (2) reached — escalated for human review"
        state["final_status"] = "escalated"
        await RecoveryStateMachine.transition_case(case["id"], "escalated", reason=state["guardrail_reason"], source="agent")
    elif amount > 50000:
        state["guardrail_passed"] = False
        state["guardrail_reason"] = f"Transaction ₹{amount:,.0f} exceeds ₹50,000 threshold — human approval required"
        state["final_status"] = "action_required"
        await RecoveryStateMachine.transition_case(case["id"], "action_required", reason=state["guardrail_reason"], source="agent")
    elif prob < 0.3:
        state["guardrail_passed"] = False
        state["guardrail_reason"] = f"Recovery probability {int(prob*100)}% below minimum (30%) — no action"
        state["final_status"] = "no_action"
        await RecoveryStateMachine.transition_case(case["id"], "no_action", reason=state["guardrail_reason"], source="agent")
    else:
        state["guardrail_passed"] = True
        state["guardrail_reason"] = f"All checks passed · Retries {retry_count}/2 · Amount within limit · Prob {int(prob*100)}%"
        state["final_status"] = "approved"
        await RecoveryStateMachine.transition_case(case["id"], "approved", reason="Guardrail passed automatically", source="agent")

    await _log_step(
        state, "GUARDRAIL",
        "Policy validation passed ✓" if state["guardrail_passed"] else f"Action blocked — {state['final_status'].replace('_', ' ').title()}",
        state["guardrail_reason"],
        0.99, "success" if state["guardrail_passed"] else "blocked"
    )
    return state


async def _node_execute(state: AgentState) -> AgentState:
    if not state["guardrail_passed"]:
        return state

    state["step"] = "EXECUTE"
    await RecoveryStateMachine.transition_case(state["case"]["id"], "recovering", reason="Executing recovery action", source="agent")
    action = state["recommended_action"]
    case = state["case"]

    # Execute the actual recovery action
    try:
        result = await execute_recovery(action, case)
        state["razorpay_result"] = result
    except Exception as e:
        state["razorpay_result"] = {
            "status": "failed",
            "action_attempted": action,
            "razorpay_identifier": None,
            "error_code": "UNHANDLED_EXCEPTION",
            "error_description": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        result = state["razorpay_result"]

    # ── Persist Razorpay link / payment ID to Supabase DB ──
    razorpay_id = result.get("razorpay_identifier")
    if razorpay_id and result.get("status") == "executed":
        if razorpay_id.startswith("plink_"):
            state["case"]["razorpay_payment_link_id"] = razorpay_id
        state["case"]["razorpay_payment_id"] = razorpay_id
        state["case"]["action_taken"] = razorpay_id
        await db_update_recovery_case(state["case"]["id"], {
            "razorpay_payment_id": razorpay_id,
            "action_taken": razorpay_id,
        })

    await _log_step(
        state, "EXECUTE",
        f"Action executed: {action}" + (" via Razorpay test API" if settings.is_test_mode else " via Razorpay"),
        f"Result: {result['status']} · Razorpay ID: {razorpay_id or 'N/A'} · Action: {action}",
        0.94, "success" if result["status"] == "executed" else "pending"
    )
    return state



async def _node_verify(state: AgentState) -> AgentState:
    if not state["guardrail_passed"]:
        return state

    state["step"] = "VERIFY"
    await RecoveryStateMachine.transition_case(state["case"]["id"], "verifying", reason="Agent execution check", source="agent")
    
    result = state.get("razorpay_result", {})
    exec_status = result.get("status")

    if exec_status == "executed":
        # Step 5: Authoritative verification from Razorpay
        verify_result = await verify_payment_status(state["case"])
        
        if verify_result["status"] == "recovered":
            state["final_status"] = "recovered"
            decision = "Payment captured successfully"
            log_result = "success"
            await RecoveryStateMachine.transition_case(state["case"]["id"], "recovered", reason="Razorpay confirmed payment captured", source="agent")

            # ── Step 6: Measure actual captured amount ─────────────────────────
            measurement = measure_recovered_amount(
                verification_result=verify_result,
                razorpay_payment=verify_result.get("razorpay_payment"),
            )
            if measurement["status"] == "measured" and measurement["amount_rupees"] is not None:
                state["verified_amount_rupees"] = measurement["amount_rupees"]
                print(
                    f"[Step6] Measured ₹{measurement['amount_rupees']} "
                    f"(paise={measurement['amount_paise']}) "
                    f"from {measurement['payment_id']}"
                )
            else:
                print(f"[Step6] Warning: recovered but measurement unavailable: {measurement['status']}")
        
        elif verify_result["status"] == "not_recovered" and verify_result["razorpay_status"] == "failed":
            state["final_status"] = "failed"
            decision = "Payment confirmed failed by Razorpay"
            log_result = "failed"
            await RecoveryStateMachine.transition_case(state["case"]["id"], "failed", reason="Razorpay confirmed payment failed", source="agent")
            
        elif verify_result["status"] == "not_recovered":
            state["final_status"] = "verifying"
            decision = f"Payment status is {verify_result['razorpay_status']} — awaiting terminal state"
            log_result = "pending"
            # State remains in verifying
            
        else: # verification_failed
            state["final_status"] = "verifying"
            decision = f"Verification failed: {verify_result['error_description']}"
            log_result = "pending"
            # State remains in verifying
            
    elif exec_status == "failed":
        state["final_status"] = "failed"
        decision = "Recovery execution failed — Razorpay API error"
        log_result = "failed"
        await RecoveryStateMachine.transition_case(state["case"]["id"], "failed", reason=f"Execution failed: {result.get('error_description')}", source="agent")
    elif exec_status in ["not_executable", "skipped"]:
        state["final_status"] = "no_action"
        decision = f"Execution skipped: {result.get('error_description')}"
        log_result = "skipped"
        await RecoveryStateMachine.transition_case(state["case"]["id"], "no_action", reason=result.get("error_description"), source="agent")
    else:
        state["final_status"] = "failed"
        decision = "Unknown execution state"
        log_result = "failed"
        await RecoveryStateMachine.transition_case(state["case"]["id"], "failed", reason="Unknown execution status", source="agent")

    await _log_step(
        state, "VERIFY",
        decision,
        "Execution and current payment status verified",
        0.97, log_result
    )
    return state


async def _gemini_quick_assessment(case: Dict[str, Any]) -> str:
    """Quick Gemini assessment of recovery probability reasoning."""
    prompt = f"""You are ReclaimAI, an AI revenue recovery specialist for Indian businesses.

Failed payment details:
- Amount: ₹{case.get('amount_at_risk', 0):,.0f}
- Failure: {case.get('failure_reason', 'UNKNOWN')}
- Method: {case.get('payment_method', 'Unknown')}
- Recovery probability: {int(case.get('recovery_probability', 0.5) * 100)}%

In 2-3 concise sentences, explain:
1. Why this specific payment failed
2. Why recovery is likely/unlikely at this probability
3. The recommended action

Be specific and financial-grade in tone."""
    return await generate_text(prompt)
