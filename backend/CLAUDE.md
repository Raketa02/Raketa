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
  **decided** — and a match's court is not seeded at all: it is *granted*, by the ladder, on the
  way through the same use cases a request runs, so a seeded match holds a court exactly when
  its seats and its clock say it should.
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
  the order of its rungs *is* the specification. `kernel.next_wake()` lives beside it and
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
- **A category names its roof, and a court that gains one moves category.** The platform
  constrains **two** facts about a club-authored `CourtCategory` — its sport and its `Cover` —
  both required at construction with no default
  ([ADR-0090](../docs/adr/0090-a-category-names-its-roof-and-a-court-that-gains-one-moves-category.md),
  narrowing [ADR-0079](../docs/adr/0079-a-category-is-club-authored-and-it-is-the-priced-unit.md)).
  It is on the category and not on a court because `kernel.court_named_at` does not assign one
  until fifteen minutes before play, so a card composed on Monday for Thursday has no court to
  read a roof off. **The cover never changes and there is no operation that changes one**: a
  club that roofs a court has changed the *court*, so `move_court` closes its catalogue row and
  opens a new one, and the history #98 asked for is ADR-0077's series rather than a fourth
  versioned fact. `Cover` is **`kernel.Cover`**, because Clubs authors it and Now renders it and
  two declarations of a closed two-value set is a mapper between two spellings. Rows that
  predate the column were backfilled from the category's own **name**, once, in
  `0013_category_cover` — the one place the product may read a domain fact out of copy,
  precisely because it happens once and never on a read path; a silent name becomes `outdoor`,
  because that is the answer that never claims shelter a club did not declare.
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
- **The hold ladder is a write, and it runs inside the write that moved the match.** Whether
  a court *should* be kept aside is composed from the seats and the clock on every read
  (`kernel.court_hold`); *since when* one has been is `held_since`, which is stored because it
  cannot be derived ([ADR-0031](../docs/adr/0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)).
  `kernel.hold_move` is the only thing that may move them apart or back together, and
  `matches.ResolveCourtHold` is the only caller — **before the save, in the same transaction**,
  on every Matches write, enforced by an AST walk. Run afterwards or on the outbox and there is
  a window in which a stored record sits in the one combination the kernel refuses to read, and
  it arrives as a 500 on a home screen rather than as a red test. A grant that finds no free
  court records an **inventory loss** — ADR-0035's single story — rather than a hold with
  nothing behind it. `held_since` **outlives the reclaim that ends it**
  ([ADR-0089](../docs/adr/0089-held-since-outlives-the-reclaim-that-ends-it.md)): the club's cap
  is measured from it, so clearing it there would reset the clock that just fired and the court
  would flicker rather than go back on sale. Read *is a court kept aside* through
  `kernel.keeping_a_court`, never off either field alone.
- **The schedule is a column, and a wake is a look.** A match carries `next_wake_at` and
  `wake_reason`, **recomputed on every write** — in `SqlAlchemyMatchRepository._columns`, which
  is the one door every write goes through, so the obligation is structural rather than a rule
  N use cases have to remember. They are the **only** derived facts this table stores, and
  [ADR-0076](../docs/adr/0076-the-schedule-is-a-column-a-wake-is-a-look-and-there-is-no-list-of-boundaries.md)
  is the licence: *when does this match next change* is a function call, *which matches change
  in the next second* is a scan, and a function cannot be indexed. The partial index is on
  `next_wake_at IS NOT NULL` and **not** on the cancellation flags — that copy would be a
  second ladder, in SQL, where nothing type-checks it. **The handler never branches on
  `wake_reason`**: it re-derives, so a late look changes *when* we look and never *what we
  find*, and taking the same wake twice is looking twice. There is therefore **no table of
  handled keys** — the record's own schedule column is the ledger of what is outstanding, and
  a look that finds nothing still **re-arms** it, or the tick picks the row up again a second
  later for ever. **No list of boundaries exists in the timekeeper** and
  `tests/unit/test_timekeeper_holds_no_thresholds.py` reddens on one appearing: the ticket that
  specified this shipped its own boundary table and it was short by five, including the two
  that release a club's court. `next_wake_at` is **never serialised onto a card**
  (ADR-0053). **Three actors are asked on
  every look** — the hold ladder, the departure settlement, and the seat-claim reaper — in a
  line rather than in a loop, and none holds a threshold: all three read theirs off the kernel
  from inside the aggregate, so the walk above stays green.
