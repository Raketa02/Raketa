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
  its seats and its clock say it should. **The account named for an empty screen holds
  nothing**, refused at import and again against the stored seats on every run: the seats
  were filled from the head of the account catalog, so the one account a client's empty
  state is drawn from was sitting on every seeded match that had anybody on it — eight of
  the nine — and nothing about the cards it drew looked wrong.
- **The five catalogs are one week, and the assembly is a test rather than a builder.**
  `tests/api/test_demo_week.py` signs in over HTTP and composes Now at **one instant on the
  seeded week**, where one address has all three regions and every shelf a v1 server
  composes. It composes rather than requesting because the week is a fixed absolute week and
  the product reads the wall clock (`Raketa02/Raketa#134`). The two audiences no v1 flow can
  reach — the four private-owner situations and the leaver — are asserted there as
  **renderings**: that the card composes and says the right name, never a flow that arrives
  at it.
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
  The strip names **no act** while five of the six receiving surfaces are unbuilt —
  ADR-0083's rule is *and a v1 surface can receive it*, and a door that will not open is
  worse than the gap — and it offers **one exit**, because the sixth landed. One consequence
  to know rather than discover: `playedNoScore` begins exactly where the tail ends, so **it
  never appears on Now**.
- **A departure is a route off Now, and the card points at it without naming it.**
  `GET`/`POST /api/v1/matches/{matchId}/departure`, which is ADR-0074's shape *"deliberately
  and without variation"*
  ([ADR-0086](../docs/adr/0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)).
  It lives in **`now/`** although its path says `matches`: the answer is Now's vocabulary end
  to end and `now` already reads `matches` everywhere here, so putting it the other way would
  point the module graph both ways for the sake of a URL. It reaches the aggregate through
  `Departures`, a port of Now's own, exactly as `money.Seats` does. It prints **all four
  outcomes always** with a server-composed `OutcomeStanding` on each — two on a private court
  — and **no `phase` field**, because the standings answer what a phase would. `stillPossible`
  is not `opens` with the moment left out: **commitment is an event and never a clock**, so
  on a match that has not filled the money outcomes are a *fill* away and nothing can name
  the moment. The quote is `kernel.live_outcome` and the table is composed *from* it, never
  read back out of it. **`may_depart` is `kernel.may_depart`**, composed once in `card_of`
  so the strip's control and the route's boolean are one expression, and it is a **spine
  boolean rather than a seventh act** — leaving is not the card's act. **A refusal is not a
  second shape**: the quote falling, the match starting or cancelling, ADR-0046's lock, a
  second tap by somebody who has already left — all five answer with the recomposed screen,
  and only a stranger's 404 and somebody else's request key answer differently.
- **A queue place is a card, and leaving one is the first card that goes.** ADR-0087 gave
  `waitlisted` the seventh act and left it on a card that rendered nowhere — the strip
  answered a seat or a departure, the offers region answers an offer, and the shelves
  exclude a queued match by rule
  ([ADR-0091](../docs/adr/0091-a-queue-place-is-a-card-and-leaving-one-is-the-first-card-that-goes.md)).
  The strip now has a **fourth membership** and it confers nothing; the region's own copy
  says so — *you are queued, not committed*. The queue is a table keyed
  `(match_id, player_id)` and is **not part of the aggregate**: a join moves no state anybody
  contends for, and going through `Match` would bump ADR-0034's version and invalidate the
  scoring-context cache on every ask. It **announces nothing**, which is this context's one
  departure from *every change is its own named event* — that obligation is about a match
  somebody paid for, and the queue's single reader is the cascade, which reads the list when
  a seat frees. A place is **deleted rather than ended**, unlike every other child table here,
  because *rejoining costs what joining cost* is only true if nothing keeps a record of every
  time she changed her mind. `DELETE /api/v1/matches/{matchId}/standby` therefore refuses
  **nothing but the address**: anybody may queue for any match, so there is no membership to
  be a stranger to, and *deleting a place she does not hold* is answered by having nothing to
  check. **Nothing joins a queue in v1** — the waitlist toggle is a match-screen control and
  that screen is out of scope — so `JoinStandby` has the seed catalog as its only caller, the
  shape the four private-owner situations already take.
