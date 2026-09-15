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
make seed        # the named accounts, the cohort, the games they have played and four
                 # more nobody has played — whose plans reach nought, one, two and
                 # three slots — then reads every Play screen as the protagonist
                 # and refuses a database that cannot draw one. Needs the stack up (Postgres + Redis, and
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
- **The last layer is the loop's own states, and it is the one that tells as it
  writes** (`app/seeds/loop.py`). Everything above it seeds the *Play* screens and the
  two layers before it reach a game arranged and a plan half agreed; this reaches
  everything between *the plan is complete* and *the score moved a Level*, plus the
  three challenge endings no other layer arrives at. Four things about it are
  load-bearing. **A card is folded and not declared**: the nine names the Now rail draws
  live in the client's `features/plans/domain/gameCard.ts`, and the claim here re-derives
  each one off `GET /games` and `GET /plans` as the player whose rail it is — so a card
  name that stops being reachable fails on a seed run rather than on somebody's phone.
  **Two of the nine are stated absences, and the arithmetic is the argument**:
  `uncounted` needs both proposal windows closed, which is a day after the entry and
  exactly when an ended card leaves the rail, so that state reaches the game screen
  through *Details* and never the rail; and `unreadable` is the client's gap for a
  standing this build has no word for, which a fixture cannot produce without inventing
  an event. **It is the one layer that cannot leave the delivery to the end**: a
  membership line is written only where a room already existed and a slot or played line
  is hung on a room *through its game*, so every line it seeds depends on an earlier
  event having been delivered — and the outbox orders by a `created_at` that is one
  **second** granular on SQLite, which is the database `make check` runs the whole seed
  against. So it drains between writes, and two batches are two orders nobody has to
  guess. And **its fill seats exactly one member and they say no**: a yes could complete
  the line-up of the very court `pairs.py` asserts is still half built, and a mutual
  mints again only once the last one it minted is finished with (ADR-0152) — so the cost
  of `SEATS_INVITED` is a `PREVIOUS_DECLINE` on one pair rather than somebody else's
  fixture.
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
  mechanism and its own ADR. Twelve jobs today — the uncommitted-photo sweep, whose
  **retention window is domain and whose cadence is configuration** (those two must not
  swap places), the candidate index's two loops below, the **exposure roll**, the
  first job here that takes no database session at all, the two **prompt loops**
  (intent drift, availability staleness), which write no value anywhere — each raises a
  question into the prompt ledger and stops, and every threshold behind them is domain
  in `matchmaking/domain/prompts.py` while only the cadences are settings — and the
  **interest expiry loop**, the first of two that delete anything. Turning that one off
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
  The twelfth is the **conversation sweep**
  ([ADR-0153](../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)),
  the second that deletes anything and the only one that deletes an **aggregate** — a room
  and its whole stream, *destroyed, not delisted*. Correctness does not depend on it: a
  room's end is derived on every read — the game's clock off its own stream, or its
  challenge being over, asked of `challenges` — so every route on it answers
  `conversation_not_found` past that instant and every list has already dropped it, whether
  or not anything has swept. What it buys is that the destruction is **real**, which is the
  whole difference between a room that is over and a record with no end. Like the lapse
  loop its read names **candidates rather than conclusions**, and here it could not do
  otherwise: a store that could answer *which rooms have ended* would be the stored
  `ends_at` ADR-0153 §5 refuses. It leaves a hole in `event_store.sequence_no`, which the
  candidate index's tail is built for — a gap is stepped over once the snapshot horizon
  proves it permanent, so a destruction costs that projection a tick of lag and never an
  event. `CONVERSATION_GRACE` is domain; only the cadence is a setting.
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
  **And the tap says whether a game came of it**
  ([ADR-0154](../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md),
  #370). `MutualChallengeMinting` kept `UUID | None` and **moved its meaning** — from *what
  this call minted* to *the game these two have*, so a repeat tap held by 0152's idempotence
  guard is answered with the game that guard is holding it on rather than with silence. The
  ids were already in the guard's hand; `express_interest` was discarding them, which is the
  whole of what #370 was. It rides out on `ExpressedInterestResponse.challenge_id`, additive
  and nullable, and `mutual` does not move: reporting it `false` because a gate refused would
  say something about the other person no refusal may. **`None` covers two unrelated causes
  and may not be narrowed to one** — a game still being *arranged* (a send, or this mutual's
  own half-built doubles court), and a gate that refused or could not be read — which is
  ADR-0130's *a withholding is stated, the gate is not named* applied one route over. Giving
  the first case an id, which is one port read away, would make absence mean *a gate refused
  about one of you* and the field would have to go; §3 of the record is where that is
  written down. `mutual_born_challenges_that_became_games` answers **newest first** for it, so
  the row named to a player is not set iteration order (ADR-0105).
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
- **The fill names the challenge it completes, and the gate steps aside for that one court**
  ([ADR-0150](../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)).
  Half the mechanism had been written and unreachable since it was authored: `Challenge.invite`
  had no caller anywhere in `app/`, and ⚡ from a challenge could not have worked if it had —
  `_locked` resolves a hand-seated player *out of this search's own pool or not at all*,
  `gate_of` excludes everybody in `open_challenge_ids`, and ADR-0142 holds that pair for the
  whole of `LINE_UP_INCOMPLETE`, so **everybody who accepted your half-built court was by
  construction absent from the pool of the search meant to finish it.** Four things fix it and
  each is narrow on purpose. `POST /lineups` grows one optional **`completing_challenge_id`**,
  and `sport`, `mode` and `locked_seats` are **refused beside it** rather than made optional —
  all three are facts that challenge holds, and a caller supplying one could lock somebody who
  is not in the challenge or forget somebody who is. `search_workbench.bind` takes that id and
  builds `open_challenge_ids` from every open challenge **except** it, which is why
  `OpenChallenge` and `SharedChallenge` grew a `challenge_id`: the exemption is an **input**,
  the roster still counts ten codes, and a court member excluded for any of the other nine
  still falls out — so `locked_seat_not_available` stops being unreachable on this path and
  starts meaning *somebody has been blocked, held or deactivated since they accepted*.
  `pool_for` takes an `excluding` set so **nobody who has answered that challenge is a
  candidate for its own fill**, which keeps `NobodyIsAskedTwice` a backstop rather than a
  screen a player reaches after choosing somebody. And **`POST /challenges/{id}/seats`** is
  the send's shape minus the mint: it re-verifies the send's five facts with the pair rule
  excepting this one court by id, resolves origins for the **newly seated only**, and calls
  `Challenge.invite`. **Any live member may fill; a court that was never a game is nobody's to
  withdraw once somebody else has joined it** (ADR-0165 §4, below) — the case that decides the fill is the mutual-born doubles
  challenge, `LINE_UP_INCOMPLETE` from birth with an "organiser" who is only whoever's yes
  arrived second. The mode is **inherited, or
  resolved from the filler's declared Play intent** on the deck's own rule, and the **window
  is never re-stamped**, so a mutual-born challenge stays window-less for life. The cost is
  recorded rather than softened, on the port and on the two routes that meet it: **a lapsed
  invitee is out of that challenge's own pool for as long as it stands** — `already_asked_at`
  feeding `NobodyIsAskedTwice`, per aggregate, and asking them again is a **new** challenge. It is
  **not** the pair rule and reaches no other search: that rule holds the people still arranging
  a game, and a seat that left is not one of them (#393, which retracted ADR-0150 §4's *every
  sport*). `HalfBuiltCourtQuery` is the **sixth** matcher demand and the only
  one whose posture is `CLOSED` without being a gate: a fill that cannot read the court it
  names would silently become an ordinary ⚡ over a pool that still excludes the very people
  it was meant to seat around.
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
  the code alone. **Nothing creates a game over HTTP, and nothing moves a seat on one over
  HTTP either** — `challenges` calls `PlannedGameHandover` **inline, in the transaction of
  the acceptance that filled the last seat**, on `MutualChallengeMinting`'s argument: a
  subscriber would have to re-derive *did this accept complete the line-up* by reading
  somebody else's aggregate, and the player who taps the last accept would be told the game
  is on by a screen that cannot yet show it. **A yes can be taken back, and a court is over
  when one is left**
  ([ADR-0162](../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md),
  [ADR-0165](../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)):
  `POST /challenges/{id}/departure` writes `LEFT` over an accepted seat on any court that
  still stands — half built, awaiting, or a game; there is no `not_a_game_yet` — and, where
  the court has become a game, hands `vacate_seat` over on the same port in the same
  transaction, so `SeatVacated` opens the seat on the game — drawn `player_id: null`, never
  dropped — and the next completed line-up hands over a **re-seat** of the same game
  (`LineUpReseated`, same id, same `planned_at`) rather than the opening of another. A result
  is refused while a seat is open (`the_court_has_an_open_seat`), every fold reads the
  current court, and the pairing read omits the forecast, the split and the stakes until it
  is whole. The **moment guard** is three ports and no arrow moves: `games` demands
  `AgreedMoment` of the Plan in its own words (signed in `plans/infrastructure/`, contracted
  on `game_demands.py`), publishes `SeatableCourt` (`games_demands.py`), and `challenges`
  reads it through its own `SeatableGameQuery` — on the departure, the fill and the
  acceptance, and only on a court that has been a game; a half-built court has no moment
  to guard. The challenge folds one fact beside its seats for this, `game_opened`, **off
  the acceptance that completed the line-up** (and the mint of a mutual-born singles) —
  never off `SeatLeft`, which can now be written on a court that was never a game. **The
  ending rule is organiser-blind**: `standing.py`'s `deserted` — *at most one player on it
  and no seat awaiting an answer* — replaces the *no live seat besides the organiser's*
  clause, and **a departure is a no**, so before a game the fold reaches `DECLINED` and the
  room ends with its challenge, and the ending is dated by the departure's own instant
  (`departed_at`, folded off `SeatLeft` for #388's reason). On a game the fold does not end the
  court; the departure use case asks the same rule after recording itself and, when it
  fires, hands `call_off` over on the same port right after the seat — `called_by` is the
  leaver — so the game is `CALLED_OFF`, singles included, and the room is destroyed by
  `GameCalledOff` reaching it (the second telling whose whole effect is that the room
  stops existing). The game admits that caller because it folds `departed` off
  `SeatVacated` — *the people who may act are the people who were on the court*. A decline
  or a lapse that leaves one player on a game does **not** call it off — only the departure
  asks the rule — and that court is filled or called off as before. **The withdraw is two
  acts on one route, told apart by whether the court has been a game** (ADR-0165 §4–§5,
  #426). On a court that was never a game it is ***Remove the challenge***: the organiser's,
  admitted **exactly while nobody besides the organiser holds an accepted seat** — before
  anybody has answered, and again once everybody who joined has left, whatever seats are
  still deciding — and refused with `somebody_has_joined` the moment one person is in, since
  a court somebody has joined is nobody's to end for the others; from there the organiser
  leaves like anybody else. ADR-0142 §2's pre-answer refusal is reversed, and the
  withdraw-and-resend it guarded against is an accepted risk with its falsifier named. Two
  things follow from a removed challenge holding seats whose day is still running, and both
  are asserted: an answer on one meets `challenge_is_over` (the seat's own refusals first,
  then the challenge's), and neither `seats_awaiting_answers` nor the lapse loop counts
  it — the read asks the fold, and `Challenge.lapse` records no day the removal cut short,
  which is ADR-0142 §5 on the write side. **On a court that has been a game it is *Call it
  off*, and it reaches the game**
  ([ADR-0163](../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)): the withdraw
  hands `call_off` over on the same port in the same transaction, `GameCalledOff` is the
  fourth end — read first by `standing_of`, in `SETTLED`, out of `PLAYED`, and **in no
  tally**, because a ghost is silence and this was an act — and the act is **any player's on
  the court**, an accepted seat, with no organiser-first rule and no fallback; only in
  `LINE_UP_INCOMPLETE` (`not_a_half_built_line_up` on a whole court or with a fill still
  pending). `withdraw_is_the_organisers` keeps its code for both acts — *the act is not
  yours* — and an ended challenge is `challenge_is_over` on both, as everywhere else. A
  court whose window already closed is withdrawn without the game being told; the ghost
  stands, and so does a game a departure already called off — `CallOffGame` steps over
  both ends rather than re-ending either. **Three ends
  are folded from the record and the clock and the fourth is announced, and all four are
  never stored** — there is no `ResultConfirmed`, no sweep and no job, because a derived
  standing has exactly one place to be true, and `GameCalledOff` may announce its end
  only because no arrangement of the record could reach it (ADR-0142 §3's exemption,
  argued again for `games`); *silence confirms* is a clock passing, so the test for it
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
  It has **two inward ports**, and the first is a single field wide:
  `PlayerNames` puts a **name** on a seat and nothing else about the person in it
  ([ADR-0141](../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md); the name and
  never the nickname since
  [ADR-0171](../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md),
  which is also why the port stopped being called `PlayerHandles` — a **handle** is now the
  nickname's word, drawn as `@…` on a record and the You tab and said nowhere). A card is
  what a *searcher* reads to decide about a game that might happen, so a Level, an area or a run
  of form on a record of an evening would be an as-of-now fact stapled to the past; the name is
  what four people already knew about each other by the time they were on a court together, and
  without it the screens named **sides** — a result agreed with nobody, and three padel games in
  a week told apart by nothing but how long ago they were arranged. **The court is the whole of
  the permission and nothing is re-gated against the reader**: the four fail-closed gates decide
  who may be *introduced*, ADR-0095 §7 already settled that a block does not reach into a game
  already agreed, and a name that vanished from a row would be §8's trace. It is **one set read
  per response** over the union of every court in the answer, and a name `users` cannot answer
  for is `null` with the seat kept — the opposite of the shortlist, which drops a row it cannot
  name. A null there never means *unnamed*: sign-up creates an account with credentials only
  and **the naming** (`PUT /api/v1/users/me/name`, one event carrying name and nickname,
  repeatable) is onboarding's first step, so the entry gate holds an unnamed account there and
  `GET /users/me` is the one read where `name` and `nickname` may be null.
  **The second inward port is `CourtPairing`, and it is read *beside* the game and never on it**
  ([ADR-0161](../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
  `GET /games/{game_id}/pairing` answers the forecast, the split, what is at stake and each
  seat's Level — **for the reader**, only for somebody on the court (`404 game_not_found`, one
  code for two cases) and only while the game is `AWAITING_ENTRY` (`409 pairing_is_history`),
  because a pairing means what a card means *because this game has not happened*. The port is
  declared in `games`' own types and signed by `matchmaking/infrastructure/games_court_pairing.py`
  on the matcher's side of the arrow, so `games` still does not import the matcher; the adapter
  reads `PairWithACourt` — the challenge card's own use case — so **the card and the game come to
  one number for one court**, and a test says so. Three things are decided in the adapter and
  each is an absence rather than a number: a seat the index cannot describe leaves the forecast
  **omitted, never provisional**, with **no reason beside the absence**; `at_stake` is omitted on
  a friendly and on a game is priced **side against side** through `AtStakeQuery`'s court-shaped
  read, because every seat is known and that is the pair `settle_results` will deliver — which
  is why a four's figure here is not the card's head-to-head one, and why a side with one
  unrated seat is priced over its rated members rather than omitted; and the seats' Levels come
  from `rating`'s **published** read (`RatedPlayerQuery.published_for`), never from the index.
  **Two providers stand behind the one port and fail on their own**: a process with no index
  draws no forecast and still names every Level and prices the court. `GET /games` is
  untouched: a seat there still carries a name and nothing else.
- **A room is opened by the first acceptance, and it is told by contexts that do not know
  it exists** ([ADR-0146](../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md),
  [ADR-0147](../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
  [ADR-0148](../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)).
  `app/modules/conversations/` is the eighth context, the platform's first messaging of any
  kind, and it is deliberately narrow: purpose-bound, never between strangers, never
  permanent. Five things about it are load-bearing and none is obvious from the code alone.
  **It is the outbox's first *writing* subscriber**, and that is ADR-0110's second
  guarantee: the candidate index went to the log because an outbox subscriber *"could never
  name the `sequence_no`"*, and a room names no event's sequence — only its own. Two
  consequences fell out of being first. `EventBatch` now takes a unit of work and **rolls
  back a failed delivery before recording the attempt**, because `mark_failed` commits the
  session the handlers ran in; and the teller is subscribed **per batch, over that batch's
  session** (`EventRuntime._dispatcher_over`), so a system line commits with the outbox row
  that caused it. Delivery is still at-least-once, so **every write here is idempotent** —
  a room per challenge on a unique index, a line per **outbox row** on `source_event_id`,
  a message per `client_message_id`. **The sequence is gapless and it is the aggregate's
  own fact**: `last_seq + 1`, minted under the conversation row's lock inside the appending
  transaction — not a Postgres sequence object, which is documented not to be gapless, and
  not a timestamp, which ADR-0097 disqualified. It is **not** the stream version, and the
  two part company at row one because the opening event writes no entry. The lock is the
  one thing this suite cannot exercise: SQLite renders no `FOR UPDATE` and runs one
  connection, so that path meets Postgres or nothing. **Membership is derived, never
  stored** — the challenge's accepted seats until the line-up completes, the game's
  **current** line-up after (ADR-0162: a seat can be left and re-seated, and the roster reads
  the game live either way), one rule read against two records, and a stored roster would be
  the copy that decides who may read the messages. **Two shapes ride one stream and no sentence is
  ever stored**: a Message is content, a system line is a code and its values, and `values`
  never repeats what membership already says, so a corrected name fixes the whole backlog —
  and **the read resolves a face for everybody the page names, not only for the roster**
  (ADR-0148 §4 as amended, #408): the person a `SEAT_LEFT` line is about was never a member
  — a *no* is not an accepted seat — so each of the three reads carries `people`: the roster
  and the entries' actors and authors on the room and the row, the page's own on a page,
  one `MemberFaces` read each. `members` stays the roster and the gate.
  **What is refused is a table rather than prose** — `application/telling.py` names every
  event either half of the loop publishes and what this room does about it, including the
  ones that write nothing and why, because a builder reading only the event list would write
  a line for each. There is no *Game on* line. And **a refused line is not a refused
  telling**: `GamePlanned` reaches the room, draws nothing, and is where the room learns its
  game — as does `ChallengeWithdrawn`, whose whole effect is that the room stops existing.
  **A room is for the episode, and its end is derived**
  ([ADR-0153](../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md),
  [ADR-0164](../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)
  §6). A room **with a game** ends on the earliest of `entry_closes_at(planned_at)` and
  `GamePlayed` plus `CONVERSATION_GRACE` — both facts the room is **already told**, so it
  costs no new event, no new field and no new telling, and the anchor is `Game.planned_at`
  and never the plan's agreed point, which two people could walk forward by tapping a chip.
  A room **without a game has ended exactly when its challenge is over** — `DECLINED`,
  `LAPSED`, `WITHDRAWN` — read on every read through `ArrangingCourt.over_among`, the port
  its membership already comes from: the adapter folds the standing with `challenges`' own
  `ENDED` and a set of ids crosses the port, so the application layer never learns what a
  standing is; a withdrawal destroys it in the same act. **There is no departure shelf.** ADR-0153 §3's *48 h after the last
  membership line when it was a departure* read the order the answers arrived in — `B yes →
  D yes → C no` closed a room under the three people still in it, `B yes → C no → D yes`
  never did — and a fill after it opened a fresh room with no history; a fill now continues
  the **same** room. There is no `ends_at` column: the instant moves as the room is told
  things, so **past its end every route answers `conversation_not_found` whether or not the
  sweep has run** — the sweep makes the destruction real, not the answer right — and
  `application/lifetime.py` is the one seam that decides *over*, for the list, the sweep and
  `ARoomOfYours` alike, asking the port about the rooms without a game and nothing about the
  rest. `CONVERSATION_GRACE` is **48 h and belongs here, not to `games`**: there is no
  interlock with `ENTRY_GRACE`, and its falsifier is written down with it.
  Three things about the lifetime are worth holding separately from the rule.
  **`conversations` imports `games`, and that arrow is the second one to run this way** —
  `domain/lifetime.py` takes `entry_closes_at`, exactly as `plans` takes `PLAN_HORIZON`
  (ADR-0148 §8); the reverse stays shut by `.importlinter`'s *No context knows the
  Conversation exists*, and the import is why the derivation is a module rather than a method
  on the aggregate, which is folded by a repository that knows nothing about entry windows.
  **The destruction appends no event and that is not the ledgers' exemption** — it is the end
  of an event-sourced aggregate rather than one that skips event sourcing, and a
  `ConversationDestroyed` on the stream it deletes would be a record of the destruction
  inside the thing destroyed. **And the coupling `domain/lifetime.py` used to state between
  `ANSWER_WINDOW` and `CONVERSATION_GRACE` went with the shelf it existed for** — it kept a
  departure from destroying a court somebody was still entitled to accept into, and a room
  that lives as long as its challenge cannot be destroyed under an open seat by any number.
  `lifetime.py` says so where the coupling was written down.
- **A plan is the challenge's, and it is born by being used**
  ([ADR-0144](../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
  [ADR-0145](../docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md),
  [ADR-0148](../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md),
  [ADR-0164](../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)).
  `app/modules/plans/` is the ninth context and the third event-sourced racket-sport one; it
  adds **no table and no migration**, because the streams live in `event_store` beside
  everybody else's. Eight things about it are load-bearing.
  **Its aggregate id is the challenge's**, so *one plan per challenge for ever* is a fact
  about the store rather than a rule a caller keeps — and it is the one context here whose
  reads need no payload match: *this court's plan* is a stream read and *these courts'
  plans* is an `IN`. One challenge has at most one room and at most one game and both carry
  `challenge_id`, so the room draws the plan by its own id **from its opening** and the game
  the challenge becomes inherits it; the four plan events carry `challenge_id` and are
  registered at **version 2**, with version 1 — `game_id` — deliberately unreadable, because
  no environment but `local` has ever run and its database is disposable.
  **Nothing is written at birth**: there is no opening event, no subscriber to `SeatAccepted`
  or `GamePlanned` and no outbox hop, so the first slot write is the birth — and `GET /plans`
  still answers **one row for every court the reader holds an accepted seat on, written or
  not**, three empty slots and the anchor for a court nobody has written on, because the row
  is what carries the anchor and says there is a plan to draw. An invitee still deciding and
  somebody who left get no row, and are refused as a stranger is: `plan_not_found`, **one
  code for three cases** — and so is the organiser **before the first yes**: their seat is
  accepted from birth and makes no court on its own, because the room the plan is drawn in
  opens on that yes and a slot written earlier would be a line with no room to land in. The
  fold asks for the room's precondition — somebody else's accepted seat, or a game — rather
  than for the room. **Three slot events and no fourth slot** — a place, a day and an
  hour recorded — because *setting a slot and moving one are the same event told with two
  sentences*; there is no completion event (the third recording **is** the completion), no
  clearing event and no cancel. **Beside them is a fourth event that is an act rather than a
  slot** — `PlanLocked`, from
  [ADR-0155](../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
  which supersedes ADR-0144's *there is no lock* and nothing else in it. **The count and the
  lock are two facts**: a complete plan is one everybody *could* agree, and `is_locked` is
  `locked_at is not None` and deliberately not `slot_count == SLOTS`. It announces itself where
  a completed plan may not — no arrangement of the three slots reaches *these people have
  agreed*, which is ADR-0142 §3's test and the one `GamePlanned` fails — and its whole
  destination is a **system line in the room**. It **freezes nothing** (a slot moved afterwards
  keeps the lock and writes its own line) and there is **no unlock**, for the same reason there
  is no clearing event. **And the lock waits for the court** (ADR-0164 §5): where, day and
  hour are proposals anybody on the court may make and move, whole or not, and *we are
  agreed* is refused with a code of its own — `the_court_is_not_whole`, beside
  `the_plan_is_not_complete` and asked before it — until every seat is accepted; a lock
  already taken survives a later departure. Whether the court is whole is a fact the
  aggregate borrows, exactly as `record_day` borrows the anchor. **Nothing derived is
  stored**: not the slot count, not the agreed point, and neither the anchor nor
  `planned_at` is ever written — `planned_at` keeps meaning *when it became a game*, and the
  plan writes to `games` at no point at all. **The horizon runs from an anchor that only
  moves later** (ADR-0164 §4): the challenge's send until the game exists, then the game's
  `planned_at`, so a day set by two of four stays valid when the court fills and the chips
  widen rather than shrink; it rides on the plan row as `anchor`. **The court being over is
  the only thing that freezes the slots** — the game leaving `AWAITING_ENTRY` once there is
  one, the challenge ending before there is — read through *one port asking one question*,
  `PlannableCourts`, which the Plan declares in its own words and contracts on
  `plan_demands.py`: *which courts is this player arranging, and which are history*, every
  challenge on which the reader holds an accepted, live seat, with the two refusals a write
  can produce, the anchor, and whether the court is whole. It is answered by
  `plans/infrastructure/plannable_courts.py`, which folds the challenge and, for a court that
  has become a game, the game, through the two providers' own ports — `conversation_demands`'
  *one rule read against two records* one context over — and its five answers (arranging,
  on and awaiting entry, history, not on it, left it) are each pinned in
  `tests/unit/test_plannable_courts_fold.py`. `games` no longer publishes `PlanningCourt`; the
  one thing it still asks of the Plan, `AgreedMoment`, is keyed by the challenge the game was
  opened from. And
  **one platform zone**, `Europe/Warsaw`, recorded as a locale assumption in the shape
  `availability.py`'s `_WEEKEND` already uses, with its falsifier named: the first shard
  whose players are somewhere else. The conversion goes through the kernel's `slot_start`
  and nowhere else — **a dead function comes alive**, since it was written for the booking
  grid the 2026-08-25 reset deleted and had no caller in `app/` until now.
  Three cross-module facts are deliberate and all run one way. `PLAN_HORIZON` **stays in
  `games/domain/windows.py` and `plans` imports it**, because its interlock with
  `ENTRY_GRACE` is the argument and two numbers whose relationship is the argument must not
  be separated; **`plans` reads `challenges` as it reads `games`**, through their ports and
  only in `infrastructure/` (ADR-0164 §3); and **`games` may not import the Plan**, which is
  ADR-0145 §4's *"beside that context without being let into it"* made checkable —
  `.importlinter` holds it, and `challenges` and `games` import neither the Plan nor each
  other's aggregates.
- **The live channel carries a nudge and a typing frame, and nothing else is on the wire**
  ([ADR-0147](../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
  [ADR-0156](../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
  `GET /conversations/{id}/stream` is the platform's **first real-time surface**, and it is
  Server-Sent Events on FastAPI's own `EventSourceResponse` — **zero new dependencies**,
  against a WebSocket path that starts with one and whose absence fails *silently*, since
  `uvicorn` is pinned without `[standard]` and would refuse the upgrade rather than erroring.
  Six things about it are load-bearing. **The frame is
  `{v, conversation_id, last_seq}` and never content**: the client fetches from **its own**
  high-water mark through the ordinary read path, so a lost frame is repaired by the next
  one for free, and *whether the UI may render what it did not read from the authoritative
  path* stops being a rule anybody keeps and becomes a thing the wire cannot express. **One
  mechanism carries messages and system lines alike** — a send publishes after its commit,
  and the room teller publishes after each line it writes, so there is no separate live-plan
  feature to build and none to defer. **Fan-out is Redis pub/sub keyed on the
  conversation**, on the subscriber's **own** client — the process's second, from
  `create_redis_subscriber_client`, whose read has no deadline because on a subscription
  waiting *is* the operation (#342). **Publisher soft, subscriber loud**: a publish happens
  after the entry is durable so an outage costs a room its liveness and never a message,
  while a dead subscriber **closes the stream**, because a chat that is not live has to look
  not-live. `/health` stays about the **process** for the same reason — a probe that pinged
  Redis would take sign-in down with the chat. **The stream closes at the access token's
  `exp`**, which keeps revocation prompt and makes reconnect run every fifteen minutes in
  production rather than only on deploys, so the hardest-to-test path cannot rot unnoticed;
  the gate and the first frame run in a **dependency**, before the response starts, which is
  also where the request's database session is closed so a fifteen-minute stream holds no
  connection. And **the envelope is declared on the route and generated** — ADR-0006 gets no
  exception — which needed `app/api/streaming.py`, a dated shim for a framework bug that
  drops a stream's item type on every `include_router`. The hole that remains is named: the
  checks cover the *declaration*, and nothing proves the emission.
  **The second frame is presence, and a heartbeat is the only honest shape for it**
  ([ADR-0156](../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
  `POST /conversations/{id}/typing` is a `204` gated exactly like the send — membership, then the
  hold, because an indicator is drawn on other people's screens — and there is deliberately no
  *stopped*: every way a client can vanish is a way a *stopped* fails to arrive, and each of them
  would leave a room saying somebody is typing for ever. **The TTL is the correctness mechanism and
  the only one**: `TYPING_TTL` sits above `TYPING_CADENCE` in `conversations/domain/live.py` with
  the ordering asserted at import, and the roster for a room is whatever has not expired. The store
  is Redis and **never Postgres** — a durable row would be the one fact here that outlives the room
  — with an index set beside the per-typist keys so a read is one keyed lookup and never a scan;
  that index is a **hint**, since a member is reported only if their own key is alive. **The frame
  moves no sequence**, which is the invariant: the heartbeat loads the room `to_read`, so the
  `FOR UPDATE` that mints a gapless `seq` is not taken by the act of typing, and it carries
  `player_ids` sorted by the sender with **the reader filtered out on the way out**. **The kind is
  the SSE `event:` name** — `nudge` and `typing` — so an unknown frame is dropped by the transport
  rather than by a branch, and `LIVE_CHANNEL_VERSION` **does not bump**. Naming an event costs the
  declaration back and it is bought back: the framework reads any `ServerSentEvent` as *this route
  builds its own frames*, so `app/api/streaming.py` reads the narrowed `data` off `LiveFrame`
  instead — without it, adding this would have deleted `LiveNudgeSchema` from `components.schemas`.
  And **this pair does *not* fail in opposite directions**: the roster read fails soft like the
  heartbeat, because it is a courtesy read on the **command** client — the one with a two-second
  deadline, asked once a second by every open stream — and failing it loud would let a merely slow
  store close every healthy stream on the platform.
- **A Player Score is what the platform watched, and two strands is what it can see**
  ([ADR-0140](../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
  `app/modules/player_score/` is the seventh context and the first that **keeps no record at
  all** — no aggregate, no repository, no table, no migration. It folds `games`' and
  `challenges`' published ports and does arithmetic over them, because a stored score would be a
  second place for *did that game happen* to be true and the copy is what gets believed. Four
  things about it are load-bearing. **Its port is `PublishedScoreQuery` and not
  `PlayerScoreQuery`** — the matcher's port of that name is the *demand* and this is the
  *publication*, and ADR-0137's rule applies: the cost of a shared word is paid by whoever
  arrives second. **Three of six strands are live and three are absent, never nought** — *keeps
  plans* and *settles up* have no provider, *sportsmanship* is published in its own right and
  the matcher may not read it, and a player with no record at all is absent from the answer,
  which is the one rule the demand suite is written around.
  **The published weights live in the context and never in a ruleset**, because a weight release
  must not change what somebody's own profile says about them; they sum to a hundred by
  arithmetic and not by rule — 85 for as long as a name was missing — since the blend
  renormalises over the strands present. And **reliability stopped being absent
  platform-wide**: `NoPlayerScoresExist` retired, `build_absent_terms` answers empty and lost its
  argument, a stood-down reliability is now `NOTHING_FROM_THEM`, and the evidence gate counts
  eight live terms rather than seven — excluding nobody, at a margin of zero rather than one.
- **A results strand counts answers, and never agreements**
  ([ADR-0160](../docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md)).
  `ReliabilityStrand.ANSWERS_RESULTS` is the third live strand, and the thing to hold in your
  head is that **it is not the strand ADR-0137 struck**. *Confirms results* counted agreements,
  and because silence already confirms a lone score it could only ever have counted
  disagreements — every denominator tried on it docked somebody ADR-0049 protects. This one
  counts **answers**: a counter scores exactly as an acceptance does, so disagreeing costs
  nothing and only silence is priced. Four things are load-bearing. **There is at most one
  opportunity per game and the opener has none** (`games/domain/answering.py`): the entry that
  says *we played* carries a score, so one side asks and the other answers, and once both sides
  have put a score up the argument is capped — filing the opener's silence would price
  **surrender**, which is docking somebody for disagreeing by a later route. **It is the only
  strand that forgets** — twelve months, a named exception to ADR-0140 §4, because turning up is
  a commitment somebody made and answering a score is a habit of opening an app; the window is
  `player_score`'s (`ANSWERED_RESULTS_WINDOW`) and crosses to `games` as an instant, it equals
  the matcher's `horizon_days` by choice, and since a provider may not read the consumer's
  ruleset the two spellings are held together by a **test** rather than by construction.
  **`min_observations` is a bar per strand** — five here, three everywhere else, exhaustive and
  refused if a key is missing — because raising the single number instead would take a newcomer
  with three games and three turn-ups from a full score to no score at all; the bar is the
  *matcher's* and the published figure still has none, which is deliberate: on the sheet the
  honesty mechanism is printing the fraction, and inside a ranking nobody can see it. And it is
  a **ruleset release**, `2026.09.08-a`, with the six-name vectors **restored rather than
  retuned** — ADR-0140 §7's rescaling of five survivors is undone exactly, the two offline gates
  move nothing but a version stamp because no corpus has a Player Score, and the whole claim is
  the one the report cannot print: every player with a record is re-mixed on deploy.
  `2026.08.26-a` is edited once more to say **nought** about a word it never knew.
- **Sportsmanship stores, and it is the first aggregate here that is not event-sourced**
  ([ADR-0158](../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)).
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
  me* — only *which of these cards are closed*, which is a fact about an act. **What this
  context publishes outward is a third port and never a method on that one**
  ([ADR-0158](../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)
  amendment, #382): `PublishedSportsmanshipQuery` answers the figure and how many different
  people it rests on for a reader, and a **coarse band** for the subject — two methods
  rather than one answer a caller narrows, because a use case that received the figure
  would already hold the subtraction ADR-0158 §2 refuses, whatever it then drew. The
  collapse costs that fold nothing, which is what the key bought: one row already is one
  person, so *the fifty most recent raters* is a `LIMIT` on a total order rather than a
  read-time collapse, and nothing is trimmed at either end. The band's edges are whole
  stars, coarsened from the **published** figure so a subject's step cannot land on the
  other side of an edge from what a reader sees. The word `stars` reaches no wire — the
  forbidden-fact sweep refuses that property name — so it crosses as `average` and
  `raters`. There are two reads here and neither touched the silence:
  `GET /api/v1/sportsmanship` lists the courts **waiting** for somebody's stars, as a game
  id and the people on it, and an open card is by definition one nobody has answered.
  It borrows one thing,
  `SettledCourts` over `games`' directory, whose adapter lives in **this** context the way
  `PlayerNames`' lives in `games`; *settled* there is narrowed to **played and over**,
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
  ([ADR-0159](../docs/adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)).
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
  **The metered rows are the fourth fact, and they are `player_score`'s live strands put
  on a wire for the first time** (#381, and a third of them with #383). Nothing new is
  computed: the raw counts already existed in that domain and the caller stopped throwing
  them away. Each row crosses as **its
  pair and its figure** — and that third number is where a strand parts company with the
  variety beside it: a strand's percentage is what the platform *acts* on, `StrandRatio.value`
  is derived in one place so a card, a profile and the matcher's evidence cannot print three
  roundings of one record, and a client dividing the pair would be the fourth. Variety prices
  no promise, so its division stays the client's. **The weights stay off the wire** — the blend
  arrives already taken, and a row carrying its weight would let a reader re-derive the pill and
  draw one strand as worth more than another. A player with no publishable strand has the
  **whole zone omitted**, a third absence asking a third question: not `skill`'s and not
  `variety`'s, since a plan that dissolved and a seat that ran out are opportunities and
  neither is a game anybody played. `SubjectReliability` is the eighth demand and the **first
  here whose provider reads a set** — `PublishedScoreQuery` answers about five hundred
  candidates for the matcher, and the narrowing to one person is the adapter's, which is the
  mirror of variety's fence. And `ReliabilityStrand` is the one name this context imports
  rather than respells: the engines are the pure layer every context reads and none owns —
  the argument `player_score` already made beside its own import contract — and the codes are
  on the player contract under that spelling already.
  **What other players said is the fifth fact and the first that depends on who is
  reading** (#382). Every other zone is one answer retitled for the subject; this is two —
  the figure and its count for a reader, a **coarse band and neither** for the person it is
  about, since an average beside a count is a subtraction that names each new rating and
  they know who they played. The split is on the **port** rather than in the assembler, so
  the sheet about you asks a question with no figure in its answer, and `PlayerRecord`
  refuses the pair beside `is_self` outright — the branch decides, the invariant makes a
  wrong branch loud. It takes **neither a sport nor an instant**, the only demand here that
  takes neither: nothing decays, because the window is fifty *people* and not fifty days.
  Its absence is the **fourth**, asking a fourth question — rating is a favour, ignoring a
  card costs nothing, and nothing records the omission, so a nought would publish a verdict
  nobody gave. The matcher reads none of it, held by an `.importlinter` contract, and a
  test walks the emitted contract to prove the words reach exactly one response type, which
  is where *it is not on search result cards* stopped being a promise.
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
  **Ten registers, and they are ten on purpose — one per kind of claim.**
  `app/bootstrap/matcher_demands.py` and `player_record_demands.py` hold the ports a
  *consumer* declares of contexts it does not write; `games_demands.py`,
  `rating_demands.py`, `player_score_demands.py` and `sportsmanship_demands.py` each hold
  the ports one *provider* publishes outward; `challenge_demands.py` holds
  what `challenges` demands of the **matcher** — the arrow's other direction, which
  arrived with the challenge detail read
  ([ADR-0143](../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md))
  — and `game_demands.py` holds the one thing `games` demands of it, the court's pairing
  ([ADR-0161](../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)), on its own list
  because `games_demands.py` is what that context *publishes* and a demand is the other kind
  of claim;
  `conversation_demands.py` holds what a **room** demands of the three contexts it is
  told by and reads from; and `plan_demands.py` holds what a **plan** demands — the courts
  a player may plan, folded over `challenges` and `games` (ADR-0164 §3), and one fact about
  a *person*. There is deliberately no *conversations provider* and no *plans provider*
  register, and there never will be: a conversation is told and tells nothing, and nothing
  on this side of the wire reads a plan **through a port the Plan declares** — `games` may
  not import it, and the card ladder that reads one is the client's `domain/`. The one fact
  `games` does read off a plan, its agreed moment, is `games`' **own** demand
  (`AgreedMoment`, on `game_demands.py`) that the Plan's adapter signs — the consumer
  contracts its own demand, which is the rule below from the other side (ADR-0162 §4).
  Neither has a consumer of a port it declares, so neither publishes one. **The Plan's court
  read used to be on somebody else's register and no longer is**, and the move is the rule
  rather than an exception to it: while a plan was the game's, *is this player on this
  game's court, and is that game still open to planning* was `games`' question about
  `games`' record, published there as `PlanningCourt` — a consumer contracting its own
  provider's port is the consumer marking its own homework. A plan is the challenge's, the
  question is about a court that may not have become a game yet, and no provider can answer
  it alone; so it is a **demand**, contracted by the consumer that declares it, which is
  `conversation_demands.py`'s shape exactly.
  Each register's exhaustiveness
  assertion is about its own kind of claim and would stop meaning anything with another
  kind in it — which is also the rule for the next one: **a new provider or a new consumer
  gets a new register, not a row in somebody else's**, and the first person to add a row
  should not have to guess which list it belongs in. The sportsmanship register is that
  rule being followed rather than restated: the sportsmanship figure could have been a row
  on the record's consumer list, and a provider's publication on a consumer's register is
  exactly what makes an exhaustiveness assertion a claim about something else. One port on
  the record's list has **three** implementations, which is what the suite has to be
  parameterised over: *where has this reader been shown this person* is a question three
  contexts each answer about themselves.
  **A row carries a builder, and not always over a bare session.** `challenge_demands.py`'s
  takes the two seams the platform supplies from outside a request — the process's
  candidate index and the exposure ledger behind Redis — because the pairing it contracts
  is recomputed through the whole scoring pipeline, and **no test in this repository needs
  Redis running**.
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
