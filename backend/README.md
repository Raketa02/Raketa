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
- Transactional outbox and embedded event-delivery worker — which is also **the
  timekeeper**: one tick, two indexed lookups, and no second process.
- `GET /api/v1/now` — the player's home screen composed in one request: three ordered
  regions, a card split into a spine and a situation half, and every code a generated enum.
  Its two light shelves — *New on Raketa* and *New clubs* — compose today, off a shared set
  cached for fifteen minutes and a row that never is.
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

That is why `app/modules/matches/domain/events.py` holds twenty-four names rather than one.
Nothing mechanical catches an event published too coarsely, so
`tests/unit/test_match_events.py` walks the aggregate with an AST and fails when a mutating
method announces nothing, and refuses a name that reads like *updated*.

### A category names its roof

ADR-0073 put indoor-or-outdoor **on the spine of every card**, and `#73` shipped it as a
required field of `PlaceResponse`. Nothing in the system could answer it: whether there was a
roof lived inside a category's free-text *name* — `Padel · indoor`, `Padel · Wall, outdoor` —
and a convention in a display string is not a fact. That blocked every ticket that composes a
match card.

`CourtCategory` now carries a `Cover`, **required, with no default**
([ADR-0090](../docs/adr/0090-a-category-names-its-roof-and-a-court-that-gains-one-moves-category.md)).
Three things about it are worth knowing:

- **It is on the category rather than on the court**, because `kernel.court_named_at` does not
  assign a court until fifteen minutes before play, so a card composed on Monday for Thursday
  has none to read. The category is already the priced unit and the thing a caller asks for,
  and ADR-0079 put the price there on the same argument: a court that costs differently is a
  different category, and so is one with a roof.
- **There is no operation to change it.** A club that roofs a court has changed the *court*, so
  the court **moves category** — `move_court` closes its catalogue row and opens a new one, and
  *this court gained a roof in October* reads back off the series ADR-0077 already built. So
  the category needs no history of its own, and `_update_categories` deliberately writes
  neither of the two facts the platform constrains.
- **`Cover` is the kernel's**, not Now's, because Clubs authors it and Now renders it. Two
  declarations of a closed two-value set is a mapper between two spellings of one fact.

Two values in v1, and a roof is `indoor`. *Covered but open-sided* reads as neither; the
question a card answers is *will I be rained on*, and a canopy answers it the way a wall does.
What it does not answer is *will I be cold* — a real loss, taken knowingly, because a third
value is an additive enum member **and a client release for its copy**.

Rows that predate the column were backfilled from the category's own name, once, in
`0013_category_cover`. That is the one place the product may read a domain fact out of copy,
precisely because it happens once and never on a read path; a name that declares nothing
becomes `outdoor`, because that is the answer that never claims shelter a club did not declare.

### A leaving is two records

A player who leaves writes **a vacancy and a departure**, and they are two facts on two axes
([ADR-0033](../docs/adr/0033-settlement-and-occupancy-are-independent.md)). The vacancy is the
hole the match now carries and the resolution ladder reads it. The departure is whose money it
is, and her card reads that.

They do not move together, and the place it shows is the filler. Taking a seat closes the
**oldest open vacancy** *and* settles the **oldest unsettled departure** — two traversals over
one list, differing only in their filter. ADR-0033 calls the single-pass version a real
implementation hazard, and the symptom is *one player was never refunded*, months later, and
never an error.

| Fact | Where | Closes when |
| --- | --- | --- |
| Vacancy | `match_vacancies` | anybody takes the seat |
| Departure | `match_departures` | no further seat event can change the outcome |

Four outcomes, ranked *refunded in full > refunded half > forfeited = reversed* — **forfeit
ties with a reversal**, because the quote protects money and in both cases the money is
nothing. Her money crosses in **two forms** rather than one with an optional amount
([ADR-0072](../docs/adr/0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md)):
reading an amount off `LeaverMoney` without narrowing does not typecheck, and the column is
null rather than zero.

`Departure.raise_to` is the only thing that moves an outcome and **cannot lower one**, so
ADR-0030's *"nothing may reduce a settled outcome"* is a property of the type rather than a
rule its callers remember. Three things move one: a filler pays, a club-side cancellation
refunds everybody, or the match reaches its **start** with the seat unfilled — which is the
timekeeper's second actor, and the reason a leaver's card ever stops saying *not yet decided*.

The **quote** is what makes two simultaneous leaves safe. The command carries the outcome
**label** the player was shown; the outcome is recomputed at apply time, and a strictly worse
one is refused with the new one attached. Equal or better applies.

### Buying a seat: five minutes, and never a fourth seat state

A seat is **never taken until it is paid**. What a player takes while she pays is a **seat
claim** — five minutes of exclusive right to buy one seat
([ADR-0081](../docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)) — and it is its own
short-lived record in `match_seat_claims`, never a state on the seat. The seat below a live
claim is still `empty`: absent from the fill count, earning the match no court, imputed by the
forecast rather than carrying the claimant's level. That is what keeps the glossary's *"there
is no window in which a seat is taken and unpaid by the taker"* true word for word — nobody
has taken a seat, they have taken the place in the queue in front of it.

| Rule | Where it lives | Why there |
| --- | --- | --- |
| Five minutes from the tap | `kernel.claim_expires_at` | three readers: the aggregate, the card's countdown, the schedule |
| Thirty seconds on the same seat | `kernel.claim_reopens_at` | the first rule in the system below a minute — see `Seconds` |
| One live claim in **this** match | `Match.open_claim` | a function of the record |
| One live claim **anywhere** | `SeatClaims.live_for` | no aggregate can see another one |
| A seat is spoken for | `kernel.claimed_seats` | the aggregate, the offer cascade and the card all ask |
| The expiry | `next_wake_at` | *"an expiry is a match wake, not a channel send"* |

