# Rakieta Backend — Technical Vocabulary

This file holds **backend-only technical vocabulary**. It does **not** define domain
language — those terms (User, Authority, Club, Court, Booking, statuses, events) live
once in the shared glossary [`../CONTEXT.md`](../CONTEXT.md), which all three apps obey.
See [`../CONTEXT-MAP.md`](../CONTEXT-MAP.md) for the topology.

> When you name a backend architecture concept, use the term as defined here or in the
> root glossary's **Cross-cutting concepts** section. Don't drift to synonyms.

## Where the architectural terms already live

The core hexagonal / event-sourcing vocabulary — **DomainEvent**, **EventRecorder**,
**DomainEventStore**, **Transactional outbox**, **EventWorker**, **Event catalog**,
**Port / adapter**, **UnitOfWork**, **Read model**, **EventStreamVersionConflict** — is
documented in [`../CONTEXT.md`](../CONTEXT.md) under *Cross-cutting concepts*. Read them
there; they are not repeated here.

## Backend-only terms

- **Module** — a bounded context's vertical slice under `app/modules/<context>/`, split
  into `domain/ application/ infrastructure/ presentation/`. _Avoid_: package, app,
  service (this codebase has exactly one service).
- **Use case** — one class in `application/` with a single `async execute(...)`.
  Constructor-injected ports only. _Avoid_: service, manager, handler (a **handler** is
  specifically an event subscriber, which is a different thing).
- **Handler** — a function subscribed to a domain event, run by the `EventWorker`
  **after commit**. The only place a side effect belongs. _Avoid_: listener, callback.
- **Command** — the input dataclass a use case's `execute` takes. Carries primitives
  from the boundary, not domain value objects.
- **Event-sourced aggregate** vs **persisted-with-events entity** — the two persistence
  shapes in this codebase, and a deliberate per-context choice. `User` is the former
  (state rebuilt from its stream); `RefreshToken` is the latter (current state is the
  truth, events provide audit + cross-context notification). Neither is the default.
- **Durable event name** — the stable `"<context>.<event>"` string plus integer version
  registered in the event catalog, e.g. `users.user_registered` / v1. It is the wire
  contract for stored history and is **independent of the Python class name**.
- **Aggregate repository** — the port a use case loads and saves an **event-sourced
  aggregate** through, e.g. `AssessmentRepository`. It owns the aggregate-type name, the
  replay, the ownership scoping and the optimistic-concurrency bookkeeping, so a use case
  never names the event store. `save` appends and publishes and **does not commit** — the
  `UnitOfWork` stays a use-case dependency, because one transaction can span two
  aggregates. Its adapter keeps a **per-request** identity map of loaded versions, so it
  must be constructed per request from the session. _Avoid_: DAO, store, gateway.
- **Invariant** vs **Unavailability** — the two ways kernel and engine code refuses, and
  they are not interchangeable ([ADR-0022](../docs/adr/0022-kernel-negative-space-and-constant-homes.md)).
  An **invariant** is a broken precondition: `invariant(subject, message)` raises
  `InvariantViolated`, nothing catches it, and it raising in production means a bug
  shipped. An **unavailability** is a legitimate domain state where no answer exists:
  it is *returned* as a `Result` and the caller branches on it. Confusing them forces
  `try` into pure code, or forces every call site to handle a case that cannot happen.
  _Avoid_: "error" for either, unqualified.
- **Result** — a frozen `Ok(value)` or a frozen `Err(reason)`, consumed by pattern match.
  Two `@final` classes with one field each, so there is no third inhabitant: never both,
  never neither. `map` and `and_then` pass a failure's reason through untouched.
- **Reason** — why there is no answer: a stable machine `kind` code and its payload
  fields, **never a sentence**. The clients own the words; a reason crosses the wire as
  `{kind, …payload}`. `Unavailable` is the closed union of them, in
  `app/kernel/unavailability.py` — its own module, because it is assembled *from* the
  modules that produce its members while `results.py` knows about none of them. It
  shipped empty (`Never`); its first member is `NonexistentLocalTime`. A function
  declares the reasons it can actually give; only code aggregating over all of them
  names `Unavailable`. _Avoid_: message, detail, error text.