- **A departure and the hole it leaves are two records, and an outcome only goes up.** A
  leaving writes a `Vacancy` — which seat, when, closed by whoever takes it — *and* a
  `Departure`, which is whose money it is
  ([ADR-0033](../docs/adr/0033-settlement-and-occupancy-are-independent.md)). A filler closes
  the **oldest open vacancy** and settles the **oldest unsettled departure**, and those are
  *not always the same one*: two FIFO traversals over one list, differing only in their
  filter, and the ADR names the single-pass version as the hazard — the symptom is *one
  player was never refunded*, months later, and never an error. Her money is **two payload
  forms** and never one with an optional amount (ADR-0072): reading an amount off
  `LeaverMoney` without narrowing does not typecheck, and the column is null rather than
  zero. `Departure.raise_to` is the **only** mutator of an outcome and cannot lower one, so
  *"nothing may reduce a settled outcome"* is a property of the type. The **quote** crosses on
  the command as a **label**, and a strictly worse outcome at apply time is refused with the
  new one; equal or better applies, which is why a forfeit quoted against a reversal goes
  through. A departure nobody filled forfeits at the **start** — the instant the aggregate
  refuses every seat move, and therefore derivably ADR-0030's *"no further seat event can
  change it"*, where its own illustration (the join cutoff) stopped being that on the day
  ADR-0081 made a running claim outlive it.
- **A seat is never taken until it is paid, and what a player takes while she pays is a seat
  claim.** Five minutes of exclusive right to buy **one seat**, and **its own record rather
  than a fourth seat state** ([ADR-0081](../docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)):
  the seat below a live claim is still `empty`, still absent from the fill count, still earning
  the match no court. That is what keeps the glossary's *"there is no window in which a seat is
  taken and unpaid by the taker"* true word for word — and `redeem_claim` takes and pays in
  **one** move, because a redemption that left a held-and-unpaid seat would open that window at
  the last step. **Live is composed, never latched**: unended *and* not yet expired, so a claim
  is over at its own instant whether or not a look has written the receipt — which is why the
  cross-match *one live claim per player* rule is a **query** and not a unique index, and why
  `open_claim` **reaps before it decides** (the write a stale row would block is the write that
  clears it). Its expiry is a **match wake** under `next_wake_at`, never a channel send, and
  `claimLapse` is first in `WakeReason` because it is the only threshold not measured from
  `start`. `joinCut` is read by `open_claim` and by nothing else: a running claim is honoured
  past it, which is the difference between a deadline and a trapdoor and costs one comparison.
  A **terminal** match never wakes, so all five endings call `end_claims_with_the_match` — one
  rule ends a claim, whatever ended it.
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
- **A sport she holds no rating at is a door, and the door is a block on the wire.**
  ADR-0084 closes the sport bar's one open cost: three of five chips lie to a one-sport
  player until she taps one, and *"the door is not a follow-up to the fixed row, it is the
  condition on it."* It is composed into the shelves list **in the position the ranked
  shelves would occupy** — never a flag, and never an inference the phone draws from absent
  shelves, which would fire wrongly on any day the city genuinely has nothing in a sport
  she *is* rated at. It occupies those shelves' position rather than sitting above them:
  unrated means `bestFit` / `sameLevel` and `fullWorthWaiting` are **absent**, because a
  player with no rating cannot be ranked. *New on Raketa* and *New clubs* still compose
  **beneath** it, which is the point rather than a leftover — the clubs are the argument
  for spending the two minutes. The block carries **which sentence** (`DoorCode`, two
  members) and neither the sport nor a destination: she named the sport on the request and
  still holds it, and the code determines the destination exactly as an act code does.
  Only a **named chip** produces one — `all` is *the sports she holds a rating at*, so it
  names none she is unrated at, and ADR-0084 puts a player holding no rating at all into
  the run itself rather than onto Now. The rating is asked **by pair**
  (`RatedSports.holds` → `SkillRatingRepository.exists_for`) and never as the set, and the
  parked-run read happens **only when a door is being drawn**, so the busiest path on the
  sport bar pays one lookup rather than a replay.
- **The enrolled strip is four rules and a fact per card, never a table of thirty-six.**
  The region a player is **committed** to
  ([ADR-0073](../docs/adr/0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md)):
  chronological with its order **fixed at composition**; **counting by money**, so seats
  *paid* and a held-and-unpaid seat are two numbers and every number a sentence prints is
  sent as that number; **one clock**, `kernel.card_clock`, which is *the next moment at which
  something happens to the viewer whether they act or not* — composed as the soonest boundary
  **the ladder itself reads**, which is `next_wake` minus the one boundary no rung reads, a
  claim's expiry, because a stranger's five minutes are not the viewer's; and a card that
  **lives twenty-four hours from the moment it closed**, which is `match_end` for a played
  match and `Match.closed_at` for the five endings, since no reader can date a cancellation.
  Everything else — a hold, a court's name, a refund, an owner's exposure, a score, a
  departure — is composed **exactly when the fact exists**, so no situation is named anywhere
  in the composition. A leaver is on the strip and **her departure is two payload forms**
  rather than one with a blank amount (ADR-0072). The **court's total** rides beside the
  spine's price because `{price} settled to the club` is the court's and has no audience.
  The strip names **no act and offers no exit** while none of the six receiving surfaces
  exists — ADR-0083's rule is *and a v1 surface can receive it*, and a door that will not
  open is worse than the gap. One consequence to know rather than discover: `playedNoScore`
  begins exactly where the tail ends, so **it never appears on Now**.