**Live is composed, never latched** — unended *and* not yet expired — so a claim is over at its
own instant whether or not any look has written the receipt. Three consequences follow, and
each is the reason something is shaped the way it is:

- The cross-match rule is a **query**, not a unique index. A unique index would have to spell
  *live* as *unended*, and would refuse a player on the strength of a row nobody had closed.
- `open_claim` **reaps first**: the write a stale row would block is the write that clears it,
  so nobody waits on a scheduled look to be allowed to tap.
- A **lapse resumes the offer waves with no write at all**. The cascade's question about that
  seat simply gets a different answer, and nobody is told twice because nothing was retracted.

**One rule ends a claim, whatever ended it** — `SeatClaim.end` takes `min(at, expires_at)`, so
a reaper arriving late dates the lapse when it *happened*. A terminal match never wakes again,
so all five endings call `end_claims_with_the_match` rather than leaving a row nobody reaps.

`joinCut` is read by `open_claim` and by **nothing else**. A claim already running when the
cutoff passes is honoured to completion — somebody who tapped at 13:29 against a 13:30 cutoff
pays at 13:33 and plays — and only *starting* one is refused. That is the difference between a
deadline and a trapdoor, and it costs one comparison. Redeeming takes **and pays** the seat in
one move; a redemption that left a held-and-unpaid seat behind would open, at the last step,
the window this whole record exists to close.

`Match.as_record()` hands the kernel a `MatchRecord` and **needs no other read**: the club's
four hold-policy fields are copied at posting and honoured *as booked*
([ADR-0077](../docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md)),
so a situation is one row-set away with no club fetch on Now's path. The cost is real and is
stated rather than hidden — a club that tightens its cap does not reach a match already
posted, and the hold ladder did **not** change that: the fix, if it is ever needed, is a write
that refreshes the snapshot with an announcement of its own rather than a club read on the
compose path.

### The ledger: one stream per player, and it refuses to forget

Money is the **one racket-sport context that is event-sourced**
([ADR-0055](../docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md)) — the
mirror image of Matches' answer, on the same per-context question. Nothing about a movement
is derived and there is no current state of the money that is not a fold, so a row with an
`amount` that can be updated would be exactly the dual write ADR-0017 refused.

**It adds no table.** A ledger *is* its stream: `app/modules/money/` has no ORM model and no
migration, and the one cross-stream read it needs — every ledger, for the nightly assertion —
is a scan the event store already answers. A projection is ADR-0018's escape hatch for the
day tens of rows becomes thousands, not a default.

| What | Where | Note |
| --- | --- | --- |
| The stream id | `money.ledger_stream_id` | `uuid5(namespace, player)` — derived, never stored |
| A movement | `money.Movement` | `payer → payee`, **strictly positive** grosze, seat, reservation, reference, cause |
| The parties | `money.Party` | `PlayerParty \| ClubParty \| RaketaParty`; a club is never a payer |
| Why it moved | `money.MovementCause` | eighteen closed names, `kernel.Cause`'s five embedded by value |
| What a cause decides | `money.CAUSE_RULES` | total table: *moves the balance?* · *names a seat?* |
| The balance | `Ledger.balance` | zero or negative; two causes reach it and nothing clamps it |
| Held, and the float | `Ledger.held_for`, `Ledger.raketa_float` | ADR-0056's own formula, stored nowhere |
| The three invariants | `money.LEDGER_INVARIANTS` | the job and the suite call the same functions |

**Custody follows what was sold**, and the two regimes are two different chains for the same
30 zł:

| Path | On arrival | `held_for(seat)` |
| --- | --- | --- |
| Open match | `player → Raketa` — nothing is booked yet | the share, until the match commits |
| Private split court | `player → Raketa`, then `Raketa → club`, in one write | zero |
| Cash at a counter | `player → club` — Raketa is neither party | zero |

### A seat payment: two transactions, and the order is the design

`money.PayForASeat` is the join between Matches, Courts and Money — the place a partial write
would leave a player holding a paid seat in a match with no court and no record of why.

| Order | What closes together | Why not the other |
| --- | --- | --- |
| 1 | the seat, the reservation **or** the inventory loss, and both outbox rows | ADR-0035: *"a seat payment that earns a court, and the court it earns, are one event or they are a bug"* |
| 2 | the movement, or the movement **and** its reversal | ADR-0055: *"no movement is ever written inside a match transaction"* — a card charge can fail after the match record is already correct |

**Matches runs first**, because a movement names the reservation *that* write produced, and
because the seat write's refusal is what decides which chain gets recorded. A process dying
between the two leaves a paid seat with no movement — the safe direction — and a replayed
report heals it: the port answers *the seat is hers* for a seat that is **already** paid,
rather than reading it as gone and refunding a seat she is sitting on.

**Custody is the match's answer; the channel is the caller's.** What was sold decides whether
the money is held or passed through, so no payer, provider or club can move it; where the money
came through — online, or cash across a counter — is the only half a caller knows. They meet in
one function and neither answers alone.

Money reaches Matches through `Seats`, a port of its own answered from
`money/infrastructure/`, so ADR-0055's one-way fence holds at the layers where the rules are.
Money arriving for a seat that has gone is a `shareOnline` and its `REV-`/`claimLapsed`
reversal **in one append**; a counter mark for a seat she no longer holds is refused outright,
because reversing it would debit the club and *the club is only ever paid* (ADR-0045,
ADR-0059) — the club returns the cash at the counter.

**Nothing is edited and nothing is deleted.** A wrong movement is corrected by a second one
with the parties reversed, under a `REV-` reference, carrying *its own* cause — the reason the
correction was needed is not the reason the original happened. Erasure appends
`PlayerPseudonymised` and every movement the aggregate hands out thereafter names an opaque id
in the player's place; the stored events are untouched, because rewriting them is the one
thing an append-only store cannot do.

