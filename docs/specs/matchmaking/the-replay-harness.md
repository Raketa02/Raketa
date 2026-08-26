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

The synthetic corpus needs a stated construction — population size, level distribution, tag
draw, grid density, area spread — and a review whenever the density hypothesis moves. A fixture
that drifts away from the city it stands for keeps producing confident diffs about nobody.

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
| **Determinism** | CI regenerates under a **different `PYTHONHASHSEED`** than produced the committed file | Whole-pipeline determinism, continuously — ADR-0105 §2 asserts it over one test. The sanctioned §4 exception, second instance |
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

None. `NEAR_MISS_RECORDED = 10` gains a **second falsifier** — promotions saturating the band —
and `K = 24`'s engine-side ceiling (`scale-posture.md` §6) is enforced by §7's runtime row rather
than restated here.
