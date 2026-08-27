# The ranking weights, and what would prove each of them wrong

Settles [#168](https://github.com/Raketa02/Raketa/issues/168) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

Everything the matcher uses to **reorder a list**, as against
[`the-five-numbers.md`](the-five-numbers.md), which decides whether a list exists at all. Each
number here is a starting vector: an admitted hypothesis with a falsifying measurement attached,
in the discipline §24 asks of itself and ADR-0015 already requires of engine constants.

**None of it is measurable before the outcome half of the telemetry chain exists**, which needs
`matches`, which is out of scope. What *can* be done now was done: the vector was **tested**
against `the-five-numbers.md`'s six judged pairings rather than asserted, and the test found
two defects the document had not — one in a term's arithmetic, one in the instrument being
asked to refuse a bad match. Both are recorded below with what they cost.

---

## 1. The eight terms are seven columns and two claims

§9.3 has eight terms; the prototype's `compat()` (`social-prototype-v1.html:1309`) has seven.
Intent alignment accounts for one of the missing two. The other was never written down anywhere:
**the prototype's single `vibe` term merges what the document splits into playing style (§9.3.6)
and social vibe (§9.3.7)**.

The document splits them **by tag group** — `ON_THE_COURT` on one side, `AFTER_THE_MATCH +
WHY_YOU_ARE_HERE` on the other. That split cannot classify its own pair table. Of the eleven
relationships §9.3.6 lists:

| | Count | Examples |
|---|--:|---|
| Wholly inside `ON_THE_COURT` | **1** | `PLAYS_TO_WIN` ↔ `LAUGHS_OFF_MISTAKES` |
| Wholly inside `AFTER_THE_MATCH` + `WHY_YOU_ARE_HERE` | 4 | `HERE_TO_MEET_PLAYERS` + `SHARES_A_LIFT` |
| **Crossing the boundary** | **5** | `TALKS_THROUGH_THE_MATCH` ↔ `QUIET_AND_FOCUSED` |
| Not a tag pair at all | 1 | `HERE_TO_IMPROVE` + *"a stronger, focused opponent"* — reads μ, and §9.3.6's own rule stands it down |

The clearest case is the only clash the document marks **Real**: `TALKS_THROUGH_THE_MATCH` ↔
`QUIET_AND_FOCUSED`, *"ruins the hour for both"* — unambiguously about the hour on court, and
`TALKS_THROUGH_THE_MATCH` lives in `AFTER_THE_MATCH`.

**The split is by relationship, not by tag.** Every entry in the relationship matrix carries a
`column`, **`MATCH` entries included** — a match is a row and not a rule
([ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md)), so a matched
tag's column may differ from its group's and a tag that may not match simply has no row. An
earlier draft of this section had a matched single tag fall to its own group's column, which
would have made the derived-domain rule below false and would have decided
`OPEN_TO_MEET_SOMEONE` by accident. A term is therefore **not a group of tags; it is a group of
claims about pairs** — and which claims are about the hour on court is exactly the kind of
judgement §23 Q18 already assigns to product.

The heading of §9.3.6 (*"the `ON_THE_COURT` group"*) and of §9.3.7 (*"`AFTER_THE_MATCH` +
`WHY_YOU_ARE_HERE`"*) are wrong as written and are not the definition of either term.

### The matrix entry

Product-owned, served as ruleset data — §23 Q18 confirmed. §9.3.6's own table already scopes
entries three ways it gives itself no field for (*"For-fun only"* twice, *"Partner relationship
only"*, *"far worse as partners than as opponents"*), and its complementary rows explicitly
claim some pairs beat a match, which one global `0.7` cannot express.

```
{ a, b,
  kind:     MATCH | COMPLEMENT | CLASH,
  column:   STYLE | VIBE,
  modes:    [COMPETITIVE, FOR_FUN],
  seats:    [PARTNER, OPPONENT],
  strength | severity }
```

The **seat** dimension bites only in doubles (§9.9), but it goes in the
shape now or the group objective has nowhere to read it.

**A column's tag domain is derived from the matrix** — the ids appearing in any entry carrying
that column — never declared separately, so it re-derives itself the moment product edits an
entry. A tag may appear in both domains, and a tag with no entry at all is in neither.

**The thirty-seven rows are [`tag-relationship-matrix.md`](tag-relationship-matrix.md)**, settled
by [#179](https://github.com/Raketa02/Raketa/issues/179): eighteen matches, twelve complements,
seven clashes, the derived domains at **STYLE 10 of 19 / VIBE 12 of 19**, and the firing, seat
and disjointness rules the shape above does not state.

---

## 2. The weights

Adopted as §9.3's, and now **tested** rather than asserted. Weights sum to 100 within a mode
before renormalisation (§10).

| # | Term | Comp | Fun |
|---|---|--:|--:|
| 1 | Level fit | **26** | 11 |
| 2 | Predicted balance | 17 | 6 |
| 3 | Intent alignment | 14 | 14 |
| 4 | Reliability | 13 | 9 |
| 5 | Availability overlap | 11 | **16** |
| 6 | Playing style | 9 | 11 |
| 7 | Distance | 6 | 11 |
| 8 | Social vibe | 4 | **22** |

**Day one, reliability stands down** (§10) and the live seven renormalise — ×100/87 competitive,
×100/91 for fun. This is the basis every number below is checked against, per §5:

| | level | balance | intent | avail | style | distance | vibe |
|---|--:|--:|--:|--:|--:|--:|--:|
| **Competitive** | 29.9 | 19.5 | 16.1 | 12.6 | 10.3 | 6.9 | 4.6 |
| **For fun** | 12.1 | 6.6 | 15.4 | 17.6 | 12.1 | 12.1 | 24.2 |

**The inversion is the shape, and it survives the test.** For fun, social vibe is the largest
term in the match — larger than level — because that is what *for fun* means, and it is a bigger
shift than the prototype's `MM_W` makes.

**Availability overlap carried a weight here with no formula behind it**, and it is settled in
[`the-availability-term.md`](the-availability-term.md):
`availability = |shared| / |mine|`, the glossary's ratio and nothing else. §9.3.5's
`significance`, `staleness` and `proximity` are struck — none of the three reads the pair
([ADR-0120](../../adr/0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md)). The weights are
unchanged at 11 / 16, and §10's floor is re-checked there against the availability column of the
six cases.

### The tag-stuffing constraint, as an inequality rather than an intention

§9.3.6's rule 2 — *"six well-chosen tags must not outrank a good level match"* — is an
intention, and intentions do not survive a weight release. Since both tag terms clamp to `[0,1]`,
the maximum possible tag contribution is exactly `w_style + w_vibe`, and the rule becomes a pure
weight constraint that needs no knowledge of φ or the matrix:

```
w_style + w_vibe  <  w_level × X / LEVEL_TOL_COMP           X = 0.30
```

`X = 0.30` is roughly half `LEVEL_TOL_COMP` — *a noticeably better game*.

| Basis | Left | Right | |
|---|--:|--:|--|
| Day one (renormalised) | 14.9 | 16.3 | ✓ |
| Full eight-term | 13.0 | 14.2 | ✓ |

**Competitive only.** For fun has no such constraint, because in for-fun the tags are *supposed*
to outrank level and saying otherwise would delete the inversion. What binds for-fun is §5's six
pairings, which is stricter and better argued.

- **Falsified by:** return rate by match profile — the ground truth for all eight (§24). And
  return rate by shared-tag count: if flat, the tag terms are worth less than their weight says.

---

## 3. The level curves

```
Δμ = |μ_searcher − μ_candidate|

competitive:  level = clamp(1 − Δμ / LEVEL_TOL_COMP, 0, 1)              LEVEL_TOL_COMP = 0.55
for fun:      level = clamp(1 − max(0, Δμ − FUN_FREE_BAND)
                                 / (LEVEL_TOL_FUN − FUN_FREE_BAND), 0, 1)
                                                                        FUN_FREE_BAND  = 0.25
                                                                        LEVEL_TOL_FUN  = 0.90
```

**The free band is adopted.** The document's argument holds where the prototype's does not: one
curve at a lower weight still ranks your exact twin first, just more quietly, and *"a friendly
against someone a quarter-point above you is no worse than one against your exact twin"* is a
claim about the game, not about the weight.

**The tolerance is absolute on μ, and the level term never calls `band_for`.** The shipped bands
are deliberately uneven — NEW 0.5 wide, DEVELOPING 1.0, ESTABLISHED 1.1, ADVANCED 1.1
(`backend/app/engines/racketskill/core.py`, *"that asymmetry is load-bearing"*) — so a fixed Δμ
tolerance spans more than the whole NEW band and half of ESTABLISHED. That asymmetry exists
because **evidence** is unevenly available down the scale, not because a tenth of a point means
less at the top; the tolerance is a claim about how the game plays.

- **Falsified by:** return rate by level gap, **split by band**. If the curve is right
  absolutely, the split shows nothing. If pairs at Δμ 0.4 return as well as pairs at 0.1, the
  curve is too steep. If the split *does* show something, tolerance is band-relative and this
  section is wrong.
- **`FUN_FREE_BAND` falsified by:** satisfaction and return rate for for-fun games inside versus
  outside the band.

**Both tolerances are also the level gate** ([ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)).
There is one number per mode, not two, so the gate and the curve can never drift apart.

---

## 4. Predicted balance

§9.3.2 transfers, with [#164](https://github.com/Raketa02/Raketa/issues/164)'s promotion of the
clamp bounds to the term's zero and one:

```
σ_pair = combine_sigma(σ_a, σ_b)
pct    = clamp(100 − Δμ·145 − σ_pair·32, BALANCE_PCT_MIN, BALANCE_PCT_MAX)   35, 96
value  = (pct − BALANCE_PCT_MIN) / (BALANCE_PCT_MAX − BALANCE_PCT_MIN)
```

**σ_pair is `combine_sigma`** — `backend/app/engines/racketskill/core.py:95`, *"the single place
any engine is allowed to combine two standard deviations"*. The matcher calls the core; it does
not re-derive the identity, and `√(σ_a² + σ_b²)` appearing in §9.3.2 is that function written
out rather than a second definition of it.

**The term goes blind at Δμ ≈ 0.34** for a typical σ_pair of 0.495 — that is where `pct` reaches
its floor and stops discriminating. Recorded here because it is load-bearing for
[ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md) and because it is not
obvious from the formula.

- **Falsified by:** Brier score of the forecast against confirmed results (§19.1). **The most
  directly falsifiable numbers in the engine** — the 145 and the 32 are a forecast, and a
  forecast is checkable.
- **`BALANCE_PCT_MIN` / `MAX` falsified by:** the observed live range. If real pairings never
  approach 96 or never approach 35, the normalisation is discriminating over a range that does
  not exist.

---

## 5. The tag terms

### The defect: the median outcome was scored as zero

```
style = clamp( dr(matches) + 0.7·dr(complements) − Σ clash_severity, 0, 1 )
```

This makes *"you two clash badly"* numerically identical to *"you two share nothing"*. The clash
arm is invisible whenever there are no matches — which is most comparisons: two random four-tag
draws from nineteen overlap **0.84 times** on average, so the *typical* pair scores at or near
zero on a term carrying 36% of for-fun.

This is the same defect §9.3.2 already identified in predicted balance — *"wastes the bottom 35
points of the range"* — in a term nobody checked. The fix is the same move:

```
dr(n) = 1 − TAG_PHI ⁿ                                       TAG_PHI = 0.45
raw   = dr(matches) + strength·dr(complements) − Σ severity    ∈ [−CLASH_CAP, 1]
value = (raw + CLASH_CAP) / (1 + CLASH_CAP)
```

| raw | value | meaning |
|---|--:|---|
| −0.25 (capped clash) | **0.00** | a real clash, both ways |
| 0 | **0.20** | no relationship fired — *different, not incompatible* |
| 0.55 (one match) | 0.64 | |
| 0.99 (six matches) | 0.99 | |

**The term's zero becomes a real clash, not an absence of relationship** — and the clash arm
becomes visible for the first time.

### The constants

| Constant | Value | Why |
|---|--:|---|
| `TAG_PHI` | 0.45 | 1 tag 0.55 · 2 tags 0.80 · 3 tags 0.91 · 6 tags 0.99. The second matched tag is worth less than the first, so tag-stuffing does not pay — and the platform caps selection at six precisely because it expects people to try |
| `TAG_COMPLEMENT_STRENGTH` | 0.70 | The **default** for a complement entry that states none. A match is two people independently choosing the same string; a complement is product's editorial claim about two different ones, and the discount prices that. An entry may override **upward to a ceiling of 1.00 and never below the default** — §9.3.6's *"sometimes better than a match"* is narrowed by [ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md), because parity is the most an editorial claim can be worth against two people's agreement. Two rows take 1.00 |
| `CLASH_SEVERITY_REAL` | 0.15 | |
| `CLASH_SEVERITY_MILD` | 0.06 | |
| `CLASH_CAP` | 0.25 | Binds at two Real clashes, or one Real plus two Mild |

**`strength · dr(complements)` is written for one discount, and the shipped matrix does not
have one.** Two rows sit at parity beside ten at the default, so *which* complement takes the
first and largest increment is a question the single-strength form cannot ask, and #205 had to
answer it to compute anything at all. `dr` is a sum of shrinking increments,
`Σ (1 − TAG_PHI)·TAG_PHI ⁱ`, so the arm is that sum with each increment priced at one row's own
strength, **strongest first**. Two properties pin it, and both are asserted rather than
described: it is *identically* `strength · dr(n)` whenever every fired row carries the same
strength — the form this table names — and taking the increments in descending strength is what
makes **adding a complement row never subtract**, which pairing them in any other order does not
guarantee. A pairing scored lower for having one more thing in common is not a reading anybody
could defend on a card.

**Clash penalties are capped and smaller than match bonuses**, per §9.3.6 rule 3. One Real clash
(0.15) is worth less than one match (0.55), and the full cap costs 2.6 points of 100 in
competitive — enough to notice, nowhere near enough to bury anybody. Being wrong about a match
costs a duller evening; being wrong about a clash unfairly buries a person, and the magnitudes
are asymmetric because the costs are.

### When a column stands down

**A column stands down when either side holds no tag in that column's domain**; otherwise a nil
result is a **measured** zero, worth 0.20. Both sides hold 2–6 tags by construction, so "we
looked and found no relationship" is a real observation, while "they declared nothing about the
hour on court" is not.

Checked against `the-five-numbers.md`'s evidence gate: a player holding only `AFTER_THE_MATCH`
tags stands playing style down and still fires **6 of 7** live terms, comfortably over the
half-the-live-terms bar. It stays true that the evidence gate excludes nobody today.

- **`TAG_PHI` falsified by:** return rate by shared-tag count. If flat, diminishing returns is
  too weak.
- **`CLASH_CAP` and the severities falsified by:** return rate of games with a scored clash,
  against games with none.
- **The matrix falsified by:** the **coverage rate** — the fraction of scored pairs in which at
  least one complement or clash row fires, over a rolling month, against
  `MATRIX_COVERAGE_FLOOR = 0.20`. Below it the matrix is decorative and either gains rows or the
  two terms collapse to a shared-tag count under a name that says so
  ([`tag-relationship-matrix.md`](tag-relationship-matrix.md) §6). This **replaces** the
  raw-score-distribution test proposed here: `dr(n)` takes seven values, so raw is discrete by
  construction and lumpy at 0 and 0.55 whatever the matrix contains — the test would have fired
  on day one against a perfect matrix. The distribution stays a reported statistic.

---

## 6. Reliability, decomposed by mode

§9.3.4's table transfers unchanged.

| Strand | Comp | Fun |
|---|--:|--:|
| Shows up | 25 | **32** |
| Answers challenges | 22 | 22 |
| Confirms results | **24** | 4 |
| Keeps plans | 14 | 14 |
| Settles up | 10 | 12 |
| Sportsmanship | 5 | **16** |

**The decomposition earns its complexity, and here is the proof rather than the assertion.**
Take two candidates identical on four strands at 0.75:

| | confirms | sportsmanship | **comp** | **fun** |
|---|--:|--:|--:|--:|
| P | 0.95 | 0.55 | **0.788** | 0.726 |
| Q | 0.55 | 0.95 | 0.712 | **0.774** |

The two modes order them **oppositely**. A single blended score cannot express that, which is
§9.3.4's argument, now checkable: **the decomposition is justified for exactly as long as such a
pair exists.** If a later ruleset flattens the two vectors until none does, the decomposition
has stopped paying and should collapse to the published number.

There are **three** blends of the same six strands in this system, and confusing them is a live
risk: the published Player Score at `35/20/15/12/10/8`
([`the-five-numbers.md`](the-five-numbers.md) §4), and these two. The reliability *floor* reads
the published one — the one deliberate exception, recorded there.

**Settles up will stand down past the other five.** Court money is out of scope
([ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)), so when
`player_score` lands the strand vector renormalises within itself exactly as §10 renormalises
the terms.

- **Falsified by:** ghost rate and answer rate regressed on each strand **separately**. A strand
  that predicts nothing on its own is a strand whose weight belongs to its neighbours.

---

## 7. The modifiers

`intent_opposed` was deleted by [`the-five-numbers.md`](the-five-numbers.md) §6. Two more
changes here leave three.

| Modifier | Range | Status |
|---|--:|---|
| **Calibration value** | 0 … +4 | Competitive only. **The only modifier whose input exists today** |
| **Familiarity** | −4 … +5 | Needs `matches` (§8) |
| **Welcoming record** | 0 … +4 | **Settled by [#175](https://github.com/Raketa02/Raketa/issues/175):** one input — *has played opponents whose rating was still settling* — from the `rating` port. Needs `matches`. Printed |
| ~~Language~~ | ~~0 … +2~~ | **Struck** |
| ~~Intent opposition~~ | ~~−6~~ | Deleted in `the-five-numbers.md` §6 |
| Reliability floor breach | −11 | Outside the budget, derived as `MODIFIER_BUDGET + 1` |

**`MODIFIER_BUDGET = ±10`, a clamp on the summed stack** rather than a per-modifier cap. On day
one it is inert — calibration is the only modifier that can fire, so the stack's real range is
`0 … +4` and only in competitive — and that is correct for the same reason the evidence gate is:
standing insurance, in place before it is needed.

**`NEWCOMER_ABSORPTION_CAP` keeps its rule and refuses its integer.**
[ADR-0114](../../adr/0114-a-newcomer-may-not-be-declined.md) bounds how often one player is
volunteered into a **newcomer's** shortlist — counted per week per sport on the exposure ledger,
and binding by **dropping** the welcoming modifier and the newcomer reorder, never by withholding.
The number cannot be set here for [`the-five-numbers.md`](the-five-numbers.md)'s reason: with no
players there is no distribution to sit it in, and with `matches` absent the modifier it bounds
never fires, so on day one any integer is untestable. Its falsifier is written and its value is
not: **answer rate of the players who absorb the most newcomer appearances, regressed on
absorption.** If answer rate does not fall as absorption rises, the cap guards nothing.

**Language is struck rather than deferred.** It reads a field that exists nowhere in the backend
and that no ticket creates; and the privacy line excludes **nationality** from the index by name,
while a shared-language bonus is the nearest available proxy for it.
[ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s rule is
*a protected characteristic may gate; it may never score* — this scores. If it returns it returns
as its own decision under that rule, not as a leftover row in a table.

**Calibration value is binary, not a ramp.** Its input is `calibration_priority` on the rating
aggregate (`backend/app/engines/assessment.py:71`), which has two values — `standard` and
`elevated`. §9.4 describes a 0…+4 range; the input supports 0 or +4 and nothing between. It
applies only where a rating is at stake, so: competitive only, and it is **printed**, because a
player is entitled to know when they are being matched partly for somebody else's benefit.

- **Falsified by:** the fraction of shortlists where the stack clamp actually binds. If it never
  binds, the budget is not doing the work its existence claims; if it binds often, the modifiers
  are competing for a budget too small to hold them.

---

## 8. Familiarity

[#164](https://github.com/Raketa02/Raketa/issues/164) settled the sign — adopted, reading
**declared tags only**, the searcher's and never the candidate's, repetition winning a tie. Left
open there: the range, the decay, and how a signed modifier sits in the budget.

```
strength = 0.5 ^ (days_since_last / FAMILIARITY_HALF_LIFE_DAYS)
         × (1 − FAMILIARITY_DEPTH_PHI ⁿ)                       n = games played together

repetition-seeking:   +5 × strength
variety-seeking:      −4 × strength
neither declared:     −4 × FAMILIARITY_DEFAULT_LEAN × strength
```

| Constant | Value | Why |
|---|--:|---|
| `FAMILIARITY_HALF_LIFE_DAYS` | 90 | An eight-month-old single game sits at **15%** of full — §9.4's *"effectively fresh again"* without pretending it never happened |
| `FAMILIARITY_DEPTH_PHI` | 0.45 | Same value as `TAG_PHI`, a **separate constant with its own falsifier**. A coincidence of values must never become a shared constant |
| `FAMILIARITY_DEFAULT_LEAN` | 0.5 | §9.4's *"mildly novelty-preferring"* default, at most −2 |

**The arm is asymmetric on purpose, and it is §9.3.6 rule 3 again**: being wrong about a positive
costs a duller evening; being wrong about a negative buries a person. `−4 … +5`.

### The reading map

Product-owned ruleset data, a **second and separate map** from the relationship matrix
([#164](https://github.com/Raketa02/Raketa/issues/164)), exhaustive over the seven
`WHY_YOU_ARE_HERE` ids:

| Repetition | Variety | Neither |
|---|---|---|
| `HERE_FOR_A_REGULAR_GAME` | `HERE_TO_MEET_PLAYERS` | `HERE_TO_COMPETE` |
| | `HERE_TO_GET_BACK_INTO_IT` | `HERE_FOR_THE_EXERCISE` |
| | `HERE_TO_IMPROVE` | `OPEN_TO_MEET_SOMEONE` |

Two are in *neither* on purpose: `HERE_TO_COMPETE` wants good opposition and says nothing about
repetition; `HERE_FOR_THE_EXERCISE` says nothing about **who**. `OPEN_TO_MEET_SOMEONE` takes
neither, settled by #164. Repetition wins a tie; an all-*neither* reader falls to the default
lean.

**This is not a double-count against the tag terms**, which also read these ids. The tag does not
add points through familiarity — it **selects which direction familiarity points**. A selector is
not an addend, which is precisely the distinction #164's strike of §9.4's σ clause turned on: the
σ clause *added* value the calibration modifier had already paid for.

- **`FAMILIARITY_HALF_LIFE_DAYS` falsified by:** acceptance rate on repeat pairings by days since
  the last game. If it does not fall, familiarity is not decaying and the half-life is too long.
- **The reading map falsified by:** repeat-pairing acceptance rate, split by the searcher's
  reading. If repetition-seekers and variety-seekers accept repeats at the same rate, the map is
  reading a tag that does not predict anything, and the whole sign flip goes with it.

---

## 9. Liveness

`liveness_offset ∈ [−25, +25]`, never entering Fit, never shown as a number
(§9.5, §12.2). `MOVE_NOTICE = 6`: anything moved more than that prints its dominant reason.

### The contradiction, and the invariant that resolves it

§9.5 says anything moved more than `MOVE_NOTICE` prints its dominant reason. §9.5.1 says a
previous decline is *"never, under any circumstance, shown to either side"* — and gives it a dock
of **−10**. Both cannot hold.

> **A silent movement never exceeds the movement that owes an explanation:
> `|Σ silent| ≤ MOVE_NOTICE` — per player, not per signal.**

**The invariant as first written was `< MOVE_NOTICE` and bound each signal on its own.** Both
halves were wrong, and
[ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md) fixes them
together. Strict `<` was **stricter than the promise it enforces** — §9.5's threshold is *more
than* 6, so movement of exactly 6 owes no explanation — and it was red against the two silent
constants in the table below. And a bound on a **signal** cannot deliver a guarantee about a
**player**, who is moved by the sum: previous decline at −6 beside a negative exposure adjustment
is twelve points with nothing to print.

```
liveness_offset = Σ printable  +  clamp(Σ silent, −MOVE_NOTICE, +MOVE_NOTICE)
```

**The silent stack is budgeted, not the silent signal** — `MODIFIER_BUDGET`'s shape one stage
earlier. So **no signal weakens**: previous decline keeps −6 and exposure keeps ±6, and the
budget binds only when both fire hard on one candidate, where what it cuts is *silence* rather
than either signal. The bound is on the **signed net**, because the only thing a searcher can
observe is position and position is the net: a −6 decline beside a +6 exposure adjustment nets to
zero and there is nothing to explain.

**The printing promise then falls out of the arithmetic.** With `|Σ silent| ≤ MOVE_NOTICE`, any
player moved more than `MOVE_NOTICE` has `|Σ printable| > 0` — a printable signal *necessarily*
exists. Two clauses replace §9.5's one sentence: **notice** — over the threshold, at least one
liveness reason is emitted; **ranking** — *dominant* means the largest **printable** contributor.
A printed reason is true but not complete, and the unstated remainder is bounded at
`MOVE_NOTICE`, which is the movement the product already decided owes nothing.

**What is a type and what is a test.** The type enforces the *separation and the funnel* — a
signal is a closed union of `Printable(code, points)` and `Silent(points)`, and `Liveness` has one
constructor, taking the two lists and applying the clamp. The **arithmetic** is three
build-failing tests: the silent net within budget over every signal at every bound;
`|offset| > MOVE_NOTICE ⇒ reasons ≠ ∅`; and a **roster test** pinning the silent set to exactly
`{previous_decline, exposure_adjustment}` and its reachable net range. Today that range is
`[−12, +6]`, so the upper clamp is unreachable and the clamp only ever cuts a *bury* — true of
the roster, not of the rule, which is what the roster test is for. §12.2's two-numbers rule is the
neighbour that *is* genuinely type-enforced; this one had been borrowing its credibility.

| Signal | Bound | Printable |
|---|--:|---|
| They said *Let's play* to you | +14 | ✓ — and it must be ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)'s carve-out) |
| Previous accept between you | +6 | ✓ |
| Answer rate and speed | −6 … +6 | ✓ |
| Recent activity | −5 … +4 | ✓ |
| Overlap proximity | 0 … +4 | ✓ |
| **Current challenge load** | **−12 … 0** *(was −8 … 0)* | ✓ as a coarse code, **never the number** — their inbox depth is theirs |
| Reciprocal asymmetry | −12 … 0 | ✓ in *Why 78?*, not on the card |
| **Previous decline between you** | **−6** *(was −10)* | ✗ never, either side |
| **Newcomer lift** | **+8** *(reclaimed)* | ✓ — [#175](https://github.com/Raketa02/Raketa/issues/175) |
| **Exposure adjustment** | **−6 … +6** *(was −6 … +8)* | ✗ |
| ~~Radius asymmetry~~ | — | **Struck** — see below |

[#175](https://github.com/Raketa02/Raketa/issues/175) **argued it, and split the signal rather
than winning it whole.** §14.2's lift was one row here and two codes on the wire, with opposite
printability arguments: *they're new — this game does most of its work for them* is a sentence
the product wants said, while *you are seeing this person because nobody has been shown them all
week* is a third party's unpopularity, which the searcher is owed no version of. So the **newcomer
lift speaks and reclaims its +8**, honestly — the invariant binds *silent* movement — and the
**exposure adjustment stays silent at ±6**, where the budget holds it. Two signals, two bounds,
two printabilities, and neither is flattened by a cap. See
[`the-newcomer-path.md`](the-newcomer-path.md) §5. It leaves exactly **two** signals in the silent
set, which is what [ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)
budgets and what its roster test pins.

### Radius asymmetry was charged twice

§9.3.8 docks a searcher who is outside the candidate's ring by −8. §9.5.2 then computes
`fit_ba` — the candidate's Fit for the searcher — which **includes the candidate's own distance
term against the candidate's own radius**. That is the same fact, priced twice.

**The standalone dock goes**; reciprocal asymmetry keeps it, and prices it *proportionately*,
which a flat −8 does not. `outside_their_radius` still prints on the card, exactly as
[ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md) requires — the fact is
unchanged, only the second charge disappears.

### Reciprocal fit

```
fit_ba = Fit(candidate → searcher)
asym   = max(0, fit_ab − fit_ba − ASYM_TOLERANCE)          ASYM_TOLERANCE = 12
dock   = −min(12, asym × 0.5)
```

Computed over the **shortlist only** — after the quality floor, typically 20–40 rows — so it
costs almost nothing.

§9.5.2 says `fit_ba` runs *"under the candidate's declared intent as the mode"*. After
[ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md) a candidate may
have declared **`NO_PREFERENCE`**, which is not a mode — and there must never be a
`NO_PREFERENCE` weight vector, since `SearchMode` has two values and `PlayIntent` three by
design.

**A `NO_PREFERENCE` candidate's reverse fit runs under the searcher's mode.** They are
indifferent about the kind of evening, so the game being proposed is the game they would be
judging. This is [#164](https://github.com/Raketa02/Raketa/issues/164)'s deck rule generalised:
**`NO_PREFERENCE` never selects a weight vector; it inherits one.**

The reverse direction flips what the asymmetric terms measure — the availability denominator
becomes the candidate's slots, per the glossary's *"the denominator is your slots"*, and distance
runs against the candidate's radius.

### The challenge-load rungs, and the cliff that is not there

[#189](https://github.com/Raketa02/Raketa/issues/189) found §14.4's **third** rung had never been
ruled on: at eight open challenges the player was *withheld from generation for 24 h* — an
exclusion, so a gate, in no roster and no constant table.
[ADR-0125](../../adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md) **deletes it and
adopts §14.4's three thresholds whole**, changing only the third's effect:

```
open_challenges ≥ 3  →  −4          ≥ 5  →  −8          ≥ 8  →  −12
```

The bound moves from `−8 … 0` to **`−12 … 0`** because the sink now carries the job alone, and
`−12` is anchored twice rather than chosen: **strictly below the `+14` interest lift**, so a
player who said *Let's play* to you still surfaces at `+2` net however full their inbox is —
[ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)'s carve-out, now
load-bearing for a second reason, since **a human's own ask outranks the engine's opinion of that
human's popularity** — and **equal to reciprocal asymmetry's −12**, the other *this candidate is a
bad bet for you* signal. It stays printable as a coarse code, so ADR-0123's silent budget and its
roster test are untouched.

- **`CHALLENGE_LOAD` falsified by:** answer rate by open-challenge bucket. If answer rate does not
  fall as load rises, the signal is measuring nothing and all three rungs are noise. Owner
  `RobertConstantin02`.

- **`ASYM_TOLERANCE` falsified by:** decline rate by asymmetry bucket.
- **`MOVE_NOTICE` falsified by:** the fraction of shortlist rows printing a liveness reason. Near
  zero and it explains nothing; near one and the explanation is noise.
- **The interest constants** are settled by
  [#194](https://github.com/Raketa02/Raketa/issues/194) and **two of the three left this file**.
  `INTEREST_TTL = 21 d` and `PASS_SUPPRESS = 30 d` are five-numbers-shaped and live in
  [`the-five-numbers.md`](the-five-numbers.md) §8 and §9 — each moves what somebody is shown and
  nothing on any screen would say so. **`OUTSTANDING_INTEREST_CAP = 20` per sport stays here**,
  as an ordinary row: it decides whether a player may *act*, hides nobody, and
  [ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md) §4 made its
  bite visible the instant it lands. **Falsified by:** refusals at the cap **and the
  distribution of outstanding counts per player** — a refusal count alone cannot tell *20 is too
  low* from *somebody is saying yes to everybody*, and the second is the behaviour the cap
  exists to catch. Owner `RobertConstantin02`. The related `+14` interest lift is §9's and is
  **flat**: ADR-0127 refuses §9.5.1's taper, because `days_ago` already crosses as evidence.

---

## 10. `QUALITY_FLOOR` = 44

[`the-five-numbers.md`](the-five-numbers.md) defined the floor by six judged pairings and handed
the integer here. **The document's 52 is refuted**, and the case that refutes it is named.

With [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)'s gate and §5's
normalisation applied, on §2's day-one basis. **The table is generated** from
[`judged-pairings.json`](judged-pairings.json) by `make gen-judged-pairings`, and a hand edit
to it fails the build:

<!-- generated: judged-totals — `make gen-judged-pairings`; do not edit by hand -->
| Case | Verdict | Comp | Fun |
|---|---|--:|--:|
| 1 · same level, full grid overlap, five minutes away, socially blank | Shown | 82.0 | 67.5 |
| 2 · case 1 with the grid emptied — **no shared slot at all** | Shown | 69.3 | 49.9 |
| **3'-comp** · just inside competitive's gate, forecast at its floor, no slot, edge of the radius | **Not shown** | 19.5 | — |
| **3'-fun** · the same, just inside for-fun's gate | **Not shown** | — | 24.5 |
| 4 · everything exceptional, competitive searcher, friendly-only candidate | Shown, reason printed | 80.3 | — |
| 5 · **the median stranger** | Shown | 44.5 | 47.8 |
| 6 · case 1 with the candidate's radius shrunk — searcher outside theirs | Shown, docked | 82.0 | 67.5 |
<!-- /generated: judged-totals -->

<!-- generated: floor-bound — `make gen-judged-pairings`; do not edit by hand -->
```
24.5  <  QUALITY_FLOOR  ≤  44.5
```
<!-- /generated: floor-bound -->

**52 hides the median stranger in both modes**, and case 5's stated job is *"this is where the
bar sits"*. That is the refutation in the form `the-five-numbers.md` requires of any change: not
a number somebody dislikes, but the case that now decides differently.

**44 stands**, and the bound above is arithmetic rather than judgement — but the margin is **half
a point**, and the two points this section previously subtracted for *"the roundings in the
readings"* are **spent, not inherited**: the readings are now exact over pinned inputs and there
is nothing left to round.

Two things the table settles beyond the integer:

- **Case 3 is replaced by case 3′, and case 3′ is two pairings.** Case 3 is now excluded by the
  gate rather than by the floor. `ADR-0103` gates at `Δμ ≥ LEVEL_TOL_mode`, which is mode-relative,
  so *just inside the gate* describes a different person in each mode
  ([ADR-0122](../../adr/0122-a-judged-pairing-is-two-people-never-a-profile-of-scores.md)).
- **Case 6 is not binding only because the radius dock is Liveness.** It is now asserted as a
  literal identity — `Fit(6) == Fit(1)` — which is the only form in which a machine can assert
  that a fact moved nothing.

### The cases are a fixture, and this section's earlier numbers are struck

**The seven totals this section used to record — `78.4 / 61.5`, `72.9 / 52.6`, `20.4 / 24.2`,
`73.8`, `46.0 / 47.9`, *high* — do not reproduce, and are superseded rather than corrected.** The
working behind them was never written down, and reconstructing it found that no coherent reading
set produces them; that **case 4's `73.8` still carries the `intent_opposed` −6 that §7 records as
deleted**; and that this section's own sensitivity line read the **for-fun** row's cell for a
competitive misalignment.

The fixture is [`judged-pairings.json`](judged-pairings.json), argued in
[`the-judged-pairings.md`](the-judged-pairings.md) and ruled by
[ADR-0122](../../adr/0122-a-judged-pairing-is-two-people-never-a-profile-of-scores.md): **a judged
pairing is two people, never a profile of scores.** It holds *inputs* — μ, σ, grid cells,
distance, both radii, tag ids, intent, gender, block and hold state, commit date — and every term
value and every Fit is derived, so a formula change re-derives the whole fixture for free. That is
what [ADR-0120](../../adr/0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md) needed and did
not have.

**A change to a case reading still moves the floor and lands as an ADR**, exactly as a change to
the floor does. And case 4's verdict is now narrower than `the-five-numbers.md` states: *"shown,
**low**"* is unachievable at 80.3, and deleting `intent_opposed` is why.

- **Falsified by:** return rate of games from candidates just above the floor versus just below
  it. Requires the outcome half.

---

## 11. Which basis, and what happens when a term turns on

§10 renormalises **per comparison**, so a candidate's Fit changes when a term turns on
platform-wide even though nothing about the pairing changed. The floor is therefore read off
**the day-one live set**, and **turning a term on is a ruleset release that re-runs the six cases
and may move the floor.**

The floor's *meaning* is what stays stable — *clears the six judged pairings under the terms
currently live* — rather than its integer. The alternative, calibrating against the full
eight-term vector, sets today's bar for a future that has not arrived and lets every day-one
score drift against it silently.

This costs nothing extra: `the-five-numbers.md` already requires every change to land as an ADR
naming which of the cases it now decides differently. It adds one demand on
[#169](https://github.com/Raketa02/Raketa/issues/169), which already carries it: **which terms
produced evidence per scored candidate**, without which a Fit is uninterpretable a year later.

**And it is now mechanical rather than a sentence.** `make judged-pairings` re-runs the six
against the live ruleset and prints the bound the verdicts leave —

```
max(Fit | not shown)  <  QUALITY_FLOOR  ≤  min(Fit | shown)
```

— failing when the configured integer sits outside it, from either side. Turning a term on
moves every renormalised weight at once, so this is the release that finds out; the reader is
[`backend/scripts/judged_pairings.py`](../../../backend/scripts/judged_pairings.py) and it runs
in CI on every backend pull request.

---

## 12. What the search-side telemetry must record for these

In the shape [`the-five-numbers.md`](the-five-numbers.md) §7 uses, and additional to it. Every
fact is search-time and cannot be reconstructed afterwards.

| For | Record, per search |
|---|---|
| The level gate | How many candidates it excluded, and the **smallest Δμ among them** — the falsifier is the widest gap still admitted against the narrowest just refused |
| The weights | The ruleset version, on every search, per §11 |
| Tag terms | Raw score before normalisation, per scored candidate, and whether each column stood down. Distinguishes *a sparse matrix* from *incompatible people* |
| Liveness | The **raw signal values**, the dominant signal, and whether a reason printed. Separates *moved* from *moved and explained* — and the offset is deliberately **not** what is stored: it is a function of the ruleset's bounds, so recording it makes a Liveness-bounds change undiffable ([ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md) §8). `search_candidate.liveness_signals` carries the inputs; the offset is re-derived. **Whether the silent budget clamped is re-derived the same way** — a query over the stored inputs and the ruleset version, never a column ([ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)). The **Modifiers** row below records its clamp directly instead; #183's argument would collapse the two, and that is a telemetry question rather than this one |
| Reciprocal asymmetry | `fit_ba` and the mode it was scored under. `NO_PREFERENCE` inherits, so the mode is not recoverable from the candidate's declaration |
| Modifiers | Which fired, and whether the stack clamp bound |
| The deck's interest constants | **One row, and two departures.** `OUTSTANDING_INTEREST_CAP = 20` per sport is falsified by refusals at the cap plus the **distribution** of outstanding counts. `INTEREST_TTL` and `PASS_SUPPRESS` are five-numbers-shaped and carry their falsifiers in [`the-five-numbers.md`](the-five-numbers.md) §8–§9 — including the two that run **without** `matches`: yeses that expired having never lifted anybody, and pass rate on re-shown profiles. The last of those cost a storage change: a lapsed Redis suppression leaves no trace, so the pass **record** is durable ([ADR-0128](../../adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)) |
| The shape of the list | **Nothing new.** `SHORTLIST_MAX` and `DECK_DEAL_MAX` are falsified by `position` on `search_candidate` against interests and passes, both of which already carry the **Origin key**. A deck card is passed or it is said yes to — there is no third thing a player does with one — so the deepest position **acted on** is the depth reached, and the deal's falsifier runs off rows that exist for other reasons. It is stated here because the two constants were unnamed long enough to look like they owed a column |

---

## 13. Every constant, and what kills it

| Constant | Start | Falsified by |
|---|--:|---|
| Competitive weights | §2 | Return rate by match profile |
| For-fun weights | §2 | Same, split by mode |
| Tag-stuffing `X` | 0.30 | Return rate by shared-tag count against level gap |
| `LEVEL_TOL_COMP` | 0.55 | Return rate by level gap, split by band |
| `LEVEL_TOL_FUN` | 0.90 | Same. **Also the level gate** — acceptance at Δμ 0.75 → tolerance |
| `FUN_FREE_BAND` | 0.25 | Satisfaction inside vs outside the band |
| `BALANCE` coefficients | 145, 32 | Brier score against confirmed results |
| `BALANCE_PCT_MIN` / `MAX` | 35 / 96 | The observed live range |
| Strand weights | §6 | Ghost and answer rate regressed per strand |
| `TAG_PHI` | 0.45 | Return rate by shared-tag count |
| `TAG_COMPLEMENT_STRENGTH` | 0.70 | Return rate of complement-scored games vs match-scored |
| `CLASH_SEVERITY_REAL` / `MILD` | 0.15 / 0.06 | Return rate of games with a scored clash |
| `CLASH_CAP` | 0.25 | How often it binds; and the raw-score distribution |
| `MODIFIER_BUDGET` | ±10 | How often the stack clamp binds |
| `FAMILIARITY_HALF_LIFE_DAYS` | 90 | Acceptance on repeat pairings by days since last |
| `FAMILIARITY_DEPTH_PHI` | 0.45 | Acceptance by number of games together |
| `FAMILIARITY_DEFAULT_LEAN` | 0.5 | Acceptance on repeats for readers with no reading tag |
| The familiarity reading map | §8 | Repeat acceptance split by reading |
| `MOVE_NOTICE` | 6 | Fraction of rows printing a liveness reason. **It does two jobs**: it is also the silent stack's budget, deliberately one constant and not two, because two can drift apart in a ruleset edit and break the printing guarantee silently ([ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)). Its second falsifier is **how often the silent clamp binds** — never, and the per-player rule was theoretical; often, and previous decline and a negative exposure adjustment are routinely stacking |
| `ASYM_TOLERANCE` | 12 | Decline rate by asymmetry bucket |
| Liveness signal bounds | §9 | Acceptance rate per signal, held out |
| The intent table | §5.2 | Acceptance rate across the six cells. If the `0.35` cell accepts like the `0.85` one, the asymmetry between the two zeros is imagined |
| `DISTANCE_FULL_MARKS_WITHIN` / `ZERO_AT` | 0.70 / 1.15 | Acceptance rate by distance **as a fraction of the searcher's own radius**. Flat out to the ring ⇒ too steep; falling away well inside 70% ⇒ the shoulder is in the wrong place. Both are fractions and never kilometres, so a ten-kilometre searcher and a fifty-kilometre one are each read against what they said far means |
| `CONCERN_POINTS` | 5 | The fraction of shown candidates carrying no concern at all. If almost every card warns about something the line has stopped being a warning and become a caption. Anchored rather than picked: the lightest term on the day-one basis is social vibe's 4.6 competitive, so a lower bar would let a term warn about a shortfall it cannot produce even by reading zero |
| `QUALITY_FLOOR` | **44** | Return rate just above vs just below |
| `SHORTLIST_MAX` | 20 | Interest and challenge rate **by position**. Nothing past position 12 converting means 20 is decoration |
| `DECK_DEAL_MAX` | 10 | The **deepest position reached per deal**. Median deal exhausted ⇒ too small; p90 stopping before position four ⇒ the tail is scored for nobody |

**Diversity contributes no row, and this time the absence is the decision.** §24 carried
`Diversity λ | 8 | challenge rate on positions 2–5 with and without`, and this table's first draft
dropped it — the same failure named below, in the other direction. It is not restored:
[ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)
strikes the stage in both places, because a spread moves **position** by more than the movement
that owes an explanation ([ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md))
and there is no reason it could print. `λ`, the window, the four similarity weights and the deck's
raised `λ` are **deleted, not deferred**. Should a spread ever return, it arrives with a printable
reason or inside ADR-0123's one silent budget — and it earns its row then.

**Availability overlap contributes no row, and that is the answer rather than an omission.**
The term is `|shared| / |mine|` and has no constants at all
([ADR-0120](../../adr/0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md)); its **shape** is
three claims and each owes a falsifier, in
[`the-availability-term.md`](the-availability-term.md) §4. It is named here because a table
titled *every constant* is exactly where a term with none goes unnoticed — which is how §24 lost
it for as long as it did.

**None of them is measurable before §19.2's telemetry chain exists.** That is why the chain is
Phase 2 and not Phase 4, and why §12 above is a demand on the first search rather than on the
first outcome.
