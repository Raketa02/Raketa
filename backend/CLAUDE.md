# Raketa Backend

FastAPI on Clean Architecture (hexagonal ports & adapters) with DDD aggregates, event
sourcing, and a transactional outbox. Python 3.11, Poetry.

> The `backend/` app of a two-app monorepo — see the root [`CLAUDE.md`](../CLAUDE.md).
> Run every command from this directory. Never import from `../frontend_*`; a hook blocks
> writes there. Shared docs: [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## Commands

Run via the Makefile from `backend/`:

```bash
make test        # poetry run pytest tests -q
make lint        # ruff check .          make format → ruff format .
make typecheck   # mypy app scripts
make check       # lint + lint-imports + typecheck + test — the same gate CI runs
make test-gates  # prove the kernel/engines purity gates still fire (CI runs it)
make openapi     # emit openapi.player.json — the contract the client generates from
make gen-walkthroughs  # rewrite the matchmaking golden files (a diff is a design change)
make up / down   # dev stack (Postgres + API + MinIO + photo-review + Redis); logs, shell
make migrate     # alembic upgrade head inside the API container
make seed        # deterministic dev accounts (make seed-host to run it on the host)
make rebuild-candidate-index  # fold the log back into the index (…-host on the host)
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
- Change public API behavior without calling it out in the plan first. **The player app
  depends on this contract**, and it is not in your session to be fixed.

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
- **State changes emit domain events.** Use cases persist them through
  `DomainEventStore.append` and enqueue them on the transactional outbox in the same
  transaction; handlers perform side effects after commit. **One deliberate exception,
  and it is the matchmaking module's four durable ledgers** — the `search` record,
  `interest`, the **pass** record and the **prompt decline** (`the-engine.md` §12:
  *nothing here is event-sourced*, and an interest is *durable without being an aggregate
  with a life story*). All four are small facts with no life story, and **nothing
  *subscribes* to one being written**: a lift is a read on the next search, the
  suppression a pass writes is a cache its use case fills after the commit rather than a
  subscriber, and a decline is read by one filter on the next search. The one thing a
  write here does cause is a **call, never a subscription** — a second *Let's play*
  facing the first opens a challenge **inline, in the same transaction** through a port
  `challenges` signs (#251), because *that player has left the deck for good* is a
  promise that must not wait for a poller. The exemption is about the interest row
  needing no event of its own, and that is unchanged.
  The authority naming all four is `the-engine.md` §12;
  ADR-0128 decides what a pass *is* and says nothing about event sourcing, and ADR-0094
  says of the decline in its own words that *declining a prompt is not a domain fact and
  earns no event* — its amendment moved the suppression out of Redis and kept that
  sentence literally. A new context does **not** inherit this — it needs the same argument made in
  an ADR.
- **Seeds execute use cases, never SQL.** `app/seeds/` creates deterministic development
  accounts through the same use cases a request runs, wired from the composition root, so
  a seeded aggregate has the event stream and the outbox rows a real one has. A structural
  walk refuses a statement import or a `session.add` in that package. The production
  refusal is checked **on import** of `app/seeds/`, not in `make seed` — a make target is
  not what runs inside a container. See the README's *Seed Data*.
- **A seed account is named for a state, and the name is checked.** The catalog is a list
  of edges — nothing yet, one open run, one abandoned, a rating at the edge of its band —
  and a rated scenario carries the band it promises, checked against the stored rating on
  every run. Seed only what is **modeled**: Players, onboarding assessments and Skill
  ratings have aggregates; nothing else does, so nothing else gets a scenario.
- **Photo bytes live behind `PhotoStorage`, and the re-encode behind
  `ImageTranscoder`** ([ADR-0091](../docs/adr/0091-photo-storage-behind-a-port.md)).
  One S3-compatible adapter serves MinIO locally and S3 deployed — same class, different
  endpoint — so the deployed answer is a setting rather than a migration of live user
  data. Every port method takes a `PhotoRef` (owner **and** photo id), so ownership is the
  port's contract rather than each caller's memory. **Every upload is re-encoded to JPEG**,
  which is how EXIF — and the GPS in it — is stripped reliably rather than best-effort.
  `.importlinter` forbids `PIL`, `pillow_heif`, `aioboto3`, `boto3`, `botocore` and
  `aiohttp` to every domain and application layer, **including through the adapter**,
  because a use case that constructs the transcoder itself has bypassed the port just as
  completely.
- **The on-court photo check runs in a sidecar, and the rule it applies does not**
  ([ADR-0129](../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md)).
  `ClipSidecarPhotoReview` is an `aiohttp` client; `docker/photo-review/` is a CLIP model
  behind one HTTP route that answers raw cosine similarities and holds **no policy**. The
  prompt set, the temperature and the threshold live in
  `player_profile/domain/photos.py` beside the size caps — behaviour a domain test can
  observe, never configuration — and `PHOTO_REVIEW_ENDPOINT_URL` /
  `PHOTO_REVIEW_TIMEOUT_SECONDS` cannot change a verdict. It **soft-warns and fails
  open**: a flagged photo is stored, and an unreachable sidecar yields `allowed` with a
  note saying so, because an outage is not a conclusion about an image. Every verdict
  records the similarity vector it was taken from, which is what makes today's
  placeholder threshold safe. **No test needs the container** — `tests/conftest.py`
  overrides the port, as it does the store.
  **The verdict now crosses the wire, and only on the upload**
  ([ADR-0133](../docs/adr/0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)).
  `PhotoResponse.review` is an optional code — `allowed` / `flagged`, never a sentence and
  **never the note**, whose model, fingerprint, confidence and raw vector are evidence for
  re-deriving the threshold and are not about the player. `GET /photos/{id}` answers `null`
  there, which is deliberately **not** `allowed`: a warning belongs to the moment a player
  chose a photograph, and the read would pay a metadata request per tile for a fact no
  client asks it for. That ended ADR-0129's measure-only posture, which was a property of
  the tree rather than a flag — so there is nothing to toggle and the fail-open trade was
  re-examined rather than inherited: an outage now costs the player *silence*, not a
  sentence about our infrastructure dressed up as one about their photo.
- **Background work is an `asyncio` loop in the API process, and a job must be safe to
  run beside itself** ([ADR-0092](../docs/adr/0092-periodic-jobs-as-embedded-loops.md)).
  `PeriodicJob` (`app/infrastructure/jobs/`) is the whole mechanism — the outbox worker
  is written on it too — and **`app/bootstrap/jobs.py` is where the next job goes**,
  built from the composition root so it reaches the same bucket and event store a
  request does. There is no cron, no beat process and no lock: with N API processes a
  job runs N times per interval, so a job that cannot tolerate that needs a different
  mechanism and its own ADR. Nine jobs today — the uncommitted-photo sweep, whose
  **retention window is domain and whose cadence is configuration** (those two must not
  swap places), the candidate index's two loops below, the **exposure roll**, the
  first job here that takes no database session at all, the two **prompt loops**
  (intent drift, availability staleness), which write no value anywhere — each raises a
  question into the prompt ledger and stops, and every threshold behind them is domain
  in `matchmaking/domain/prompts.py` while only the cadences are settings — and the
  **interest expiry loop**, the only one that deletes anything. Turning that one off
  changes no rule a domain test could observe (every ledger read is bounded by `now`,
  so a lapsed yes lifts nobody whether or not it has been swept); what it buys is a
  table the size of what is live, and the one figure a lapsed row could ever be asked
  for — *yeses that expired having never lifted anybody*, `INTEREST_TTL`'s only day-one
  falsifier, which cannot be computed once the rows are gone. The eighth is the
  **scale-pressure probe** — the only job whose work *is* its own scheduling: it measures
  how late the loop woke it, and closes the fifteen-minute window
  [`scale-posture.md`](../docs/specs/matchmaking/scale-posture.md) §4 states trigger 1
  over. It reads this process's own counters and writes nothing anywhere, so it needs no
  session and no store, and *N processes, N runs* is what the trigger wants — it is
  stated **per worker**. The ninth is the **photo re-review backfill**
  ([ADR-0132](../docs/adr/0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md)),
  the second job that takes no session — its whole input and output are the object store.
  Every photo uploaded before ADR-0129's checker landed carries `review: allowed` written
  by a pass-through that looked at nothing, and **the note is what tells the three
  populations apart**: no `review-note` key is the pass-through era, `unavailable=…` is a
  photo that arrived while the sidecar was down and that population keeps growing, and a
  full `clip;m=…;p=…;c=…;s=…` was really scored. The job fixes the first two and
  **counts the third without touching it** — reviewed against captions that have since
  moved is a judgement nobody has made, and `PROMPT_SET_FINGERPRINT` is what makes it
  answerable. Four rules, each a way it could go wrong invisibly: it re-reviews
  **through the `PhotoReview` port**, so there is one copy of `verdict_from_similarities`
  and a batch cannot disagree with the upload path about one image; it **never rewrites a
  note that is already right**, because an S3 metadata update is a copy of the object onto
  itself; a run against a sidecar it cannot **reach** stops rather than stamping a fresh
  `unavailable` over an old one, while a refusal about one image is counted and stepped
  over — ending the run on one would stall the job at that photo for ever
  (`PhotoReviewUnavailability.is_about_the_reviewer` is the split); and a note it cannot
  parse reads as *nobody looked* — the deliberate inverse of the sweep, whose action is a delete. The budget, the
  pause and the cadence are settings and none of them selects which photos are chosen.
- **The candidate index tails the log; the outbox delivers side effects**
  ([ADR-0110](../docs/adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md),
  [ADR-0111](../docs/adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md),
  [ADR-0112](../docs/adr/0112-the-snapshot-is-a-per-partition-container-bound-once.md)).
  The platform's first read model, and **the same domain event now has two consumers with
  different guarantees** — hold both in your head. `CandidateIndexTail` reads `event_store`
  by `sequence_no`, takes the one cursor row `FOR UPDATE`, and applies **only the contiguous
  prefix**, because a position is assigned at `INSERT` and not at `COMMIT`. A hole is stepped
  over only once the snapshot horizon proves it permanent — **and never on SQLite**, which has
  neither a horizon nor a concurrent appender, so that path is exercised against Postgres or
  not at all. `DatabaseCandidateSource` holds one immutable container per partition per
  process, refreshes it by copying row references, and calls `gc.freeze()` after every load and
  after every refresh that decoded a row — **not** after one that decoded none, because the
  freeze promotes everything tracked and would otherwise leak whatever was in flight, every two
  seconds, for ever.
  Three rules that outlive the code: **the index holds only facts a player changes about
  themselves** (every live-truth fact travels in the search context instead — a column for one
  would make staleness cost safety); **the partition is derived and there is no shard-key
  field**; and **`rebuild == tail`**, which is why every stamp is the moving event's own
  sequence number and never a batch boundary. Repair is `make rebuild-candidate-index` and
  **there is no admin route** — a walk over `app/api/` and every `presentation/` fails the
  build if one appears. The staleness **ladder** is domain
  (`matchmaking/domain/index_staleness.py`); only the two cadences are configuration.
- **The three lossy ledgers live in Redis, and the gate is the cache — the evidence is
  the row** ([ADR-0093](../docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md),
  `the-engine.md` §12). Exposure and suppression are ports in
  `matchmaking/domain/ledgers.py` with TTLs, and the **prompt ledger** — where the two
  loops leave a standing question — is declared in `matchmaking/domain/prompts.py` and
  registered in the same posture table; everything that must survive is a durable row
  elsewhere, and a test at each port says so. **All three fail soft**, which is the opposite of
  the block gate beside them and is deliberate: applying ADR-0095's *a gate that cannot be
  evaluated excludes* to a courtesy would **empty the deck rather than protect anybody**.
  The posture is a wrapper applied in the composition root, so **no unwrapped adapter is
  ever handed out** and `.importlinter` keeps `redis` — and the adapter over it — out of
  every domain and application layer. Neither TTL is configuration: `PASS_SUPPRESS` is in
  the released ruleset and `EXPOSURE_RETENTION_WEEKS` in the domain, and only `REDIS_URL`
  and the loops' cadences are settings. **No test needs Redis** — all three ports have an
  in-memory implementation that `tests/conftest.py` wires for the whole HTTP suite, and the
  Redis adapters are held to the same contract suite against an in-process stand-in.
- **Interest is durable, in the module, and it is the only lift that admits**
  ([ADR-0127](../docs/adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md),
  [ADR-0109](../docs/adr/0109-a-read-back-names-what-it-withholds.md)). `POST/GET
  /api/v1/interest` and the `interest` table are the first durable ledger in this module
  — a row rather than a Redis key, because a person reached out to a person and that is
  the one thing here a human would miss. Four rules shape it, and each is structural
  rather than remembered. **There is no method on `InterestLedger` that answers *who has
  said yes to me***: the lift's read takes the candidate population it may answer about,
  so an inbox is not a query the port can express. **The origin key is two columns on the
  row** — an interest citing a search that is unknown, foreign or that never showed that
  person is refused, never linked as null, and the position is read off the record rather
  than sent. **Nothing decays**: `INTEREST_TTL` is flat then absent, `expires_at` is dated
  at birth, and at `OUTSTANDING_INTEREST_CAP` the write is **refused** rather than
  shortening a yes already sent. And it is the **one** thing that may admit a candidate
  below `QUALITY_FLOOR` — `admits(..., interest_received=True)` in `engines/matchfit/v1/
  floor.py`, with the reason printed; the newcomer and zero-exposure lifts reorder and
  never admit. All three numbers are ruleset rows and only the sweep's cadence is a
  setting.
- **The deck reads a declaration, and a pass is a statement about my deck**
  ([ADR-0128](../docs/adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md),
  `the-two-contracts.md` §6). `POST /api/v1/deck` takes **the sport and the week this one
  deal runs on** and creates a search: there is no mode on the wire in either direction,
  because the deck resolves the weight vector backend-side from the viewer's declared Play
  intent — `NO_PREFERENCE → fun`, never a third vector — and `search.intent_read` records
  **the declaration as it stood**, so a later change to the mapping does not rewrite
  history. Its order is its whole variety (three bands, then `PASS_SUPPRESS`); the
  **relaxation ladder does not reach it** — the week is the only ask beside the sport, and
  it is an ask like the shortlist's: it writes nothing, and the deal comes back carrying
  `KEEP_THESE_TIMES`, which is the offer to save it; and a spent deal deals again — a new
  `search_id`, the same exclusions plus everybody dealt within `DEALT_MEMORY`, so only a
  *fresh* deal that came back empty is the honest empty state.
  `POST /api/v1/passes` is **write-only and answers `204`**: no route returns a pass, to
  anyone, in any shape, and `PASS_SUPPRESS` crosses the wire in **no shape at all**. It
  has three boundaries, all the opposite of a block's — deck only, one-directional, never
  escalating — and the split that makes them enforceable is **the gate is the cache; the
  evidence is the row**: the durable `player_pass` row is written and committed first, and
  the 30-day Redis suppression derived from it is written after and **fails soft**, so an
  outage repeats a card and never empties a deal. Two telemetry columns exist for the one
  falsifier `PASS_SUPPRESS` has — `search.n_excluded_by_suppression` and
  `search_candidate.suppression_lapsed`, both **deck deals only**, both check-constrained.
  **`application/search_workbench.py` is the seam the two surfaces share** — read the
  searcher, bind the snapshot and every live gate fact, attach the card and the at-stake
  block, record, commit, note exposure — so a shortlist and a deal cannot come to two
  answers about which reads fail closed. What stays in each use case is what that surface
  decides: the mode, the exclusions, the order, the ladder, the prompts.
- **A returned search is a recorded search**
  ([ADR-0104](../docs/adr/0104-the-search-record-is-the-answer-and-never-expires.md)).
  `POST /api/v1/searches` is the platform's first matchmaking route, and the rule that
  shapes it is that the `search` row is written **in the request's own transaction and
  committed before the response returns** — if that fails, the search fails, because the
  `search_id` *is* the answer's identity. Every fact on it is search-time and **there is
  no backfill**, which is why the two tables are wide on day one and why
  `their_slot_count`, `days_away` and the raw `liveness_signals` are recorded and read by
  nothing: *a strike that is not recorded becomes irreversible by accident.* Nothing
  deletes a row; erasure will be the only path that ever does.
  Three seams are worth holding in your head, because a change lands in exactly one of
  them. **`domain/shortlist.py` is pure** — a bound `SearchContext` in, an ordered answer
  out, no I/O — which is what lets the three walkthroughs be golden files
  (`make gen-walkthroughs`; **a diff there is a design change and must be argued for in
  the pull request**). **`domain/fence.py` is the crossing**: everything the scorer will
  ever see is built there, so a field that must not reach it has one place to be refused.
  And **`application/run_shortlist_search.py` owns the order** — read the searcher live,
  bind one snapshot and every live gate fact, run the pipeline, record and commit, then
  write exposure *after* the commit. **Never a fallback list:** when the engine raises the
  feature is down, and there is deliberately nothing to catch it with.
  **`GET /api/v1/searches/{id}` reads one back, and it is not a cache**
  ([ADR-0109](../docs/adr/0109-a-read-back-names-what-it-withholds.md),
  [ADR-0130](../docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)). The
  record is immutable and the four fail-closed gates — block, hold, account state, mutual
  gender — are re-evaluated live, so a row they no longer admit **keeps its place and states
  that it is withheld** while naming no gate and carrying no person. That is why both routes
  render `SearchRecord` through one function and why the row records the card, the concerns,
  the whole-kilometre distance and the at-stake block: what a read-back cannot reproduce off
  the row, it would have to re-read from sources that have moved on.
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
([ADR-0006](../docs/adr/0006-backend-owns-api-contract.md)). The contract is emitted as
`openapi.player.json`, and the client generates its TypeScript wire types from it
(`make openapi`), so a response-shape change is load-bearing outside this directory. When
you change it, run the `api-contract-change` skill.

Prefer additive changes. Removing or renaming a field breaks a shipped client — a mobile
app whose old versions stay installed on real phones for months.

## Testing — test first

Write the failing test, make it pass, refactor. Every domain or use-case change ships with
tests.

- Tests live in `tests/`, not beside source. Files are `test_*.py`.
- `tests/unit/` — pure domain/application/adapter logic; mock ports with hand-written stub
  classes implementing the `Protocol` (see `tests/unit/test_resolve_current_user.py`).
- `tests/api/` — full HTTP flows via the `client` fixture (HTTPX ASGI + in-memory SQLite).
  Reuse fixtures from `tests/conftest.py` rather than standing up new app/db instances.
- `tests/demands/` — the matcher's **outward demands**, parameterised over every
  implementation registered in `app/bootstrap/matcher_demands.py`
  ([ADR-0098](../docs/adr/0098-matcher-demands-as-executable-contracts.md)). Adding a row
  to the register enrols an adapter; a port with no row fails the suite. Not named
  *contract* — that word already means `openapi.player.json` drift here.
- Async by default (`asyncio_mode = "auto"`) — no `@pytest.mark.asyncio`.

## Environment gotchas

- **`make up` needs no env file** — `docker-compose-local.yml` supplies the DB URLs and
  `.env.docker` the rest, and migrations run on container start. This is the normal path.
- To run uvicorn **on the host**, `cp .env.example .env`. The filename matters: `config.py`
  loads `.env` (`SettingsConfigDict(env_file=".env")`), so a file named `.env.local` is
  read by nothing. Required: `WRITER_DB_URL`, `JWT_SECRET_KEY`, `DB_SSL_MODE`.
- **`APP_ENV` is a strict enum** over `local | development | staging | production`, the
  same four names the client uses. Only `local` runs; selecting `development` or
  `staging` without `APP_HOST` and `WRITER_DB_URL` refuses to start, and so do five other
  dangerous configurations (see the README's refusal table). It also supplies the defaults
  for `DEBUG`, `LOG_LEVEL` and `LOG_JSON`, each still overridable. **The environment may
  select configuration; it may never select behaviour a domain test could observe.**
- Tests set their own env in `conftest.py` (SQLite, test JWT secret, `APP_ENV=local`) —
  no `.env` needed. There is no `test` environment: a test run happens on somebody's
  laptop or a CI runner, and both are `local`.
- The embedded event-delivery worker polls the outbox on startup; toggle with
  `EVENT_DELIVERY_WORKER_ENABLED`. Scheduled jobs are toggled one at a time —
  `PHOTO_SWEEP_ENABLED`, `PHOTO_REVIEW_BACKFILL_ENABLED`, `CANDIDATE_INDEX_ENABLED`,
  `EXPOSURE_ROLL_ENABLED`, `INTENT_DRIFT_ENABLED`, `GRID_STALENESS_ENABLED`,
  `INTEREST_EXPIRY_ENABLED`, `SCALE_PRESSURE_ENABLED` — and **every
  job's first run is at startup**, not after its first interval, so a six-hourly job is
  observable on a laptop.

## Git & domain language

Conventional Commits, scoped `api` or the module: `feat(rating): revise a submitted
answer`. Run `make check` before pushing; CI runs the same gate for `backend/**` changes.

The shared glossary is [`../CONTEXT.md`](../CONTEXT.md); backend-only technical vocabulary
is in [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally. **Only Users, Auth
and Skill rating are modeled** — the rest of the racket-sport domain has no terms committed
at all after the reset. Before writing a new context, resolve its terms into the glossary
and record the aggregate shape in an ADR, including whether it is event-sourced or
persisted-with-events.
