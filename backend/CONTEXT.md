# Raketa Backend — Technical Vocabulary

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
- **Minute coordinates** — `MinuteOfDay`, `DayOffset`, `Minutes` and `IsoWeekday`, branded
  integers, and what engines compute in: that is what makes an availability check integer
  comparisons rather than datetime arithmetic. `slot_start()` is the **single**
  conversion from coordinates to an `Instant`, so every timezone question has one place
  to be asked; `zoneinfo` is imported in one module and a test walks `app/` to keep it
  that way. **A `DayOffset` is never persisted and never serialised** — it is
  anchor-relative, so a stored one silently changes meaning. An `IsoWeekday` is Monday 1
  through Sunday 7 and is branded against the mistake that reads Wednesday as 00:03.
  _Avoid_: slot index, day number, offset (unqualified).
- **Local clock face** — `local_minute_of_day()` and `local_iso_weekday()`, the two halves
  of reading an `Instant` back in a zone, and `slot_start()`'s inverse. Both take the zone,
  because a weekday read off an instant's own UTC date is wrong for the two hours either
  side of a local midnight — 22:30 UTC on a Sunday is already Monday in Warsaw — and wrong
  silently. A **declaration** is a claim about a clock face and an `Instant` is UTC, so
  these are the only place the two meet.
- **Zone** — the kernel's alias for `zoneinfo.ZoneInfo`, exported so that a value object can
  *hold* a zone without importing the module the walk allows in one file. Holding one is
  legal everywhere; **building one is not legal in an engine**, because resolving an IANA
  name reads the tz database, which is configuration and I/O — a separate walk over
  `app/engines/` keeps it that way. An engine is given its zone exactly as it is given
  `now`. _Avoid_: tz, timezone string, IANA name.
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
  `MatchSnapshot`, `SeatSnapshot`, `PlayerSkill`, `UnratedPlayer`, `ClubSnapshot`,
  `PlayerProfile`, and the two that ship dark, `PlayerScore` and `PlayHistory`
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
- **Term kinds** — `matchfit/core.constraint_term()` and `matchfit/core.evidence_term()`, and
  the kind of a term is which one built it rather than a label anybody set. The first returns
  a `ScoredTerm` and has no path to an exclusion; the second takes an **optional** observation
  and returns an `ExcludedTerm` when there is none. So *a constraint is never excluded* and
  *absent evidence never scores full marks* are unwritable rather than reviewed for, which is
  ADR-0027's whole repair expressed as two return types. An `ExcludedTerm` has no `value`
  field for a friendly default to be written into and derives its kind, since only evidence is
  ever excluded. _Avoid_: optional term, soft/hard signal, nullable value.
- **Observation** (`matchfit/core.Observed`) — a term value and the payload it was read from,
  **together or not at all**, the same rule the rating context states as *a rating is never
  only a number*. One optional argument rather than two makes *a score with no payload* and
  *a payload with no score* unwritable instead of two invariants somebody has to keep.
- **Term payload** (`fit.TermFact`) — one `@final` class per term that can score, each with a
  `kind` `Literal` equal to its `TermCode` value and a body of integers, exact ratios and
  enums. The engine emits **no display text**: a formatted price, a rendered Level or a
  sentence would show up as a new `str` field, and a test over the source says which three
  string fields are legitimate. A `ScoredTerm` checks its payload's kind against its own code,
  because the two are the same machine key spelled twice. _Avoid_: reason text, message,
  description.
- **Pending weights** (`matchfit/v1/constants.PENDING_WEIGHTS`) — the terms the table still
  owes, written out with the weight each will take, and the constants refuse to be built
  unless the declared and the pending weights sum to a hundred. **Empty as of v1's tenth
  term**, so *the weights sum to 100* now holds unqualified — and completing the table was
  exactly the diff the mapping promised, two lines moved from one mapping to the other. Both
  the mapping and its guard survive it being empty, so an eleventh term declares its debt in
  arithmetic rather than in a comment.