**The reconciliation reports and never repairs.** `ReconcileLedgers` is constructed with the
repository and a clock and **no unit of work**, so there is no transaction for it to commit —
*"a ledger that repairs itself has destroyed the evidence of the bug that made the repair
necessary."* A breach is one ERROR line naming the invariant, the ledger, the subject and the
arithmetic; a sound run logs too, because a check that only speaks when something is wrong is
indistinguishable from one that has stopped running.

**`held` and the float can be negative on a seat**, and that is the working-capital position
ADR-0045 names: a refund Raketa advanced on the private path, before the owner charge that
recovers it. The seat-chain invariant is therefore *no seat settles more to a club than the
player funded for it* — ADR-0056's *broken split* — and deliberately says nothing about the
advance, which closes across a reservation once a movement no context writes yet lands.

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

### The timekeeper

Now has moments nobody is looking at when they arrive: a commitment deadline passing, a
court's soft hold lapsing. The schedule for them **is a column** — `matches.next_wake_at` and
`matches.wake_reason`, under a partial index over the rows that have one
([ADR-0076](../docs/adr/0076-the-schedule-is-a-column-a-wake-is-a-look-and-there-is-no-list-of-boundaries.md)).
There is no queue table, no timer store, and Redis stays declared and unused.

Three things are worth knowing before touching it.

**It is recomputed on every write, and the one place that is structurally true is the
repository.** `SqlAlchemyMatchRepository._columns` builds the values for both `add` and
`save`, and there is no third door into the table, so a new use case cannot forget. It has to
be every write rather than every write that moves a deadline: the candidate set is a function
of the *record*, so a match on two paid seats wakes at T−12h and the same match after a third
payment wakes at T−4h with nothing about its calendar having changed.

**A wake is a look, not an instruction.** `TakeMatchWake` re-derives from the record and the
clock and never reads the `wake_reason` it was handed — that reason was computed at a past
write and the match may have moved since. Two consequences fall out. A **late** wake produces
what an on-time one would have, which is what makes at-least-once scheduling affordable with
no leader election and no distributed lock. And a **duplicate** wake is a no-op, because the
first look already moved the record — so there is no table of handled keys anywhere, and the
match's own schedule column is the ledger of what is outstanding.

**A look that finds nothing still re-arms.** The hold ladder is deliberately silent when it
has no move to make, and a row left naming a moment that has passed is one the tick picks up
again a second later, for ever. `MatchSchedule.re_arm` writes the two columns **without
bumping the version and without announcing anything** — the schedule is derived, so moving it
is not a change a support agent would need explained — guarded on the version the row was read
at, so a real writer that moved the match in between keeps its own, better answer.

Two rules about where thresholds may live:

- **The index predicate is `next_wake_at IS NOT NULL`**, not a SQL restatement of the four
  cancellation flags. Both spell *non-terminal* today; the second is a second ladder
  ([ADR-0040](../docs/adr/0040-one-ladder-resolves-a-situation.md)) in the one place nothing
  type-checks it, and it fails silently — the predicate here over-covers by a page, while a
  drifted copy of terminality leaves a due row unindexed and a club's court held for ever.
- **No list of boundaries exists in the timekeeper**, and
  `tests/unit/test_timekeeper_holds_no_thresholds.py` reddens on one appearing — a duration
  written down, arithmetic on an instant, or a reach for a kernel function that *produces* a
  boundary rather than the one that chooses between them. The ticket that specified this
  shipped its own boundary table and it was short by five, including the two that release a
  club's court. Nobody was careless: a hand-maintained table cannot track a set that is a
  function of the record.

`next_wake_at` is **internal and never serialised onto a card**. It is the earliest instant
*anything* could differ, chosen by a `min()` over candidates the player is not being told
about, and a countdown pointed at it drifts away from the words above it
([ADR-0053](../docs/adr/0053-the-phone-holds-no-rules-and-only-subtracts.md)).

The third of ADR-0076's *"three queries, one tick"* — the notification channel's scheduled
sends — arrives with its queue (`Raketa02/Raketa#84`). Its table has no reader yet, and a
table with no reader is not forwards-compatibility
([ADR-0071](../docs/adr/0071-two-fields-with-no-reader-are-not-forwards-compatibility.md)).

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
| `CommandLog` | What a destructive command already did, for 24 h | `SqlAlchemyCommandLog` |

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
| `GET` | `/api/v1/matches/{matchId}/departure` | Bearer access token | What leaving this match is worth, and what it could still become. |
| `POST` | `/api/v1/matches/{matchId}/departure` | Bearer access token | Leave at the quoted outcome; returns this screen and Now's update. |
| `DELETE` | `/api/v1/matches/{matchId}/standby` | Bearer access token | Leave this match's standby queue; returns Now's update. |

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
| `shelves` | the server's fixed list of **blocks** | present, `shelves: []` |
| `debt` | what she owes, and the one consequence | **absent** (`null`) |

That asymmetry is the rule, not an accident. A **region** with nothing in it is present and
empty; a **shelf** with nothing in it is **absent**, because a shelf makes a claim and a row
appearing every week to say *nothing worth waiting for* is a row players learn to scroll
past. The debt line is absent rather than zero, so the client never compares an amount to
decide whether to draw it.

**The regions fill one ticket at a time and the envelope never moves.** The route shipped
with all three empty so both clients could compile against it. What composes today is the
**enrolled strip**, the shelves region's last two shelves — the two that do not run through
the ranked funnel — and, for a sport the viewer holds no rating at, the door. The offers
region is the invitation cascade's.

#### The enrolled strip: her own matches, counted in money

