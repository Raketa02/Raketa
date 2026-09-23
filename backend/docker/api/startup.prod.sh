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
# measured against it — in particular `stopTimeout` in deploy/ecs/taskdef.json, which
# is when the ECS agent stops asking and sends SIGKILL. It outlives this number.
# Change this and you must change that; `make taskdef` fails the build if they ever
# disagree (#345).
#
# The ALB target group's `deregistration_delay.timeout_seconds` is the third deadline,
# and it follows this number by MATCHING it rather than outliving it — that window runs
# before SIGTERM, not after, so it is a budget in sequence with this one. No check can
# see it: the target group is provisioned by hand and is not in this repository. Change
# this and set it too — docs/deployment/aws-ecs.md provisions it in section 1 step 6 and
# argues it in section 4b, and both restate this number (#372).
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
