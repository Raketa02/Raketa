---
paths:
  - "migrations/**"
  - "alembic.ini"
  - "app/infrastructure/**"
---

# Alembic migrations

- **Never edit an already-applied migration.** Add a new one. An applied migration is
  history that other checkouts and the running database have already consumed.
- A database schema change requires a new file in `migrations/versions/` with the next
  sequential `NNNN_*` prefix.
- **Two drivers must both keep working.** The app uses `postgresql+asyncpg`; Alembic uses
  `psycopg2`. A change to DB config that only satisfies one of them breaks the other at a
  different time than you make the change.
- `make migrate` runs `alembic upgrade head` inside the API container. With `make up`,
  migrations already run on container start.
- **A revision id may be up to 64 characters, and only because `migrations/env.py` says so.**
  Alembic sizes `alembic_version.version_num` at 32, and `0036_payment_customers_and_notices`
  and `0038_a_card_can_lose_its_court_hour` are longer — Postgres refused to record them until
  `env.py` widened the column before Alembic reads it (#541). SQLite enforces no length, so no
  test sees a long id; prove a new migration on Postgres.