The region a player is **committed** to, above the suggestions and never ordered by
quality. Four rules run over it, and each is *one* rule rather than a table of thirty-six
judgements (ADR-0073):

| Rule | What it says |
|---|---|
| **Order** | Chronological, and fixed at composition, so a card never moves as she reaches for it |
| **Counting** | Seats **paid**, with a held-and-unpaid seat as **its own number** beside that count |
| **Clock** | *The next moment at which something happens to the viewer whether they act or not* |
| **Tail** | A card lives **24 hours from the moment it closed**, not from when the match would have ended |

**Enrolment is a relationship, not an object.** There is no enrolment row: her matches are
a seat that names her, a departure that does, *or a standby place she holds*. ADR-0030's leaver is an audience of the
same card — *"the leaver's card is the match's card rendered for somebody who used to hold
a seat"* — so she keeps a card, and it keeps showing the match's progress, because a refill
is the only thing that decides her refund. Her money rides beside the situation in **two
payload forms**, `recoverable` and `nothingTaken`, and never as one with an amount that is
sometimes absent.

**The clock is `kernel.card_clock`**, and it is the soonest boundary **the ladder itself
reads** ahead of now. That is `next_wake` minus exactly one thing — a seat claim's expiry,
which no rung reads — because a stranger's five minutes are not this viewer's; her own
claim is passed in and wins outright. A terminal match has no boundaries at all, so *over
or cancelled counts to nothing* is a consequence rather than a case.

**The tail needs a stored fact.** A played match closed at `match_end` and a reader can
derive that; a cancelled one closed when somebody cancelled it and no reader can, so all
five endings write `Match.closed_at`. One consequence is worth knowing rather than
discovering: `playedNoScore` begins exactly at `matchEnd + 24 h`, so it **never appears on
Now** — it is the result route's rendering.

Everything else a card carries is composed **exactly when the fact exists**, so no
situation is named anywhere in the composition: the hold and its age, the specific court
(only from fifteen minutes before play), the cancellation's cause, a refund with the
destination that fixes its tense, a private court's two figures, and the score with both
sides named and the viewer's first.

**The strip has a fourth membership, and it confers nothing.** A queue place puts the
match on the strip as `waitlisted`, because that is the only region on Now that could hold
the card: the offers region is seats offered to her, and the ranked shelves exclude a
queued match by rule
([ADR-0091](../docs/adr/0091-a-queue-place-is-a-card-and-leaving-one-is-the-first-card-that-goes.md)).
The region's own copy admits the exception — *you are queued, not committed*.

**The strip names one act and offers one exit.** ADR-0083's rule is *a card names an act
when the viewer can take it now **and a v1 surface can receive it***, and of the seven
receiving surfaces two now exist: the departure route (`#80`), whose control is a spine
boolean rather than an act, and the standby write (`#81`), which is why a `waitlisted` card
names `leaveStandby`. The seat claim (`#89`), the result route (`#79`), Find (`#115`) and
the Getting-in sheet are unbuilt, so their acts stay absent — a door offered that will not
open is worse than the gap.

#### The door into a sport you have no rating at

A player who taps a chip for a sport she holds no rating at gets a **door** into that
sport's questionnaire, in the position the ranked shelves would occupy — so the app
answers *how do I get squash matches* instead of showing her a blank screen (ADR-0084).

```json
{ "block_type": "door", "code": "noRunYet" }
```

Each entry in `shelves` therefore carries `block_type`, one of `shelf · door`, and the
list is a **discriminated union** — the same shape a card's `card_type` takes one ring in.

- **The door is a block the server composed**, never a flag and never an inference the
  phone draws from absent shelves. An inference would fire wrongly on any day the city
  genuinely has nothing in a sport she *is* rated at, and the phone holds no rules.
- **It takes those shelves' position rather than sitting above them.** Unrated means
  `bestFit` / `sameLevel` and `fullWorthWaiting` are **absent**: she cannot be ranked
  against matches in a sport the platform holds no Level for her at.
- **`newPlayers` and `newClubs` still compose beneath it**, and that is the point rather
  than a leftover — the clubs are the argument for spending the two minutes, so they
  belong under the ask.
- **`code` names which sentence**, in two members: `noRunYet` and `runParked`. One block
  type, so the client holds one row per sentence and never learns that two states produced
  them. A parked run never expires, so this is existence and never freshness.
- **Neither the sport nor a destination crosses**: she named the sport on the request and
  still holds it, and the code determines the destination exactly as an act code does.
- **Only a named chip produces one.** `all` means the sports she holds a rating at, so it
  names none she is unrated at; a player holding no rating at all belongs in the run
  itself rather than on Now.

The rating is asked **by pair** — `RatedSports.holds`, over the rating context's
`exists_for` — and never as the set, and the parked-run read happens **only when a door is
being drawn**. A named chip is the busiest path on the sport bar and pays one lookup for
the door rather than a replay of every rating she holds.

#### The ranked funnel: *Best fit for you* and *Full, but worth waiting for*

| Shelf | Holds | Floor | Cap | Seat rule |
|---|---|---|---|---|
| `bestFit` / `sameLevel` | open matches the viewer could join | **70** (none when retitled) | **6** | `HasFreeSeat` |
| `fullWorthWaiting` | full future matches | **80** | **3** | `IsFull` |

**One pipeline, two shelves**: retrieve → eligibility → score → floor → `FEED_ORDER` →
diversity → cap. What separates them is one eligibility rule, one floor and one cap, which
is ADR-0051's *a lane is data, not a branch*. They may **never** be merged into one ordered
list — a full match outranks the joinable version of itself, because being full is the
strongest available evidence the match will be played and viability is the one term that
can never be excluded, so the merged list would be topped by matches nobody can join.

