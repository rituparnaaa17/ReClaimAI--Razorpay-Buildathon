"""
Batch API — Phase 1, Step 2.

Endpoints:
  POST /api/recovery/batch            — trigger a batch run
  GET  /api/recovery/batch/{batch_id} — get batch status / results
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.batch_engine import BatchEngine
from app.services.batch_db import db_get_batch

router = APIRouter()


class BatchRequest(BaseModel):
    merchant_id: str
    case_ids: Optional[List[str]] = None  # omit = all eligible cases for merchant


@router.post("/batch")
async def run_batch(request: BatchRequest):
    """
    Trigger a batch recovery run for a merchant.

    - Selects all eligible (non-terminal) cases for the merchant.
    - Optionally restricts to a provided list of case_ids.
    - Processes each case via the existing LangGraph recovery agent.
    - Returns aggregate results including per-case outcomes.
    """
    if not request.merchant_id:
        raise HTTPException(status_code=400, detail="merchant_id is required")

    result = await BatchEngine.run_batch(
        merchant_id=request.merchant_id,
        case_ids=request.case_ids,
    )
    return result.to_dict()


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Retrieve a batch record by ID.
    Returns the current batch status and aggregate counters.
    Note: per-case results are not stored in the batch record —
    use this endpoint for status polling / observability.
    """
    batch = await db_get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return batch
