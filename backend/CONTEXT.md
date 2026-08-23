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
- **Seconds** (`kernel.Seconds`, `kernel.moved`) — a length of time in whole seconds, and **a
  separate brand rather than a finer spelling of `Minutes`**: a `Minutes` handed to something
  expecting a `Seconds` is a sixtyfold error that reads perfectly, and the compiler is what
  refuses it. It exists because exactly one rule in the system is measured below a minute —
  a seat claim's thirty-second cooldown (ADR-0081) — and rounding that up to a minute would
  be the rule told as a lie. `moved()` is the **one** place an instant is moved at all, with
  `shifted()` as its minutes-shaped wrapper, so there is a single construction of a
  `timedelta` and a single answer to the elapsed-versus-wall-clock question.
  _Avoid_: a bare `timedelta(seconds=…)` at a call site, and a float duration.
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
  may go back from released to held. **A match that is over is keeping nothing**, above the
  base ladder and before any tier: a cancelled match on two paid seats would otherwise compose
  a soft hold for a court that went back the moment it cancelled. Distinct from
  `matchmaking.CourtHold`, which is the three-rung *word* an engine reads, and from
  `keeping_a_court`, which is what the record says rather than what the ladder says.
  _Avoid_: reservation, lock.
- **Keeping a court** (`kernel.keeping_a_court()`) — whether a court is standing aside for
  this match **on the record**, read from `heldSince` and `releasedAt` **together**. Not the
  same question as the composed hold: that one is *should a court be kept aside*, computed
  from the seats and the clock, and the whole of the ladder's decision is the gap between
  them. `heldSince` **outlives the reclaim that ends it** — the club's cap is measured from
  it, so a reclaim that also cleared it would reset the clock that had just fired, grant again
  on the next look and reclaim again a cap later, for ever
  ([ADR-0089](../docs/adr/0089-held-since-outlives-the-reclaim-that-ends-it.md), amending
  ADR-0031). _Avoid_: reading either field alone, `isHeld` (that is the composed answer).
- **Hold move** (`kernel.hold_move()`) — grant · withdraw · stand: the ladder's *act*, one
  function away from its answer, and the only thing in the system allowed to move
  `heldSince`. A match keeping no court is asked about **as though a hold were granted now** —
  not a second ladder but the question a grant actually poses, and it is what lets the ladder
  ask about a record in a soft tier under a club cap without tripping the invariant that
  combination is refused by. The anchor is kept where one exists, so a reclaimed hold answers
  *stand* rather than being granted again. _Avoid_: resolve, reconcile, sync.
- **The hold ladder, acting** (`matches.ResolveCourtHold`) — the ladder as a *write*: it asks
  `hold_move`, claims a court through Courts or gives one back, and it runs **inside the
  transaction that moved the match** rather than after it. That is not caution — entering a
  tier and being granted a court have to be one write, or a stored record sits in the
  combination the kernel refuses and it arrives as a five-hundred on a home screen rather than
  as a red test. A grant that finds no free court is an **inventory loss**, which is
  ADR-0035's single story. `tests/unit/test_resolve_court_hold.py` walks the package and
  reddens when a Matches write saves without asking. _Avoid_: an event handler (it runs after
  commit), a scheduled reconciler.
- **Wake** (`kernel.next_wake()`, `kernel.next_wake_at()`) — the next instant a match could
  resolve differently, or `None`. **A wake is a look, not an instruction**: the handler
  re-derives from the record, so a late wake changes *when* we look and never *what we find*.
  It sits beside the ladder because both read one list of boundaries — which is what makes *a
  threshold cannot exist in the ladder and be missing from the schedule* true by construction
  rather than by two lists being kept in step
  ([ADR-0076](../docs/adr/0076-the-schedule-is-a-column-a-wake-is-a-look-and-there-is-no-list-of-boundaries.md)).
  Internal, and never serialised onto a card. `next_wake_at` is the same answer with its name
  dropped, for a caller that wants only a moment. _Avoid_: timer, schedule, transition.
- **Boundary** (`kernel.Boundary`) — one instant a ladder compares the clock against, **and
  which one it is**: a `WakeReason` and an `Instant`. The eleven reasons are the commitment
  deadline, a hold tier lapsing, a hold going stale, a vacancy decaying, the rescue window,
  the checkpoint, the join cutoff, the door code, the start, the end of play and the result
  window. _Avoid_: threshold as a noun for the pair — a threshold is the moment alone.
- **Wake reason** (`matches.next_wake_at` / `wake_reason` columns) — the label a scheduled look
  is filed under, and **half of the idempotency key** `{matchId}:{threshold}:{scheduledFor}`.
  **Nothing branches on it.** The tie-break between two boundaries on one instant is
  `WakeReason`'s own declaration order, because a label chosen by construction order would
  file one moment under two names. _Avoid_: wake type, wake kind, trigger.
- **Re-arming** (`matches.MatchSchedule.re_arm`) — moving a match's `next_wake_at` forward
  **without bumping its version and without announcing anything**, which is what a look that
  found nothing still has to do. The schedule is derived, so moving it is not a change anybody
  could ask to have explained; guarded on the version it was read at, so a real writer that
  moved the match in between keeps its own answer. _Avoid_: rescheduling, touching.
- **Take a wake** (`matches.TakeMatchWake`) — one look at one match: re-derive, act on whatever
  the ladder now says, re-arm. **Taking the same wake twice is looking twice**, and the second
  look finds a record the first already moved — which is why there is no table of handled keys
  and no exactly-once guarantee to keep. _Avoid_: handle, process, fire.
- **Effective-dated series** (`clubs.Series`) — the shape a fact that carries history
  takes: an ordered tuple of versions, each with a value, a `validFrom`, a nullable
  `validTo` and an actor, **at most one of them open, and it is the last**. A change closes
  the row in force and opens a new one in one operation, so the two cannot be written apart
  and get out of step. Intervals are half-open, the same convention a reservation's claimed
  range uses, so *what was this on Friday at 16:00* has exactly one answer at the instant of
  the change as well as either side of it. The fold is *the row whose interval contains
  now*, not a replay — which is event sourcing's non-drift property without event sourcing's
  machinery, because the current value is not a copy kept beside the history, it **is** the
  open row. _Avoid_: an audit table beside a mutable row (two representations of one fact),
  a `current` flag, updating a version in place.
- **Open row** — the version of a series in force: `validTo IS NULL`. Guarded twice, and the
  two guards answer different questions — a **partial unique index** stops a second one
  reaching disk, and the `Series` type stops one being constructed. `app/modules/clubs/…
  /sqlalchemy_club_models.py` declares the index for **both** engines, so the guarantee holds
  in the fast SQLite suite as well as in production. _Avoid_: `WHERE` clauses spelled
  differently per series; a whole-table unique index, which refuses history.
- **Cover** (`kernel.Cover`) — whether a court has a roof: `indoor` or `outdoor`, and no
  third value in v1. It is the **kernel's** rather than Now's, because Clubs authors it and
  Now renders it on the spine of every card, and a closed two-value set declared in two
  contexts is a mapper between two spellings of one fact. A roof is `indoor`: the question
  the card answers is *will I be rained on*, and a canopy answers that the way a wall does —
  what it does not answer is *will I be cold*, which is the loss ADR-0090 takes knowingly.
  `COVER_COUNT` is pinned, so a third value is a decision in a diff **and** a client release,
  because each client holds an exhaustive table over these names. _Avoid_: a boolean
  `is_indoor`; a second copy in a module's own vocabulary; *covered* as a third value nobody
  authored.
- **The two facts a category is constrained on** (`clubs.CourtCategory`) — its **sport** and
  its **cover**, both required at construction with no default, and everything else about a
  category is the club's. The two constraints are one argument: a category spanning two sports
  makes a seat share undefined, and one spanning two roofs makes the card lie, because a
  player swapped onto the other court in November has been sold something else. It is the same
  argument ADR-0079 used to move the price off a court. Nothing enforces that a club authored
  honestly — only the venue knows, which is why the category is club-authored at all. _Avoid_:
  a platform enum of surfaces; a per-court cover, which no card composed before match day
  could read.
- **A roof is a move, not an edit** — a category's cover **never changes**, and there is no
  operation that changes one. A club that roofs a court has changed the *court*, so the court
  **moves category**, which closes its catalogue row and opens a new one — the history is
  ADR-0077's series, already built, rather than a fourth versioned fact. `_update_categories`
  writes a category's name, rate and retirement in place and writes neither constrained fact,
  and that absence is asserted. Note that a cover is read **live** where a rate is **copied
  onto the match at booking**, and both are right: the price was agreed when the match was
  posted, and the roof is a fact about the evening she is walking into. _Avoid_: a
  `reprice_category`-shaped setter for the cover; effective-dating the category.
- **The one-off backfill** (`migrations/…/0013_category_cover.py`) — where a category's cover
  came from for rows that already existed: its own free-text **name**, parsed once, in a
  migration, in a diff somebody reviewed. That is the whole distinction from the thing the
  product refuses — parsing it on the compose path would be deriving a domain fact from copy
  on the busiest read there is. A name containing *indoor* becomes `indoor` and **everything
  else becomes `outdoor`**, because the answer that never claims shelter a club did not
  declare is the one that costs a player a match rather than a soaking. Three statements
  rather than one, so the constraint is honest: an added column with **no server default**, a
  backfill, then `NOT NULL`. _Avoid_: a server default; `LIKE` without `lower()`, which is
  case-insensitive on SQLite and case-sensitive on the only database this runs against.
- **Record repository** — the port a use case loads and saves a **record aggregate** through,
  e.g. `ClubRepository`. Neither of the other two kinds: it is not an *aggregate repository*
  (there is no stream to replay and no stream version) and not a *read-model repository*
  (it writes). Its concurrency guard is a **version column**, compared in the same UPDATE
  that bumps it, so a stale writer loses on `rowcount` rather than on whichever child table
  it happened to touch. _Avoid_: reading the version and comparing it in Python; merging
  two writers' changes.
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
  context created tomorrow is fenced the day it exists — it fenced Clubs, Courts, Bookings
  and Matches before any of them had a line of code, and Money before it has one now. A use
  case that needs a configured value
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

- **Seed club** — a deterministic development club created by `app/seeds/clubs.py`, named
  for the **state** it represents, with its name doubling as its natural key so the two
  cannot drift. Seven of them, one per edge the Clubs context exists to represent: a club that
  never holds speculatively, one that tightened its cap, one whose sport is priced as two
  categories, one that retired a court, one that retired a category, one that changed its
  bank, and one that needs a turnaround between bookings. Every payout destination carries an
  IBAN whose check digits are invalid on purpose —
  the reserved-TLD argument, one context over. _Avoid_: nine plausible venues, which is one
  scenario nine times.
- **Club claim** — what a seeded club's *name* promises, as a predicate over the stored club
  plus the sentence it is promising. Checked on every run, including one that created
  nothing. Deliberately **not** shaped like a `Rating claim`: a rated player's band is
  produced by an engine that can be retuned, where a club's state is exactly what the catalog
  authored — so checking the authored numbers against themselves would be a tautology, and
  what is worth checking is that the state the name *describes* is still there. _Avoid_:
  asserting the catalog's own numbers back; a claim checked only on the run that created the
  club.
- **Reservation record** (`courts.Reservation`) — one court, one time range, claimed, with a
  version and a `releasedAt`. Two intervals, and they are different facts: **played** is what
  the players get and the only one anybody is shown, **claimed** is what excludes everybody
  else. A record rather than a stream (ADR-0034 one context over), so a court's booking
  history is a query over reservations rather than a fold. _Avoid_: one interval; a
  reservation deleted rather than released; a claim narrower than the play it is for.
- **Holder** (`courts.Holder`) — who a reservation is claimed for, as a closed union of three:
  a **Booking** (a player bought the court), a **court hold** (a match's speculative claim,
  granted and withdrawn by the hold ladder), and a **club block** (the venue's own — a league
  night, a lesson, a walk-in). Whether the club's `turnaroundMin` widens the claim is read off
  the holder and stored nowhere, because the holder already says it. _Avoid_: a `padded` or
  `origin` column beside the holder — one fact spelled twice, and the day they disagree the
  turnaround is applied to a block that was already padded.
- **Claimed vs played** — `claimed = played` for a club block, and `played` widened at the
  **tail** by `turnaroundMin` for anything Raketa creates. The tail alone, because padding
  both ends charges the gap twice; and it composes only because intervals are half-open, so
  the next claim may begin the instant this one ends. _Avoid_: padding a club-published block,
  which double-books the gap it already contains.
- **The exclusion constraint** (`ex_reservations_no_overlapping_claim`) — `EXCLUDE USING gist
  (court_id WITH =, tstzrange(claimed_from, claimed_to, '[)') WITH &&) WHERE (released_at IS
  NULL)`. The whole of ADR-0035 as one line of DDL, and the reason double-booking is
  structurally impossible rather than unlikely. Four properties, each a different constraint if
  it moves: keyed on the court, testing **overlap** rather than adjacency, half-open, and
  partial over the live rows. Declared by a dialect-scoped `after_create` listener, because an
  `ExcludeConstraint` in the metadata would break `create_all` on SQLite. _Avoid_: a unique
  index on a slot's start, which lets 14:00–15:30 and 14:30–16:00 share a court.
- **Losing inventory** (`courts.InventoryLost`) — *no court of this category is free for this
  window*. **Always a query result, never a race outcome**: the constraint makes the race
  impossible rather than detectable, so there is exactly one story to tell the player. A
  retired category answers the same way as a fully-booked one. _Avoid_: telling a player
  anything about a race; `CourtAlreadyClaimed` reaching a caller outside the context.
