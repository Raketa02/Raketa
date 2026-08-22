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
- `GET /api/v1/now` — the player's home screen composed in one request: three ordered
  regions, a card split into a spine and a situation half, and every code a generated enum.
- Async SQLAlchemy persistence with Alembic migrations.
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

The `matches` module models `Match` as a **record with a version and an outbox**, and it is
the one racket-sport context that is deliberately **not** event-sourced
([ADR-0034](../docs/adr/0034-matches-is-a-record-and-keeps-no-history.md)). Almost nothing
about a match is stored — the state is recomputed from the record and the clock every time
anybody looks — so there is little history to source, and the home screen reads several
matches per open, which a replay per match would sit on top of. Concurrency comes from a
`version` column compared in the UPDATE that bumps it, which is the identical guarantee
`expected_version` gives a stream.

Every stored fact declares one of **five kinds**, by the question *may a reader derive
this*: **Constitutive**, **Occupancy**, **Allocation**, **Crossing** and **Declaration**. A
new fact has to name its kind before it can be added, and a reviewer asking *can a reader
derive this?* has a table to answer from. Two of the flags — `form_cancelled` and
`checkpoint_cancelled` — are **receipts** on conclusions the clock already reached rather
than a sixth kind: the situation derives without them, and they record only that the refund,
the court release and the notice completed. So a downed timekeeper delays the money and never
the truth.

Because the match keeps no history, the outbox trail *is* the record of what happened, and
ADR-0034 attaches one obligation that is not ordinary:

> Every change a support agent would one day need to explain to a player is announced as its
> own named event — never as a generic *match updated*.

That is why `app/modules/matches/domain/events.py` holds twenty-one names rather than one.
Nothing mechanical catches an event published too coarsely, so
`tests/unit/test_match_events.py` walks the aggregate with an AST and fails when a mutating
method announces nothing, and refuses a name that reads like *updated*.

`Match.as_record()` hands the kernel a `MatchRecord` and **needs no other read**: the club's
four hold-policy fields are copied at posting and honoured *as booked*
([ADR-0077](../docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md)),
so a situation is one row-set away with no club fetch on Now's path. The cost is real and is
stated rather than hidden — a club that tightens its cap does not reach a match already
posted, and the hold ladder did **not** change that: the fix, if it is ever needed, is a write
that refreshes the snapshot with an announcement of its own rather than a club read on the
compose path.

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
| `GET` | `/api/v1/now` | Bearer access token | The whole Now screen, composed for this viewer. |

Example login request:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123"}'
```

(The assessment and rating routes are documented in the emitted contract rather than
repeated here; `make openapi` is the source of truth for all of them.)

### `GET /api/v1/now`

One request returns the whole screen. It takes **the selected sport and nothing else** —
no stamp of what the phone is holding, no conditional header — and the server never
answers *nothing has changed*: Now is asked for only when the player is explicitly asking,
and pull-to-refresh carries a promise a `304` would break.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/v1/now?sport=all'
```

`sport` is one of `all · PADEL · TENNIS · SQUASH · BADMINTON`, and `all` means **the sports
this player holds a rating at** — a rating rather than a declaration, because the sports
picker persists nothing and a rating is the only durable record that somebody plays a sport.

The answer is three ordered regions and one fact about the viewer:

| Field | Holds | Empty means |
|---|---|---|
| `offers` | seats offered to her, soonest-to-expire | present, `cards: []` |
| `your_matches` | the matches she is in, chronological | present, `cards: []` |
| `shelves` | the server's fixed list of shelves | present, `shelves: []` |
| `debt` | what she owes, and the one consequence | **absent** (`null`) |

That asymmetry is the rule, not an accident. A **region** with nothing in it is present and
empty; a **shelf** with nothing in it is **absent**, because a shelf makes a claim and a row
appearing every week to say *nothing worth waiting for* is a row players learn to scroll
past. The debt line is absent rather than zero, so the client never compares an amount to
decide whether to draw it.

**The regions are empty in v1.** The route ships before anything fills them, deliberately:
it unblocks both clients against a *compiled* contract, and each later ticket fills one
region without touching the envelope.

### What the Now contract will not carry

Enforced by `tests/unit/test_now_contract_document.py`, which reads the emitted document
back rather than reading the source:

- `server_time` and `next_transition` — two fields with no reader are not
  forwards-compatibility (ADR-0071).
- A degrade marker — a fact about our infrastructure printed on a player's home screen.
- A policy version — support is us, reading our own logs, and a screenshot has a timestamp.
- `tone`, `tag` and `alert` — total functions of the situation, so they belong to the
  client's own thirty-six-row table and a flag would let the two disagree.
- `phase` — refused on the result route and refused here.
- Free text of any kind. No `title`, `label`, `note`, `message` or `sentence`; a shelf
  carries a **code** and an optional **caption code**, and the client writes the words.

