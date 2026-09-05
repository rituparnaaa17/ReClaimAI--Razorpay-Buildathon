import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.supabase_client import get_supabase

async def seed_mock_cases():
    print("Loading environment variables...")
    load_dotenv()
    sb = get_supabase()
    
    # 1. Create or get Merchant
    merchant_res = sb.table("merchants").select("id").limit(1).execute()
    if merchant_res.data:
        merchant_id = merchant_res.data[0]["id"]
    else:
        merchant_id = str(uuid.uuid4())
        sb.table("merchants").insert({"id": merchant_id, "name": "Demo Merchant", "email": "demo@merchant.com"}).execute()
        
    print(f"Using Merchant ID: {merchant_id}")

    mock_data = [
        {
            "customer_name": "Arjun Sharma", "customer_email": "arjun.sharma@example.com",
            "amount": 4999.0, "failure_reason": "UPI_TIMEOUT", "method": "upi", "prob": 0.85
        },
        {
            "customer_name": "Priya Patel", "customer_email": "priya.patel@example.com",
            "amount": 12500.0, "failure_reason": "INSUFFICIENT_BALANCE", "method": "card", "prob": 0.62
        },
        {
            "customer_name": "Rahul Verma", "customer_email": "rahul.verma@example.com",
            "amount": 2999.0, "failure_reason": "BANK_DECLINE", "method": "netbanking", "prob": 0.75
        }
    ]

    for item in mock_data:
        # 2. Create Customer
        customer_id = str(uuid.uuid4())
        sb.table("customers").insert({
            "id": customer_id,
            "merchant_id": merchant_id,
            "name": item["customer_name"],
            "email": item["customer_email"]
        }).execute()
        
        # 3. Create Transaction
        transaction_id = str(uuid.uuid4())
        sb.table("transactions").insert({
            "id": transaction_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "amount": item["amount"],
            "status": "failed",
            "failure_reason": item["failure_reason"],
            "payment_method": item["method"],
            "razorpay_payment_id": f"pay_mock_{uuid.uuid4().hex[:8]}"
        }).execute()
        
        # 4. Create Recovery Case
        case_id = str(uuid.uuid4())
        sb.table("recovery_cases").insert({
            "id": case_id,
            "merchant_id": merchant_id,
            "transaction_id": transaction_id,
            "amount_at_risk": item["amount"],
            "recovery_probability": item["prob"],
            "status": "detected"
        }).execute()
        
        print(f"Created Recovery Case {case_id} for {item['customer_name']}")
        
    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_mock_cases())