- **Money brands** — `Grosze` and its three refinements `CourtPrice`, `SeatShare` and
  `Payable`, each a `NewType` with **exactly one** constructor
  ([ADR-0023](../docs/adr/0023-money-integer-grosze-gross-whole-zloty.md); the domain
  words are the shared glossary's). What the brands buy is the **rounding order**:
  `court_price()` compounds the multipliers and rounds once to whole złoty,
  `divide_among_players()` accepts *only* a `CourtPrice`, so there is no path from a raw
  number to a `SeatShare` and dividing before rounding does not typecheck. Arithmetic
  goes through named functions (`add_grosze`, `subtract_grosze`, `negate_grosze`,
  `at_least_zero`) and **loses the refinement** — a share plus a fee is a `Grosze`. The
  unit is in each name because the kernel is one flat import path. `NewType` erases at
  runtime, so what enforces all of this is `tests/typecheck/kernel_misuse.py`, plus one
  runtime backstop: the whole-złoty law is *asserted* at the split, since
  `CourtPrice(Grosze(8650))` is reachable from a call site that ignores the convention.
  _Avoid_: amount, cents, minor units (unqualified), `Decimal`, float.
- **Ratio** — an exact multiplier or refund fraction: a `NewType` over `Fraction`, built
  from **two integers** by `ratio(n, d)` or `percent(n)`. Never a float, and never
  `Fraction(0.9)` either — that is the double nearest nine tenths, not nine tenths, and
  it rounds identically for years before the one time it does not. Compounding in exact
  rationals is what makes a 55 zł court at 70% cost 39 zł rather than the 38 zł a double
  gives. A test walks `app/kernel/money.py` for float literals and the name `float` and
  finds neither. _Avoid_: multiplier (unqualified), rate, factor, percentage.
- **ClubCard** — the closed union `NoCard | CardAllowance | CardCoversShare`, three
  `@final` frozen members, and the backend spelling of the glossary's *card offset*.
  `card_offset()` is the **one** implementation of the capping rule and `payable_from()`
  derives from it, so a payable is non-negative by construction rather than by a clamp
  that could disagree with the offset beside it. _Avoid_: discount, voucher, credit.
- **Instant** — a timezone-aware `datetime` in UTC, and the only representation of a
  moment in this codebase ([ADR-0024](../docs/adr/0024-instant-as-aware-datetime-minute-coordinates.md)).
  Not epoch milliseconds: the clock returns one, every domain event carries one, and
  Postgres stores `timestamptz`, so a second representation would buy a conversion at
  four boundaries and nothing else. It is a `NewType`, i.e. a **refinement** — an
  `Instant` goes wherever a `datetime` is wanted and a bare `datetime` does not go where
  an `Instant` is required. Built only through `instant()`, which rejects a naive value.
- **Minute coordinates** — `MinuteOfDay`, `DayOffset` and `Minutes`, branded integers,
  and what engines compute in: that is what makes an availability check integer
  comparisons rather than datetime arithmetic. `slot_start()` is the **single**
  conversion from coordinates to an `Instant`, so every timezone question has one place
  to be asked; `zoneinfo` is imported in one module and a test walks `app/` to keep it
  that way. **A `DayOffset` is never persisted and never serialised** — it is
  anchor-relative, so a stored one silently changes meaning. _Avoid_: slot index, day
  number, offset (unqualified).
- **Clock** — the `Protocol` in the kernel returning an `Instant`, **passed, never
  imported**. No module reads ambient time (ADR-0015's first purity rule), which is what
  makes scrubbing forwards and backwards, determinism and every fixed-`now` test
  possible. One read per command, captured once and passed on: two reads inside one
  command can disagree. Its wall-clock adapter is `SystemClock` in
  `app/infrastructure/clock.py`, and only a composition root imports it — depending on
  *what a clock is* must not drag a live one into scope.
- **Matchmaking brands** — `Level` and `Uncertainty`, both `NewType`s over the kernel's
  `Ratio` and both carried in **hundredths** (`level(320)` is 3,20), plus `PlayerRef`.
  They live in `app/engines/matchmaking.py`, not the kernel: ADR-0022 records that
  promoting the scale is a *relocation* to be done when the rating core can import it
  back, and until then the kernel is untouched. The brands are what stop a Level standing
  in for how sure the platform is about it — the two are the same `Fraction` at runtime, so
  the claim is worth exactly what `tests/typecheck/kernel_misuse.py` checks. **The scale's
  upper bound is deliberately not restated here**; 1,0–5,0 belongs to `racketskill/core`.
  _Avoid_: rating (that is the pair), skill (that is the aggregate), mu, sigma.
- **Snapshot** — a frozen value object a calling module assembles and an engine reads:
  `MatchSnapshot`, `SeatSnapshot`, `PlayerSkill`, `UnratedPlayer`
  ([ADR-0026](../docs/adr/0026-matchmaking-engines-snapshot-input-contract.md)). Never an
  aggregate — engines may not import a module, and the contexts that own this data do not
  exist yet, so the snapshot *is* the specification for what Matches will have to own. A
  sport's sold seat count is **read from the kernel registry**, never carried as a field.
  _Avoid_: DTO, view model, projection (that is a read model over a stream).
- **Occupant** — who is on a seat, as a closed union of `PlayerSkill | UnratedPlayer`. The
  second is somebody the platform has never rated *at this sport* and it carries a
  `PlayerRef` and nothing else, because *a rating is never only a number*: the Level, the
  Uncertainty and the Confidence arrive together or not at all, so the absence is a second
  type rather than three nullable fields with an all-or-nothing rule between them. The
  `current_player` is an `Occupant` too — a player rated at tennis alone still gets padel
  cards. _Avoid_: unrated user, guest, provisional rating.
- **Contender** — one place on a resolved `Roster`: a **definite** Level and Uncertainty,
  the `PlayerRef` on that seat if anybody is on it, and whether the Level was stood in for.
  The forecast arithmetic runs on these and never on snapshot seats, and only a `Contender`
  or a `PlayerSkill` satisfies `pairing/core.Rated` — which is the fence that stops a seat
  reaching a team strength before somebody has said where its Level came from. It carries
  **no Confidence**, so the engine provably cannot compute with one. The domain word for
  the whole tuple is **Roster**; this is one place on it. _Avoid_: participant, member,
  slot, seat (that is the snapshot's).
- **Exactness boundary** — `pairing/core.as_float()`, the one place matchmaking's exact
  ratios become floating point. Levels stay exact through subtraction and through a
  `Ratio`-weighted team strength; exactness ends at the first square root, so *where does
  this stop being exact* has one answer and a test walks the package to keep it one.
- **Split** — one of the three arrangements four players admit, as a value object on
  `PairingAnalysis`: the two sides as `PlayerRef`s plus the `BalanceForecast` computed from
  them, all three returned ranked best-first. **Not the split bar** — that is
  `favourite_share` / `underdog_share` on the forecast and says how lopsided a match is,
  where a `Split` says who is with whom. Membership and team strength are built together, so
  `split.side_a` and `split.forecast.side_a` are the same team by construction and no caller
  can pair a forecast with an arrangement it was not computed from.
  _Avoid_: pairing (that is the domain word for the whole question), team, line-up.
- **Evening level** — the Level that, sat beside one named seated player, makes the two
  sides exactly equal. `pairing/core.even_partner_level()` solves it by **inverting the team
  strength**: a strength is piecewise-linear in the joiner's Level with one kink where the
  joiner overtakes their partner, so the answer is one comparison and one division in exact
  ratios. Three seated players give three of these, and the domain's **Seat target** is the
  middle one — the code word and the domain word are deliberately different, because two of
  the three are never advertised. _Avoid_: ideal level, optimal partner, best fit.
- **Analysis decline** — each field of a `PairingAnalysis` answers or declines on its own,
  as a `Result` with its own reason: `SidesNotFormed` (nobody to put on a side, or an arity
  with no pairing rule), `SeatUnderDetermined` (not exactly one seat open), `NobodySeated`,
  and `UnratedSeat` (a seated player the platform cannot place on the scale). So a forming
  match answers what it can, and *"no forecast"* is never read as *"nothing to say"*. Two
  reasons are deliberately shared between fields, because each is one fact answering more
  than one question: a sport with no pairing rule has no sides **and** no seat to aim, and
  an unrated roster has no band, nothing to impute from **and** no exact seat target. The
  thresholds differ and the payload is what distinguishes them — the band and the forecast
  need *one* rated player, the seat target needs *all* of them.
- **Read-model repository** — the port a use case reads *projected current state* through,
  e.g. `UserRepository`. It answers queries against a table, not by replaying a stream, and
  has no version bookkeeping. **The trap:** `UserRepository` is this kind despite its name
  and despite `User` being an event-sourced aggregate — it is the projection side, not the
  write side. It keeps its name; read the shape, not the noun.

Add backend-specific technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.
