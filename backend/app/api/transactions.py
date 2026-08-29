from fastapi import APIRouter, Query
from typing import Optional
from app.services.db_service import db_get_transactions

router = APIRouter()


@router.get("/")
async def list_transactions(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    txns = await db_get_transactions(status=status, limit=limit + offset)
    return txns[offset: offset + limit]


@router.get("/{txn_id}")
async def get_transaction(txn_id: str):
    from app.services.db_service import db_get_transactions
    from fastapi import HTTPException
    txns = await db_get_transactions()
    txn = next((t for t in txns if t.get("id") == txn_id), None)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn
