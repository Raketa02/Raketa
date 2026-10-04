# ADR-0120 — A factor reads the pair, or it is not a factor: availability overlap is the glossary's ratio and nothing else

- **Status:** Accepted
- **Date:** 2026-08-26
- **Amended 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**: the cells the overlap reads become hours per weekday; the term still reads the pair and nothing else. The judged pairings and the ruleset diff are regenerated with the change.

## Context

[`ranking-weights.md`](../specs/matchmaking/ranking-weights.md) settled level, balance, the tag
terms, reliability, the modifiers, familiarity, liveness and the quality floor. **Availability
overlap appears there only as a weight** — 11 competitive / 16 for fun, which on the day-one
renormalised basis is **17.6 of 100 and the second-heaviest for-fun term.** Its formula was
never ruled on, and it appears in **neither** constant table: not §13's, and not the design
document's own §24. It is the largest untested thing in the engine.

The design document's [§9.3.5](../specs/matchmaking/matchmaking-engine.md) proposes three
factors and a multiplier over the glossary's definition:

```
overlap      = |shared| / |mine|                        # the glossary's term, unchanged
significance = |shared| / min(|mine|, |theirs|)
proximity    = exp(−days_to_next_shared / PROX_TAU)      PROX_TAU = 5 d
staleness    = clamp(1 − (grid_age_days − 60)/240, 0.6, 1)

availability = (0.55·overlap + 0.25·significance + 0.20·proximity) · staleness
```

