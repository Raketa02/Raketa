# Raketa Backend

FastAPI on Clean Architecture (hexagonal ports & adapters) with DDD aggregates, event
sourcing, and a transactional outbox. Python 3.11, Poetry.

> The `backend/` app of the monorepo — see the root [`CLAUDE.md`](../CLAUDE.md). Run every
> command from this directory. Never import from `../frontend_*`; a hook blocks writes there.
> Shared docs: [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## Commands

`make help` lists every target. The ones a session reaches for:

```bash
make test           # the suite in parallel (xdist, one worker per core). WORKERS=0 is serial,
                    # in collection order: the command for an order-dependent failure
make test-affected  # only the tests the change can affect (testmon) — inner loop, never the gate
make check          # lint + lint-imports + typecheck + test — the same gate CI runs
make lint           # ruff check .     make format → ruff format .     make typecheck → mypy
make test-gates     # prove the kernel/engines purity gates still fire (CI runs it)
make openapi        # emit openapi.{player,dev,club,public}.json — see The API contract
make gen-cohort     # rewrite the seed cohort's population (a diff is a fixture change)
make up / down      # dev stack: Postgres, API, MinIO, photo-review, Redis, Mailpit
                    # (every email lands in http://localhost:8025)
make migrate        # alembic upgrade head inside the API container
make seed           # deterministic dev accounts, the cohort and their history, through the
                    # use cases; needs the stack up (make seed-host on the host). The dev
                    # surface keeps its roster (/dev/roster) for the games test console (#590)
```

One test: `poetry run pytest tests/unit/test_user_domain.py::test_name`.

**Deployment is dormant** ([ADR-0010](../docs/adr/0010-local-first-development-aws-deferred.md)):
everything runs locally and the AWS ECS path is blocked for agent sessions. If a task seems
to call for deploying, it doesn't — say so.

## Safety — never without an explicit request

- Run deployment targets (`build-prod`, `ecr-*`, `ecs-*`). *(hook-enforced)*
- Create or edit a real `.env*`, secret, certificate or credential. Edit the
  `.env*.example` template instead. *(hook-enforced)*
- Edit an already-applied Alembic migration. Add a new one.
- Import FastAPI, SQLAlchemy, Pydantic or an external SDK into a `domain/` layer.
  *(lint-enforced, including through a module that imports one — #101)*
- Call an external side effect (email, webhook, provider API) directly from a use case —
  emit a domain event, or write the mail queue.
- Change public API behavior without calling it out in the plan first. **Three clients
  depend on this contract**, and none of them is in your session to be fixed.

## Architecture

Code lives under `app/`. Features are vertical slices in `app/modules/<context>/`, each
split into four layers:

- `domain/` — aggregates, value objects, domain events, errors, and the module's ports
  (`Protocol`s like `UserRepository`) in `domain/ports.py`. **Pure Python.**
- `application/` — use cases (one class with `async execute(...)`), commands. Depend on
  ports via constructor injection, never on concrete adapters.
- `infrastructure/` — SQLAlchemy ORM models + adapters implementing the ports.
- `presentation/` — FastAPI routes, request/response schemas, route dependencies.

Cross-cutting ports (unit of work, event publisher/store) live in `app/application/ports/`;
shared infra in `app/infrastructure/`; event-runtime assembly in `app/bootstrap/events.py`
and the register of scheduled jobs in `app/bootstrap/jobs.py`.

Rules to preserve:

- **Dependencies point inward:** presentation → application → domain. **Adapters are
  constructed in `app/bootstrap/composition.py` and nowhere else** — one plain function per
  port, so a seed run or a worker gets the wiring a request gets. The FastAPI dependency
  files declare *when* an adapter is built (`Annotated[Port, Depends(factory)]`), never
  what; `tests/unit/test_composition_root.py` fails if one imports an adapter.
- **A domain layer raises from `app/shared/domain/errors.py`** (pure stdlib: `AppError` and
  the five status classes). The envelope, handlers and OpenAPI schema live in
  `app/core/exception_handlers.py`. An error class keeps its own `status_code`, so a new
  subclass cannot be added without one.
- **State changes emit domain events**, appended through `DomainEventStore.append` and
  enqueued on the transactional outbox in the same transaction; handlers perform side
  effects after commit. The few event-free tables, and the ADR argument a new one needs,
  are in `.claude/rules/domain-events.md`.
- **A secret never enters the event store or the outbox** (ADR-0184 §4) — a link, code or
  ticket is a hashed row in `one_time_credentials`, issued through `OneTimeCredentials`.
- **Derived, never stored.** A standing, a room's membership and end, what a club can sell,
  who runs a group, a Player Score — each is folded from the record and the clock on every
  read. A stored copy is a second place for a fact to be true, and it is the one that gets
  believed.
- **Contexts meet through ports the consumer declares in its own words.** The adapter
  lives wherever the import arrow allows, `.importlinter` holds each arrow, and every
  outward port is contracted in a `tests/demands/` register.
- **Validate and normalize inside the value object**, not in the use case — see
  `app/modules/users/domain/value_objects.py`.
- **Seeds execute use cases, never SQL.** `app/seeds/` builds deterministic development
  data through the same use cases a request runs, wired from the composition root; a
  structural walk refuses a statement import or a `session.add` there, and the production
  refusal fires **on import** of `app/seeds/`.
- **Background work is an `asyncio` loop in the API process**
  ([ADR-0092](../docs/adr/0092-periodic-jobs-as-embedded-loops.md)) — `PeriodicJob`,
  registered in `app/bootstrap/jobs.py`. No cron, no lock: N API processes run a job N
  times, so a job must be safe beside itself. A window or threshold is domain; only the
  cadence is configuration.
- **The outside world sits behind ports** — photo storage, the photo-check sidecar (fails
  open), a room's live channel on Redis (fails soft), the mail queue and `Mailer`, `PaymentProvider`,
  `PushNotifications` (Expo; fails soft).
  `.importlinter` keeps each SDK out of every domain and application layer, including
  through the adapter, and `tests/conftest.py` overrides each port, so no test needs a
  container, Redis, Mailpit, Stripe or Expo.
- **Money is integer grosze.** Wall-clock hours are `Europe/Warsaw`, converted through the
  kernel's `slot_start` and nowhere else.
- **New routes mount on the surface whose client calls them**
  ([ADR-0187](../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §5), under `/api/v1`: `app/api/v1/player.py`, `club.py` (`/api/v1/club`) or `public.py`
  (`/api/v1/public`, no route takes a session). No path is in two documents; a route no
  client calls, like the payment webhook, is on no surface.
- **`app/kernel/` and `app/engines/` are pure** — `.importlinter`, a source walk and mypy
  strict fence them; an engine takes `now` as an input. The kernel is one import path
  (`app.kernel`). Raise a broken precondition through `invariant()`; return `Err(reason)`
  for a legitimate domain state — **Invariant vs Unavailability** in
  [`CONTEXT.md`](CONTEXT.md).

### Context notes

Each context's load-bearing decisions — the ones the code does not show — are a rule in
[`.claude/rules/`](.claude/rules/) that loads when you touch that context's files. **Before
changing code that calls into another context, read its rule.**

| Rule | Covers |
| --- | --- |
| `domain-events.md`, `migrations.md` | event registration and the event-free tables; Alembic |
| `seeds.md` | named accounts, the cohort, the played history as booked games, the screens it reads |
| `jobs.md` | every periodic job and what correctness depends on |
| `surfaces.md` | route surfaces, the dev console, the four OpenAPI documents |
| `kernel-and-engines.md` | the purity gates and the kernel's surface |
| `demands.md` | the demand registers and which one a new port belongs in |
| `player-profile-and-photos.md` | photo storage, the on-court check, profile reads and writes |
| `matchmaking.md` | what the new games kept (the balance forecast, the level window), the three outward demands, the candidate index until #580 |
| `games.md` | the booked game: opening, a seat left and taken, call-offs, results, the pairing |
| `conversations.md` | rooms, their end and the live channel |
| `player-score.md`, `sportsmanship.md`, `player-record.md` | the player record |
| `clubs.md`, `groups.md` | clubs, token audiences, club courts; groups and official groups |
| `payments.md`, `proposals.md` | the payments port and webhook; club money and payouts, once a day after the game; proposals and the group deck |
| `bookings.md` | the fill: all-or-nothing seat charges, the booking, its game and chat; On request — the club's answer; leaving, refunds, the cut-off and the record of who kept a booked game; rescues — seats to fill, the first join wins; the club's bookings — by day, Move, Cancel, Check in; no-shows on the Game; the club's Money page and its daily summary of new bookings |
| `accounts-and-mail.md` | the mail queue, administrators, signing out everywhere |
| `notifications.md` | who is told what and when: push through Expo, the recent list, the three choices, caps and bundling |

## The API contract

This app is the single source of truth for the API
([ADR-0006](../docs/adr/0006-backend-owns-api-contract.md)). `make openapi` writes one
document per surface — `openapi.player.json`, `openapi.club.json`, `openapi.public.json`,
and the dev console's `openapi.dev.json`, which has no client — and each client generates
its wire types from its own. When you change a request or response shape, run the
`api-contract-change` skill, commit the regenerated documents with whatever moved them, and
hand the clients a `make gen-api` at the root.

Prefer additive changes. Removing or renaming a field breaks a shipped client — a mobile
app whose old versions stay installed on real phones for months.

## Testing — test first

Write the failing test, make it pass, refactor. Every domain or use-case change ships with
tests.

- Tests live in `tests/`, files `test_*.py`. Async by default (`asyncio_mode = "auto"`) —
  no `@pytest.mark.asyncio`.
- `tests/unit/` — pure domain/application/adapter logic; mock ports with hand-written stub
  classes implementing the `Protocol` (see `tests/unit/test_resolve_current_user.py`).
- `tests/api/` — full HTTP flows via the `client` fixture (HTTPX ASGI + in-memory SQLite).
  Reuse `tests/conftest.py`'s fixtures rather than standing up new app/db instances:
  **`clock`** — check an expiry by moving time (`clock.move(timedelta(hours=1))`), never by
  waiting — and **`mailbox`**, which delivers through the real worker so a test reads the
  emails, links and codes a person would.
- `tests/demands/` — every outward port, parameterised over every adapter in its register
  ([ADR-0098](../docs/adr/0098-matcher-demands-as-executable-contracts.md)); a port with no
  row fails the suite. A new provider or consumer gets a new register.
- **Every test stays parallel-safe**
  ([ADR-0181](../docs/adr/0181-the-merge-gate-runs-every-test-and-choosing-tests-is-the-inner-loops-job.md)):
  the suite runs on xdist and nothing retries. Write under `tmp_path`; give a background
  job beside a request its own connection per session.
- **While iterating, `make test-affected`; at the end of every ticket, `make test`.**
  testmon cannot see tests that read the source tree as text (the kernel purity walk,
  `test_only_a_composition_root_imports_the_wall_clock`), JSON specs and fixtures, or code
  run in a subprocess (the seed, the two-hash-seed runs, mypy) — a domain module that
  imports the wall clock passes it green.

## Environment gotchas

- **`make up` needs no env file** — `docker-compose-local.yml` and `.env.docker` supply
  everything, and migrations run on container start.
- To run uvicorn **on the host**, `cp .env.example .env` — `config.py` loads `.env` and
  nothing else. Required: `WRITER_DB_URL`, `JWT_SECRET_KEY`, `DB_SSL_MODE`.
- **`APP_ENV`** is a strict enum over `local | development | staging | production`; only
  `local` runs, and the others refuse to start without their settings (the README's
  refusal table). **The environment may select configuration; it may never select
  behaviour a domain test could observe.**
- Tests set their own env in `conftest.py`; there is no `test` environment. A test
  asserting on log records sets its level through `caplog` — never `-p no:logging`, which
  removes the fixture.
- The outbox worker and every scheduled job have their own `*_ENABLED` toggle in
  `app/core/config.py`, and **every job's first run is at startup**, not after its first
  interval.

## Git & domain language

Conventional Commits, scoped `api` or the module: `feat(rating): revise a submitted
answer`. Run `make check` before pushing; CI runs the same gate for `backend/**` changes.

The shared glossary is [`../CONTEXT.md`](../CONTEXT.md); backend-only technical vocabulary
is in [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally. Before writing a new
context, resolve its terms into the glossary and record the aggregate shape in an ADR,
including whether it is event-sourced or persisted-with-events.