**Eligibility is exhaustive.** `exclusions()` answers the set of rules a candidate
*failed*, not a boolean, so nothing can be written as a chain that stops at the first
`False` — and the operational difference between *seven of them already full* and *seven of
them already mine* survives. The eight common rules are `NotAlreadyMine`, `StartsInFuture`,
`BeforeJoinCutoff`, `NotCancelled`, `SportMatchesFilter`, `NoScheduleConflict`,
`NotSuppressed` and `NotOnStandby`. `WithinTravelCeiling` is in **neither** set: travel is
a weight-8 term that never excludes at any distance. `NotSuppressed` is a v2 slot that
**runs and passes** rather than one waiting to be added, and `NotOnStandby` tests against a
port that answers empty for every player, because standby has no store anywhere in the
product yet (`Raketa02/Raketa#81`, `#82`).

**`FEED_ORDER` is `[desc(fit), asc(start), asc(dist), asc(id)]`**, the total base order,
with every later pass a named delta over it. The fourth comparator is not decoration:
without a guaranteed-total final key the order falls back on retrieval order, which is the
query plan, and two identical requests reshuffle the shelf under the player's thumb. An
unknown distance — which is every viewer's today — sorts **last** rather than first.

**Diversity defers and never drops.** At most two cards from one club in one hour sit
together; the third goes to the back of the shelf. The prototype dropped it, and could
return fewer than the cap with cards still waiting.

**Shelf 1 never goes silent.** When nothing clears 70 it keeps its cards, drops its floor
and becomes `sameLevel`. That is what makes a floor affordable at all: an unfillable shelf
is *absent* rather than empty, so no card claims the city is empty.

**One cache, and it cannot be stale.** The *match scoring context* — the record, the club's
facts, its saturation and the seated players' ratings — is everything that is expensive
*and* the same for everybody looking at that match, filed under `matchId : recordVersion`.
A seat payment bumps the version and the next ask files under a key nobody wrote, so there
is no TTL, no reverse index and no `forget`. Every viewer-relative fact stays outside it.

It sits **behind** the retrieval port and not in front of it, which is the opposite of where
ADR-0068 puts the new-arrivals cache — and that ADR's own line is the reason: *"the key is a
fact about the viewer and the port's question is not."* That holds for a set filed under a
city and inverts for a context filed under a match, and it is not a stylistic choice — above
the port the adapter would run every reservation query and every rating replay and the
composer would then discard the result for the copy already held, which is a cache that
saves nothing at all. Asked before anything expensive happens, a warm screen pays the club
lookup and stops.

**There is no player feed cache** (ADR-0068): every ask pays the full funnel, because that
was the only store on this screen keyed on the person asking.

**Travel is a sentinel and crowding is computed**, and the asymmetry is the point.
`ClubSnapshot` requires both with no default. Travel is a *constraint* term, so an
undeclared radius is genuinely no limit and the term scores full marks whatever the minutes
are — and no player can declare a radius, because the preferences editor has no screen and
no contract (`#105`). So the sentinel provably moves no score and no order, which is
asserted as a property rather than argued. It **may rank and may never be printed**: a
travel *reason* is withheld from the badge, since *"20 minutes away"* drawn from a sentinel
is a claim about a journey nobody measured. Crowding is *evidence* and multiplies straight
into the score, so it is a real query — the club's live courts against the reservations
touching the match's window, paid once per club and hour.

**Degrade is caught once per screen.** Any engine failure becomes one `Unscorable`; shelf 1
falls back to soonest-first with no badge under the `sameLevel` code — the thin-week
fallback, so the degraded screen is one players have already seen — and shelf 2 is dropped,
because an 80 floor with no scorer is not a claim we can make. **No degrade marker crosses
the wire**: a flag would be a fact about our infrastructure printed on a player's home
screen.

**The badge** always carries a number clamped to 20–99 at display time, up to three reasons
as term codes with their **typed fact payloads**, a warning boolean read off the engine's
own threshold, and the aimed-at Level **only when it is precise** — the seat target, which
exists while exactly one seat is open. Coverage never crosses in any form. The badge is
withheld entirely from a viewer with no rating at that sport, and her list is still ranked
by the score.

**Nothing is random.** No seed, no draw, nothing recorded for replay — asserted by a walk
over the feature's own source with a negative control.

#### *New on Raketa* and *New clubs*

| Shelf | Holds | Window | Cap | Floor | Order |
|---|---|---|---|---|---|
| `newPlayers` | players rated at the selected sport | 30 days | 8 | none | closeness to the viewer's Level |
| `newClubs` | clubs with a live court in a live category for it | 60 days | 6 | none | newest first, distance breaking ties |

Both orders are claims about the shelf's own title. *New on Raketa* is ordered by
**closeness and never descending by Level**: descending makes the shelf a leaderboard,
telling every new player where they rank on the home screen of every stranger in the city.
*New clubs* is **newest first and never nearest**, because a shelf saying *this is new*
must not answer *this is near*. Neither has a floor — there is no such thing as a player
who is insufficiently new — so a viewer the platform cannot compare anybody against still
gets a shelf, with the incomparable at the back.

A person card carries a **Level and one boolean**. The boolean means *a questionnaire is
the whole evidence behind this*, and it is a boolean rather than a second number because
onboarding cannot produce Confidence above 30 % and a 3,2 from six questions is visually
identical to a 3,4 from eleven matches.

**The membership is cached and the row is not** (ADR-0068). *Who is new here* is the same
answer for everybody in a city looking at one sport, so it is stored as a set of ids under
`city : sport : kind` for **fifteen minutes**; what a card prints is read live, so a
renamed club reaches the next screen. That split is a type — the store holds
`tuple[UUID, ...]` — rather than a rule somebody has to remember.

