#!/bin/bash
set -euo pipefail

APP_PORT="${APP_PORT:-8000}"
APP_HOST="${APP_HOST:-0.0.0.0}"
WORKERS="${GUNICORN_WORKERS:-2}"

# Migrations are off by default in production — ECS should run them as a
# one-shot task before the rolling deploy. Toggle on if you intentionally want
# the API container to migrate on boot.
if [[ "${RUN_MIGRATIONS_ON_STARTUP:-false}" == "true" ]]; then
    echo "[startup] running alembic upgrade head"
    alembic -c "${APP_HOME:-/home/app}/alembic.ini" upgrade head
fi

echo "[startup] launching gunicorn on ${APP_HOST}:${APP_PORT} with ${WORKERS} workers"
exec gunicorn application.server:app \
    --bind "${APP_HOST}:${APP_PORT}" \
    --workers "${WORKERS}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --graceful-timeout 30 \
    --timeout 60
