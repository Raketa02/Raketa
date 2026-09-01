# The ruleset gate, and the three signals nobody can read

Built for [#215](https://github.com/Raketa02/Raketa/issues/215) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
The decisions are [ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md),
[ADR-0119](../../adr/0119-a-ruleset-ships-on-an-offline-diff-and-a-deploy.md) and
[ADR-0121](../../adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md); the report
shape is [`the-replay-harness.md`](the-replay-harness.md) and the thresholds are
[`scale-posture.md`](scale-posture.md). **This file is what was actually built, what was
deliberately not, and where each of the three instruments emits into.**

Two things ship here and they are not the same kind of thing. The first is a **gate**: a
machine that fails a build. The second is **instrumentation**: three signals that say when
the bet this architecture is built on stops holding. Nothing about the second is a bet that
the numbers are right; it is a bet that they will be **measured**.

---

## 1. Shipping a ruleset is an offline diff and a deploy

ADR-0119 collapsed `matchmaking-engine.md` §22's three-rung rollout. **Canary** cannot
measure its own success — its metric is acceptance, and the outcome half of the telemetry
chain needs `matches`, which does not exist. **Shadow** is the only full-fidelity instrument
on real traffic and it buys a slower version of an answer already on hand; it is armed by the
first shape-class change whose synthetic corpus its owner will not sign. What is left is the
diff, and *no ruleset ships without a diff* had to stop being a sentence.

| Half | Mechanism | What it proves | Where |
|---|---|---|---|
| **Synthetic** | Committed artifact; regenerated and diffed in CI | A ruleset edited without regenerating its diff **fails the build** | [`check-ruleset-diff.sh`](../../../.github/scripts/check-ruleset-diff.sh) |
| **The population** | Seeded generator in code, its output committed | A generator edit arrives as a **visible population diff** instead of silently rewriting every past comparison | `population.thin.json` |
| **Determinism** | Regenerated under **two different `PYTHONHASHSEED`s**, both required to reproduce | Generation and pipeline in one assertion, on every pull request | the same check |
| **The check itself** | Driven against a deliberately broken tree and asserted to go red | A guardrail that silently stops matching is worse than none | [`test-ruleset-diff.sh`](../../../.github/scripts/test-ruleset-diff.sh) |
| **Recorded** | A `pull_request` job asserts the body carries a report block naming its **corpus window** and **coverage** | **Presence, not truth** — nothing in CI can see the corpus, and it refuses only a release that never looked | [`check-release-report-block.sh`](../../../.github/scripts/check-release-report-block.sh) |
| **Runtime** | `verify_ruleset()` at startup; a bad ruleset **fails the deploy** | §11's *the previous one keeps serving*, restated for an embedded ruleset | `app/bootstrap/matchmaking.py` |

```
make gen-ruleset-diff    # re-run the corpus, rewrite the artifacts, print the diff
make ruleset-diff        # verify the committed artifacts reproduce, under both seeds
make test-ruleset-diff   # verify that check still fires
```

**The signature half is checked for presence and nothing more.** The recorded-corpus diff needs
a database restore (ADR-0118 §7), so no machine here can tell whether the window is the one that
was replayed or the coverage figure the one the harness printed. What it refuses is a ruleset
release shipped with no report at all — the failure that actually happens — and it asks only the
pull requests that move the diff artifacts, because a gate that asks everybody for a corpus
window is a gate everybody learns to paste nonsense into.

**The report the generator prints is the diff.** There is one ruleset embedded in the binary
(ADR-0093), so *baseline against candidate* is *what the last release answered against what
this tree answers* — which is the comparison a release argument actually makes, and it is why
the answers are committed rather than computed twice from the same code.

**Two failures, and they are not the same failure.** A ruleset moved and its diff was not
regenerated is a release that needs an argument. The same seed producing two different
answers is a **determinism** failure and not a ruleset change at all. The check prints the
seed beside each file that did not reproduce, so the two are told apart on the way in.

**What the classification is, and what it is not.** ADR-0118 §3's test is derived, never
declared: the corpus is run and each term's *values* are hashed, so *weight-only* and
*shape-class* are computed rather than annotated. The report prints the term readings beside
the digests, because a value moving and the **gated population** moving are both shape-class
and have different answers — a moved value voids the recorded corpus for that term, where a
moved gate is *bounded and not computed* on it (ADR-0118 §8).

### 1.1 The corpus that runs, and the one that does not

[`the-replay-harness.md`](the-replay-harness.md) §2.1 states two densities. **Only the thin
one is a build gate, and the reason is runtime rather than preference.**

| | `thin` | `dense` |
|---|---|---|
| Players per sport per area | 20 | 2 000 |
| Members | **167** — two sports × four districts, plus the seven-row adversarial tail | ~16 000 |
| Searches | **436** — every member in both modes, every fifth on all four surfaces | ~41 600 |
| Measured cost | **~1.9 s** | **hours** — a search over an 8 000-row partition is ~230 ms, and there are 41 600 of them |
| Committed | **Yes** | No |

`make gen-ruleset-diff` takes `--density dense` through
`poetry run python -m scripts.ruleset_diff --density dense` for anybody who wants it; it is
not a gate and its artifacts are not committed. **A gate that takes hours is a gate somebody
turns off**, and the thin corpus is the launch market this platform actually has —
[#161](https://github.com/Raketa02/Raketa/issues/161)'s measured figure, where 63% of
searches return under five candidates.

The construction is ADR-0121's and lives in
[`backend/scripts/ruleset_diff/population.py`](../../../backend/scripts/ruleset_diff/population.py),
parameter by parameter. **Two things are rules rather than draws** — the newcomer fraction
and the ledger coverage — because a rule survives a population resize where a percentage does
not, which is §2.1's own argument applied to the one thing it decides.

### 1.2 What this gate cannot see, printed on every run

- **It does not stand for a city and does not try to** (ADR-0121). Every number is baseline
  against candidate over one population; the report makes no absolute claim about anything.
- **σ is near-constant**, so predicted balance is effectively a function of Δμ and the ×32 σ
  coefficient is never exercised. §2.1's fourth named approximation.
- **Reliability has no provider on this platform**, so the term stands down for everybody and
  its digest is the empty one.
- **The recorded corpus is not run and cannot be** — no database in CI, and ADR-0118 §7
  restricts it to a restore.
- **The near-miss band's saturation is counted every run.** If a diff's promotions ever
  saturate the band, the diff **understated** the change and `NEAR_MISS_RECORDED = 10` is too
  small — the blindness announces itself instead of being assumed away.

---

## 2. The three signals, and the fact that nowhere reads them

`scale-posture.md` §4: **both triggers ship instrumented in the first build**, because *a
trigger that requires somebody to go and measure fires late, which is the same disease as a
claim with no trigger.* All three below are **structured log records** and there is **nowhere
to read them** — no metrics stack, no dashboard, no alerting. That is named fog, not a gap
this build closes, and it is the map's missing operational surface gaining its instruments
before its readers.

| Signal | Fires at | Record | Level when it fires |
|---|---|---|---|
| **Trigger 1** — scoring contends with the request | p99 of one scoring call > **20 ms**, **or** duty cycle > **0.25**, on one worker over 15 min | `scoring pressure window`, once per window per worker | `WARNING` |
| **Trigger 4** — the index outgrows the container | `bytes_per_row × rows × workers` > **50%** of the limit — roughly **25 000 players** at four workers on a 1 GB container | `candidate index refreshed`, at every index load | `WARNING`, and it **never refuses** |
| **Index staleness** | 15 min flags, 24 h refuses (`index_staleness.py`) | `candidate index refreshed`, and `index_stale` on the search row | `WARNING` past §17's p99 |

**Trigger 1 has two instruments and they are both here.** The *histogram around the scoring
call* is the same span the search row already records as `pipeline` — one measurement, because
the day two timers disagree there is no way to tell which one is the cost of a search. The
*event-loop lag monitor* is an ADR-0092 `PeriodicJob` that measures **its own oversleep**: it
asks the loop to wake it in a second and is woken in a second plus ε, and ε is time the loop
could not get back to it. It costs one subtraction per tick and is measured by the loop it is
measuring.

Both halves of trigger 1 are recorded whichever fired, because *the p99 crossed* and *the duty
cycle crossed* send the reader to different rungs of `scale-posture.md` §5 — the first to
bucketing and cheaper distance, the second to a process pool with a resident index.

**Trigger 4 warns and never refuses.** An index that has outgrown half its container is a
capacity decision — `array`-packed columns at 43 bytes a row, at 23% on the scan — and a
process that refused to load its index over it would take the platform down to avoid using
memory it had been given. Where there is no cgroup limit to read, the record says the limit is
**unknown**: unknown is not unlimited, and reporting a comfortable fraction of a made-up limit
would be the invented measurement this map refuses everywhere else.

### 2.1 The three constant rosters, pinned by test

Each because **a table titled *every constant* has already quietly gained or lost a row on
this map.**

| Roster | Pinned by | What it refuses |
|---|---|---|
| The **silent liveness signals** and their reachable net | `test_matchfit_ruleset.py` | A third silent signal, which is ADR-0123 decision and not a row |
| The **modifier roster** | `test_matchfit_modifiers.py` | The two struck modifiers returning, and a fourth arriving unbudgeted |
| The **evidence-kind union against the wire** | `test_matchmaking_evidence_vocabulary.py` | A reshaped variant leaving `openapi.player.json` stale — the middle link of a three-artifact release |

The third one is new, and it closes a gap: **nothing regenerates the contract document from
the code.** Without it a reshaped evidence variant leaves a stale document, the drift check
compares that stale document against types generated from it, and the build stays green with
the client drawing the old shape. With it, a variant reshaped without `make gen-api` fails in
the backend job, and one regenerated without its client types fails in the player job — the
chain [ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)
always described, now closed at both ends and driven against a broken tree by
[`test-contract-drift.sh`](../../../.github/scripts/test-contract-drift.sh).

---

## 3. The SLOs, and the error budgets that are not computed

Restated from `scale-posture.md` §3 rather than re-derived, because two copies of a service
level is how a platform ends up holding itself to the looser one.

| | p50 | p99 | Holds |
| --- | ---: | ---: | --- |
| A ranked shortlist, server-side | 8 ms | **60 ms** | up to trigger 1 |
| A doubles line-up, server-side | 12 ms | **90 ms** | up to trigger 1, at `K ≤ 24` |
| Client tap → answer, end to end | 120 ms | **400 ms** | **a stated target, not an SLO** |

**End to end is a target and not an error-budgeted SLO**, because two of its three legs — the
device and the network — are not ours to hold, and an SLO whose misses are somebody else's is
a number nobody acts on.

**The error budgets are recorded and explicitly not computed.** §17's 99.9% / 99.5% need an
SLO pipeline this repository does not have. A 99.9% claim that nothing measures is exactly the
decoration this posture exists to refuse; when there is a pipeline, those are the numbers to
put in it. Nothing in this build computes an error budget, and nothing pretends to.

---

## 4. Deliberately not asserted anywhere in the suite

**No wall-clock bound. No p99. No empty-result rate.** Those are metrics, and a metric
asserted in a test suite on a shared runner is a mute waiting to happen: it goes red for the
runner's reasons, somebody widens it, and what survives asserts nothing at all.

What the suite asserts instead is arithmetic over **injected** samples — that a p99 of a
stated list is the stated number, that a duty cycle is time over wall-clock, that trigger 4
reproduces `scale-posture.md`'s own *25 000 players* from the constants — and that each record
is **emitted** carrying the fields its trigger is stated in. The committed diff artifact holds
no timing for the same reason: a file that moved because a runner was busy would go red for
reasons nobody can argue about, which is how a gate gets switched off.

---

## 5. What this build did not close, stated rather than implied

- **There is nowhere to read any of the three signals.** They emit; nothing consumes. This is
  the map's missing operational surface, and it now has instruments waiting on it rather than
  a plan to build them later.
- **Half the release gate is a signature**, and a signature can be given without reading. CI
  checks that the block is *there*; a block whose numbers are invented passes, and the suite
  asserts that it passes so nobody mistakes presence for truth. It is the weakest joint in
  ADR-0119 and it is named there rather than dressed.
- **The dense corpus is not a gate**, so a ruleset change is argued against 436 searches over
  a launch-sized market and not against a year-one city. The comparison is sound at either
  size (ADR-0121); what the thin corpus buys less of is *rare arms*, which is what the
  adversarial tail exists for and why its block is printed separately.
- **No weight change on this platform is justified by a measured outcome** until the outcome
  half of the telemetry chain exists. Every release until then is argued from a diff and from
  search-side rates — strictly more than *"I think vibe should be 24"*, and strictly less than
  the experiment §11 promised.
