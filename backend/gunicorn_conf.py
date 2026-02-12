import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:8000"

# Worker Options
# For DeepFace CPU-bound tasks, we limit workers to avoid OOM.
# Each worker loads its own TensorFlow model (~500MB).
# With preload_app=True, the model is loaded ONCE and shared via COW.
workers = int(os.getenv("GUNICORN_WORKERS", min(4, multiprocessing.cpu_count())))
threads = int(os.getenv("GUNICORN_THREADS", 2))

worker_class = "uvicorn.workers.UvicornWorker"

# CRITICAL: Load the app BEFORE forking workers.
# This means TensorFlow/DeepFace models are loaded once in the master process
# and shared across all workers via copy-on-write memory.
# Saves ~500MB RAM per worker and speeds up startup.
preload_app = True

# Timeout
# Face recognition can be slow on CPU, increasing timeout to avoid dropping requests.
timeout = 300
graceful_timeout = 120  # Time to finish in-flight requests during restart
keepalive = 5

# Logging
loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"   # stderr

# Process Naming
proc_name = "prodify_face_backend"

# Reload
# Disabled in production - Docker handles restarts
reload = False
