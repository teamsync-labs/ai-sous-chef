#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z "${POSTGRES_HOST:-postgresql}" "${POSTGRES_PORT:-5432}"; do
  sleep 1
done
echo "PostgreSQL is ready"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