- **The court is taken** (`courts.COURT_IS_TAKEN`) — the two SQLSTATEs that mean *somebody
  else reached this court*: `23P01` (`exclusion_violation`) and `40P01` (`deadlock_detected`).
  The second arrives when two writers are exactly simultaneous — a GiST exclusion index
  inserts its entry before it scans for a conflict, so each can wait on the other — and it is
  **not** an `IntegrityError`, which is why the adapter catches `DBAPIError`. Both mean *look
  again*, and the use case re-asks with that court removed. _Avoid_: catching `IntegrityError`
  alone, which lets the closest race of all escape as a 500.
- **Availability, projected** (`courts.free_courts`) — *is a court of this category free for
  this window*, computed from reservations on every ask. **No availability number is stored
  anywhere**, so there is nothing beside the rows to drift from — and a club's own block takes
  a court out of inventory without anything having to remember to decrement it. _Avoid_: a
  counter against `(club, category, interval)`, which is the same defect as a uniqueness rule
  on a slot's start.
- **Published court** (`courts.PublishedCourt`) — what a reader outside the context may be
  told: the **category** always, and the **court** only from `kernel.court_named_at(start)` —
  fifteen minutes before play, the same constant the door code reads. That is what lets a seat
  price be quoted before a court exists and stay fixed when one is assigned. _Avoid_: naming a
  court on a card, which promises something the club never sold and may reassign.
- **Seed reservation** — a deterministic development claim created by `app/seeds/courts.py`,
  named for the **state** it represents and checked against the stored reservation on every
  run. Its window is a **fixed absolute instant**, not an offset from now: *next Tuesday at
  18:00* computed at run time is a different Tuesday tomorrow, and the run that creates nothing
  could never happen. Two of the three holders are **authored** here; a match-held claim is a
  court the **hold ladder** grants, so it is never written into this catalog and arrives
  anyway, because the seeded matches run the same use cases a request runs. _Avoid_: a uuid standing in for an aggregate, which satisfies every
  import walk in the suite and is still an invented context.

- **Match aggregate** (`matches.Match`) — **one** aggregate, a **record with a version and an
  outbox**, and the only racket-sport context that is not event-sourced (ADR-0034). *Enrolled*
  is a relationship and not an object: a seat names a player or it does not, and there is no
  `Enrolment` with a lifecycle. Concurrency is a `version` column compared in the UPDATE that
  bumps it — the guarantee ADR-0002 took from a stream, without the stream. `as_record()` hands
  the kernel a `MatchRecord` and **needs no other read**, which is what makes *the busiest
  object in the product the cheapest to read* true rather than aspirational. _Avoid_: a match
  event store, an `Enrolment` aggregate, a `status` column.
