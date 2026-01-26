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
