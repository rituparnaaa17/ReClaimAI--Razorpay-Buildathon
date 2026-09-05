import sys, os
import asyncio
from datetime import datetime, timezone
sys.path.insert(0, '.')

from app.services.razorpay_service import verify_payment_status

def _uuid(n: int) -> str:
    return f"00000000-0000-0000-0000-{n:012d}"

async def run_smoke_test():
    print("=========================================")
    print("STEP 5: REAL PAYMENT VERIFICATION SMOKE TEST")
    print("=========================================\n")

    # We will test two real Razorpay payments:
    # 1. A captured payment
    # 2. A failed payment

    # 1. Captured payment scenario
    captured_payment_id = "pay_TQy4AVtB1G89Kl"
    
    print(f"--- Scenario A: Verification of Captured Payment ---")
    print(f"Using REAL Razorpay ID: {captured_payment_id}")
    case_captured = {
        "id": _uuid(101),
        "merchant_id": "merchant-test",
        "status": "verifying",
        "amount_at_risk": 5000,
        "recovery_probability": 0.85,
        "failure_reason": "UPI_TIMEOUT",
        "payment_method": "UPI",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "retry_count": 0,
        "razorpay_payment_id": captured_payment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    res1 = await verify_payment_status(case_captured)
    print(f"Verification Result:")
    print(f"  status: {res1['status']}")
    print(f"  razorpay_status: {res1['razorpay_status']}")
    assert res1['status'] == 'recovered', f"Expected recovered, got {res1['status']}"
    assert res1['razorpay_status'] == 'captured', f"Expected captured, got {res1['razorpay_status']}"
    print("[PASS] Scenario A Passed: Captured payment successfully verified as 'recovered'\n")

    # 2. Failed payment scenario
    failed_payment_id = "pay_TQxsKH4hRdEoTh"
    print(f"--- Scenario B: Verification of Failed Payment ---")
    print(f"Using REAL Razorpay ID: {failed_payment_id}")
    case_failed = {
        **case_captured,
        "id": _uuid(102),
        "razorpay_payment_id": failed_payment_id,
    }
    
    res2 = await verify_payment_status(case_failed)
    print(f"Verification Result:")
    print(f"  status: {res2['status']}")
    print(f"  razorpay_status: {res2['razorpay_status']}")
    assert res2['status'] == 'not_recovered', f"Expected not_recovered, got {res2['status']}"
    assert res2['razorpay_status'] == 'failed', f"Expected failed, got {res2['razorpay_status']}"
    print("[PASS] Scenario B Passed: Failed payment verified as 'not_recovered' (failed)\n")
    
    # 3. Invalid identifier scenario
    print(f"--- Scenario C: Invalid Identifier ---")
    print(f"Using identifier: 'plink_invalid_123'")
    case_invalid = {
        **case_captured,
        "id": _uuid(103),
        "razorpay_payment_id": "plink_invalid_123",
    }
    res3 = await verify_payment_status(case_invalid)
    print(f"Verification Result:")
    print(f"  status: {res3['status']}")
    print(f"  error: {res3['error_description']}")
    assert res3['status'] == 'verification_failed', f"Expected verification_failed, got {res3['status']}"
    print("[PASS] Scenario C Passed: Payment link identifier correctly blocked by verification boundary\n")

    print("=========================================")
    print("ALL REAL RAZORPAY VERIFICATION TESTS PASSED")
    print("=========================================")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