Everything that *is* a code crosses as an **OpenAPI enum** — `situation`, the act code,
`TermCode`, the card's hold reason, the cause, the shelf code, the caption code, the cover
and the currency. That is what lets each client write an exhaustive `Record` over a
generated union, so a missing sentence is a build error in the client's own build. A bare
string degrades that `Record` into an index signature, and an index signature never fires.

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
| `production` with the default `JWT_SECRET_KEY` | It is public in this repo's history, so every token it signs is forgeable. |
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

The password for every seeded account is `raketa-seed1`, and it is public by
construction — it is written in `app/seeds/catalog.py`.

Clubs are seeded too, in `app/seeds/clubs.py`, on the same rule — **a club is named for
the state it represents**, and its name is its natural key so the two cannot drift. Seven
of them, one per edge:

| Club | State |
| --- | --- |
| `club-that-never-holds` | `maxHoldAge = 0` — declines to hold a court speculatively at all |
| `club-with-two-padel-categories` | One sport priced as two categories, ADR-0079's `ps` |
| `club-that-retired-a-court` | A closed catalogue row: gone from availability, still named by history |
| `club-that-retired-a-category` | A retired category and the courts that were in it |
| `club-that-tightened-its-cap` | 48 h then 6 h — ADR-0077's motivating scenario, standing |
| `club-that-changed-its-bank` | Two payout destinations and one policy |
| `club-that-needs-a-turnaround` | A quarter of an hour between bookings, so a claim is wider than the game |

Every seeded payout destination carries an IBAN whose check digits are invalid on purpose,
so a run pointed at the wrong database cannot pay a stranger — the reserved-TLD argument,
one context over.

Court claims are seeded too, in `app/seeds/courts.py`, on the same rule:

| Claim | State |
| --- | --- |
| `court-the-club-blocked` | A block the venue published — takes the court, and is never padded |
| `court-claimed-past-the-game` | A claim Raketa created, widened by the club's turnaround |
| `court-given-back` | Released, never deleted: the row stays and blocks nobody |
| `court-bought-outright` | A Booking holding a claim, with the price the player was quoted |

Their windows are **fixed absolute instants** on Monday 7 September 2026, not offsets from
now: *next Tuesday at 18:00* computed at run time is a different Tuesday tomorrow, and a
second run would claim a second court. A week somebody can walk through arrives with the
demo week (`Raketa02/Raketa#96`).

`app/seeds/matches.py` adds eight matches, and here the name is checked by the **kernel**:

| Match | The situation its name promises |
| --- | --- |
| `match-forming` | `forming` — posted, nobody on it, deadline days away |
| `match-with-a-seat-held-and-unpaid` | `formingHeld` — held and paid are two facts |
| `match-past-its-commitment-deadline` | `formingLate` — short, with the deadline behind it |
| `match-that-lost-a-player` | `replacement` — committed, and one seat short |
| `match-played-and-unscored` | `needsResult` — played, waiting twenty-four hours for a score |
| `match-private-with-seats-opened` | `privateOpen` — somebody's court, two seats for sale |
| `match-holding-a-court-softly` | `heldSoft` — one seat from full, and a court kept aside |
| `match-the-club-cancelled` | `cancelledClub` — a decision, not a receipt |

Every other catalog checks a property somebody wrote down. A match's state is *derived*, so a
scenario names the `Situation` it must resolve to and the runner asks `kernel.situation`
against the **stored** record on every run — at the scenario's own fixed instant, because a
situation is a function of the record *and* the clock. Retune a threshold or reorder a rung
and `make seed` stops and says which account's screen just moved.

**No scenario says whether a court is held, and none may.** The hold ladder decides that
(ADR-0031), and it runs inside the same use cases the runner drives — so five of the eight
seeded matches end up holding a real reservation whose holder is `MatchHeld(match_id)`, and
`held_since` is the instant the seeded week entered the tier. That is why
`app/seeds/courts.py` refuses a match-held claim outright: a match's court is *granted*, not
authored, and writing one there would be writing down the answer the ladder computes.

Matches is also the one context seeded on a clock the runner **sets**. Every other seeded
aggregate is timeless; a match *is* its clock, so `committed_at` and a hole's `vacated_at`
taken from the wall clock would make the scenario's name a claim about the day the seed ran.
The `Clock` port is what makes that a configuration rather than a fake.

Scope is what is **decided**: players, onboarding assessments, Skill ratings, clubs, court
reservations and bookings, and matches. Nothing **authors** a match-held reservation — a
match's court is granted by the hold ladder (ADR-0031) as a consequence of its seats and its
clock, so `app/seeds/courts.py` refuses one and `app/seeds/matches.py` gets them for free by
running the real use cases. A walk over `app/seeds/` asserts the package imports **exactly**
the five contexts
that exist — equality in both directions, so it grows deliberately and cannot silently fall
behind.

Four rules hold this together, and each exists because of a specific way seed data goes
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
  screen it is developed against would look wrong. A club carries the same kind of claim,
  written as what its *name* promises — `club-that-never-holds` must still not hold
  speculatively — because a club's numbers are exactly what the catalog authored and
  checking those against themselves would prove nothing.
