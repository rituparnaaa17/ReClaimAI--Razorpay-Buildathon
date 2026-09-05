import asyncio, sys
sys.path.insert(0, '.')

async def smoke_test():
    from app.services.razorpay_service import execute_recovery

    case = {
        'id': 'smoke-test-step4-001',
        'amount_at_risk': 500.0,
        'customer_name': 'Smoke Test Customer',
        'customer_email': 'smoketest@reclaim.ai',
        'failure_reason': 'BANK_DECLINE',
        'merchant_id': 'merchant-test',
    }
    action = 'Alt. Payment Method'

    print('[SMOKE] Action:', action)
    print('[SMOKE] Calling execute_recovery against REAL Razorpay Test Mode...')
    
    result = await execute_recovery(action, case)
    
    print('[SMOKE] Result status:       ', result['status'])
    print('[SMOKE] Action attempted:    ', result['action_attempted'])
    print('[SMOKE] Razorpay identifier: ', result['razorpay_identifier'])
    print('[SMOKE] Error code:          ', result['error_code'])
    print('[SMOKE] Error description:   ', result['error_description'])
    print('[SMOKE] Timestamp:           ', result['timestamp'])
    return result

result = asyncio.run(smoke_test())
print()
if result['status'] == 'executed' and result['razorpay_identifier']:
    print('[SMOKE PASS] Razorpay Test Mode API accepted the request.')
    print('[SMOKE PASS] Payment Link ID returned:', result['razorpay_identifier'])
    print('[SMOKE PASS] No payment captured. No recovered state set.')
elif result['status'] == 'failed':
    print('[SMOKE FAIL] Razorpay returned error:', result.get('error_description'))
else:
    print('[SMOKE RESULT]', result)
