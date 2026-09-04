"""
Batch DB Service — persistence operations for recovery_batches table.
Kept separate from batch_engine.py to preserve clean separation of concerns.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.services.supabase_client import get_supabase


async def db_create_batch(merchant_id: str, total_cases: int) -> Optional[str]:
    """
    Insert a new recovery_batch record and return its id.
    Returns None if the insert fails (caller should treat this as a batch-level failure).
    """
    batch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    try:
        sb = get_supabase()
        sb.table("recovery_batches").insert({
            "id": batch_id,
            "merchant_id": merchant_id,
            "status": "created",
            "total_cases": total_cases,
            "processed_cases": 0,
            "successful_cases": 0,
            "failed_cases": 0,
            "skipped_cases": 0,
            "created_at": now,
        }).execute()
        return batch_id
    except Exception as e:
        print(f"[BatchDB] db_create_batch failed: {e}")
        return None


async def db_update_batch(batch_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a recovery_batch record. All callers use this — no direct Supabase access
    outside this module.
    """
    try:
        sb = get_supabase()
        sb.table("recovery_batches").update(updates).eq("id", batch_id).execute()
        return True
    except Exception as e:
        print(f"[BatchDB] db_update_batch failed for {batch_id}: {e}")
        return False


async def db_get_batch(batch_id: str) -> Optional[Dict]:
    """
    Retrieve a recovery_batch record by id.
    """
    try:
        sb = get_supabase()
        result = sb.table("recovery_batches").select("*").eq("id", batch_id).single().execute()
        if result.data:
            return result.data
    except Exception as e:
        print(f"[BatchDB] db_get_batch failed for {batch_id}: {e}")
    return None
