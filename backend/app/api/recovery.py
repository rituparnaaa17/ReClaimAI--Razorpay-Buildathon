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
    return cases[offset: offset + limit]


@router.get("/cases/{case_id}")
async def get_recovery_case(case_id: str):
    case = await db_get_recovery_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
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