- **Aim resolution** (`matchfit/v1/engine._aimed_at`) — how the skill overlap term decides
  what a match is aimed at: the `PairingAnalysis`'s `seat_target` if it answered, the
  `target_band`'s midpoint otherwise, and nothing at all when neither did. It **branches on
  which field answered** and never counts open seats, because *when is a seat target
  available* is the pairing engine's rule and this engine is fenced from holding a second copy
  of it. The band's `half_width` travels on the payload for the second case and is absent for
  the first, which is how a client tells *"this seat is aimed at 3,00"* from *"this match is
  aimed at 2,50–3,50"* — the quantity carrying the distinction rather than a label naming the
  branch, the same shape as `PriceFact.ceiling`. _Avoid_: target resolution strategy, aim
  mode.
- **Borrowed constant** — a figure another lineage owns, written out in this engine's
  constants with the derivation in its docstring, an AST walk asserting the package does not
  import that lineage, and a mirrored assertion in the **persona** suite so a retune there
  turns this red. `matchfit/v1`'s `overlap_span` is 1,10 because that is the widest band the
  rating context prints; the pairing engine's `imputation_uncertainty` copies the same
  context's onboarding σ floor the same way. The alternative — importing it — would let a
  rating retune move a balance percentage or a Match Fit score, and the falsification
  programme rests on being able to attribute a number to exactly one lineage. _Avoid_:
  shared constant, cross-engine constant.