- **The ranked funnel is one pipeline and eligibility is exhaustive.** Shelves 1 and 2 run
  through retrieve → eligibility → score → floor → `FEED_ORDER` → diversity → cap
  ([ADR-0051](../docs/adr/0051-now-is-ordered-not-drawn.md), ADR-0036/0037), and the only
  thing separating them is one rule, one floor and one cap — *a lane is data, not a
  branch*. They may **never** be merged into one ordered list: a full match outranks the
  joinable version of itself, so the merged list would be topped by matches nobody can
  join. `exclusions()` answers the **set of rules a candidate failed**, so *evaluate all,
  never short-circuit* is the shape rather than a discipline; `WithinTravelCeiling` is in
  neither set and `NotSuppressed` is a v2 slot that runs and passes. `FEED_ORDER` is
  `[desc(fit), asc(start), asc(dist), asc(id)]` and its fourth comparator is load-bearing —
  without a total final key the order is the query plan, and two identical requests
  reshuffle the shelf under her thumb. **Diversity defers and never drops**; the cap is the
  only pass that removes a card. Floors 70 and 80, caps 6 and 3 — which is the 23 cards
  across four lanes both budgets are measured against (ADR-0085). Shelf 1 never goes
  silent: nothing over 70 **retitles** it to `sameLevel` and drops the floor, and the order
  does not change with the title, because closeness to her Level is what `desc(fit)`
  already leads on. **Nothing is random** — no seed, no draw, nothing recorded for replay —
  and there is **no player feed cache**, both asserted by walks with negative controls.
- **A snapshot is assembled here and nothing in `app/engines/` moves.** The shipped
  `matchfit` engine with its ten `TermCode`s is the fixed point (ADR-0036). What is decided
  on this side of the input contract: the **context cache**, keyed
  `matchId : recordVersion` and therefore never stale — no TTL, no `forget`, because the
  invalidation is already in the key — holding only what is expensive *and* viewer-
  independent, and living **behind** `CityMatches` rather than in front of it, since
  ADR-0068's *"the key is a fact about the viewer and the port's question is not"* inverts
  for a key filed under a match, and a cache above the port would build every context and
  then throw it away for the copy already held; a **travel sentinel** for a player the platform cannot locate
  (`Raketa02/Raketa#102`, ADR-0063), which is safe only because travel is a **constraint**
  term and nobody can declare a radius (`#105`), asserted as a property and **withheld from
  the badge's reasons**, since a number that ranks identically for every candidate is not a
  number that may be printed; **crowding computed** rather than defaulted, because it is
  *evidence* and multiplies into the score; and `phase=FORMING` **stated** with the guard it
  gives up reinstated through `invariant`, since `MATCH_PHASE_OF` calls a full match
  `LOCKED` and deriving it would make shelf 2 unbuildable. **Both engines are handed a
  minute-truncated `now`** — they refuse seconds, `SystemClock` reads microseconds, and
  before the truncation every live compose degraded silently. A scorer failure is one
  `Unscorable`, caught **once per screen**: shelf 1 falls back to soonest-first with no
  badge under `sameLevel`, shelf 2 is dropped, and **no marker crosses the wire**.
- **Shelves 4 and 5 cache the membership and never the row.** *New on Raketa* (30 days,
  cap 8) and *New clubs* (60 days, cap 6) are the only part of Now that does not run through
  the ranked funnel, and
  [ADR-0068](../docs/adr/0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md)
  splits them on one line: *who is new here* is the same answer for everybody in a city
  looking at one sport and is cached under `city : sport : kind`; *what a card prints* is
  read live. That is a **type** rather than a discipline — `ArrivalSets` holds
  `tuple[UUID, ...]`, so a nickname could not be cached by somebody widening a signature.
  The cache **expires after fifteen minutes and has no invalidation path at all**, which is
  the design and not a gap: against shelf clocks of 30 and 60 *days* the lag is
  imperceptible, and a `forget` is a second thing to keep in step with the truth. It is
  in-process and hangs off `app.state` — the one adapter in this app whose lifetime is the
  application's — because a Redis adapter would arrive with a client, a connection lifetime,
  a failure policy and a serialisation format that no test run can exercise. **Neither shelf
  has a floor** and both are ordered by a rule that is a claim about the shelf's own title:
  *New on Raketa* by **closeness to the viewer's Level and never descending** (descending is
  a leaderboard on a stranger's home screen), *New clubs* **newest first with distance
  breaking ties** (by distance, a shelf saying *this is new* would answer *this is near*). A
  questionnaire-derived Level carries **one boolean** and never a second number — the
  Confidence percentage on a card is the gauge ADR-0037 refused. The **city component of the
  key has no source yet** (`Raketa02/Raketa#102`) and resolves to `CITY_UNKNOWN`; it stays in
  the key rather than being added later, because a key that gains a component answers the
  wrong city for fifteen minutes on the day it lands.
