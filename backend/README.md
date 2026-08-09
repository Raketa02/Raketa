# Rakieta

Rakieta is a production-oriented FastAPI service for user registration,
authentication, refresh-token rotation, and current-user resolution. The codebase
is structured around Clean Architecture and ports-and-adapters boundaries, with a
domain-event pipeline that combines an append-only event store and a transactional
outbox for durable side effects.

The project is intentionally small in feature scope, but the internal shape is
closer to a real service than a CRUD starter: domain rules live in framework-free
models, application services depend on protocols, infrastructure implements those
ports, and Docker images are built separately for development and production.

## Capabilities

- User signup with domain validation for email, nickname, and password strength.
- Login with access and refresh JWT issuance.
- Refresh-token rotation with server-side token state and replay protection.
- Idempotent logout that does not leak token existence.
- Authenticated `/users/me` endpoint backed by bearer access tokens.
- Event-sourced `User` aggregate with durable event stream persistence.
- Transactional outbox and embedded event-delivery worker.
- Async SQLAlchemy persistence with Alembic migrations.
- Dockerized local development and production runtime images.

## Architecture

The repository uses a modular architecture under `app/`:

```text
app/
  main.py                         FastAPI app factory and health endpoint
  api/
    v1/router.py                  API version router composition
    dependencies.py               Dependency wiring from HTTP to application ports
  core/                           Settings, lifespan, logging, middleware, errors
  application/
    ports/                        Protocols consumed by use cases
    events/                       Event catalog, codec contracts, dispatcher workflow
  bootstrap/
    events.py                     Runtime assembly for event catalog/dispatcher/worker
  infrastructure/
    database/                     SQLAlchemy engine, sessions, unit of work, ORM imports
    events/                       Event store, outbox, codec, delivery worker adapters
  modules/
    users/
      domain/                     User aggregate, value objects, domain events, ports
      application/                User use cases and event subscriptions
      infrastructure/             SQLAlchemy user projection adapter
      presentation/               FastAPI routes and Pydantic schemas
    auth/
      domain/                     Refresh-token entity, auth events, ports
      application/                Login, refresh, logout, token rotation
      infrastructure/             JWT, bcrypt, SQLAlchemy refresh-token adapter
      presentation/               FastAPI routes and Pydantic schemas
  shared/                         Clock, IDs, domain-event recorder
```

The dependency direction is deliberate:

```text
presentation -> application -> domain
infrastructure -> application/domain ports
bootstrap/core -> composition
```

Domain code does not import FastAPI, SQLAlchemy, Pydantic, or Docker-specific
runtime concerns. Application services depend on protocols such as
`UserRepository`, `RefreshTokenRepository`, `TokenService`,
`DomainEventStore`, `DomainEventPublisher`, and `UnitOfWork`. Concrete adapters
are selected at the boundary through FastAPI dependency functions and bootstrap
code.

## Domain Model

The `users` module models `User` as an event-sourced aggregate. State changes are
expressed as immutable domain events:

- `UserRegistered`
- `UserDisabled`
- `UserPromotedToAdmin`

The aggregate can be created from history with `User.from_history(...)`, records
new events through an internal `EventRecorder`, and exposes pending events with
`pull_events()`. Value objects (`Email`, `Nickname`, `RawPassword`,
`HashedPassword`) keep validation and normalization close to the domain.

The `auth` module models refresh-token state separately. Refresh tokens are JWTs
for transport, but the server persists a bcrypt hash and `jti` so refresh and
logout can verify, revoke, and rotate tokens safely. Auth domain events include:

- `RefreshTokenIssued`
- `RefreshTokenRevoked`
- `RefreshTokenRotated`

## Event Sourcing And Outbox

The project uses two event-related persistence tables with different purposes:

- `event_store`: append-only aggregate history for event-sourced domain state.
- `event_delivery_queue`: transactional outbox for asynchronous side effects.

For user signup, the flow is:

1. `RegisterUser` validates input through value objects.
2. It creates a `User` aggregate, which records `UserRegistered`.
3. `SqlAlchemyEventStore` appends the event to `event_store` with an expected
   stream version.
4. The user read model is projected into `users`.
5. `EventPublisher` writes the released event to `event_delivery_queue`.
6. The unit of work commits the event stream, projection, and outbox row in one
   transaction.
