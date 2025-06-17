#!/bin/bash

set -e

# Wait for Postgres to be ready
dockerize -wait tcp://db:5432 -timeout 60s

# Run database migrations
alembic upgrade head

# Start the FastAPI app with debugpy attached
exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client \
    -m uvicorn application.server:app --host 0.0.0.0 --port 8000 --reload
