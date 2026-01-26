YOU ARE THE LEAD ARCHITECT OF THIS PROJECT.
This entire document is the SINGLE source of truth for the current state of the Face Attendance System as of January 12, 2026.
All future answers MUST be 100% consistent with this document unless I explicitly say to change something.
When I ask for code, plans, fixes, or improvements — always refer back to this context first.


1.Technical Documentation
# Face Attendance System - Technical Documentation
**Version:** 1.0.0
**Date:** January 12, 2026
**Status:** Alpha / Active Development

---

## 1. Table of Contents
1. [System Overview & Architecture](#2-system-overview--architecture)
2. [Detailed Component Breakdown](#3-detailed-component-breakdown)
3. [End-to-End Face Recognition Process](#4-data-flow--end-to-end-face-recognition-process)
4. [Database Schema](#5-database-schema)
5. [Current Implementation Status](#6-current-implementation-status--gaps)
6. [Security & Anti-Spoofing](#7-security--anti-spoofing-considerations)
7. [Roadmap & Priorities](#8-next-development-priorities-roadmap)
8. [Best Practices](#9-best-practices--recommendations)

---

## 2. System Overview & Architecture

The Face Attendance System is a high-performance, privacy-focused biometric attendance solution designed for corporate environments. It combines a sleek, touch-free Kiosk interface with robust backend processing capable of sub-second recognition.

### Tech Stack
*   **Frontend**: React, Vite, TailwindCSS (Dark-first UI)
*   **Backend**: Python, FastAPI
*   **Database**: SQLite (with SQLAlchemy/SQLModel ORM)
*   **AI/ML Engine**: DeepFace (ArcFace Model) + OpenCV
*   **Vector Search**: FAISS (Facebook AI Similarity Search) or Linear Search (scale-dependent)
*   **Infrastructure**: Local deployment support, Docker-ready

### Architecture Diagram

```mermaid
graph TD
    subgraph "Frontend Layer (React/Vite)"
        Kiosk["Kiosk UI (Capture Zone)"]
        EmpDash["Employee Dashboard (Mock)"]
        MgrDash["Manager Dashboard (Live)"]
        Router["App Router (Index.tsx)"]
    end

    subgraph "Backend Layer (FastAPI)"
        API["API Gateway (Routers)"]
        Liveness["Liveness Service (Motion/Blink)"]
        FaceEng["DeepFace Engine (ArcFace)"]
        Audit["Audit Service"]
        VectorSvc["Vector Service (FAISS/Linear)"]
    end

    subgraph "Data Persistence"
        DB[(SQLite DB)]
        EmbedStore[("Embedding Store (BLOB)")]
        Cache["In-Memory Cache (Redis/Local)"]
    end

    %% Flows
    Kiosk -->|images (burst 5x)| API
    API --> Liveness
    Liveness -->|validated frames| FaceEng
    FaceEng -->|512D Vector| VectorSvc
    VectorSvc -->|Search Query| EmbedStore
    VectorSvc -.->|High Scale| FAISS[(FAISS Index)]
    
    MgrDash -->|Fetch Stats/Logs| API
    API -->|Read| DB
    
    Router --> Kiosk
    Router --> EmpDash
    Router --> MgrDash
```

---

## 3. Detailed Component Breakdown

The frontend application is structured as a Single Page Application (SPA) with three distinct zones.

### A. Kiosk Zone (The "Face")
Focused on speed and zero-interaction usability.
*   **Navigation**: `ClockCaptureScreen` (Reused for In/Out).
*   **Features**:
    *   Real-time camera preview.
    *   Burst mode capture (5 frames per event).
    *   Feedbacks: Status toasts, sound effects (planned), and visual cues (glow effects).

### B. Manager Zone (The "Brain")
**Status: LIVE Integration**
Fully connected to backend APIs for real-time monitoring.
1.  **Dashboard Home**:
    *   **Day View**: Aggregated stats (Present, Late, Absent).
    *   **Live Feed**: Latest punches list with timestamps and duration.
2.  **Timesheet View**:
    *   Weekly grid visualization of staff attendance.
    *   Auto-calculation of "Worked Hours" based on punch pairs.
3.  **Pending Actions**:
    *   UI placeholder for approving leave requests/regularizations.

### C. Employee Zone (The "User")
**Status: MOCK / Prototype**
Standalone sub-app for individual staff members.
1.  **Dashboard**: Shift schedule (horizontal scroll) and recent punch logs.
2.  **Timesheet**: Calendar view of monthly attendance status.
3.  **Leave Management**: UI for applying for leave and viewing history.
*   *Note: Currently uses static mock data and local state.*

---

## 4. Data Flow & End-to-End Face Recognition Process

### The "5-Step" Pipeline
1.  **Capture (Client-Side)**
    *   User stands before Kiosk.
    *   Camera captures a burst of **5 frames** over ~1 second.
    *   Images are bundled into `FormData` and POSTed to `/api/v1/identify`.

2.  **Liveness Verification (Server-Side)**
    *   **Input**: 5 consecutive frames.
    *   **Logic**: Passive Liveness Check using `liveness_service`.
    *   **Method**: Calculates pixel variance and motion flow between frames to reject static photos (spoofing).
    *   *Result*: If motion < threshold, request is rejected as "Spoof/Static".

3.  **Feature Extraction**
    *   **Input**: The "best" frame (usually middle frame #3).
    *   **Engine**: `FaceService` wraps **DeepFace**.
    *   **Model**: **ArcFace** (ResNet-100 backbone).
    *   **Output**: A normalized **512-dimensional floating-point vector**.

4.  **Vector Matching**
    *   **Service**: `VectorService`.
    *   **Strategy Strategy Pattern**:
        *   **Small Tenant (<1k users)**: `LinearEngine` (Numpy dot product). Exact and fast for small sets.
        *   **Large Tenant (>1k users)**: `FaissEngine`. Uses Facebook's FAISS library for indexed, approximate nearest-neighbor search.
    *   **Threshold**: Cosine Similarity > **0.5**.

5.  **Audit & Response**
    *   **Success**: Returns User Object `{id, name, confidence}`.
    *   **Failure**: Returns error code (e.g., `low_confidence`, `liveness_failed`).
    *   **Persistence**: Async write to `AuditLog` table with timestamp, event type, and confidence score.

---

## 5. Database Schema

The system uses SQLite for simplicity and portability, designed to be migrated to PostgreSQL for production.

### Core Tables

#### 1. `User`
*   Identity source of truth.
*   **Columns**: `id` (PK), `name`, `employee_id` (Unique), `role` (user/admin/manager), `created_at`.

#### 2. `Embedding`
*   Stores biometric data separated from PII (Privacy by Design).
*   **Columns**: `id` (PK), `user_id` (FK), `vector` (BLOB - serialized numpy array), `created_at`.

#### 3. `AuditLog`
*   The "Punch" record.
*   **Columns**: `id` (PK), `timestamp`, `user_id` (FK), `kiosk_id`, `event_type` ('in'/'out'), `confidence` (float), `thumbnail_path` (optional).

#### 4. `Kiosk` (New)
*   Device registration and authentication.
*   **Columns**: `id`, `name`, `api_key_hash`, `location_id`.

### Proposed Schema Additions (Roadmap)
*   **`Shift`**: `id`, `name`, `start_time`, `end_time`, `grace_period_mins`.
*   **`LeaveRequest`**: `id`, `user_id`, `type`, `start_date`, `end_date`, `status` (pending/approved/rejected), `reason`.
*   **`PayrollConfig`**: `user_id`, `hourly_rate`, `currency`, `overtime_multiplier`.

---

## 6. Current Implementation Status & Gaps

| Module | Component | Status | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Kiosk** | Capture UI | 🟢 Live | Camera/DeepFace |
| **Kiosk** | Face Rec Pipeline | 🟢 Live | ArcFace/FAISS |
| **Kiosk** | Offline Mode | 🟡 Partial | LocalStorage (queue exists, sync pending) |
| **Manager** | Dashboard Stats | 🟢 Live | API (`/manager/stats`) |
| **Manager** | Timesheet | 🟢 Live | API (`/manager/timesheet`) |
| **Employee** | Dashboard | 🟡 Mock | Static JSON |
| **Employee** | Leave | 🟡 Mock | UI Only |
| **Core** | Payroll Logic | 🔴 Missing | None |
| **Core** | Auth/RBAC | 🟡 Partial | Fixed Roles |

---

## 7. Security & Anti-Spoofing Considerations

1.  **Passive Liveness**:
    *   Basic motion-based detection is implemented to stop "phone screen" or "printed photo" attacks.
    *   *Upgrade*: Future implementation of blink detection or depth-estimation.

2.  **Data Privacy**:
    *   **Images are Ephemeral**: Raw face images are processed in-memory and discarded. Only the math vector is saved.
    *   **Vector Protection**: Vectors are stored as binary blobs. Reverse-engineering a face from a 512D ArcFace vector is theoretically extremely difficult.

3.  **Kiosk Security**:
    *   API requests from Kiosk require an `X-Kiosk-API-Key` header.
    *   Kiosk registration flow binds a device ID to a location.

---

## 8. Next Development Priorities Roadmap

### Phase 1: Employee Integration (Est. 3 Days)
*   [ ] Connect Employee Dashboard to `GET /employee/dashboard`.
*   [ ] Implement `POST /employee/leave` API and connect frontend form.
*   [ ] Replace random attendance status with real query from `AuditLog`.

### Phase 2: Robust Payroll & Shifts (Est. 5 Days)
*   [ ] Implement `Shift` model to define "Late" vs "On Time".
*   [ ] Create "Payroll Service" to calculate: `(Total Hours - Unpaid Breaks) * Rate`.
*   [ ] Add `Overtime` calculation logic.

### Phase 3: Hardening & Deployment (Est. 4 Days)
*   [ ] **Sync Service**: Robust backend worker to process offline punches from Kiosk.
*   [ ] **Containerization**: Dockerfile for Frontend (Nginx) and Backend (Uvicorn).
*   [ ] **SSL/TLS**: Enforce HTTPS for camera permissions in production.

---

## 9. Best Practices & Recommendations

1.  **Lighting Conditions**:
    *   Deploy Kiosks in evenly lit areas (300-500 lux). Avoid backlighting (windows behind users).
    
2.  **Scalability**:
    *   Current SQLite + FAISS setup can handle ~5,000 users comfortably.
    *   **Next Step**: Migration to PostgreSQL + pgvector for >10k users.
    
3.  **Concurrency**:
    *   Face recognition is CPU intensive. For high traffic (shift change times), consider deploying Celery workers or a separate "Inference Microservice" to keep the API responsive.

4.  **Compliance**:
    *   **GDPR/BIPA**: Ensure explicit consent is collected before enrollment. Add a "Delete My Data" feature for employees (Right to be Forgotten).

2.System Architecture Diagram + Component Diagram
Here are the Mermaid diagrams representing your Face Attendance System architecture and the detailed clock-in flow.

1. High-Level System Architecture

graph TD
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef backend fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef hardware fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;

    subgraph ClientSide ["Frontend Layer (React SPA + Vite)"]
        direction TB
        Webcam((Webcam / Camera)):::hardware
        Kiosk["Kiosk App<br>(Burst Capture & UI)"]:::frontend
        MgrDash["Manager Dashboard<br>(Live Stats & Real-time Feeds)"]:::frontend
        EmpApp["Employee App<br>(Mock/Prototype)"]:::frontend
    end

    subgraph ServerSide ["Backend Layer (Python FastAPI)"]
        direction TB
        API["API Gateway<br>(/api/v1/identify)"]:::backend
        
        subgraph Processing ["Biometric Pipeline"]
            Liveness["Liveness Service<br>(Passive Motion Check)"]:::backend
            DeepFace["DeepFace Engine<br>(ArcFace Model, 512D)"]:::backend
            Matcher["Vector Matching Svc<br>(FAISS / Linear Search)"]:::backend
        end
    end

    subgraph Storage ["Persistence Layer (SQLite)"]
        direction TB
        UserTable[("User Table<br>(Identity & Roles)")]:::database
        AuditTable[("AuditLog Table<br>(Time, Event, Conf)")]:::database
        VectorStore[("Embedding Store<br>(Binary BLOBs)")]:::database
    end

    %% Flows
    Webcam -->|"Stream (5 Frames)"| Kiosk
    Kiosk -->|"POST Multi-part (Images)"| API
    MgrDash -.->|"GET /stats (Polling)"| API
    EmpApp -.->|"GET /profile (Planned)"| API

    API --> Liveness
    Liveness -->|"Verified Frames"| DeepFace
    DeepFace -->|"Vector (Float32)"| Matcher
    
    Matcher <-->|"Indexed (Speed)"| VectorStore
    
    API -->|"Log Transaction"| AuditTable
    API -->|"Fetch Context"| UserTable
    
   2. Clock-In Event Sequence (Detailed Data Flow)
   
   sequenceDiagram
    autonumber
    actor User
    participant Cam as Webcam
    participant Kiosk as Kiosk Frontend
    participant API as FastAPI Backend
    participant Live as Liveness Svc
    participant Engine as DeepFace (ArcFace)
    participant Vector as Vector Svc (FAISS)
    participant DB as SQLite DB

    Note over User, Kiosk: User approaches Kiosk

    User->>Cam: Faces Camera
    Kiosk->>Cam: Trigger Burst Capture
    Cam-->>Kiosk: Return 5 Frames (approx. 1 sec duration)
    
    Kiosk->>API: POST /identify (5 Images, Multipart)
    activate API
    
    %% Step 1: Liveness
    API->>Live: Check Passive Liveness (Frame Sequence)
    alt Motion Variance < Threshold
        Live-->>API: Result: SPOOF DETECTED
        API-->>Kiosk: 400 Bad Request (Liveness Check Failed)
        Kiosk-->>User: Show "Please move slightly" Error
    else Liveness Passed
        Live-->>API: Result: REAL
        
        %% Step 2: Embedding
        API->>Engine: Process Best Frame (Middle)
        Engine-->>API: Return 512D Embedding Vector
        
        %% Step 3: Matching
        API->>Vector: Search Nearest Neighbor (Vector)
        Vector->>Vector: Compare Cosine Similarity
        
        alt Similarity Score > 0.5
            Vector-->>API: Match Found (User ID: 101, Conf: 0.92)
            
            %% Step 4: Logging
            par Async Logging
                API->>DB: INSERT into AuditLog (User 101, IN, Timestamp)
            and Cache Update
                API->>DB: Fetch User Name & Role
            end
            
            DB-->>API: User Details ("Alice Smith")
            API-->>Kiosk: 200 OK { user: "Alice Smith", confidence: 0.92 }
            
            Kiosk-->>User: Green Success Glow + "Welcome Alice"
            
        else Similarity Score < 0.5
            Vector-->>API: No Match Found
            API->>DB: Log Audit (User: Unknown, Type: Failure)
            API-->>Kiosk: 401 Unauthorized
            Kiosk-->>User: Red Error Glow + "Face Not Recognized"
        end
    end
    deactivate API
    
    
3.Payroll Logic Design & Implementation Plan

# Payroll Module Design Document

## 1. Overview
This design introduces a robust Payroll module to transform raw biometrics into actionable financial data. It moves away from on-the-fly calculations to a persistent, state-based model using **Daily Summaries** and **Payroll Runs**.

## 2. Database Schema (SQLModel)

We need three new tables to handle configuration, daily aggregation, and finalized pay runs.

```python
# backend/models/payroll.py
from typing import Optional
from datetime import date, datetime
from sqlmodel import Field, SQLModel, Relationship

class PayrollConfig(SQLModel, table=True):
    """Stores individual salary settings per employee."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    base_hourly_rate: float = Field(default=0.0)
    overtime_multiplier: float = Field(default=1.5) # e.g. 1.5x for OT
    currency: str = Field(default="USD")
    # Link to shift if needed, or default 9-5
    shift_start_time: str = Field(default="09:00") 

class DailySummary(SQLModel, table=True):
    """
    Pre-calculated daily record. 
    Critically separates raw punches from business logic.
    Populated by a daily cron or 'Refresh' action.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date
    
    # Aggregated from AuditLog
    first_in: Optional[datetime] = None
    last_out: Optional[datetime] = None
    
    # Computed Headers
    total_hours: float = Field(default=0.0)
    regular_hours: float = Field(default=0.0)
    overtime_hours: float = Field(default=0.0)
    
    # Status
    is_late: bool = Field(default=False)
    status: str = Field(default="Absent") # Present, Absent, Leave, Holiday, MissedPunch
    
    # Financial snapshot (rates can change, so we verify here?) 
    # Usually kept separate, but calculated during PayrollRun.

class PayrollRun(SQLModel, table=True):
    """Represents a generated batch for a month."""
    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    is_finalized: bool = Field(default=False) # If true, locks changes
    total_payout: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Payslip(SQLModel, table=True):
    """The final artifact for an employee."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="payrollrun.id")
    user_id: int = Field(foreign_key="user.id")
    
    gross_pay: float
    total_deductions: float
    net_pay: float
    
    # Breakdown structure stored as JSON
    details: str = Field(default="{}") 
```

## 3. Calculation Logic (Backend Service)

### Algorithm: Daily Aggregation
Instead of calculating payroll directly from raw logs, we first normalize data into `DailySummary`.

```python
# backend/services/payroll_service.py

def aggregate_daily_attendance(user_id: int, target_date: date, session: Session):
    # 1. Fetch raw punches
    logs = session.exec(select(AuditLog)...).all()
    
    # 2. Identify First In / Last Out
    in_punches = [l for l in logs if l.event_type == 'in']
    out_punches = [l for l in logs if l.event_type == 'out']
    
    if not in_punches:
        # Check leave table
        return create_summary(status="Absent" or "Leave")
        
    first_in = in_punches[0].timestamp
    
    # 3. Handle Missing Out (Edge Case)
    if not out_punches:
        # Strategy: Mark as 'MissedPunch' - requires manual manager override
        # OR Auto-close at 6 PM (risky)
        return create_summary(status="MissedAction", first_in=first_in)
        
    last_out = out_punches[-1].timestamp
    
    # 4. Calculate Duration
    duration = (last_out - first_in).total_seconds() / 3600.0
    
    # 5. Apply Rules
    STANDARD_Hours = 8.0
    regular = min(duration, STANDARD_Hours)
    overtime = max(0, duration - STANDARD_Hours)
    
    # 6. Late Check
    SHIFT_START = 9.0 # 9 AM
    is_late = first_in.hour + (first_in.minute/60) > SHIFT_START + 0.25 # 15 min grace
    
    create_summary(
        regular_hours=regular,
        overtime_hours=overtime,
        is_late=is_late,
        status="Present"
    )
```

### Algorithm: Payroll Generation
Iterate over `DailySummary` rows for the date range.

`Pay = (RegularHours * Rate) + (OvertimeHours * Rate * 1.5) - (LateCount * Deduction)`

## 4. API Endpoints

### Manager
*   `POST /api/v1/payroll/aggregate`: Force re-calculation of daily summaries for a date range (e.g., after fixing a punch).
*   `POST /api/v1/payroll/generate`: Create a draft `PayrollRun`. Returns a Run ID.
*   `GET /api/v1/payroll/run/{run_id}`: View totals for review.
*   `POST /api/v1/payroll/run/{run_id}/finalize`: Lock the run, allowing employees to see slips.

### Employee
*   `GET /api/v1/payroll/slips`: List available slips.
*   `GET /api/v1/payroll/slips/{id}`: Detailed view.

## 5. Integration Points
*   **Existing `ManagerTimesheetView`**:
    *   **Change**: Stop summing `AuditLog` directly in the frontend/backend timesheet API.
    *   **New**: Read from `DailySummary` table. It's faster (O(1) vs O(N)) and accurate (includes manual overrides).
*   **Manual Corrections**:
    *   Add a "Fix Punch" button in Manager Dashboard. When a manager manually edits a time, **trigger the Aggregation Logic** for that day immediately to update `DailySummary`.

## 6. Frontend Screens

### A. Manager Payroll Dashboard
1.  **Overview Card**: "Pending Payroll for Jan 2026".
2.  **Batch Generation**: Button "Generate January Payroll".
3.  **Review Table**:
    *   List of Employees | Total Hours | OT Hours | Estimated Payout | Status (Ready/Error).
    *   *Highlight "Error" rows (Missed Punches) in red.*

### B. Employee Payslip
A clean, printable component:
*   **Header**: Company Logo, Pay Period.
*   **Grid**:
    *   Base Pay: 160hrs @ $20/hr = $3200
    *   Overtime: 5hrs @ $30/hr = $150
    *   Deductions: Late (2) = -$20
*   **Footer**: Net Pay, Tax hints (if applicable).

## 7. Handling Edge Cases
1.  **Missing Out Punch**:
    *   *System*: Flags day as `MissedPunch` in `DailySummary`.
    *   *Payroll Calc*: Defaults hours to 0 for that day to force Manager attention.
    *   *Fix*: Manager adds manual `Out` time -> recalculates summary -> user gets paid.
2.  **Holidays**:
    *   Need a `Holiday` table. `aggregate_daily_attendance` should check this list first. If user punches on holiday -> Auto-mark as OT or specialized Holiday Pay.
3.  **Active Leaves**:
    *   Start of aggregation checks `Leave` table. If `Approved` leave exists, set `DailySummary.status = "Leave"` and `payable_hours = 0` (or 8 if paid leave).


4.Employee App Real Data Integration Plan

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

## Product Roadmap

### Phase 1 — Core Employee Experience
- **Employee Zone → Live Data**  
  Enable regular employees to view real-time attendance data.  
  Why this next?: Biggest visible gap. Makes the app usable for normal employees (not just managers & kiosk)
  Dependencies:Existing Auth + AuditLog 
  Suggested Order:Do first
  _Effort:_ ★★☆ 

### Phase 2 — Payroll Foundation
- **Basic Payroll Calculation & Daily Summary**  
  Convert attendance into payable amounts.  
  Why this next?: Turns raw attendance into money — core value of any attendance system
  Dependencies:Employee data live
  Suggested Order:Second
  _Effort:_ ★★★ 

- **Shift & Leave Models + Rules**  
  Define late, holiday, and paid leave logic.  
  Why this next?: Payroll needs context (what is "late"? what is "holiday"? paid leave?)
  Dependencies:(days)Payroll foundation
  Suggested Order:With/after 2  
  _Effort:_ ★★☆ 
### Phase 3 — Manager Controls
- **Manager Payroll Review & Generation**  
  Allow review, corrections, and approval before payouts.  
  Why this next?: Managers need to see/approve/fix before money moves
  Dependencies:Payroll calc working
  Suggested Order:After 2–3
  _Effort:_ ★★☆ 

### Phase 4 — Reliability & Infrastructure
- **Offline Queue & Kiosk Sync**  
  Ensure system reliability during internet outages.  
  Why this next?: Real-world reliability (internet drops during shift change)     
  Dependencies:Core flows stable
  Suggested Order:Later
  _Effort:_ ★★★ 

- **Containerization & Deployment**  
  Move from local development to real environments.  
  Why this next?: Move from local dev → testable on real hardware/network
  Dependencies:Features somewhat stable
  Suggested Order:Parallel/after 1–4
  _Effort:_ ★★☆ 


