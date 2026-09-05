import sys, os
sys.path.insert(0, '.')
from app.services.razorpay_service import get_razorpay_client

client = get_razorpay_client()
print('Fetching recent payments...')
try:
    payments = client.payment.all({'count': 5})
    for p in payments.get('items', []):
        print(f"ID: {p['id']}, Status: {p['status']}")
except Exception as e:
    print('Failed to fetch payments:', e)
