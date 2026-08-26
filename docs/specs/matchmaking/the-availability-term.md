# The availability term: the glossary's ratio, and nothing else

Resolves [#184](https://github.com/Raketa02/Raketa/issues/184) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
The rule is [ADR-0120](../../adr/0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md); this
file is the arithmetic, the readings and the falsifiers.

[`ranking-weights.md`](ranking-weights.md) settled seven terms and left this one carrying a
weight with no formula behind it — **11 competitive / 16 for fun**, which on the day-one
renormalised basis is **17.6 of 100 and the second-heaviest for-fun term.** It appears in
neither constant table, §13's or §24's, and had never been tested.

---

## 1. The term

```
availability = |shared| / |mine|
```

`|shared|` is the number of grid cells both players ticked; `|mine|` is the number the
**searcher** ticked. That is the root [`CONTEXT.md`](../../../CONTEXT.md) definition verbatim:
*"the denominator is your slots, because the question it answers is how much of my week does
this person cover."*

**Blank on either side returns `NoEvidence`** and the term renormalises away (§10):
`|mine| = 0 → NoEvidence`, `|theirs| = 0 → NoEvidence`. §9.3.5's closing clause survives — see
§5 below, where [#184](https://github.com/Raketa02/Raketa/issues/184) had it recorded as struck
and it is not.

**No constants.** The ticket asked for *"its four constants"*; the answer is that there are
none. What the term owes instead is in §4.

### Reversed, for `fit_ba`

`ranking-weights.md` §9's reciprocal fit flips the denominator to the **candidate's** slots,
per the glossary. That is the whole of the flip: `|shared|` is symmetric, so `fit_ba`'s
availability is `|shared| / |theirs|`.

### What is struck, and why each fails differently

| Struck | Why |
| --- | --- |
| `significance = \|shared\| / min(\|mine\|,\|theirs\|)` | **Identically equal to `overlap`** whenever the candidate has at least as many slots as the searcher, so for that majority `0.55·overlap + 0.25·significance` is just `0.80·overlap`. Where it *does* differ it ranks **less** coverage above **more**: at `\|mine\| = 14` a candidate sharing their single slot scores **0.423** against **0.359** for one sharing three of yours. What it claims to read — *they flagged two slots all week, so they mean it* — is **intent**, which has a term at 14/14 |
| `staleness = clamp(1 − (grid_age_days − 60)/240, 0.6, 1)` | Reads **account age**. `grid_age_days` runs from `availability_changed`, which most players never emit, so for them it is time since profile creation — and the clamp binds at **day 156**, so within six months the market is docked identically and the published `240` is never reached. That is [ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md) in a mirror. §9.3.5 never says **whose** grid, either. And the stale grid already has a mechanism: the inline *"Keep these times?"* offer on the search screen |
| `proximity = exp(−days_to_next_shared / PROX_TAU)`, `PROX_TAU = 5 d` | Reads **which weekday you searched**. The grid recurs weekly so `days_to_next_shared ∈ [0,7)`; §9.3.5's *"an overlap in nine days evaporates"* is written for a horizon this grid does not have, and τ = 5 over a six-day domain is a near-linear ramp wearing an exponential's clothes. It re-scores an unchanged pair every day — ~2.5 for-fun points by weekday — and if it scored, every one of §10's six judged pairings would need a **search weekday** attached, a judgement never made |

All three fail one test: **none of them reads the pair.**

---

## 2. What proximity still does

Struck from the score, kept as evidence — [ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md)'s
shape. It keeps the two jobs it is genuinely about:

- **The card's sentence.** `availability.py`'s own invariant is that *"only the count of shared
  slots and the name of the next shared one are ever shown"*, which sanctions exactly
  `shared_count` and `next_slot` and nothing else.
- **Ordering [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md) rung A's
  slot suggestions.** The rung tests single-slot additions to the searcher's grid; which one to
  lead with is a proximity question and always was.

### `next_shared(shared, today: IsoWeekday)`

Day resolution, matching [ADR-0100](../../adr/0100-challenge-window-derived-never-chosen.md)'s
`window_of(grid, today)` signature exactly — no date, no timezone, the caller resolves *today*.
A cell on today's weekday reads `days_away = 0` whatever the part of day it is now.

Part resolution was rejected: the grid is *a preference, not a promise*, the product's finest
time precision is a third of a day, and #166 already ruled this term is *"evidence a game can be
arranged, never a proposed time"*. Nothing is lost by it — the wire carries `next_slot:
{day, part}`, **a cell of the grid rather than a relative time**, so *"today"* versus *"Monday"*
is the client's word to choose with the clock it already has
([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md)).

**One correction rides along.** [`scale-posture.md`](scale-posture.md)'s multi-country
commitment says *"the clock half is ADR-0100's derived window"* — it is now **the window and
this derivation**, a second reader of the same `IsoWeekday` input rather than a second
parameter. *"Trigger 4 plus one clock parameter"* is intact.

### The evidence blob

```
{kind: "availability_overlap", shared_count, next_slot: {day, part}}
```

`grid_stale` is gone with `staleness`. **`days_away` does not cross the wire** — it is derivable
from `next_slot`, and #171 settled that *a reason line never restates a value the card already
renders*. It is recorded in the store (§3), because ADR-0106's line is *the wire union is
closed, the store stays open*.

---

## 3. What the search record holds

Additional to [`search-telemetry.md`](search-telemetry.md) §2 and §3, where these land.

| Column | Row | Why |
|---|---|---|
| `searcher_slot_count` | `search` | Per-search, not per-candidate: the near-miss band pays per-candidate costs ten rows at a time. The denominator, and the input to the first falsifier |
| `shared_count` | `search_candidate` | |
| `their_slot_count` | `search_candidate` | Not read by the term. Recorded so a re-admitted `significance` is re-derivable |
| `days_away` | `search_candidate` | Nullable — null when nothing is shared. Recorded **although nothing scores it**, because it is the input to its own falsifier |

**The raws, not the value.** [ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md)'s
recorded corpus re-weights recorded term *values*. If only the value were kept, the day a future
ruleset re-admitted `significance` or `proximity` the corpus could not re-derive either, and
**the strike would become irreversible by accident** — the failure
[#183](https://github.com/Raketa02/Raketa/issues/183) named for `liveness_signals`, fixed the
same way one term over.

`degraded_terms` already carries the `NoEvidence` case; **which side was blank** rides in the
`terms` blob, so a stood-down term is distinguishable from one that never ran.

`grid_updated_at` is **not** recorded here. With staleness struck it has no search-side reader;
the *"Keep these times?"* backstop reads the profile.

---

## 4. Three claims, three falsifiers, no constants

§13 is titled *"Every constant, and what kills it"*, so a term with none is simply absent from
it — which is how this term went unfalsified in §24 for as long as it did. The shape is three
claims and each owes one, in `ranking-weights.md`'s existing *"Falsified by"* form.

| The claim | Falsified by |
|---|---|
| **The denominator is the searcher's own slots**, and the one-cell searcher's high scores are priced by reciprocal fit rather than by a constant | **Decline rate by searcher grid size.** If a one-cell searcher's candidates decline no more often than a twenty-one-cell searcher's, `fit_ba` is not doing the pricing and §6 needs a real mechanism |
| **Proximity does not belong in the score** | **Acceptance rate by `days_away`, held out.** A strike owes a falsifier as much as an adoption does; if acceptance falls off sharply inside the week, this is the record to come back to |
| **The lumpiness in §6 is an acceptable price** | **The distribution of distinct term values by searcher grid size.** The only one of the three **readable before `matches` exists** — plain SQL over §3's columns |

---

## 5. The `NoEvidence` clause was never struck

[#184](https://github.com/Raketa02/Raketa/issues/184) listed §9.3.5's closing sentence —
*"Either grid empty → `NoEvidence`"* — among the things already decided and not to be
re-opened, on the grounds that [ADR-0102](../../adr/0102-silence-is-never-scored.md) *"removed
the case"*. ADR-0102 part 3 says the opposite, naming both routes by which a blank grid still
arrives: a player may clear their grid through `AvailabilityChanged`, and profiles committed
before that record already hold one. Its words: *"the matcher's standing rule is therefore
blank means we do not know, and it is the rule the engine is built to, not a migration
artefact."*

ADR-0102 removed the case **at profile commit** and deliberately kept the **rule**. The clause
stands, on both sides, and is load-bearing twice: it is the only thing between the term and a
division by zero, and scoring a cleared grid as `0` would be the invented zero
[ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) forbids and ADR-0102 was
written to remove.

**A correction to the ticket's framing, not a reversal of a fenced decision.**

---

## 6. What this costs, stated rather than discovered later

### The term is lumpy

`|shared| / |mine|` takes at most `|mine| + 1` distinct values. For a three-slot searcher the
second-heaviest for-fun term is a **four-way sort key** — `{0, 5.9, 11.7, 17.6}`.
[#179](https://github.com/Raketa02/Raketa/issues/179) struck a falsifier for exactly this
lumpiness in `dr(n)`.

Taken knowingly: *none / some / most / all of your week* is an honest description of what the
product means, six continuous terms break the ties, and §4's third falsifier is what would say
otherwise. Note the inversion — the **picky** searcher gets the coarse term and the **flexible**
one gets the fine-grained one.

### The one-cell grid is the strongest play, and nothing new prices it

ADR-0102 set the minimum at one tick. A one-cell searcher scores **1.00** on anyone who shares
that cell and **0.00** on everyone else; a twenty-one-cell searcher can never exceed
`|theirs|/21 ≈ 0.33` against a typical candidate.

The **expectation is identical** — `E[|shared|] = |mine|·|theirs|/21`, so `E[overlap] =
|theirs|/21`, independent of `|mine|`. But `QUALITY_FLOOR` reads the **distribution**, not the
expectation: the picky searcher's term is bimodal at `{0, 1}` and the flexible one's is pinned
near `|theirs|/21` for everybody, so no candidate ever excels for them on this term.

ADR-0102 refused the blank grid because it *"rewards saying nothing with a perfect score on the
term"*. **One tick now does most of that.** We price it with `fit_ba` and `ASYM_TOLERANCE`,
which already exist and already run on the shortlist, rather than with a new constant — the map
having twice struck a mechanism a live one already covered — and §4's first falsifier is what
says whether that was right.

### ADR-0099 rung A can shrink a candidate's score

Rung A adds a slot to the searcher's **own** grid. Any candidate who does not share the added
slot goes from `s/m` to `s/(m+1)`, strictly lower. At `|mine| = 3, |shared| = 3` one unhelpful
added slot costs **3.5 for-fun points**, and ADR-0099 §3's follow-on offer to make a widen
permanent makes it permanent for every future search.

Nothing is hidden — the rung's offered count is a real re-run, so the number the player sees is
true. But **relaxation that evicts** is a real shape and it is recorded here rather than
discovered in production.

---

## 7. The floor holds, on a margin of seven tenths of a point

`ranking-weights.md` §10 fixes `QUALITY_FLOOR = 44` against `24.2 < FLOOR ≤ 46.0`. Changing the
term's formula changes the six judged pairings' readings, so the floor owes a re-check. This is
the availability column, written out — the first of the six that anybody has written down.

| Case | Availability reading | Under §9.3.5 | Now |
|---|---|---|---|
| 1 · same level, **three shared evenings**, five minutes away, socially blank | `\|shared\| = 3`, and the prose reads as the searcher's own three | `0.80 + 0.20·prox` | **1.00** |
| 2 · ideal level, even forecast, close — **no shared slot at all** | forced | **0.00** | **0.00** |
| 3′ · just inside the level gate, forecast at its floor, **no slot**, edge of the radius, no tag relationship | forced | **0.00** | **0.00** |
| 4 · everything exceptional, competitive searcher, friendly-only candidate | *exceptional* | `0.80 + 0.20·prox` | **1.00** |
| 5 · **the median stranger** — average on everything | *average* | `0.40 + 0.20·prox` | **0.50** |
| 6 · strong match inside the searcher's radius, searcher outside theirs | *strong* | high | high |

**Both bounds survive, and one of them cannot move at all.**

- **The lower bound is untouched.** Cases 2 and 3′ both read *no shared slot*, which is `0.00`
  under both formulas. `24.2` is exactly what it was.
- **The upper bound moves by at most 1.3 points.** Case 5 competitive is the binding one at
  `46.0`, and `prox` was never written down, so the shift spans its whole range: `−1.26` if it
  was read at `1.00` → **44.7**; zero if it was read at `0.50`; `+0.50` if it was read at the
  domain minimum `0.30` → **46.5**.

```
24.2  <  44  ≤  44.7
```

**`QUALITY_FLOOR = 44` holds** — by seven tenths of a point in the worst reading, which is
thinner than anybody should be comfortable with.

### And the fixture that would settle it does not exist

§10 states that each case *"now carries an explicit term-value reading"* and that the floor is
*"re-derivable by machine"*. The document holds only the seven totals; there is no per-term
table anywhere in `docs/specs/matchmaking/`. **This ticket is the first thing to need it and the
first to find it missing** — which is why the bound above is a range rather than an arithmetic
fact.

The availability column is written out above. The other six terms are
[#186](https://github.com/Raketa02/Raketa/issues/186), blocking
[#172](https://github.com/Raketa02/Raketa/issues/172): reconstructing them means re-making
judgements that were made once and never recorded, which is original work and not an assembly
pass.

---

## 8. What moves elsewhere

| File | Change |
|---|---|
| [`ranking-weights.md`](ranking-weights.md) | §2 points here for the formula; §13 gains one line saying the term contributes no constants, so a coverage audit does not read absence as an oversight — which is how §24 lost it |
| [`the-group-objective.md`](the-group-objective.md) §2.3 | `group_avail = significance₄`. `staleness₄` and `proximity₄` go with their pairwise originals. §9.9's X4 contrast turns on `\|shared₄\|` and is untouched; `significance₄` survives because among four people there is no *mine*, so it is the group's only coverage factor and is not degenerate there |
| [`search-telemetry.md`](search-telemetry.md) | §3's four columns |
| [`scale-posture.md`](scale-posture.md) | The clock-parameter correction in §2 |
| [`README.md`](README.md) | Two rows on the conflict table: §9.3.5's three factors, and §24's missing row |

**Nothing is added to the map's missing-surface fog.** The one signal readable before `matches`
exists is a distribution over the search records — plain SQL over tables
[#169](https://github.com/Raketa02/Raketa/issues/169) already built, needing no new place to
read anything. [#183](https://github.com/Raketa02/Raketa/issues/183) is the only other decision
on this map that could say that.