The cache **has no invalidation path at all**, and that is the design. Against shelf clocks
of thirty and sixty *days*, a quarter of an hour of lag is imperceptible, and a cache with
nothing to invalidate is the one shape that cannot go wrong. Its visible cost is asserted
rather than left implicit: `tests/api/test_now_shelves.py` has a club that registers after
a compose and waits for the TTL.

It lives **in this process**, on `app.state`, which is a deviation from ADR-0068's *"Redis
and Celery are already backend dependencies, so both caches have a home"*. Redis has no
importer anywhere in this tree, so a Redis adapter would arrive with a client, a connection
lifetime, a failure policy and a serialisation format that no test run can exercise. What
ships is the port and a store that is correct: N workers pay N misses instead of one, and
each answers from a real query. The seam is one line in the composition root.

**The key's city component has no source yet.** ADR-0063 makes *where you play* a declared
fact about the player and no context stores one (`Raketa02/Raketa#102`), so every compose
files under `CITY_UNKNOWN`. The component stays in the key rather than being added the day
the fact lands — a key that *gains* a component is a key whose old entries answer the wrong
city for fifteen minutes.

#### Composition: two passes over the screen, and two budgets over the answer

Once every region and every shelf exists, two passes run over the whole composed screen —
**shelf order → repeat guard → emphasis** — because neither question can be answered where
its subject was built. A shelf cannot know it repeats the shelf above it, and a card cannot
know it is the only one allowed to shout.

**The repeat guard** drops a shelf when **every** card on it is already on the nearest
shelf still standing. Partial overlap is allowed and a match may sit on two shelves: two
shelves make two different claims about one match, and hiding a good match for having been
mentioned is worse than mentioning it twice. It cannot fire on today's four lanes — a free
seat against full is one exclusive rule, and people against clubs are two card types — so
it is written for `recentlyViewed`, which is reserved with no producer and would arrive as
a *server* change (ADR-0085), with no chance to add the guard on the way in.

**Emphasis is at most one card on the whole screen**: the first in final composed order
clearing fit ≥ 90 **and** coverage ≥ 80 % **and** a seat open, and **any offer on the screen
silences it entirely**. The cap is the guarantee rather than the thresholds — whatever real
scores turn out to do, the one loud colour cannot become wallpaper, which is what keeps
ADR-0037's *coral is never decorative* true without amendment. Only a ranked card can carry
it, and that is a consequence rather than a rule: `ComposeShelves` answers a `Ranked` — its
shelves **and** the scores behind the cards they kept — so the strip, the arrival shelves
and a degraded screen have nothing to gate on.

**The payload budget fails the build.** 150 KB uncompressed for the whole composed
envelope, measured on the fullest realistic screen at **23 cards across four lanes**
(ADR-0069, ADR-0085). It is a gate rather than a log line for the reason the ceiling exists
at all: one that only advises can be reasoned past a defensible field at a time. The
envelope is weighed through `NowResponse`'s own serialiser, and `tests/api/test_now.py`
asserts that what the route renders is byte-for-byte what that serialiser renders.

**The latency figure is reported and does not fail.** p99 ≤ 150 ms warm and 250 ms cold are
ADR-0069's stated gate; what the build prints is a measurement **with its conditions beside
it** — warm context cache, 500 live city matches of which retrieval answers the soonest 300,
23 cards, the sample count, and whether coverage was tracing. Naming the conditions is the
load-bearing half: a p99 against a cold cache measures the cache, and the same suite under
`--cov` and under `--no-cov` reports numbers that differ by more than the gate's headroom.
The **cold** figure is not measured at all, because the cold cost is the context adapter's
and that suite has no database. It becomes a gate when there is something profileable to
gate.

Every number in ADR-0069's table is modelled and none has ever been measured. This is the
first measurement, and it is allowed to find the shape wrong rather than the numbers.

### `GET` / `POST /api/v1/matches/{matchId}/departure`

The first action taken **off** Now, and ADR-0074's shape without variation
([ADR-0086](../docs/adr/0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)).
It states what leaving is worth right now, and the route *is* the confirmation: one button
carrying the quote, no third step, and she is not asked twice — a dialog over a screen whose
whole job is to state the consequence asks the same question twice.

**All four outcomes print, always**, each with a server-composed standing:

| Standing | What it says |
|---|---|
| `searching` | the live quote — leaving now is worth this, and the cascade looks at that price |
| `opens` | it becomes the quote at a moment already fixed, carried as `opens_at` |
| `stillPossible` | reachable, with **no moment to name** |
| `spent` | behind her, and it cannot happen again whatever the match does |

Not only the reachable ones: *"a table that quietly drops forfeited once it is unreachable is
also a table that never showed it while it was."* A private court prints **two** rows, because
only *refunded in full* and *forfeited* are reachable there — the glossary being read rather
than a second rule — and names **no commitment deadline**, because the court was bought at
booking.

`stillPossible` is not `opens` with the moment left out. **Commitment is an event and never a
clock**: a match past its own deadline and still short has bought nothing, so on a match that
has not filled the three money outcomes are a *fill* away, and naming a moment there would
promise a turn that may never come.

Beside the table ride the quote's reasons — the commitment deadline as a moment, the seat's
amount on the spine, and how full the match is. There is **no `phase` field**: the standings
already say which phase she is in.

`may_depart` is a **server boolean** and the phone derives none of it. It is
`kernel.may_depart`, which is what `Match.depart` refuses on, so the control is drawn exactly
where the write would succeed — false for a viewer holding no seat, for one holding a live
seat claim, after the start, under ADR-0046's private-court lock, and on a cancelled match. It
is composed once, in `now.card_of`, so the card on Now and the route's boolean are one
expression, and it is a **spine boolean rather than a seventh act code**: leaving is not the
card's act.

