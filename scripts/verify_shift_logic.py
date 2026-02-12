import sys
import os
from datetime import datetime, time, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from backend.models.audit import AuditLog
from backend.models.shift import Shift
from backend.routers.employee import calculate_daily_stats

def verify_logic():
    print("Verifying Shift Logic...")
    
    # 1. Setup Shift: 9:00 - 18:00, 15m grace
    shift = Shift(
        name="General Shift",
        start_time=time(9, 0),
        end_time=time(18, 0),
        grace_period_mins=15
    )
    
    # 2. Case A: On Time (9:10 AM)
    # 9:10 is within 9:00 + 15m (9:15)
    logs_a = [
        AuditLog(
            timestamp=datetime(2026, 1, 13, 9, 10),
            event_type="in",
            user_id=1,
            confidence=0.99
        ),
        AuditLog(
            timestamp=datetime(2026, 1, 13, 18, 0),
            event_type="out",
            user_id=1,
            confidence=0.99
        )
    ]
    
    stats_a = calculate_daily_stats(logs_a, shift=shift)
    print(f"\nCase A (9:10 AM - On Time):")
    print(f"  First In: {stats_a['first_in']}")
    print(f"  Is Late: {stats_a['is_late']}")
    print(f"  Late Mins: {stats_a['late_minutes']}")
    
    assert stats_a['is_late'] == False, "Case A Failed: Should NOT be late"
    assert stats_a['late_minutes'] == 0, "Case A Failed: Late minutes should be 0"
    
    # 3. Case B: Late (9:20 AM)
    # 9:20 is > 9:15 grace limit
    logs_b = [
        AuditLog(
            timestamp=datetime(2026, 1, 13, 9, 20),
            event_type="in",
            user_id=1,
            confidence=0.99
        ),
        AuditLog(
            timestamp=datetime(2026, 1, 13, 18, 0),
            event_type="out",
            user_id=1,
            confidence=0.99
        )
    ]
    
    stats_b = calculate_daily_stats(logs_b, shift=shift)
    print(f"\nCase B (9:20 AM - Late):")
    print(f"  First In: {stats_b['first_in']}")
    print(f"  Is Late: {stats_b['is_late']}")
    print(f"  Late Mins: {stats_b['late_minutes']}")
    
    assert stats_b['is_late'] == True, "Case B Failed: Should be late"
    # Late by 20 mins from start time 9:00 (since 9:20 - 9:00 = 20)
    assert stats_b['late_minutes'] == 20, f"Case B Failed: Expected 20 late mins, got {stats_b['late_minutes']}"

    # 4. Case C: Exact Grace Limit (9:15 AM)
    # Should be On Time (inclusive usually? code says > grace_limit so 9:15 is <= 9:15 -> OK)
    logs_c = [
        AuditLog(
            timestamp=datetime(2026, 1, 13, 9, 15),
            event_type="in",
            user_id=1,
            confidence=0.99
        )
    ]
    stats_c = calculate_daily_stats(logs_c, shift=shift)
    print(f"\nCase C (9:15 AM - Grace Boundary):")
    print(f"  Is Late: {stats_c['is_late']}")
    
    assert stats_c['is_late'] == False, "Case C Failed: 9:15 should be NOT late"

    print("\nSUCCESS: All shift logic verification tests passed!")

if __name__ == "__main__":
    verify_logic()
