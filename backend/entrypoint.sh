#!/bin/sh
set -e

echo "Ждём PostgreSQL..."
while ! nc -z postgresql 5432; do
  sleep 1
done
echo " PostgreSQL готов!"

echo "  Накатываем миграции Alembic..."
alembic upgrade head

echo "   Запускаем FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