- **A result is a conversation on a route, and the ladder settles it rather than a write.**
  `GET`/`POST /api/v1/matches/{matchId}/result` and `POST …/result/acceptance`, ADR-0074's
  shape, in `now/` for the reason the departure route is
  ([ADR-0074](../docs/adr/0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md),
  [ADR-0060](../docs/adr/0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md),
  [ADR-0048](../docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)).
  It embeds the spine verbatim, resolves off the **same ladder** — five renderings, one
  reader — and is **not a card**. The result block is **four facts and no history**, always
  present and empty when nothing is on the table. **Two clocks, both named**, and the
  thirty-minute grace crosses only while it runs, because hiding it produces the outcome
  ADR-0048 built it to prevent inverted: the screen says *settled* half an hour early.
  **ADR-0048 replaced one constant with two** — `result_window` bounds every way a score
  arrives, which is what makes the forty-eight-hour outer bound arithmetic, and
  `settlement_deadline` is a property of the **proposal**, so a correction replaces it.
  **Silence is derived**: the ladder answers `completed` for a lone proposal past its
  deadline whether or not a wake has been round, and `result_agreed` is a receipt like the
  two cancellation flags — which is what makes the ordering ADR-0048 reversed real rather
  than dependent on a job. Two proposals settle nothing, and nothing is written for them.
  **Two writes, not ADR-0074's three**: entering, correcting and countering are one act at
  three moments and the aggregate tells them apart, because a client choosing between two
  endpoints would hold ADR-0048's cap as a rule. The three booleans are three **labels**
  over two sends, and every one of ADR-0048's permissions is enforced on the aggregate as
  well as composed on the screen — the lesson `#80` paid for. The validator **declines the
  obviously impossible and never the rulebook**, with a per-sport ceiling, and a bare
  rejection is refused by having no shape to send one in.

- **A seat that frees reaches somebody, in two dispatches over one ranked pool.** The
  invitation cascade ([ADR-0061](../docs/adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md),
  amending [ADR-0052](../docs/adr/0052-a-vacancy-is-offered-not-announced.md)) replaced the
  exclusive offer — and its hold, its three-offer cap and its twelve-hour backstop — with
  **one open call at every distance**, kept honest by the *wording* rather than by
  retraction: *a seat just opened, first to take it* is still true after somebody else takes
  it. It lives in **`now/`** for the reason the departure and result routes do. **Opening is
  synchronous and dispatching is not**: two rows join the departure's transaction, because a
  vacancy with no cascade behind it is a seat that dies quietly and nothing re-reads old
  vacancies; the pool, the rating replays and the scores are the dispatch's, on the tick the
  outbox already runs. The pool is **seven fact rules evaluated whole**, on
  `funnel.exclusions`'s shape and for its reason. **The band is the wall and it has no field
  behind it** — it is the pairing engine's `TargetBand`, the mean of the seated Levels, so
  *"the band the players who stayed signed up for"* is derived rather than stored and moves
  when the seats do; **no band is no wall**, because refusing everybody on a missing fact
  turns a hole into a seat nobody can ever be told about. The **rung dominates the fit** —
  ADR-0052 refused pure fit ranking by name, since under it joining a queue buys nothing —
  and three rungs ship **dark**, one of them (4) not named by the ADR because ADR-0085's
  *Recently viewed* store was never built. A **live seat claim leaves a wave due** rather
  than spending it, and nobody is told twice about one hole. `kernel.seat_price` is
  `refill_outcome`'s **mirror**, asserted as an equivalence: the leaver recovers what the
  filler paid. **The two tables are Now's first** — an offer changes nothing about the
  match, so ADR-0091's argument for keeping the queue out of the aggregate applies harder,
  and neither table announces anything.
- **The offers region is the cascade's output on a screen, and the refusal path is one
  expression.** Seats put in front of this viewer, **soonest-to-expire** —
  `cascade.seat_expires_at`, which is the join cutoff and the one instant `Match.open_claim`
  enforces — with no floor, no cap and no caption, all three because `OffersRegion` has
  nowhere to put them (ADR-0052, kept by ADR-0061). An offer is a **fact about the past** and
  a seat is not, so liveness is asked live through `cascade.seat_exclusions`, the four pool
  rules that are about the seat rather than about a candidate, written once and read from
  both ends. The region never re-asks the **candidate** half: withdrawing a seat by a rule
  she cannot see is what that ADR replaced retraction with wording to avoid. The card hands
  the ladder an offer **exactly while there is still a seat**, so one composer answers both
  *first to take it* and *the seat is gone*, and a refusal is what a success returns
  (ADR-0070) rather than a second shape.
- **`POST /api/v1/matches/{matchId}/seat` opens ADR-0081's five minutes, and refuses nothing
  but the address.** Anybody may buy a free seat in any match — `open_claim` is how *any*
  seat is taken from the marketplace. Six refusals answer with the recomposed card; **two
  answer 409 and both are about her rather than the seat** (she is buying elsewhere, or she
  let this one go thirty seconds ago), because neither can be said by recomposing a card
  about this match. Its answer is the **first** to carry ADR-0070's region slots — the offer
  is gone and the match belongs in the strip — and they ride **beside** the update, present
  exactly when `claimed` is true, so the two writes that move no region grow no field nobody
  fills. **The strip gained a fifth membership with it**: a live seat claim, or the match she
  has five minutes to pay for would be on no region of her screen at all.
- **One match is one card, and the strip is what yields.** A standby player is rung 1, so she
  holds a queue place *and* a live offer; the ladder settled which sentence wins by putting
  the seat above the queue that produced it, so `ComposeNow` composes the offers region first
  and hands the strip what it is already speaking for. The yield is narrowed to the
  membership that **confers nothing** — a seat, a departure or a claim is never taken off the
  strip by a region above it, so a disagreement costs a duplicate card rather than a missing
  one.
