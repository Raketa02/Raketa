# The engine, assembled

**The one entry point.** A build agent with no memory of the map starts here, reads the
precedence rule in §0, then walks the pipeline in §2–§11 and follows a link wherever it needs
the argument behind a decision.

Settles [#172](https://github.com/Raketa02/Raketa/issues/172), the terminal ticket on
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**This file decides almost nothing.** Every decision on this map lives in an ADR or in the spec
file that argued it, and a decision stated twice is a decision free to drift. What is here is
the **order** — which stage runs when, what each one reads, and who owns it — plus the handful of
places where assembling the set exposed a contradiction. Those are marked ⚠ in place and
catalogued in §18; two of them are **open decisions and are tickets**, not gaps this file may
close by picking.

The **three refusals** bind every line below, and a proposal that breaks one is refused rather
than weighed:

> The engine never sends a challenge on a player's behalf. It never returns a bad match to avoid
> returning nothing. It never produces a number it cannot explain in one sentence with the
> evidence named.

---

## 0. Precedence — which document wins

Five kinds of document describe this engine and they do not agree, deliberately. The previous
map on this repository learned the cost of leaving that implicit; state it once, plainly.

| Rank | Source | Binds |
| ---: | --- | --- |
| **1** | **`CONTEXT.md`** (root) | The **name** of a thing, and the invariants recorded under a context. A term means what the glossary says it means, everywhere, in both apps |
| **2** | **An ADR**, later number first | Any decision it states. An ADR is immutable; a later ADR that amends one **says so in its own text** and in the [ADR index](../../adr/README.md) |
| **3** | **The spec set** — this directory's hand-written files | Shapes, field lists, constants, arithmetic and falsifiers. A spec file may **not** overturn an ADR; where it appears to, the ADR is right and the spec file is stale |
| **4** | **This file** | Sequence and assembly only. Where it restates a rule and the owner disagrees, **the owner wins** |
| **5** | **`matchmaking-engine.md`** and **`social-prototype-v1.html`** | Input material. Binding **only** where nothing above has spoken |

**Rank 5 splits, and the split is the map's third reading rule.** The **document** wins on
algorithm — where it corrects the prototype's maths it was written to. The **prototype** wins on
surface: a screen behaviour the document never addresses **survives and gets specced**, rather
than being deleted by the document's silence. Both are byte-frozen and are never edited; every
correction is a row on [`README.md`](README.md)'s conflict table.

**Four consequences worth stating, because each is a mistake somebody will otherwise make:**

- **A rank-2 source may be stale in its details and still bind its decision.** ADR-0094's
  alignment table still prints `+ intent_opposed` in one cell;
  [`the-five-numbers.md`](the-five-numbers.md) §6 deleted that modifier. The **six cells** are
  ADR-0094's and stand; the modifier is gone. An ADR is immutable, so its corrections live
  outside it — follow the index line and the conflict table before implementing from an ADR's
  arithmetic.
- **Rank 3 outranks rank 5 even when the spec file is silent about the document.** The absence
  of a conflict row is not permission; it means nobody has looked yet.
- **A number is rank 3; a *shape* is rank 2.** A weight moves in a ruleset release. An evidence
  variant is the API contract ([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).
- **Where an input document overturns a rule, it does so by argument and it amends.** A document
  wins only on a case that its way produces **materially better matchmaking or more value for the
  player** — never on preference, never on having said it first — and winning **amends** the ADR
  in a record that says so. [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)
  is the only rebuttal so far, and it went the other way: the product overturned the *document*.

### Where each part is owned

| Part | Owner |
| --- | --- |
| Where the code lives, the two version stamps | [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) |
| The eight terms, weights, curves, modifiers, liveness bounds, the floor's integer | [`ranking-weights.md`](ranking-weights.md) |
| The five product numbers and their owner | [`the-five-numbers.md`](the-five-numbers.md) |
| The availability term | [`the-availability-term.md`](the-availability-term.md) |
| The tag matrix's thirty-seven rows | [`tag-relationship-matrix.md`](tag-relationship-matrix.md) |
| The quality floor's six judged cases | [`the-judged-pairings.md`](the-judged-pairings.md) · [`judged-pairings.json`](judged-pairings.json) |
| Doubles: gates over six pairs, the objective, arrangement | [`the-group-objective.md`](the-group-objective.md) |
| The newcomer path | [`the-newcomer-path.md`](the-newcomer-path.md) |
| Routes, envelope, candidate, errors | [`the-two-contracts.md`](the-two-contracts.md) |
| What each Play surface is owed | [`the-play-screens.md`](the-play-screens.md) |
| The candidate index, the tail reader, staleness | [`the-candidate-index.md`](the-candidate-index.md) |
| Every recorded fact | [`search-telemetry.md`](search-telemetry.md) |
| What the matcher demands of contexts that do not exist | [`consumer-driven-contracts.md`](consumer-driven-contracts.md) |
| Latency, memory, the triggers, `K` | [`scale-posture.md`](scale-posture.md) |
| Rulesets, the diff, the two corpora | [`the-replay-harness.md`](the-replay-harness.md) |

---

## 1. Where the code goes

[ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md). **No fourth
deployable, no second language.** §15 and §16 of the input document are discarded; §9 transfers.

```
backend/app/modules/matchmaking/     the stateful half — index, ledgers, telemetry, use cases
backend/app/engines/matchfit/        the pure scorer — ADR-0015's rules, unchanged
```

**Three boundaries, and only one of them is HTTP:**

| Boundary | Between | Carries |
| --- | --- | --- |
| Public | `frontend_player/` → backend | HTTP, `openapi.player.json`, generated types (ADR-0006) |
| Module | API layer → `modules/matchmaking/` | A use case. All the I/O |
| **Engine** | `modules/matchmaking/` → `engines/matchfit/` | A pure call. **The privacy fence** |

**The fence is the package boundary with no exceptions in it.** Gating and candidate generation
live in the *module*, where the I/O is. `matchfit` receives an already-gated, already-fenced set
and does scoring, modifiers, liveness, the floor, ranking, the group objective and arrangement.
Splitting gates by kind — *identity* outside, *arithmetic* inside — was rejected: a fence with a
judgement call in it is not a fence.

A `ScorableCandidate` has **no gender, no name, no photo, no birthdate, no precise location and
no `shard_key`**. Two build-failing assertions at `app/engines/matchfit/` say so, which is what
makes §7.2's sentence — *a term cannot read a protected characteristic because the value is not
in the process* — literally true rather than aspirational.

**Two version stamps ride on every result.** The **engine version** says how the maths works (a
directory that lives forever); the **ruleset version** says what the numbers were (a named,
dated, frozen dataset, immutable once released). Neither is ever selected by the environment —
`local`, `development`, `staging` and `production` run the same numbers
([ADR-0028](../../adr/0028-four-environment-model-and-typed-configuration.md)).

**Determinism is a set-iteration problem, and it is asserted rather than assumed**
([ADR-0105](../../adr/0105-determinism-is-a-set-iteration-problem-in-python.md)). A set is never
the source of an order; ties break on `(rank_key desc, fit desc, player_id asc)`; enforcement is
two subprocesses with different `PYTHONHASHSEED` values, and the seed is **never pinned**.

---

## 2. The pipeline

Eight stages. **Stages 1–6 are shared by every surface; only stage 7 differs** — which is the
whole reason there is one engine rather than three.

```
  SearchContext  ── bound once at entry, with one immutable index snapshot ──▶

  1  GATE          ten hard exclusions. no relaxation reaches one            §3
  2  GENERATE      sport ∧ box ∧ gates, over the partition                   §4
  3  FIT           eight terms, renormalised, evidence each   ── THE NUMBER  §5
  4  MODIFY        three modifiers, ±10 stack, each prints                   §6
  5  QUALITY FLOOR below it, not shown at all. minimum evidence beside it    §7
  6  LIVENESS      reorders. never enters Fit. never crosses as a number     §8
  7  TERMINAL      shortlist │ line-up → group objective → arrange │ deck    §10
  8  EXPLAIN       evidence codes, ranked by contribution                    §5.4
```

**Three structural changes the input document's own diagram does not show:**

- **Stage 5 no longer loops.** §9's `too few above it → relax one rung, GOTO 2` is struck. The
  strict answer returns, carrying **offers** ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md), §11).
- **Stage 1 runs twice for doubles.** A pairwise gate cannot be spent at generation, because
  eligibility for a *seat* is a property of a **combination**
  ([ADR-0116](../../adr/0116-in-a-four-every-gate-binds-all-six-pairs.md), §10.2).
- **The document's stage 7 is gone**, so its terminal and explain stages move up one
  ([ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md), §9).
  The document's own numbering already skips a stage — **there is no Stage 5 in it** — and this
  file does not inherit a second hole: the stages here are contiguous, and a citation of the
  document's *Stage 7* resolves at §9 below, where it is struck.

