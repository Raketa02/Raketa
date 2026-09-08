# Raketa

Raketa is a production-oriented FastAPI service for user registration,
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
- Player photo upload and retrieval, behind an S3-compatible storage port, with
  the on-court check run by a CLIP sidecar over HTTP.
- Dockerized local development and production runtime images.

## Architecture

The repository uses a modular architecture under `app/`:

```text
app/
  main.py                         FastAPI app factory and health endpoint
  api/
    v1/router.py                  API version router composition
    dependencies.py               Request-scoped declarations over the factories
  core/                           Settings, lifespan, logging, middleware, errors
  application/
    ports/                        Protocols consumed by use cases
    events/                       Event catalog, codec contracts, dispatcher workflow
  bootstrap/
    composition.py                Adapter factories — every port, no web framework
    events.py                     Runtime assembly for event catalog/dispatcher/worker
    jobs.py                       The register of scheduled jobs — add the next one here
  infrastructure/
    database/                     SQLAlchemy engine, sessions, unit of work, ORM imports
    events/                       Event store, outbox, codec, delivery worker adapters
    jobs/                         The periodic-job loop every scheduled job runs on
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
are built by `app/bootstrap/composition.py` and declared to the framework by the
dependency modules — the composition root is one root, and it does not need a
request.

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
| `PhotoStorage` | Store and sign URLs for photo bytes | `S3PhotoStorage` (MinIO locally) |
| `ImageTranscoder` | Re-encode an upload to the stored format | `PillowImageTranscoder` |
| `PhotoReview` | Whether a photo meets the on-court rule | `ClipSidecarPhotoReview` (a container, over HTTP) |

This keeps use cases testable without depending directly on infrastructure.

**Every adapter is constructed in `app/bootstrap/composition.py`** — one plain
function per port, taking a database session and the settings. Nothing in it
imports FastAPI and nothing in it reads a request, so anything that is not an
HTTP request (a seed run, a worker, a management command) assembles a use case
without booting the API. `app/bootstrap/events.py` assembles event catalogs,
dispatchers, codecs, publishers, stores and workers, and `get_event_runtime()`
hands back the process's runtime rather than one read off an application object.

`app/api/dependencies.py` and each module's `presentation/dependencies.py` are
thin callers over those factories. They decide *when* an adapter is built and how
long it lives — one per request, cached by FastAPI for that request — and never
what is built. The split is enforced by a walk, not by review:
`tests/unit/test_composition_root.py` fails if a dependency declaration imports
an adapter, because the alternative is one line of convenience inside a `Depends`
callable, and nothing about a green suite would look different afterwards.

## API

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Liveness probe. Does not touch the database. |
| `POST` | `/api/v1/users` | None | Register a user. |
| `POST` | `/api/v1/auth/login` | None | Issue access and refresh tokens. |
| `POST` | `/api/v1/auth/refresh` | Refresh token body | Rotate token pair. |
| `POST` | `/api/v1/auth/logout` | Refresh token body | Revoke refresh token, idempotently. |
| `GET` | `/api/v1/users/me` | Bearer access token | Return the current authenticated user. |
| `POST` | `/api/v1/photos` | Bearer access token | Upload one photo. Raw image body; `Content-Type` names the format. |
| `GET` | `/api/v1/photos/{photo_id}` | Bearer access token | A short-lived signed URL for one of your own photos. |

The route table above is not the whole surface — `/api/v1/sports`,
`/api/v1/assessments`, `/api/v1/ratings` and `/api/v1/player-profile/options`
are in `openapi.player.json`, which is the document that is authoritative.

There is a second surface, and it is not a client: the **dev console** at `/dev`, whose
contract is `openapi.dev.json` and holds one path. It is served in `local`, `development`
and `staging` and refuses to be imported in `production`. See *The Dev Console* below.

Example login request:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123"}'
```

In `production`, OpenAPI docs are disabled, with no way to re-enable them.

## Runtime Configuration

Configuration is loaded with Pydantic Settings from environment variables and an
optional `.env` file.

### The four environments

`APP_ENV` is a strict enum over **`local`**, **`development`**, **`staging`** and
**`production`** — the same four spellings the player app and the club app use. A
value outside that set fails at startup rather than being accepted silently.

**Only `local` runs today.** `development` and `staging` are defined and validated
but not provisioned: no domain is registered, so neither has a host or a database.
Selecting one without setting `APP_HOST` and `WRITER_DB_URL` is a startup failure
naming the missing variable — never a silent fallback.

`APP_ENV` supplies the defaults for the three settings that always move together.
Each stays overridable by setting it explicitly:

| `APP_ENV` | `DEBUG` | `LOG_LEVEL` | `LOG_JSON` |
|---|---|---|---|
| `local` | `true` | `DEBUG` | `false` |
| `development` | `false` | `DEBUG` | `true` |
| `staging` | `false` | `INFO` | `true` |
| `production` | `false` | `INFO` | `true` |

The boundary that governs this: **the environment may select configuration defaults;
it may never select behaviour a domain test could observe.** No business rule,
threshold, validation, status code or response shape varies by `APP_ENV`.