- **One message, one queue, and one line per player.** The push channel (ADR-0062,
  amended by [ADR-0065](../docs/adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)
  and [ADR-0067](../docs/adr/0067-the-quiet-replacement-is-evidenced-and-the-extra-message-waits.md))
  is the only thing in this backend that makes a phone light up, and it is the **fourth job**
  on the tick the outbox already runs — its **own queue**, because a send is not a change
  leaving the building. `push_lines` is one row per player, which is *one live message per
  player* expressed as a key, with the queue as a nullable `due_at` on the same row. **A
  notification is a prompt to look**: the sentence is past tense — *a padel seat just opened*
  — so it is still true after somebody else takes the seat, and there is nothing to withdraw,
  which is just as well because no platform offers server-side removal as a guarantee.
  `PushSender` therefore has **one method**, and the only deletion in the path is a device row
  whose token has moved to another account. The **named seat** is the one the line names and
  the rest are a count: a seat she *asked for* outranks one we chose, soonest-to-expire inside
  each group, ranked over her **whole live set on every send** rather than within one dispatch
  — which is what stops a chosen seat taking the line from a standby seat. **A message goes
  only when the named seat changes**; a count-only change sends nothing on either platform,
  because `IOS_COUNT_REFRESH` ships off until `#37` measures the APNs hop. Only a seat she
  asked for **buzzes** (iOS `time-sensitive`, otherwise `passive`); Android is **one channel**
  at `IMPORTANCE_HIGH` and Notification Policy Access is not requested. `timeSensitiveSetting`
  is stored and **branched on by nothing**, walked over the whole app. `push_body` is the one
  place this backend writes English — ADR-0075's exception stated by class, and the sentence
  walk is narrowed to that function rather than to its file — and it carries sport, time and
  travel time and **never the venue**, which is a property of `NamedSeat` rather than a rule:
  the value has no club on it. The transport is a **log until one is provisioned** (`#26`,
  `#37`), and travel time has no source at all (`#129`).
- **Now's update is one card in one of two forms.** `CardChanged` or `CardGone`, and the
  second is ADR-0070's *"the one-card answer must be able to say this card is no longer on
  your screen"*, produced for the first time by leaving standby — a departure **keeps** the
  leaver's card (ADR-0030), so nothing before it could. A **discriminated union** and not a
  nullable card, on ADR-0072's rule for the leaver's money: *it is gone* and *this build sent
  none* are opposite sentences and a blank cannot tell them apart. **Neither region slot is
  here yet**: a region belongs in an update when its *contents or order* change, a single card
  leaving is said by the form, and the first act that moves an order is taking a seat.
- **A destructive command carries a key, and the log is cross-cutting.** ADR-0030's
  `command_log`, keyed `(command, idempotency key)` — which is the table's primary key, so the
  collision is the database's answer. **Twenty-four hours applied on the read**, so
  correctness never waits on a sweep, and the **prune runs on the write** scoped to that
  command's own rows, so the table is bounded without a scheduler nobody built. It **does not
  commit**: the log row joins the transaction its command is written in, or the two can
  disagree — the one state that makes a replay dangerous rather than merely useless. The log
  records **what she got** and not what she asked for, because equal or better applies and a
  replay must hand back the outcome she actually had.
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
- **Two passes run over the composed screen, and both are about relationships between
  rows.** Shelf order → **repeat guard** → **emphasis**
  ([ADR-0032](../docs/adr/0032-now-is-one-screen.md), ADR-0037), in
  `now/domain/composition.py`, over the whole `NowScreen` and never inside `_blocks` —
  emphasis has to see the offers region and a list of blocks does not contain it. The guard
  drops a shelf only when **every** card on it is on the nearest shelf **still standing**;
  partial overlap is allowed, because two shelves make two different claims about one match.
  Emphasis is **at most one card on the whole screen**, the first in final composed order
  clearing fit ≥ 90 **and** coverage ≥ 80 % **and** a seat open, and **any offer silences it
  entirely**. The cap is the guarantee, not the thresholds. Only a ranked card can carry it,
  which falls out of `ComposeShelves` answering `Ranked` — shelves *and* the scores behind
  the cards they kept — rather than out of a rule; a degraded screen carries no scores and
  therefore no loud card, which is one fact and not two. The two passes **commute today**
  and that is asserted by exhaustive search rather than assumed, because it is a property of
  the drop condition and not of the passes.
- **Now has two budgets and they are not the same kind of thing**
  ([ADR-0069](../docs/adr/0069-the-budget-is-two-budgets-and-both-fail-the-build.md),
  ADR-0085), both in `tests/unit/test_now_budgets.py` and both measured on the fullest
  realistic screen — **23 cards across four lanes**, asserted rather than described.
  **Payload is a gate**: 150 KB uncompressed for the whole composed envelope, and going over
  **fails the build**; the answer to a red one is an ADR or a smaller card, never a bigger
  number. **Latency is reported and never asserted on**, with its conditions in the line —
  warm cache, 500 live city matches, 300 retrieved, 23 cards, and whether coverage was
  tracing, which moves the figure by more than a factor of two. The **cold** ceiling is not
  measurable from that suite at all, because the cold cost is the adapter's.
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
