#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

