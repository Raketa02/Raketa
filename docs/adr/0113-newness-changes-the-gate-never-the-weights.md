# ADR-0113 — Newness changes the gate, never the weights

- **Status:** Accepted
- **Date:** 2026-08-26

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** The ranking is gone (#580), so there are no weight vectors and no quality floor for newness to leave alone: decisions 1 and 5, and the Consequences' empty screens, radius rungs, calibration modifier and judged pairings, describe nothing that runs, and decision 4 is moot. Decisions 2 and 3 are the rule today: while either player in a pair is inside their fourteen-day newcomer window, the pair is held to the competitive tolerance whatever the kind of game (`matchmaking/domain/level_window.py`) — for every pair the proposer, the fill and a rescue would seat, and for a post's level range.

## Context

§9.10 of `matchmaking-engine.md` — *The newcomer
path* — opens with **a distinct ruleset**:

> level 30 · balance 22 · reliability 20 · intent 14 · availability 8 · style 4 · vibe 2 ·
> distance 0

selected when `counted_games == 0 ∧ rating_status == INITIAL_ESTIMATE`. Its argument is sound and
this ADR does not dispute it: a first game is the most consequential game a player will play, the
return-rate figure applies most brutally to it, and evenness and reliability are what protect it.

Resolving [#175](https://github.com/Rakieta02/Rakieta/issues/175) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Rakieta02/Rakieta/issues/155)
found the vector unaffordable for a reason that has nothing to do with its numbers.

**A third weight vector re-opens the quality floor.**
`the-five-numbers.md` sets **one** `QUALITY_FLOOR` for
both modes and every sport, on an explicit argument — *"each extra dimension is a place to lower
it quietly for whichever pool is thin"* — and refuses to define it as an integer at all. It is
defined by **six judged pairings** and the constraint

```
Fit(case 3)  <  QUALITY_FLOOR  ≤  min( Fit(1), Fit(2), Fit(4), Fit(5), Fit(6) )
```

which `ranking-weights.md` then read as **44**, against
the two existing vectors. A third vector re-derives every Fit value in that table. Either the
floor moves for newcomers — the precise thing the map refused — or the vector owes the same six
judged pairings, in a mode where the judgements were never made.

A second finding removed the assumption that made the vector look free. **Nothing about a
newcomer's own newness stands a single Fit term down.** All eight terms are pairwise, and the ones
that go quiet are about the *candidate*; a newcomer searching has level, balance, intent,
availability, style, vibe and distance all firing normally. So §9.10's re-weighting is not what
§10's renormalisation would have produced anyway — it is a genuine, chargeable product choice.

A third: **§9.10's selection predicate cannot be evaluated.** `counted_games` exists nowhere in
the backend, and every rating the questionnaire produces is stamped `"Initial Estimate"`
(`backend/app/engines/racketskill/v3/engine.py:309`) with no transition that can change it. As
written the predicate is true for every player who will ever exist.

## Decision

**Newness changes the gate, never the weights.**

1. **§9.10's newcomer weight vector is struck.** There are two weight vectors in this system —
   competitive and for-fun — and there is one quality floor over both.

2. **While *either side* of a pairing is inside their newcomer window, the level gate of
   [ADR-0103](0103-where-the-curve-saturates-the-gate-begins.md) is evaluated at
   `LEVEL_TOL_COMP`, in both modes.**

3. **It binds the pairing, not the search.** Not the searcher's newness, not the candidate's —
   either.

4. **§9.10's *"never the most competitive player in the pool"* is refused**, not deferred.

5. **§9.10's distance-weight-to-zero is struck as redundant.**

The window itself, and everything else this ticket settled, is in
`the-newcomer-path.md`.

## Consequences

**No constant is introduced, so nothing is owed.** `LEVEL_TOL_COMP = 0.55` and
`LEVEL_TOL_FUN = 0.90` both already exist and both already carry falsifiers in §24's shape. The
rule is expressible in one sentence with no new number in it: *a first game is judged on the
stricter of the two bars the product already has.* A scaling factor would have been a third
constant needing a §24 row, a falsifier, and a place in the six pairings — for a bar the product
already draws.

**Binding the pairing rather than the search is the load-bearing half.** Gating only the
newcomer's own search leaves the bad first game arriving through the veteran's list — a game the
newcomer never searched for, cannot see coming, and under
[ADR-0114](0114-a-newcomer-may-not-be-declined.md) cannot decline. This is the third time this map
has reached the same shape: [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s
block and [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s preference
are both facts about a **pair**, and both bind whoever is in it. A rule about a pairing that binds
only one side is a rule with a door in it.

**It is a real exclusion in for-fun, and it is the point.** For 14 days a newcomer will not be
shown a for-fun opponent between Δμ 0.55 and 0.90 who would otherwise have been admitted. At
launch density ([#161](https://github.com/Rakieta02/Rakieta/issues/161): 63% of searches already
return fewer than five candidates) that will occasionally be why a screen is emptier. It is the
same trade ADR-0099 took deliberately — **a bad
match is worse than no match** — and the empty-result rate stays a guardrail metric, never
sufficient grounds to move it.

**The distance rule was already true.** §9.10's *a first game is worth a longer journey* is
correct, and ADR-0099's radius rungs already deliver it — **if the searcher asks**. Zeroing the
weight would have delivered it whether they asked or not, which is the widening-on-somebody's-
behalf that ADR-0099 exists to forbid. Nothing is lost and the map's standing rule is kept.

**Refusing the percentile cap costs something, and the something is named.** §9.10's case is a
3.40 with fifty counted games against a 3.35 with none: Δμ = 0.05, so **no level gate at any
tolerance catches it**. The concern is about *experience*, and the engine holds no unit for
experience. Four reasons decide it anyway:

- It is a **percentile over the pool**, so the identical pairing is admissible in a large city and
  refused in a small one — the shape ADR-0101
  struck for the partition, and unexplainable in one sentence naming evidence, which is the third
  refusal.
- Its input does not exist.
- ADR-0103's gate does not reach it.
- **It refuses the pairing the calibration modifier pays `+4` for.** §9.4 rewards *their band is
  wide and yours is narrow, and the game would be counted*; §9.10 forbids it two sections later.
  One of them is wrong, and a rule that contradicts a rule in the same document cannot be adopted
  by transcription.

If the concern survives, it returns in Δμ and σ — the units the engine has — and lands as a gate
under ADR-0103, where it must reconcile with calibration value rather than sit two sections away
from it.

**The falsifier:** return rate of first games at Δμ between `LEVEL_TOL_COMP` and `LEVEL_TOL_FUN`,
compared against the same band for non-newcomers. If newcomers convert as well there as anybody,
the tightening is unearned and this ADR is wrong. The measurement needs the outcome half of the
telemetry chain, which needs `matches`, which is out of scope — so it ships as an argued judgement
with its falsifier attached, like the other five numbers. Search-side it costs no column: whether
each side was inside their window is reconstructible from `profile_created_at` and the search
timestamp.

**What would reverse it.** A judged pairing set for a third vector, made in the same way the six
were, showing that a newcomer's list is materially better under weights than under a gate. That is
the rebuttal the map's Notes already permit — *materially better matchmaking or more value for the
player*, argued — and it would amend this record rather than bend it.
