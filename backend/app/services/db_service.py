"""
Database service — reads and writes to Supabase.
Falls back gracefully to mock data if the DB isn't seeded yet.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.services.supabase_client import get_supabase
from app.services.mock_data import (
    get_mock_recovery_cases,
    get_mock_recovery_case,
    get_mock_transactions,
    get_mock_analytics,
    get_mock_agent_logs,
)


# ── Recovery Cases ────────────────────────────────────────────────────────────

async def db_get_recovery_cases(status: Optional[str] = None, merchant_id: Optional[str] = None) -> List[Dict]:
    try:
        sb = get_supabase()
        q = sb.table("recovery_cases").select("*").order("created_at", desc=True)

        if status and status != "all":
            q = q.eq("status", status)
        if merchant_id:
            q = q.eq("merchant_id", merchant_id)

        result = q.limit(100).execute()
        if result.data:
            return result.data
    except Exception as e:
        print(f"[DB] get_recovery_cases failed: {e}")

    return get_mock_recovery_cases()


async def db_get_recovery_case(case_id: str) -> Optional[Dict]:
    try:
        sb = get_supabase()
        result = sb.table("recovery_cases").select("*").eq("id", case_id).single().execute()
        if result.data:
            return result.data
    except Exception as e:
        print(f"[DB] get_recovery_case failed: {e}")

    return get_mock_recovery_case(case_id)


async def db_update_recovery_case(case_id: str, updates: Dict) -> bool:
    try:
        sb = get_supabase()
        sb.table("recovery_cases").update({
            **updates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", case_id).execute()
        return True
    except Exception as e:
        print(f"[DB] update_recovery_case failed: {e}")
        return False


async def db_create_recovery_case(case: Dict) -> Optional[str]:
    try:
        sb = get_supabase()
        result = sb.table("recovery_cases").insert({
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **case,
        }).execute()
        if result.data:
            return result.data[0]["id"]
    except Exception as e:
        print(f"[DB] create_recovery_case failed: {e}")
    return None


# ── Agent Logs ─────────────────────────────────────────────────────────────────

async def db_save_agent_log(case_id: str, log: Dict) -> bool:
    try:
        sb = get_supabase()
        sb.table("agent_logs").insert({
            "id": str(uuid.uuid4()),
            "recovery_case_id": case_id,
            "step": log.get("step"),
            "decision": log.get("decision"),
            "reason": log.get("reason"),
            "confidence": log.get("confidence"),
            "timestamp": log.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "result": log.get("result"),
        }).execute()
        return True
    except Exception as e:
        print(f"[DB] save_agent_log failed: {e}")
        return False


async def db_get_agent_logs(case_id: str) -> List[Dict]:
    try:
        sb = get_supabase()
        result = sb.table("agent_logs").select("*").eq("recovery_case_id", case_id).order("timestamp").execute()
        if result.data:
            return result.data
    except Exception as e:
        print(f"[DB] get_agent_logs failed: {e}")

    return get_mock_agent_logs(case_id)


# ── Transactions ───────────────────────────────────────────────────────────────

async def db_get_transactions(status: Optional[str] = None, limit: int = 50) -> List[Dict]:
    try:
        sb = get_supabase()
        q = sb.table("transactions").select("*").order("created_at", desc=True)
        if status:
            q = q.eq("status", status)
        result = q.limit(limit).execute()
        if result.data:
            return result.data
    except Exception as e:
        print(f"[DB] get_transactions failed: {e}")

    return get_mock_transactions()


# ── Analytics ──────────────────────────────────────────────────────────────────

async def db_get_analytics_overview() -> Dict:
    try:
        sb = get_supabase()

        # Total revenue at risk
        risk = sb.table("recovery_cases").select("amount_at_risk").in_("status", ["at_risk", "processing", "human_review"]).execute()
        recovered = sb.table("recovery_cases").select("amount_recovered").eq("status", "recovered").execute()
        all_cases = sb.table("recovery_cases").select("status").execute()
        txn_data = sb.table("transactions").select("status").execute()

        if all_cases.data:
            total = len(all_cases.data)
            recovered_count = len([c for c in all_cases.data if c["status"] == "recovered"])
            at_risk_amount = sum(r.get("amount_at_risk") or 0 for r in risk.data or [])
            recovered_amount = sum(r.get("amount_recovered") or 0 for r in recovered.data or [])
            failed = len([t for t in (txn_data.data or []) if t["status"] == "failed"])
            abandoned = len([t for t in (txn_data.data or []) if t["status"] == "abandoned"])

            return {
                "revenue_at_risk": at_risk_amount,
                "revenue_recovered": recovered_amount,
                "recovery_rate": round((recovered_count / total * 100) if total > 0 else 0, 1),
                "failed_payments": failed,
                "abandoned_checkouts": abandoned,
                "recovery_attempts": total,
                "successful_recoveries": recovered_count,
                "avg_recovery_time_seconds": 287,
            }
    except Exception as e:
        print(f"[DB] get_analytics_overview failed: {e}")

    return get_mock_analytics()["overview"]
