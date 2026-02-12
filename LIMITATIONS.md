# Application Limitations & Known Issues

This document outlines the current limitations of the **Face Attendance Kiosk** application. It is intended to help developers and stakeholders understand the constraints of the current **Prototype / MVP** implementation.

## 1. Security & Authentication
-   **Hardcoded Employee Context**: The `EmployeeDashboard` currently displays hardcoded data ("Dhumala Madhav Karthik") for demonstration purposes. In a production environment, this must be replaced with dynamic data fetched based on an authenticated user session.
-   **No Login for Employee Zone**: The "Employee Zone" is currently accessible without a password or face verification step. A proper authentication layer (Face Auth or Password) is required.
-   **API Security**: The backend API endpoints (e.g., `/employee/{id}/dashboard`) do not enforce strict authorization checks. Any user ID can currently be queried if the ID is known.

## 2. Database & Scalability
-   **SQLite Database**: The project uses `kiosk.db` (SQLite). While excellent for development, it is not suitable for high-concurrency production environments due to write locking.
    -   **Recommendation**: Migrate to PostgreSQL or MySQL for production.
-   **In-Memory Vector Search**: Face embeddings are loaded into memory and searched linearly. This will become slow as the user base grows (O(N) complexity).
    -   **Recommendation**: Use a dedicated Vector Database like **Milvus**, **Qdrant**, or **faiss** for efficient indexing.
-   **No Database Migrations**: The project currently relies on deleting `kiosk.db` to apply schema changes (`rm kiosk.db`). A migration tool like `alembic` is needed for preserving data during updates.

## 3. AI & Face Recognition
-   **Liveness Detection**: The current "Passive Liveness" check uses **Laplacian Variance** to detect blurriness. This is a basic check and can be easily spoofed by high-quality printed photos or screens.
    -   **Recommendation**: Implement active liveness (blink detection, head turn) or use a depth-sensing camera (RealSense/Kinect).
-   **Model Performance**: The **ArcFace** model (via DeepFace) is highly accurate but computationally expensive. Inference on a standard CPU can take 1-2 seconds per frame, which may cause UI lag.
    -   **Recommendation**: Enable GPU acceleration (CUDA) or use a lighter model (FaceNet Mobile) for edge devices.

## 4. Frontend & UI
-   **Mock Data**: Several parts of the "Timesheet" and "Dashboard" rely on mock logic for generating shifts and history (e.g., defaulting to "S8" shift).
-   **Browser Compatibility**: The application is optimized for Chrome/Edge (Chromium based). Camera access and CSS features may behave differently on Safari or Firefox.

## 5. Deployment
-   **Dev Server**: The application runs on `uvicorn --reload` and `vite`, which are development servers.
    -   **Recommendation**: Use a production build for React (`npm run build`) and a process manager like `gunicorn` or `systemd` for the backend.
-   **Single Instance**: The current architecture assumes a single kiosk instance. Synchronizing data across multiple kiosks requires a centralized cloud database.
