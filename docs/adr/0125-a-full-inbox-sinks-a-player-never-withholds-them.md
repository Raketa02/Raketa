# ADR-0125 — A full inbox sinks a player; it never withholds them

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §14.4 protects the popular
player from a death spiral — unanswered challenges pile up, their answer rate falls, and the
matcher punishes them for having been in demand. It is throttling *before* the symptom rather
than a penalty after it, and the concern is real.

It states three rungs:

```
open_challenges ≥ 3   →  liveness −4
open_challenges ≥ 5   →  liveness −8
open_challenges ≥ 8   →  withheld from generation for 24 h
```

**The first two are adopted.** [`ranking-weights.md`](../specs/matchmaking/ranking-weights.md) §9
carries *current challenge load* at `−8 … 0`, printable as a coarse code and **never as the
number**, because somebody's inbox depth is theirs.

**The third was never ruled on.** An exclusion from generation is a **gate**, and it appears in
no gate roster, no constant table and no ticket on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
[`the-newcomer-path.md`](../specs/matchmaking/the-newcomer-path.md) §4 cites it as still standing
— *"§14.4's withholding is a remedy for a **measured** full inbox"* — while arguing in the same
paragraph that `NEWCOMER_ABSORPTION_CAP` may **never** withhold, because withholding makes a thin
pool thinner for the person who can least afford it
([ADR-0114](0114-a-newcomer-may-not-be-declined.md)). Both cannot be unexamined.
[#189](https://github.com/Raketa02/Raketa/issues/189) settles it.

### The distinction the citation was carrying

ADR-0114 refused withholding on *suspicion of load* and let §14.4 keep it on *measurement*. That
is a real distinction and it is about the wrong party. **The measurement is of the candidate's
inbox; the cost is paid by everyone searching.** A gate inherits *no relaxation rung reaches a
gate, at any rung, ever* — so the searcher who is offered nothing tonight has no way back to the
person the engine withheld, and is never told they existed. In a market this map already measured
as thin ([#162](https://github.com/Raketa02/Raketa/issues/162),
[#166](https://github.com/Raketa02/Raketa/issues/166)), withholding the pool's most-asked player
for 24 h can empty a search that had exactly one good answer.

### What the sink already does, and where it stops

Liveness reorders and never enters Fit: `rank_key = fit + liveness_offset`, and the shortlist is
capped. A player at the bottom of the ordering in a healthy pool sits below twenty better
candidates and is **effectively invisible** — the cap does the excluding, at no cost in
vocabulary, reason codes or relaxation exceptions. In a thin pool the same player still appears,
which is exactly right: **when there is nobody else, showing the busy person beats showing
nobody.** Withholding cliffs where sinking degrades.

## Decision

**§14.4's third rung is deleted as an exclusion and adopted as the deepest step of the sink.**

```
open_challenges ≥ 3   →  −4
open_challenges ≥ 5   →  −8
open_challenges ≥ 8   →  −12
```

`Current challenge load` moves from `−8 … 0` to **`−12 … 0`**. §14.4's own three thresholds are
adopted whole; only the third's *effect* changes. The **24 h** duration is deleted rather than
rehomed — it was the duration of an exclusion, and there is no longer one; the sink lifts when
the inbox empties, which is the behaviour the rule wanted and a fixed window only approximates.

**`−12` is anchored, not chosen.**

- **Strictly below the `+14` interest lift.** A player who said *Let's play* to you still surfaces
  at `+2` net however full their inbox is. That carve-out is
  [ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md)'s and it is now load-bearing for a
  second reason: **a human's own ask outranks the engine's opinion of that human's popularity.**
  At `−16` the lift would be cancelled and the engine would quietly overrule a person who had
  already been asked.
- **Equal to reciprocal asymmetry's `−12`**, the other *this candidate is a bad bet for you*
  signal, and inside the `[−25, +25]` envelope.

**It stays printable as a coarse code and never as a number** (ADR-0106), and it stays out of the
silent set, so [ADR-0123](0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)'s
budget and its roster test are untouched.

**Falsified by: answer rate by open-challenge bucket.** If answer rate does not fall as load
rises, the signal is measuring nothing and all three rungs are noise. The constant's owner is
`RobertConstantin02`, on [#167](https://github.com/Raketa02/Raketa/issues/167)'s discipline.

**The telling is unchanged and owes the engine nothing.** §14.4 promises the player is told and
the searcher is not. The searcher half is already kept by the coarse code. The player half is
`count(open challenges)` — a fact the `matches` context owns and the player is entitled to, shown
by the app when they next open it. The engine never emits a string a human reads (ADR-0022), and
nothing in this repository can push anything, so it is a client surface and not a deferral.

## Consequences

- **The roster stays at ten.** The eleventh exclusion the input document contained is not a gate,
  and `the-engine.md` §3 says so where a reader would otherwise go looking for it.

- **ADR-0114's argument is generalised rather than contradicted.** It refused withholding for a
  newcomer-driven cap and preserved §14.4's as the measured exception. The exception is now gone
  and the rule is one rule: **the engine bounds how hard it pushes somebody, and never removes
  them from the pool.** The remaining ways out of a search are the ten gates, all of which are
  about whether a game is *possible* or *safe* — never about whether somebody is *busy*.

- **A busy player is now recoverable by relaxation, and was not.** They are ranked, so a rung
  that lifts scores against the floor can reach them. That is the whole difference between a
  term and a gate, and this is the second time on this map that a rung was found relaxing
  something that had never been excluding anybody
  ([#166](https://github.com/Raketa02/Raketa/issues/166)).

- **The load signal now carries the job alone, and one bound moved to pay for it.** Deleting a
  cliff is not free: `−8` was calibrated beside an exclusion that caught the tail. `−12` is the
  compensation, and its falsifier is the check that it was needed.

- **Nothing turns on it today.** `open_challenges` comes from `MatchHistoryQuery`, and `matches`
  does not exist — which is precisely why it was decided here rather than by whoever wires that
  context and meets §14.4 as written.

- **Both of this ticket's rows failed the same way.** A table titled *every gate* and a table
  titled *every constant* are where a rule with no owner goes unnoticed — the third and fourth
  instance on this map, after [#184](https://github.com/Raketa02/Raketa/issues/184) and
  [#190](https://github.com/Raketa02/Raketa/issues/190).
