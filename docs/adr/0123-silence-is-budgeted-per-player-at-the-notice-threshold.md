# ADR-0123 — Silence is budgeted per player, and the budget is the notice threshold

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §9.5 makes Liveness a
promise as well as a mechanism: it reorders, it never enters Fit, and **anything moved more than
`MOVE_NOTICE = 6` points must print its dominant liveness reason.** §9.5.1 then makes one signal
unprintable in the strongest terms available — a previous decline is *"never, under any
circumstance, shown to either side"* — and [#175](https://github.com/Raketa02/Raketa/issues/175)
made a second one unprintable on a different argument: a third party's unpopularity is not the
searcher's business, so the **exposure adjustment** stays silent while the newcomer lift speaks.

[`ranking-weights.md`](../specs/matchmaking/ranking-weights.md) §9 reconciled the promise with
the two silent signals by writing an invariant, and declaring it enforced by the type system:

> **A silent movement never exceeds the movement that owes an explanation:
> `|silent movement| < MOVE_NOTICE`.**

The reconciliation is right and it is kept. **Its arithmetic was wrong in two independent ways,
and the second was the dangerous one.** Resolving
[#188](https://github.com/Raketa02/Raketa/issues/188) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
settles both, and settles what the type system is actually being asked to do.

### The inequality was stricter than the promise it enforces

§9 sets previous decline at **−6** and the exposure adjustment at **−6 … +6**, both never
printable. `|−6| < 6` is false, so the invariant was **red against the constants shipping beside
it on day one**. But §9.5's own threshold is *more than* 6 — movement of exactly 6 owes no
explanation, by the product's own rule — so the strict `<` demanded a margin the promise never
asked for. Taking `<` literally would have meant moving both signals to `±5`, weakening two
bounds #175 had just argued to, for a transcription slip rather than an argument about the
signals.

### The bound was on a signal where the promise is about a player

A player is moved by the **sum**. Previous decline and a negative exposure adjustment can both
fire on the same candidate: **twelve points of movement with nothing to print** — double the
threshold the invariant exists to respect, and exactly the outcome §9.5 forbids. A per-signal
bound cannot deliver a guarantee about a total, and no amount of tidying the inequality reaches
this half.

### The two ways out that are already closed

**Promoting the dominant silent reason to printable** is closed from both ends — §9.5.1 forbids
it for a previous decline, #175 forbids it for exposure. **Taking the exposure adjustment out of
Liveness** would leave one silent signal, where per-signal and per-player coincide; it reopens
#175 to fix an arithmetic problem, and it relocates the adjustment somewhere with no bound at
all rather than bounding it.

### The shape the pipeline already uses, one stage earlier

[`the-engine.md`](../specs/matchmaking/the-engine.md) §6: **`MODIFIER_BUDGET = ±10`, a clamp on
the summed stack and not a per-modifier bound.** Stage 4 already met the case where several small
adjustments pile onto one candidate, and already decided to budget the pile rather than the item.
Stage 6 wrote the per-item version of the same problem and called it a type.

## Decision

**We will bound the silent stack per player, at `MOVE_NOTICE`, by clamping it.**

```
liveness_offset = Σ printable  +  clamp(Σ silent, −MOVE_NOTICE, +MOVE_NOTICE)
```

**The inequality is `≤`, and no signal moves.** Previous decline stays **−6**, the exposure
adjustment stays **−6 … +6**. The invariant now reads:

> **A silent movement never exceeds the movement that owes an explanation:
> `|Σ silent| ≤ MOVE_NOTICE` — per player, not per signal.**

**The bound is on the signed net, not the summed magnitude.** A previous decline at −6 beside an
exposure adjustment at +6 nets to zero: the candidate sits precisely where their printed score
puts them, and there is nothing to explain. The only thing a searcher can observe is **position**,
and position is the net.

**The notice rule stops being a rule and becomes a consequence.** If `|Σ silent| ≤ MOVE_NOTICE`
and `|liveness_offset| > MOVE_NOTICE`, then `|Σ printable| ≥ |liveness_offset| − |Σ silent| > 0` —
**a printable signal necessarily exists**. §9.5's promise is satisfied by arithmetic rather than
by policing. So §9.5's single sentence becomes two clauses:

- **Notice.** `|liveness_offset| > MOVE_NOTICE` ⟹ at least one liveness reason is emitted.
- **Ranking.** *Dominant* means the largest **printable** contributor. Liveness reasons join the
  ranked list [`the-engine.md`](../specs/matchmaking/the-engine.md) §5.4 already emits — *the
  engine ranks the reasons by contribution; the client picks how many to show*. Silent signals
  are absent from that ranking and are **not** a client-renderable gap: §5.3's *an unknown `kind`
  is a named gap, never silence* is about version skew, not about deliberate silence.

**The budget is `MOVE_NOTICE` itself, not a second constant.** The proof above holds only while
`budget ≤ notice threshold`, and two constants can drift apart in a ruleset edit and break the
guarantee **silently** — the one failure mode this record exists to close. One constant also
couples correctly in both directions: lowering `MOVE_NOTICE` says less movement may go
unexplained and should tighten the silent budget; raising it should loosen it. `ranking-weights.md`
§13 gains **no row**.

**We will split what "enforced by the type system" claims, because half of it was decoration.**
`|Σ silent| ≤ MOVE_NOTICE` is a fact about a runtime sum and no type can check it. §12.2's
neighbouring rule — `Fit` has no `Add(Liveness)` — is genuinely type-enforced, and this one had
been borrowing its credibility.

- **The type enforces the separation and the funnel.** A liveness signal is a closed union of
  `Printable(code, points)` and `Silent(points)`. `Liveness` has one constructor, it takes the
  two lists, and it applies the clamp — so there is no path to an offset that skipped it.
- **Tests enforce the arithmetic**, and they fail the build:
  1. a property test over every signal at every bound, asserting the applied silent net stays
     within budget;
  2. a property test asserting `|offset| > MOVE_NOTICE ⟹ reasons ≠ ∅`;
  3. a **roster test** pinning the silent set to exactly `{previous_decline, exposure_adjustment}`
     and pinning its reachable net range.

Today previous decline ranges `[−6, 0]` and exposure `[−6, +6]`, so the silent net lives in
**`[−12, +6]`** and the budget's **upper clamp is unreachable** — in practice the clamp only ever
cuts a *bury*, which is the direction the invariant exists to protect. That is a property of
today's roster, not of the rule, and test 3 is what makes the day a positive silent signal is
added break loudly instead of quietly.

**The falsifier is a query, not a column.** [#183](https://github.com/Raketa02/Raketa/issues/183)
already records the **raw signal values** in `search_candidate.liveness_signals` and deliberately
leaves the offset out as re-derivable ([ADR-0118](0118-a-past-search-is-not-reproducible.md) §8).
Whether the clamp bound is a function of stored inputs and the ruleset version, so it is derived
from the SQL search tables [#169](https://github.com/Raketa02/Raketa/issues/169) settled. It
does **not** join the six signals the map has nowhere to read.

The budget is falsified two ways: if the clamp **never binds**, the per-player rule was
theoretical and a per-signal bound would have done; if it binds **often**, previous decline and a
negative exposure adjustment are routinely stacking and one of the two is miscalibrated rather
than the budget being wrong.

## Consequences

- **§9.5's promise becomes provable.** *Anything moved more than `MOVE_NOTICE` prints its
  dominant reason* was an intention that the shipping constants contradicted. It is now a
  theorem over the clamp, with a test that runs.

- **Both silent signals keep the strength #175 argued them to**, and the budget binds only in the
  case #175 never considered: both firing hard on one candidate. When it binds, what gets cut is
  **silence**, not the signals — which is the trade the invariant is for.

- **A candidate can still be buried by six points with nothing printed, and that is deliberate.**
  Six is the movement §9.5 already decided owes no explanation. The `≤` is not a rounding
  convenience; it is the statement that this rule enforces the promise rather than exceeding it.

- **A printed liveness reason is true but not complete, and the spec now says so.** The card may
  name a −3 signal on a candidate moved −9. This is not §5.3's *breakdown that quietly stops
  adding up*, because that rule is about **Fit**, which crosses as a number and must reconcile —
  **Liveness crosses as reasons and never as a number** (§12.2, ADR-0106 §5), so there is nothing
  to add up. The unstated remainder is bounded at `MOVE_NOTICE` by construction.

- **`MOVE_NOTICE` now does two jobs, and tuning it moves both.** Its existing falsifier — the
  fraction of shortlist rows printing a liveness reason — is unchanged, but a change to it is now
  also a change to how hard the silent stack is clamped. That coupling is the point rather than a
  side effect, and `ranking-weights.md` §13's row says so.

- **A third silent signal is now a decision rather than an addition.** Any signal joining the
  silent set enters a fixed budget it must share, and the roster test refuses it until somebody
  re-argues the budget. This is the same protection the map twice found missing when a table
  titled *every constant* quietly gained or lost a row
  ([#184](https://github.com/Raketa02/Raketa/issues/184),
  [#190](https://github.com/Raketa02/Raketa/issues/190)).

- **One inconsistency is surfaced and left alone.** `ranking-weights.md` §12's **Modifiers** row
  records *whether the stack clamp bound* directly, while its **Liveness** row deliberately stores
  inputs and re-derives. #183's argument would collapse those to the same treatment. It is noted
  rather than fixed here, because it is a telemetry question and not this one.

- **The rule generalises, and that is why it is a record.** *A bound on a signal is not a
  guarantee about a player* is [ADR-0117](0117-a-group-term-reads-only-what-fit-did-not.md) and
  [ADR-0120](0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md) in a third key: those two ask
  what a term is allowed to **read**, this asks what a promise is made **about**. The next
  invariant written about a component when the promise is about a person gets tested against it.