- **Production is refused, on import.** `app/seeds/__init__.py` calls the guard, so
  importing anything in the package under `APP_ENV=production` raises `SeedRefused`
  before a database is opened. The guard is not in the make target: a make target is not
  what runs inside a container.

Addresses are on `.example` — a TLD RFC 2606 reserves, so no registry can sell it and a
run pointed at the wrong database cannot mail a stranger. Not the `.test` of the same
sentence, because `EmailStr` at the HTTP boundary refuses that one and a seeded account
nobody can sign in as is not an account.

## Testing And Quality

The test suite uses pytest, pytest-asyncio, HTTPX ASGI transport, and in-memory
SQLite with `StaticPool` so each test gets a fast isolated database.

Test coverage is split by intent:

- API tests cover signup, login, refresh, logout, health, `/users/me`, and event
  delivery behavior.
- Unit tests cover domain value objects, event-sourced aggregate behavior,
  refresh-token rules, current-user resolution, event-store version conflicts,
  outbox delivery, and worker lifecycle.
- **Integration tests are the ones that need a real PostgreSQL** — see below.

Run tests:

```bash
poetry install
poetry run pytest
```

### Which suite owns a Postgres-only case

**`tests/integration/`, and nothing else.** If a guarantee cannot be expressed in
SQLite, its test goes there; if it can, it stays in `tests/unit/` or `tests/api/`
where it runs on every machine in milliseconds. The API suite is *not* moving to
Postgres — an in-memory database per test is what keeps two thousand of them
fast, and that is worth more than uniformity.

Three guarantees live there today: a reservation's overlapping-interval exclusion
(`EXCLUDE USING gist`, ADR-0035), the partial unique indexes that keep exactly one
open row per club series, and `FOR UPDATE SKIP LOCKED` outbox claiming.
The first has no SQLite equivalent at all; the second and third have shapes that
resemble one and behave differently under concurrency.

The reservation exclusion is where the split costs the most, and the line is worth
knowing before writing a Courts test. The **ordinary** path — scan the category's
courts, pick the first free one, write the claim — has no constraint in it and runs
on SQLite in milliseconds (`tests/unit/test_court_reservations.py`); so does the
*handling* of a refusal, driven by a stub that raises what the constraint raises.
What only PostgreSQL can produce is the refusal itself and the race that causes it,
and that is `tests/integration/test_reservation_exclusion.py` — including two real
`ClaimCourt` calls racing on one court, which is the acceptance criterion in its own
words. A useful thing that file measured: the loser gets `23P01` about three times in
four and `40P01` — a deadlock, because a GiST exclusion index inserts before it scans
— the rest of the time, and only one of the two is an `IntegrityError`.

The Clubs indexes are the one case where the *same* guarantee is asserted twice on
purpose, and the split is worth knowing. They are declared for both engines
(`postgresql_where` **and** `sqlite_where`), so `tests/unit/test_club_repository.py`
exercises them at millisecond cost on every `make check` — ADR-0077's own point, that
this is the cheap case of ADR-0035's pattern. What SQLite cannot speak for is the DDL
those declarations compile to *on PostgreSQL*, which is a different string built from a
different keyword argument: a typo in one is invisible on the other.
`tests/integration/test_club_series.py` creates the real tables from `Base.metadata` in a
throwaway schema and reads the predicate back out of `pg_indexes`.

Get a database and run them:

```bash
make up                       # Postgres 17 on localhost:5432
POSTGRES_TEST_URL=postgresql+asyncpg://raketa_user:raketa_pwd@localhost:5432/raketa \
  poetry run pytest tests/integration
```

Without one, those cases **skip on a laptop and fail in CI**. The requirement is
keyed on `CI` — which GitHub Actions sets — rather than on `POSTGRES_TEST_URL`,
which the workflow sets. Keying it on the URL would be self-defeating: deleting
the variable would delete the requirement to have it, and the pipeline would go
green having asserted nothing. `tests/integration/postgres.py` is where that rule
lives, and `tests/integration/test_harness_guard.py` checks it without needing a
database.

When you add a case there, add the constraint's *removal* to
`scripts/test-postgres-gates.sh` as well (`make test-pg-gates`). A constraint
test written against a schema that already satisfies it has never been seen to
fail, which is indistinguishable from not working; that script breaks each
constraint in turn and asserts the suite goes red. CI runs it. It mutates two
files: `tests/integration/ddl.py` for the throwaway shapes, and
`app/modules/clubs/infrastructure/sqlalchemy_club_models.py` for the real Clubs
declarations — where a mutation breaks the schema the application maps to rather
than a copy of it.

### The models and the migration say the same thing

Two files describe the Clubs tables: `Base.metadata`, which the whole fast suite is
tested against, and `migrations/versions/0007_clubs.py`, which is what a real database
gets. `tests/unit/test_clubs_migration.py` runs the migration's `upgrade()` against a
recorder standing in for `alembic.op` and compares the compiled PostgreSQL DDL, string
for string. An index present in one and absent from the other would be a guarantee that
holds in every test and nowhere else — worse than not having it, because the suite reads
as though it were enforced. It needs no database, so it runs on every `make check`.

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
