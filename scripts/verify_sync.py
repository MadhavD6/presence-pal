import sys
import os
import requests
import json
from datetime import datetime, timedelta

sys.path.append(os.getcwd())
# Assuming local server running on 8000
API_URL = "http://localhost:8000/api/v1"
KIOSK_KEY = "dev-kiosk-123"

def verify_sync():
    print("--- Verifying Phase 6: Offline Sync ---")
    
    # 1. Prepare Batch
    # User 1, 2 items.
    now = datetime.now()
    t1 = now - timedelta(minutes=10)
    t2 = now - timedelta(minutes=5)
    
    batch = [
        {
            "user_id": 1,
            "timestamp": t1.isoformat(),
            "event_type": "in",
            "confidence": 0.98,
            "kiosk_id": "test-script"
        },
        {
            "user_id": 1,
            "timestamp": t2.isoformat(),
            "event_type": "out",
            "confidence": 0.99,
            "kiosk_id": "test-script"
        }
    ]
    
    # 2. Call Sync
    print("Sending Batch 1...")
    headers = {"X-Kiosk-API-Key": KIOSK_KEY}
    try:
        r = requests.post(f"{API_URL}/kiosk/sync", json=batch, headers=headers)
        r.raise_for_status()
        data = r.json()
        print(f"Response: {data}")
        
        assert data["processed"] == 2
        assert data["skipped"] == 0
        
    except Exception as e:
        print(f"FAILED: {e}")
        # Print response body if available
        if 'r' in locals():
            print(r.text)
        sys.exit(1)
        
    # 3. Duplicate Test (Resend Same Batch)
    print("Resending Batch (Duplicate Test)...")
    try:
        r = requests.post(f"{API_URL}/kiosk/sync", json=batch, headers=headers)
        data = r.json()
        print(f"Response: {data}")
        
        assert data["processed"] == 0
        assert data["skipped"] == 2
        
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
        
    print("✅ SUCCESS: Sync Verification Passed!")

if __name__ == "__main__":
    verify_sync()
