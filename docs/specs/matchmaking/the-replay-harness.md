# The replay harness, and what has to be true before a ruleset ships

Settles [#183](https://github.com/Raketa02/Raketa/issues/183) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
The decisions are in [ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md) and
[ADR-0119](../../adr/0119-a-ruleset-ships-on-an-offline-diff-and-a-deploy.md); this is the report
shape they imply and the checklist a build agent ticks off.

**A past search is explainable forever and is not reproducible.** Those are different words and
§20.3 ran them together. What the harness answers is *what would this ruleset have done to the
searches we have*, which is a narrower question and the one a weight argument actually asks.

---

## 1. The four inputs, and the three that are gone

| Input | Where it is at search time | Later |
|---|---|---|
| **Candidate index** — μ, σ, tags, grid, intent, area, radius, gender | A per-worker projection at `snapshot_version` | **Reconstructible** by replaying `event_store` (ADR-0110) — and the harness declines to |
| **Live block set**, pairwise history, open challenges | `SearchContext`, per request (ADR-0095, ADR-0098) | **Gone** |
| **Held account** | `AccountHoldQuery`, live (ADR-0098) | **Gone** |
| **Ledgers** — interest, exposure, suppression | Redis, with TTLs (ADR-0093) | **Gone** |

The three are absent by decision. [ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)
took every live-truth fact out of the index so staleness costs quality and never safety;
[ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md) kept the search
record to ids and counts because it is *"still a social graph"*.

What replaces them is a fact `search-telemetry.md` §3 already records: **`terms` holds each
term's value**, `degraded_terms` holds the renormalisation basis, `modifiers` holds which fired.
A ruleset moves weights; the index produces values.

---

## 2. Two corpora

| | **Recorded** | **Synthetic** |
|---|---|---|
| Population | Every search ever made | A fixed generated city, checked in |
| Inputs | Recorded term values | Invented, therefore complete |
| Pipeline run | Re-weight, renormalise, re-rank, re-floor | Generation → gates → scoring → group objective → floor |
| Sees | Movement inside the recorded band | Promotion from anywhere, gate changes, value changes |
| Blind to | Anything outside `RETURNED` ∪ `NEAR_MISS`; anything that moves a term *value* | Real people |
| Cost | One SQL query | One in-process run |
| Runs in CI | No — restore only (ADR-0118 §7) | **Yes**, hermetic |

The synthetic corpus's construction is in §2.1. **It does not stand for the city and does not
try to** — [ADR-0121](../../adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md).

---

## 2.1 The synthetic corpus, constructed

Settles [#185](https://github.com/Raketa02/Raketa/issues/185).
[ADR-0121](../../adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md).

**Every number this harness prints is a comparison** — baseline ruleset against candidate over
the *same* population — and §5 already forbids it a materiality threshold, so it makes no
absolute claim about anything. A neutral population orders two rulesets correctly. What it
cannot do is tell you what the empty-result rate *is*, and the report says so on its face.

### Two densities, one generator

| | `thin` | `dense` |
|---|---|---|
| Players per sport per area | **20** | **2 000** |
| Stands for | the launch market — [#161](https://github.com/Raketa02/Raketa/issues/161)'s measured figure, where 63% of searches return under five candidates | a plausible year-one single city, 30× below trigger 4 |
| Newcomer fraction | **100%** — what a launch factually is | **25%** |

**Sports: PADEL and TENNIS.** One doubles and one singles — the minimum that exercises both the
group objective and a shortlist where `G` does not run (`the-group-objective.md` §3). All four
would quadruple the run to reach no additional branch.

**Geography: one metro, several districts, spread deliberately wider than the median radius**,
so ADR-0099's ×1.5 and ×2.0 rungs have real candidates to count instead of structural zeroes.

### The draws

Uniform wherever the repository supplies no shape. A non-uniform draw is admissible **only where
something already states one**, and there is exactly one.

| Field | Draw | Source of the bounds |
|---|---|---|
| Social tags | uniform over the **nineteen** ids, count uniform over the served **2–6** | `social_tags.py`, product-confirmed 2026-08-25 |
| Availability grid | uniform over the **twenty-one** cells, ≥ 1 ([ADR-0102](../../adr/0102-silence-is-never-scored.md)) | `availability.py` — 7 days × MORNING/AFTERNOON/EVENING |
| Search radius | uniform over **1–50 km**, step 1 | `search_radius.py` |
| Play intent | uniform over the **three** values | [ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md) |
| Gender · preference | uniform over theirs | [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) |
| **Level μ** | **truncated normal, centre 2.8, σ 0.6**, clamped to 1.0–5.0 | **the one departure — argued below** |
| **Player σ** | **≈ 0.34** | every rating today is an *Initial Estimate* |
| Profile commit date | a named window **straddling ADR-0113's fourteen days**, to hit the fraction above | never an emergent side effect of when the fixture was written |

**Why μ is not uniform.** Uniform over the scale puts a quarter of the population in ADVANCED,
clears `LEVEL_TOL_COMP` for only ~26% of pairs, and under-samples close pairs — where
**predicted balance goes blind past Δμ ≈ 0.34** (`ranking-weights.md` §4). A spread that rarely
produces near-twins never exercises the discriminating region of a term carrying 19.5 of 100
competitive. The centre is read off §20.1's own walkthrough players — **2.71, 2.92, 2.75, 2.35,
3.40, 2.50** — the only stated sample of this market that exists. σ ≈ 0.34 back-solves §4's
typical σ_pair of 0.495 from the document's own newcomer, stamped "±0,34".

**And its cost, printed rather than discovered:** σ near-constant makes `combine_sigma`
near-constant, so predicted balance is effectively a function of Δμ alone and **the corpus never
exercises the ×32 σ coefficient.** A fourth named approximation, beside ADR-0118 §8's three.

### The `SearchContext`, and what is deliberately absent

**The corpus exercises what a ruleset can move.**

| Fact | In the corpus | Why |
|---|---|---|
| Blocks | **Yes**, ~1 per 20 players — **invented, and stated as invented** | ADR-0116 puts them in the `K × K` admissibility mask; a corpus with none over-reports admissible combinations |
| Interest · exposure · suppression ledgers | **Yes**, by a **coverage rule, not a rate** — `INTEREST_LIFT`, `NEWCOMER_WINDOW` and `ZERO_EXPOSURE` each fire for ≥ 1 row per density | A rule survives a population resize where a percentage does not. These are also the three rows ADR-0118 §8 makes the *recorded* corpus carry forward unrecomputed — recomputing them is something only this corpus can do |
| Held accounts | **No** | Binary, never relaxed, no constant — no ruleset release can change what it does. Its coverage is §20.2's *"no gated player ever appears"* and ADR-0098's contract suite |
| Pairwise history · open challenges | **Yes**, by the **same coverage rule** — `PREVIOUS_ACCEPT`, `PREVIOUS_DECLINE` and each of `CHALLENGE_LOAD`'s three rungs fire for ≥ 1 row per density, and ≥ 1 pair is gated on an open challenge | They used to be a **No**, on the grounds that the provider was `NoMatchHistoryExists` — and [#253](https://github.com/Raketa02/Raketa/issues/253) killed that justification. Three of these are **priced**, so leaving them out would put a ruleset that moved the load rungs behind an **empty diff**. The inbox depths are the fixture's own constants and never read from the ruleset, so a rung moving is a diff rather than a population that quietly re-straddled it |

### The clock

**A fixed Wednesday instant, stated with its reason.** ADR-0100's derived window rides on the
response and `TODAY | TOMORROW | WEEKEND | THIS_WEEK` are thresholds against *now* — on a
Saturday, `TODAY` and `WEEKEND` collapse and two of the four become unreachable. ADR-0120's
`next_shared(shared, today)` writes the availability card's sentence off the same weekday.
Mid-week is the only position from which all four are reachable and distinct.

### The searches

Every player runs `SHORTLIST` in **both modes**. Every *n*-th player **by id order** runs
`LINEUP`, `FILL_SEATS` and `DECK` — a rule, never a sample, because a rule survives a resize.
The collision is real: `SHORTLIST` is 1.00 µs per surviving candidate and a line-up is 2 024
combinations × 3 arrangements at `K = 24` (`scale-posture.md` §6). **Per-surface search counts
are printed**, so the coverage is on the face of the report.

### The adversarial tail

Uniform draws under-sample the rare arms — [#179](https://github.com/Raketa02/Raketa/issues/179)'s
seven clash rows, the ×2.0 rung, floor crossings in both directions. A small stated tail of
constructed players makes them fire, and is **excluded from every rate denominator and printed
as its own block**. Coverage is asserted off the tail; rates are read off the neutral body.

### What it is not

**§20.1's scenarios are a second artifact, not a slice of this one.** They are hand-authored,
carry complete expected responses, and assert verdicts. In particular
[#186](https://github.com/Raketa02/Raketa/issues/186)'s six judged pairings are **not corpus
members**: they define `QUALITY_FLOOR`, so measuring a floor change against a population
containing them tests a ruleset against its own definition. Both are built from the same
builders, tag ids and clock, so a domain change breaks them together.

### When it goes stale

**By contradiction, never by resemblance.** Each parameter is paired with the query that measures
its live counterpart on [ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md)'s
never-expiring record — median candidates generated per search, level-gate exclusion rate, floor
clearance rate, tag-overlap distribution, empty-result rate. The corpus is reviewed when one
leaves its stated band. **A periodic report, never a trigger in code.**

ADR-0118's *"a review whenever the density hypothesis moves"* survives as a **floor** on this,
mandatory the day the hypothesis resolves — not as the whole rule, because a rule that waits on
fog may never fire.

> This review has **nowhere to be read**. It is the sixth signal on the map's missing operational
> surface, and the second — after #179's `MATRIX_COVERAGE_FLOOR` — that is a report rather than a
> log record.

---

## 3. The validity test, which runs first

Run the synthetic population under both rulesets and compare **term values**, not contributions.

```
values identical   → weight-only  → print the recorded diff and the synthetic diff
any value moved    → shape-class  → print the synthetic diff only, and say why
```

Derived, never declared: there is no per-constant annotation to maintain and none to get wrong.
It catches term activation for free — a term that was not live has no recorded values anywhere,
so every historical search is void for it.

---

## 4. The report

Every line names which corpus produced it. Nothing is a pass or a fail; §5 says who decides.

```
$ make ruleset-diff RULESET=2026.09.01-b BASELINE=2026.08.25-a CORPUS=<restore>

  classification                 weight-only        (synthetic: 0 term values moved)

  recorded corpus                2026-08-26 → 2026-09-30
  searches                       12 481
  replayed                       12 402  (99.4%)
  excluded                          79   redacted by erasure

  verdicts                       unchanged            71.8%
                                 reordered            10.6%
                                 composition changed   9.8%
                                 crossed the floor     6.1%
                                 emptiness flipped     1.7%

  top-1 changed                       7.4%
  mean fit of top-1              76.3 → 77.1          (over 6 renormalisation bases)
  empty results                   4.1% →  3.6%
  offer computation flipped           2.2%
  exposure Gini                  0.51 → 0.47          (from shortlists, not the ledger)

  near-miss band saturated in         0 searches
  carried forward unchanged         311 rows          INTEREST_LIFT / NEWCOMER_WINDOW / ZERO_EXPOSURE
  level gate                     bounded, not computed — 0 admitted Δμ moved
```

**The metrics, and where each survives from §20.3:**

| Metric | Corpus | Note |
|---|---|---|
| Shortlist composition changed | Recorded | Coherent only because the near-miss band is read (ADR-0118 §4) |
| Top-1 changed | Recorded | |
| Mean Fit of top-1 | Recorded | §10 renormalises per comparison, so this is a mixture — **print the basis count beside it** |
| Empty results | Recorded | The number the quality floor owns |
| **Exposure Gini** | Recorded | **Re-sourced.** The ledger is a TTL and is gone; `band = RETURNED` over the window *is* the exposure record — who was shown, how often, durably. Measures the thing the metric always meant |
| Rung relaxations | Split | *Whether offers were computed* is recorded and diffable; each rung's **real count** needs generation at a wider radius and is the synthetic corpus's |
| **Floor crossings** | Recorded | New. Both directions, and the single most consequential change a ruleset makes |
| **Near-miss saturation** | Recorded | New. The blindness indicator — see §6 |
| **Coverage** | Recorded | New. See §6 |

---

## 5. Who decides

The harness classifies and counts. **It carries no materiality threshold**, because a number
saying *18% composition change is acceptable* is a product decision smuggled into code.

The **owner accountable for the quality floor** signs the release (ADR-0119 §5), and the pull
request carries the diff plus one line per changed constant — the hypothesis and its falsifier,
which is the discipline `ranking-weights.md` §13 and §24 already apply to every constant here.

---

## 6. What the harness refuses to hide

- **Coverage.** Erasure is the only path that deletes a row (ADR-0104 §3). Erasing a *candidate*
  removes a row from a search that still exists, so the replayed set differs for a reason that is
  not the ruleset. `count(band = RETURNED) ≠ search.n_returned` detects it exactly; affected
  searches are **excluded and counted, never repaired**. This makes `n_returned` load-bearing
  rather than redundant.
- **Near-miss saturation.** If every recorded near-miss crossed the floor, the diff understated
  the change and `NEAR_MISS_RECORDED` is too small. Printed every run.
- **The three carried-forward inclusion reasons.** `INTEREST_LIFT`, `NEWCOMER_WINDOW` and
  `ZERO_EXPOSURE` read ledgers that no longer exist, so those rows carry into the candidate
  ruleset unchanged instead of being recomputed. Counted on the report.
- **The level gate.** `ranking-weights.md` §12 records the gate's exclusion count and the smallest
  admitted Δμ — a **bound**, not a computation. A `LEVEL_TOL` change is bounded by the recorded
  corpus and answered by the synthetic one.

---

## 7. The gate

| Half | Mechanism | What it proves |
|---|---|---|
| **Synthetic** | Committed artifact; `check-ruleset-diff.sh` regenerates and diffs in CI; `make test-ruleset-diff` proves the check still fires | A ruleset edited without regenerating its diff **fails the build** |
| **The population** | Seeded generator in code, **its output committed as a file**; CI regenerates and requires byte-identity ([ADR-0121](../../adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md) §5) | A generator edit arrives as a **visible population diff** instead of silently rewriting every past comparison. The repo's generate-commit-diff idiom, third instance |
| **Determinism** | CI regenerates under a **different `PYTHONHASHSEED`** than produced the committed file | **Generation and pipeline in one assertion** — ADR-0105 §2 asserts the pipeline over one test, and the generator is where a set of generated ids would be ordered unnoticed. The sanctioned §4 exception, second instance |
| **Recorded** | CI asserts the PR body carries a report block naming its corpus window and coverage | **Presence, not truth.** Half this gate is a signature and that is said out loud |
| **Runtime** | Validation at startup; a bad ruleset **fails the deploy** and the old pods keep serving | §11's *"the previous one keeps serving"*, restated for an embedded ruleset with no hot reload |

---

## 8. What this demands, and what it hands onward

**Two demands on [`search-telemetry.md`](search-telemetry.md), applied in the same change:**

| Demand | Why |
|---|---|
| `n_near_miss_recorded` on `search` | One integer. Without it, redaction inside the near-miss band is undetectable, where `n_returned` makes it exact for the returned band |
| `liveness_signals` on `search_candidate` — the **raw values** | The offset is ruleset-dependent, so recording the offset makes a Liveness-bounds change undiffable. `ranking-weights.md` §12 asked for the offset and its dominant signal, which is the wrong half |

**What it hands onward:**

- **The runtime ruleset store**, still deferred, now owes one more thing: §7's runtime row stops
  being true the day a ruleset is read from somewhere other than the binary.
- **The outcome half of the chain** is what arms canary (ADR-0119 §2). Until it exists, no weight
  change on this platform is justified by a measured outcome.
- **A shape-class change** with a synthetic corpus its owner will not sign is what arms shadow
  (ADR-0119 §3). It is the only condition under which nothing else can answer.

---

## 9. Constants introduced

**No ruleset constants.** `NEAR_MISS_RECORDED = 10` gains a **second falsifier** — promotions
saturating the band — and `K = 24`'s engine-side ceiling (`scale-posture.md` §6) is enforced by
§7's runtime row rather than restated here.

§2.1 introduces **seven generator parameters**, none of which is read by scoring and none of
which is a ruleset constant:
[ADR-0121](../../adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md) carries the
table and a falsifier for each. `CORPUS_BLOCK_RATE` is the one openly invented number here, and
it is the first thing replaced the day the telemetry has a measured rate.

---

## 10. Where this lives, now that it is built

Settled by [#215](https://github.com/Raketa02/Raketa/issues/215) and written up in
[`the-ruleset-gate.md`](the-ruleset-gate.md), which is the account of what was built and what
was deliberately not.

- **The synthetic half of §7 is a build gate.** The population and the corpus's answers are
  committed under `ruleset-diff/`, regenerated by `make gen-ruleset-diff`, and diffed by
  [`check-ruleset-diff.sh`](../../../.github/scripts/check-ruleset-diff.sh) — under **two
  different `PYTHONHASHSEED`s**, both required to reproduce, which is §7's determinism row and
  ADR-0105 §4's sanctioned exception used a second time. `make test-ruleset-diff` drives that
  check against a deliberately broken tree.
- **§3's validity test is derived, and its two failure modes are told apart.** The values are
  hashed per term over every scored pairing — not over the recorded band, whose membership a
  *floor* change moves — so a floor release classifies as **weight-only** rather than sending
  its owner to shadow scoring for a change the recorded corpus can answer exactly. When the
  classification is shape-class, the report says whether the values moved or the **gate** did,
  because ADR-0118 §8 bounds the second on the recorded corpus and voids it for the first.
- **§2's `dense` column is not a gate.** It runs on demand
  (`python -m scripts.ruleset_diff --density dense`) and is measured in hours where the thin
  corpus is measured in seconds; `the-ruleset-gate.md` §1.1 carries the figures. A gate that
  takes hours is a gate somebody turns off.
- **§4's report is printed, never committed.** What is committed is the corpus's answers; the
  report is what regenerating them prints, which is what the pull request argues for.
- **The recorded half is untouched and unbuilt, and its signature is asked for.** The diff
  itself needs a restore (ADR-0118 §7) and does not run in CI; what runs is
  [`check-release-report-block.sh`](../../../.github/scripts/check-release-report-block.sh),
  on the pull requests that move the diff artifacts, asserting the body names its **corpus
  window** and its **coverage**. **Presence and not truth** — a block whose numbers are
  invented passes, and the suite asserts that it passes, exactly as ADR-0119 §4 says.