That boundary is enforced, not remembered. An `.importlinter` contract forbids
`app.core.config` to the domain and application layers — `app/application/`,
`app/shared/domain/`, and every `app/modules/*/domain` and `app/modules/*/application`
— so configuration can only be read at the composition boundary and handed inward. A
use case that needs a configured value takes it as a constructor argument.
`pydantic_settings` and `os` are forbidden beside it, since declaring a second
settings class or reading `os.environ` is the same rule broken by a different import.

The two `app/modules/*` arms are wildcards, so a context created tomorrow is fenced
without anybody editing `.importlinter`. `make check` runs the contract; `make
test-gates` drives it against a deliberately-violating tree — one probe per arm,
because **import-linter reports a wildcard matching nothing as KEPT**, and an arm
that quietly stopped matching would read as a fence that held and checked nothing.

### Refusing to start

Configuration that is dangerous rather than merely wrong refuses to boot. Every
refusal names the offending variable and the reason, and **never echoes its value** —
a `WRITER_DB_URL` carries a password, and a refusal message ends up in a log
aggregator.

| Refused when | Because |
|---|---|
| `APP_ENV` is not one of the four | A typo must not silently change behaviour. |
| `development`/`staging` with no `APP_HOST` or `WRITER_DB_URL` | Neither is provisioned; falling back points at a database that does not exist. |
| `development`/`staging` with no `REDIS_URL` | Same reason, one step further: the ledgers behind it fail soft, so falling back to a laptop's service name would boot permanently degraded and look exactly like a quiet week. |
| `production` with the default `JWT_SECRET_KEY` | It is public in this repo's history, so every token it signs is forgeable. |
| `production` with the default `PHOTO_STORAGE_SECRET_KEY` | It is the local MinIO container's, published in this repo, and it unlocks every photo the platform holds. |
| `production` with `DEBUG=true` | It serves verbose errors to callers. |
| `production` with wildcard `ALLOW_ORIGINS` **and** `ALLOW_CREDENTIALS` | Browsers reject the combination anyway. |
| a deployed environment with a non-`https://` entry in `ALLOW_ORIGINS` | A browser origin reached over a public network in the clear is a session cookie in the clear. |
| `production` with a `DB_SSL_MODE` that does not encrypt | Transport security should not be something anyone has to remember. |

The origin refusal is the backend's instance of the platform's **public-network scheme
rule**, added by #99 so that all three apps carry it (`docs/environments.md`). The backend
calls nothing over HTTP, so `ALLOW_ORIGINS` is the only public-network URL it holds. The
wildcard is skipped — it is not an origin, and it has its own refusal above — and `local`
is exempt, because `http://localhost:3000` is what the club app actually serves on a
laptop. The message reports how many entries are wrong, never which.

The checks live on the settings object, not in the application factory, so they hold
for every construction path — a worker, a migration or a seed run, not only a process
serving HTTP.

### Settings

| Setting | Purpose |
|---|---|
| `APP_ENV` | `local`, `development`, `staging`, or `production`. |
| `WRITER_DB_URL` | Primary SQLAlchemy database URL. |
| `READER_DB_URL` | Optional read database URL; defaults to writer. |
| `DB_SSL_MODE` | `disable`, `require`, `verify-ca`, or `verify-full`. |
| `JWT_SECRET_KEY` | Signing secret for access and refresh JWTs. |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | Access-token TTL. |
| `REFRESH_TOKEN_EXPIRE_SECONDS` | Refresh-token TTL. |
| `EVENT_DELIVERY_WORKER_ENABLED` | Enables the embedded outbox worker. |
| `EVENT_DELIVERY_POLL_INTERVAL_SECONDS` | Outbox worker poll interval. |
| `EVENT_DELIVERY_BATCH_SIZE` | Max outbox rows processed per poll. |
| `PHOTO_REVIEW_ENDPOINT_URL` | Where the photo-review sidecar is. Server-to-server; no scheme rule. |
| `PHOTO_REVIEW_TIMEOUT_SECONDS` | The whole budget for one review. Exceeding it fails open. |
| `PHOTO_SWEEP_ENABLED` | Enables the uncommitted-photo sweep job. |
| `PHOTO_SWEEP_INTERVAL_SECONDS` | How often the sweep runs. Not the retention window — see *Background Jobs*. |
| `PHOTO_REVIEW_BACKFILL_ENABLED` | Enables the photo re-review backfill job. |
| `PHOTO_REVIEW_BACKFILL_INTERVAL_SECONDS` | How often the backfill runs. |
| `PHOTO_REVIEW_BACKFILL_BATCH_LIMIT` | Most photos one backfill run may send to the reviewer. |
| `PHOTO_REVIEW_BACKFILL_PAUSE_SECONDS` | Gap between two reviews inside one run. Not which photos it picks — that is the note on the object. |
| `REDIS_URL` | The ephemeral store, holding the exposure and suppression ledgers. Server-to-server; no scheme rule. |
| `EXPOSURE_ROLL_ENABLED` | Enables the hourly exposure roll. |
| `EXPOSURE_ROLL_INTERVAL_SECONDS` | How often the roll runs. Not either ledger's TTL — see *The ephemeral store*. |
| `INTENT_DRIFT_ENABLED` | Enables the daily intent-drift prompt loop. |
| `INTENT_DRIFT_INTERVAL_SECONDS` | How often it runs. Not any of its thresholds — those are domain. |
| `GRID_STALENESS_ENABLED` | Enables the daily availability-staleness prompt loop. |
| `GRID_STALENESS_INTERVAL_SECONDS` | How often it runs. Not how old a grid must be — that is domain. |
| `INTEREST_EXPIRY_ENABLED` | Enables the hourly *Let's play* expiry sweep. |
| `INTEREST_EXPIRY_INTERVAL_SECONDS` | How often the sweep runs. **Not `INTEREST_TTL`**, which is a ruleset row. |
| `CHALLENGE_LAPSE_ENABLED` | Enables the hourly challenge lapse loop, which records a passed answer window as a lapse. |
| `CHALLENGE_LAPSE_INTERVAL_SECONDS` | How often it runs. **Not `ANSWER_WINDOW`**, which is the promise the invitation makes and is domain. |
| `RATING_CATCH_UP_ENABLED` | Enables the hourly rating catch-up, which moves a Level on every confirmed counted result. **The only job whose absence a player would notice** — nothing announces a confirmation, so this is the whole path a result has to a rating. |
| `RATING_CATCH_UP_INTERVAL_SECONDS` | How often it runs. **Not the update rule**, which is `engines/racketskill/results.py` and is domain — an environment that could pick a K-factor decides how a marketplace rates people. |
| `SCALE_PRESSURE_ENABLED` | Enables the scale-pressure probe — trigger 1's event-loop lag monitor, which also closes the fifteen-minute scoring window. |
| `SCALE_PRESSURE_INTERVAL_SECONDS` | How often it ticks. The tick *is* the measurement: the probe records how much later than this the loop got back to it. **Not the trigger's 15-minute window and not its thresholds** — those are domain, in `matchmaking/domain/scale_triggers.py`. |
| `GUNICORN_WORKERS` | How many workers this container runs. Read by `docker/api/startup.prod.sh` and by trigger 4's arithmetic, so the memory reading is about the fleet that exists. It selects no behaviour: it is a multiplier inside a log record. |
| `RUN_MIGRATIONS_ON_STARTUP` | Optional production startup migration toggle. |

