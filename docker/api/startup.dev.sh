#!/bin/bash
set -euo pipefail

DB_HOST="${DB_WAIT_HOST:-db}"
DB_PORT="${DB_WAIT_PORT:-5432}"
APP_ROOT="${APP_HOME:-/home/app}"

mkdir -p "${PYTHONPYCACHEPREFIX:-/tmp/pycache}"

echo "[dev] waiting for ${DB_HOST}:${DB_PORT}…"
dockerize -wait "tcp://${DB_HOST}:${DB_PORT}" -timeout 60s

echo "[dev] running migrations"
alembic -c "${APP_ROOT}/alembic.ini" upgrade head

# Debugpy is optional — set DEBUGPY_WAIT=true to block until a debugger attaches.
DEBUGPY_FLAGS=""
if [[ "${DEBUGPY_WAIT:-false}" == "true" ]]; then
    DEBUGPY_FLAGS="--wait-for-client"
fi

echo "[dev] launching uvicorn (reload) on 0.0.0.0:${APP_PORT:-8000}"
exec python -m debugpy --listen 0.0.0.0:5678 ${DEBUGPY_FLAGS} \
    -m uvicorn app.main:app \
    --host 0.0.0.0 --port "${APP_PORT:-8000}" \
    --reload \
    --reload-dir "${APP_ROOT}/app" \
    --reload-dir "${APP_ROOT}/migrations"