7. The embedded `EventWorker` polls unpublished outbox rows and dispatches them
   to subscribed application handlers.

Durable event names are registered in the event catalog, for example
`users.user_registered` and `auth.refresh_token_issued`. This avoids persisting
Python class names as public contracts. The JSON codec serializes dataclass
events with stable names and schema versions, and rehydrates payloads back into
domain-event classes when delivering or loading streams.

Outbox delivery uses `SELECT ... FOR UPDATE SKIP LOCKED` on PostgreSQL, which
allows multiple workers or processes to share pending work without delivering the
same row concurrently. Production starts one Gunicorn worker by default because
one application process hosts one embedded event worker; the database locking
keeps extra processes safe if the worker count is increased intentionally.

## Ports And Adapters

The main ports are defined as Python protocols:

| Port | Purpose | Main adapter |
|---|---|---|
| `UserRepository` | User reads and projection writes | `SqlAlchemyUserRepository` |
| `RefreshTokenRepository` | Refresh-token persistence | `SqlAlchemyRefreshTokenRepository` |
| `TokenService` | Issue and decode typed JWTs | `JwtTokenService` |
| `PasswordHasher` | Hash and verify passwords/tokens | `BcryptPasswordHasher` |
| `UnitOfWork` | Commit, flush, rollback boundary | `AsyncSqlAlchemyUnitOfWork` |
| `DomainEventStore` | Append/load aggregate streams | `SqlAlchemyEventStore` |
| `DomainEventPublisher` | Queue released domain events | `EventPublisher` |
| `PendingOutbox` | Fetch and mark outbox delivery rows | `SqlAlchemyOutboxRepository` |

This keeps use cases testable without depending directly on infrastructure.
FastAPI dependencies in `app/api/dependencies.py` are the composition boundary for
HTTP requests, while `app/bootstrap/events.py` assembles event catalogs,
dispatchers, codecs, publishers, stores, and workers.

## API

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Liveness probe. Does not touch the database. |
| `POST` | `/api/v1/users` | None | Register a user. |
| `POST` | `/api/v1/auth/login` | None | Issue access and refresh tokens. |
| `POST` | `/api/v1/auth/refresh` | Refresh token body | Rotate token pair. |
| `POST` | `/api/v1/auth/logout` | Refresh token body | Revoke refresh token, idempotently. |
| `GET` | `/api/v1/users/me` | Bearer access token | Return the current authenticated user. |

Example login request:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123"}'
```

In production mode, OpenAPI docs are disabled unless `DEBUG=true`.

## Runtime Configuration

Configuration is loaded with Pydantic Settings from environment variables and an
optional `.env` file. Important settings include:

| Setting | Purpose |
|---|---|
| `ENV` | `dev`, `test`, `staging`, or `prod`. |
| `WRITER_DB_URL` | Primary SQLAlchemy database URL. |
| `READER_DB_URL` | Optional read database URL; defaults to writer. |
| `DB_SSL_MODE` | `disable`, `require`, `verify-ca`, or `verify-full`. |
| `JWT_SECRET_KEY` | Signing secret for access and refresh JWTs. |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | Access-token TTL. |
| `REFRESH_TOKEN_EXPIRE_SECONDS` | Refresh-token TTL. |
| `EVENT_DELIVERY_WORKER_ENABLED` | Enables the embedded outbox worker. |
| `EVENT_DELIVERY_POLL_INTERVAL_SECONDS` | Outbox worker poll interval. |
| `EVENT_DELIVERY_BATCH_SIZE` | Max outbox rows processed per poll. |
| `RUN_MIGRATIONS_ON_STARTUP` | Optional production startup migration toggle. |

PostgreSQL URLs using `postgresql://` or `postgres://` are normalized to the
asyncpg driver at runtime. Libpq SSL query parameters are stripped and replaced
with an explicit asyncpg SSL context built from the `DB_SSL_*` settings.

## Docker Development

Start the full development stack:

```bash
docker compose -f docker-compose-dev.yml up --build -d
```

The development compose file starts:

- `api`: FastAPI with Uvicorn reload and optional debugpy on port `5678`.
- `db`: PostgreSQL 17 with a persistent named volume.
- `redis`: Redis 7.2, available for future integrations.

The API container waits for Postgres, runs `alembic upgrade head`, then starts
Uvicorn. Source code, migrations, and `alembic.ini` are bind-mounted for reload.