Resolving [#184](https://github.com/Raketa02/Raketa/issues/184) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
ran the formula rather than reading it. **Each of the three additions fails, and each fails for
a different reason — but all three fail the same test.**

### `significance` is `overlap` for most of the market, and inverts the glossary for the rest

`min(|mine|, |theirs|) = |mine|` whenever the candidate has at least as many slots as the
searcher, and there the two factors are **identically equal**. For that majority
`0.55·overlap + 0.25·significance` is simply `0.80·overlap`, and the second factor contributes
nothing at all.

It fires only when the candidate is *pickier* than the searcher — and there it ranks **less
coverage above more**. At `|mine| = 14`, a candidate sharing their single slot scores **0.423**;
a candidate sharing three of yours scores **0.359**. Covering 7% of your week beats covering
21% of it, on the term whose stated question is *"how much of my week does this person cover"*.

What the factor claims to read — *this person has flagged two slots all week, so they mean it* —
is a claim about **intent**, which has a term of its own at 14/14.

### `staleness` reads account age, not the pairing

`grid_age_days` runs from `player_profile.availability_changed`. Most players never emit one, so
for them it is time since profile creation. The clamp binds at **day 156**
(`1 − (156−60)/240 = 0.6`), so within six months of launch the majority of the market is docked
identically — and a grid untouched for a year scores exactly what one untouched for five months
does. **The published 240 is never reached**; the real curve is *free for 60 days, linear to 0.6
by day 156*.

That is **oldness changing the weights**, which is
[ADR-0113](0113-newness-changes-the-gate-never-the-weights.md) held up to a mirror. §9.3.5 also
never says **whose** grid it reads; [`the-group-objective.md`](../specs/matchmaking/the-group-objective.md)
§2.3 says *"min over the four"*, but the pairwise case is simply silent. And there is already a
mechanism for a stale grid: the inline *"Keep these times?"* offer, in
[ADR-0094](0094-play-intent-declared-per-sport-in-its-own-aggregate.md)'s shape, firing on
`grid_updated_at`. Docking punishes a player for a thing the same screen is simultaneously
offering to repair.

### `proximity` reads which weekday you searched

The grid is a **recurring week**, so `days_to_next_shared ∈ [0, 7)`. §9.3.5's justification —
*"an overlap tomorrow converts; an overlap in nine days evaporates"* — is written for a horizon
this grid does not have. Nothing is ever nine days away, and every slot recurs forever.

`PROX_TAU = 5` over a six-day domain compresses the factor into **[0.30, 1.00]** and is very
nearly linear across it: the exponential's shape does no work, and the constant is sized for a
calendar rather than for a pattern. Worse, the factor re-scores an **unchanged pair every day**.
The same two people, the same two grids, rank differently on a Sunday than on a Tuesday, by
roughly 2.5 for-fun points against an absolute bar.

It also carries a cost nobody has paid. If proximity scores, then every one of
[`ranking-weights.md`](../specs/matchmaking/ranking-weights.md) §10's six judged pairings needs
a **search weekday** attached to it — a judgement never made. That is the argument ADR-0113 used
to strike §9.10's third weight vector, arriving here unprompted.

### One test the three of them fail

`significance` reads what `overlap` already read. `staleness` reads the searcher's account age.
`proximity` reads the calendar. **None of the three reads the pair**, which is the only thing a
Fit term is for.

## Decision

**We will admit a factor into a term only if it reads the pairing that no other factor read —
and by that test, availability overlap is the glossary's ratio and nothing else.**

```
availability = |shared| / |mine|
```

Five parts:

1. **`significance` is struck from the pairwise term.** Not from the group term:
   `the-group-objective.md` §2.3's `significance₄` is the group's **only** coverage factor —
   among four people there is no *mine* — so it is not degenerate there, and the argument is
   local to the pairwise case.

2. **`staleness` is struck, in both terms.** `group_avail` loses `staleness₄` in the same
   change. `grid_updated_at` stays in the candidate index, because the *"Keep these times?"*
   backstop reads it; nothing in scoring does.

3. **`proximity` is struck from the score and kept as evidence**, which is
   [ADR-0115](0115-a-tag-about-the-person-may-be-shown-never-scored.md)'s shape — *may be
   shown, never scored*. `PROX_TAU` is deleted. `proximity₄` goes with it, leaving
   `group_avail = significance₄`. Proximity keeps the two jobs it is genuinely about: **ordering
   [ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md) rung A's slot suggestions**, and
   the card's own sentence.

4. **The weights are unchanged at 11 / 16**, and `QUALITY_FLOOR` stays at **44**. The two cases
   that bound it are `24.2 < FLOOR ≤ 46.0`; cases 2 and 3′ both read *no shared slot* and are
   **0 under both formulas**, so the lower bound does not move at all, and the binding upper
   bound (case 5, competitive) shifts by between −1.3 and +0.5 points across every plausible
   reading of *"average on everything"*. **44 survives on a worst-case margin of seven tenths of
   a point**, which is thinner than anybody should be comfortable with — see the consequences.

5. **§9.3.5's `NoEvidence` clause stands, on both sides.** `|mine| = 0 → NoEvidence`;
   `|theirs| = 0 → NoEvidence`. See below: #184 recorded this as struck and it is not.

**The term ends with no constants.** The ticket that asked for *"its four constants"* is
answered *there are none*.

### The correction #184 carried, and why it is not a re-opening

[#184](https://github.com/Raketa02/Raketa/issues/184) listed §9.3.5's closing clause among the
things already decided and not to be re-opened, on the grounds that
[ADR-0102](0102-silence-is-never-scored.md) *"made the grid required … and removed the case"*.
ADR-0102 says the opposite, in its own part 3:

> Requiring the field at commit does not make blank grids impossible: a player may clear their
> grid afterwards through `AvailabilityChanged`, and profiles committed before this record may
> already hold one. **The matcher's standing rule is therefore *blank means we do not know*, and
> it is the rule the engine is built to, not a migration artefact.**

ADR-0102 removed the case *at profile commit* and deliberately kept the *rule*, naming both
routes by which a blank grid still arrives. The clause survives verbatim, and it is load-bearing
twice over: it is the only thing standing between the term and a division by zero, and scoring a
cleared grid as `0` would be the invented zero
[ADR-0098](0098-matcher-demands-as-executable-contracts.md) forbids and ADR-0102 was written to
remove.

### What the term owes, having no constants to owe it with

§13 is titled *"Every constant, and what kills it"*, so a term with none would simply be absent
from it — which is exactly how the term went unfalsified in §24 for as long as it did. **The
shape is three claims and each owes a falsifier**, carried as `ranking-weights.md`'s existing
*"Falsified by"* bullets, with one line in §13 pointing at them so a reader auditing coverage
does not read absence as an oversight:

| The claim | Falsified by |
|---|---|
| The denominator is the searcher's own slots, and the one-cell searcher's high scores are priced by reciprocal fit rather than by a constant | Decline rate by searcher grid size. If a one-cell searcher's candidates decline no more often than a twenty-one-cell searcher's, `fit_ba` is not doing the pricing |
| Proximity does not belong in the score | Acceptance rate by `days_away`, held out. **A strike owes a falsifier as much as an adoption does** |
| The lumpiness below is an acceptable price | The distribution of distinct term values by searcher grid size. **Readable before `matches` exists** |

## Consequences

- **The prototype's maths was right.** §9.3.5 opens *"three fixes over the prototype's bare
  `shared ÷ mine`"*, and all three are now struck, each for its own reason. This is the first
  place on the map where the **document** loses to the **prototype** on algorithm rather than on
  surface — the standing rule is *the document wins on algorithm, the prototype wins on
  surface*, and it is rebutted here on the document's own §6.5 principle.

- **The term is lumpy, and that is taken knowingly.** `|shared| / |mine|` takes at most
  `|mine| + 1` distinct values, so for a three-slot searcher the second-heaviest for-fun term is
  a **four-way sort key** — `{0, 5.9, 11.7, 17.6}`. [#179](https://github.com/Raketa02/Raketa/issues/179)
  struck a falsifier for precisely this lumpiness in `dr(n)`. We accept it: *none / some / most
  / all of your week* is an honest description of what the product means, six continuous terms
  break the ties, and the third falsifier above is the one that would tell us otherwise. Note
  the inversion it creates — the **picky** searcher gets the coarse term and the **flexible** one
  gets the fine-grained one.

- **The one-cell grid is the strongest play on this term, and nothing new prices it.** ADR-0102
  set the minimum at one tick. A one-cell searcher scores **1.00** on anyone who shares that cell
  and 0.00 on everyone else; a twenty-one-cell searcher can never exceed `|theirs|/21 ≈ 0.33`
  against a typical candidate. The *expectation* is identical — `t/21`, independent of `|mine|` —
  but `QUALITY_FLOOR` reads the distribution, not the expectation. ADR-0102 refused the blank
  grid because it *"rewards saying nothing with a perfect score on the term"*; one tick now does
  most of that. **We price it with `fit_ba` and `ASYM_TOLERANCE`, which already exist and already
  run on the shortlist**, rather than with a new constant — and the first falsifier above is what
  says whether that was right.

- **ADR-0099 rung A can shrink a candidate's score, and this record does not fix it.** Rung A
  adds a slot to the searcher's own grid; any candidate who does not share the added slot goes
  from `s/m` to `s/(m+1)`, strictly lower. At `|mine| = 3, |shared| = 3` one unhelpful added slot
  costs **3.5 for-fun points**, and ADR-0099 §3's follow-on offer to make a widen permanent makes
  it permanent for every future search. The rung's offered count is a real re-run and stays
  honest, so nothing is being hidden — but *relaxation that evicts* is a real shape and it is
  recorded here rather than discovered later.

- **`QUALITY_FLOOR`'s margin is seven tenths of a point, and the fixture that would prove it does
  not exist.** `ranking-weights.md` §10 states that each of the six cases *"now carries an
  explicit term-value reading"* and that the floor is *"re-derivable by machine"*. The document
  holds only the seven totals; there is no per-term table anywhere in
  `docs/specs/matchmaking/`. This record is the first thing to need it and the first to find it
  missing. The availability column is written out here for all six; the other six terms are filed
  as [#186](https://github.com/Raketa02/Raketa/issues/186), blocking
  [#172](https://github.com/Raketa02/Raketa/issues/172).

- **A struck factor stays diffable, at the cost of four telemetry fields.**
  [ADR-0118](0118-a-past-search-is-not-reproducible.md)'s recorded corpus re-weights recorded
  term *values*. If only the value were recorded, the day a future ruleset re-admitted
  `significance` or `proximity` the corpus could not re-derive either, and **the strike would
  become irreversible by accident** — the failure
  [#183](https://github.com/Raketa02/Raketa/issues/183) named for `liveness_signals` and fixed
  the same way. So the raws are recorded: `searcher_slot_count` on the `search` row,
  `shared_count` / `their_slot_count` / `days_away` on `search_candidate`. `days_away` is
  recorded **although nothing scores it**, because it is the input to its own falsifier.

- **`next_slot` picks at day resolution, and the client says how near it is.**
  `next_shared(shared, today: IsoWeekday)` matches
  [ADR-0100](0100-challenge-window-derived-never-chosen.md)'s `window_of` signature exactly — no
  date, no timezone, the caller resolves *today*. A cell on today's weekday reads `days_away = 0`
  whatever the part, because the grid is *a preference, not a promise* and part resolution would
  claim a precision the data does not have. The wire carries `next_slot: {day, part}` — a **cell
  of the grid, not a relative time** — so *"today"* versus *"Monday"* is the client's word, which
  is [ADR-0022](0022-kernel-negative-space-and-constant-homes.md) unchanged.
  `scale-posture.md`'s *"only ADR-0100's derived window needs a zone"* becomes **the window and
  the next-shared-slot derivation**: a second reader of the same input, not a second parameter,
  so the *"trigger 4 plus one clock parameter"* promise survives intact.

- **The rule is reusable and is the point.** This is
  [ADR-0117](0117-a-group-term-reads-only-what-fit-did-not.md) one level down — 0117 admits a
  **term** only if it reads what no seat's Fit read; this admits a **factor** only if it reads
  the pairing. The next term that arrives with three factors and one argument gets tested against
  it rather than against three separate refutations.