- **The five kinds** — how every stored fact on a match is classified, by the question *may a
  reader derive this*: **Constitutive** (chosen at creation — sport, share, counted, created,
  the category, the policy snapshot), **Occupancy** (seats, vacancies, transferring, seats
  opened), **Allocation** (`held_since`, `released_at`, `inventory_lost`), **Crossing**
  (`committed_at` — derivable once, then frozen), **Declaration** (the two cancellations, the
  court lock, the extension, the no-show, the score's four facts). A new fact declares its kind
  before it is added, and *a reader cannot derive this* has to be true of it. **Receipts are an
  annotation, not a sixth kind**: `form_cancelled` and `checkpoint_cancelled` record only that
  the refund, the court release and the notice completed, so a downed timekeeper delays the
  money and never the truth. _Avoid_: a stored `filled`, a stored situation, a `phase` column.
- **The policy snapshot** — the four hold-policy fields a match copies from its club **when it
  is posted**, and reads for the rest of its life. ADR-0077 puts a club value that must be
  honoured *as booked* on the match record as a Constitutive fact rather than in a temporal
  query, and it is also what lets a situation be resolved from one row-set with no club fetch
  on Now's path. The cost is stated rather than hidden: a club that tightens its cap does not
  reach a match already posted, and if the hold ladder decides it must, the fix is a **write**
  that refreshes the snapshot — never a club read on the compose path. _Avoid_: joining the
  club's series to resolve a card.
- **The announcement obligation** (`matches.events`) — ADR-0034's one non-ordinary rule: the
  match keeps no history, so **every change a support agent would need to explain is its own
  named event** and there is no generic *match updated*. Twenty-one names, registered under
  durable strings, published onto the transactional outbox in the transaction that writes the
  row. Nothing mechanical catches an event published too coarsely, so
  `tests/unit/test_match_events.py` walks the aggregate and fails when a mutating method
  announces nothing. _Avoid_: one `MatchChanged` carrying a reason enum, which is the forbidden
  event wearing a disguise.
- **Seat and vacancy** (`matches.Seat`, `matches.Vacancy`) — a seat is its **position** and is
  never created or destroyed, only occupied and emptied; *taken* and *paid* are two facts, and
  folding them is how a match reads full while a seat may still lapse. A vacancy is the hole a
  departure left, **filled, never deleted**, carrying no amount and no outcome — settlement and
  occupancy are independent axes (ADR-0033), and what a leaver recovered belongs to her
  departure. Taking a seat closes the **oldest** open hole, so the newest still says when this
  match last lost somebody. _Avoid_: a seat state enum with a third value, an amount on a hole.
- **Departure record** (`matches.Departure`) — the other half of a leaving, beside the hole:
  whose seat, when, the **label she was shown** (`quoted`), her money, and the outcome. Its own
  file and its own table, because a hole and a settlement have two lifecycles — a filler closes
  the **oldest open vacancy** and settles the **oldest unsettled departure**, and ADR-0033 calls
  those two traversals over one list *"a real implementation hazard"* whose symptom is *one
  player was never refunded*, months later, and never an error. Found by the **player**, never
  by the seat she left: the seat may be somebody else's by then, which is the whole point.
  _Avoid_: one loop doing both queues, a departure keyed on a seat.
- **Leaver money** (`kernel.NothingTaken`, `kernel.Recoverable`) — what a departure took, in
  **two forms** rather than one with an optional amount (ADR-0072). `Recoverable` names what she
  paid in; whether any of it comes back is the *outcome's* answer, so a forfeited departure still
  carries the figure. `NothingTaken` has **no field that could hold an amount**, and reading one
  off the union without narrowing does not typecheck — which is what makes the refusal bite.
  Stored as a nullable column and **never a zero**: *nothing was taken* and *nothing has come
  back yet* are opposite sentences a blank cannot tell apart. _Avoid_: `amount: Grosze | None`.
- **Raising an outcome** (`matches.Departure.raise_to`) — the **only** operation that moves a
  settlement, and it cannot lower one. ADR-0030's *"nothing may reduce a settled outcome"* is
  therefore a property of the type rather than a rule its callers remember: an unsettled
  departure settles, a settled one improves, and anything else moves nothing and announces
  nothing. A departure that took nothing never moves at all — there is no money to return.
- **The two questions** (`kernel.live_outcome`, `kernel.refill_outcome`) — *what do I get if I
  leave now* and *what does somebody who has already left recover when a filler pays now*. They
  agree everywhere except past the **checkpoint**, where leaving is quoted `forfeited` and a
  filler still pays the rescue price — so a late filler **improves** what the leaver had. The
  asymmetry is safe exactly because settlement is monotonic upward: a quote may under-promise
  for ever and may never over-promise once. _Avoid_: one function answering both.
- **Settling at the start** (`matches.Match.settle_departures_if_closed`) — a departure nobody
  filled forfeits at `start`, which is where the timekeeper's `play` wake finds it. ADR-0030
  *defines* settlement as *"the moment no further **seat** event can change it"* and illustrates
  it with the join cutoff; ADR-0081 landed later and made a seat claim *"honoured to
  completion"* past that cutoff, so the illustration stopped being the last seat event. `start`
  is the instant this aggregate refuses every seat move, so it is **derivably** the definition's
  answer. Nobody settles early, which is the only direction that matters.
- **Seat claim** (`matches.SeatClaim`, `kernel.SeatClaim`) — five minutes of exclusive right
  to buy **one seat**, and **not a seat state** (ADR-0081). The seat below it is untouched:
  still empty, still absent from the fill count, still earning the match no court and still
  imputed by the forecast rather than carrying the claimant's level — which is what keeps the
  glossary's *"there is no window in which a seat is taken and unpaid by the taker"* true word
  for word. Its own table, **ended and never deleted**, because the thirty-second cooldown is
  measured from `ended_at`. **Live is composed** — unended *and* not yet expired — so it is
  over at its own instant whether or not any look has written the receipt, exactly as a stale
  court hold is. _Avoid_: widening *held*, a fourth seat state, a thirty-seventh situation.
- **One rule ends a claim** (`matches.SeatClaim.end`) — one mutator for all three endings:
  the five minutes running out, the seat being bought, and the match dying underneath it.
  `min(at, expires_at)`, so a reaper arriving late dates the lapse when it **happened** rather
  than when it noticed — a worker that was down for an hour must not extend anybody's thirty
  seconds by an hour. Which of the three it was rides on the announcement, never on the row.
  _Avoid_: an `ending` column, and a second rule for a match that dies.
- **Reaping** (`matches.Match.reap_lapsed_claims`) — writing the receipt for a claim whose
  window has run out. It **changes nothing and records something**, which is why the timekeeper
  can ask on every look and why asking twice is free. Asked by two callers: the wake, and
  `open_claim`, which reaps **before** it decides — the write a stale row would block is the
  write that clears it, so a player never waits on a scheduled look to be allowed to tap.
  _Avoid_: dating the receipt at the reap.
- **Exclusivity** (`kernel.claimed_seats`, `matches.Match.seats_under_claim`) — *is this seat
  spoken for*, composed from the claims and the clock. Read by three: the aggregate refusing a
  second claim or an invitation onto the same seat, the invitation cascade deciding whether to
  offer it at all (`Raketa02/Raketa#82`), and the card deciding whether to draw an exit. **A
  lapse resumes the offers with no write at all** — the answer simply changes — and nobody is
  told twice, because nothing was retracted and the cascade keeps its own record of who it
  reached. _Avoid_: a `suppressed` flag on anything.
- **A deadline and not a trapdoor** — `joinCut` is read by `open_claim` and by nothing else. A
  claim already running when it passes is **honoured to completion** (ADR-0081), so somebody
  who tapped at 13:29 against a 13:30 cutoff pays at 13:33 and plays; what is refused is
  *starting* one. It is also why settlement lands at `start` rather than at the cutoff — see
  **Settling at the start**. _Avoid_: the cutoff in `redeem_claim`.
- **Seed match** — a deterministic development match created by `app/seeds/matches.py`, named
  for the **`Situation` it resolves to** and checked by `kernel.situation` against the stored
  record on every run, at the scenario's own fixed instant. The strongest name-check in the
  seed system, because a match's state is derived: retune a threshold and the seed stops and
  says which account's screen just moved. Written on the **seeded week's clock** rather than
  the wall clock — a match *is* its clock, so `committed_at` from a wall clock would make the
  name a claim about the day the seed ran. A scenario that loses a player also names what
  that player's **money** is — settled or open, and whether her card names an amount — checked
  against the stored departures, and the only claim in the seed system that is about a refund.
  _Avoid_: a claim with no instant, which is not a claim.

- **Composed screen** (`modules/now`) — a **read** with no aggregate behind it: Now owns no
  state, writes nothing and stores nothing, and what it does own is the *composition* —
  which regions exist, in what order, and what a card carries. It reaches every other
  context through a port of its own (`now.domain.ports`) rather than through that context's
  repository, so another context reshaping a read Now never asked for does not reach the
  composer. _Avoid_: calling it a context — it makes no decision that could be wrong.
- **Region vs shelf** — a **region** is one of Now's three ordered lists and is **present
  and empty** when it holds nothing; a **shelf** is one row inside the shelves region and
  is **absent** when it holds nothing. The asymmetry is the whole rule: a shelf makes a
  *claim*, and a row appearing every week to say *nothing worth waiting for* is a row
  players learn to scroll past. A region makes none. _Avoid_: an empty shelf, and an absent
  region — the two spellings of the same bug in opposite directions.
- **Block** (`now.screen.Block`, `now.vocabulary.BlockType`) — one entry in the shelves
  region, which is a **shelf** or **the door**. The list stopped being homogeneous when
  ADR-0084 put the door *in* it, so each entry carries `block_type` — the same rule
  `card_type` follows one ring in: an entry is identified by what it *is*, never by its
  position, so a client narrows once and the server may reorder freely. The field is named
  `shelves` still, because renaming it would break every client reading a region that has
  not otherwise changed, for a word. _Avoid_: `is_door`, which makes a third block either
  a lie or a second boolean beside the first.
- **The door** (`now.screen.Door`) — the way into a sport's questionnaire, composed into
  the shelves list **in the position the ranked shelves would occupy** for a viewer who
  holds no rating at the sport she asked for. It is a block the **server** put there and
  never an inference the phone draws from absent shelves, which would fire wrongly on any
  day the city genuinely has nothing in a sport she *is* rated at. It occupies those
  shelves' position rather than sitting above them: unrated means they are **absent**, not
  empty. *New on Raketa* and *New clubs* still compose **beneath** it — the clubs are the
  argument for spending the two minutes. _Avoid_: a flag, an empty ranked shelf beside it,
  and a door on `all` — which names only sports she is rated at, so it names none she is
  not.
- **Door code** (`now.vocabulary.DoorCode`) — which of the door's two sentences it shows:
  `noRunYet` for a player who has never started this sport's questionnaire, `runParked`
  for one whose run is waiting. **One block type, two codes**, so the client holds one row
  per sentence and never learns that two states produced them. Named for the fact rather
  than for the words, like every code here. A parked run **never expires** (ADR-0020's own
  control walks back through answers), so this is existence and never freshness. _Avoid_:
  the sport or a destination beside it — she named the sport on the request and still holds
  it, and the code determines the destination exactly as an act code does.
- **Parked run** (`now.ParkedRuns`, `ParkedRunsFromAssessments`) — whether this sport's
  questionnaire is already part-answered, which is the one fact deciding which of the
  door's two sentences shows. A **boolean and not the run**: Now composes a code from it,
  and a port answering with an aggregate would invite a later session to read a transcript
  on the home screen's path. Asked **only when a door is being drawn**, so a chip the
  viewer is rated at never pays for it. _Avoid_: reading a run parked at another sport as
  an answer for this one — the question is asked by pair, and *pick up where you left off*
  into a questionnaire she has never opened is worse than the honest ask.
- **Rated at one sport** (`now.RatedSports.holds`) — the by-pair question beside
  `for_player`'s whole-set replay. A rating stream is keyed by `(player, sport)`, so this
  is one lookup where the set replays every rating she holds — and a named chip, the sport
  bar's busiest path, now has exactly this question to ask before it knows whether a door
  is owed. _Avoid_: filtering `for_player` in the caller, which pays the replay to answer
  a question about one sport.
- **Spine and situation half** — the two nested halves of a card. The **spine** is read by
  every phone that has ever shipped; the **situation half** (`{situation, facts}`) is read
  only by one that knows the name. A client meeting an unknown situation draws the spine
  and drops the status line — it never skips the card. That is a **shape** rather than a
  discipline: a flat card would let the first situation-dependent field added at the top
  level break it in silence. _Avoid_: a situation-dependent field on the spine.
- **Stamp** — one monotonically increasing integer per region and one per card, and **no
  screen-level stamp**. Derived from **when the answer was composed** (`stamp_at`, whole
  milliseconds since the epoch), not from a record's version: the race it arbitrates is a
  pull and a tap racing, where both answers read the same version, and a card whose
  situation moved because a threshold passed has no version change at all. _Avoid_: an
  opaque string, which cannot answer *is this newer than what I hold*.
- **Act code** (`now.vocabulary.ActCode`) — the one act a card may name, from a closed set
  of seven, **composed by the server** and carried in the spine as a code alone with no
  target beside it. Twenty-six of the thirty-six situations name none, and that is not a
  hole to patch: `Open match` died with its destination. An eighth arrives **with the
  surface that receives it**, never ahead of it. _Avoid_: `{label, target}`, and a fallback.
- **Card hold reason** (`now.vocabulary.CARD_HOLD_REASON_OF`) — the five of the kernel's
  twelve `HoldReason`s that reach a card, as a **total table** off the kernel's own
  vocabulary, asserted exhaustive at module load. The second such projection in the tree
  after `MATCH_PHASE_OF`, and the same rule: a consumer needing a coarser vocabulary writes
  a table off the kernel's, never a second ladder. _Avoid_: deriving it from a name prefix,
  which absorbs a thirteenth kernel reason into *no reason at all*.
- **Cause** (`kernel.Cause`) — why money moved and why a match ended, in five closed names.
  In the kernel because Matches produces it, Money records it and Now renders it, and a
  second implementation of any of the three would be a defect — ADR-0022's own test.
  `settlementReopened` is in the enumeration and reaches no card. _Avoid_: a per-context
  copy, and a free-text reason beside it.
- **Membership against row** (`now.NewArrivals`, `now.ArrivalRows`) — the split shelves 4
  and 5 are built on: *who is new here* is the same answer for everybody in a city looking
  at one sport and is **cached**; *what a card prints* is read live and is **not**. Two
  ports rather than four methods on one, because that is what makes the split structural —
  the cache's value type is `tuple[UUID, ...]`, so *the set and not the row* is a type
  error rather than a rule. One implementation answers both: they are the same eligibility
  asked at two depths. _Avoid_: caching a nickname or a club's name, which is fifteen
  minutes of telling a player about a venue that no longer goes by that name.
- **New-arrivals set** (`now.ArrivalKey`, `now.ArrivalSets`, `InMemoryArrivalSets`) — Now's
  only cache today, keyed `city : sport : kind`, holding identifiers, expiring after
  **fifteen minutes** and **never invalidated**. The absence of an invalidation path is the
  decision, not an omission: the shelves' own clocks are 30 and 60 **days**, so a quarter
  of an hour of lag is invisible against them, and a cache with nothing to invalidate is the
  one shape that cannot go wrong. In-process and hung off `app.state` rather than in Redis —
  a Redis adapter would arrive with a client, a connection lifetime, a failure policy and a
  serialisation format, none of which a test run can exercise. _Avoid_: a `forget`, and a
  module-level singleton, which survives from one test's database into another's.
- **The unknown city** (`now.CITY_UNKNOWN`) — what the key's city component reads as while
  no context stores a player's city (`Raketa02/Raketa#102`). The component stays in the key
  rather than being dropped until it has a source: a key that *gains* a component later is
  a key whose old entries answer the wrong city for fifteen minutes on the day it lands.
  _Avoid_: keying on sport and kind alone and adding the city afterwards.
- **Level and the quiet marker** (`now.screen.Level`) — what a person card prints: μ on the
  1,0–5,0 scale, and **one boolean** meaning *a questionnaire is the whole evidence behind
  this*. A boolean because the alternative was a second number — onboarding cannot exceed
  30 % Confidence, and printing that percentage beside the Level is the gauge ADR-0037
  refused, while printing nothing claims a certainty the platform does not have. Derived
  from the Rating status against `engines.assessment.STATUS_INITIAL_ESTIMATE`, which lives
  in the shared engine vocabulary so no reader holds its own copy of the string. _Avoid_:
  shipping the three-value Rating status, which is a table the client would hold for one
  question, and a Level a rating does not exist for.
- **Closeness, never descending** (`now.by_closeness`) — *New on Raketa* is ordered by the
  absolute gap between an arrival's Level and the viewer's **at the same sport**. Descending
  by Level makes the shelf a leaderboard: it tells every new player where they rank on the
  home screen of every stranger in the city, and puts the players the viewer can least enjoy
  a game with at the front. A viewer the platform cannot compare anybody against still gets
  a shelf — those fall to the back, newest first — because **neither shelf has a floor**:
  there is no such thing as a player who is insufficiently new. _Avoid_: dropping somebody
  for being far, and breaking a tie on an id, which a shared creation stamp makes random.
- **Newest first, never nearest** (`now.by_arrival`) — *New clubs* is ordered by arrival with
  distance breaking ties, because the shelf's title is its claim and ordering by distance
  would make a shelf that says *this is new* answer *this is near*. A club whose distance is
  unknown sorts **after** one whose distance is known: absent is not nearest. _Avoid_: a zero
  where there is no Distance anchor.
- **Enrolment** (`now.Enrolment`, `EnrolledFromMatches`) — one match the viewer holds a
  seat in **or has left**, and everything five contexts say about it: the kernel record, the
  club's name/zone/roof, her share, the whole court, the reserved court, the score with its
  players named, her departure and what she has actually funded. There is no enrolment row
  to read — *enrolment is a relationship* — so the port stands in for one, over a seat that
  names her or a departure that does. It answers **facts and decides nothing**: the court is
  returned whether or not it may be printed, and the score in the order it was stored.
  _Avoid_: applying a rule in the adapter, which puts it in two places.
- **The card's tail** (`now.CARD_TAIL`, `Match.closed_at`) — a card lives **twenty-four
  hours from the moment it closed**, and never from when the match would have ended
  (ADR-0073, narrowing ADR-0048). A played match closed at `match_end` and a reader can
  derive that; a cancelled one closed when somebody cancelled it and no reader can, so the
  five endings store the instant. One consequence is worth knowing rather than discovering:
  `playedNoScore` begins exactly at `matchEnd + 24 h`, so **it never appears on Now** — it is
  the result route's rendering. _Avoid_: `matchEnd + 24 h` on a cancellation, which leaves a
  Thursday cancellation on a home screen until Sunday.
- **The card's clock** (`kernel.card_clock`) — *the next moment at which something happens to
  the viewer whether they act or not*, composed as **the soonest boundary the ladder itself
  reads** ahead of now. One rule and not thirty-six judgements: a boundary is by definition
  an instant at which the card's sentence changes. It is `next_wake` minus one thing —
  **a claim's expiry, which no rung reads** — because a stranger's five minutes are not the
  viewer's; her own claim is passed in and wins outright. A terminal match has no boundaries
  at all, so *over or cancelled counts to nothing* falls out rather than being a case beside
  it. _Avoid_: serialising `next_wake_at`, which is a `min()` over candidates the player is
  not being told about (ADR-0053).
- **Counting is by money** (`now.SeatCounts`, `kernel.turned_up`) — `paid`, `held` and
  `turned_up` are three numbers and never one with arithmetic on the phone. A held seat is a
  name with no money behind it, so folding it into the count says *full* while a seat may
  lapse; and **every number a sentence prints is sent as that number**, because *one less
  than the seats* stops being minus one the moment a doubles match loses two people.
  `turned_up` is present exactly once the match has been played — a clock condition, not a
  per-situation judgement. _Avoid_: deriving attendance from `filled` anywhere downstream.
- **A fact per rule, never a table of thirty-six** (`now.compose_enrolled`) — a hold, a
  court's name, a refund, an owner's exposure, a score and a departure are each composed
  **exactly when the fact exists**, and no situation is named anywhere in the composition.
  The counting and the court's total are unconditional because every match has them.
  _Avoid_: a `Situation → which facts` table, which is the maintenance failure ADR-0073
  names by name.
- **The court's total against her share** (`now.SituationFacts.court_total`) — two money
  numbers on one card, on purpose. `price` is the spine's and is *written for whoever is
  looking*; `court_total` is the subject of `{price} settled to the club` and is **the same
  number for every audience**, because what that sentence tells the viewer is *this game is
  happening*. _Avoid_: reusing the share there — her money left days ago.
- **Refund destination** (`now.vocabulary.RefundDestination`, `REFUND_DESTINATION_OF`) —
  `card` or `clubCredit`, a **total** table over `Cause`. The destination fixes the tense: a
  card refund is never claimed to have landed, and a club credit is definite because it
  genuinely is instant. It crosses even though it is a function of the cause, because
  deriving it is a rule and the phone holds none. _Avoid_: an *arrived* flag, which would
  ship on every cancellation card and never render.
- **A leaver's two payload forms** (`now.CardDeparture`, `now.vocabulary.DepartureForm`) —
  `recoverable` names what she paid and what became of it; `nothingTaken` has **no field that
  could hold an amount**. Never one payload with an optional figure: *nothing was taken* and
  *nothing has come back yet* are opposite sentences and a blank cannot tell them apart. Her
  card keeps the **match's** own progress beside it, because a refill is the only thing that
  decides her outcome. _Avoid_: dropping a leaver from the strip.
- **A private owner's two figures** (`now.OwnerExposure`) — what the marketplace has
  **recovered** and the **whole court** she still guarantees, and they disagree on purpose:
  every marketplace payer is refunded in full if the format is unmet, so her exposure does
  not move until it fills. Both are facts about the **court** and not about the viewer,
  because the record carries no owner (`Raketa02/Raketa#99`); every private situation in v1
  arrives from seed. _Avoid_: showing the guarantee alone, which reads as broken.
- **The no-sentence walk** (`tests/unit/test_now_vocabulary.py`) — the AST walk asserting
  that nothing under `app/modules/now/` composes a phrase a player could read. Three kinds
  are exempt by name and for a stated reason: a docstring, an `invariant()` message, and a
  `summary=`/`description=` keyword. It carries its own negative control, because a guard
  nobody has seen fire is one nobody should watch. _Avoid_: exempting a string for being
  short.

- **Postgres-only guarantee** — a rule the database enforces that SQLite cannot express,
  so a suite running on SQLite can state it in a comment and enforce nothing. Three exist:
  a reservation's overlapping-interval exclusion (`EXCLUDE USING gist`), the partial unique
  index keeping one open row per versioned series, and `FOR UPDATE SKIP LOCKED` outbox
  claiming. The first is now on a real table — see **The exclusion constraint** above. Their
  tests live in `tests/integration/` and **nowhere else**; the API suite
  stays on in-memory SQLite, which is what makes it fast. _Avoid_: asserting one of these
  against SQLite, where the assertion passes and means nothing.
- **The harness guard** — the rule that a Postgres-only case **skips on a laptop and fails
  in a pipeline**. Keyed on `CI`, which the runner sets, rather than on `POSTGRES_TEST_URL`,
  which `.github/workflows/ci.yml` sets: keying the requirement on a variable the workflow
  owns means deleting the variable deletes the requirement, and the pipeline reports a
  guarantee as enforced while enforcing nothing. Checked by
  `tests/integration/test_harness_guard.py`, which needs no database and therefore runs on
  every `make check`. _Avoid_: `pytest.skip` on a missing database with no `CI` branch —
  the shape this replaced.

- **Ledger stream** (`money.ledger_stream_id`) — one event-sourced stream per player, its
  id **derived** as `uuid5(namespace, player)` rather than minted and stored, on
  ADR-0019's rule. A lookup table can be missing a row, and the miss is a second stream for
  a player who already has one — after which her balance is the fold of whichever half was
  read. Money is the first racket-sport context to be event-sourced, and the only one
  (ADR-0055); Clubs, Courts, Bookings and Matches are all records with a version, which is
  what a genuinely per-context choice looks like. _Avoid_: a `ledgers` table, and a stream
  per reservation — a reservation protects no invariant.
- **Movement** (`money.Movement`) — one money event: `payer → payee`, gross grosze, a seat,
  a reservation, a reference and a cause. Frozen, never edited, never deleted. **The
  direction is the parties and never the sign**: the amount is strictly positive and a
  refund is `Raketa → player`, so a fold is three sums over positive numbers rather than
  one over terms that already carry a sign. _Avoid_: a negative amount, and a `held` flag —
  ADR-0056 retires it by name.
- **Party** (`money.Party`) — `PlayerParty | ClubParty | RaketaParty`, three `@final`
  members and a union rather than an enum beside a nullable id, so *Raketa with an id* and
  *a player without one* are unwritable. **A club is never a payer** (ADR-0045), refused at
  construction *and* asserted over what is stored — the door guards what was written after
  the door existed. _Avoid_: a fourth party, and an enum plus `party_id`.
- **One player per stream, at most one per movement** — how ADR-0055's *"every movement has
  exactly one player party"* is read. Its own justification is *"so no movement is homeless
  and none is written to two streams"*, and that is what is enforced: a movement lives on
  exactly one player's ledger, and when it names a player it names **that** player. The
  strict reading and ADR-0056 cannot both hold — an online share's `Raketa → club` half
  names no player, and without it `held` is not derivable. _Avoid_: two player parties on
  one movement, which is the half that *is* refused.
- **Movement cause** (`money.MovementCause`) — eighteen closed names, the **wider**
  enumeration with `kernel.Cause`'s five embedded **by value**, and the inclusion asserted
  at module load. Wider rather than growing the kernel's, because `Cause` crosses the wire
  as an OpenAPI enum both clients build an exhaustive table over, and thirteen ledger-only
  names would be thirteen sentences no card can print. Same shape as `CARD_HOLD_REASON_OF`,
  pointed the other way. _Avoid_: restating a shared name's string, and a free-text reason.
- **Cause rules** (`money.CAUSE_RULES`) — one total table over `MovementCause`, asserted
  exhaustive at module load, answering two questions per cause: *does it move the balance*
  and *does it name a seat*. Exactly two move a balance (`collectionFailed`, `debtCleared`)
  and exactly one names no seat (`debtCleared`). _Avoid_: a nineteenth cause added without
  answering both — which is a build error here, deliberately.
- **Balance** (`Ledger.balance`) — zero or negative, folded from the two balance-bearing
  causes alone. An ordinary seat payment leaves it at zero, because paying for a court is
  not owing for one; a half-refunded leaver is at zero too, because she lost half rather
  than owing it. **Not clamped**: a positive balance is stored value, and clamping would
  hide it from the one assertion that exists to find it. _Avoid_: a net of every movement,
  which reads an ordinary payment as a 38 zł debt.
- **Held, and the float** (`Ledger.held_for`, `Ledger.raketa_float`) — both derived and
  stored nowhere. `held_for(seat)` is ADR-0056's own formula,
  `Σ(player→Raketa) − Σ(Raketa→club) − Σ(Raketa→player)`. It goes **negative** on the
  private path between a refund Raketa advanced and the owner charge that recovers it, and
  that is the working-capital position ADR-0045 names rather than a defect. _Avoid_: a
  stored figure, and an assertion that `held` is non-negative.
- **Reference** (`money.Reference`) — a kind and a token, printed `PAY-…` / `REF-…` /
  `REV-…`. The kind **is** the prefix rather than a field beside a free string, so the two
  cannot disagree about whether a movement is a compensation — which the reconciliation
  reads by kind. Unique within a ledger, which is the duplicate-webhook guard. _Avoid_: a
  VAT invoice number, which is not a reference and not this context's.
- **Compensation** (`Ledger.compensate`) — a correction is a **second** movement with the
  parties reversed, the same amount, a `REV-` reference and **its own cause**: the reason
  the correction was needed is not the reason the original happened. `shareOnline`
  compensated by `claimLapsed` is ADR-0081's shape. _Avoid_: amending a movement, and a
  compensation filed under `PAY-`.
- **The append-only walk** (`tests/unit/test_money_is_append_only.py`) — an AST walk that
  refuses every write to `Ledger._recorded` but the one `append` in `_apply` that replays a
  stored event. It exists because the behavioural tests were **measured** not to cover the
  rule: a `_prune` dropping the oldest movements past a threshold no fixture reaches passes
  the whole unit suite, and silently takes the balance, `held` and the float with it. Public
  or private — the realistic edit is a helper, not a method somebody names `forget`. Carries
  a negative control per shape it refuses. _Avoid_: relying on the public-surface pin alone,
  which catches a new method's **name** and not a write inside one that already exists.
- **Pseudonymising a ledger** (`Ledger.pseudonymise`) — erasure as a **read-time
  substitution**: an event is appended and every movement the aggregate hands out names an
  opaque id in the player's place, with nothing about the amounts, causes or references
  changed. The stored events are untouched, because rewriting them is the one thing an
  append-only store cannot do — and ADR-0055 forbids it in the sentence that asks for the
  pseudonym. The stream stays findable by player id; what identifies a person lives in
  Users and is erased there. _Avoid_: deleting a movement, and a pseudonym derived from the
  player id, which is a mapping table written as a formula.
- **Ledger invariants** (`money.LEDGER_INVARIANTS`) — the three ADR-0055 names, as
  functions the nightly job and the test suite both call: `no_club_is_a_payer`,
  `no_balance_above_zero`, `every_seat_chain_closes`. The third is *no seat settles more to
  a club than the player funded for it* — ADR-0056's *broken split*. **They report; they
  never repair**, and `ReconcileLedgers` is built with **no unit of work**, so that is a
  property of its constructor. _Avoid_: a second copy of an invariant, and a job that fixes
  what it finds — the evidence of the bug is what the ledger is for.
- **Seed ledger** — a seeded ledger is named for the state it represents and the name is a
  checked claim: the movement count, `held` on its seat and the player's balance, all
  **folds**, checked against the stored ledger on every run including one that creates
  nothing. The reference is the idempotency probe. The whole seeded set is then asserted
  against the three invariants. _Avoid_: seeding a movement for a paid seat — that join is
  `Raketa02/Raketa#70`, and the runner does not drive it yet: the catalog would have to
  name what each seeded match's money *is*, which is the demo week's own effort
  (`Raketa02/Raketa#96`).
- **Custody** (`money.Custody`) — who is holding a seat's money the instant it arrives:
  `held` for an open match, `passedThrough` for a private court (ADR-0056). It **follows
  what was sold, never how it was paid**, so it is the match's answer and nothing on a
  command can move it. Cash across a counter is not a third member — it is a *channel*,
  and Raketa is never a party to it. _Avoid_: letting a payer, a provider or a club state
  it; the same 38 zł means two different things and the difference is invisible on the
  screen.
- **Payment channel** (`money.PaymentChannel`) — `Online` or `AcrossTheCounter`: where the
  money came through, which is the **caller's** fact because it is the only one that knows
  it. Put together with the custody above, the two decide which movements a share writes;
  neither answers it alone. `Online` carries the `Raketa → club` settlement's own
  reference, required rather than optional because a caller cannot know in advance whether
  the court was already bought.
- **The seat a share is for** (`money.Seats`, `SeatsThroughMatches`) — Money's one question
  to another context, stated in Money's words: *give this player the seat this money is
  for, and tell me what the money is for*. ADR-0055 fences the dependency one way, so
  `money/infrastructure/` is the only directory in the context that knows a seat is a
  position on a `Match`. It **writes and does not commit**. _Avoid_: reaching for
  `MatchRepository` from a use case — `tests/unit/test_money_events.py` walks Money's
  domain and application layers for exactly that.
- **The two transactions of a seat payment** (`money.PayForASeat`) — the seat, the
  reservation (or the inventory loss) and both outbox rows close **together** (ADR-0035);
  the movement is a **second** transaction, because ADR-0055 refuses a movement inside a
  match transaction. Matches runs **first**, because the movement names the reservation
  that write produced. A process dying between them leaves a paid seat with no movement,
  and a replayed report heals it — the port answers *hers* for a seat that is already
  paid. _Avoid_: the other order, which records money against a seat she never got; and
  one commit, which is a match rolled back because a bank was slow.

- **The ranked funnel** (`now.ComposeShelves`) — retrieve → eligibility → score → floor →
  order → diversity → cap, for **both** ranked shelves, because what separates them is one
  eligibility rule, one floor and one cap. Shelf 1 and shelf 2 may never be merged into one
  ordered list: a full match **outranks the joinable version of itself** (viability is the
  one term that can never be excluded), so a single list would be topped by matches nobody
  can join. _Avoid_: a second pipeline for the second shelf; a lane is data, not a branch.
- **Exclusion** (`now.Exclusion`, `now.exclusions`) — the set of eligibility rules a
  candidate **failed**, answered instead of a boolean, which is what makes *evaluate all,
  never short-circuit* a property of the shape rather than a rule somebody remembers. Eight
  common rules plus one seat rule per shelf; `WithinTravelCeiling` is in **neither**, and
  `NotSuppressed` is a v2 slot that runs and passes rather than one waiting to be added.
  A diagnosis vocabulary that crosses **no wire** — *"seven of them already full"* is an
  operational sentence, not a player's. _Avoid_: `a and b and c`, which throws away the
  difference between *seven were full* and *seven were too far*.
- **`FEED_ORDER`** (`now.feed_key`) — `[desc(fit), asc(start), asc(dist), asc(id)]`, the
  **total** base order, with every later pass expressed as a named delta over it. The
  fourth comparator is load-bearing and not decoration: without a guaranteed-total final
  key the order falls back on retrieval order, which is the query plan, and two identical
  requests reshuffle the shelf under the player's thumb. An unknown distance sorts **last**
  — a club the platform cannot place is not thereby the nearest one.
- **Diversity defers, never drops** (`now.diversify`) — at most two cards from one club in
  one hour sit together, and the third goes to the **back of the shelf** rather than out of
  it. The pass is a permutation, asserted as one; the cap is the only thing in the funnel
  that removes a card. _Avoid_: the prototype's `continue`, which returned fewer than the
  cap with cards still waiting.
- **The retitle** (`now.code_for`, `now.floor_for`) — when nothing clears 70, shelf 1 keeps
  its cards, drops its floor and becomes `sameLevel`. That is what *"shelf 1 never goes
  silent"* means, and it is why a floor is affordable at all: an unfillable shelf is
  **absent** rather than empty, so no card claims the city is empty. The **order does not
  change with the title** — closeness to her Level is what `desc(fit)` already leads on,
  and a second order computed from one term of a ten-term score would disagree with the
  badge beside it.
- **Match scoring context** (`now.MatchScoringContext`, `ScoringContexts`) — one match as
  **everybody** looking at it sees it: the record, the club's facts, its saturation and the
  seated players' ratings. Cached under `matchId : recordVersion` and therefore **never
  stale** — a seat payment bumps the version and the next ask files under a key nobody
  wrote. No TTL, no reverse index, no `forget`. What is *not* in it is everything the
  viewer supplies. It lives **behind `CityMatches`** and not in front of it, which is the
  opposite of where ADR-0068 puts the new-arrivals cache — and that ADR's own line is why:
  *"the key is a fact about the viewer and the port's question is not"* holds there and
  inverts here. Above the port it would assemble every context and then throw it away for
  the copy already held. _Avoid_: putting the distance or her own rating on it; a
  viewer-relative field on a shared value is one player's answer with everybody else's name
  on it.
- **The travel sentinel** (`now.TRAVEL_UNMEASURED`) — `ClubSnapshot.travel_minutes` is
  required with no default and the platform holds no player location (`#102`, ADR-0063).
  Travel is a **constraint** term, so an undeclared radius is *no limit* and the term
  scores full marks whatever the minutes are; no player can declare a radius (`#105`), so
  the sentinel provably moves no score and no order, which is asserted as a property rather
  than argued. **It may rank and it may never be printed**: a travel *reason* is withheld
  from the badge, because *"20 minutes away"* drawn from a sentinel is a claim about a
  journey nobody measured. _Avoid_: zero, which is the one value that would flatter.
- **Crowding is computed** (`CityMatchesFromMatches`) — the club's live courts against the
  reservations touching the match's window, keyed per club **and hour** because a club is
  not crowded, it is crowded on a Tuesday evening. Unlike travel it is **evidence** and
  multiplies straight into the score, so a default of nothing is an empty club — the most
  flattering answer available.
- **The phase is stated and the guard moves** (`now.snapshot_for`) — `MatchSnapshot`
  refuses anything but `FORMING` and `MATCH_PHASE_OF` maps a **full** match to `LOCKED`, so
  deriving the phase would make shelf 2 unbuildable. The projection asks *is this roster
  fixed*; the guard asks *is this a candidate*. The assembler states `FORMING` and
  **reinstates the guard it gave up**, refusing a terminal or already-started match through
  `invariant` — so the loud failure the field exists for still happens, one layer up, where
  eligibility has already made it unreachable.
- **`Unscorable`, and degrade** (`now.MatchScorer`) — any engine failure becomes one
  exception, caught **once per screen**: a shelf ordered from a pass that half ran is a
  shelf whose order means nothing. Shelf 1 falls back to soonest-first with no badge under
  the `sameLevel` code — the thin-week fallback, so the degraded screen is one players have
  seen — and shelf 2 is **dropped**, because an 80 floor with no scorer is not a claim we
  can make. **No marker crosses the wire.**
- **The engines are given the minute** (`now.MatchScorer`) — both refuse a `now` carrying
  seconds, and a composed screen's clock is `SystemClock`. Left alone every live compose
  raised, every raise was an `Unscorable`, and **every screen degraded** with nothing on the
  wire saying so — invisible to a unit suite whose fixtures are all minute-aligned. The
  kernel keeps the true instant; only the two engine calls get the truncation.
- **A reason is quantities** (`now.FitReason`, `FitReasonPayload`) — a term code and its
  **typed fact payload**, in the units the kernel keeps them in, and never a weight, a
  value, a contribution or a sentence. The fact is the engine's own object, passed by
  identity, so a card cannot show a reason computed from anything but the badge beside it.
  `FitSide` is derived from the two Levels rather than carried, and crosses because
  choosing a sentence from the sign of a subtraction is a rule the phone does not hold.
- **The aim crosses only when precise** (`now.Fit.target`) — the pairing engine's *seat
  target*, which exists only while exactly one seat is open. A target **band** is nearly
  always the viewer's own band restated, so printing it would be the card telling her what
  she already knows in the voice of a measurement.

Add backend-specific technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.