PostgreSQL URLs using `postgresql://` or `postgres://` are normalized to the
asyncpg driver at runtime. Libpq SSL query parameters are stripped and replaced
with an explicit asyncpg SSL context built from the `DB_SSL_*` settings.

## Docker Development

Start the full development stack:

```bash
docker compose -f docker-compose-local.yml up --build -d
```

The development compose file starts:

- `api`: FastAPI with Uvicorn reload and optional debugpy on port `5678`.
- `db`: PostgreSQL 17 with a persistent named volume.
- `minio`: S3-compatible object storage for player photos, with a persistent
  named volume. The S3 API is on `9000` and the browser console on `9001`.
- `minio-init`: creates the photo bucket and exits.
- `photo-review`: the on-court photo check — a CLIP model behind one HTTP route,
  on `8100`. Built from `docker/photo-review/` with the weights baked in, so the
  first build is slow and a container start needs no network. **The API does not
  wait for it**: the client fails open, so a sidecar still loading costs an
  upload its verdict and never costs a player their photo.
- `redis`: Redis 7.2, available for future integrations.

The API container waits for Postgres, runs `alembic upgrade head`, then starts
Uvicorn. Source code, migrations, and `alembic.ini` are bind-mounted for reload.

Useful commands:

```bash
curl http://localhost:8000/health
docker compose -f docker-compose-local.yml logs -f api
docker compose -f docker-compose-local.yml exec api alembic current
docker compose -f docker-compose-local.yml exec api alembic check
```

## Production Image

> **Dormant.** There is no deployed environment — development is entirely local
> (`docker-compose-local.yml`). This section and `docker-compose-prod.yml` are kept
> intact for when deployment resumes; see
> [ADR-0010](../docs/adr/0010-local-first-development-aws-deferred.md).

The production image is built from `docker/api/Dockerfile.prod`.

