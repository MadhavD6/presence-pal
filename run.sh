#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p)
    exit
}

trap cleanup SIGINT SIGTERM

# Helper to kill port use
kill_port() {
  lsof -ti :$1 | xargs -r kill -9
}

echo "Cleaning up ports 8000 and 8080..."
kill_port 8000
kill_port 8080

echo "Starting Backend..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting Celery Worker..."
celery -A backend.celery_app worker --loglevel=info &
WORKER_PID=$!

echo "Starting Uvicorn API..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend..."
npm run dev -- --host 0.0.0.0 --port 8080 &
FRONTEND_PID=$!

echo "Application running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8080"
echo "API Docs: http://localhost:8000/docs"

wait $BACKEND_PID $FRONTEND_PID $WORKER_PID