A **leaver's route resolves** rather than 404ing — a 404 tells her the match never existed —
and a stranger's is the only 404, which is authorisation rather than a state of the match.

**A refusal is not a second shape.** The quote falling below what she was shown, the match
starting or cancelling, the lock closing, a second tap by somebody who has already left: every
one answers with the screen, recomposed at that instant, so she *sees* the correction rather
than being told it. The `POST` carries a **client-generated idempotency key** — ADR-0030's
command log, not the version ADR-0074 refused — and a replay returns the outcome she actually
got and writes nothing further. The response says **what the tap did**: `applied` is the
outcome the departure was made at, and `null` exactly when nothing was applied, so *was I
refused* is a fact the client is told rather than a rule it derives from `may_depart`. The write returns its own screen's answer **and** Now's
update, which for a departure is the card **changed in place**: nothing is removed and no
region moves, because ADR-0030 keeps the leaver's card until her outcome settles.

The route lives in `app/modules/now/` although its path says `matches`. The answer is Now's
vocabulary end to end and `now` already reads `matches` everywhere in this tree; the write
reaches the aggregate through `Departures`, a port of Now's own, exactly as `money.Seats`
does over the same aggregate. A general `GET /api/v1/matches/{id}` still does not exist.

### `DELETE /api/v1/matches/{matchId}/standby`

The second action off Now, and the one that is **a write rather than a screen**
([ADR-0087](../docs/adr/0087-leaving-standby-is-the-seventh-act.md)). A route exists to hold
a consequence and leaving a queue has none: no seat, no money, no cascade, no outcome, and
**no position to forfeit**, because a standby position is a fact the platform refuses to show
precisely so that it can rise.

**No confirmation and no warning**, for the same reason — a confirmation would imply a cost
the model says does not exist, and that is worse than a mis-tap. **No idempotency key**:
ADR-0030's log is for *destructive* commands, and a repeated delete of a place she no longer
holds is the state she asked for.

**It refuses nothing but the address.** Anybody may queue for any match, so there is no
membership to be a stranger to; *deleting a place the viewer does not hold answers exactly
what a success answers*, by having nothing to check. The only 404 is a match id that names
nothing.

It answers **Now's update and nothing beside it** — ADR-0074's shape is *its own screen's
answer and Now's update*, and this act has no screen. The update is **one card in one of two
forms**:

| Form | When |
|---|---|
| `card` | she is still something to the match — a seat, a departure, a live claim — so the card is recomposed in place |
| `gone` | the queue place was the whole of it, so the card leaves her screen |

The second is ADR-0070's *"the one-card answer must be able to say **this card is no longer
on your screen**"*, produced here for the first time: a departure keeps the leaver's card, so
nothing before this could remove one. It is a **discriminated union** rather than a nullable
card, on ADR-0072's rule for the leaver's money — *it is gone* and *this build sent none* are
opposite sentences and a blank cannot tell them apart.

**Nothing joins a queue in v1.** The waitlist toggle is a match-screen control and that screen
is out of scope, so `JoinStandby` exists as a use case with the seed catalog as its only
caller — the shape the four private-owner situations already take. Its named future caller is
the **standing rule** that auto-joins matching lists.

The route lives in `app/modules/now/` for the reason the departure route does, and the queue
itself is a table beside the aggregate rather than part of it: a join moves no state anybody
contends for, and going through `Match` would bump ADR-0034's version column and invalidate
the scoring-context cache keyed `matchId : recordVersion` on every ask.

### `GET` / `POST /api/v1/matches/{matchId}/result` · `POST …/result/acceptance`

The result conversation, and the third action off Now
([ADR-0074](../docs/adr/0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md),
[ADR-0060](../docs/adr/0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md),
[ADR-0048](../docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)).
It **embeds the match's spine verbatim**, carries the situation off the **same ladder** a
card resolves on, and is **not a card** — no fit badge, no emphasis, no card stamp. There is
**no `phase`**, because the situation answers what a phase would, and **no version**: a
client-held one would make the phone hold a rule about its own staleness.

**Five renderings, one reader.** Entry, both audience renderings of a live proposal, the
counter, the settled result and the unscored ending are `needsResult`, `confirmResult`,
`completed` and `playedNoScore` resolved for the viewer who asked.

**The result block is four facts and no history**, always present and empty when nothing is
on the table — a region's rule rather than a shelf's, because it makes no claim.

| Fact | |
|---|---|
| `score` | the sets, **the viewer's side first**, sides named by their players |
| `proposed_by` | an index into `score.sides`, so `0` is always *your side* |
| `agreed` | settled, by a tap or by the silence that confirms it |
| `proposals` | how many **sides** have spoken, capped at two |

**Two clocks, both named.** `settlement_deadline` is the hero — the entry deadline before
anybody speaks, and the live proposal's own deadline after. `acceptance_grace` is the
quieter line and crosses **only while it runs**: hiding it produces the outcome ADR-0048
built it to prevent, inverted — the screen says *settled* half an hour early.

**ADR-0048 replaced one constant with two, and they are twenty-four hours from different
moments.** `result_window` bounds *every* way a score arrives — a first entry, a correction
and a counter alike — which is what makes that ADR's outer bound of forty-eight hours
arithmetic rather than a second rule. `settlement_deadline` is a property of the
**proposal**, so a correction replaces it along with the score. The cost is named rather
than hidden: an opponent's window to *counter* a proposal made at hour 23 is one hour, where
her window to *accept* it runs the full day.

**Silence is derived, and `result_agreed` is a receipt.** The ladder answers `completed` for
a lone proposal past its deadline whether or not a wake has been round — the same standing
the two cancellation flags have, and what makes the reversal ADR-0048 specified real rather
than dependent on a job landing. The timekeeper's **fourth actor** writes the announcement.
**Two proposals settle nothing** and nothing is written for them: Raketa will not arbitrate,
and it will not file a receipt saying it did.

