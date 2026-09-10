#!/bin/bash
set -euo pipefail

APP_PORT="${APP_PORT:-8000}"
APP_HOST="${APP_HOST:-0.0.0.0}"
# One application process hosts one embedded event delivery worker by default.
# Extra processes remain safe because pending event rows are locked while fetched.
WORKERS="${GUNICORN_WORKERS:-1}"

# Migrations are off by default in production — ECS should run them as a
# one-shot task before the rolling deploy. Toggle on if you intentionally want
# the API container to migrate on boot.
if [[ "${RUN_MIGRATIONS_ON_STARTUP:-false}" == "true" ]]; then
    echo "[startup] running alembic upgrade head"
    alembic -c "${APP_HOME:-/home/app}/alembic.ini" upgrade head
fi

echo "[startup] launching gunicorn on ${APP_HOST}:${APP_PORT} with ${WORKERS} workers"
# --graceful-timeout is THE NUMBER THAT LEADS. It is how long the application
# gives itself to drain after SIGTERM, and every deadline outside the process is
# chosen to outlive it — in particular `stopTimeout` in deploy/ecs/taskdef.json,
# which is when the ECS agent stops asking and sends SIGKILL. Change this and you
# must change that; `make taskdef` fails the build if they ever disagree (#345).
#
# It is 30 because an SSE stream (docs/adr/0147) will use every second of it: a
# stream lives until the access token expires, so a rolling deploy severs open
# streams rather than waiting them out. That is the intended trade — the client
# reconnects and the nudge design means a severed stream costs latency, never
# data — and raising this number would not change it. It would only delay the
# deploy for every other request in the process.
exec gunicorn app.main:app \
    --bind "${APP_HOST}:${APP_PORT}" \
    --workers "${WORKERS}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --graceful-timeout 30 \
    --timeout 60
