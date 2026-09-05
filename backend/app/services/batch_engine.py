"""
Batch Recovery Engine — Phase 1, Step 2.

Orchestrates multiple recovery cases in a controlled, observable batch run.

Architecture:
  BatchEngine
    ↓ selects and orchestrates cases
  RecoveryStateMachine
    ↓ controls legal lifecycle transitions (NOT bypassed here)
  run_recovery_agent()
    ↓ the existing LangGraph agent handles all AI/execution/verification logic

The engine does NOT contain business logic that belongs to the agent.
It does NOT directly manipulate case state — all transitions go through
RecoveryStateMachine.

Batch states:
  created → running → completed        (all cases processed, none threw exceptions)
                    → partial_failure  (batch finished, ≥1 case threw an exception)
                    → failed           (infrastructure failure; batch could not proceed)
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.services.db_service import db_get_recovery_cases, db_get_recovery_case
from app.services.state_machine import RecoveryStateMachine
from app.services.batch_db import db_create_batch, db_update_batch
from app.agents.recovery_agent import run_recovery_agent


# ── Eligible States ───────────────────────────────────────────────────────────

# Terminal states the batch engine must NEVER process.
# These mirror RecoveryStateMachine.TERMINAL_STATES plus the legacy values.
TERMINAL_STATES = frozenset([
    "recovered", "failed", "escalated", "no_action", "expired",
])

# Active (non-terminal) states that are eligible for batch processing.
ELIGIBLE_STATES = frozenset([
    # New state machine states
    "detected", "analyzing", "predicting", "deciding",
    "action_required", "approved", "recovering", "verifying",
    # Legacy states kept for backward compatibility
    "at_risk", "processing", "human_review",
])


# ── Case Result ───────────────────────────────────────────────────────────────

@dataclass
class CaseResult:
    """Structured result for a single case processed within a batch."""
    case_id: str
    initial_state: str
    final_state: str
    result: str           # "success" | "failed" | "skipped"
    reason: str = ""
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "initial_state": self.initial_state,
            "final_state": self.final_state,
            "result": self.result,
            "reason": self.reason,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


# ── Batch Result ──────────────────────────────────────────────────────────────

@dataclass
class BatchResult:
    """Aggregate result returned from BatchEngine.run_batch()."""
    batch_id: str
    merchant_id: str
    status: str
    total_cases: int = 0
    processed_cases: int = 0
    successful_cases: int = 0
    failed_cases: int = 0
    skipped_cases: int = 0
    case_results: List[CaseResult] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "merchant_id": self.merchant_id,
            "status": self.status,
            "total_cases": self.total_cases,
            "processed_cases": self.processed_cases,
            "successful_cases": self.successful_cases,
            "failed_cases": self.failed_cases,
            "skipped_cases": self.skipped_cases,
            "case_results": [r.to_dict() for r in self.case_results],
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


# ── Batch Engine ──────────────────────────────────────────────────────────────

class BatchEngine:
    """
    Orchestrates batch recovery processing.

    Usage:
        result = await BatchEngine.run_batch(merchant_id="...", case_ids=[...])
    """

    @classmethod
    async def run_batch(
        cls,
        merchant_id: str,
        case_ids: Optional[List[str]] = None,
    ) -> BatchResult:
        """
        Main entry point for batch recovery processing.

        Args:
            merchant_id: Scope for the batch — only this merchant's cases are processed.
            case_ids:    Optional explicit list of case IDs to process. If omitted,
                         all eligible cases for the merchant are selected.

        Returns:
            BatchResult with aggregate counts and per-case outcomes.
        """
        started_at = datetime.now(timezone.utc).isoformat()
        print(f"[BatchEngine] Starting batch for merchant={merchant_id}")

        # ── 1. Select eligible cases ──────────────────────────────────────────
        try:
            eligible_cases = await cls._select_eligible_cases(merchant_id, case_ids)
        except Exception as e:
            # Infrastructure failure during case selection — cannot proceed safely
            err = f"Failed to select eligible cases: {e}"
            print(f"[BatchEngine] BATCH FAILED — {err}")
            # Attempt to create a failed batch record for observability
            batch_id = await db_create_batch(merchant_id, 0) or "unknown"
            await db_update_batch(batch_id, {
                "status": "failed",
                "error_message": err,
                "started_at": started_at,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            return BatchResult(
                batch_id=batch_id,
                merchant_id=merchant_id,
                status="failed",
                error_message=err,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        total = len(eligible_cases)
        print(f"[BatchEngine] {total} eligible cases selected")

        # ── 2. Create the batch record ────────────────────────────────────────
        batch_id = await db_create_batch(merchant_id, total)
        if not batch_id:
            # DB unavailable — batch-level failure
            err = "Failed to create batch record in database"
            print(f"[BatchEngine] BATCH FAILED — {err}")
            return BatchResult(
                batch_id="unknown",
                merchant_id=merchant_id,
                status="failed",
                total_cases=total,
                error_message=err,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        # Mark batch as running
        await db_update_batch(batch_id, {
            "status": "running",
            "started_at": started_at,
        })

        result = BatchResult(
            batch_id=batch_id,
            merchant_id=merchant_id,
            status="running",
            total_cases=total,
            started_at=started_at,
        )

        # ── 3. Handle empty batch gracefully ──────────────────────────────────
        if total == 0:
            completed_at = datetime.now(timezone.utc).isoformat()
            await db_update_batch(batch_id, {
                "status": "completed",
                "completed_at": completed_at,
            })
            result.status = "completed"
            result.completed_at = completed_at
            print(f"[BatchEngine] Batch {batch_id} completed — no eligible cases")
            return result

        # ── 4. Process each case in isolation ────────────────────────────────
        exception_count = 0

        for case in eligible_cases:
            case_result = await cls._process_case(case, batch_id, merchant_id)
            result.case_results.append(case_result)
            result.processed_cases += 1

            if case_result.result == "success":
                result.successful_cases += 1
            elif case_result.result == "skipped":
                result.skipped_cases += 1
                result.processed_cases -= 1   # skipped ≠ processed
            else:
                result.failed_cases += 1
                if case_result.error:
                    exception_count += 1

            # Update batch counters in DB after each case
            await db_update_batch(batch_id, {
                "processed_cases": result.processed_cases,
                "successful_cases": result.successful_cases,
                "failed_cases": result.failed_cases,
                "skipped_cases": result.skipped_cases,
            })

        # ── 5. Finalize batch status ──────────────────────────────────────────
        completed_at = datetime.now(timezone.utc).isoformat()
        result.completed_at = completed_at

        if exception_count > 0:
            # Batch finished but some cases threw exceptions during processing
            result.status = "partial_failure"
        else:
            result.status = "completed"

        await db_update_batch(batch_id, {
            "status": result.status,
            "completed_at": completed_at,
        })

        print(
            f"[BatchEngine] Batch {batch_id} {result.status} — "
            f"total={result.total_cases} processed={result.processed_cases} "
            f"success={result.successful_cases} failed={result.failed_cases} "
            f"skipped={result.skipped_cases}"
        )
        return result

    # ── Private helpers ───────────────────────────────────────────────────────

    @classmethod
    async def _select_eligible_cases(
        cls,
        merchant_id: str,
        case_ids: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """
        Fetch and filter eligible cases for this merchant.

        Merchant isolation: only cases where merchant_id matches are returned.
        The existing db_get_recovery_cases() already applies the merchant filter,
        which in a Supabase RLS environment means RLS will also enforce it.

        If case_ids are provided, only those IDs are considered — but they are
        still filtered for merchant ownership and eligibility.
        """
        if case_ids:
            # Fetch specific cases individually to preserve merchant check
            cases = []
            for cid in case_ids:
                case = await db_get_recovery_case(cid)
                if case:
                    # Merchant isolation: skip cases that don't belong to this merchant
                    if case.get("merchant_id") != merchant_id:
                        print(
                            f"[BatchEngine] SECURITY: case {cid} belongs to "
                            f"merchant {case.get('merchant_id')}, not {merchant_id} — skipping"
                        )
                        continue
                    cases.append(case)
        else:
            # Fetch all cases for this merchant (db layer already filters by merchant_id)
            cases = await db_get_recovery_cases(merchant_id=merchant_id)

        # Filter to eligible states only — do NOT process terminal cases
        eligible = [c for c in cases if cls._is_eligible(c)]
        terminal_count = len(cases) - len(eligible)
        if terminal_count > 0:
            print(f"[BatchEngine] Filtered out {terminal_count} terminal/ineligible cases")
        return eligible

    @classmethod
    def _is_eligible(cls, case: Dict[str, Any]) -> bool:
        """
        Returns True if the case is in an active (non-terminal) state.
        This is called at selection time AND again immediately before processing
        (stale case protection).
        """
        status = case.get("status", "")
        return status in ELIGIBLE_STATES

    @classmethod
    async def _process_case(
        cls,
        case: Dict[str, Any],
        batch_id: str,
        merchant_id: str,
    ) -> CaseResult:
        """
        Process a single recovery case within a batch.

        Isolation guarantee: exceptions raised inside this method are caught
        here so the batch loop continues with the next case.

        Steps:
        1. Re-fetch the case to get the latest state (stale case protection).
        2. Re-check merchant ownership.
        3. Re-check eligibility.
        4. Delegate to run_recovery_agent() — the agent owns all business logic.
        5. Return a structured CaseResult.
        """
        case_id = case["id"]
        initial_state = case.get("status", "unknown")
        started_at = datetime.now(timezone.utc).isoformat()

        try:
            # ── Stale case protection: re-fetch current state ─────────────────
            fresh_case = await db_get_recovery_case(case_id)
            if not fresh_case:
                return CaseResult(
                    case_id=case_id,
                    initial_state=initial_state,
                    final_state=initial_state,
                    result="skipped",
                    reason="Case no longer exists in database",
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            # ── Re-check merchant ownership ───────────────────────────────────
            if fresh_case.get("merchant_id") != merchant_id:
                return CaseResult(
                    case_id=case_id,
                    initial_state=initial_state,
                    final_state=fresh_case.get("status", initial_state),
                    result="skipped",
                    reason="Merchant ownership mismatch — security check failed",
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            # ── Re-check eligibility (stale case may now be terminal) ─────────
            current_state = fresh_case.get("status", "")
            if not cls._is_eligible(fresh_case):
                return CaseResult(
                    case_id=case_id,
                    initial_state=initial_state,
                    final_state=current_state,
                    result="skipped",
                    reason=f"Case became ineligible before processing (state: {current_state})",
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            print(f"[BatchEngine] Processing case {case_id} (state={current_state}) in batch {batch_id}")

            # ── Delegate to the existing recovery agent ───────────────────────
            # The agent owns: detection, diagnosis, prediction, decision,
            # guardrail evaluation, execution, and verification.
            # The batch engine does NOT replicate any of this logic.
            agent_result = await run_recovery_agent(fresh_case)

            final_state = agent_result.get("final_status", current_state)

            return CaseResult(
                case_id=case_id,
                initial_state=current_state,
                final_state=final_state,
                result="success",  # The agent completed successfully without throwing an exception
                reason=f"Agent completed — final state: {final_state}",
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as e:
            # ── Case-level isolation: exception does NOT abort the batch ───────
            error_msg = str(e)
            print(f"[BatchEngine] Case {case_id} raised exception: {error_msg}")
            return CaseResult(
                case_id=case_id,
                initial_state=initial_state,
                final_state=initial_state,  # state unknown after exception
                result="failed",
                reason="Exception during case processing",
                error=error_msg,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
