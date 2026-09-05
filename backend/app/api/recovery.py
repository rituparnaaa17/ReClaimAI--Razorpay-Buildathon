from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.db_service import (
    db_get_recovery_cases, db_get_recovery_case,
    db_get_agent_logs, db_update_recovery_case
)
from app.services.recovery_service import analyze_case, execute_recovery_action

router = APIRouter()


@router.get("/cases")
async def list_recovery_cases(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    cases = await db_get_recovery_cases(status=status)
    # Auto-sync live statuses for active recovering/verifying cases
    for i, c in enumerate(cases):
        if c.get("status") in ["recovering", "verifying"] and (c.get("razorpay_payment_link_id") or c.get("razorpay_payment_id")):
            try:
                v_res = await verify_payment_status(c)
                if v_res["status"] == "recovered":
                    await RecoveryStateMachine.force_transition(c["id"], "recovered", reason="Live status sync from Razorpay", source="system")
                    meas = measure_recovered_amount(verification_result=v_res, razorpay_payment=v_res.get("razorpay_payment"))
                    amt = float(meas["amount_rupees"]) if meas["status"] == "measured" and meas["amount_rupees"] is not None else float(c.get("amount_at_risk", 0))
                    await db_update_recovery_case(c["id"], {"status": "recovered", "amount_recovered": amt})
                    cases[i] = {**c, "status": "recovered", "amount_recovered": amt}
                elif v_res["status"] == "not_recovered" and v_res.get("razorpay_status") in ["failed", "cancelled", "expired"]:
                    await RecoveryStateMachine.force_transition(c["id"], "failed", reason="Live status sync: payment failed/cancelled/expired", source="system")
                    await db_update_recovery_case(c["id"], {"status": "failed"})
                    cases[i] = {**c, "status": "failed"}
            except Exception as e:
                print(f"[Recovery API] Live sync warning for case {c.get('id')}: {e}")

    return cases[offset: offset + limit]


from app.services.razorpay_service import verify_payment_status
from app.services.state_machine import RecoveryStateMachine
from app.services.measurement import measure_recovered_amount


@router.get("/cases/{case_id}")
async def get_recovery_case(case_id: str):
    case = await db_get_recovery_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    # Auto-sync live status from Razorpay if in recovering or verifying state
    if case.get("status") in ["recovering", "verifying"] and (case.get("razorpay_payment_link_id") or case.get("razorpay_payment_id")):
        try:
            v_res = await verify_payment_status(case)
            if v_res["status"] == "recovered":
                await RecoveryStateMachine.force_transition(case_id, "recovered", reason="Live status sync from Razorpay", source="system")
                meas = measure_recovered_amount(verification_result=v_res, razorpay_payment=v_res.get("razorpay_payment"))
                amt = float(meas["amount_rupees"]) if meas["status"] == "measured" and meas["amount_rupees"] is not None else float(case.get("amount_at_risk", 0))
                await db_update_recovery_case(case_id, {"status": "recovered", "amount_recovered": amt})
                case = await db_get_recovery_case(case_id)
            elif v_res["status"] == "not_recovered" and v_res.get("razorpay_status") in ["failed", "cancelled", "expired"]:
                await RecoveryStateMachine.force_transition(case_id, "failed", reason="Live status sync: payment failed/cancelled/expired", source="system")
                await db_update_recovery_case(case_id, {"status": "failed"})
                case = await db_get_recovery_case(case_id)
        except Exception as e:
            print(f"[Recovery API] Live status check warning: {e}")

    logs = await db_get_agent_logs(case_id)
    return {**case, "agent_logs": logs}


@router.post("/analyze/{case_id}")
async def analyze_recovery_case(case_id: str):
    case = await db_get_recovery_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    result = await analyze_case(case)
    return result


@router.post("/execute/{case_id}")
async def execute_recovery(case_id: str):
    case = await db_get_recovery_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    result = await execute_recovery_action(case)
    return result
