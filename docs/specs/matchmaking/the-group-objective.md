# The doubles group objective: what the four are optimised for

Settles [#180](https://github.com/Raketa02/Raketa/issues/180) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

§9.9's principle — **the group is the objective, not the sum of pairs** — is accepted. Reading it
against what the map has already settled found that most of its arithmetic does not implement it,
and found the reason in one sentence:

> **A four contains six pairs. The searcher is in three of them.** Every gate and every term in
> this engine was decided while looking at a shortlist, where the searcher is one half of every
> pair on the screen.

Two ADRs and one spec file follow from that.
[ADR-0116](../../adr/0116-in-a-four-every-gate-binds-all-six-pairs.md) makes the gates bind all
six. [ADR-0117](../../adr/0117-a-group-term-reads-only-what-fit-did-not.md) admits a term into the
objective only if it reads something no seat's Fit read.

---

## 1. Admissibility: the three gates, over six pairs

[ADR-0116](../../adr/0116-in-a-four-every-gate-binds-all-six-pairs.md). A pairwise gate over
candidates **cannot be spent at candidate generation** — eligibility for a *seat* is a property of
a combination, not of a candidate — so it moves inside enumeration, where §9.9 already puts the
quality floor.

| Gate | Reading in a four | Fails |
| --- | --- | --- |
| Block ([ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)) | no edge, either direction, between any two of the four | **closed** — one bulk query over the `K` ids; unresolvable ⇒ the line-up refuses |
| Gender preference ([ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)) | mutually satisfied between every pair | closed; already in the index |
| Level ([ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)) | `Δμ < LEVEL_TOL_mode` for every pair | closed; already in the index |

**Newness tightens the pairs it is in, not the search.**
[ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md) binds *the pairing and
not the search*, so every pair containing a newcomer takes `LEVEL_TOL_COMP` in both modes,
whoever ran the search.

**The mechanism is one `K × K` bitmask**, precomputed once per line-up — 276 pair triples at
`K = 24` — after which a combination is admissible iff its three candidate-pairs are set. Three
lookups against 6 072 evaluations; `O(K²)` against a cubic enumeration.

**One class of gate is deliberately left searcher-only:** ADR-0098's pending-pair set — *do these
two already have an open challenge* — is a `matches` fact that fails **soft**, and a soft gate
made pairwise on an absent provider would empty every line-up.

---

## 2. The objective

```
G(lineup) = w_bal      · balance_norm(arrangement)
          + w_seatfit  · mean( post-modifier Fit of the unlocked non-viewer seats )
          + w_minfit   · min ( post-modifier Fit of the unlocked non-viewer seats )
          + w_cross    · ( mean(cross reading over the three cross pairs) + seat_delta )
          + w_crossmin · min ( cross reading over the three cross pairs )
          + w_avail    · group_avail

hard rules:  any seat below QUALITY_FLOOR disqualifies the combination
             any pair failing §1 disqualifies the combination
             no group floor exists — G is only ever compared to another G
```

Each term reads something no other reads:

| Term | Reads | Invisible to |
| --- | --- | --- |
| `w_bal` | team strengths under the arrangement | every Fit |
| `w_seatfit` | mean of the searcher's Fits | — |
| `w_minfit` | min of the same | — |
| `w_cross` | the three cross pairs, plus the partner seat delta | every Fit |
| `w_crossmin` | the worst of the three cross pairs | every Fit |
| `w_avail` | the four-way slot intersection | every Fit |

### 2.1 What a cross reading is

A **cross pair** is a pair inside a line-up containing no searcher — three of the six, invisible
to Fit by construction. A cross reading is **Fit's own person-to-person sub-score**, renormalised
over its own three terms on `ranking-weights.md` §2's day-one basis:

```
cross(x, y)  comp = ( 16.1·intent + 10.3·style + 4.6·vibe ) / 31.0
             fun  = ( 15.4·intent + 12.1·style + 24.2·vibe ) / 51.7
```

It invents no constant, and it inherits the inversion for free: **51.7% of a for-fun Fit is
person-to-person against 31.0% competitive**, so a cross reading is automatically worth more in a
friendly without `w_cross` having to say so a second time. Style and vibe come from the same
matrix, `dr()`, `TAG_PHI` and seat scope as Fit — **one implementation of *how do these two get
on*, called six times, three printed as Fit and three feeding the objective.**

### 2.2 The seat delta

[#179](https://github.com/Raketa02/Raketa/issues/179) ruled that an unseated pair reads the
`OPPONENT` row and a `PARTNER`-only row does not fire at all, handing the harsher reading to the
seating stage. The **seat delta** is what a pair's reading gains when it stops being unseated:

```
seat_delta = cross_at(PARTNER, viewer, partner) − cross_at(OPPONENT, viewer, partner)
```

Added for the searcher's partner pair only; **exactly zero for the two opponent seats by
construction**, because unseated already reads `OPPONENT`.

**A seated reading never re-scores Fit.** The card said 78 in the shortlist and it says 78 in the
builder. The delta enters `G` and the line-up's reasons; it never enters `fit`
([ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md),
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).

### 2.3 Group availability

Three good pairwise overlaps do not imply a four-way one. A searcher free Monday and Tuesday,
`a` free Monday, `b` free Tuesday, `c` free Monday reads well on every Fit and gives **a four
with no common slot**.

```
group_avail    = significance₄ · proximity₄ · staleness₄

significance₄  = |shared₄| / min over the four of |their declared slots|
proximity₄     = exp( −days_to_next_shared₄ / PROX_TAU )          PROX_TAU = 5 d
staleness₄     = min over the four of §9.3.5's staleness
```

**No new constant.** `PROX_TAU`, `significance` and the staleness bounds are §9.3.5's own;
§9.3.5's asymmetric `overlap` — *"the denominator is your slots"* — does not generalise, because
among four people there is no *mine*. `staleness₄` takes the **minimum** because the weakest grid
sets the confidence, which is ADR-0098's shape.

**A term, not a gate.** The pairwise term does not gate at zero either, and ADR-0099 rung A
relaxes exactly these times. An empty intersection zeroes the whole term — 16 / 20 points — and
carries `NO_SHARED_SLOTS`, so the screen can say *"you would all have to bend"*, which is the
prototype's shipped copy for the pairwise case.

**There is deliberately no group distance term.** Four people converging is a group property too,
but no court exists to converge on and the searcher's own radius is already priced per pair.

### 2.4 What was struck

| Struck | Why |
| --- | --- |
| `partner_clash_penalty(viewer, partner)` | Re-expressed as the **seat delta**, which is signed and reads complements and matches too |
| `PARTNER_STYLE_MULTIPLIER = 1.6` / `OPPONENT_STYLE_MULTIPLIER = 0.7` | The asymmetry is already carried by the matrix's `seats` scope. A blanket scalar says it a third time, and would scale relationships that have nothing to do with sitting beside somebody — `SHARES_A_LIFT` is a complement about the journey, and a lift is not a seat |
| `group_tag_coherence` over raw tag ids | Breaches [ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md): three of four ticking `OPEN_TO_MEET_SOMEONE` would score, in a term carrying 28 of 100 for fun |
| `group_intent_coherence` read against the searcher | Charges declarations Fit's intent term already charged |
| The ≥ ⌈3n/4⌉ superadditive bonus | Cannot be expressed over matrix rows. Group coherence is an **emergent property of the three cross readings**, never a term. The builder's *"What this group has in common"* panel stays — ADR-0115 permits showing a tag it forbids scoring |
| `G` for singles | Reduces to a monotone transform of Fit plus a re-charged balance term; not order-preserving, so `POST /lineups` and `POST /searches` could disagree on who is best. **The singles line-up is the top-ranked candidate by Fit** |

---

## 3. The weights

Adopted, and **tested** against §4's contrasts rather than asserted.

| Term | Comp | Fun | §9.9 had |
| --- | --: | --: | --- |
| `w_bal` | **34** | 16 | 40 / 20 |
| `w_seatfit` | 20 | 17 | 22 / 20 |
| `w_minfit` | 16 | 13 | 18 / 14 |
| `w_cross` | 8 | **20** | (`w_tag` 8 / 28) |
| `w_crossmin` | 6 | 14 | — |
| `w_avail` | 16 | 20 | — |
| | **100** | **100** | |

**The inversion arrives without being asserted.** Competitive `w_cross + w_crossmin = 14` against
`w_seatfit + w_minfit = 36`; for fun **34 against 30** — plus §2.1's basis, which already makes a
for-fun cross reading richer.

**`w_crossmin` earns its place on intent, not on clashes.** An opposed-intent cross pair zeroes
the intent component and drops that reading by **0.519** competitive / **0.298** for fun —
through the min and its share of the mean, **4.5 and 6.2 points**. That is §9.9's own example,
*one person keeping score in a four where three want a beer*, priced for the two people Fit never
asked about.

**A full tag clash between two candidates is worth about 1.0 point for fun and 0.5
competitive.** `CLASH_CAP` normalised over `[−CLASH_CAP, 1]` costs 0.20 of a column's range; the
column is 23% of a cross reading; then it is diluted across three pairs. **This is
[#179](https://github.com/Raketa02/Raketa/issues/179)'s decision carried faithfully, not a
defect** — the same order of magnitude it measured for competitive singles, and §9.3.6 rule 3
(*being wrong about a clash buries a person*) is why it is small. At group level the clash arm is
a tie-breaker.

**`w_bal 16` against `w_seatfit 17` for fun is parity, and that is the vector's known weak
point.** Competitive reproduces §9.9's founding claim easily at 34 against 20. For fun, contrast
X1 resolves only when the balance gap is large and the Fit gap small — deliberate, since for-fun
balance is 6.6 of 100 in Fit and evenness is not what a friendly is for, but it is **the first
contrast to re-run** once real fours exist.

### 3.1 The arrangement

Because the seat delta varies by arrangement, the combination is chosen by **`argmax G` over all
three pairings**, and `arrange()` stops being a separate step. `scale-posture.md`'s 6 072
evaluations already budget per-arrangement work, so the cost is one array lookup.

**Balance outweighs the seat delta by roughly fifty to one.** The delta is 0.34 points for fun and
0.19 competitive; balance across the three arrangements of a four at 3.0 / 3.2 / 3.5 / 3.8 spans
gaps of 0.025, 0.245 and 0.545 — 0.52 of `balance_norm`, **17.8 points** at `w_bal = 34`. So
`is_best ≠ is_evenest` will essentially never fire for a four with any level spread, and *will*
fire for a four of near-equal levels — **precisely when balance has nothing left to say.** ADR-0103's
shape, arriving on its own; recorded so nobody later finds the term inert and rips it out.

`is_best` on [`the-two-contracts.md`](the-two-contracts.md) §5's three arrangements now means
*best by `G`*. ***Even it out* keeps its own meaning** — it selects the min-gap arrangement — and
the glossary's two forecasts stay two words. The new fact the builder can state is
`is_best ≠ is_evenest`.

### 3.2 The cost

| | | |
| --- | --: | --- |
| Measured today (`scale-posture.md` §6) | 8.2 ms | 6 072 evaluations, M3 Max; 27% of the 90 ms budget derated |
| `O(K²)` precompute | ~1.7 ms | 276 admissibility triples, 552 seat-scoped tag readings, 276 intent comparisons |
| Per combination | ~1.0 ms | three cross lookups, one 21-bit grid `AND` + popcount |
| Per arrangement | ~0.3 ms | one seat-delta lookup |
| **Estimated** | **~11 ms** | **25–38% of budget derated**, against 27% today |

**Estimates, not measurements**, and owed one before build — the standard
[#161](https://github.com/Raketa02/Raketa/issues/161) and
[#165](https://github.com/Raketa02/Raketa/issues/165) set. The *shape* is unchanged: still cubic
in `K`, still dominated by the per-combination term, and an `O(K²)` precompute cannot overtake
it, so **`K = 24` and its engine-side ceiling stand.**

Aside, recorded because it is in the right direction: `scale-posture.md`'s 6 072 is `C(24,3)·3`,
but §9.9 fixes the viewer's seat — `C(23,3)·3 = 5 313`. The measurement is 14% conservative.

---

## 4. What would prove the vector wrong

**`G` needs ordered contrasts, not judged verdicts — and no floor.**
[`the-five-numbers.md`](the-five-numbers.md)'s six judged pairings work because `QUALITY_FLOOR` is
a *bar* and needs absolute Fit values. `G` is only ever compared to another `G`; nothing is shown
because its `G` cleared something. So the fixture is **contrasts** — *this four should beat that
four* — which are cheaper to state than a judged line-up and are exactly what an argmax consumes.

| | Claim | Sets |
| --- | --- | --- |
| **X1** | Four excellent individual Fits, lopsided teams **loses to** three good and one modest, near-perfect balance | `w_bal` : `w_seatfit` |
| **X2** | Fits 90 / 88 / **46** **loses to** 72 / 71 / 70 | `w_minfit` : `w_seatfit` |
| **X3** | Otherwise equal, one four carries an opposed-intent cross pair — it **loses** | `w_crossmin` |
| **X4** | Best on every other term with **zero** four-way shared slots **loses to** clearly worse with three | `w_avail` |
| **X5** | Searcher's Fits excellent / cross poor **beats** the reverse **in competitive, and loses in for fun** | `w_cross` by mode |
| **X6** | Same four, two arrangements at near-identical balance — the one not seating `TALKS_THROUGH_THE_MATCH` beside `QUIET_AND_FOCUSED` **wins** | the seat delta |

X2 is worked: mean .747 / min .46 against mean .710 / min .70 — competitive, A gains
`20 × .037 = 0.74` and B gains `16 × .24 = 3.84`.

**X3 and X6 are near-tie claims, and the first drafts of both were wrong.** They were written as
dominance claims — a clash beating a modest advantage elsewhere — and §3's arithmetic refutes both
at ~1.0 and ~0.34 points. Recorded rather than quietly rewritten, because the correction *is* the
finding: at group level the tag arms break ties and intent moves scores.

### 4.1 Every constant, and what kills it

| Constant | Start | Falsified by |
| --- | --: | --- |
| Group weights, comp | §3 | Return rate of completed doubles by line-up profile |
| Group weights, fun | §3 | Same, split by mode. **X1 first** |
| `w_minfit` | 16 / 13 | Return rate of the **worst-fit seat** against the mean-fit seat in the same four. If flat, the mean/min split is unnecessary and it folds into `w_seatfit` |
| `w_cross` | 8 / 20 | Return rate of **the two players who did not search**, by their cross reading. If flat, the cross idea is wrong at the root |
| `w_crossmin` | 6 / 14 | Return rate of the player in the *worst* cross pair, against the other two |
| `w_avail` | 16 / 20 | Challenge-to-played conversion for line-ups with zero four-way slots against non-zero |
| `PROX_TAU` | 5 d | Acceptance by days to the next shared slot (inherited from §9.3.5) |
| `significance₄` | §2.3 | The observed live range. If it never leaves the top of its range it discriminates over a range that does not exist |
| The seat delta | §3.1 | **How often `is_best ≠ is_evenest`.** If never, the argmax is decoration |
| `K` | 24 | `max(fit_rank)` among the seated, 95th percentile against `K` — **replaces §24's, which cannot fire** |

§24's own falsifier for `K` reads *"whether the winning combination ever contains a candidate
ranked > K"*, but `scale-posture.md` §6 truncates to the top `K` by Fit, so the answer is **never,
by construction, at every value of `K`.**

**One falsifier measures from the first line-up, before `matches` exists: the distribution of §5's
deciding reason code.** If one code takes more than ~80% of line-ups, the other terms are
decoration and the vector is wrong — and nobody has to wait for an outcome to learn it. Every
other row here waits on the outcome half of the chain, exactly as
[`ranking-weights.md`](ranking-weights.md) says; this one does not, and it is why §6's fourth
telemetry layer is worth its two rows.

---

## 5. What the response carries

**`G` is recorded and never returned as a number.** It chose these four over 2 023 combinations,
and the third refusal — *never a number it cannot explain in one sentence with the evidence named*
— applies. A second score the player must trust is worse than none: it competes with Fit and
nobody can act on it. The **evidence** half is paid by one closed reason code naming **the term
with the largest margin between the winning combination and the runner-up** — the group analogue
of the card's top three reasons.

```
group_reason:  EVENEST_ARRANGEMENT | STRONGEST_WEAKEST_SEAT | BEST_AVERAGE_FIT
             | MOST_SHARED_SLOTS   | GROUP_RAPPORT
```

Closed vocabulary, [ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)-shaped:
the client writes the sentence, the engine names which.

### 5.1 When a seat cannot be filled

[`the-two-contracts.md`](the-two-contracts.md) §5 fixed that the slot and the code exist and left
the vocabulary here. **Same shape, different codes** — a partial line-up is always a `200` with
seats carrying `unfilled_reason`, and *nobody* is that shape with three unfilled seats, never a
separate empty state.

| Code | Means |
| --- | --- |
| `NO_CANDIDATE_ABOVE_FLOOR` | the pool had people; none cleared `QUALITY_FLOOR` |
| `NO_ADMISSIBLE_COMBINATION` | candidates cleared the floor; **no combination passed §1's six pairs** |
| `POOL_EXHAUSTED` | there was nobody |
| `NO_SHARED_SLOTS` | seated, but the four-way intersection is empty — a dock, never a refusal |

`NO_ADMISSIBLE_COMBINATION` is new and load-bearing. Without it
[ADR-0116](../../adr/0116-in-a-four-every-gate-binds-all-six-pairs.md)'s gate is
indistinguishable from a thin pool, on the screen and in the telemetry — and after ADR-0113 it is
also how a screen says *"nobody at their level yet"* about a newcomer's first four rather than
*"nobody"*.

**And the rule inherited unchanged:** a seat is never filled below the quality floor to complete
a line-up ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)), a newcomer
least of all ([#175](https://github.com/Raketa02/Raketa/issues/175)).

---

## 6. What a line-up records that a shortlist does not

[#169](https://github.com/Raketa02/Raketa/issues/169)'s three layers are all **per candidate**.
A line-up's unit is the **combination**, and none of the three sees one — so ADR-0116's gate would
be unfalsifiable and §5's reason code unreproducible.

**A fourth layer, and it is two rows rather than a band:**

| | |
| --- | --- |
| The winning combination | members, and the full `G` breakdown |
| The runner-up | the same — exactly what the deciding margin is computed from |
| Counters | combinations enumerated · refused by the pairwise gate · refused by the floor |
| `max(fit_rank)` among the seated | `K`'s replacement falsifier |

Two rows, not 2 024: enough to replay the choice and compute the margin, and no more than any
question anybody has asked. It inherits #169's rules unchanged — **written before the answer is
returned, never expires, and no route ever returns it.** A runner-up combination is a
group-shaped near miss, and *a player may ask why somebody was shown, and nobody may ask who was
withheld.*

---

## 7. What leaves this ticket

**[#184](https://github.com/Raketa02/Raketa/issues/184) — §9.3.5, the unadopted term.**
`ranking-weights.md` settled level, balance, tags, reliability, modifiers, familiarity, liveness
and the floor. **Availability overlap appears only as a weight** — 11 / **16**, the second-heaviest
for-fun term at 17.6 renormalised — and its formula, `PROX_TAU`, the 0.55 / 0.25 / 0.20 split and
the staleness bounds appear in **no row of §13's constant table**. Its closing clause, *"either
grid empty → `NoEvidence`"*, is **dead**: [ADR-0102](../../adr/0102-silence-is-never-scored.md)
made the grid required and removed the case.

§2.3 takes the three factors the group term needs — `significance`, `PROX_TAU`, the staleness
bounds — and gives them §13 rows; the dead clause is struck here rather than left standing. **The
rest is filed rather than absorbed**, because adopting the second-heaviest for-fun term inside a
doubles ticket is the decision-by-silence this map keeps refusing.
