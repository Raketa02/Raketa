# Rakieta Backend

FastAPI backend on Clean Architecture (hexagonal ports & adapters) with DDD
aggregates, event sourcing, and a transactional outbox. Python 3.11, Poetry.

> **Monorepo note.** This is the `backend/` app of a three-app monorepo (see the root
> [`CLAUDE.md`](../CLAUDE.md) and [`../CONTEXT-MAP.md`](../CONTEXT-MAP.md)). Everything
> in this file scopes to `backend/` — **run all commands from this directory.** The
> Expo player app (`../frontend_player/`) and the Next.js club app (`../frontend_club/`)
> have their own `CLAUDE.md`; never apply these Python rules there, and never import
> across apps. A `PreToolUse` hook blocks writes outside `backend/` from this session.
> Shared docs live at the root: domain glossary [`../CONTEXT.md`](../CONTEXT.md),
> ADRs [`../docs/adr/`](../docs/adr/).

## Default workflow

For non-trivial changes:
1. Explore the relevant files; state current behavior and constraints.
2. Propose a minimal plan before editing. For refactors touching >5 files, stop and confirm first.
3. Write or update tests first when behavior changes (see Testing).
4. Make the smallest safe change.
5. Run the most focused relevant tests first, then `make test` when practical.
6. Run `make lint` before finishing if code changed.
7. Summarize changed files, checks run, and remaining risks.

Do not claim a task is done unless the relevant tests/checks ran — or plainly state why they did not.

## Safety — never do these without an explicit request

- Run deployment targets (`build-prod`, `ecr-*`, `ecs-*`). *(hook-enforced)*
- Create or edit a real `.env*`, secret, certificate, or credential. Edit the
  `.env*.example` template instead. *(hook-enforced)*
- Edit an already-applied Alembic migration. Add a new one.
- Import FastAPI, SQLAlchemy, Pydantic, or an external SDK into a `domain/` layer.
- Call an external side effect (email, webhook, provider API) directly from a use case
  — emit a domain event instead.
- Change public API behavior without calling it out in the plan first. **Two client
  apps depend on this contract**, and neither is in your session to be fixed.

## Commands

Run via the Makefile from `backend/` (each target wraps the real command):

- `make install` — `poetry install`
- `make test` — `poetry run pytest tests -q`
- `make lint` / `make format` — `ruff check .` / `ruff format .`
- `make typecheck` — `mypy app`
- `make check` — lint + typecheck + test, the same gate CI runs
- `make openapi` — dump `openapi.json`, the contract both clients generate from
- `make up` / `make down` — start/stop the dev stack (Postgres 17 + API + Redis)
- `make logs` — tail API logs; `make shell` — bash into the API container
- `make migrate` — `alembic upgrade head` inside the API container

Run a single test with `poetry run pytest tests/unit/test_user_domain.py::test_name`.

**Deployment is dormant.** Everything runs locally — local Postgres and local Docker via
`docker-compose-dev.yml`. There is no deployed environment. The AWS ECS path
(`build-prod`, `ecr-*`, `ecs-*`, `deploy/ecs/taskdef.json`,
[`docs/deployment/aws-ecs.md`](docs/deployment/aws-ecs.md)) is kept intact for later but
is not in use and is blocked for agent sessions. See
[ADR-0010](../docs/adr/0010-local-first-development-aws-deferred.md). If a task seems to
call for deploying, it doesn't — say so rather than reaching for those targets.

## Architecture

Code lives under `app/`. Features are vertical slices in `app/modules/<context>/`, each
split into four layers:

- `domain/` — aggregates, value objects, domain events, errors, and the module's ports
  (`Protocol`s like `UserRepository`) in `domain/ports.py`. **Pure Python.**
- `application/` — use cases (one class with `async execute(...)`), commands. Depend on
  ports via constructor injection, never on concrete adapters.
- `infrastructure/` — SQLAlchemy ORM models + adapters implementing the ports.
- `presentation/` — FastAPI routes, request/response schemas, route dependencies.

Feature-specific ports live in each module's `domain/ports.py`; cross-cutting ports
(unit of work, event publisher/store) live in `app/application/ports/`. Shared infra
(engine, session, UoW, event store/outbox) lives in `app/infrastructure/`, event-runtime
assembly in `app/bootstrap/events.py`, helpers (clock, ids) in `app/shared/`.

