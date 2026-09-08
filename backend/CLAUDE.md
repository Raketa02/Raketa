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
make openapi     # emit openapi.{player,dev}.json — the player contract the client
                 # generates from, and the dev console's one-path contract
make gen-walkthroughs  # rewrite the matchmaking golden files (a diff is a design change)
make up / down   # dev stack (Postgres + API + MinIO + photo-review + Redis); logs, shell
make migrate     # alembic upgrade head inside the API container
make seed        # the named accounts, the cohort and the games they have played, then
                 # reads every Play screen as the protagonist and refuses a database
                 # that cannot draw one. Needs the stack up (Postgres + Redis, and
                 # MinIO for the three photographs — without it the run says so and
                 # seeds the rest); make seed-host on the host
                 # Then http://localhost:8000/dev — the dev console, the thing that answers
                 # back, since no Play flow can be exercised with one phone
make gen-cohort  # rewrite the cohort's committed population (a diff is a fixture change)
make rebuild-candidate-index  # fold the log back into the index (…-host on the host)
make photo-flag-rate  # the on-court flag rate at each candidate threshold, read off the
                 # similarity vectors already stored beside the photographs — no image
                 # re-scored, nothing written (…-host on the host)
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
  every run. Four of the eleven are **protagonists** carrying a per-player *profile* axis,
  and a Play screen is developed signed in as one of them.
- **Behind the named accounts is the cohort, and it is a workbench that says so on its
  face** (`app/seeds/cohort.py`, `app/seeds/screens.py`). One search over eleven accounts
  finds them all in one ring, so a population is generated from a seed and committed as
  `app/seeds/cohort.json` — **inputs only**, never a level, an uncertainty or a band, and
  every draw keyed off the member's own handle so adding one changes that row and nobody
  else's (`make gen-cohort`, and a test asserts byte-identity). It borrows
  `scripts/ruleset_diff/population.py`'s mechanics and **none of its numbers**: that corpus
  is a comparator and this one's job is to *reach* states, which is why ADR-0121 is
  undisturbed. **Two lists, asymmetric** — the declarations are the generator's inputs, and
  the assertions are outcomes of the **real read paths run as the protagonist**, because a
  ruleset that tightens `QUALITY_FLOOR` moves no distribution and still empties every
  screen. It fails `make seed` on **three clocks**: an engine retune moves the band
  histogram (a range per band, never a μ — a μ would pin the engine), a ruleset retune
  empties a screen, and the calendar walks every newcomer out of ADR-0113's window, which
  fails **by name with the age in days**. The run injects a `Clock` — a port, so ADR-0029
  is honoured rather than bent — and **ticks the candidate index's tail in-process** before
  reading, which ADR-0110 makes safe rather than exempt. Half the gate is a signature: the
  assertions need a database and do not run in CI. Seed only what is **modeled**, and the
  fence is expressed as **writes against reads** rather than as imports — the layer
  below widened it from three written contexts to five, and the played history made it six.
