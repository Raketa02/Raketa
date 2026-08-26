# The scale posture

**What the matchmaking engine is designed for, what is a configuration-and-capacity change,
and what would be a rewrite.**

Produced by [The scale posture](https://github.com/Raketa02/Raketa/issues/165) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
Every number here is **measured**, not restated — the harness and the raw runs are in
[`docs/research/matcher-scale-in-python.md`](../../research/matcher-scale-in-python.md)
(branch `research/matcher-scale`), captured for
[#161](https://github.com/Raketa02/Raketa/issues/161).

**The decisions live in ADRs; this file is the set of commitments to check work against.**
The partition, the two triggers and the multi-country commitment are
[ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md); where the matcher
runs at all is [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md).

> **Ratios transfer; absolute milliseconds do not.** Everything was measured on an Apple M3
> Max running CPython 3.11.6 — the version `Dockerfile.prod` and `ci.yml` both pin. A
> performance core there is worth roughly two to three small cloud vCPUs, so every measured
> figure below is a **floor**, and the derated column is what to hold the deployment to.

---

## 1. The size of the problem

| Quantity | Value |
| --- | --- |
| Players in a launch city | 10³ – 10⁴ |
| Candidate rows | ~2.5 × players (§17) — **write every threshold in rows, never in players** |
| Bytes per row, `__slots__` objects | **782** (measured; §7.2's 160 is wrong three different ways) |
| Bytes per row, `array`-packed columns | **43** |
| Whole index, 50 000-player city | **98 MB per worker** |
| Searches at peak (Thursday evening) | 1 – 20 / s (§17) |
| One 50 000-player city search | **2.79 ms** |
| Scoring duty cycle at §17's peak | **0.07** |

At §17's peak the engine uses seven percent of one event loop. **The load the architecture
would be separated to isolate does not exist**, which is what ADR-0093 rests on and what the
measurement confirms.

## 2. The cost of a search, in CPython

§17's table is a Go budget and does not transfer. This one does.

| Stage | M3 Max | Derated (×2–3) |
| --- | ---: | ---: |
| Generate — scan the sport bucket, box test | ~0.6 ms | 1.2 – 1.8 ms |
| Fit — eight terms over the survivors | ~2.4 ms | 4.8 – 7.2 ms |
| Group objective — doubles, `K = 24` | ~8.2 ms | 16 – 25 ms |
| Serialise — `orjson` | ~0.13 ms | 0.3 – 0.4 ms |
| **A ranked shortlist, end to end in-process** | **~2.8 ms** | **5.6 – 8.4 ms** |
| **A doubles line-up, end to end in-process** | **~11.4 ms** | **23 – 34 ms** |

Two things in that table are worth reading twice.

**The bounding box is not the cost.** Rejecting a row costs **18.5 ns**; a row that survives
costs **1.00 µs**. Four fifths of a search is the eight terms, which is why §9.2's suggested
geo-cell bucket map buys 4–17% and is struck (§7 below), and why bucketing by **sport** — a
4× cut in rows scanned — is the partition that actually pays.

**Serialisation is the one stage where Python beats the document's Go budget**, by 8.5×,
because `orjson` is already a backend dependency: 0.035 ms against §17's 0.300 ms. The
matcher's routes return `ORJSONResponse`, not FastAPI's default `JSONResponse` — worth 0.26 ms,
a tenth of a search, for one import.

## 3. The SLOs, and the population they hold at

**An SLO with no population attached cannot be missed.** §17 proposes its numbers off a
"< 1 ms total" cost table; in CPython on a small vCPU the scoring p99 alone is ~34 ms, which
is 57% of the search budget rather than the 60× headroom the table implies. The numbers still
stand — but they stand **up to trigger 1**, and trigger 1 is what defends them.

| | p50 | p99 | Holds |
| --- | ---: | ---: | --- |
| A ranked shortlist, server-side | 8 ms | **60 ms** | up to trigger 1 |
| A doubles line-up, server-side | 12 ms | **90 ms** | up to trigger 1, at `K ≤ 24` |
| Client tap → answer, end to end | 120 ms | **400 ms** | **a stated target, not an SLO** |

**End to end is a target and not an error-budgeted SLO**, because two of its three legs — the
device and the network — are not ours to hold, and an SLO whose misses are somebody else's is
a number nobody acts on.

**The error budgets are recorded and explicitly not yet computed.** §17's 99.9% / 99.5% need
an SLO pipeline this repository does not have. A 99.9% claim that nothing measures is exactly
the decoration this posture exists to refuse; when there is a pipeline, these are the numbers
to put in it.

**Index staleness is not in this table.** §17 (2 s p50 / 15 s p99) and §18 (serve normally
under 15 minutes, flag under 24 hours, **refuse** past 24 hours) are two different budgets
wearing one name, and reconciling them belongs to
[The matcher's picture of the city](https://github.com/Raketa02/Raketa/issues/173), which owns
freshness.

## 4. The two triggers, and the two instruments

The thresholds are [ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md),
which amends ADR-0093's prose versions. In short:

| Trigger | Fires at | Today |
| --- | --- | ---: |
| **1** — request latency contends with scoring | p99 of one scoring call > **20 ms**, or duty cycle > **0.25**, on one worker over 15 min | 11.4 ms / 0.07 |
| **4** — the index no longer fits beside the API | `bytes_per_row × rows × workers × 2` > **50%** of the container memory limit | ~80 000 rows on four workers of a 1 GB container |

**Both ship instrumented in the first build**, as fixed-name structured log records:

- a **histogram around the scoring call**;
- an ADR-0092 `PeriodicJob` that **measures its own oversleep** — the event-loop lag monitor;
- the **trigger-4 arithmetic recomputed at every index load**, from the actual
  `GUNICORN_WORKERS` and the actual cgroup limit, warning and never refusing.

A trigger that requires somebody to go and measure fires late, which is the same disease as a
claim with no trigger.

**One thing that is not a trigger and belongs beside them: the garbage collector.** One
automatic gen-2 collection over a live index cost **57.9 ms stop-the-world** — roughly thirty
times the search it interrupted — and pushed an unrelated request's max to 65 ms.
`gc.freeze()` after the index loads cuts four collections to **1.1 ms total, 0.4 ms max**.
Without it the matcher's p99 is set by the collector rather than by the algorithm. The
mechanics belong to [#173](https://github.com/Raketa02/Raketa/issues/173); the number belongs
here, so nobody has to rediscover it.

## 5. The escalation ladder, before any reversal

Each rung is measured to work, and they are taken in this order. **Reversing ADR-0093 is
below the last rung, not above the first.**

| Rung | Buys | Cost |
| ---: | --- | --- |
| 1 | Bucket by `(sport)`, then `(sport, cell)` | **4×** on rows scanned; the cell key is derived (ADR-0101) |
| 2 | Equirectangular distance instead of haversine | **13%** — haversine is 188 ns and 23% of the term loop; equirectangular is 81 ns |
| 3 | Cap the candidate block | bounded work per search, at the cost of a stated truncation |
| 4 | `ProcessPoolExecutor` whose workers hold a **resident** index | loop-lag p99 back to 0.82–0.94 ms, for +0.7 ms of latency |

**Two measured dead ends, recorded because they are the first things anybody reaches for:**

- **A thread offload makes it worse.** The GIL follows the work; loop-lag p99 degraded in all
  three shapes tried.
- **A process pool that is *shipped* the candidate block is worse than doing nothing.** 3 048
  rows pickle to 658 KB and **5.3 ms of `pickle.dumps` on the event loop** — more than the
  search it was meant to move. Only the resident-index shape in rung 4 survives.

**The memory ladder is separate and has one rung:** `array`-packed columns, **43 bytes a row**,
which genuinely share across forked workers (5 MB per worker instead of 108) and cost **23% on
the scan**. They are the answer to **trigger 4** and never to trigger 1.

## 6. `K = 24`, and why it is not "just a config change"

§9.9 says `K` — the candidate cap for the doubles enumeration — *"moves; it is a config change,
not a rewrite."* **That is true in Go and false in Python.** The enumeration is cubic in `K`
with a flat per-combination cost:

| `K` | Combinations | M3 Max | Derated |
| ---: | ---: | ---: | ---: |
| 15 | 1 365 | 2.08 ms | 4 – 6 ms |
| **24** | **6 072** | **8.2 ms** | **16 – 25 ms** |
| 32 | 14 880 | 20 ms | 40 – 60 ms |
| 48 | — | 69 ms | 138 – 207 ms |
| 64 | — | 169 ms | — |

At `K = 24` the group objective is 27% of the 90 ms line-up budget. At `K = 32` the budget is
gone.

**So `K = 24` is a ruleset constant with an engine-side ceiling that refuses to load a ruleset
exceeding it.** Ruleset because ADR-0093 names *a cap* as ruleset material; the ceiling because
otherwise the one number that can destroy the latency budget ships as "just configuration" —
and §11 already establishes that a malformed ruleset refuses to load rather than falling back.
Above `K` eligible candidates, truncate to the top `K` by Fit.

## 7. What is deliberately not built now

**Absence is only distinguishable from oversight when it has a number beside it.** Ten
entries, and none of them is waiting on permission.

| Not built | Why, measured |
| --- | --- |
| A distributed scoring cluster | §17 — for a problem measured in tens of megabytes and 7% of one event loop |
| A spatial index | The box rejects at 18.5 ns a row; four fifths of a search is the terms |
| A search-engine dependency | Same; and sqlite in memory, indexed, no socket, took **2.80 ms** against 2.80 ms for the whole in-memory search |
| §9.2's geo-cell bucket map **as a speed measure** | Buys **4–17%**. It survives only as the *partition* mechanism (rung 1), which is a different job at a different scale |
| `array`-packed columns | 43 B/row but **23% slower**. Held as trigger 4's answer |
| A thread offload | Measured **worse** — the GIL follows it |
| A process pool that ships the candidate block | **5.3 ms of pickling on the event loop** |
| A `shard_key` field | Nothing produces one, and it is derivable from the area. A schema test asserts it absent ([ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md)) |
| A second `LocationArea` per player | `player_profile`'s question, not the matcher's. Row identity is `(player, sport)` and stays that way |
| A load balancer routing by city | That **is** the extracted service, and therefore trigger 2 rather than a configuration change |
| A metrics stack | Structured logs are the instrument, so the two trigger instruments wait on nothing |

## 8. What multi-country actually costs

The map targets **multi-city within one country**, built so that multi-country is a
configuration-and-capacity change and never a rewrite. Walked against the code, almost nothing
in the matcher knows what a country is:

- the **cell partition** is geographic and works at any latitude;
- **equirectangular distance** already carries its `cos(lat)` correction;
- the **availability grid is timezone-free by construction** — `availability.py` records that
  *"nothing in this module has a duration, a date or a timezone in it"*.

So multi-country is **trigger 4 plus one clock parameter**:

- **The capacity half is trigger 4, and its answer already exists.** Ten cities is 978 MB per
  worker as objects and **54 MB** as packed columns. That is the posture's promise being kept.
- **The clock half is [ADR-0100](../../adr/0100-challenge-window-derived-never-chosen.md)'s
  derived window** — `TODAY | TOMORROW | WEEKEND | THIS_WEEK` is a rule with thresholds
  evaluated against *now*. **The zone is an input to the derivation, never `Europe/Warsaw`
  baked into it.** One parameter today; a rewrite if it is skipped.

**And the non-commitment, stated so it is not read into the promise:** currency, language and
legal data residency are not matcher concerns, and nothing here says anything about them.
