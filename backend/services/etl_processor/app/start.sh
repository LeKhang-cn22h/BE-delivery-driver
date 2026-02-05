#!/bin/bash
set -e

echo "=========================================="
echo "Starting Analytics Service (FastAPI + ETL)"
echo "=========================================="

# Start ETL worker in background
echo "Starting ETL worker in background..."
python -u etl_worker.py &
ETL_PID=$!

# Give ETL worker time to initialize DB
sleep 5

# Start FastAPI server
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 5000 &
API_PID=$!

# Wait for both processes
wait $ETL_PID $API_PID