# Raketa Backend

FastAPI on Clean Architecture (hexagonal ports & adapters) with DDD aggregates, event
sourcing, and a transactional outbox. Python 3.11, Poetry.

> The `backend/` app of a three-app monorepo — see the root [`CLAUDE.md`](../CLAUDE.md).
> Run every command from this directory. Never import from `../frontend_*`; a hook blocks
> writes there. Shared docs: [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## Commands

Run via the Makefile from `backend/`:

```bash
make test        # poetry run pytest tests -q
make lint        # ruff check .          make format → ruff format .
make typecheck   # mypy app
make check       # lint + lint-imports + typecheck + test — the same gate CI runs
make test-gates  # prove the kernel/engines purity gates still fire (CI runs it)
make test-pg-gates # prove the Postgres constraint gates still fire (needs a DB; CI runs it)
make openapi     # emit openapi.player.json + openapi.club.json, one per client
make up / down   # dev stack (Postgres 17 + API + Redis); make logs, make shell
make migrate     # alembic upgrade head inside the API container
make seed        # deterministic dev accounts (make seed-host to run it on the host)
```

One test: `poetry run pytest tests/unit/test_user_domain.py::test_name`.

**Deployment is dormant.** Everything runs locally; there is no deployed environment. The
AWS ECS path is kept intact but unused and blocked for agent sessions
([ADR-0010](../docs/adr/0010-local-first-development-aws-deferred.md)). If a task seems to
call for deploying, it doesn't — say so.

## Safety — never without an explicit request

- Run deployment targets (`build-prod`, `ecr-*`, `ecs-*`). *(hook-enforced)*
- Create or edit a real `.env*`, secret, certificate or credential. Edit the
  `.env*.example` template instead. *(hook-enforced)*
- Edit an already-applied Alembic migration. Add a new one.
- Import FastAPI, SQLAlchemy, Pydantic or an external SDK into a `domain/` layer.
  *(the first four are lint-enforced, including through a module that imports one —
  which is how it was broken for months, see #101)*
- Call an external side effect (email, webhook, provider API) directly from a use case —
  emit a domain event instead.
- Change public API behavior without calling it out in the plan first. **Two client apps
  depend on this contract**, and neither is in your session to be fixed.

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
shared infra in `app/infrastructure/`; event-runtime assembly in `app/bootstrap/events.py`.

Rules to preserve:

- **Dependencies point inward:** presentation → application → domain. **Adapters are
  constructed in `app/bootstrap/composition.py` and nowhere else** — one plain function
  per port, taking a session and the settings, with no web framework in it, so a seed
  run or a worker gets the wiring a request gets instead of a copy of it.
  `app/api/dependencies.py` and each module's `presentation/dependencies.py` declare
  *when* an adapter is built and how long it lives (`Annotated[Port, Depends(factory)]`),
  never what. `tests/unit/test_composition_root.py` walks those files and fails if one
  imports an adapter.
- **A domain layer raises from `app/shared/domain/errors.py`**, which is pure stdlib.
  The error *taxonomy* — `AppError` and the five status classes — lives there; the
  envelope, the handlers and the OpenAPI schema live in `app/core/exception_handlers.py`,
  which imports it. They shared a file until #101, and that made every module's
  `domain/errors.py` import FastAPI transitively. An error class keeps its own
  `status_code`, deliberately: a status held in a separate registry is one a new
  subclass can be added without, and the miss is a 500 in production rather than a red
  test.
- **State changes emit domain events.** An event-sourced aggregate persists them through
  `DomainEventStore.append`; a **record** aggregate has no stream and enqueues them straight
  onto the transactional outbox. Either way it happens **in the same transaction as the state
  change**, and handlers perform side effects after commit.
- **Seeds execute use cases, never SQL.** `app/seeds/` creates deterministic development
  accounts through the same use cases a request runs, wired from the composition root, so
  a seeded aggregate has the event stream and the outbox rows a real one has. A structural
  walk refuses a statement import or a `session.add` in that package. The production
  refusal is checked **on import** of `app/seeds/`, not in `make seed` — a make target is
  not what runs inside a container. See the README's *Seed Data*.
- **A seed account is named for a state, and the name is checked.** The catalog is a list
  of edges — nothing yet, one open run, one abandoned, a rating at the edge of its band —
  and a rated scenario carries the band it promises, checked against the stored rating on
  every run. The same rule now covers clubs, court claims and matches, each named for its own
  edge — and a **seeded match names the `Situation` it resolves to**, checked by the kernel,
  which is the strongest form of the rule available anywhere in the catalog. Seed only what is
  **decided**: nothing seeds a match-held reservation, because *when* a court is held is the
  hold ladder's call and that ladder is not written yet.
- **New routes mount under `app/api/v1/router.py`;** keep the `/api/v1` prefix.
- **Validate and normalize inside the value object**, not in the use case — see
  `app/modules/users/domain/value_objects.py`.
- **`app/kernel/` and `app/engines/` are pure and fenced by three gates**, because no one
  of them covers all of it ([ADR-0015](../docs/adr/0015-engines-as-a-pure-versioned-layer.md),
  [ADR-0022](../docs/adr/0022-kernel-negative-space-and-constant-homes.md)): `.importlinter`
  forbids `app.shared`, `random`, `uuid`, `secrets` and `time` to both — and `datetime` to
  the engines, whose one legitimate home is the kernel; `tests/unit/test_kernel_purity.py`
  walks the source for the clock reads module granularity cannot see; and `pyproject.toml`
  scopes **mypy strict** to those two packages. An engine takes `now` as an input.
- **One ladder resolves a match, and every other state vocabulary projects off it.**
  `kernel.situation(record, viewer | None, now)` is the single resolver over 36 names, and
  the order of its rungs *is* the specification. `kernel.next_wake_at()` lives beside it and
  reads the same boundaries, so a threshold cannot exist in the ladder and be missing from
  the schedule. A consumer that needs a coarser vocabulary writes a **total table off
  `Situation`**, asserted exhaustive at module load — never a second ladder over the record
  ([ADR-0040](../docs/adr/0040-one-ladder-resolves-a-situation.md)). `MatchPhase` in
  `app/engines/matchmaking.py` is the first and, today, the only one.
- **History belongs to named facts, never to the aggregate.** A club is a *record*, not an
  event-sourced stream, and three of its facts carry history as an **effective-dated series**
  — policy, payout destination, court catalogue
  ([ADR-0077](../docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md)). A change **closes the
  row in force and opens a new one**, in one operation, and is never an update in place or a
  row beside an audit table. At most one open row per series, guarded twice on purpose: a
  partial unique index stops a second one reaching disk, and the `Series` type stops one being
  constructed. A series is rebuilt from disk by **one** ordering function — `valid_from` alone
  is ambiguous the moment two rows share an instant, and an ambiguous ORDER BY reads as a
  broken database rather than as a bug.
- **A match is a record with a version, and every change announces itself by name.** Matches
  is the one racket-sport context that is **not** event-sourced
  ([ADR-0034](../docs/adr/0034-matches-is-a-record-and-keeps-no-history.md)): the concurrency
  guard is a `version` column compared in the UPDATE that bumps it, and the history is the
  **outbox trail** rather than a stream. That trades one obligation for another and the
  obligation is not optional — *every change a support agent would one day need to explain to
  a player is its own named event*, never a generic *match updated*. Nothing mechanical
  catches an event published too coarsely, so `tests/unit/test_match_events.py` walks the
  aggregate and reddens when a mutating method announces nothing. **Every stored fact declares
  one of five kinds** — Constitutive, Occupancy, Allocation, Crossing, Declaration — and *a
  reader cannot derive this* has to be true of it: `filled`, the situation, whether a court is
  held and which court it is are all computed or answered elsewhere. The club's four
  hold-policy fields are **copied at posting** and honoured as booked (ADR-0077), which is what
  lets `Match.as_record()` resolve a situation with **no other read**.
- **A court is claimed by a reservation, and the database is what refuses the second one.**
  A reservation is one court and one **time range**, and two may never overlap on one court —
  enforced by `EXCLUDE USING gist` over `tstzrange(claimed_from, claimed_to, '[)')`, partial
  over the live rows, never by read ordering
  ([ADR-0035](../docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md)). A caller
  asks for **a category and a window**, never for a court. Losing inventory is therefore a
  **query result and never a race outcome**: a refused claim is re-asked with that court
  removed, and only *nothing was free* reaches a player. The refusal arrives as one of two
  SQLSTATEs — `23P01` and, when the writers are exactly simultaneous, `40P01` — so the adapter
  catches `DBAPIError` rather than `IntegrityError`. **Availability is a projection over
  reservations and no count is stored anywhere.** A reservation is **released, never
  deleted**, because a court's booking history is a query over reservations. SQLite has none
  of this: the ordinary path is tested fast and the race lives in `tests/integration/`.
- **Now is a composition, not a context, and the phone holds no rules.**
  `app/modules/now/` owns no aggregate and writes nothing; what it owns is the shape of the
  answer ([ADR-0070](../docs/adr/0070-now-is-three-regions-and-a-card-has-two-halves.md)).
  One request returns **three ordered regions**, and the asymmetry between them is
  load-bearing: a **region** with nothing in it is present and empty, a **shelf** with
  nothing in it is absent. A card is **two nested halves** — a spine every phone draws and a
  situation half only a current one does — so an unknown situation costs a sentence and never
  a card. Everything a client could be asked to *derive* is composed here instead: the act
  code, the one clock slot, the emphasis flag, the fit badge already clamped. **The tag, the
  tone and the alert cross no wire at all** — all three are total functions of the situation
  and belong to the client's own table, and a flag would let the server and the phone
  disagree about whether a card is urgent. Every code crosses as an **OpenAPI enum**: a bare
  string degrades the client's exhaustive `Record` into an index signature that never fires,
  which is the one failure mode no typecheck can reach afterwards. And **no sentence is
  composed here** — an AST walk over the package reddens on any string literal that could be
  copy, with a negative control proving it can tell one from a code.
- **The kernel is one import path.** `app.kernel` re-exports its whole public API through
  an explicit `__all__`, and nothing outside the package — tests included — imports a
  submodule, so a definition can move between kernel files without touching a caller
  (`tests/unit/test_kernel_surface.py`). Refuse a broken precondition by raising through
  `invariant()`; refuse a legitimate domain state by returning an `Err(reason)` — see
  **Invariant vs Unavailability** in [`CONTEXT.md`](CONTEXT.md). Because `@final` and
  branded types erase at runtime, the constraints the kernel claims are asserted by
  running mypy over `tests/typecheck/kernel_misuse.py`; **each new branded module adds
  its deliberately-wrong call sites there**, or nothing checks that its brand binds.

## The API contract

This app is the single source of truth for the API
([ADR-0006](../docs/adr/0006-backend-owns-api-contract.md)). The contract is emitted as two
documents — `openapi.player.json` and `openapi.club.json` — and each client generates its
TypeScript wire types from its own (`make openapi`), so a response-shape change is
load-bearing outside this directory. When you change one, run the `api-contract-change` skill.

Prefer additive changes. Removing or renaming a field breaks two shipped clients, one of
which is a mobile app whose old versions stay installed on real phones for months.

## Testing — test first

Write the failing test, make it pass, refactor. Every domain or use-case change ships with
tests.

- Tests live in `tests/`, not beside source. Files are `test_*.py`.
- `tests/unit/` — pure domain/application/adapter logic; mock ports with hand-written stub
  classes implementing the `Protocol` (see `tests/unit/test_resolve_current_user.py`).
- `tests/api/` — full HTTP flows via the `client` fixture (HTTPX ASGI + in-memory SQLite).
  Reuse fixtures from `tests/conftest.py` rather than standing up new app/db instances.
- `tests/integration/` — **and only here** — cases needing a real Postgres, because the
  guarantee has no SQLite equivalent: the interval-exclusion constraint, the partial unique
  index on a versioned series' open row, `FOR UPDATE SKIP LOCKED`. Take `pg_engine` from
  `tests/integration/conftest.py`. They **skip on a laptop and fail in CI**, keyed on `CI`
  rather than on the URL variable the workflow sets — a requirement the workflow can switch
  off is not one. Never `pytest.skip` on a missing database without that branch. Adding a
  case means adding its constraint's removal to `scripts/test-postgres-gates.sh`, or nothing
  has ever seen that assertion fail. See the README's *Which suite owns a Postgres-only case*.
- Async by default (`asyncio_mode = "auto"`) — no `@pytest.mark.asyncio`.

## Environment gotchas

- **`make up` needs no env file** — `docker-compose-local.yml` supplies the DB URLs and
  `.env.docker` the rest, and migrations run on container start. This is the normal path.
- To run uvicorn **on the host**, `cp .env.example .env`. The filename matters: `config.py`
  loads `.env` (`SettingsConfigDict(env_file=".env")`), so a file named `.env.local` is
  read by nothing. Required: `WRITER_DB_URL`, `JWT_SECRET_KEY`, `DB_SSL_MODE`.
- **`APP_ENV` is a strict enum** over `local | development | staging | production`, the
  same four names both clients use. Only `local` runs; selecting `development` or
  `staging` without `APP_HOST` and `WRITER_DB_URL` refuses to start, and so do five other
  dangerous configurations (see the README's refusal table). It also supplies the defaults
  for `DEBUG`, `LOG_LEVEL` and `LOG_JSON`, each still overridable. **The environment may
  select configuration; it may never select behaviour a domain test could observe.**
- Tests set their own env in `conftest.py` (SQLite, test JWT secret, `APP_ENV=local`) —
  no `.env` needed. There is no `test` environment: a test run happens on somebody's
  laptop or a CI runner, and both are `local`.
- The embedded event-delivery worker polls the outbox on startup; toggle with
  `EVENT_DELIVERY_WORKER_ENABLED`.

## Git & domain language

Conventional Commits, scoped `api` or the module: `feat(bookings): reject overlapping
slots`. Run `make check` before pushing; CI runs the same gate for `backend/**` changes.

The shared glossary is [`../CONTEXT.md`](../CONTEXT.md); backend-only technical vocabulary
is in [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally. **Money is listed but
not yet modeled** — before writing code in it, resolve its terms into the glossary and record
the aggregate shape in an ADR, including whether it is event-sourced or persisted-with-events.
[ADR-0055](../docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md) has already
answered that one: the ledger is event-sourced, and it is the first racket-sport context to go
that way. Clubs, Courts, Bookings and Matches are modeled and all four are **records with a
version**, decided by
[ADR-0077](../docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md),
[ADR-0035](../docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md) and
[ADR-0034](../docs/adr/0034-matches-is-a-record-and-keeps-no-history.md) — which is what a
genuinely per-context choice looks like once five contexts have made it.
