import sys
sys.path.insert(0, '.')
from app.services.razorpay_service import get_razorpay_client

client = get_razorpay_client()
payment = client.payment.fetch('pay_TQy4AVtB1G89Kl')
print(f"Amount: {payment.get('amount')}")
print(f"Currency: {payment.get('currency')}")
