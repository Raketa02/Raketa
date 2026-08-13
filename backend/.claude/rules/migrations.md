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