```bash
docker build -f docker/api/Dockerfile.prod -t raketa_api:prod .
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

## Seed Data

Deterministic development accounts, so a screen can be built against a fixed starting
point rather than against whatever the database drifted into.

```bash
make seed        # into the running stack's database (needs `make up` first)
make seed-host   # the same seed from the host — needs .env, like host-run uvicorn
```

Both run `python -m app.seeds`. The schema must already exist; `make up` migrates on
container start.

Every address is `<state>@raketa.example`, and the state is what the name says. The
catalog is a list of **edges**, not of people: nothing yet, exactly one, the maximum, the
failed case. A hundred average players is one scenario a hundred times, and no screen
breaks on it.

| Address | State |
| --- | --- |
| `brand-new-player@raketa.example` | Registered and nothing else — every empty state at once |
| `assessment-in-progress@raketa.example` | Padel assessment open at its first question, no rating |
| `assessment-abandoned@raketa.example` | Padel run ended without a rating; the sport is free to start again |
| `assessment-completed@raketa.example` | One completed run and the rating it produced, band **New** |
| `rating-barely-established@raketa.example` | Padel Level just inside **Established**, its range still reaching into Developing |
| `rating-well-established@raketa.example` | Padel Level well inside **Established**, clear of the lower edge |
| `rated-in-every-sport@raketa.example` | All four sports rated, one per band — the longest ratings list there is |
| `the-populated-player@raketa.example` | **The default protagonist.** Padel and tennis rated, settled, at the centre of every ring — every Play screen is developed signed in as this one |
| `the-newcomer@raketa.example` | The same answers and a profile committed inside ADR-0113's fourteen days — the widened gate from the newcomer's own side |
| `the-one-sport-player@raketa.example` | Padel and no tennis at all — a second sport's absence, refused rather than emptied |
| `the-blank-week-player@raketa.example` | A week committed and then cleared — the availability term stands down rather than scoring a nought |

The password for every seeded account is `raketa-seed1`, and it is public by
construction — it is written in `app/seeds/catalog.py`.

Behind those eleven state-named addresses is the **cohort**: a population of `cohort-<ring>-<nn>`
members, generated from a seed and committed as `app/seeds/cohort.json`. It exists because
one search over eleven accounts finds them all in one ring, and every Play screen would be
developed against an empty result.

It is a **workbench and it says so on its own report**: chosen so that every Play screen
state is *reachable*, standing for nothing outside itself, describing no real market. The
comparator corpus under `docs/specs/matchmaking/ruleset-diff/` answers a different question
and is not this — the cohort borrows its mechanics (seeded draws keyed off a handle,
assignment by rule rather than by rate) and none of its numbers.

Two lists, and they are asymmetric. `app/seeds/cohort.py` holds the **declarations** — the
generator's inputs: rings cut by the relaxation ladder's own ×1.5 and ×2.0 plus a handful
past the slider's 50 km ceiling, one archetype per band, and a rule apiece for the newcomer
share, the proposals opt-out, the mutual-gender exclusion and the dual-sport membership.
`app/seeds/screens.py` holds the **assertions**, and every one of them is an outcome of a
real read path run as the protagonist — the pool search, the deal, the line-up, the ladder.
Nothing is asserted about a number the generator chose, because a ruleset that tightens
`QUALITY_FLOOR` moves no distribution at all and still empties every screen.

Regenerate the population with `make gen-cohort` and commit the result. It records
**inputs only** — no level, no uncertainty, no band, because those are the engine's answers
and a committed copy of an answer is a second number nothing keeps honest.

Behind the cohort is a third layer, and it exists because **a distribution cannot assert a
pair**. Five of the ten Liveness codes a card can print are facts about two people — *they
said yes to you*, *they turned your court down*, *their inbox is full* — and no population,
however well shaped, can exhibit one: a rate over sixty members produces edges nobody
named, and it cannot assert that *exactly one* instant-match pair exists. So eleven
accounts are named for a **relationship to `the-populated-player`**, from her side, and
`app/seeds/pairs.py` writes each edge through the use case that owns it.

| Address | Relationship, and what it makes true |
| --- | --- |
| `said-yes-to-you@raketa.example` | A live inbound *Let's play* — her pool card carries `INTEREST_RECEIVED`, the only lift that admits below `QUALITY_FLOOR` |
| `your-yes-makes-it-mutual@raketa.example` | A second live yes, on her **deck** — say yes back and a game opens inline. The one instant match this database can produce |
| `you-said-yes-to-them@raketa.example` | Her own outgoing yes — the outstanding-per-sport count, and a repeat tap that changes nothing |
| `you-challenged-them@raketa.example` | An open **tennis** singles challenge, so they are missing from her **padel** pool — one open challenge per pair, across sports |
| `they-challenged-you@raketa.example` | Organiser of a padel doubles court she holds a seat on, with its own day running |
| `in-your-line-up-and-accepted@raketa.example` | A co-invitee on that court who said yes — a filled seat, and gone from every one of her surfaces |
| `in-your-line-up-still-deciding@raketa.example` | The other co-invitee, who has answered nothing — an unanswered seat beside the filled one |
| `they-turned-down-your-court@raketa.example` | Declined a seat on a court she organised; it ended with the seat, so they are back in her pool carrying the refusal |
| `you-blocked-them@raketa.example` | Blocked by her — absent from all four surfaces, silently |
| `they-blocked-you@raketa.example` | Blocked **her** — the same absence and a different fact, and it is checkable only by signing in as them |
| `you-passed-them@raketa.example` | Passed on — gone from her deck and a full candidate in her pool |

Three rules shape that layer, and each is a way a relationship fixture goes wrong:

- **Every edge costs a real search or deal run as the sender**, because `Interest` and
  `Pass` have no non-search constructor and a send cites the search its court was built on.
  That cost is turned into the check: the origin must resolve, which proves the protagonist
  was genuinely findable through gender, level and radius before any lift is claimed.
- **An absence claim asserts the gate histogram, not the absence.** An account gated for an
  accidental reason — no rating, out of range, the wrong gender preference — is absent too,
  and a naive claim passes; the histogram is counted first-in-declaration order, so
  `excluded_by_gate[OPEN_CHALLENGE] >= 4` names the reason exactly.
- **One code is not reached by these fixtures.** A pair is `OPEN_CHALLENGE`-gated while
  they are still **arranging**, and this cohort's accepted seat is exactly that — a
  co-invitee's seat on a doubles court with an unanswered seat beside it — so
  `PREVIOUS_ACCEPT` is drawn on no card here. It is **not** unreachable on the platform:
  [ADR-0142](../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §1 releases a pair the moment their line-up completes, so a pair who finished arranging a
  game are shown each other again. The code is listed as absent **by name**, with that
  reason, and the release is contracted by a demand in `tests/demands/` — and the run goes
  red on the day the code *is* drawn here, which is how it moves to the promised side.

Two costs are printed on the report rather than hidden. The pass's suppression is a Redis
TTL that **fails soft** while its durable row never expires, so the run is idempotent for
the row and unconditional for the cache — and when a deck deals somebody it should not, the
complaint names the cache rather than accusing the fixture. And the deal that earned the
pass's origin key is remembered for a day (ADR-0131), so `make seed` leaves the
protagonist's deck that many cards short.

Behind all of it is a fourth layer, and it is the only one that **writes nothing until the
outbox has run**. A conversation is *told* — its rooms are opened and grown from events
`challenges` and `games` publish, by contexts that do not know it exists
([ADR-0146](../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §5) —
so there is no *open a room* use case for a fixture to call and deliberately none.
`app/seeds/rooms.py` drains the transactional outbox in process, exactly as the embedded
worker drains it under the API, and every acceptance, completion and *we played* the layers
above already seeded arrives at the room it belongs to. What it then writes is the one
thing a room cannot be told: somebody saying something, through `SendMessage`, enough of it
to reach **a room long enough to page backward through**.

It reaches three of the four room shapes a screen has to draw — a two-member room whose
game is recorded, a doubles room whose membership is still growing, and the deep one — and
**names the fourth on the report rather than in a docstring**: a room carrying every
system-line code needs a `SeatsInvited`, nothing here performs a fill, and a fill would cost
a real search that seats somebody new and moves the gate histogram this run asserts. A
fixture that quietly reached three of four reads as having reached four.

Scope is what is **modeled**: players, onboarding assessments, Skill ratings, Player
profiles, Challenges and Blocks. Clubs, Courts, Bookings and Matches have no aggregates, so they
have no scenarios; each adds its own when it exists. A walk over `app/seeds/` asserts the
package **writes** those six contexts and reaches every other one — matchmaking, today —
only through that context's own use cases. Conversations is on neither side of that walk,
and that is the point: the seed never writes one, and the rooms in the database are there
because the outbox delivered what the six wrote.

Six rules hold this together, and each exists because of a specific way seed data goes
wrong:

- **Seeds execute use cases; nothing writes a table.** These aggregates are event-sourced
  with a transactional outbox, so a directly-inserted row is an aggregate with no history:
  it reads correctly until something replays it. Wiring comes from
  `app/bootstrap/composition.py` — the composition root the API uses, not a copy of it.
  A structural walk over `app/seeds/` refuses a statement import, an ORM model and
  `session.add`.
- **A rated account answers the questionnaire.** The engine chooses each question from the
  answers so far, so the only route to a Level near the bottom of Established is to answer
  the way a player would. A scenario carries an `AnswerPolicy` — which option to pick,
  counted from the weakest — and the transcript behind the rating is one a review screen
  can render.
- **Re-running changes nothing.** Registration is skipped when the address is already
  there; starting an assessment needs no help, because `CreateAssessment` is already
  idempotent per player and sport; and abandoning or completing looks at the run itself,
  because *abandoned* and *never started* are the same answer from every finder. That last
  probe is also what resumes a run an interrupted seed left half answered. A seeded
  account's **address** is the stable handle — its uuid is minted by the write path, so a
  fresh database yields a new one.
- **A name that stops matching its state stops the seed.** Every rated scenario carries the
  band it promises and where in that band the Level must sit; the runner checks it against
  the **stored** rating on every run, including one that creates nothing. Retune the engine
  so `rating-barely-established` lands in Developing and `make seed` says so by name — an
  account whose name lies is worse than one that is missing, because nothing about the
  screen it is developed against would look wrong.
- **The seed runs on injected clocks, and the calendar can fail it.** `SystemClock` makes
  a *settled* player unreachable on a fresh database — everybody committed through the wall
  clock is a newcomer, and ADR-0113's gate cannot be seen with one side present. So each
  account and each member is written on a clock set to its own commit date, straddling the
  fourteen days with both edges clear. `Clock` is a port and the commit is the same use
  case, so ADR-0029 is honoured rather than bent. The dates are relative to the run that
  wrote them and a re-run re-commits nothing, so a fortnight on every newcomer ages out at
  once — and `make seed` **fails by name, with the age in days**, rather than handing a
  developer a newcomer path with no newcomers in it.
- **The assertions read the screens, and the seed ticks the tail first.** They read the
  candidate index, which has not seen what the run just wrote — so the run folds the log in
  **in this process** before asserting. That is safe by ADR-0110's own design: the index is
  a projection behind one `FOR UPDATE` cursor, so a concurrent API tick blocks and then
  finds nothing to do. Half the gate is a signature: none of this runs in CI, because it
  needs a database with the seed in it.
- **Production is refused, on import.** `app/seeds/__init__.py` calls the guard, so
  importing anything in the package under `APP_ENV=production` raises `SeedRefused`
  before a database is opened. The guard is not in the make target: a make target is not
  what runs inside a container.

Addresses are on `.example` — a TLD RFC 2606 reserves, so no registry can sell it and a
run pointed at the wrong database cannot mail a stranger. Not the `.test` of the same
sentence, because `EmailStr` at the HTTP boundary refuses that one and a seeded account
nobody can sign in as is not an account.

## The Dev Console

**Nothing in Play can be exercised with one phone.** `Line-up incomplete`, the decline that
reopens a seat, the instant match born of a mutual yes — every one of them needs a real
second player answering. The dev console is that second player.

```bash
make up && make seed          # the stack, and the accounts to act as
open http://localhost:8000/dev
```

Three views, in order — **roster**, **search as**, **answer as**. Pick a row, and the
console signs in as that account through the ordinary `POST /api/v1/auth/login` with the
one public seed password. From there it runs real searches, says *Let's play*, and accepts
or declines seats, all through the player API, as that player.

What it is, stated because each half is load-bearing:

- **It is not a third app.** It is `app/api/dev/`, one no-build `console.html` behind a
  `FileResponse` and one route. No npm, no bundler, no codegen, no lint lane. The day it
  wants a component tree it has become a product, and the placement is re-argued rather
  than grown into.
- **There is no impersonation endpoint and no `Act-As` header.** The obvious shape —
  `POST /dev/sessions {handle} → tokens` — was refused by name. The browser presents a
  credential to the ordinary login route, which means the roster hands it one: the response
  carries the seed password **once, at the top level**, because one password for every
  seeded account is what `app/seeds/catalog.py` decided. The consequence is the good one —
  every write the console presses is a *player-surface* write.
- **It is gated structurally and by data, and only one of those can fail.** The structural
  gate is `app/api/dev/gate.py`'s `CONSOLE_SERVED`, a second table written out per
  environment — importing `app/api/dev/routes.py` under `APP_ENV=production` raises
  `ConsoleRefused`, and `create_app` mounts nothing. The data gate is a *consequence*: the
  roster lists accounts addressed on the reserved `.example` TLD, and production has none.
- **Nothing reacts on its own.** There is not one timer in the page. UI spec §G4 is explicit
  that *"acceptance is not instant and may never arrive"*, and the console exists so that a
  human decides when the other side answers.
- **Its contract is `openapi.dev.json`, and it holds exactly one path** — the roster.
  Nothing generates types from it, so it is gated by a **freshness** check
  (`make contract-freshness`) rather than by the client drift check, which has no purchase
  on a document with no client.

## Photo Storage

Player photos are the first thing this platform stores that is expensive per unit
and cannot be regenerated. They live behind a **`PhotoStorage` port**
([ADR-0091](../docs/adr/0091-photo-storage-behind-a-port.md)), with one
S3-compatible adapter: MinIO on a laptop, AWS S3 deployed, the same class with a
different endpoint. That is the whole of the deployed answer — a setting, not a
migration of live user data, which is what shipping them as `bytea` in Postgres
would have cost.

**One photo per request.** `POST /api/v1/photos` takes the raw image as the
request body with `Content-Type` naming the format, and returns an id. The
profile commit will carry **ids only**: three multi-megabyte images inside an
idempotent JSON POST would turn it into a multipart upload whose failure took the
whole part's answers with it.

**Bytes are re-encoded on receipt** — accepted as JPEG, PNG or HEIC/HEIF, stored
as JPEG with the long edge capped. Re-encoding is the mechanism, not an
optimisation: it is how EXIF is stripped reliably, and EXIF carries GPS, which
the product's privacy rules put in the row nobody ever sees. The orientation tag
is applied before it is discarded, or every phone photo is stored sideways.

Two caps, and they answer different questions. `MAX_UPLOAD_BYTES` bounds the
request and is enforced *while the body streams*, because Starlette's multipart
parser caps only non-file parts and would otherwise spool an unbounded upload to
disk before a handler ran. `MAX_DECODED_PIXELS` bounds the image's **declared**
dimensions, read from the header before a pixel is allocated — a small PNG can
declare 30000x30000 and decode to 2.7 GB, which the byte cap cannot see.

**Photos are served through short-lived presigned URLs; there is no public
bucket.** Locally that needs two endpoint settings, and the distinction is the
platform's own (`docs/environments.md`): `PHOTO_STORAGE_ENDPOINT_URL` is the
server-to-server address this API calls, and `PHOTO_STORAGE_PUBLIC_ENDPOINT_URL`
is the public-network address a *phone* opens. SigV4 signs the host, so a URL
signed for `http://minio:9000` is invalid everywhere a device can reach.