---

## 3. Stage 1 — the gates

**Ten.** Eight are §9.1's; the ninth and tenth were added by the map. No relaxation rung reaches
one, at any rung, ever.

| # | Gate | Reading | Fails | Day one |
| ---: | --- | --- | --- | --- |
| 1 | **Block, either direction** | live `BlockQuery`, never the index | **closed** | wired, `NoBlocks` — [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) |
| 2 | **Held account** | live `AccountHoldQuery`, **both ways** — a held searcher is refused at the entry point | **closed** | wired, `NoHoldsExist` |
| 3 | **No rating for that sport** | the index row | — | ✅ live |
| 4 | **Candidate outside the searcher's radius** | the searcher's own ask, so a filter | — | ✅ live |
| 5 | **An open challenge already exists between you** | live, from `MatchHistoryQuery` | **soft** — §7.5's re-verify is the backstop | ✅ **live** — `challenges` signs it ([#253](https://github.com/Raketa02/Raketa/issues/253)); still soft and still out of the read-back |
| 6 | **Missing or unapproved photo** | `PhotoReview` | — | ⚠ **live and inert** — ADR-0091's adapter passes everything through; [#181](https://github.com/Raketa02/Raketa/issues/181) |
| 7 | **Proposals opt-in explicitly `false`** | **gates the push, not the person** — reads `initiation`, never `surface` | — | ✅ live |
| 8 | **Account active** | live `AccountStatusQuery` against `users`, **candidate-side only** | **closed** | ✅ **live** — [ADR-0124](../../adr/0124-the-matcher-gates-account-state-never-age.md) |
| 9 | **Gender preference, mutually satisfied** | both directions; the value reaches gating and **never the scorer** | **closed** | ✅ live once [#182](https://github.com/Raketa02/Raketa/issues/182) lands — [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) |
| 10 | **Level** — `Δμ < LEVEL_TOL_mode` | **the same number the curve uses**, so gate and curve cannot drift | — | ✅ live — [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md) |

**A gate that cannot be evaluated excludes; a term that cannot be evaluated stands down.** The
test for a fact whose provider does not exist is whether a zero would be **measured** or
**invented**: nobody can be held because nothing can hold anybody, so gate 2 ships true-over-empty
and is a real absence. Gate 5 is the one exception and it fails **soft**, because the backend
re-verifies the returned rows anyway — it is embarrassment with a backstop, not a safety failure.

**Gate 10 tightens for newness.** While **either side** of a pairing is inside its newcomer
window, the level gate is evaluated at `LEVEL_TOL_COMP` **in both modes**. It binds the pairing
and not the search, because gating only the newcomer's own search leaves the bad first game
arriving through the veteran's list
([ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md)). No constant is
introduced.

**The empty availability grid is not a gate**, and it never was. It is required at profile
commit ([ADR-0102](../../adr/0102-silence-is-never-scored.md)); a grid that is blank anyway means
*we do not know*, and the **term stands down**.

**Row 8 held two rules, and neither was the one it looked like**
([ADR-0124](../../adr/0124-the-matcher-gates-account-state-never-age.md)). §9.1's *"below the age
or eligibility threshold — whatever that policy turns out to be"* is the only row that ever named
a policy instead of a provider.

- **The age half leaves this map.** Nothing in `backend/app` collects a date of birth and §7.2
  forbids the index to hold one, so the gate had no input — but ADR-0096 *permits* an age gate, so
  the privacy line is not what refuses it. What refuses it is that **there is no policy**: *may
  you hold an account* is not *may these two be shown to each other*. The platform is **adults
  only**, by an **attestation at sign-up — one boolean, never a date** — in `users`, filed outside
  the map as [#191](https://github.com/Raketa02/Raketa/issues/191). If minors are ever admitted, an under-18 pairing rule is **reopened**, not amended in.
- **The eligibility half was a live exclusion nobody had named.** `is_active` ships today and
  `auth` refuses a disabled account four ways — and §2 above tails `player_profile`, `rating` and
  `auth`, **never `users`**, so a disabled account keeps its index row and stays a candidate
  indefinitely. Gate 8 now reads it: a **fifth port**, resolved **once per search as a set**
  beside the block set, **candidate-side only** because `auth` closes the searcher side before
  the matcher is reached, failing **closed** like gates 1 and 2, and **told to nobody**. Never an
  index column — a stale *active* flag makes staleness cost **safety**, which is the one thing
  ADR-0111 exists to prevent. The word *eligibility* is struck rather than reassigned; a club or
  league rule would be its own named gate, and account **erasure** stays fog.

**The eleventh exclusion in the input document is not a gate.** §14.4 withheld a player from
generation for 24 h at eight open challenges. Its liveness half was already adopted (§8); the
withholding half is **deleted**, and §14.4's three thresholds are adopted whole with only the
third's *effect* changed — `≥3 → −4`, `≥5 → −8`, `≥8 → −12`
([ADR-0125](../../adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md)). The sink plus
the shortlist cap does everything the withholding did, except in a thin pool — where withholding
was wrong anyway, because **when there is nobody else, showing the busy person beats showing
nobody.**

---

## 4. Stage 2 — candidate generation

```
sport  ∧  bounding box of the searcher's radius  ∧  every gate in §3
```

**§9.2's `shard_key ==` conjunct is struck.** An equality inside the generation conjunction
**excludes**, and the document's own sentence is *a partition, never a matching criterion*. The
partition is therefore **derived** — `(sport)` today, `(sport, cell)` at trigger 4 — so there is
no field for a future conjunct to attach to, and a schema test asserts `shard_key` **absent**
beside §7.2's forbidden name, photo and precise location
([ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md)). **The box is the
only spatial truth.**

**What the search reads.** `CandidateSource.snapshot(partition)` returns one immutable container,
**bound once into the `SearchContext` at entry**, so a refresh mid-search cannot move the index
underneath it ([ADR-0112](../../adr/0112-the-snapshot-is-a-per-partition-container-bound-once.md)).
That is `atomic.Pointer` in Python, and it is the whole of §13's property.

**What travels beside it, because the index may not hold it.** The searcher's live block set,
their pairwise counterparts (bounded at **500**, most-recent-first), every open challenge, and
the ledger reads. The index row is per `(player, sport)` and has nowhere to put a fact about a
**pair** — and *the index holds only facts a player changes about themselves*
([ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)).
That invariant is what makes staleness cost **quality** and never **safety**.

**Guaranteed inclusions are down to one.** Only an **interest lift** — a human's own *Let's
play* — may admit a candidate below the floor, with its reason printed. The newcomer-window and
zero-exposure lifts **reorder** and never admit: exposure fairness is not a reason to show
somebody a bad evening (ADR-0099, amended by [#175](https://github.com/Raketa02/Raketa/issues/175)).

**The pure scorer never touches a database.** The *search* does — that is where §15.3's slogan
narrows to the sentence that was load-bearing.

---

## 5. Stage 3 — the eight terms of Fit

Every term returns `(value ∈ [0,1], Evidence)` or **`NoEvidence`**, in which case it is dropped
from the sum and the remaining weights **renormalise** (§10 of the input document). `NoEvidence`
is never `0` and never a neutral `0.5`.

### 5.1 The weights

Weights sum to 100 within a mode **before** renormalisation.

| # | Term | Comp | Fun | Formula owner |
| ---: | --- | ---: | ---: | --- |
| 1 | Level fit | **26** | 11 | [`ranking-weights.md`](ranking-weights.md) §3 |
| 2 | Predicted balance | 17 | 6 | §4 |
| 3 | Intent alignment | 14 | 14 | [ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md) |
| 4 | Reliability | 13 | 9 | §6 · [`consumer-driven-contracts.md`](consumer-driven-contracts.md) |
| 5 | Availability overlap | 11 | **16** | [`the-availability-term.md`](the-availability-term.md) |
| 6 | Playing style | 9 | 11 | §5 · [`tag-relationship-matrix.md`](tag-relationship-matrix.md) |
| 7 | Distance | 6 | 11 | §9.3.8, unamended |
| 8 | Social vibe | 4 | **22** | §5 · the matrix |

**Day one reliability stands down**, so the live basis is seven terms renormalised ×100/87
competitive and ×100/91 for fun. **Every judged reading, every floor bound and every cross
reading on this map is computed on that basis** — it is `judged-pairings.json`'s `basis` block,
and it is the number to reproduce:

| | level | balance | intent | avail | style | distance | vibe |
| --- | --: | --: | --: | --: | --: | --: | --: |
| **Competitive** | 29.885 | 19.540 | 16.092 | 12.644 | 10.345 | 6.897 | 4.598 |
| **For fun** | 12.088 | 6.593 | 15.385 | 17.582 | 12.088 | 12.088 | 24.176 |

**The inversion is the shape.** For fun, social vibe is the largest term in the match — larger
than level — because that is what *for fun* means.

### 5.2 The arithmetic

```
1  level      comp:  clamp(1 − Δμ / LEVEL_TOL_COMP, 0, 1)                LEVEL_TOL_COMP = 0.55
              fun:   clamp(1 − max(0, Δμ − FUN_FREE_BAND)
                                    / (LEVEL_TOL_FUN − FUN_FREE_BAND), 0, 1)
                                                                          FUN_FREE_BAND  = 0.25
                                                                          LEVEL_TOL_FUN  = 0.90
   The tolerance is absolute on μ. The term never calls band_for: the shipped bands are
   deliberately uneven and that asymmetry is about evidence, not about the game.
   Both tolerances ARE the level gate (§3 row 10). One number per mode, not two.

2  balance    σ_pair = combine_sigma(σ_a, σ_b)     ← racketskill/core.py:95, never re-derived
              pct    = clamp(100 − Δμ·145 − σ_pair·32, BALANCE_PCT_MIN, BALANCE_PCT_MAX)  35, 96
              value  = (pct − BALANCE_PCT_MIN) / (BALANCE_PCT_MAX − BALANCE_PCT_MIN)
   The clamp bounds are the term's zero and one, not cosmetics. It goes blind at Δμ ≈ 0.34
   for a typical σ_pair of 0.495 — which is what ADR-0103's gate exists to cover.

3  intent     table lookup: the searcher's live Mode against the candidate's declared
              Play intent. Six cells, ADR-0094. NO_PREFERENCE reads 0.85 in both modes;
              a directly opposite declaration reads 0.00 and takes no further modifier.

4  reliability  six strands read SEPARATELY, weighted per mode (ranking-weights §6), each
              strand standing down below ITS OWN min_observations — 5 for answers about
              results, 3 for the rest (ADR-0160) — the whole term standing down past
              RELIABILITY_HORIZON_DAYS = 365. Three of the six have a provider
              (ADR-0140, ADR-0160); the other three stand down for everybody and the
              survivors renormalise inside the term.

5  availability  |shared| / |mine|        ← the glossary verbatim. NO CONSTANTS AT ALL.
   |mine| is the SEARCHER's ticked cells. Either grid empty → NoEvidence, on both sides —
   the only thing between the term and a division by zero.
   §9.3.5's significance, staleness and proximity are ALL STRUCK: none reads the pair.

6/8 style, vibe   dr(n)  = 1 − TAG_PHI ⁿ                                  TAG_PHI = 0.45
              raw   = dr(matches) + strength·dr(complements) − Σ severity
              value = (raw + CLASH_CAP) / (1 + CLASH_CAP), clamped to [0,1]
   raw 0 → 0.20, the MEASURED zero: "different, not incompatible".
   A capped clash → 0.00. The term's zero is its worst outcome, never its most common one.
   The split is BY RELATIONSHIP, not by tag group — every matrix entry carries a column.
   A column stands down when EITHER side holds no tag in that column's domain.

7  distance   clamp( (1.15·r − km) / (0.45·r), 0, 1 )              r = searcher's radius
   Full marks inside 70% of the ring, zero at 115%. The hard cut at the ring is gate 4.
   The searcher being outside the CANDIDATE's ring is a Liveness dock and never a gate,
   and the standalone −8 is struck — fit_ba already prices it, proportionately.
```

### 5.3 Evidence — a closed, discriminated union

Every term's evidence crosses keyed by `kind`, and the union is enumerated in
`openapi.player.json`; the client generates an exhaustive type and a renderer per variant
([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).

| Term | `kind` and payload |
| --- | --- |
| Level fit | `{level_fit, their_mu, my_mu, delta, direction}` |
| Predicted balance | `{predicted_balance, pct, my_sigma, their_sigma, confidence}` |
| Intent alignment | `{intent_alignment, their_intent, my_mode, aligned}` |
| Reliability | `{reliability, score, strands, floor_breached}` — `strands` is the **six named** strands, closed (*confirms results* struck by ADR-0137 and removed by ADR-0140; *answers about results*, which counts answers and not agreements, added by ADR-0160) |
| Availability overlap | `{availability_overlap, shared_count, next_slot: {day, part}}` — `grid_stale` gone with staleness; `days_away` is **stored and never crossed** |
| Playing style | `{playing_style, matched, complementary, clashing}` |
| Social vibe | same shape, `{social_vibe, …}` |
| Distance | `{distance, km, area_code, outside_their_radius}` |

**Absence has two spellings and they generate as different types.** *Omitted* is *this does not
apply here*; *`null`* is *this applies and the answer is a measured nothing*. `at_stake` in a
for-fun search is **omitted**; `rung_offers: null` means the offers were not computed at all.

**An unknown `kind` is a named gap, never silence.** A card drops it — it shows three of eight
anyway — and *Why 78?* renders a gap saying this app is out of date. **A breakdown that quietly
stops adding up is the same class of lie as a recomputed score, and worse for being invisible.**

**Releasing a ruleset that adds, removes or reshapes a variant is an API change**: `make gen-api`
in the same commit, or `check-contract-drift.sh` goes red. Moving a weight is free.

### 5.4 Stage 8 — explaining

**The engine ranks the reasons by contribution; the client picks how many to show.** The ordering
is arithmetic and is not the client's. The full breakdown ships with the search rather than
behind a tap — *Why 78?* is the moment the product's central claim is tested, and a spinner there
is the claim failing.

`concerns[]` — the engine's own statement that a term is genuinely weak, keyed by `term`, ranked.
What counts as weak is a judgement about weights and curves and belongs where they live; a client
thresholding a value would be that judgement in TypeScript. **The cap is the client's**: a card
shows one, *Why 78?* shows all.

**A reason line never restates a value the card already renders** — §12 rule 3, narrowed. Stated
broadly it would delete `radiusPresentation.test.ts`'s deliberate figure-plus-words pattern;
stated narrowly it is testable ([`the-play-screens.md`](the-play-screens.md) §10).

---

## 6. Stage 4 — the modifiers

**Three survive.** `MODIFIER_BUDGET = ±10`, a clamp on the **summed stack** and not a per-modifier
cap.

| Modifier | Range | Prints | Day one |
| --- | ---: | --- | --- |
| **Calibration value** | 0 … +4 | ✓ | ✅ **the only one whose input exists** — binary, not a ramp: `calibration_priority` has two values. Competitive only |
| **Familiarity** | −4 … +5 | ✓ | needs `matches` |
| **Welcoming record** | 0 … +4 | ✓ | `NoEvidence` — one input, *has played opponents whose rating was still settling* |
| ~~Language~~ | ~~0 … +2~~ | — | **struck** — reads a field that exists nowhere, and is the nearest proxy for the nationality the privacy line excludes by name. *A protected characteristic may gate; it may never score* |
| ~~Intent opposition~~ | ~~−6~~ | — | **deleted** — the 0.00 term value already costs strictly more than silence, and a second charge is a gate wearing a modifier's clothes |
| **Reliability floor breach** | **−11** | ✓ | **outside the budget**, derived as `MODIFIER_BUDGET + 1` |

**Familiarity's sign is read from the searcher's own declared tags, never the candidate's**, over
a second and separate map from the relationship matrix, exhaustive over the seven
`WHY_YOU_ARE_HERE` ids. Repetition wins a tie; an all-*neither* reader falls to
`FAMILIARITY_DEFAULT_LEAN = 0.5`. **This is not a double-count against the tag terms** — the tag
does not add points through familiarity, it **selects which direction familiarity points**, and a
selector is not an addend.

**The reliability floor reads the published Player Score**, the number on the player's own
profile, and **not** the matcher's per-mode blend. That is the one deliberate place the matcher
reads the blend, recorded as an exception so it never later reads as an oversight: a penalty
justified by a figure that exists nowhere a human can look is unexplainable. The bar is **70**,
and it is a **dock, not an exclusion** — refusing to show a good match over one missed game is
the block's job.

**`NEWCOMER_ABSORPTION_CAP` keeps its rule and refuses its integer.** It bounds how often one
player is volunteered into a **newcomer's** shortlist, counted per week per sport on the exposure
ledger, and binds by **dropping** the welcoming modifier — the thumb that selects the experienced
players it is about — **never** by withholding, and **nobody is told**, because nothing has
happened to them. It does **not** reach the newcomer lift: that fires only for a candidate inside
the window, and capping it would take the subsidy from the people the cap exists to keep from
being leaned on ([ADR-0114](../../adr/0114-a-newcomer-may-not-be-declined.md), amended).

---

## 7. Stage 5 — the quality floor, and minimum evidence

**`QUALITY_FLOOR = 44.`** Below it a candidate is not shown at all.

The floor is **defined by the six judged cases it must satisfy**, not by an integer, and its
integer is read off them on the day-one basis. The bound is arithmetic:

```
24.5  <  QUALITY_FLOOR  ≤  44.5
```

**The margin is half a point**, and the two points an earlier draft subtracted for *"the
roundings in the readings"* are **spent, not inherited** — the readings are now exact over pinned
inputs. **The next term activation that moves case 5 for-fun downward moves the floor with it.**

**One floor, both modes, every sport.** Each extra dimension is another place the bar is lowered
quietly for whichever pool is thin. **Never relaxed**, at any rung. **The empty-result rate is a
guardrail metric, never a target**, is reported only paired with the return rate, and is never on
its own sufficient grounds to move the floor. Any change lands as an ADR naming **who moved it**
and **which of the six cases now decides differently**. Owner: `RobertConstantin02`.

**The floor is a bar over a score whose ingredients vary per comparison**, so a separate rule
carries the honesty: below a **minimum of evidence about that specific person**, they are not
shown — a **gate**, never a score adjustment, expressed as a **fraction** of the terms live for
the platform (**at least half**), counting gaps specific to that person and never platform-wide
absence. **Today it excludes nobody, and that is the point**: it is standing insurance, in place
before the day *we know nothing about this person* could quietly become a passing score.

**Its one exemption is the newcomer window** — and the window bends nothing else, not the floor,
not a gate, not a block. That exemption is why the window exists: the moment `player_score` and
`matches` land, the person with a person-specific gap is exactly the newcomer, and minimum
evidence would become a newcomer exclusion on the day it started working.

---

## 8. Stage 6 — Liveness

```
rank_key = fit + liveness_offset          liveness_offset ∈ [−25, +25]
```

**`rank_key` is never shown and never crosses the wire in any shape.** `fit` is what the card
prints. There is no field a Liveness offset could be written to (ADR-0106 §5) — a schema fact,
asserted centrally over every response type rather than per route.

| Signal | Bound | Prints |
| --- | ---: | --- |
| They said *Let's play* to you | **+14, flat** | ✓ — **and it must** |
| Newcomer lift | **+8** | ✓ |
| Previous accept between you | +6 | ✓ |
| Answer rate and speed | −6 … +6 | ✓ |
| Recent activity | −5 … +4 | ✓ — read as ***this week* … *dormant***, not *Active now*; it is projected from `auth` refresh-token events and resolves **days** |
| Overlap proximity | 0 … +4 | ✓ |
| Current challenge load | **−12 … 0** | ✓ **as a coarse code, never the number** — their inbox depth is theirs |
| Reciprocal asymmetry | −12 … 0 | ✓ in *Why 78?*, not on the card |
| **Previous decline between you** | **−6** | ✗ never, either side |
| **Exposure adjustment** | **−6 … +6** | ✗ |
| ~~Radius asymmetry~~ | — | **struck** — `fit_ba` already prices it |

**The coarse code the full inbox prints is `SOME` / `BUSY` / `FULL`**, one per rung, carried by
the rung rather than derived from its position — so moving a threshold cannot silently re-point a
code at a different depth. There is no fourth code for an empty inbox: a signal that does not fire
is absent from the list, which is a different statement from *we counted and it was low*.

**Only the full inbox reads a measurement; the ramped signals arrive as a reading in `[0, 1]` and
are priced linearly across their own bound.** The curve from *days since they last opened the app*
to a reading is a measurement and lives on the other side of the fence with the clock and the
ledgers; putting it inside the engine would mean inventing a threshold per signal — six or seven
constants nobody measured, in the one place whose whole discipline is that every number carries a
falsifier. The full inbox is the exception because its three thresholds **were** measured (§14.4)
and [ADR-0125](../../adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md) adopted them
whole. **Points are whole numbers**, because every bound in the roster is an integer and so is
`MOVE_NOTICE` — a fractional offset would make *moved more than six* depend on a rounding nobody
wrote down.

**`+14` is flat for the whole life of the yes and then absent — it does not taper.** §9.5.1's
decay over the final 7 days is refused by
[ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md): the age of the
yes **already crosses** as evidence (`days_ago`), so a decay charges one fact twice, once
visibly and once not, and prints the same sentence at day 2 and day 20 from two different
positions. Note what would *not* have caught it — a decaying lift is **printable**, so ADR-0123's
silent budget never sees it and the roster test below stays green.

**The printing rule, and the budget that makes it provable.** §9.5 says anything moved **more
than** `MOVE_NOTICE = 6` prints its dominant reason. That promise is about a **player**;
[`ranking-weights.md`](ranking-weights.md) §9 bound a **signal**, strictly, and was red against
the two silent constants shipping beside it. Settled by
[ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md):

```
liveness_offset = Σ printable  +  clamp(Σ silent, −MOVE_NOTICE, +MOVE_NOTICE)
```

**The silent stack is budgeted per player at `MOVE_NOTICE`, on the signed net** —
`MODIFIER_BUDGET`'s shape one stage earlier (§6). The inequality is `≤`, matching §9.5's own
*more than*, so **no signal weakens**: previous decline stays −6, exposure stays ±6. Only the net
is observable, so a −6 decline beside a +6 exposure adjustment nets to zero and there is nothing
to explain.

**The notice rule is then a consequence, not a rule to police.** If `|Σ silent| ≤ MOVE_NOTICE`
and `|liveness_offset| > MOVE_NOTICE`, then `|Σ printable| > 0` — a printable signal
**necessarily** exists. Two clauses replace one:

- **Notice.** `|liveness_offset| > MOVE_NOTICE` ⇒ at least one liveness reason is emitted.
- **Ranking.** *Dominant* is the largest **printable** contributor; liveness reasons join §5.4's
  ranked list. A printed reason is **true but not complete** — the card may name a −3 signal on a
  candidate moved −9 — and that is not §5.3's *breakdown that quietly stops adding up*, which is a
  rule about **Fit**, the thing that crosses as a number. Liveness crosses as reasons only, so
  there is nothing to add up; the unstated remainder is bounded at `MOVE_NOTICE` by construction.
  Silent signals are absent from the ranking and are **not** a client-renderable gap — §5.3's
  *named gap* is version skew, not deliberate silence.

**What the type asserts, and what a test asserts.** A liveness signal is a closed union of
`Printable(code, points)` and `Silent(points)`; `Liveness` has **one** constructor, it takes the
two lists, and it applies the clamp — there is no path to an offset that skipped it. The
arithmetic is three build-failing tests: the silent net stays within budget over every signal at
every bound; `|offset| > MOVE_NOTICE ⇒ reasons ≠ ∅`; and a **roster test** pinning the silent set
to exactly `{previous_decline, exposure_adjustment}` and its reachable net range. Today that
range is **`[−12, +6]`**, so the upper clamp is unreachable and the clamp only ever cuts a
*bury* — a property of the roster, not of the rule, which is what the roster test is for.

**The roster test is about this stage, and the guarantee is about the whole pipeline.** That gap
is what let §9.6's spread move a player 8 points, one stage later, with the test green
([ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)).
§17.3 now carries the wider property — *the silent roster is the whole of silent movement* — so a
future stage that moves a row without a reason arrives as a red test rather than as a green one
somewhere else.

**Reciprocal fit.** `fit_ba = Fit(candidate → searcher)`;
`asym = max(0, fit_ab − fit_ba − ASYM_TOLERANCE)` at `ASYM_TOLERANCE = 12`;
`dock = −min(12, asym × 0.5)`. Computed over the **shortlist only**, after the floor, so it costs
almost nothing. **A `NO_PREFERENCE` candidate's reverse fit runs under the searcher's mode** —
`NO_PREFERENCE` never selects a weight vector, it inherits one. The reverse direction flips what
the asymmetric terms measure: availability's denominator becomes the candidate's slots, and
distance runs against the candidate's radius.

---

## 9. The stage that is not there — diversity, struck

§9.6 placed a greedy maximal-marginal-relevance pass over the top of every list — λ = 8 over the
top 12, similarity `0.35·level_bucket + 0.25·distance_ring + 0.20·intent + 0.20·tag_jaccard` — and
§9.11 raised λ to 14 for the deck. **Both are struck**
([ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)).
It is the one stage no ticket on the map ever read.

**It moves no number, and that is why the rule it breaks is easy to miss.** `fit` is untouched;
*Why 78?* still adds up. What it moves is **position**, and the promise about position is §9.5's,
which [ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md) made
provable two tickets earlier: a silent movement never exceeds the movement that owes an
explanation. λ = 8 exceeds `MOVE_NOTICE = 6` — one stage after the roster test that asserts
nothing does, so **the test stays green and the guarantee is false**.

**It could not be given a reason.** *You are fourth because the three above you resemble each
other* is a fact about the **other rows**; ADR-0106's vocabulary is closed and every code in it is
a statement about the candidate. Three of its four similarity components — `level_bucket`,
`distance_ring`, `tag_jaccard` — are defined in no file on this map, so adopting it meant
inventing two binning schemes and a set similarity first, at roughly eight constants rather than
four. `tag_jaccard` is
[ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md)'s struck
construction reaching further than it ever did: two people who both ticked `OPEN_TO_MEET_SOMEONE`
are counted similar and one of them is pushed down. And at launch density it does nothing at all —
**63% of searches return under five candidates** — while its own falsifier needs the experiment the
runtime ruleset store was deferred for.

**The rule that replaces it, for the next spread that wants in:** *position moves on a fact about
the player, never on a fact about the list.* Name a printable reason, or enter the silent stack and
share ADR-0123's **one** budget at `MOVE_NOTICE` — one budget over all silent movement, never one
per stage.

**What still spreads a list, and is not this.** The **exposure adjustment** at ±6 is silent,
budgeted and candidate-side — fairness about who gets shown across many searches, not variety
inside one. `PASS_SUPPRESS` and the deck's three-band order do the deck's version. Neither becomes
a diversity pass by standing where one used to be.

The cost is named rather than hidden: at a density this product does not have, the top of a list
may be five similar profiles. It returns as its own argued record when there is a pool dense enough
for that to happen **and** `search_candidate` rows to prove it — held meanwhile as fog on the map,
*the list reads like a leaderboard*.

---

## 10. Stage 7 — the terminal stages

### 10.1 Shortlist

Ranked by `rank_key`, bounded and unpaginated at **`SHORTLIST_MAX = 20`**. There is no page two;
past the last row there are rung offers or an honest empty state.

**It does not bind at launch and cannot be wrong yet** — with `QUALITY_FLOOR = 44` and 63% of
searches under five candidates, it is a bound on a mature city's list. It is a ruleset constant
like any other and carries a falsifier it cannot yet run — **interest and challenge rate by
position**: if nothing past position 12 ever converts, 20 is decoration and the honest number is
smaller. It was unnamed for the same reason the stage above it was unexamined, and naming it is
most of what was owed.

### 10.2 Line-up — doubles

**A four contains six pairs, and the searcher is in three of them.** Every gate and every term in
this engine was decided while looking at a shortlist, where the searcher is one half of every pair
on the screen. That one sentence is what both doubles ADRs follow from.

**Admissibility (ADR-0116).** Block, gender preference and the level gate bind **all six pairs**,
inside enumeration, as one `K × K` bitmask — 276 pairs precomputed once per line-up, after which a
combination is admissible iff its three candidate-pairs are set. `O(K²)` against a cubic
enumeration. Newness carries with it: **every pair containing a newcomer takes `LEVEL_TOL_COMP`,
whoever ran the search.** The price is named: a four can be impossible where candidates are
plentiful, which is a partial line-up with a reason of its own.

**The objective (ADR-0117).** A term earns its place only by reading something **no seat's Fit
read**.

```
G = w_bal      · balance_norm(arrangement)
  + w_seatfit  · mean( post-modifier Fit of the unlocked non-viewer seats )
  + w_minfit   · min ( the same )
  + w_cross    · ( mean(cross reading over the three cross pairs) + seat_delta )
  + w_crossmin · min ( cross reading over the three cross pairs )
  + w_avail    · group_avail

hard rules   any seat below QUALITY_FLOOR disqualifies the combination
             any pair failing admissibility disqualifies the combination
             no group floor exists — G is only ever compared to another G
```

| | `w_bal` | `w_seatfit` | `w_minfit` | `w_cross` | `w_crossmin` | `w_avail` |
| --- | --: | --: | --: | --: | --: | --: |
| Comp | **34** | 20 | 16 | 8 | 6 | 16 |
| Fun | 16 | 17 | 13 | **20** | 14 | 20 |

A **cross reading** is Fit's own person-to-person sub-score over the three pairs containing no
searcher, renormalised on the day-one basis — `(intent + style + vibe) / 31.0` competitive,
`/ 51.7` for fun. **It invents no constant and inherits the inversion for free.** The **seat
delta** is what a pair's reading gains when it stops being unseated, added for the searcher's
partner pair only and **exactly zero** for the two opponent seats, because an unseated pair
already reads the `OPPONENT` row. **A seated reading never re-scores a Fit** — the card says 78 in
the shortlist and 78 in the builder.

`group_avail = significance₄ = |shared₄| / min over the four of |their declared slots|`. Three
good pairwise overlaps do not make a four that can meet. **No constant.** It is a **term, not a
gate**: an empty intersection zeroes it and carries `NO_SHARED_SLOTS`.

**Struck:** `partner_clash_penalty` (re-expressed as the signed seat delta), the 1.6 / 0.7 seat
multipliers (the matrix's `seats` scope already carries the asymmetry), `group_tag_coherence`
over raw tag ids, `group_intent_coherence` against the searcher, the superadditive bonus, and
**`G` for singles** — where it reduces to a non-order-preserving transform of Fit plus a
re-charged balance term, so `POST /lineups` and `POST /searches` could name different best
candidates for the same search. **The singles line-up is the top-ranked candidate by Fit.**

**Arrangement.** There are exactly three pairings of four people, and because the seat delta
varies by arrangement, the combination is chosen by **`argmax G` over all three** — `arrange()`
stops being a separate step. All three cross with a forecast each, so *Even it out* is a
**selection and never a calculation**. `is_best` means *best by `G`*; *Even it out* still selects
the min-gap arrangement, and `is_best ≠ is_evenest` is a new fact the builder can state.

**`G` is recorded and never returned as a number.** A second score the player must trust is worse
than none. One closed reason code names the term with the largest margin between the winner and
the runner-up: `EVENEST_ARRANGEMENT | STRONGEST_WEAKEST_SEAT | BEST_AVERAGE_FIT |
MOST_SHARED_SLOTS | GROUP_RAPPORT`.

**A seat may be unfilled and the line-up is still a `200`.** `NO_CANDIDATE_ABOVE_FLOOR`,
`NO_ADMISSIBLE_COMBINATION`, `POOL_EXHAUSTED`, `NO_SHARED_SLOTS`. ***Three of four* is not a
different shape from *nobody*** — there is no separate empty state for a line-up. **A seat is
never filled below the floor to complete a four**, a newcomer least of all.

`K = 24`, a ruleset constant with an **engine-side ceiling that refuses to load a ruleset
exceeding it** — cubic enumeration makes `K = 32` cost the whole line-up budget, so it is not
"just a config change" in Python. Above `K` eligible candidates, truncate to the top `K` by Fit.

### 10.3 The deck

**One deal, one `search_id`, an ordered batch of cards.** One-at-a-time is how the deck is
*shown*, not how it is computed: §9.11's ordering policy is a property of a whole deal.

**The deck has no `mode`** — a check constraint, not a convention — **and reads no declaration
either** ([ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §2, superseding the mapping this paragraph carried): every deal scores under
`fun`'s vector, `INTENT_ALIGNMENT` stands down for every pairing on this surface, and
`play_intent_not_declared` is never raised by it. `search` still records `intent_read` — the
declaration as it stood — so what a viewer had declared when dealt is not lost, and a later
change to this rule does not rewrite history.

**The relaxation ladder does not reach the deck.** Its own exclusions — passed within
`PASS_SUPPRESS`, already asked, already has an open game with you, and **in the deck's cool-off**
— are gates, and their numbers are set ([#194](https://github.com/Raketa02/Raketa/issues/194),
[ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §6): **`PASS_SUPPRESS = 30 days`, `INTEREST_TTL = 21 days`, `OUTSTANDING_INTEREST_CAP = 20`
per sport, `DECK_COOL_OFF = 30 days`** — the last a deck-only window after a shared challenge or
game is behind the pair, deliberately equal to the pass window and cleared with it.

**`PASS_SUPPRESS` is deck-only, one-directional, and never escalates**
([ADR-0128](../../adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)). It reaches no
other surface — a passed player is a full candidate in the shortlist, the line-up and a forecast,
immediately — it suppresses in the passer's deck and never in the other person's, and a second
pass on the same person buys the same 30 days and no more. §9.5.1's *repeated passes are a soft
signal respected quietly* is struck: it cannot print, it cannot enter ADR-0123's closed silent
roster, and where it leads is a **Block**, which exists and requires somebody to mean it. All
three boundaries are the opposite of ADR-0095's, because **a pass is a statement about my deck
and a block is a statement about a person**. The named cost: pass on somebody tonight, find them
third in your shortlist tomorrow.

**`INTEREST_TTL` expiry returns a person to the deck.** *Already asked* lapses with the yes, so
the same person may be dealt again 21 days later — a fresh chance rather than a loop, and part of
why 21 rather than 30 (
[`the-five-numbers.md`](the-five-numbers.md) §8).

**A deal is `DECK_DEAL_MAX = 10` cards, and the constant is a cap and never a target.** A deal is
scored once and its liveness ages as the player taps through, so a deal of forty is stale by the
bottom and writes forty candidate rows nobody looks at. Falsified by **the deepest position
reached per deal**: if the median deal is exhausted, it is too small; if p90 stops before position
four, the tail is scored for nobody.

**A spent deal deals again** — a new search, a new `search_id`, the same exclusions plus everybody
already dealt. Exhausting a *deal* is not exhausting the *pool*, and the two were one sentence
until this was asked: the honest empty state belongs to a fresh deal that came back with nothing,
never to a player who has seen ten of forty.

**The deck's ordering is its own and its variety is that order** — **two bands** since [ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §4:
the lifted (where the person who already said yes to you sits by rank key, unmarked, on their
`+14`), then the rest — plus `PASS_SUPPRESS`. §9.11's raised λ is struck with the
stage it belonged to (§9): a card at a time makes order the whole experience, which is the
stronger case for a spread and still not strong enough to buy a move nobody can be given a reason
for.

**A pass is write-only**, carries the Origin key, and **no route ever returns one**. **There is a
*Show them again*** ([ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §5): `POST /deck/reset` clears a sport's suppression, dealt memory and
cool-off in one act, `204`, and the durable record stays — the constant's falsifier now excludes
resets from its sample, which is the cost #231 named and the author accepted. **The exhausted
deck is still the honest empty state**, and it now says how many are left before it is reached:
`pool.remaining` on the envelope, and `pool.want_to_play_you` for the chip.

---

## 11. Relaxation — offered, never applied

**A rung may only relax something the searcher themselves asked for. It may never touch a
measurement, a term, a weight, or the quality floor.** §9.8's rungs 1, 3 and 4 are **struck**:
familiarity is a modifier, availability overlap and level fit are terms, so all three raised
scores against a fixed floor rather than widening the catchment — which is arithmetically
indistinguishable from lowering the bar.

| Rung | The ask | Mechanism |
| --- | --- | --- |
| **A** | **Your times** | single-slot additions to the searcher's own grid, carried as `availability_override` for that one search |
| **B** | **Your radius** × 1.5 | `radius_km_used` |
| **C** | **Your radius** × 2.0 | as above |

Times before distance: a slot you were already free in costs nothing; distance costs travel on
every game forever. **There is no third radius rung** — tripling still leaves 15% of searches
under five candidates at launch density, so past double it mostly spends the player's travel
budget on failing.

**Every rung clamps to `SEARCH_RADIUS_BOUNDS.maximum_km` (50).** A searcher already at 50 km gets
**no radius rung at all**; one at 40 km gets **one**, because a rung duplicating another rung's
radius is not offered twice. **There is no per-search radius input** — the searcher's ask *is*
their profile radius.

**Offered, not applied.** The strict answer returns carrying every available rung with its
**real** count — genuinely re-running generation and scoring per rung, ~3 ms each, because a count
on a screen that was estimated breaks the third refusal. `MIN_SHORTLIST = 5` decides **whether
the offers are computed at all**; it triggers nothing. **An accepted widen is a new search citing
the one that offered it**, scoped to that search, never a silent profile write — and afterwards
the app may offer to make it permanent, inline, bounded by the player's own slider.

**One climb per search screen.** A search that took a rung is offered none: the widening is the
searcher's own radius by the time a ladder would be priced, so a second rung would be priced off
the first and four taps from 8 km would land on the 50 km ceiling without the player being asked
once. *There is no third radius rung* is the same sentence said about multipliers, and this is
where it binds — **×2.0 of the radius the player saved is the furthest any accepted offer
reaches.** The climbed search answers an **empty** `rung_offers` rather than `null`, because `null`
already means *the list was long enough that nobody priced a rung*; `rung_taken` beside it on the
same row is what tells the two empties apart, and **no field was added for it**.

⚠ **Rung A can evict.** Adding a slot to the searcher's grid takes every candidate who does not
share it from `s/m` to `s/(m+1)`. At `|mine| = 3` one unhelpful slot costs **3.5 for-fun points**.
Nothing is hidden — the offered count is a real re-run — but relaxation that evicts is a real
shape and is recorded rather than discovered in production.

**Past the last rung the shortlist is empty and the pool is described**, structured, post-gate:
`{sport, radius_km_used, players_in_range, window, post_gate: true}`. **No pre-gate count is ever
carried**, because the ninth gate makes the two differ per searcher and the delta would tell a
searcher how many people a mutual gate hid from them.

---

## 12. The ledgers, and what is left of the sweeper

| Ledger | Where | Why | Fails |
| --- | --- | --- | --- |
| **Interest** | **durable**, in the module | the only thing here a human would miss — a person reached out to another person | — |
| **Pass** | **durable**, in the module | its constant's only falsifier is *pass rate on **re-shown** profiles*, and a Redis suppression that lapses leaves no trace that the pair was ever passed — so the falsifier the Origin key was bought for is uncomputable. The record is telemetry; the **live suppression stays the Redis TTL below**, derived from it | — |
| Suppression | Redis, TTL, derived from the pass record | a courtesy | **soft** |
| Exposure | Redis, TTL | losing a week of *who was shown to whom* costs nobody a fact | **soft** |
| Prompt | Redis, TTL | a standing question, left by a loop for the next search to pick up. Losing one costs a prompt nobody sees this week, and the loop raises it again on its next tick | **soft** |
| **Prompt decline** | **durable**, in the module | the two constants in `prompts.py` are falsified by *take-up rate on the prompt* and *acceptance rate on the offer*, and a decline is the only one of a prompt's three outcomes that nothing else records — the raise conditions are recomputable from the search store forever, and an accept writes a value. A suppression that lapses leaves no trace the player was ever asked. The record is telemetry; the **live suppression is derived from it** at the one place every prompt converges | — |
| **Deck reset** | **durable**, in the module | *Show them again* ([ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §5 and its amendment) is **one moment** per press, per player, per sport, and the next deal reads it three ways — against the pass record, the search record and the courts — so the route touches none of the stores it clears. Durable because two of the three are rows that do not fail soft, and a reset lost to a cache outage would re-hide the people a player just asked to see; append-only because `PASS_SUPPRESS`'s falsifier now excludes the re-shows a reset caused, and only the moments can say which | — |
| ~~Search results~~ | — | **deleted** — §8.3's `search:{id}` at a 30-minute TTL held the same Fit as §19.2's table, free to disagree, in the one place §8.3 calls disagreement fatal | — |
| ~~Standing searches~~ | — | out of scope; still fog on the map | — |

**Suppression fails soft and it is worth saying out loud**, because ADR-0095's rule reads like it
should not: applying *a gate that cannot be evaluated excludes* to suppression would **empty the
deck rather than protect anybody**. Suppression is a courtesy; a block is a safety control.

**Nothing here is event-sourced**, and interest is durable without being an aggregate with a life
story: it is a small fact with an expiry date. The same is true of a pass, with one difference:
**an interest expires, a pass record does not.** The 30-day *suppression* lapses; the row saying
the pass happened is kept, because [#194](https://github.com/Raketa02/Raketa/issues/194) found
that its constant's falsifier needs exactly the fact a TTL destroys. Suppression still fails
soft, and the split is why: the **gate** is the cache, the **evidence** is the row. **And the
gate can now be cleared without being touched**: a deck reset is a moment on a row, and the deal
subtracts from the cache what the pass record, read against that moment, says was cleared — the
keys lapse on their own.

**The split has a second instance, and it is the same argument about a question rather than a
person.** A prompt is a courtesy and its ledger is a cache; a **decline** is a player's answer,
and thirty days of silence bought by a Redis key is thirty days of evidence a TTL then destroys
([#237](https://github.com/Raketa02/Raketa/issues/237),
[ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md) as amended).
So the decline is a row, the suppression is derived from it, and neither of them **retires** the
standing prompt — `PromptLedger`'s *two methods and no delete* is untouched, because suppressing
stops the next **raise** and clears nothing. The read is one filter over every raised prompt,
after the commit and inside the courtesy, so it degrades the way the block around it already
degrades: **to no prompt**. That direction is forced — the two degraded outcomes are *ask
somebody who said no* and *stay quiet*, and staying quiet is what the rest of the block already
does.

**The sweeper's loops, after the map.** Loops are ADR-0092 `PeriodicJob`s.

| §14.5 loop | Now |
| --- | --- |
| Expiry | survives |
| Exposure roll | survives |
| **Newcomer window** | **struck** — the window is `now − profile_created_at < 14 d`, computed where it is read. A stored flag goes stale hourly; a date does not |
| Intent drift | survives — **raise a prompt, never change the value** |
| Outcome join | needs `matches` |
| Index health | survives, plus the **tail reader @ 1 s** and the **snapshot refresh @ 2 s** |

**The index is fed by tailing the ordered log, not by the outbox** — the outbox orders by
`(created_at, id)`, both non-orders ADR-0097 rejected by name, and mints a row id unrelated to the
event's, so an outbox subscriber can never name a `sequence_no`. Two subscriptions, two
guarantees ([ADR-0110](../../adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md)).
The projection applies the **contiguous prefix only** and steps over a hole once `xmin` proves it
permanent — because identity is assigned at `INSERT`, not at `COMMIT`, so a reader consuming to
`max(sequence_no)` records a watermark that is a lie about what it has seen.

---

## 13. The ruleset, restated

§11's structure predates every decision on this map. This is what a ruleset actually holds.

```
Ruleset
  version            "2026.09.08-a"      immutable once released; a new set is a new name
  modes
    competitive      { weights{8}, strand_weights{6}, level_tol, ... }
    for_fun          { weights{8}, strand_weights{6}, level_tol, fun_free_band, ... }
                     ── NO newcomer vector: ADR-0113 struck it for a gate ──
  tags               { phi, complement_strength, clash_severities, clash_cap,
                       relationship_matrix[37], familiarity_reading_map }
  balance            { coefficients(145, 32), pct_min, pct_max }
  reliability        { min_observations{6}, horizon_days, published_score_bar }
  modifiers          { budget, calibration, familiarity, welcoming,
                       newcomer_absorption_cap }
  liveness           { signal bounds, move_notice, asym_tolerance }
  group              { w_bal, w_seatfit, w_minfit, w_cross, w_crossmin, w_avail, K }
  floors             { quality_floor, min_shortlist, minimum_evidence_fraction }
  shape              { shortlist_max(20), deck_deal_max(10) }
  relaxation         { rungs A/B/C, multipliers 1.5/2.0 }
  telemetry          { near_miss_recorded }
  interest           { ttl_days(21), cap(20, per sport), pass_suppress_days(30) }
```

**Struck from §11's shape:** the `newcomer` mode, `w_intent` / `w_tag` (ADR-0117 replaced them),
`max_rung`, the ordered-rung list, `score_min` — a key nothing in the design ever defines — and
**`diversity` entire**, whose stage is struck (§9,
[ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)).
`shape` is the two constants that decide how long each surface's answer is, and they are here
rather than under `floors` because a floor decides whether somebody is shown at all and these
decide only where the list stops.

**Validated on load**, and a malformed ruleset **refuses to load while the previous one keeps
serving**; it never falls back to defaults, because a matcher that silently falls back is one
that quietly A/B tests against itself. Two validations the map added: **`K` may not exceed its
engine-side ceiling**, and **every evidence `kind` the ruleset can emit must be present in the
wire union**.

**It ships embedded with the code**, so a release is a deploy. The runtime store is deferred until
there is enough traffic for an experiment to mean anything, and its arrival changes only where the
file is read from, never what the stamp guarantees.

**Shipping a ruleset:** offline diff → deploy → watch the search-side rates that already exist.
§22's shadow → canary → full collapses to that. **Canary's stated obstacle is recorded as
wrong** — hash assignment needs no routing surface — and it is deferred on its real one: its
metric is acceptance, which needs `matches`. **Shadow** is armed by the first shape-class change
whose synthetic corpus its owner will not sign. The gate is `check-ruleset-diff.sh`, regenerated
under a different `PYTHONHASHSEED` so it doubles as a whole-pipeline determinism assertion, and
**half of it is a signature rather than a machine**, said out loud.

**A past search is explainable forever and is not reproducible.** Three of a search's four inputs
are outside the index on purpose. The harness re-weights recorded term **values** over a recorded
corpus, beside a synthetic corpus that decides whether the recorded one may be believed. The
release kind — **weight-only** or **shape-class** — is **derived, never declared**.

---

## 14. The contracts

Nine routes. [`the-two-contracts.md`](the-two-contracts.md) holds the shapes.

| Route | Creates a search | Notes |
| --- | --- | --- |
| `POST /api/v1/searches` | ✓ | **deliberately not idempotent** — two taps are two searches, and §19's denominator is *searches run* |
| `POST /api/v1/lineups` | ✓ | `LINEUP` / `FILL_SEATS`, differing only by `locked_seats` |
| `POST /api/v1/deck` | ✓ | `sport`, and the week this one deal runs on — no mode, no rung |
| `GET /api/v1/searches/{id}` | — | the **same schema** the `POST` returned |
| `POST /api/v1/interest` | — | idempotent per `(from, to, sport)`; `search_id` required |
| `POST /api/v1/forecasts` | **no — deliberately** | re-`POST`ing a line-up per swap would enter a six-edit builder session into the denominator as six searches |
| `POST /api/v1/passes` | — | write-only |
| `POST /api/v1/prompt-declines` | — | write-only, **no Origin key** — the pass's was bought for a named falsifier and nothing here needs one, and two of the three questions it answers are raised by a loop with no search to cite ([#237](https://github.com/Raketa02/Raketa/issues/237)) |
| `GET /api/v1/interest` | — | **outgoing and mutuals only** |

**The client sends what it is asking for and never a fact about the searcher.** The backend reads
the profile, grid, radius, tags, rating, intent and gender preference itself, at request time —
a stale radius supplied by a client is a gate evaluated on a lie.

**Three field families have a different author from the rest of the candidate**, and all three
ride the same seam, attached by the **backend after `matchfit` returns**: `player_card`
(ADR-0107), `at_stake` (`AtStakeQuery` over `rating` — ADR-0021 forbids the client computing it
and ADR-0098 forbids the matcher re-deriving it), and `distance_km`.

**`GET /searches/{id}` re-verifies the fail-closed gates and states what it withholds.** The
record stays immutable; the gate is live. A withheld row is **stated, never vanished** — a list
that quietly gets shorter is the same class of lie as a breakdown that quietly stops adding up —
and it **names no gate**
([ADR-0130](../../adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)): a block, a
hold, an account state and the mutual gender preference reach the wire as one indistinguishable
statement, on a separate row shape that carries no id and no card.
The round-trip test asserts **the recorded answer plus live gate state, over the record's
fields** — never a byte-identical payload, since the photo URL is re-minted per response by
design. Written down because a test drafted naively will fail on a row that is *supposed* to
differ, and the temptation will be to loosen it.

**Errors are structured codes on the backend's existing envelope**, distinct at one status,
because a client must tell a transient outage from a refusal about *you*:
`matchmaking_unavailable`, `gate_data_unavailable`, `index_too_stale`, `search_not_recorded`
(503); `sport_not_rated`, `play_intent_not_declared` (409); `account_held` (403). **An empty
shortlist is a `200`.** **Never a fallback list** — when the engine is down the feature is down; a
hand-rolled backend ranker arriving as a hotfix is how a second, worse, unexplainable ranking
implementation enters the system permanently.

---

## 15. The telemetry

**Written in the request's own transaction, committed before the response returns. If it fails,
the search fails** — the `search_id` *is* the answer's identity. **Every fact is search-time and
cannot be reconstructed afterwards; there is no backfill.**

Three layers, plus a fourth for line-ups: **counters** on the `search` row, the **returned** rows
in full (≤ 20), a **near-miss band** of the best `NEAR_MISS_RECORDED = 10` that did not clear, and
for a line-up the **winning combination and the runner-up** — two rows, not 2 024, which is
exactly what the deciding margin is computed from.

**Layer 3 and layer 4 are engine-internal and no route ever returns them, to anyone.** *A player
may ask why somebody was shown; nobody may ask who was withheld.*

**The record is durable and unexpiring**, one store rather than two, and **erasure is the only
path that ever deletes a row** — which is what makes `n_returned` a redaction detector rather than
a redundant column. The **Origin key** is two columns on the record that expresses interest, never
a third table; an interest citing an unknown or foreign `search_id` is **refused, never linked as
null**, because a silently-dropped link is a denominator that lies.

**Two columns exist because a strike must stay reversible.** `their_slot_count` and `days_away`
are recorded and **read by nothing** — ADR-0120 struck their consumers. *A strike that is not
recorded becomes irreversible by accident*, and `liveness_signals` stores the **raw inputs** and
never the offset for the same reason: the offset is a function of the ruleset's bounds, so storing
it makes a Liveness-bounds change undiffable.

---

## 16. What is live on day one

| | Status | Waiting on |
| --- | --- | --- |
| Level fit · predicted balance · availability · style · vibe | ✅ **live** | — |
| Distance | ✅ live | area centroid resolution |
| **Intent alignment** | ✅ live | [#182](https://github.com/Raketa02/Raketa/issues/182) — one aggregate, one event |
| Reliability | **stands down** | `player_score` |
| At stake | ✅ **live** | — the rule ships ([ADR-0139](../../adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)); omitted only for an unrated pair |
| Familiarity | ✅ **live** | — `games` ships ([ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md)) |
| Welcoming record | `NoEvidence` | the welcoming modifier |
| Blocks · holds | **wired, true-over-empty** | `blocks`, `cases` |
| **Gate 8 — account active** | ✅ **live** | — the only outward port whose provider ships ([ADR-0124](../../adr/0124-the-matcher-gates-account-state-never-age.md)) |
| **Challenge load, all three rungs** | **wired, never binds** | `matches` — and it now *sinks* at `−12` rather than withholding ([ADR-0125](../../adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md)) |
| Minimum evidence | **live and inert** | — it excludes nobody today, on purpose |
| `NEWCOMER_ABSORPTION_CAP` | **wired, never binds** | — the tally is counted from searches and read on every newcomer's; what is missing is the **integer**, which stays refused until there are weeks of it to choose against |
| Newcomer window and its `+8` | ✅ **live** | — |
| The photo gate | ⚠ **live and inert** | [#181](https://github.com/Raketa02/Raketa/issues/181) |
| Availability grid required | ⚠ | [#176](https://github.com/Raketa02/Raketa/issues/176)–[#178](https://github.com/Raketa02/Raketa/issues/178) |
| Gender and gender preference | ⚠ | [#182](https://github.com/Raketa02/Raketa/issues/182) — four event contracts |

**Everything ships wired.** Nothing stands in for an absent provider, because *a gate may be
honestly empty; a term may never be honestly neutral* — and every proxy available for the
welcoming record is an input the engine has **already counted**.

**Seven terms live, renormalised, is not a degraded engine**: it is 29.9 / 19.5 / 16.1 / 12.6 /
10.3 / 6.9 / 4.6 competitive, close to the prototype's shipped weights and demonstrably good
enough. **The engine degrades to something sensible rather than to something broken.**

---

## 17. The acceptance suite

Two artifacts, one idiom, and **they must not be merged**: the judged pairings ask *does this
ruleset still show the six things we said it must* — pass/fail against named verdicts — while the
replay harness asks *how this ruleset moves the population* and has no floor in it.

### 17.1 The three walkthroughs, as golden files

§20.1's walkthroughs are the acceptance suite, not illustrations. Each is **a fixed population, a
fixed clock, a fixed ruleset and the complete expected response**. **A diff is a design change and
must be argued for in the pull request** — which is precisely the point, because it makes weight
changes visible instead of quiet.

| | Asserts |
| --- | --- |
| **A — competitive singles** | a *Let's play* candidate **lifted to the top with the reason printed and `fit` unchanged by the lift**; a held account **absent**; a reliability-floor breach printed and the candidate still **shown, low**; a strong asymmetric candidate **docked** rather than gated |
| **B — for fun, building a four** | the weights invert; **the group objective beats the top three individuals**; an opposed-intent candidate scores `0.00` on intent, takes **no** further modifier, and their `PLAYS_TO_WIN` tag moves the **playing-style term and nothing else** — asserted explicitly, because §6.5's trap is that a tag leaks into intent |
| **C — a newcomer's first search** | evenness and reliability carry; the forecast is labelled **provisional**; the tightened level gate binds **both** sides of the pairing; the newcomer lift prints |

**Three corrections the map forces on §20.1, and each would otherwise be written wrong:**

- **Walkthrough C's players cannot be scored on a third weight vector.** ADR-0113 struck it. C
  runs the ordinary vectors with the gate at `LEVEL_TOL_COMP`.
- **B's opposed-intent candidate takes no `intent_opposed` modifier**; it was deleted. Asserting
  the old total is asserting a deleted modifier.
- **A's expected `at_stake` block is omitted, not zero** — the walkthrough's players hold no
  ratings for the rule to price, and an unrated pair is an absence rather than a pair of zeros.

### 17.2 The six judged pairings

[`judged-pairings.json`](judged-pairings.json), read by
[#187](https://github.com/Raketa02/Raketa/issues/187). It holds **inputs** — μ, σ, grid cells,
distance, both radii, tag ids, intent, gender, block and hold state, commit date — and **derives**
every term value and every Fit, so a formula change re-derives the whole fixture for free rather
than stranding it. **A judged pairing is two people, never a profile of scores.**

Its release-time job: **re-derive the floor bound and fail if `QUALITY_FLOOR` leaves it.** The
margin is half a point.

### 17.3 The property tests

| Property | Why it is the one worth having |
| --- | --- |
| Same input + same snapshot + same ruleset ⇒ **byte-identical** output, **across two subprocesses with different `PYTHONHASHSEED`** | a set of ids reorders *between* processes and never *within* one: every test green, two workers disagreeing |
| **Liveness never changes the printed Fit** — permute every signal, assert every `fit` unchanged | the one number a player is asked to trust |
| **No gated player appears**, under any rung — and in a four, **in any of the six pairs** | ADR-0116's gate is otherwise indistinguishable from a thin pool |
| **Renormalised weights sum correctly for every subset of live terms** | §10 is the property that lets this ship at all |
| **Provisional == arranged** the moment the last seat is filled | one implementation produces both figures |
| **Modifier totals stay inside the budget**, for every generated combination | |
| **The silent roster is the whole of silent movement** — position is a function of `fit`, the printable liveness signals and the clamped silent net, and of **nothing else** | ADR-0123's roster test is a test about stage 6; the stage that broke its guarantee ran one stage later and left it green ([ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)) |
| **`Fit(case 6) == Fit(case 1)` identically** | the only form in which a machine can assert that a named fact moved **nothing** |
| **`arrange()` returns `argmax G`**, brute-forced over all three | not the min-gap pairing — that is *Even it out*, a different word |
| **Rebuild-equals-tail**: tail a fixture incrementally, rebuild it from zero, require the tables identical | proves the projection is a pure function of the log. **Never a wall-clock bound** — that is a flaky test that gets muted |
| **No forbidden fact in any response type**, asserted **centrally** | a test per route passes forever and then somebody adds a route |

**Relaxation monotonicity is struck as written.** §20.2 asserts *rung n+1's candidate set is a
superset of rung n's* — true of the radius rungs and **false of rung A**, which adds a slot to the
searcher's own grid and can lower a candidate's score (§11). The property that survives is the one
about the rungs that widen: **B ⊆ C, and both ⊇ the strict set.**

---

## 18. What is still open

**Nothing this file may close by picking.** Every decision the map owed the engine is made; the
section that held the last one is §9, and what stands there is a strike. The ⚠ marks that remain
are **dependencies, not questions** — the photo gate live and inert behind
[#181](https://github.com/Raketa02/Raketa/issues/181), the grid and the gender contracts behind
[#176](https://github.com/Raketa02/Raketa/issues/176)–[#182](https://github.com/Raketa02/Raketa/issues/182),
rung A's eviction shape recorded rather than open. **The deck's three interest constants are no
longer among them** — see below.

**Two are closed.** [#189](https://github.com/Raketa02/Raketa/issues/189)'s two exclusions are
settled by [ADR-0124](../../adr/0124-the-matcher-gates-account-state-never-age.md) — §9.1's row 8
held two rules, the age half leaves for `users` as an attestation and the eligibility half becomes
**gate 8, Account active**, live on day one — and by
[ADR-0125](../../adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md) — §14.4's
withholding is **deleted**, its three thresholds adopted whole at `−4 / −8 / −12`, anchored below
the `+14` interest lift. §3 and §8 above carry them.

**And** [#188](https://github.com/Raketa02/Raketa/issues/188)'s silent-movement
invariant is settled by
[ADR-0123](../../adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md) — `≤`, the
budget is per **player** on the signed silent net, no signal weakens, and §9.5's printing promise
becomes a consequence of the clamp rather than a rule to police. §8 above carries it.

**And** [#190](https://github.com/Raketa02/Raketa/issues/190)'s stage is settled by
[ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md) —
**stage 7 is struck in both places**, the pipeline is eight stages, and *position moves on a fact
about the player, never on a fact about the list*. Its two neighbours outlive it as ordinary
constants: `SHORTLIST_MAX = 20` (§10.1) and `DECK_DEAL_MAX = 10` with a spent deal dealing again
(§10.3). §2, §8, §9, §10.1, §10.3 and §17.3 above carry them.

**And** [#194](https://github.com/Raketa02/Raketa/issues/194)'s three deck numbers are set —
`INTEREST_TTL = 21 d` flat, `OUTSTANDING_INTEREST_CAP = 20` per sport and refusing, and
`PASS_SUPPRESS = 30 d` deck-only — by
[ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md) and
[ADR-0128](../../adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md). **This closes
the last ⚠ in §13's ruleset**, and it moved one thing that was not a number: the pass ledger
becomes durable (§12), because the falsifier the Origin key was bought for cannot be computed
from a suppression that has lapsed. §8, §10.3, §12 and §13 above carry them.

**And what is deliberately deferred rather than open** — see the map's *Not yet specified*: the
runtime ruleset store, the density hypothesis, standing search, the operational surface these six reports have nowhere to be read on, and the fact that
**nothing in this repository can push anything**, so two people who both said yes find out by
opening the app.