- **Beside them is a played history, because a card that prints what the platform
  watched needs something watched** (`app/seeds/games.py`,
  `app/seeds/photos.py`). A seeded game is a real challenge sent off a real search,
  every seat accepted, and a result stated and answered — so the cohort now writes a
  sixth context. Three things about it are load-bearing. **It is the one layer the seed
  writes in the past**: a score is confirmed when its window closes, so a game seeded an
  hour ago is a game still awaiting an answer, and each one is written on its own
  backdated clock while every relationship is still written at the run's own now.
  **Five counted games costs five distinct opponents**, and that cost is now *kept*
  rather than forced: a completed line-up releases its pair
  ([ADR-0142](../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §1, #343), so a pair that has played is shown each other again. Rewriting the rows would
  move `cohort.json` for nothing. **No game seats the protagonist, and that reason
  inverted**: a game with her in it used to take that person *out* of the pool every
  `screens.py` assertion is read from, and would now put them back *in* carrying an
  `ACCEPTED` tally — which is `PREVIOUS_ACCEPT`, named in `CANNOT_BE_DRAWN` as absent. The
  tennis opponents live in ring d for the ladder's sake, which was always a separate
  reason and is untouched. And **the photographs are a declared verdict
  and generated bytes**: `PhotoReview` is a port the fixture supplies like the clock,
  because what a check concluded about a synthetic image is a thing a workbench chooses
  rather than discovers — the note itself is written by the domain's own constructors, so
  a seeded shield is one `decision_on_record` agrees to believe. The object store is the
  one thing the seed writes that lives outside the database, so the run **asks it one
  question first** and reports rather than dies when it cannot answer.
- **A distribution cannot assert a pair, so eleven accounts are named for one**
  (`app/seeds/relationships.py`, `app/seeds/pairs.py`, `app/seeds/paths.py`). Five of the
  ten `LivenessSignal` codes are facts about **two people** — *they said yes to you*, *they
  turned your court down*, *their inbox is full* — and no cohort, however well shaped, can
  exhibit one; a rate cannot assert that **exactly one** instant-match pair exists. So the
  cohort keeps the six that are properties of one person and this layer signs the pairwise
  five, each account named for the relationship from the protagonist's side.
  **Every edge costs a real search or deal run as the sender** — `Interest` and `Pass` have
  no non-search constructor, a send cites the search its court was built on — and that cost
  is the check: an origin that resolves proves the protagonist was genuinely findable
  through gender, level and radius before any lift is claimed. **`PREVIOUS_ACCEPT` is
  narrowed out by name, and the name is now about the fixtures**: a pair is
  `OPEN_CHALLENGE`-gated while they are **still arranging**, which this cohort's accepted
  seat is — a co-invitee's seat on a doubles court with an unanswered seat beside it. It is
  no longer unreachable on the platform (ADR-0142 §1 releases a completed line-up), so what
  `tests/demands/` contracts is the **release** and the half-built court that does not
  release, rather than a permanence. **Absence claims assert the gate histogram**,
  not the absence, because an account gated for an accidental reason is absent too and a
  naive claim passes. Two costs are **printed on the report** rather than hidden: the
  pass's suppression is a Redis TTL that fails soft while its row never expires — so the
  run is idempotent for the row and unconditional for the cache, and the complaint names
  the **cache** — and the deal that earned the pass's origin key leaves the protagonist's
  deck a day short (ADR-0131). This is the only place the seed writes `challenges` and
  `blocks`, and it writes them through their own use cases like everything else.
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
  open**: a flagged photo is stored, and an unreachable sidecar yields **no decision at
  all** with a note saying which outage, because an outage is not a conclusion about an
  image. Every verdict records the similarity vector it was taken from, which is what makes
  today's placeholder threshold safe **and replaceable without paying for inference
  twice**: `make photo-flag-rate` (#316) walks the stored notes and prints the flag rate
  each candidate line would have produced, how many stored verdicts each move would make
  wrong, and — before the curve, because a rate is a number over a denominator — the four
  exclusions. **One curve per reviewer, never one blended**: two models are two corpora and
  a rate across both is a fact about neither, which is the way this reading can mislead —
  the seed's declared verdicts carry well-formed, current-fingerprint notes and on a laptop
  are most of the bucket. Where the rate should sit is a product judgement the command
  deliberately does not make; the chosen number goes in `photos.py` beside the caps and
  never in configuration. **No test needs the container**
  — `tests/conftest.py` overrides the port, as it does the store.
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
  **And the verdict now reaches a stranger, on the player card, where *never checked* is a
  third answer**
  ([ADR-0138](../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
  A shield saying *checked and passed* cannot be drawn on a photo nothing looked at, so
  `verdict_when_unreviewable` records **no decision** and `review_metadata` writes no key
  — and, because three legacy populations already say `allowed` about unexamined images,
  `decision_on_record` believes a stored decision **only where the note proves a score**
  (model, prompt set, confidence, vector — all four). ADR-0132's backfill is therefore the
  cleanup and never the gate. The card **records** the verdict rather than minting it:
  `PlayerCardSource` pays one `HEAD` per shortlisted row that has a photograph and
  `RecordedCard` stores the code, so the read-back draws the shield that *was* drawn
  (ADR-0109) — the mirror of `photo_url`, which cannot be stored because it dies within the
  hour. `GET /photos/{id}` is untouched, and the note still crosses on no route at all.
- **Background work is an `asyncio` loop in the API process, and a job must be safe to
  run beside itself** ([ADR-0092](../docs/adr/0092-periodic-jobs-as-embedded-loops.md)).
  `PeriodicJob` (`app/infrastructure/jobs/`) is the whole mechanism — the outbox worker
  is written on it too — and **`app/bootstrap/jobs.py` is where the next job goes**,
  built from the composition root so it reaches the same bucket and event store a
  request does. There is no cron, no beat process and no lock: with N API processes a
  job runs N times per interval, so a job that cannot tolerate that needs a different
  mechanism and its own ADR. Eleven jobs today — the uncommitted-photo sweep, whose
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
  The tenth is the **challenge lapse loop** (#252), and it is the only job here that
  **appends a domain event**. A seat past its answer window already reads as lapsed, its
  pair already releases and its challenge already stands as `LAPSED` — a standing is
  folded from the seats and the clock and stored nowhere, so a reader asking *is this
  challenge still open* between a deadline and a sweep gets the same answer either way.
  What the loop buys is the **record**: a `SeatLapsed` in the log, so that *answers
  challenges* has a denominator. What it appends is never a `SeatDeclined` — **a lapse is
  not a decline**, and a Strand that filed silence as judgement would be measuring the
  wrong people. Its read names **candidates rather than conclusions** and that is
  deliberate: a store that could filter on *has this seat lapsed* would be the derived
  standing, stored. `ANSWER_WINDOW` is domain; only the cadence is a setting.
  The eleventh is the **rating catch-up**
  ([ADR-0139](../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
  the second that appends a domain event and **the only one on this list that correctness
  depends on**. Every other job buys a record or a table's size; this is the only path a
  confirmed result has to a Level, because ADR-0137 refused a `ResultConfirmed` event — a
  confirmation is a clock passing and announces nothing — and recorded that cost by name. A
  player whose game confirmed on Tuesday keeps Monday's Level until it runs. It **holds no
  cursor**: every move records the game that caused it, so *have I applied this* is answered
  by replaying the aggregate that would change, and a half-finished run is re-derived in full
  by the next tick rather than being a lost result. Its walk is over every game the platform
  has recorded — the same cost profile as every other read in `games`. The **rule** it applies
  is `engines/racketskill/results.py` and is emphatically not configuration: an environment
  that could pick a K-factor is an environment that decides how a marketplace rates people.
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
- **New routes mount under `app/api/v1/router.py`;** keep the `/api/v1` prefix. The one
  exception is the **dev console** (`app/api/dev/`, #256) — a second *surface*, not a
  second client: one no-build `console.html` behind a `FileResponse` at `/dev`, and one
  roster route, which is the whole of `openapi.dev.json`. It **acts as another player by
  signing in as them** through the ordinary `POST /api/v1/auth/login` with the public seed
  password the roster hands over, so there is no impersonation endpoint, no `Act-As` header
  and no authorisation path that exists for it — every write it presses is a
  player-surface write. It is gated **structurally and by data**, asymmetrically:
  `CONSOLE_SERVED` in `app/api/dev/gate.py` is a **second table** and never `SEEDABLE`
  (deriving one refusal from another is what `app/seeds/guard.py` argues against), and
  importing `routes.py` in production raises `ConsoleRefused` — while the data half is a
  *consequence*, since the roster lists only the reserved `.example` TLD and production has
  no such accounts. The refusal is at the top of `routes.py` rather than in the package's
  `__init__`, deliberately: `create_app` reads the gate in **every** environment, so a
  package that refused on import would take the production deployable down at startup. It
  **declines the `app/seeds/` import it is entitled to** — which is what keeps the console's
  own refusal the one that fires — at the cost of spelling two constants twice, pinned by
  `tests/unit/test_dev_console_surface.py`. Its contract is checked for **freshness**
  (`make contract-freshness`), not by the client drift check, which has no purchase on a
  document with no client.
- **A game is opened by a completed line-up, and a result is the record that it
  happened** ([ADR-0137](../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
  `app/modules/games/` is the sixth context and the second event-sourced racket-sport one;
  it adds **no table and no migration**, because the streams live in `event_store` beside
  everybody else's. Four things about it are load-bearing and none of them is obvious from
  the code alone. **Nothing creates a game over HTTP** — `challenges` calls
  `PlannedGameOpening` **inline, in the transaction of the acceptance that filled the last
  seat**, on `MutualChallengeMinting`'s argument: a subscriber would have to re-derive
  *did this accept complete the line-up* by reading somebody else's aggregate, and the
  player who taps the last accept would be told the game is on by a screen that cannot yet
  show it. **The three ends are folded and never stored, and nothing announces one** —
  there is no `ResultConfirmed`, no sweep and no job, because a derived standing has
  exactly one place to be true; *silence confirms* is a clock passing, so the test for it
  advances a clock and there is deliberately no method called `confirm`. **One route
  resolves three acts** — `POST /games/{id}/result` is a proposal, a correction or a
  counter depending on what already stands, so a client cannot mislabel one, and there is
  no rejection endpoint because *a counter must carry a score*. And **a bad score is a
  refusal, never an `invariant`**: a score arrives from a person typing it, so a level set
  answers with `a_score_must_name_a_winner` rather than a 500 — the split
  `CONTEXT.md`'s *Invariant vs Unavailability* names, applied at the one value object in
  this repository a player composes by hand. Its three clocks are in
  `games/domain/windows.py` and **none of them is configuration**. Its fourth published read
  is `ConfirmedResultLedger`, which exists **because nothing announces a confirmation**: the
  rating context walks confirmed counted results forward, oldest first, ordered on the derived
  moment each became final
  ([ADR-0139](../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)).
  It has **one inward port too**, and it is a single field wide:
  `PlayerHandles` puts a **nickname** on a seat and nothing else about the person in it
  ([ADR-0141](../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). A card is
  what a *searcher* reads to decide about a game that might happen, so a Level, an area or a run
  of form on a record of an evening would be an as-of-now fact stapled to the past; the handle is
  what four people already knew about each other by the time they were on a court together, and
  without it the screens named **sides** — a result agreed with nobody, and three padel games in
  a week told apart by nothing but how long ago they were arranged. **The court is the whole of
  the permission and nothing is re-gated against the reader**: the four fail-closed gates decide
  who may be *introduced*, ADR-0095 §7 already settled that a block does not reach into a game
  already agreed, and a handle that vanished from a row would be §8's trace. It is **one set read
  per response** over the union of every court in the answer, and a handle `users` cannot answer
  for is `null` with the seat kept — the opposite of the shortlist, which drops a row it cannot
  name.
- **A Player Score is what the platform watched, and two strands is what it can see**
  ([ADR-0140](../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
  `app/modules/player_score/` is the seventh context and the first that **keeps no record at
  all** — no aggregate, no repository, no table, no migration. It folds `games`' and
  `challenges`' published ports and does arithmetic over them, because a stored score would be a
  second place for *did that game happen* to be true and the copy is what gets believed. Four
  things about it are load-bearing. **Its port is `PublishedScoreQuery` and not
  `PlayerScoreQuery`** — the matcher's port of that name is the *demand* and this is the
  *publication*, and ADR-0137's rule applies: the cost of a shared word is paid by whoever
  arrives second. **Two of five strands are live and three are absent, never nought** — *keeps
  plans*, *settles up* and *sportsmanship* have no provider, and a player with no record at all
  is absent from the answer, which is the one rule the demand suite is written around.
  **The published weights live in the context and never in a ruleset**, because a weight release
  must not change what somebody's own profile says about them; they sum to 85 on purpose, since
  the blend renormalises over the strands present. And **reliability stopped being absent
  platform-wide**: `NoPlayerScoresExist` retired, `build_absent_terms` answers empty and lost its
  argument, a stood-down reliability is now `NOTHING_FROM_THEM`, and the evidence gate counts
  eight live terms rather than seven — excluding nobody, at a margin of zero rather than one.
- **Sportsmanship stores, and it is the first aggregate here that is not event-sourced**
  ([ADR-0154](../docs/adr/0154-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)).
  `app/modules/sportsmanship/` is the eighth context, and it is the mirror image of the
  seventh: `player_score` keeps no record at all, and this one is the first part of the
  player record that keeps one — an aggregate, two tables and a migration. The exemption
  from *state changes emit domain events* is **argued rather than inherited**, on the terms
  that rule demands: a card is **born answered**, so a stream would be one event per card
  and a replay a `SELECT` with extra steps; **nothing subscribes**, so an outbox row would
  wait for nobody; and there is **no standing to derive**, which is the whole reason `games`
  replays. Five things are load-bearing and none is obvious from the code. **The collapse is
  the primary key** — `sportsmanship_rating` is keyed `(rater_id, subject_id)` and a later
  card *replaces* the earlier answer, because a read-time collapse is a rule the first
  reader to forget hands the farming problem back with a plausible number; the earlier
  answer is not archived, and the cost of that is named in the record. **Two tables, because
  the all-blank card has to close** — a blank is spelled by absence and nothing else, which
  is what makes *not rating leaves no record of the omission* structural, so the closure
  cannot live on the answers. **You rate everybody else on the court**, partner included, so
  there is no *side* in this context and rating yourself is refused by the same rule that
  refuses a stranger. **The matcher never reads it — the floor and the term** — and that is
  held by an `.importlinter` contract rather than by a test, because a Match Fit term
  reading a star average would look like every term beside it and nothing would go red;
  it is also why the reliability pill stays the counted-only number. And **no individual
  rating reaches anybody in any shape**: the write answers `204`, the use case returns
  `None`, and `SportsmanshipLedger` has no method that answers *what did somebody say about
  me* — only *which of these cards are closed*, which is a fact about an act. There is one
  read here and it grew without touching that: `GET /api/v1/sportsmanship` lists the courts
  **waiting** for somebody's stars, as a game id and the people on it, and an open card is
  by definition one nobody has answered. It borrows one thing,
  `SettledCourts` over `games`' directory, whose adapter lives in **this** context the way
  `PlayerHandles`' lives in `games`; *settled* there is narrowed to **played and over**,
  because a ghost has nobody to rate and an unscored game very much does. **The card's two
  clocks are domain and neither is configuration** (`domain/window.py`): it opens the day
  after the game — an answer given ten minutes after losing badly is not the answer wanted —
  and closes seven days later. Both edges run from `games`' `played_at`, which is *the moment
  somebody said we played* and never the hour on court, because this platform records no such
  hour; it is never earlier than the game, so the day-after rule holds conservatively. Anchoring
  the close to a *settlement* instead would let an argument over the score restart somebody's
  week, and the price is named rather than discovered: a game two sides argued over settles up
  to a day into the week, so that one card is drawn for six days rather than seven. *Has it
  settled* stays the port's separate gate. **Nothing sweeps an expired card** — the expiry
  is a fold, because *not rating leaves no record of the omission* means there is no row for
  a job to correct — and the window governs the **prompt** and not the permission: a card
  that lapsed while somebody was typing is still answerable, which is the opposite of
  refusing one of two identical taps.
- **A record is read through a prior disclosure, and the refusal names nothing**
  ([ADR-0155](../docs/adr/0155-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)).
  `app/modules/player_record/` is the ninth context and the second that keeps **no record
  at all** — no aggregate, no table, no migration, and a structural test that walks the
  package for an ORM import and the migrations for a table named after it. What separates
  it from `player_score` is that it also **enforces admission**, and that is the whole of
  what it decides for itself. Five things are load-bearing. **A record opens on a prior
  disclosure and never on a person**: you are the subject, a search of yours *returned*
  them, or you share a live challenge or a game — otherwise a route taking a player id is
  a player-enumeration endpoint, and a UUID being hard to guess is not an authorization
  model. **Nothing expires**, because a search record is kept for ever (ADR-0104) and a
  shorter window could only refuse a face the app is currently showing. **The four
  fail-closed gates run live, in the partition of the disclosure** — never in the sport
  the reader arrived from, since the gender gate reads a candidate index row and the index
  is keyed by sport, so a subject rated only in squash has no padel row and *a gate that
  cannot be evaluated excludes*; that is why `PriorDisclosure` answers in **sports** and
  why the partitions are walked in the sport registry's own order rather than a set's
  (ADR-0105). The reader's **own** hold refuses here too, because a hold points both ways
  and would otherwise end at the one route that remembers what a search already showed —
  while **your own record has no gates at all** and is a *second use case* rather than a
  branch, so the screen that tells a player how they appear cannot be taken down by the
  gate machinery. **The four refusals are one refusal, byte for byte** — never disclosed,
  blocked either way, held and no such player are one `404` with one body, asserted as a
  sameness rather than as four statuses. And **this context declares its own ports and its
  own types**: it borrows nothing from another context's domain, held by an `.importlinter`
  contract rather than a test, because an application layer importing `CardIdentity` would
  read as sensible reuse in the diff and nothing would go red. The cost is a second
  spelling of four words — `OnCourtVerdict` beside `PhotoReviewDecision`, `GameOutcome`
  beside `games`' `Outcome` — and their agreement is asserted, the way `games` asserts its
  two bounds against each other; the same rule reaches the **wire**, where
  `RecordLikelyRangeSchema` is named for its surface because a second `LikelyRangeSchema`
  would not shadow the card's, it would rename it.
  **`?sport=` says what the sheet is about and never who may be seen** — it reaches the
  assembler and never the admission, so naming a sport you were never shown somebody in
  changes what is drawn and nothing about whether it is drawn. Resolving it is the one rule
  this context owns (`domain/sport_choice.py`): the sport asked for where they hold a
  rating in it, otherwise their **most counted** — never their highest Level, which would
  make the header a boast, and never their most recent, which is activity recency wearing a
  sport's name — ties broken by the sport registry's own order, and `None` for somebody
  rated in nothing, whose sheet draws pills and no skill card. Registry order is
  **structural**: both functions walk `Sport` and look the mapping up rather than iterating
  a mapping and sorting after (ADR-0105). **`counted_games` on the skill card is not the
  card's number under the same word** — it is `SkillRating`'s own applied-games count, per
  sport, *what this certainty rests on*, so it comes off the same stream as the Level and
  moves in step with it; the player card's is *how much have they played*, over every sport,
  and counts an evening nobody agreed a score for. Two provider ports widened for it:
  `rating`'s **read** port gained `ratings_of` (one player, every sport — never the
  repository, which remembers stream versions), and `games` gained `recent_results_in` as a
  **second method rather than a parameter**, because the set read is frozen into search
  records kept for ever and because this one filters on the sport *before* it trims to five.
  **Opponent variety is the third fact to arrive, and it is a *separate port* on `games`
  rather than a sixth method on that one** (#380). The fold is deliberately **unbounded** —
  that is what makes it a career statistic, and a window here would be a second horizon that
  must not disagree with the matcher's — so an unbounded fold on the port a search already
  holds is one somebody eventually calls inside the walk over five hundred candidates. It
  answers about **one player and never a collection**, the fence is the signature, and both
  sides of the seam assert their own. What crosses is the **raw pair and no percentage**: a
  bare share would hide whether *70 %* is fourteen of twenty or seven of ten, which is the
  argument the metered rows beside it print their fractions for, and the division is a
  client's. Absence is the same absence everything else here spells — no counted game means
  the row is **omitted**, never `0` and never `0 / 0` — and it is a *different* absence from
  `skill`'s, so the assembler asks for it whatever sport resolved. Its denominator is
  `counted_games_for`'s own predicate, written once in `games` and read by both, so the sheet
  cannot print a pair that disagrees with the card beside it.
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

**`make openapi` writes one document per surface, and there are two.** The second is the
**dev console**'s `openapi.dev.json` — one path, and no client, so nothing generates types
from it. Both are committed, and both are gated at the repository root by
`make contract-freshness`: re-emit and diff, which is a different question from
`make test-drift`'s (that one asks whether the *client's* generated types reproduce from
the document, and has no purchase on a document with no client). Commit the regenerated
documents with whatever moved them.

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
- `tests/demands/` — the **outward demands**, parameterised over every implementation
  registered in a register beside the wiring
  ([ADR-0098](../docs/adr/0098-matcher-demands-as-executable-contracts.md)). Adding a row
  to a register enrols an adapter; a port with no row fails the suite. Not named
  *contract* — that word already means `openapi.player.json` drift here.
  **Five registers, and they are five on purpose — one per kind of claim.**
  `app/bootstrap/matcher_demands.py` and `player_record_demands.py` hold the ports a
  *consumer* declares of contexts it does not write; `games_demands.py`,
  `rating_demands.py` and `player_score_demands.py` each hold the ports one *provider*
  publishes outward. Each register's exhaustiveness assertion is about its own kind of
  claim and would stop meaning anything with another kind in it — which is also the rule
  for the next one: **a new provider or a new consumer gets a new register, not a row in
  somebody else's**, and the first person to add a row should not have to guess which
  list it belongs in. One port on the record's list has **three** implementations, which
  is what the suite has to be parameterised over: *where has this reader been shown this
  person* is a question three contexts each answer about themselves.
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
  `INTEREST_EXPIRY_ENABLED`, `SCALE_PRESSURE_ENABLED`, `CHALLENGE_LAPSE_ENABLED`,
  `RATING_CATCH_UP_ENABLED` — and **every
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