`.importlinter` holds the ports open: no domain or application layer may import
`PIL`, `pillow_heif`, `aioboto3`, `boto3`, `botocore` or `aiohttp`, directly
**or through the adapter**, and `make test-gates` drives probes through every arm
of that contract.

Uploaded-but-uncommitted photos are swept after 24 hours by a scheduled job —
see *Background Jobs* below.

## The On-Court Photo Check

The product rule is that a profile photo shows a racket sport on a court. It is
checked behind the **`PhotoReview` port**, server-side because a client-side
check is trivially bypassed, and it **soft-warns rather than hard-blocks**: a
flagged photo is stored, and the verdict rides on the object as metadata
([ADR-0091](../docs/adr/0091-photo-storage-behind-a-port.md),
[ADR-0129](../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md)).

**The model runs in a sidecar, not in this process.** `ClipSidecarPhotoReview` is
a thin `aiohttp` client; `docker/photo-review/` is the service. Its image is
**3.2 GB** — `torch`, its BLAS stack and 605 MB of weights — and keeping that out
of `poetry install`, out of every CI run and out of the API image is the whole
point. The model can also be swapped without a backend release.

**The rule stays here; only the arithmetic goes over the wire.** The sidecar is
asked *how close is this image to each of these captions* and answers one raw
cosine similarity per caption. Which captions, how those become a confidence and
where the line sits are in `app/modules/player_profile/domain/photos.py`, beside
the size caps and for the same reason: they are behaviour a domain test can
observe, and a photo flagged on a laptop and allowed in production is exactly
what the environment rule forbids. `PHOTO_REVIEW_ENDPOINT_URL` and
`PHOTO_REVIEW_TIMEOUT_SECONDS` are the configuration, and neither can change a
verdict.