- **The ledger is event-sourced, one stream per player, and it refuses to forget.** Money
  is the first racket-sport context to answer ADR-0002's per-context question with *yes*
  ([ADR-0055](../docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md)), and
  it is the mirror image of Matches' *no*: nothing about a movement is derived, and there
  is no current state of the money that is not a fold. The stream id is **derived** from
  the player, never minted and stored. A movement is `payer → payee` with a **strictly
  positive** amount — the direction is the parties, never the sign — and `balance`, `held`
  and Raketa's float are all folds stored nowhere
  ([ADR-0056](../docs/adr/0056-a-movement-has-two-parties-and-custody-follows-what-was-sold.md)
  retires `held: true` by name). **Custody follows what was sold**: an open match's share
  is held by Raketa until commit, a private court's passes through on arrival, and cash at
  a counter is the one `player → club` movement Raketa was never party to (ADR-0059).
  **Nothing is edited and nothing is deleted** — asserted by an AST walk
  (`tests/unit/test_money_is_append_only.py`), because the behavioural tests provably do
  not cover it: a prune dropping the oldest movements past a threshold no fixture reaches
  passes all 3108 of them, and takes the balance, `held` and the float with it. The walk
  refuses every write to the movement list but the one `append` that replays a stored
  event. A wrong movement is compensated by a
  second one under a `REV-` reference, carrying *its own* cause
  ([ADR-0057](../docs/adr/0057-every-movement-names-the-rule-that-caused-it.md)), and
  erasure replaces the player party on the way **out** rather than rewriting history. The
  eighteen causes are a **wider** enum than `kernel.Cause`'s five, with the shared names
  embedded by value and the inclusion asserted at module load: growing the kernel's would
  put thirteen ledger-only names on a wire enum both clients build an exhaustive table
  over. The three standing invariants live in `domain/invariants.py` and the nightly job
  and the test suite call the same functions; **it reports and never repairs**, and
  `ReconcileLedgers` takes no unit of work, so that is a property of its constructor rather
  than a rule to remember. **Money reads Matches; Matches never reads Money** — a fence in
  `.importlinter`, because a ledger read inside state derivation would make the situation
  ladder depend on a second aggregate's fold.
- **A seat payment is two transactions, and the order is the design.** `money.PayForASeat`
  is the join between Matches, Courts and Money
  ([ADR-0035](../docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md),
  [ADR-0055](../docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md),
  [ADR-0056](../docs/adr/0056-a-movement-has-two-parties-and-custody-follows-what-was-sold.md)).
  First the **seat, the reservation *or* the inventory loss, and both outbox rows**, closed
  together — *"a seat payment that earns a court, and the court it earns, are one event or
  they are a bug."* Then the **movement**, in a transaction of its own, because ADR-0055
  refuses a movement inside a match transaction: *"a card charge can fail after the match
  record is already correct."* **Matches runs first**, because a movement names the
  reservation that write produced, and because the seat write's refusal is what decides
  which chain is recorded. A process dying between the two leaves a paid seat with no
  movement — the safe direction, and a replayed report heals it, because the port answers
  *the seat is hers* for a seat that is **already** paid rather than reading it as gone and
  refunding a seat she is sitting on. **Custody follows what was sold and is the match's
  answer**; the **channel** — online, or cash across a counter — is the caller's, and the
  two meet in exactly one function. Money reaches Matches through `Seats`, a port of its
  own, so `tests/unit/test_money_events.py` still walks Money's domain and application
  layers and finds no other context in them. The reservation's half of the atomicity claim
  is in `tests/integration/`, and **not** by preference: pysqlite opens no transaction
  before a `SAVEPOINT`, so a reservation written inside ADR-0035's savepoint survives a
  rollback on SQLite and nowhere else.
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
is in [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally. **Money is modeled**
now, and it is event-sourced —
[ADR-0055](../docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md), the first
racket-sport context to go that way and so far the only one. Clubs, Courts, Bookings and
Matches are modeled and all four are **records with a
version**, decided by
[ADR-0077](../docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md),
[ADR-0035](../docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md) and
[ADR-0034](../docs/adr/0034-matches-is-a-record-and-keeps-no-history.md) — which is what a
genuinely per-context choice looks like once five contexts have made it.
