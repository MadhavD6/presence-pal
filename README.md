# PresencePal - Comprehensive Technical Documentation

**PresencePal** is a Face Attendance Kiosk Application engineered for high-throughput, touch-free attendance marking. This document serves as a "Zero-to-Hero" guide, detailing every layer of the stack, from the React frontend to the SQLite schema.

---

## 🏗 High-Level Architecture

The system operates on a **Client-Server** model, but optimized for a Kiosk environment where the Client and Server often reside on the same machine (localhost).

```mermaid
graph TD
    subgraph "Frontend Layer (React)"
        Router[Router (Index.tsx)]
        Manager[Manager State State]
        Camera[Camera Module]
        UI[Shadcn UI Layer]
    end

    subgraph "API Layer (FastAPI)"
        Endpoints[FastAPI Routers]
        AuthSvc[Auth Service]
        VectorSvc[Vector Service (AI)]
        AuditSvc[Audit Service]
    end

    subgraph "Data Layer"
        SQL[SQLite Database]
        Files[File System (Images)]
    end

    Camera -->|1. Capture Image| Router
    Router -->|2. POST /identify| Endpoints
    Endpoints -->|3. Validate| AuthSvc
    Endpoints -->|4. Embedding Search| VectorSvc
    VectorSvc -->|5. Audit Log| AuditSvc
    AuditSvc -->|6. INSERT| SQL
```

---

## � Call Graph: "What Calls What?"

### Scenario 1: User Clocks In
This is the critical path of the application.

1.  **Frontend (`src/components/attendance/ClockCaptureScreen.tsx`)**:
    -   `capturedImage` is generated via `react-webcam`.
    -   Calls `api.identify(blob, 'in')` in `src/services/api.ts`.
2.  **API Request**:
    -   `POST http://localhost:8000/api/v1/identify`
    -   Payload: `Multipart-Form-Data` containing `file` (image) and `event_type` ('in').
3.  **Backend Router (`backend/routers/api.py`)**:
    -   Receives request.
    -   **Step A**: Calls `vector_service.get_embedding(file)`.
        -   Uses `DeepFace` to crop and generate a 512-float vector.
    -   **Step B**: Calls `vector_service.search(vector)`.
        -   Iterates through in-memory vectors to find Cosine Similarity < 0.4.
    -   **Step C**: Calls `audit_service.log_event(...)`.
        -   Saves the event to `AuditLog` table.
4.  **Database**:
    -   `INSERT INTO auditlog (timestamp, user_id, event_type, confidence) VALUES (...)`
5.  **Response**:
    -   JSON: `{ status: "success", user: { name: "John" }, confidence: 0.88 }`
6.  **Frontend**:
    -   Receives JSON.
    -   Triggers `SuccessOverlay.tsx` animation.
    -   Redirects to Home.

---

## 💾 detailed Backend Schema

The database is **SQLite** (`kiosk.db`), managed via **SQLModel**.

### 1. `User` Table
**Purpose**: The central identity registry.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-incrementing ID. |
| `name` | `VARCHAR` | `INDEX` | Full Name (e.g., "Karthik Dhumala"). |
| `employee_id` | `VARCHAR` | `UNIQUE`, `INDEX` | Corporate ID (e.g., "PI-30023"). |
| `role` | `VARCHAR` | Default: "user" | "admin" or "user". |
| `created_at` | `DATETIME` | Default: `now()` | Timestamp of registration. |

### 2. `Embedding` Table
**Purpose**: Stores the biometric "Face ID". Separated from `User` to allow multiple faces per user (future proofing) or cleaner loading.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-incrementing ID. |
| `user_id` | `INTEGER` | `FOREIGN KEY (User)` | Links to the `User`. |
| `vector_json` | `TEXT` | `NOT NULL` | The 512D vector stored as a JSON string (`"[0.123, -0.45, ...]"`) for easy serialization/deserialization. |
| `created_at` | `DATETIME` | Default: `now()` | When this face was enrolled. |