**What the viewer may do is three named booleans**, and the phone derives none of them.

| Boolean | |
|---|---|
| `may_enter` | put **her own side's** score up — the first entry, or a correction of her side's live one |
| `may_accept` | agree with what is on the table. Opposing side only; one opponent suffices |
| `may_counter` | put a different score up against it. False once her side has spoken |

**Two writes and not ADR-0074's three.** Entering, correcting and countering are one act at
three moments — ADR-0048 caps *proposals per side* across all of them, and which one a given
score is depends on what is already on the table. A client picking between two endpoints
would be holding exactly that rule (ADR-0053), so a score goes to one address and the server
decides what it was. Accepting has its own address because it carries nothing.

**A bare rejection is refused by having no shape to send one in**, rather than by a
validator that turns one away. **The server validates permissively** — it declines the
obviously impossible and never the rulebook, with a per-sport ceiling, because local
variation is wide enough that a strict validator eventually calls a real match illegal.

**A refusal is not a second shape.** A side that has already spoken, a result that settled
while her screen was open, a deadline that ran out, a leaver tapping through a stale screen
— every one comes back as what a success returns, including ADR-0074's own named case: *a
stale accept comes back as the counter's situation with `may_accept` false*. The two
exceptions are not about the act — a stranger's 404, and a score no format could produce,
which is about what she typed and needs a reason a recomposed screen cannot carry.

**Anyone who held a seat when the match ended resolves, including a leaver**, whose screen
opens and offers nothing. **A general `GET /matches/{id}` does not exist**, and its absence
is asserted.

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
  carries a **code** and an optional **caption code**, a door carries a **code**, and the
  client writes the words.

- A **level movement** beside a settled score, and a **tiebreak** field beside a set. No
  engine updates a rating from a result and a tiebreak's own points are not modelled, so
  both would be shapes claiming a number the platform does not have.

Everything that *is* a code crosses as an **OpenAPI enum** — `situation`, the act code,
`TermCode`, the card's hold reason, the cause, the shelf code, the caption code, the door
code, the block type, the cover, the currency, the refund destination and the departure's
outcome. That is what lets each client write an exhaustive `Record` over a
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
| `club-with-two-padel-categories` | One sport priced as two categories under two roofs, ADR-0079's `ps` |
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
| `match-that-lost-a-player` | `replacement` — committed, one seat short, and a leaver who is owed |
| `match-played-and-unscored` | `needsResult` — played, waiting twenty-four hours for a score |
| `match-private-with-seats-opened` | `privateOpen` — somebody's court, two seats for sale |
| `match-holding-a-court-softly` | `heldSoft` — one seat from full, and a court kept aside |
| `match-the-club-cancelled` | `cancelledClub` — a decision, not a receipt |

**No scenario carries a seat claim, and that is now a decision rather than a gap.** ADR-0081
refuses a thirty-seventh situation, so a claim moves no name in this catalog at all: a
scenario with one would resolve to `forming`, which the first row already names, and *two
matches saying the same thing would be one scenario twice*. It would also have lapsed by the
time anybody signed in — five minutes measured from a fixed instant on a fixed week — so the
seeded card would say nothing. A claim is checked in its own suite, where it can be asserted
as *this seat is spoken for* rather than as a name that does not mention one.

A scenario that loses a player also names what that player's **money** is — settled or open,
and whether her card names an amount at all — checked against the stored departures on every
run. It is the only claim in the seed catalog that is about a refund, and the outcome itself is
never authored: like the court hold, it is what the rules composed on the way through the same
use cases a request runs.

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

`app/seeds/money.py` adds five ledgers, one per way money can have arrived, and here every
number in the claim is a **fold**:

| Ledger | State |
| --- | --- |
| `ledger-holding-a-share` | An open match's share, held by Raketa until the match commits |
| `ledger-with-a-share-passed-through` | A private court's share, at the club the moment it arrived |
| `ledger-with-a-counter-paid-share` | Cash the club took — the one movement Raketa was never party to |
| `ledger-with-a-corrected-movement` | A share and its `REV-` reversal, both standing |
| `ledger-in-debt` | We paid out and did not collect: a balance below zero |

The claim is the movement count, `held` on the scenario's seat and the player's balance,
checked against the **stored** ledger on every run — and then the whole seeded set is asserted
against the same three invariants the nightly reconciliation calls. The reference is the
idempotency probe: a movement is filed under a fixed `PAY-<token>`, and the ledger refuses a
second one under it, so finding it is finding that the scenario has already run.

**A paid seat does not write a movement yet, and none is authored here.** The eight seeded
matches hold fourteen paid seats between them and are still paid through `PaySeat`, not
through `money.PayForASeat`. The join exists now (`Raketa02/Raketa#70`); what does not is a
catalog that can *name* what each seeded match's money is, and a scenario carrying money
nobody claimed would break the rule every other seeded fact is held to. Driving the join from
the runner is the demo week's own effort, `Raketa02/Raketa#96`.

Scope is what is **decided**: players, onboarding assessments, Skill ratings, clubs, court
reservations and bookings, matches, and ledgers. Nothing **authors** a match-held reservation — a
match's court is granted by the hold ladder (ADR-0031) as a consequence of its seats and its
clock, so `app/seeds/courts.py` refuses one and `app/seeds/matches.py` gets them for free by
running the real use cases. A walk over `app/seeds/` asserts the package imports **exactly**
the six contexts
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

`tests/unit/test_command_log.py` does the same for `command_log`, on the same argument and
with the same recorder shape. It found a real disagreement the first time it ran: the
migration named the primary-key constraint and the model did not, so the two DDLs differed
by the one constraint ADR-0030 actually asks for.

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
