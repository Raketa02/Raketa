# ADR-0121 — A fixture stands for a comparison, never for a city

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[ADR-0118](0118-a-past-search-is-not-reproducible.md) makes the synthetic corpus load-bearing in
three separate places — the validity test that decides whether the recorded corpus may be
believed, the only answer to a shape-class release, and the committed CI artifact that doubles as
a whole-pipeline determinism assertion — and names the hazard in its own consequences:

> A population that drifts away from the city it stands for will keep producing confident diffs
> about nobody. It needs a stated construction and a review whenever the density hypothesis moves.

[#185](https://github.com/Raketa02/Raketa/issues/185) was charted to supply that construction, and
asked *what population does the corpus stand for, and what makes it stop standing for the city*.

**The framing carried the error.** The corpus cannot resemble the city, because there is no city:
the market is eleven players ([#162](https://github.com/Raketa02/Raketa/issues/162)), the density
hypothesis is fog, and [#161](https://github.com/Raketa02/Raketa/issues/161) measured only that
twenty clustered players behave like eighty scattered ones. Any richer shape the generator adopts
— a level pyramid, a correlation between intent and tags, a realistic block rate — is **invented**,
and it is exactly the invented facts that would decide the rates. They would then appear in the
diff wearing the clothes of evidence, which is ADR-0118's hazard arriving through the door built
to prevent it.

**And resemblance was never the property the harness needed.** Every number it prints is
*comparative* — baseline ruleset against candidate ruleset over the **same** population — and
ADR-0118 §5 already forbids it to carry a materiality threshold, so it never makes an absolute
claim about anything. A neutral population orders two rulesets correctly. It simply cannot tell
you what the empty-result rate *is*, which the harness was not entitled to say.

That reframes the second half of the question too. *When does it stop resembling the city* has no
evaluable answer while the city is unbuilt. *When is one of its stated parameters contradicted by
what we have recorded* is answerable from the first search ever made, because
[ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) keeps `n_generated`,
`excluded_by_gate`, `n_scored` and `n_cleared_floor` forever.

### Ruled out

- **A best-guess realistic city.** Its authority is borrowed from measurements nobody took, and
  the review trigger it implies — *does this still look like the city* — cannot be evaluated
  against a city that does not exist. It is the `QUALITY_FLOOR = 52` mistake
  ([#167](https://github.com/Raketa02/Raketa/issues/167)) in a fixture: a number that cannot be
  calibrated, which later reads as a decision.
- **A purely adversarial population**, built so every branch fires. It maximises coverage and
  destroys the rates — a corpus that is all edge cases reports a composition-changed figure no
  market would produce. Kept below as a **tail**, never as the body.
- **One population.** Launch density and coverage density are different numbers, and the newcomer
  mix proves one fixture cannot be both: at launch every player is inside
  [ADR-0113](0113-newness-changes-the-gate-never-the-weights.md)'s fourteen days, so a truthful
  launch corpus can never exercise `LEVEL_TOL_FUN` at all.
- **A committed generator with no committed population.** ADR-0119 §4's regeneration under a
  different `PYTHONHASHSEED` then asserts the *pipeline* is deterministic and never the
  *generator* — and the generator is precisely where
  [ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md)'s set-iteration hazard
  hides, since a set of generated ids is ordered without anybody noticing. A generator edit would
  also change the city silently under every past diff.
- **ADR-0118's density-hypothesis review as the only staleness rule.** The hypothesis is fog and
  may not resolve for a year. As the sole trigger it may never fire. It survives below as a
  floor.

## Decision

**We will build a corpus that stands for a comparison rather than for a city, at two densities,
and that goes stale by contradiction rather than by resemblance.**

### 1. Neutral by default; every departure argued and named

Uniform draws wherever the repository supplies no shape — tags over the nineteen shipped ids
within the served 2–6 bounds, grid cells over the twenty-one, radius over 1–50 km, intent over
the three values, gender and gender preference over theirs. A non-uniform draw is admissible
**only where something already states a shape**, and each one is argued in
[`the-replay-harness.md`](../specs/matchmaking/the-replay-harness.md) and printed on the report.

The rule this expresses: **the corpus asserts nothing it is not prepared to be contradicted
about.**

### 2. Two densities, one generator

| | `thin` | `dense` |
|---|---|---|
| Players per sport per area | **20** | **2 000** |
| Stands for | the launch market — the figure #161 measured, where 63% of searches return under five candidates | a plausible year-one single city, 30× below trigger 4 |
| Newcomers | **100%** | **25%** |

**PADEL and TENNIS** — one doubles sport and one singles, the minimum that exercises both the
group objective and a shortlist where `G` does not run. **One metro, several districts, spread
deliberately wider than the median radius**, so ADR-0099's ×1.5 and ×2.0 rungs have real
candidates to count rather than structural zeroes.

Same generator, same distributions, different `N` — so the pair is comparable by construction and
*"this ruleset empties the thin market and does nothing to the dense one"* is a readable line
rather than an inference.

### 3. The one argued departure: the level distribution

μ is a **truncated normal, centre 2.8, σ 0.6, clamped to the scale's 1.0–5.0**. Uniform over the
scale puts a quarter of the population in ADVANCED, clears `LEVEL_TOL_COMP` for only ~26% of
pairs, and — the damaging part — under-samples close pairs, where **predicted balance goes blind
past Δμ ≈ 0.34** (`ranking-weights.md` §4). A spread that rarely produces near-twins never
exercises the discriminating region of a term carrying 19.5 of 100 competitive.

The centre is not invented. It is read off §20.1's own walkthrough players — **2.71, 2.92, 2.75,
2.35, 3.40, 2.50** — the only stated sample of this market that exists.

Per-player **σ ≈ 0.34**, narrow, because every rating today is an *Initial Estimate* and the
document's newcomer is stamped "±0,34", which back-solves §4's typical σ_pair of 0.495 exactly.

**Its cost is named rather than discovered:** with σ near-constant, `combine_sigma` is
near-constant, so predicted balance is effectively a function of Δμ alone and **the corpus never
exercises the formula's ×32 σ coefficient**. That is a fourth approximation printed on the face of
every report, beside ADR-0118 §8's three.

### 4. The adversarial tail is counted separately

Uniform draws under-sample the rare arms — the seven clash rows of
[#179](https://github.com/Raketa02/Raketa/issues/179)'s matrix, the ×2.0 rung, floor crossings in
both directions. A small **stated tail** of constructed players makes them fire.

The tail is **excluded from every rate denominator and printed as its own block.** Coverage is
asserted off the tail; rates are read off the neutral body. Merging them would contaminate the
numbers with the fixture's own intentions, which is the failure this record exists to prevent.

### 5. The population is the artifact of record

Generator code with a fixed seed; **its output committed as a file**; CI regenerates under a
different `PYTHONHASHSEED` and requires byte-identity. Generation and pipeline in one assertion,
and a generator edit arrives in the pull request as a visible population diff instead of silently
rewriting history.

This is the repository's own idiom for the third time, after
[`check-contract-drift.sh`](../../.github/scripts/check-contract-drift.sh) and
[`check-poetry-pin-drift.sh`](../../.github/scripts/check-poetry-pin-drift.sh): generate, commit,
have CI regenerate and diff, and prove the check still fires.

### 6. Staleness is contradiction by the telemetry, not resemblance to a city

Each generator parameter is paired with the query that measures its live counterpart on ADR-0104's
record — median candidates generated per search, level-gate exclusion rate, floor clearance rate,
tag-overlap distribution, empty-result rate. **The corpus is reviewed when one leaves its stated
band**, and the check is a **periodic report, never a trigger in code**.

ADR-0118's *"a review whenever the density hypothesis moves"* survives as a **floor** on this —
mandatory the day the hypothesis resolves — rather than as the whole rule. That narrows ADR-0118's
consequence; it does not amend its decision.

### 7. Two artifacts, one vocabulary

The corpus is generated and asserts nothing. §20.1's scenarios are hand-authored, carry complete
expected responses, and are the acceptance suite. Both are built from the same builders, the same
nineteen tag ids and the same clock, so a domain change breaks them together.

**[#186](https://github.com/Raketa02/Raketa/issues/186)'s six judged pairings are not corpus
members.** They *define* `QUALITY_FLOOR`, so measuring a floor change against a population
containing them would test a ruleset against its own definition.

### 8. The corpus exercises what a ruleset can move

Blocks and the three ledgers are in; **holds and pairwise history are not, and are not
manufactured.** A hold is binary, never relaxed, and carries no constant, so no ruleset release
can change what it does — its coverage belongs to §20.2's *"no gated player ever appears"* and to
[ADR-0098](0098-matcher-demands-as-executable-contracts.md)'s contract suite, not to a diff
instrument.

Blocks stay in because [ADR-0116](0116-in-a-four-every-gate-binds-all-six-pairs.md) puts them in
the `K × K` admissibility mask, so a corpus with none systematically over-reports admissible
combinations. Their rate is **invented and stated as invented**. The ledgers get a **coverage rule
instead of a rate** — `INTEREST_LIFT`, `NEWCOMER_WINDOW` and `ZERO_EXPOSURE` each fire for at
least one row in each density — because a rule survives a resize where a percentage does not.

### 9. The clock is a Wednesday, and it is stated with its reason

ADR-0100's derived window reaches the diffed payload, and `TODAY | TOMORROW | WEEKEND |
THIS_WEEK` are thresholds evaluated against *now*: on a Saturday, `TODAY` and `WEEKEND` collapse
and two of the four values become unreachable. ADR-0120's `next_shared(shared, today)` writes the
availability card's sentence off the same weekday.

Mid-week is the only position from which all four window values are reachable and distinct. It is
written down because a fixture clock with no stated reason is a fixture clock somebody tidies.

## Consequences

**Easier**

- **The staleness question becomes answerable today.** It was unanswerable as posed — *does this
  resemble the city* — and it is measurable as re-posed, against a record that already exists and
  never expires.
- **The corpus cannot smuggle a product claim.** ADR-0118 §5 keeps materiality out of the harness;
  this keeps invented correlations out of the population, which is the same discipline one level
  further back. A neutral body plus a separately-counted tail means no number the report prints
  was decided by a shape nobody measured.
- **The two densities say different things on purpose.** The newcomer split is the clearest case:
  `thin` shows for-fun collapsing to the competitive tolerance across the whole market, which is
  factually what a launch is, and `dense` is where `LEVEL_TOL_FUN` and the newcomer lift are both
  live and separable.

**Harder**

- **The report can never answer *what is our empty-result rate*** — only how one ruleset moves it
  against another. That sentence belongs on the face of the report, because a reader will
  otherwise supply the absolute reading themselves.
- **Two densities is two of everything** — two populations, two runs, two diff blocks, and a
  reader who must be told which one a line came from.
- **The σ arm of predicted balance is untested by this instrument**, by a choice made for a good
  reason elsewhere (§3). It is printed, not hidden, and it is the corpus's only structurally blind
  term.
- **The map's missing operational surface gains a sixth signal**, and the second of them — after
  [#179](https://github.com/Raketa02/Raketa/issues/179)'s `MATRIX_COVERAGE_FLOOR` — that is a
  **periodic report** rather than a structured log record. §6's review has nowhere to be read.

## Constants introduced

All are generator parameters. None is read by scoring, and none is a ruleset constant.

| Constant | Value | What would falsify it |
|---|---|---|
| `CORPUS_THIN_N` | **20** per sport per area | The launch market landing at a materially different density — #161's own measurement superseded by a real one |
| `CORPUS_DENSE_N` | **2 000** | A rare arm still unfired at this size, or a `LINEUP` pass over it no longer affordable in CI |
| `CORPUS_MU_CENTRE` / `CORPUS_MU_SIGMA` | **2.8** / **0.6** | The live μ distribution on ADR-0104's record differing from it beyond a stated band |
| `CORPUS_PLAYER_SIGMA` | **0.34** | A rating provider that stops stamping every estimate *Initial Estimate*, at which point σ becomes a real distribution |
| `CORPUS_NEWCOMER_FRACTION` | **1.00** thin / **0.25** dense | The measured fraction of searches whose pairs contain a newcomer leaving its band |
| `CORPUS_BLOCK_RATE` | **~1 per 20 players** — invented, and stated as invented | Any measured block rate at all. This is the first number replaced the day the telemetry has one |
| Corpus clock | a fixed **Wednesday** instant | A window rule whose thresholds stop making all four values reachable mid-week |
