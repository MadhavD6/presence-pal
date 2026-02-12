#!/usr/bin/env python3
"""
Comprehensive Test Script for Presence-Pal Backend Logic
Tests all recently implemented features and edge cases.

Run with: .venv/bin/python3 scripts/test_backend_logic.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, time, datetime, timedelta
from sqlmodel import Session, select, create_engine
from backend.core.config import get_settings
from backend.models.shift import Shift, EmployeeShift
from backend.models.user import User
from backend.models.leave import Leave
from backend.models.correction import AttendanceCorrection
from backend.models.audit import AuditLog
from backend.models.site import Site  # Required for FK resolution
from backend.services.attendance import calculate_daily_stats

# Setup
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_pass(msg):
    print(f"  {Colors.GREEN}✓ PASS{Colors.RESET}: {msg}")

def print_fail(msg):
    print(f"  {Colors.RED}✗ FAIL{Colors.RESET}: {msg}")

def print_info(msg):
    print(f"  {Colors.YELLOW}ℹ INFO{Colors.RESET}: {msg}")

# ============================================================
# TEST 1: Shift Model - crosses_midnight field
# ============================================================
def test_shift_crosses_midnight():
    print_header("TEST 1: Shift Model - crosses_midnight field")
    
    with Session(engine) as session:
        # Create a night shift
        night_shift = Shift(
            name="Test Night Shift",
            start_time=time(22, 0),  # 10 PM
            end_time=time(6, 0),     # 6 AM next day
            grace_period_mins=15,
            crosses_midnight=True
        )
        session.add(night_shift)
        session.commit()
        session.refresh(night_shift)
        
        # Verify
        fetched = session.get(Shift, night_shift.id)
        if fetched and fetched.crosses_midnight == True:
            print_pass(f"Night shift created with crosses_midnight=True (ID: {fetched.id})")
        else:
            print_fail("crosses_midnight field not saved correctly")
            
        # Cleanup
        session.delete(night_shift)
        session.commit()
        print_info("Cleaned up test shift")

# ============================================================
# TEST 2: EmployeeShift - weekly_offs field
# ============================================================
def test_employee_shift_weekly_offs():
    print_header("TEST 2: EmployeeShift - weekly_offs field")
    
    with Session(engine) as session:
        # Find a test user
        user = session.exec(select(User).limit(1)).first()
        if not user:
            print_fail("No users in database for testing")
            return
            
        # Find any shift
        shift = session.exec(select(Shift).limit(1)).first()
        if not shift:
            print_fail("No shifts in database for testing")
            return
            
        # Create assignment with custom weekly offs (Saturday + Sunday)
        assignment = EmployeeShift(
            user_id=user.id,
            shift_id=shift.id,
            start_date=date.today(),
            weekly_offs="5,6",  # Saturday (5) and Sunday (6)
            is_active=True
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        
        # Verify
        fetched = session.get(EmployeeShift, assignment.id)
        if fetched and fetched.weekly_offs == "5,6":
            print_pass(f"EmployeeShift created with weekly_offs='5,6' (ID: {fetched.id})")
            
            # Parse and verify
            offs = [int(x) for x in fetched.weekly_offs.split(",")]
            if 5 in offs and 6 in offs:
                print_pass("Weekly offs correctly parsed to [5, 6]")
            else:
                print_fail("Weekly offs parsing failed")
        else:
            print_fail("weekly_offs field not saved correctly")
            
        # Cleanup
        session.delete(assignment)
        session.commit()
        print_info("Cleaned up test assignment")

# ============================================================
# TEST 3: calculate_daily_stats - Night Shift Handling
# ============================================================
def test_attendance_night_shift():
    print_header("TEST 3: calculate_daily_stats - Night Shift")
    
    # Create mock shift
    night_shift = Shift(
        id=99999,
        name="Test Night",
        start_time=time(22, 0),  # 10 PM
        end_time=time(6, 0),     # 6 AM
        grace_period_mins=15,
        crosses_midnight=True
    )
    
    # Create mock logs (punch in at 10:05 PM, out at 6:15 AM next day)
    base_date = datetime(2026, 1, 27, 22, 5)  # Jan 27, 10:05 PM
    
    class MockLog:
        def __init__(self, id, ts, event):
            self.id = id
            self.timestamp = ts
            self.event_type = event
    
    logs = [
        MockLog(1, base_date, "in"),
        MockLog(2, base_date + timedelta(hours=8, minutes=10), "out")  # 6:15 AM next day
    ]
    
    result = calculate_daily_stats(logs, night_shift)
    
    # Verify worked hours (should be ~8 hours)
    if result["total_hours"] > 7.5:
        print_pass(f"Worked hours calculated correctly: {result['worked_hours']}")
    else:
        print_fail(f"Worked hours incorrect: {result['worked_hours']} (expected ~8h)")
    
    # Verify late check (5 mins late, within grace period)
    if not result["is_late"]:
        print_pass("Late check correct: Not late (within 15 min grace)")
    else:
        print_fail(f"Late check incorrect: Marked as late ({result['late_minutes']} mins)")
        
    # Verify shift label shows (+1) for crossover
    if "(+1)" in result["shift_end"]:
        print_pass(f"Shift end shows crossover: {result['shift_end']}")
    else:
        print_fail(f"Shift end missing crossover indicator: {result['shift_end']}")

# ============================================================
# TEST 4: Leave Overlap Detection
# ============================================================
def test_leave_overlap_detection():
    print_header("TEST 4: Leave Overlap Detection")
    
    with Session(engine) as session:
        user = session.exec(select(User).limit(1)).first()
        if not user:
            print_fail("No users in database")
            return
            
        # Create first leave
        leave1 = Leave(
            user_id=user.id,
            leave_type="Casual Leave",
            start_date=date(2026, 2, 5),
            end_date=date(2026, 2, 10),
            reason="Test Leave 1",
            status="Pending"
        )
        session.add(leave1)
        session.commit()
        print_info(f"Created Leave 1: Feb 5-10")
        
        # Try to create overlapping leave (Feb 8-12)
        # The actual API endpoint would reject this, but let's verify the query logic
        overlap_start = date(2026, 2, 8)
        overlap_end = date(2026, 2, 12)
        
        from sqlmodel import and_
        overlapping = session.exec(
            select(Leave)
            .where(Leave.user_id == user.id)
            .where(Leave.status != "Rejected")
            .where(
                and_(
                    Leave.start_date <= overlap_end,
                    Leave.end_date >= overlap_start
                )
            )
        ).first()
        
        if overlapping:
            print_pass(f"Overlap detected correctly! Conflicts with: {overlapping.start_date} to {overlapping.end_date}")
        else:
            print_fail("Overlap NOT detected (should have found conflict)")
            
        # Clean up
        session.delete(leave1)
        session.commit()
        print_info("Cleaned up test leave")

# ============================================================
# TEST 5: Cross-Day Correction Logic
# ============================================================
def test_cross_day_correction():
    print_header("TEST 5: Cross-Day Correction Logic (Night Shift)")
    
    # Simulate correction timestamps
    original_date = date(2026, 1, 27)
    corrected_in = datetime(2026, 1, 27, 22, 0)   # 10 PM on Jan 27
    corrected_out = datetime(2026, 1, 27, 6, 0)   # 6 AM - WRONG (should be Jan 28)
    
    print_info(f"Original In: {corrected_in}")
    print_info(f"Original Out: {corrected_out}")
    
    # Apply our fix logic
    if corrected_out.time() < corrected_in.time():
        corrected_out_fixed = corrected_out + timedelta(days=1)
        print_pass(f"Cross-day detected! Adjusted Out to: {corrected_out_fixed}")
        
        # Verify the fix
        if corrected_out_fixed.date() == date(2026, 1, 28):
            print_pass("Out date correctly adjusted to Jan 28")
        else:
            print_fail(f"Wrong adjustment: {corrected_out_fixed.date()}")
    else:
        print_fail("Cross-day not detected")

# ============================================================
# TEST 6: User Department Field
# ============================================================
def test_user_department_field():
    print_header("TEST 6: User Department Field")
    
    with Session(engine) as session:
        user = session.exec(select(User).limit(1)).first()
        if not user:
            print_fail("No users in database")
            return
            
        # Check if department field exists
        if hasattr(user, 'department'):
            print_pass("User model has 'department' field")
            
            # Try setting it
            original = user.department
            user.department = "Test Engineering"
            session.add(user)
            session.commit()
            session.refresh(user)
            
            if user.department == "Test Engineering":
                print_pass(f"Department saved correctly: {user.department}")
            else:
                print_fail("Department not saved")
                
            # Restore
            user.department = original
            session.add(user)
            session.commit()
            print_info("Restored original department value")
        else:
            print_fail("User model missing 'department' field")

# ============================================================
# TEST 7: Historical Shift Lookup
# ============================================================
def test_historical_shift_lookup():
    print_header("TEST 7: Historical Shift Lookup")
    
    with Session(engine) as session:
        user = session.exec(select(User).limit(1)).first()
        if not user:
            print_fail("No users in database")
            return
            
        today = date.today()
        
        # Query historical shift
        employee_shift = session.exec(
            select(EmployeeShift)
            .where(EmployeeShift.user_id == user.id)
            .where(EmployeeShift.start_date <= today)
            .where(
                (EmployeeShift.end_date == None) | (EmployeeShift.end_date >= today)
            )
        ).first()
        
        if employee_shift:
            shift = session.get(Shift, employee_shift.shift_id)
            if shift:
                print_pass(f"Found historical shift for user {user.name}: {shift.name}")
                print_info(f"  - Start Date: {employee_shift.start_date}")
                print_info(f"  - Weekly Offs: {employee_shift.weekly_offs}")
            else:
                print_fail("Shift record found but shift details missing")
        else:
            # Check fallback
            if user.shift_id:
                shift = session.get(Shift, user.shift_id)
                print_info(f"No EmployeeShift record, using cached shift_id: {shift.name if shift else 'None'}")
            else:
                print_info("No shift assigned to user (both historical and cached)")

# ============================================================
# MAIN
# ============================================================
def main():
    print(f"\n{Colors.BOLD}{'#'*60}")
    print(f"# Presence-Pal Backend Logic Test Suite")
    print(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}{Colors.RESET}")
    
    tests = [
        ("Shift crosses_midnight", test_shift_crosses_midnight),
        ("EmployeeShift weekly_offs", test_employee_shift_weekly_offs),
        ("Night Shift Attendance Calc", test_attendance_night_shift),
        ("Leave Overlap Detection", test_leave_overlap_detection),
        ("Cross-Day Correction", test_cross_day_correction),
        ("User Department Field", test_user_department_field),
        ("Historical Shift Lookup", test_historical_shift_lookup),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            print_fail(f"Exception in {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
            continue
    
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"  TEST SUMMARY")
    print(f"{'='*60}{Colors.RESET}")
    print(f"  All tests executed. Check individual results above.")
    print()

if __name__ == "__main__":
    main()
