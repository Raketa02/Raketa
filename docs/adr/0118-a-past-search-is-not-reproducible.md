# ADR-0118 — A past search is not reproducible; the replay harness re-weights what was recorded

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §20.3 calls the replay
harness *"the single most valuable test asset in the system"* and says what it does: record
production searches — request plus snapshot version — replay them against a candidate ruleset,
diff the shortlists. It is what turns *"vibe should be 24"* from an argument into an experiment,
and it is the reason §11 exists.

[#183](https://github.com/Raketa02/Raketa/issues/183) was charted as unblocked by
[ADR-0110](0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md)'s watermark, on the
reasoning [ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md) left behind:
determinism ships now as a two-subprocess property test, while replaying a *past* search
*"additionally needs the index as it stood."* That sentence is true. It is also the smaller half
of the condition, and the charting read it as the whole one.

**A search has four kinds of input, and the index is one of them.**

| Input | Where it is at search time | Reconstructible later |
| --- | --- | --- |
| The **candidate index** — μ, σ, tags, grid, intent, area, radius, gender | A per-worker projection at `snapshot_version` | **Yes**, by replaying `event_store` to that point (ADR-0110) |
| The searcher's **live block set**, and their **pairwise history and open challenges** | The `SearchContext`, assembled per request ([ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md), [ADR-0098](0098-matcher-demands-as-executable-contracts.md)) | **No** |
| The **held account** check | `AccountHoldQuery`, live (ADR-0098) | **No** |
| The **ledgers** — interest, exposure, suppression | Redis, with TTLs (ADR-0093) | **No** |

Three of the four are absent **by decision, not by oversight**.
[ADR-0111](0111-the-index-holds-only-what-a-player-changes-about-themselves.md) took every
live-truth fact out of the index precisely so a stale index can cost quality and never cost
safety; [ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) kept the search
record to ids and counts because it is *"still a social graph"* and refused to widen it. So
§20.3's premise — **replay a past search** — is not available today and does not become available
by finishing anything on this map. Reconstructing the index reconstructs one input of four.

**What is available is something this map already paid for and had not spent.**
[`search-telemetry.md`](../specs/matchmaking/search-telemetry.md) §3 records
`search_candidate.terms` as *"every term with its **value**, weight, contribution and evidence
codes"* — the value, not only the contribution — with `degraded_terms` carrying the
renormalisation basis and `modifiers` carrying which fired. A ruleset changes weights; the index
produces values. **B's Fit for a recorded candidate is therefore arithmetic over rows that already
exist**, needing no index, no event replay and no `SearchContext`.

### Ruled out

- **Reconstruct the index to `snapshot_version` and re-run generation, gating and scoring.**
  Affordable — searches sort by watermark, so it is one forward pass over a log that tails at
  959 000 events/s — and it lands *between* the two options kept, on both axes. Its candidate set
  differs from the original's by exactly the live-truth exclusions it cannot apply, in an unknown
  direction, so it is **lower fidelity than re-weighting** for the weight changes that actually
  ship and **contaminated** for everything else. It buys an index rebuild to be worse at both jobs.
- **Record the `SearchContext` on the search row** so a replay has its live inputs. That is a
  durable record of who blocked whom, written on the table ADR-0104 already named as the largest
  in the system and deliberately kept to ids and counts. The harness is not worth it.
- **Annotate every ruleset constant with whether it moves a weight or a value.** A taxonomy
  maintained by hand, wrong in exactly the case that matters — the one nobody thought to classify.
- **Shadow scoring as the primary instrument.** The only full-fidelity real-traffic answer there
  is, and priced and deferred in [ADR-0119](0119-a-ruleset-ships-on-an-offline-diff-and-a-deploy.md)
  rather than here.

## Decision

**We will build a replay harness with two corpora and one validity test, and it will never
reconstruct an index.**

### 1. The recorded corpus, re-weighted

Read `search` and `search_candidate`. Recompute each candidate's Fit from the **recorded term
values** under the candidate ruleset, renormalising over `degraded_terms`, re-applying modifiers
by code, re-ranking on ADR-0105 §3's named total order, and re-applying the candidate ruleset's
floor.

Exact, retroactive to the first search ever recorded, and costing a SQL query. Bounded to the
returned rows plus the near-miss band — so a candidate who ranked four hundredth cannot be
promoted, because their value was never stored.

### 2. The synthetic corpus, run end to end

A fixed generated population, a fixed clock and a fixed `SearchContext`, through the whole
pipeline — generation, gates, scoring, the group objective, the floor. Complete and exact,
because every input is invented rather than remembered. It is checked into the repository and it
is deterministic.

It covers precisely what §1 is blind to: promotion from outside the recorded band, gate changes,
and any constant that alters what a term *reports*.

### 3. The synthetic corpus decides whether the recorded one may be believed

Run the synthetic population under both rulesets and compare the **term values**, not the
contributions.

- **Every value identical** — the change is weight-only, the recorded corpus is exact, and the
  harness prints its diff.
- **Any value moved** — the change alters what the index produces, the recorded corpus cannot
  answer it, and the harness prints **only** the synthetic diff and says so in the report.

The classification is derived rather than declared, so there is no annotation to maintain and
none to get wrong. It catches for free the case an annotation would certainly have missed:
`ranking-weights.md` §11's *turning a term on is a ruleset release* — a term that was not live
has no recorded values anywhere, so every historical search is void for it, and the harness
discovers that rather than being told.

### 4. Both bands, and the band announces its own blindness

The diff reads `RETURNED` **and** `NEAR_MISS`. Reading only the returned rows makes every
candidate the new ruleset lifts *into* a shortlist invisible, and the harness would report
*composition unchanged* for a release that changes three seats — so layer 3 is what makes §1
coherent, not an enrichment of it. ADR-0104 §5's *no route ever returns it, to anyone* is
untouched and unamended: an offline `make` target read by the ruleset's owner is not a route, and
that sentence is written here so §5 is not later read as forbidding this.

`NEAR_MISS_RECORDED = 10` gains a second falsifier. **If a diff's promotions ever saturate the
band, the diff understated the change**, and the harness prints that count on every run so the
blindness announces itself instead of being assumed away.

### 5. The harness classifies; it never judges

One verdict per search — unchanged, reordered, composition changed, crossed the floor, emptiness
flipped — rolled up to rates. **No materiality threshold lives in the harness.** A number that
says *18% composition change is acceptable* is a product decision smuggled into code, and
ADR-0119 puts a name on the person who owns it.

### 6. Coverage is printed, and redaction is detected against the counters

Erasure is the only path in this design that deletes a row (ADR-0104 §3), and erasing a
*candidate* removes one row from a search that still exists — so the replayed set differs for a
reason that is not the ruleset. `search.n_returned` lives on the surviving row, so
`count(band = RETURNED) ≠ n_returned` is an exact redaction detector. **Affected searches are
excluded and counted, never repaired**, and the report prints its coverage, because a replay
whose coverage is quietly 60% is the same disease as a silent truncation.

`n_returned` is therefore load-bearing rather than redundant, and the near-miss band needs the
same counter — see §8.

### 7. It runs from the composition root, against a restore

A `make` target and a CLI built from `app/bootstrap/composition.py`, following ADR-0110's rebuild
precedent. **No route, ever** — and the recorded-corpus run reads a **restored copy**, never the
live database, so a replay can never contend with a search and the social graph is not read en
masse from a process that also answers player requests. The synthetic run is hermetic and belongs
in CI.

### 8. Two demands back on the telemetry, and three approximations named

Recorded in [`the-replay-harness.md`](../specs/matchmaking/the-replay-harness.md) and applied to
[`search-telemetry.md`](../specs/matchmaking/search-telemetry.md) in the same change:

- **`n_near_miss_recorded` on the `search` row** — one integer, for exactly the reason
  `n_returned` works. Without it, redaction inside the near-miss band is undetectable.
- **`liveness_signals` on `search_candidate`** — the **raw signal values**, not the offset they
  produced. The offset is ruleset-dependent, so recording it makes a Liveness-bounds change
  undiffable; `ranking-weights.md` §12 asked for the offset and its dominant signal, which is the
  wrong half.

And three things the recorded corpus approximates rather than computes, printed on the face of
every report rather than known by whoever wrote the harness: rows admitted by `INTEREST_LIFT`,
`NEWCOMER_WINDOW` or `ZERO_EXPOSURE` **carry forward unchanged**, because all three read ledgers
that no longer exist; a `LEVEL_TOL` change's effect is **bounded and not computed**, from the
gate's recorded exclusion count and smallest admitted Δμ; and each relaxation rung's **real
count** is the synthetic corpus's to produce, because it needs generation at a wider radius.

## Consequences

**Easier**

- **The experiment §11 promised is available on day one and reaches backwards.** ADR-0104's
  never-expiring record stops being only an explanation surface and becomes the corpus, so the
  first ruleset argument is settled against every search ever made rather than against a sample
  gathered after somebody remembered to gather it.
- **The harness cannot quietly overstate itself.** Its validity is computed, its coverage is
  printed, and its blind spot has a counter that fires when it starts to matter.
- **No index reconstruction to build, own or keep correct.** ADR-0110's rebuild target stays a
  one-shot operational tool with one job.

**Harder**

- **§20.3's headline claim is retired, and something narrower replaces it.** *"Record production
  searches; replay them"* is not what this system does and the document should not be read as
  though it were. A past search stays **explainable forever** — that is ADR-0104's promise and it
  is untouched — and is **not reproducible**, which are different words that had been running
  together, including in `CONTEXT.md`'s own gloss on **Snapshot version**, corrected in this
  change.
- **A shape-class change is answerable only against a population we invented.** That is a real
  gap and it is the exact condition ADR-0119 arms shadow scoring on.
- **The synthetic corpus is a fixture with all a fixture's failure modes.** A population that
  drifts away from the city it stands for will keep producing confident diffs about nobody. It
  needs a stated construction and a review whenever the density hypothesis moves.

  > **Narrowed by [ADR-0121](0121-a-fixture-stands-for-a-comparison-never-for-a-city.md).** The
  > construction is supplied, and the framing of this sentence is corrected rather than kept: the
  > corpus does not stand for the city and cannot, so *drift away from the city* has no evaluable
  > test while the city is unbuilt. It goes stale by **contradiction** — a named generator
  > parameter leaving its band against ADR-0104's record — and the density-hypothesis review
  > survives as a **floor** on that rather than as the whole rule. The decision above is
  > untouched.
- **`snapshot_version` is not spent by this decision and is not wasted either.** It stamps the
  world a Fit was computed against, which is what makes an old breakdown interpretable, and it
  remains the input a full replay would need if the live-truth half ever becomes recordable.
  ADR-0110 is unamended; ADR-0105's *"additionally needs the index as it stood"* is true and was
  necessary-but-not-sufficient, and this record supplies the rest of the condition rather than
  correcting it.