**Every verdict records its evidence** — the model, the prompt-set fingerprint,
the confidence and the raw similarity vector, in the `review-note` metadata key,
on allowed photos as much as flagged ones. The threshold shipping today is an
explicit placeholder, and this is what makes replacing it cheap: the corpus is
already on the objects.

**`make photo-flag-rate` reads that corpus** (#316). It walks the stored notes
and prints the flag rate the check would have produced at each candidate line,
plus how many stored verdicts each move would make wrong. **Read-only in the
strongest sense**: no image is re-scored, nothing is written, and the sidecar is
not asked anything — the whole exercise is a softmax per row over numbers already
held. `make photo-flag-rate THRESHOLDS="0.55 0.6"` asks about particular lines
instead of the default sweep, and `-host` runs it outside the stack.

**It prints the population before the curve**, because a rate is a number over a
denominator. Four exclusions: the photos nobody looked at, the ones that arrived
while the sidecar was down and the ones scored against captions that have since
moved — ADR-0132's three populations — plus a fourth for a note this application
did not write.

**And there is one curve per reviewer, never one blended.** Two models are two
corpora, and a rate across both is a fact about neither. The instance that
matters is not a model upgrade: the seed's declared verdicts
(`app/seeds/photos.py`) go through the real constructors, so their notes are
well-formed and current-fingerprint, and on a laptop they are most of the bucket.
Where the rate should sit, and whether any one corpus is yet big enough for a
rate to mean anything, are the two judgements the command deliberately does not
make.

**It fails open, and an outage now costs silence rather than a word.** An
unreachable, slow, refusing or unusably-answering sidecar yields **no decision**,
with a note naming which of those it was, from a closed set
([ADR-0138](../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
A reviewer that turned its own outage into a failed upload would refuse a real
player's first photo for a reason that is not about the photo; one that recorded
`allowed` would tell twenty strangers an unexamined image had been checked.

**The verdict reaches two audiences, which is why the placeholder is now a cost.**
It crosses on the upload as a warning to the photograph's owner
([ADR-0133](../docs/adr/0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md))
and on a player card as a **✓ ON COURT** shield shown to people who are not
(ADR-0138). A genuine on-court photo scoring 0.49 therefore leaves its owner
silently unbadged on other people's screens, with nothing they can do about it —
the sharper of the two costs, and the one no signal we can read would tell us
about.

## Background Jobs

Two kinds of background work run as `asyncio` tasks inside the API process, both
started and stopped by the lifespan (ADR-0092). There is no cron, no beat
process and no second deployable.

- **The outbox drain** (`EventWorker`) polls `event_delivery_queue` every second
  and dispatches to subscribed handlers. Its worker id is the lease its batches
  claim rows under.
- **Scheduled jobs** (`PeriodicJob`) run because an interval elapsed.
  `app/bootstrap/jobs.py` is the register, and ten jobs are in it today: the
  **uncommitted-photo sweep**, which deletes every photo the object store has
  held for more than 24 hours that no committed profile currently names; the
  **photo re-review backfill**, which asks the reviewer about the photos nobody
  ever asked it about; the candidate index's **tail reader** and **snapshot
  refresh**; the **exposure roll**, which publishes one scalar per sport per week
  saying what *shown more often than most* means; the two **prompt loops** —
  intent drift and availability staleness — which write no value anywhere and each
  raise a standing question instead; the **interest expiry loop**, which removes
  every *Let's play* whose twenty-one days have passed; the **scale-pressure
  probe**, whose work is measuring how late the event loop woke it; and the
  **challenge lapse loop**, which writes down every answer window that passed with
  nothing in it. Two of them take no database session: the roll, whose whole input
  and output are in Redis, and the backfill, whose whole input and output are the
  object store.

  The expiry loop is the only job here that deletes anything, and **correctness
  does not depend on it running**: every read of the interest ledger is bounded by
  `now`, so a lapsed yes lifts nobody and counts against nobody's cap whether or
  not it has been swept. What the loop buys is a table the size of what is live,
  and one figure that could not be bought later — *yeses that expired having never
  lifted anybody*, `INTEREST_TTL`'s only day-one falsifier, which a lapsed row
  leaves no trace to compute.

  The lapse loop is the only job here that **appends a domain event**, and it is
  the clearest case of a loop bought for the record rather than for correctness. A
  seat past its answer window already reads as lapsed, its pair already releases
  and its challenge already stands as `LAPSED`, because a standing is folded from
  the seats and the clock and stored nowhere — a reader asking *is this challenge
  still open* between a deadline and a sweep gets the same answer either way. What
  the loop buys is a `SeatLapsed` in the log, so that **answers challenges** has a
  denominator. What it appends is never a `SeatDeclined`: **a lapse is not a
  decline**, and a Strand that filed silence as judgement would be measuring the
  wrong people. `ANSWER_WINDOW` is domain, in
  `app/modules/challenges/domain/answer_window.py`; only
  `CHALLENGE_LAPSE_INTERVAL_SECONDS` is configuration. It is also the one job
  here that takes **a transaction per item rather than per run**: every process
  walks the same clock-derived list in the same order, so a run that ended on its
  first version conflict would be a loop that made no progress anywhere. A
  conflict is counted and stepped over, exactly as the backfill does with a
  refusal about one image.

**A job may only be registered if it is idempotent and safe to run beside
itself.** With N API processes a job runs N times per interval, at unrelated
moments, and there is no lock anywhere — that is the price of not owning a
scheduler, and ADR-0092 states it as a rule rather than a coincidence. The sweep
qualifies because listing and the reference check are reads and `DeleteObject`
is idempotent.

The **retention window is domain and the cadence is configuration**, and the two
must not be confused. *How old a photo must be before it is an orphan* is a rule
a domain test can observe and lives in
`app/modules/player_profile/domain/photos.py`; *how often the sweep runs* is
`PHOTO_SWEEP_INTERVAL_SECONDS`. Turning the job off changes nothing a domain test
would see — orphans simply accumulate.

The first run of a job happens at startup rather than after the first interval,
which is the only thing that makes a six-hourly job observable on a laptop.

**The re-review backfill is the same shape and the same rules**
([ADR-0132](../docs/adr/0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md)).
Every photo uploaded before the checker landed carries `review: allowed` written by
a pass-through that allowed everything, and nothing looked at those images. *Which
photos need re-reviewing* is a query rather than a guess, because the note already
tells the three populations apart: no note at all is the pass-through era,
`unavailable=…` is a photo that arrived while the sidecar was down, and a full
`clip;m=…;p=…;c=…;s=…` is one that was really scored. The job fixes the first two,
**counts** the third — reviewed honestly against a prompt set that has since moved —
without touching it, because whether that is worth re-running is a judgement nobody
has made. It re-reviews through the same `PhotoReview` port the upload path holds, so
there is exactly one copy of the rule; it never rewrites a note that is already
right, because a metadata update is a copy of the object onto itself; and a run
against a sidecar it cannot **reach** stops rather than stamping a fresh *could
not be asked* over an old one. A refusal about one image is the other case and is
stepped over — ending the run on one would let a single photo end every run at the
same place for ever, which is a stall rather than a pause.

## The ephemeral store

Redis holds the **two ledgers that are allowed to be lossy** — exposure and
suppression — and nothing else (ADR-0093). The rule that separates it from
everything durable is one sentence: **the gate is the cache; the evidence is the
row.** A fact that must survive is a durable row elsewhere. *Who was shown to
whom in week 34* is answered by the search record; *were these two ever passed
on* is answered by the durable pass record, which is exactly the fact a TTL
destroys and exactly why the two are stored apart.

**Both ledgers fail soft, and it is worth saying out loud** because ADR-0095's
*a gate that cannot be evaluated excludes* reads like it should reach them.
Applying that to a suppression would **empty the deck rather than protect
anybody**: a suppression is a courtesy, a block is a safety control. So an
unreachable Redis degrades **ordering and repetition** and never excludes
anybody or empties a surface. The posture is applied once, by
`matchmaking/infrastructure/fail_soft_ledgers.py`, and the composition root
never hands out an unwrapped adapter — so no caller can get it wrong and none
has to remember to.

**Neither TTL is configuration.** How long a suppression lasts is
`PASS_SUPPRESS`, a product number in the released ruleset; how long a week of
exposure survives is `EXPOSURE_RETENTION_WEEKS`, in
`app/modules/matchmaking/domain/ledgers.py`. Both decide what can still be
asked. What *is* configuration is where the store lives and how often the roll
runs — the same split the photo sweep's retention window and cadence have.

**No test needs Redis running.** Both ledgers sit behind ports with an in-memory
implementation that the whole HTTP suite runs against, wired in
`tests/conftest.py` exactly as the object store and the photo-review sidecar
are; and the Redis adapters themselves are exercised by the same contract suite
against an in-process stand-in, so the key shapes and TTLs are tested rather
than assumed.

## Testing And Quality

The test suite uses pytest, pytest-asyncio, HTTPX ASGI transport, and in-memory
SQLite with `StaticPool` so each test gets a fast isolated database.

Test coverage is split by intent:

- API tests cover signup, login, refresh, logout, health, `/users/me`, and event
  delivery behavior.
- Unit tests cover domain value objects, event-sourced aggregate behavior,
  refresh-token rules, current-user resolution, event-store version conflicts,
  outbox delivery, worker and job lifecycle, and the photo sweep in both
  directions — an orphan past the window is removed, a referenced photo is not.

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
  README focuses on the service architecture and Docker runtime. That guide is
  **dormant** — nothing in it is provisioned, and the pipeline is manual-only and
  gated. See [ADR-0010](../docs/adr/0010-local-first-development-aws-deferred.md).

## Out Of Scope

- Email verification.
- Password reset.
- OAuth or external identity providers.
- Rate limiting.
- Persistent access-token revocation list.