Useful commands:

```bash
curl http://localhost:8000/health
docker compose -f docker-compose-dev.yml logs -f api
docker compose -f docker-compose-dev.yml exec api alembic current
docker compose -f docker-compose-dev.yml exec api alembic check
```

## Production Image

The production image is built from `docker/api/Dockerfile.prod`.

```bash
docker build -f docker/api/Dockerfile.prod -t rakieta_api:prod .
```

The image uses:

- A Poetry export stage to produce pip-installable requirements.
- A builder stage that installs dependencies into a clean prefix.
- A slim runtime stage with `tini`, `gunicorn`, and `uvicorn.workers.UvicornWorker`.
- A non-root `app` user.
- A Docker health check against `/health`.
- A `.dockerignore` that excludes local env files, secrets, cache directories,
  docs, and other non-runtime artifacts from the image context.

`docker-compose-prod.yml` is available for an on-host production-style API
container. It expects secrets and database URLs from the environment or
`.env.prod`; it does not define a database service.

## Database Migrations

Alembic migrations live in `migrations/versions`.

Current migration sequence:

1. `0001_initial`: users and refresh tokens.
2. `0002_event_outbox`: transactional outbox table.
3. `0003_outbox_delivery_leases`: historical outbox leasing state.
4. `0004_simplify_event_outbox_state`: simplified outbox state.
5. `0005_event_delivery_queue`: renamed outbox to delivery queue.
6. `0006_event_store`: append-only aggregate event store.

`migrations/env.py` resolves the database URL from `Settings.WRITER_DB_URL` or
`ALEMBIC_DATABASE_URL`, converts asyncpg URLs to sync psycopg URLs for Alembic,
and imports all ORM models so schema checks see the full metadata.

## Testing And Quality

The test suite uses pytest, pytest-asyncio, HTTPX ASGI transport, and in-memory
SQLite with `StaticPool` so each test gets a fast isolated database.

Test coverage is split by intent:

- API tests cover signup, login, refresh, logout, health, `/users/me`, and event
  delivery behavior.
- Unit tests cover domain value objects, event-sourced aggregate behavior,
  refresh-token rules, current-user resolution, event-store version conflicts,
  outbox delivery, and worker lifecycle.

Run tests:

```bash
poetry install
poetry run pytest
```

Run linting:

```bash
poetry run ruff check .
```

The configured tooling includes Black, isort, Ruff, mypy, pytest-cov, and
pytest-env.

## Security Practices

- Passwords and persisted refresh tokens are hashed with bcrypt.
- Passwords longer than bcrypt's 72-byte input limit are SHA-256 prehashed
  before bcrypt hashing, with legacy truncated-bcrypt verification retained.
- Access and refresh tokens carry explicit `token_type`; access tokens cannot be
  used as refresh tokens and refresh tokens cannot authenticate `/users/me`.
- Refresh-token rotation revokes the old token before accepting the next one.
- Logout is idempotent and does not reveal whether a refresh token exists.
- JWT decode requires `exp`, `iat`, `sub`, and `jti`, and validates issuer.
- Domain/application errors are rendered as structured JSON responses.
- Production docs are disabled by default.
- Database TLS is explicit through `DB_SSL_MODE` and certificate path settings.
- Runtime secrets are expected from environment-specific secret management, not
  baked into images.
- Local `.env.*`, `.secrets`, `pgdata`, cache, and coverage directories are
  runtime artifacts, not source architecture, and are excluded from Docker image
  builds.

## Operational Notes

- `/health` is intentionally a lightweight liveness check and does not query the
  database. This prevents transient database issues from causing noisy health
  check cascades.
- Migrations run automatically in the development container. In production, they
  are off by default and can be enabled with `RUN_MIGRATIONS_ON_STARTUP=true` if
  that operational model is desired.
- Event delivery is hosted inside the API process by default. If the worker is
  disabled, domain events still enter `event_delivery_queue` and can be delivered
  by a separately hosted worker using the same application workflow.
- Detailed cloud deployment notes live in `docs/deployment/aws-ecs.md`; this
  README focuses on the service architecture and Docker runtime.

## Out Of Scope

- Email verification.
- Password reset.
- OAuth or external identity providers.
- Rate limiting.
- Persistent access-token revocation list.
