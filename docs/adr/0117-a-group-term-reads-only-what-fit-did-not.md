# ADR-0117 — A group term reads only what Fit did not

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

§9.9's objective for a doubles four is:

```
G(lineup) = w_bal      · balance_norm(arrange(lineup))
          + w_seatfit  · mean(fit of the three non-viewer seats)
          + w_minfit   · min(fit of the three non-viewer seats)
          + w_intent   · group_intent_coherence
          + w_tag      · group_tag_coherence
          − partner_clash_penalty(viewer, partner)
```

Its stated principle — *the group is the objective, not the sum of pairs* — is right and is
accepted. **Four of its six lines do not implement it.**

`w_seatfit` and `w_minfit` read the searcher's three Fits. `group_intent_coherence` counts
misaligned seats, and read against the searcher it charges the same three declarations Fit's
intent term (14 in both modes) already charged — the shape
[#167](https://github.com/Raketa02/Raketa/issues/167) deleted `intent_opposed` for, and
[#168](https://github.com/Raketa02/Raketa/issues/168) struck the radius-asymmetry dock and the
familiarity σ clause for. `partner_clash_penalty(viewer, partner)` reads the searcher-to-partner
pair a third time.

`group_tag_coherence = Σ over tags held by ≥ ⌈3n/4⌉ seats of dr(count) / normaliser` is worse
than duplicative: it reads **raw tag ids**, not matrix rows.
[ADR-0115](0115-a-tag-about-the-person-may-be-shown-never-scored.md) settled that *a match is a
row, not a rule*, and that `OPEN_TO_MEET_SOMEONE` takes no row of any kind and may never score.
Under §9.9 as written, three of four ticking `OPEN_TO_MEET_SOMEONE` scores — in a term carrying
28 of 100 for fun — from a rule about a different question, which is the exact defect
[#179](https://github.com/Raketa02/Raketa/issues/179) killed. It also ignores `column` and
`modes`.

Meanwhile **the three pairs that no Fit can see are read by nothing.** In a four there are six
pairs and the searcher is in three; the objective as written never asks how `a`, `b` and `c` get
on with each other, and never asks whether all four are free at the same time — the four-way
grid intersection, which three good pairwise overlaps do not imply.

One line is not duplication, and it took a closer reading to see why.
[#179](https://github.com/Raketa02/Raketa/issues/179) ruled that **an unseated pair reads the
`OPPONENT` row and a `PARTNER`-only row does not fire at all** — the forgiving reading, because
*being wrong about a clash buries a person* — and explicitly handed the harsher reading to the
seating stage. So the printed Fit *deliberately declined* to take the partner reading, and
`partner_clash_penalty` is the document's crude name for collecting it.

## Decision

**We will admit a term into the group objective only if it reads something no seat's Fit read.**

> The printed Fit already carries every fact about the searcher-to-candidate pair. What it did
> **not** carry is the three cross pairs, the four-way intersection, the arrangement — and the
> seat-scoped reading of the searcher's own partner pair, which the unseated Fit deliberately
> declined.

Six terms, each reading something no other reads:

| Term | Reads | Invisible to |
| --- | --- | --- |
| `w_bal` | team strengths under the arrangement | every Fit |
| `w_seatfit` | mean of the searcher's Fits, unlocked seats, post-modifier | — |
| `w_minfit` | min of the same | — |
| `w_cross` | mean of the three cross readings, plus the partner **seat delta** | every Fit |
| `w_crossmin` | min of the three cross readings | every Fit |
| `w_avail` | the four-way slot intersection | every Fit |

**A cross reading is Fit's own person-to-person sub-score**, renormalised over its own three
terms — not a second definition of how two people get on. On `ranking-weights.md` §2's day-one
basis that is `(16.1·intent + 10.3·style + 4.6·vibe) / 31.0` competitive and
`(15.4 + 12.1 + 24.2) / 51.7` for fun. It invents no constant, and it inherits the inversion for
free: **51.7% of a for-fun Fit is person-to-person against 31.0% competitive**, so a cross
reading is automatically worth more in a friendly without `w_cross` having to say so a second
time.

**The seat delta is the partner reading minus the opponent reading**, added for the searcher's
partner pair only. For the two opponent seats it is exactly zero by construction, because
unseated already reads `OPPONENT` — which is what #179's rule bought.

**A seated reading never re-scores Fit.** The card said 78 in the shortlist; seating that person
as the searcher's partner must not make it 71.
[ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) makes the recorded Fit the
answer and [ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) makes
its evidence contract — a Fit that moves when somebody crosses the net is *Why 78?* failing on
the one screen that promises to show its working. The delta enters `G` and the line-up's reasons;
it never enters `fit`.

Four things follow and are part of the decision:

- **`partner_clash_penalty` is struck as a named term** and re-expressed as the seat delta,
  which is signed and reads complements and matches too rather than only clashes.
- **`PARTNER_STYLE_MULTIPLIER = 1.6` and `OPPONENT_STYLE_MULTIPLIER = 0.7` are struck.** The
  asymmetry is already carried by the matrix's `seats` scope, which #179 used — two disjoint rows,
  REAL 0.15 as partners and MILD 0.06 across the net, *introducing no constant*. A blanket scalar
  is the same asymmetry expressed a third time, and it would scale relationships that have nothing
  to do with sitting beside somebody: `SHARES_A_LIFT` is a complement about the journey, and a
  lift is not a seat. If product believes the general claim, it belongs as **more `PARTNER` rows**
  — arguable without a code review, per §23 Q18 — and §24's falsifier transfers to them unchanged.
- **The superadditive tag bonus is dropped, and the panel is kept.** A tag shared by three of four
  cannot be scored over matrix rows without reintroducing what ADR-0115 struck, so group coherence
  is an **emergent property of the three cross readings and never a term of its own**. The
  builder's *"What this group has in common"* panel stays — ADR-0115 permits showing a tag it
  forbids scoring, and this is the panel that rule was written for.
- **`w_seatfit` and `w_minfit` read post-modifier Fit and unlocked seats only.** Post-modifier so
  there is one number, the same one the floor tests and the card prints. Unlocked only because a
  locked seat with a poor Fit pins the min across every combination, so `w_minfit` would go inert
  in `FILL_SEATS` — ADR-0103's *blind over the range it is asked to score*, in the objective this
  time. A constant in an argmax is not a term.

## Consequences

**§9.9's arithmetic is replaced; its principle is finally implemented.** *The group is the
objective* now means something checkable — three of the six pairs enter the score, and they enter
through the same functions that print the other three.

**The objective can tell whether the evening can happen.** `w_avail` reads the four-way
intersection, which no Fit sees: a searcher free Monday and Tuesday, `a` free Monday, `b` free
Tuesday, `c` free Monday gives three excellent pairwise overlaps and **a four with no common
slot**. It is a **term and not a gate** — the pairwise term does not gate at zero either, and
ADR-0099 rung A relaxes exactly these times — so an empty intersection is a dock worth 16 / 20
points with a `NO_SHARED_SLOTS` reason, not an exclusion. There is deliberately **no group
distance term**: four people converging is a group property too, but no court exists to converge
on and the searcher's own radius is already priced per pair.

**`w_crossmin` earns its place on intent, not on clashes, and the arithmetic says so.** An
opposed-intent cross pair drops that reading by 0.519 competitive / 0.298 for fun — **4.5 and 6.2
points** through the min and its share of the mean. That is §9.9's own example, *one person
keeping score in a four where three want a beer*, priced for the two people Fit never asked
about. A full tag clash between two candidates is worth about **1.0 point for fun and 0.5
competitive**, because `CLASH_CAP` normalised over `[−0.25, 1]` costs 0.20 of a column's range and
that column is 23% of a cross reading, then diluted across three pairs. That is #179's decision
carried faithfully rather than a defect: the clash arm is a tie-breaker at group level, and
§9.3.6 rule 3 is why it is small.

**The seat delta decides the arrangement exactly where balance saturates.** Because arrangement
now changes one term, the combination is chosen by `argmax G` over all three pairings and
`arrange()` stops being a separate step — at the cost of one array lookup, since
`scale-posture.md`'s 6 072 evaluations already budgeted per-arrangement work. But the delta is
**0.34 points for fun and 0.19 competitive**, while balance across the three arrangements of a
four at 3.0 / 3.2 / 3.5 / 3.8 spans 17.8 points at `w_bal = 34` — **roughly fifty to one**. So
`is_best ≠ is_evenest` will essentially never fire for a four with any level spread, and *will*
fire for a four of near-equal levels, which is precisely when balance has nothing left to say.
This is ADR-0103's shape arriving on its own, and it is recorded here so that nobody later finds
the term inert and rips it out.

**`is_best` changes meaning and *Even it out* does not.** `is_best` on
[`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §5's three arrangements now
means *best by `G`*, not *evenest*. The button keeps its own meaning — it selects the min-gap
arrangement — and the glossary's two forecasts stay two words. The new fact the builder can state
is `is_best ≠ is_evenest`.

**The group objective does not run for singles.** With two seats, `mean` and `min` over one Fit
are the same number, there is no arrangement and there are no cross pairs, so `G` reduces to a
monotone transform of Fit **plus `w_bal · balance_norm`, which re-charges predicted balance** —
already Fit's term 2 at 19.5 / 6.6. The transform is not order-preserving, so `POST /lineups` and
`POST /searches` could return **different best candidates for the same search**, and a player
watching ⚡ pick the second name on the list they were just shown has found a bug. §9.9's
*"singles use the same machinery"* is a claim about code reuse that costs correctness: the shared
machinery is the **scorer**, not the objective. The singles line-up is the top-ranked candidate by
Fit.

**`G` is recorded and never returned as a number.** It chose these four over 2 023 combinations
and the third refusal — *never a number it cannot explain in one sentence with the evidence named*
— applies. Printing a second score the player must trust is worse than printing none: it competes
with Fit and nobody can act on it. The **evidence** half is owed and is paid by one closed reason
code naming the term with the largest margin between the winning combination and the runner-up —
`EVENEST_ARRANGEMENT`, `STRONGEST_WEAKEST_SEAT`, `BEST_AVERAGE_FIT`, `MOST_SHARED_SLOTS`,
`GROUP_RAPPORT` — the group analogue of the card's top three reasons. The client writes the
sentence; the engine names which.

**The cost is estimated and owed a measurement.** An `O(K²)` precompute (552 seat-scoped tag
readings, 276 intent comparisons) at roughly 1.7 ms, plus about 1.0 ms per-combination and 0.3 ms
per-arrangement, moves the group objective from 27% to an estimated **25–38% of the 90 ms line-up
budget** derated. The *shape* is unchanged — still cubic in `K`, still dominated by the
per-combination term — so `K = 24` and its engine-side ceiling stand
([`scale-posture.md`](../specs/matchmaking/scale-posture.md) §6). These are estimates, not
measurements, and [#161](https://github.com/Raketa02/Raketa/issues/161) and
[#165](https://github.com/Raketa02/Raketa/issues/165) set the standard that they get measured
before build.

**It borrows one formula nobody adopted, and says so.** `w_avail` reuses §9.3.5's `significance`,
`PROX_TAU` and staleness bounds — a term carrying 17.6 of 100 for fun whose formula appears in
**no** row of `ranking-weights.md` §13 and whose closing clause, *"either grid empty →
`NoEvidence`"*, [ADR-0102](0102-silence-is-never-scored.md) has since made dead. Those three
factors are adopted here with §13 rows and the dead clause is struck; the rest — the
0.55 / 0.25 / 0.20 split, and whether the pairwise term is right at all — is
[filed as its own ticket](https://github.com/Raketa02/Raketa/issues/184), because adopting the
second-heaviest for-fun term inside a doubles ticket would be exactly the decision-by-silence
this map keeps refusing.
