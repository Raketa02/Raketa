# ADR-0026 — Two matchmaking engines, one snapshot input contract

- **Status:** Accepted
- **Date:** 2026-08-17

## Context

Two engines are being built together, and they are not the same question.
**Pairing** asks whether a match is *balanced* — who plays with whom, and how close the result
should be. **Match Fit** asks whether a match is *for you* — level, balance, company, distance,
price, timing, whether it counts. A perfectly balanced match forty minutes away at twice your
price ceiling scores well on the first and badly on the second, and both answers are correct.

Three forces shape how they fit together.

**Match Fit already has more than one consumer.** The player app's home list ranks by it; the
overlap-awareness rules use it both to filter alternatives during match creation and to rank
them. This is the multi-consumer case [ADR-0015](0015-engines-as-a-pure-versioned-layer.md)
predicted, and it is the reason engines are a pure layer rather than logic inside one module.

**Match Fit consumes Pairing's output.** Its balance term is the forecast; its skill-overlap
term is the seat target or the target band. So the two engines are already composed, and *how*
they compose is a decision rather than a detail.

**The context that owns the data does not exist.** Matches, Clubs, Courts and Bookings are named
in the glossary and modelled nowhere. Meanwhile the facts the engines need are spread across
places that do exist or are separately specified: ratings from the rating context, prices from
`kernel/money.py`, sport arity from `kernel/sports.py`, a seat's paid/held/empty state and a
match's phase and join cutoff from the clock and commitment rules, the player's declared days,
hours, ceiling and distance from the intent-pool profile.

An engine may not read any of it. It cannot import a module, touch a database, read
configuration or call a clock; `now` is an explicit input. So *something* has to name the facts
an engine is given, and that something is a deliverable in its own right.

The alternatives considered:

- **Engines take the aggregates.** Impossible under the import fence, and impossible today in
  any case, because the aggregates do not exist. It would also couple the arithmetic to
  SQLAlchemy and make the cheapest tests in the codebase require fixtures.
- **One merged matchmaking engine.** Fewer moving parts, and it removes the composition
  question by fiat. But balance and fit retune on different evidence and at different rates — a
  weaker-partner coefficient is falsified by set margins, a term weight by join rates — and one
  version number over both means every retune of either invalidates the attribution of both.
- **Match Fit imports and calls the pairing engine.** Natural-looking, and wrong in a specific
  way: the caller already needs the forecast to draw the card, so Fit would either recompute it
  or receive it anyway — and a Fit engine free to construct its own forecast can score against a
  different pairing than the one displayed beside the score. That is *two implementations of one
  question* smuggled back in one layer up.
- **Two engines, composed by the caller, over one shared input vocabulary.**

## Decision

We will build **two engines with two Protocols and two version lineages**, over **one shared
snapshot input contract**, composed by the calling module.

```
app/engines/
  matchmaking.py     # shared INPUT vocabulary, assembled by modules, read by both engines
  forecast.py        # Protocol BalanceForecastEngine + its output vocabulary
  fit.py             # Protocol MatchFitEngine + its output vocabulary
  pairing/core.py    # what outlives a version: team strength, σ-propagation, the three splits
  pairing/v1/        # constants + engine
  matchfit/core.py   # what outlives a version: term kinds, renormalisation, reason ranking
  matchfit/v1/       # constants + engine
```

- **Snapshots, not aggregates.** `matchmaking.py` declares frozen value objects —
  `MatchSnapshot`, `SeatSnapshot`, `PlayerSkill`, `ClubSnapshot`, `PlayerProfile`, and the
  two that ship dark, `PlayerScore` and `PlayHistory`. A module assembles them; an engine reads
  them and nothing else.
- **The snapshot borrows vocabulary verbatim.** A seat's paid/held/empty state, a match's phase,
  its hold tier and its join cutoff are the clock's words, and the snapshot spells them the same
  way. Renaming them here would fork the clock, which is a worse version of inventing a second
  price ceiling.
- **Pairing returns one object.** `PairingAnalysis` carries the forecast, the seat target, the
  target band and the ranked splits together, because a caller that needs one of them almost
  always needs the others and the four must agree with each other.
- **Match Fit takes `PairingAnalysis` as an input field, never as a collaborator.** The caller
  runs Pairing, then runs Fit with the result. `fit.py` may import `forecast.py`'s *output
  types* — that is vocabulary. Neither version package may import the other, and
  `.importlinter` gains a contract forbidding `pairing/` ↔ `matchfit/` so this survives a
  reviewer's memory.
- **Both versions travel on the output.** A Match Fit score has two producers and carries both
  identifiers, so a constant belonging to either can be attributed and therefore falsified.
- **`now` is an explicit `Instant`, rounded to the minute.** The kernel already computes in
  integer minute coordinates ([ADR-0024](0024-instant-as-aware-datetime-minute-coordinates.md)),
  so minute granularity costs nothing, makes every score reproducible from its stored inputs,
  and makes a result cacheable for a minute instead of never.
- **The engines ship before Matches exists**, tested entirely against hand-built snapshots. This
  is the `kernel/money.py` precedent: the rounding order and the seat split were built correct
  and finished ahead of the first club, and that is precisely why they could be built at all.

## Consequences

**Easier**

- The snapshot becomes the specification for the Matches aggregate. When Matches is modelled it
  must own exactly the facts the snapshot names and no more, which is a far better input to that
  ADR than guessing an aggregate shape and discovering the gaps afterwards.
- Both engines are testable with no database, no fixtures and no HTTP, from the first commit and
  before their data source exists.
- A retune of one engine leaves the other's attribution intact, because the version lineages are
  independent.
- `kernel/money.py` acquires its first production caller, having been written for one.

**Harder**

- **The snapshot can drift from the aggregate it mirrors.** Two representations of a match now
  exist, and nothing mechanical keeps the assembler honest — a field that stops being populated
  correctly is a silent scoring bug, not a type error. The mapping needs its own tests and they
  are not the cheap kind.
- **Call sites are wordier.** Assembling a `MatchSnapshot` means gathering ratings, prices,
  profile and clock facts across contexts before either engine can be called at all, where a
  direct lookup would have been one line.
- **Two engines is more ceremony than one** for a reader who sees them always called together,
  and the reason they are separate is a claim about future retuning cadence — which is exactly
  the kind of claim that can turn out to be wrong.
- Composition is the caller's job, so a caller can get it wrong: running Fit with a stale or
  absent `PairingAnalysis` is possible and produces a quietly worse score rather than an error.

**Neutral**

- Nothing changes for the assessment engine or the rating context; this is the second and third
  member of a layer whose shape was already decided.
- Which of Fit's terms are computable at launch is a separate matter
  ([ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md)); the input contract
  carries the dark fields as absent from day one so lighting them up is a constant change and
  not a signature change.
