from fastapi import APIRouter, HTTPException
from app.services.db_service import db_get_recovery_case, db_get_agent_logs, db_get_recovery_cases
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
    for case in cases[:10]:
        logs = await db_get_agent_logs(case["id"])
        if logs:
            result.append({
                "case_id": case["id"],
                "case_amount": case.get("amount_at_risk", 0),
                "case_failure": case.get("failure_reason", ""),
                "logs": logs,
            })
    return result