Rules to preserve:
- **Dependencies point inward:** presentation → application → domain. Adapters are wired
  to ports only at the FastAPI boundary in `app/api/dependencies.py` using
  `Annotated[Port, Depends(factory)]`.
- **State changes emit domain events.** Use cases persist them through
  `DomainEventStore.append` and enqueue them on the transactional outbox in the same
  transaction; handlers/workers perform side effects after commit.
- **New routes mount under `app/api/v1/router.py`;** keep the `/api/v1` prefix.
- **Durable event names are a contract.** Register every event in the catalog with an
  explicit `name=` and `version=`. Renaming a Python class must never change the wire
  format of already-stored history.

## The API contract

This app is the **single source of truth** for the API
([ADR-0006](../docs/adr/0006-backend-owns-api-contract.md)). Both clients generate their
TypeScript wire types from `openapi.json`.

That makes response-shape changes load-bearing beyond this directory. When you change
one:
1. Say so explicitly in your summary — name the endpoints and the shape change.
2. Run `make openapi` so the committed contract matches the code.
3. Flag that the clients need `make gen-api` (from the repo root). **Do not edit them
   yourself** — the ownership hook will block it, and correctly so.

Prefer additive changes. Removing or renaming a field breaks two shipped clients, one
of which is a mobile app whose old versions stay installed on real phones for months.

## Testing (TDD — test first)

Write the failing test before the implementation, then make it pass, then refactor.
Every domain or use-case change ships with tests; `pytest` must pass and new code must
be covered before a change is considered done.

- Tests live in `tests/`, not beside source. Files are `test_*.py`.
- `tests/unit/` — pure domain/application/adapter logic; mock ports with hand-written
  stub classes implementing the `Protocol` (see `tests/unit/test_resolve_current_user.py`).
- `tests/api/` — full HTTP flows via the `client` fixture (HTTPX ASGI + in-memory
  SQLite). Reuse fixtures from `tests/conftest.py` (`client`, `session_factory`,
  `valid_signup_payload`) rather than standing up new app/db instances.
- Tests are async by default (`asyncio_mode = "auto"`); no `@pytest.mark.asyncio` needed.

## Code style

- Ruff is the linter and formatter (rules `E`, `F`, `B`; `B008` ignored). Line length
  **88**, target **py311**. Imports follow the isort black profile. Run `make format`
  before committing.
- New value objects/aggregates go in the module's `domain/`; **validate and normalize
  inside the value object** (see `app/modules/users/domain/value_objects.py`).
- Database schema changes require a new Alembic migration in `migrations/versions/`
  (next sequential `NNNN_*` prefix).

## Environment & gotchas

- **`make up` needs no env file** — `docker-compose-dev.yml` supplies the DB URLs and
  `.env.docker` the rest, and migrations run on container start. This is the normal path.
- To run uvicorn **on the host** instead, `cp .env.example .env`. The filename matters:
  `config.py` loads `.env` (`SettingsConfigDict(env_file=".env")`), so a file named
  `.env.local` is read by nothing. Required: `WRITER_DB_URL`, `JWT_SECRET_KEY`,
  `DB_SSL_MODE`; `READER_DB_URL` defaults to the writer if unset. Point it at
  `rakieta_user:rakieta_pwd@localhost:5432/rakieta` to share the container's database.
- Tests set their own env in `conftest.py` (SQLite, test JWT secret) — no `.env` needed.
- Migrations are async-driver aware: the app uses `postgresql+asyncpg`, Alembic uses
  `psycopg2`. Keep **both** drivers working when touching DB config.
- The embedded event-delivery worker polls the outbox on startup; toggle with
  `EVENT_DELIVERY_WORKER_ENABLED`.

## Git & PRs

- Conventional Commits (commitizen). Scope backend work `api`, or the module:
  `feat(bookings): reject overlapping slots`.
- CI (`../.github/workflows/ci.yml`) runs `ruff check` then `pytest --cov` with
  `working-directory: backend`, and only when `backend/**` changed. Run `make check`
  before pushing.

## Domain language

The shared glossary is [`../CONTEXT.md`](../CONTEXT.md) — the source of truth for terms
like User, Authority, Court, Booking. Backend-only *technical* vocabulary lives in
[`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally.

The racket-sport contexts (Clubs, Courts, Bookings, Matches) are **listed but not yet
modeled**. Before writing code in one, resolve its terms into the shared glossary and
record the aggregate shape in an ADR — including whether it is event-sourced or
persisted-with-events. That decision is not a default; make it deliberately.
