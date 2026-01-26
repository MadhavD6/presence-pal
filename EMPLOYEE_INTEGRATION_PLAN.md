# Employee Zone Integration Plan

This document outlines the step-by-step process to transition the Employee App from mock data to live backend integration.

## 1. Backend Implementation (FastAPI)

We need to instantiate specific endpoints in `backend/routers/employee.py`. Ensure all endpoints are protected by a `get_current_active_user` dependency.

### A. Core Endpoints
**File**: `backend/routers/employee.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from backend.core.security import get_current_user
from backend.models.user import User

router = APIRouter()

# 1. Dashboard Snapshot
@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Returns:
    - User Profile (name, id, role)
    - Today's Punch Status (In/Out/Time)
    - Upcoming Shifts (Next 7 days)
    """
    # ... logic to fetch today's logs and next 7 days shifts ...
    return {
        "profile": current_user,
        "today": {"status": "In", "first_in": "09:00 AM"},
        "shifts": [] # Populate from Shift model
    }

# 2. Monthly Timesheet
@router.get("/timesheet")
async def get_my_timesheet(
    month: str, # YYYY-MM
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Returns date-wise status for the requested month.
    Used for the Calendar View.
    """
    # Logic:
    # 1. Fetch all audit logs for user in date range
    # 2. Fetch approved leaves
    # 3. Merge into daily status (Present, Absent, Leave, WO)
    pass

# 3. Leave Management
@router.get("/leaves")
async def get_leave_history(current_user: User = Depends(get_current_user)):
    pass

@router.post("/leaves")
async def apply_leave(
    leave_data: LeaveCreate, # Define Pydantic model
    current_user: User = Depends(get_current_user)
):
    pass
```

## 2. Frontend Service Layer

Update `src/services/api.ts` to include employee-specific calls. Use a centralized axios instance with interceptors for JWT injection.

```typescript
// src/services/api.ts

export const employeeApi = {
    getDashboard: async () => {
        const response = await fetch(`${API_BASE_URL}/employee/dashboard`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch dashboard');
        return response.json();
    },

    getTimesheet: async (month: Date) => {
        const monthStr = month.toISOString().slice(0, 7); // YYYY-MM
        const response = await fetch(`${API_BASE_URL}/employee/timesheet?month=${monthStr}`, {
            headers: getAuthHeaders()
        });
        return response.json();
    },

    applyLeave: async (data: any) => {
        const response = await fetch(`${API_BASE_URL}/employee/leaves`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return response.json();
    }
};
```

## 3. Frontend Component Integration

Refactor the components to remove `const shifts = [...]` mock data and replace with Async Data Fetching.

### A. `EmployeeDashboard.tsx`
Replace static state with `useEffect` or `useQuery` (TanStack Query is already installed).

```tsx
import { useQuery } from '@tanstack/react-query';
import { employeeApi } from '@/services/api';

const EmployeeDashboard = ({ onBack }) => {
    // Replace Mock Data
    const { data, isLoading, error } = useQuery({
        queryKey: ['employeeDashboard'],
        queryFn: employeeApi.getDashboard
    });

    if (isLoading) return <LoadingSpinner />;
    if (error) return <ErrorState message="Could not load dashboard" />;

    const { profile, shifts, today } = data;

    return (
        // ... Render UI using `profile.name`, `shifts.map(...)`
    );
};
```

### B. `TimesheetScreen.tsx`
This requires dynamic fetching when the user changes months.

```tsx
const TimesheetScreen = ({ initialDate }) => {
    const [currentMonth, setCurrentMonth] = useState(initialDate);

    const { data: monthlyData, isLoading } = useQuery({
        queryKey: ['timesheet', currentMonth],
        queryFn: () => employeeApi.getTimesheet(currentMonth)
    });

    // ... Render Calendar Grid using `monthlyData`
};
```

## 4. Authentication Flow (JWT)

Since the Kiosk app might be shared, the Employee Zone needs a generic "Login" screen if not using Face ID for access.

1.  **Login Screen**: If `token` is missing in `localStorage`, redirect `currentScreen` to a new `EmployeeLogin` component.
2.  **Face Login (Optional)**:
    - User clicks "Employee Zone".
    - Camera opens ( reuse `ClockCaptureScreen` logic).
    - Backend identifies user -> Returns JWT.
    - Frontend stores JWT -> Redirects to Dashboard.

## 5. Real-Time Strategy

For an attendance app, **Polling** is often sufficient and simpler than WebSockets.

*   **Strategy**: Poll `getDashboard` every 30-60 seconds.
*   **Why**: Attendance doesn't change millisecond-by-millisecond. 1-minute freshness is acceptable.

```tsx
useQuery({
    queryKey: ['employeeDashboard'],
    queryFn: employeeApi.getDashboard,
    refetchInterval: 30000 // 30 seconds
});
```

## 6. Testing Checklist

- [ ] **Auth**: access `/employee/*` without token -> Should 401.
- [ ] **Data mapping**: Ensure `status: "Present"` sets the green color in Calendar.
- [ ] **Empty States**: New employee with 0 punches should see empty logs, not crash.
- [ ] **Error Handling**: Network failure shows "Offline / Retry" button.
- [ ] **Dates**: Verify Timezone consistency (UTC vs Local) between Python backend and JS frontend.