### 3. `AuditLog` Table
**Purpose**: The immutable ledger of all attendance actions. This is the source of truth for Timesheets.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-incrementing ID. |
| `timestamp` | `DATETIME` | `NOT NULL` | Exact time of punch. |
| `user_id` | `INTEGER` | `FOREIGN KEY (User)` | Who punched in. Nullable if unknown/failed punch. |
| `event_type` | `VARCHAR` | "in" / "out" | Direction of the punch. |
| `confidence` | `FLOAT` | `NOT NULL` | The AI confidence score (0.0 - 1.0). |
| `thumbnail_path` | `VARCHAR` | `NULLABLE` | File path to evidence image (e.g., `/data/evidence/123.jpg`). |

### 4. `Shift` Table
**Purpose**: Definitions of work timings.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | ID. |
| `name` | `VARCHAR` | `INDEX` | Name (e.g., "General Shift"). |
| `start_time` | `TIME` | `NOT NULL` | (e.g., "09:00:00"). |
| `end_time` | `TIME` | `NOT NULL` | (e.g., "18:00:00"). |

### 5. `EmployeeShift` Table
**Purpose**: Maps users to shifts on specific dates (Rostering).
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | ID. |
| `user_id` | `INTEGER` | `FOREIGN KEY` | Employee. |
| `shift_id` | `INTEGER` | `FOREIGN KEY` | Assigned Shift. |
| `date` | `DATE` | `NOT NULL` | The specific calendar date. |

### 6. `Leave` Table
**Purpose**: Leave requests and approvals.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY` | ID. |
| `user_id` | `INTEGER` | `FOREIGN KEY` | Employee. |
| `leave_type` | `VARCHAR` | `NOT NULL` | "Sick", "Casual", etc. |
| `start_date` | `DATE` | `NOT NULL` | From. |
| `end_date` | `DATE` | `NOT NULL` | To. |
| `status` | `VARCHAR` | Default: "Pending" | "Approved", "Rejected". |

---

## 💻 Frontend Structure Breakdown

### 1. `src/pages/Index.tsx` (The Brain)
This file acts as the **state-machine routing layer**. Since this is a Kiosk app, we avoid traditional URL routing (like `react-router`) to prevent browser history stack issues. We use a simple state variable `currentScreen`.
-   **States**: `home`, `clockIn`, `clockOut`, `register`, `employee`, `manager`.
-   **Logic**: Renders the corresponding component based on state. Mounts/Unmounts components to trigger their `useEffect` hooks (e.g., starting camera on mount).

### 2. Services (`src/services/api.ts`)
A typed wrapper around the `fetch` API. It unifies error handling and response types.
-   `api.enroll(formData)`: POST /admin/enroll
-   `api.identify(blob)`: POST /identify

---

## ⚙️ Backend Service Logic

### `vector_service.py`
This is the heavy lifter.
1.  **Startup**:
    -   Loads `backend/data/vectors.pkl`.
    -   If missing, reads all `Embedding` rows from SQL and builds the index.
2.  **Runtime**:
    -   Uses `DeepFace.represent(img_path, model_name="ArcFace")` to get embeddings.
    -   Calculates **Cosine Distance**: $$ 1 - \frac{A \cdot B}{||A|| ||B||} $$
    -   Threshold: **0.40** (tuned for typical webcam quality).

### `audit_service.py`
1.  **Logging**: Writes to `AuditLog`.
2.  **Purging**: On startup, deletes logs older than 90 days (configurable) to keep SQLite fast.

---

## 🚀 How to Run (Full Stack)

The project includes a unified runner script `run.sh` that manages both processes.

1.  **Frontend Server**:
    -   Command: `npm run dev`
    -   Port: `8080` (Proxies `/api` requests to backend).
2.  **Backend Server**:
    -   Command: `uvicorn backend.main:app --reload`
    -   Port: `8000`

**To Start:**
```bash
./run.sh
```
This script handles the virtual environment activation and parallel execution.
