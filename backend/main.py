# Force Reload for Timecard Variable Fix
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import get_settings
from backend.core.database import create_db_and_tables
from backend.services.vector import vector_service
from backend.services.audit import audit_service
from backend.services.audit import audit_service
from backend.routers import api, employee, kiosk as kiosk_router, manager, payroll, manager_payroll, manager_holidays, attendance, shifts
from backend.models import user, audit, shift, leave, kiosk as kiosk_model, correction, site, gallery
from prometheus_fastapi_instrumentator import Instrumentator

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Startup: Initializing DB...")
    create_db_and_tables()
    print("Startup: Loading Vector Index...")
    vector_service.load_index()
    print("Startup: Running Audit Purge...")
    await audit_service.purge_old_logs()
    yield
    # Shutdown
    print("Shutdown: Clearing resources...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

from fastapi import Request
import uuid
from backend.core.trace import request_id_ctx_var

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    # Generate unique ID
    request_id = str(uuid.uuid4())
    
    # Set in context
    token = request_id_ctx_var.set(request_id)
    
    import time
    from backend.core.logger import logger
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=f"{process_time:.2f}"
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=f"{process_time:.2f}"
        )
        raise e
    finally:
        # Clean up
        request_id_ctx_var.reset(token)

# CORS (Allow all for local kiosk - strictly controlled network)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix=settings.API_V1_STR)
app.include_router(attendance.router, prefix=settings.API_V1_STR)
app.include_router(employee.router, prefix=settings.API_V1_STR)
app.include_router(kiosk_router.router, prefix=settings.API_V1_STR)
app.include_router(manager.router, prefix=settings.API_V1_STR)
app.include_router(payroll.router, prefix=settings.API_V1_STR)
app.include_router(manager_payroll.router, prefix=settings.API_V1_STR)
app.include_router(manager_holidays.router, prefix=settings.API_V1_STR)
app.include_router(shifts.router, prefix=settings.API_V1_STR)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "isolated", "vectors_loaded": vector_service.is_loaded}