- **Court hold** (`matchmaking.CourtHold`) — how firmly a court is held for a match, as the
  clock's own three-rung ladder: `NONE`, `SOFT`, `HARD`. Borrowed vocabulary with no owner
  yet, like a seat's state and a ladder qualification — the documents that specify the hold
  ladder are outside this repository, so the spelling is fixed here and whichever context
  ends up owning courts will define it. **The order lives with the word**, as
  `matchmaking.HOLD_LADDER`, never in a version's constants: *a firmer hold never makes a
  match less likely to be played* is a claim about the domain, and a monotonicity test that
  walked a version's own mapping would pass by walking whatever order a retune left.
  _Avoid_: reservation, booking (that is the Bookings context's), lock, option.
- **Match phase** (`matchmaking.MatchPhase`) — where a match is on the clock's ladder:
  `FORMING`, `LOCKED`, `CANCELLED`. **Carried, asserted and never read by a term.** Whether
  a match is joinable at all is a *hard filter* candidate generation applies before an
  engine is called ([ADR-0027](../docs/adr/0027-fit-and-certainty-are-separate-ranking-is-policy.md)),
  so `MatchSnapshot` refuses every phase but `FORMING`: a cancelled match ranked last is
  still a cancelled match in a home list. The *run-up* to the join cutoff is the matter of
  degree, and that is what the viability term reads. It is no longer borrowed: it is the
  first **situation projection**, and `matchmaking.MATCH_PHASE_OF` is the table.
  _Avoid_: status, state (that is a seat's), stage.
- **Situation projection** — a smaller state vocabulary derived from `kernel.Situation` by a
  **total table**, owned by the consumer that needs it and asserted exhaustive **at module
  load** so a rung added to the ladder fails the import rather than one branch of one call
  ([ADR-0040](../docs/adr/0040-one-ladder-resolves-a-situation.md)). It reads the situation
  and nothing else: a projection that reached for the record or the clock would be a second
  derivation of what a match is doing, which is the failure the single ladder exists to make
  unreachable. `matchmaking.match_phase()` is the first and only one today. _Avoid_: mapper,
  adapter, second ladder.
- **Viability's two halves** — `matchfit/v1`'s viability term is a **probability composed as
  one**: the chance there will be people times the chance there will be a court. Both halves
  have the same shape — what is already committed, plus what might still be got, discounted
  by how likely getting it is — so the paid seats and the court hold are the committed parts,
  and the run-up to the join cutoff and the club's `crowding` discount the rest. A weighted
  blend of two marks was the alternative and is a worse fit for the same facts: only a
  probability admits the measurement all three of its constants are falsified by, which is
  the share of joined matches that were actually played, by viability decile. _Avoid_:
  confidence (that is the rating context's), likelihood score, fill rate.
- **Rounding, in one place** — `kernel.round_half_away_from_zero()` over a `Fraction` is the
  rule, and it is the only implementation of it. Both engines delegate: `matchfit/core.
  whole_percent()` scales a `Ratio` by a hundred and guards its range, `pairing/core.
  round_half_away_from_zero()` converts a float to the exact rational — each owns its own
  *crossing* into the rule's domain, which is engine vocabulary, and neither owns the rule.
  It reached three implementations in two packages first, and was promoted by ADR-0022's two
  questions ([#88](https://github.com/RobertConstantin02/rakieta/issues/88)): it answers
  nothing about the domain, and a second implementation of it is a defect. **This does not
  breach the engine fence.** `.importlinter` forbids the two matchmaking packages from
  importing each other in both directions, and still does; what that fence protects against
  is one engine's arithmetic moving when the *other engine's version* moves, and a kernel
  rule carries no version and no tuning knob. _Avoid_: restating it in a third engine —
  reach for `app.kernel`.
- **Match record** (`kernel.MatchRecord`) — the closed set of stored facts the resolution
  ladder and the wake function read, and **not the Matches aggregate**. It stands to a match
  as `MatchSnapshot` stands to one for an engine: a narrow input contract published to be
  resolved, holding nothing derived and no player identity. `filled()` counts seats **paid**
  and `held_unpaid()` counts seats somebody holds and nobody has paid for — two numbers,
  never one, because folding them tells four people a match is complete while a seat may
  still lapse. _Avoid_: match aggregate, match entity, match DTO.
- **Situation ladder** (`kernel.situation()`) — the one resolver, over one closed enumeration
  of **thirty-six** names, in which **the order is the specification** and the first matching
  rung wins. Pure in the record and the clock, with an **optional viewer**: called with one it
  may answer `SEAT_OFFERED`, `SEAT_OPENED` or `WAITLISTED`, and called without it cannot. The
  absolute form is the same function with the parameter absent, never a second derivation.
  Everything else an audience changes — a non-member's money line, a leaver's card, who is
  asked for a score — is rendering downstream. _Avoid_: state machine, status resolver,
  context key (this repo spends *context* on bounded contexts).
- **Court hold, composed** (`kernel.court_hold()`) — the hold ladder as a *computation*: the
  base tiers priced in paid seats, then the club's two amendments, and never a stored court
  id. **Staleness is not latched** — a third payment makes a stale hold live again, so a card
  may go back from released to held. Distinct from `matchmaking.CourtHold`, which is the
  three-rung *word* an engine reads. _Avoid_: reservation, lock.
- **Wake** (`kernel.next_wake_at()`) — the next instant a match could resolve differently, or
  `None`. **A wake is a look, not an instruction**: the handler re-derives from the record, so
  a late wake changes *when* we look and never *what we find*. It sits beside the ladder
  because both read one list of boundaries — which is what makes *a threshold cannot exist in
  the ladder and be missing from the schedule* true by construction rather than by two lists
  being kept in step ([ADR-0076](../docs/adr/0076-the-schedule-is-a-column-a-wake-is-a-look-and-there-is-no-list-of-boundaries.md)).
  Internal, and never serialised onto a card. _Avoid_: timer, schedule, transition.
- **Read-model repository** — the port a use case reads *projected current state* through,
  e.g. `UserRepository`. It answers queries against a table, not by replaying a stream, and
  has no version bookkeeping. **The trap:** `UserRepository` is this kind despite its name
  and despite `User` being an event-sourced aggregate — it is the projection side, not the
  write side. It keeps its name; read the shape, not the noun.

- **Environment** — one of exactly four: `local`, `development`, `staging`, `production`,
  spelled identically by all three apps and carried by `APP_ENV`. `local` is a developer's
  own machine — a container on your laptop is still `local`, because the name describes
  *where the software runs*, not whether it is containerised. **The load-bearing rule: the
  environment may select configuration defaults; it may never select behaviour a domain
  test could observe.** No deadline, threshold, validation, status code or response shape
  varies by it. `APP_ENV` rather than `ENV` because the old name collides with an ordinary
  shell variable, so a value inherited from the surrounding environment could decide what
  environment the application thought it was in. _Avoid_: `dev`, `prod`, `test`, `stage` —
  those are the spellings whose synonymy is the bug, and the settings object refuses every
  one of them.
- **Environment profile** — the settings `APP_ENV` supplies defaults for: `DEBUG`,
  `LOG_LEVEL`, `LOG_JSON`. One value replaces three that had to be kept in agreement by
  memory, and the failure that removes is the silent one — nothing goes wrong until the
  deployment where somebody sets two and forgets the third. Each stays **explicitly
  overridable**, because a legitimate one-off (verbose logging in staging while chasing a
  bug) must not require abandoning the mechanism. Implemented with `model_fields_set`, so
  *"was this configured?"* means *"did somebody actually set it"* rather than *"does it
  differ from a sentinel"*. _Avoid_: environment-specific config file, profile inheritance.
- **Startup refusal** — a `ConfigurationError` raised while the settings object is being
  built, for configuration that is dangerous rather than merely wrong. It lives on the
  settings object and not in the application factory, so it holds for a worker, a
  migration or a seed run and not only for a process serving HTTP. Two constraints on the
  message: it **names the offending variable and the reason**, and it **never contains the
  offending value** — a `WRITER_DB_URL` carries a password and a refusal goes straight to a
  log aggregator. `ConfigurationError` is deliberately **not** a `ValueError`: pydantic
  wraps `ValueError` raised inside a validator into a `ValidationError` whose repr carries
  `input_value=…`, which for an after-validator is the entire settings object, signing key
  included. _Avoid_: falling back, warning and continuing, a "strict mode" flag.
- **Unprovisioned environment** — `development` and `staging`. Defined and validated, but
  no domain is registered, so neither has a host or a database. Selecting one without
  `APP_HOST` and `WRITER_DB_URL` is a startup refusal naming the missing variable. **No
  placeholder hostname is written anywhere**, which is why "configured" can only mean
  "somebody set it": there is nothing to compare a host against. _Avoid_: inventing
  `api-dev.…`; a config file naming a host that does not exist describes infrastructure
  that does not exist.
- **Public-network scheme rule** — the platform rule that a URL a browser or a phone
  reaches over the internet is `https://` in every deployed environment, and unconstrained
  in `local`. The backend calls nothing over HTTP, so its only instance is `ALLOW_ORIGINS`:
  a non-`https://` entry there while `APP_ENV` is deployed is a startup refusal, because a
  credentialed CORS grant to a plaintext origin is the club console's session cookie in the
  clear. The wildcard is not an origin and is skipped; it has its own refusal. Defined once
  for all three apps in [`../docs/environments.md`](../docs/environments.md). _Avoid_:
  extending it to a **server-to-server** address — `http://backend.svc.cluster.local:8000`
  never crosses a public network, and whether that hop is encrypted is a
  deployment-topology question no app can assert.
- **Composition root** — `app/bootstrap/composition.py`, the one place an adapter is
  constructed. One plain function per port, taking a database session and the settings,
  with no web framework in it and no request anywhere near it. Before it, every adapter
  was built inside a `Depends` callable, so anything that is not an HTTP request had two
  options and both were bad: boot the API to create data, or hand-copy the wiring into a
  second root. **A hand-copied composition root drifts silently** — it keeps working, and
  it stops being what production runs. _Avoid_: constructing an adapter anywhere else; a
  walk over the dependency modules refuses it.
- **Declaration vs construction** — the split the composition root buys, and the reason
  `app/api/dependencies.py` still exists. A dependency declaration answers *when* an
  adapter is built and how long it lives — one per request, cached by FastAPI for that
  request, which is what keeps a repository from answering with another request's stream
  versions. The factory answers *what* is built. Sharing is therefore the caller's
  business: every adapter is a stateless wrapper over its session, so a caller outside a
  request that wants one store for two repositories builds it once and passes it on.
- **Configuration boundary** — the line configuration is read at and never crosses. It is
  the composition boundary: `app/bootstrap/`, `app/api/dependencies.py`, `app/core/`,
  `app/main.py` and the adapters. Inward of it — `app/application/`, `app/shared/domain/`
  and every `app/modules/*/domain` and `app/modules/*/application` — the settings module is
  **structurally unreachable**, enforced by an `.importlinter` contract rather than by
  review. That is what makes *the environment may never select behaviour a domain test
  could observe* a checkable claim instead of an aspiration: a use case reading `APP_ENV`
  to pick a deadline is a rule that is true on a laptop and false in production, and the
  domain suite cannot see the difference. `pydantic_settings` and `os` are forbidden beside
  it, because declaring a second settings class or reading `os.environ` is the same rule
  broken by a different import. The two `app/modules/*` arms are **wildcards**, so a
  context created tomorrow is fenced the day it exists — Clubs, Courts, Bookings and
  Matches are all named and none is modelled. A use case that needs a configured value
  takes it as a constructor argument. _Avoid_: importing settings "just for a default",
  a module-level `get_settings()` inside a business layer, an exemption.

- **Seed account** — a deterministic development account created by `app/seeds/`, named
  for the **state it represents** rather than for a person: signing in as
  `assessment-in-progress@raketa.example` is a statement about what you expect to see.
  The address is *derived* from that name, so an account cannot be called one thing and
  reachable at another, and it is on a TLD RFC 2606 reserves so it can never become
  somebody's real mailbox. **`.example` rather than `.test`**, though the same sentence of
  the same RFC reserves both: `EmailStr` at the HTTP boundary is `email-validator`, which
  refuses `test`, `invalid`, `localhost`, `local`, `arpa` and `onion` outright — so a
  `.test` account is one no client can sign in as. _Avoid_: a fixture user, a real domain,
  an address that names a person.
- **Seeding through the write path** — the rule that makes seed data trustworthy: a seed
  executes the same use cases a request executes, wired from the **composition root**, so
  the event stream, the outbox row and the projection are written by the code that
  normally writes them. A row inserted straight into a table produces an aggregate with
  **no history** — it reads correctly until something replays it, and then the seeded data
  and the system's own account of that data disagree; it also skips every handler that
  should have reacted. A structural walk over `app/seeds/` refuses a statement import, an
  ORM model and `session.add`. _Avoid_: fixtures SQL, a factory that builds ORM objects.
- **Seed guard** — the refusal that keeps fabricated accounts out of production, checked
  **on import** of `app/seeds/` and again against the settings `run` is handed. Not in the
  make target: a make target is not what runs inside a container, and a guard that
  `python -m app.seeds` walks around is decoration. Seeding is permitted in `local`,
  `development` and `staging`, written out per environment rather than derived as
  "everything but production", so a fifth environment has to be decided about rather than
  inheriting an answer. _Avoid_: guarding the entry point instead of the module.
- **Seed scenario** — what one seeded account holds, **for one sport**: a run left open, a
  run abandoned, or a run answered through and rated. A closed union, so the runner's
  `match` over it stops typechecking the day a fourth state exists — an unhandled scenario
  would otherwise be an account silently seeded into no state at all. One sport is one
  scenario: two on the same sport describe a state the domain cannot reach, because a
  rated sport refuses a second assessment. _Avoid_: an account that is a person rather
  than a state, a scenario for a context with no aggregate.
- **Answer policy** — how a seed scenario answers whatever the questionnaire asks: an
  index into the question's *own* options counted from the weakest, clamped to the last
  one, with one number for demonstrations and one for everything else. The split is read
  off `Question.tier` — the port's own marker for an execution question — never off a
  question id, which belongs to an engine version. Two small numbers rather than a script
  of option ids, so rewritten copy and renamed options leave it working. _Avoid_: a fixed
  transcript, a per-question-id table, choosing answers by reaching into the engine.
- **Rating claim** — what a seeded account's *name* promises about the rating its run
  produces: a band, and where in that band the Level must sit, as a fraction of the band's
  own width. Checked against the **stored** rating on every run, including one that
  created nothing, so an engine retune that moves `rating-barely-established` into
  Developing stops the seed by name. The band's edges come from the rating rather than
  from a second copy, so a re-cut band moves the claim with it. _Avoid_: a claim written as
  literal Levels, a check that only runs on the account this run happened to create.

Add backend-specific technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.
