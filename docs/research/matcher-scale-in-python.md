# What scoring in Python actually costs, and where the in-process design breaks

Research output for [`Raketa02/Raketa#161`](https://github.com/Raketa02/Raketa/issues/161), under the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**This file decides nothing.** [The scale posture](https://github.com/Raketa02/Raketa/issues/165)
decides what to do about these numbers, and
[The matcher's picture of the city](https://github.com/Raketa02/Raketa/issues/173) decides how
a search reads the index. The job here is to replace the design document's **Go** performance
claims with **measured CPython** ones, and to put a number on the two
[ADR-0093](adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) reversal triggers
this ticket exists to make measurable.

Every claim carries one of three tags:

| Tag | Means |
| --- | --- |
| **[MEASURED]** | Run on the hardware named below, by the harness in [`bench/matcher-scale/`](bench/matcher-scale/). Every table quoted here is from the captured run in [`bench/matcher-scale/results.md`](bench/matcher-scale/results.md) |
| **[ESTIMATED]** | Arithmetic on measured inputs, or a projection. The inputs are shown so the estimate can be disagreed with |
| **[NOT MEASURED]** | Named so the gap is not silently filled later |

## Where these numbers came from

| | |
| --- | --- |
| Machine | Apple M3 Max, 14 cores (10 performance + 4 efficiency), 36 GB, macOS 15.7.1 |
| Python | CPython **3.11.6**, arm64 — the version `Dockerfile.prod` and `ci.yml` both pin |
| Libraries | fastapi 0.136.1 and uvicorn 0.47.0 (the versions `backend/pyproject.toml` pins), orjson 3.12, numpy 2.4.6 |
| Native floor | `cc -O2` (Apple clang), the same loop in C, called through `ctypes` |

**What a laptop measurement predicts, and what it does not.**

- **It predicts ratios well.** Objects versus packed columns versus numpy versus C, one term
  against another, `gc.freeze()` on against off, thread offload against process offload —
  these are properties of CPython and of the code, not of the machine, and they will hold on
  a Graviton or an x86 Fargate task.
- **It does not predict absolute latency on the production instance.** An M3 Max performance
  core is roughly two to three times a vCPU of the small instance a one-developer product
  actually deploys on, and ECS adds CPU-quota throttling a laptop has no equivalent of.
  **Treat every absolute millisecond below as a floor and multiply by two to three for a small
  cloud instance** — then measure it there, because that multiplier is itself an estimate.
  [ESTIMATED]
- **It does not predict tail behaviour under a noisy neighbour**, nor anything about network
  or database latency, neither of which is in the scoring path anyway.
- The load driver runs on the same machine as the server, so client cost sits inside the
  request-latency figures. The in-process event-loop lag monitor exists precisely so the
  headline item-2 numbers do not depend on the client.
- **Single-event figures vary run to run.** The gen-2 GC pause is one event in a twenty-second
  window; it measured 58 ms in the captured run and 78 ms in an earlier one. The *ratio* to
  the frozen case (a hundredfold and more) is stable; the absolute is not.

---

## Verdict — read this first

> **Scoring in CPython costs roughly thirty times what the same loop costs in C, and the
> document's sub-millisecond search becomes 2.8 ms for a 50 000-player city — which is still
> nowhere near a problem, because §17's peak of twenty searches a second is a 7% duty cycle on
> one event loop. The in-process decision survives the measurement comfortably.**
>
> **Three things do not survive it:**
>
> 1. **Trigger 4 is already wrong by an order of magnitude.** ADR-0093 reasons with §7.2's
>    32 MB. The same index as plain Python objects is **98 MB**, as a naively-spelled
>    dataclass with `uuid` and `datetime` fields it is **241 MB**, and it is held **once per
>    gunicorn worker** with no copy-on-write relief. Four workers on a 1 GB container reach
>    the trigger at about **32 000 players**, not at "several cities". The fix is a
>    representation change, not a service: `array`-packed columns are **44 bytes a row**,
>    below the Go figure the ADR trusted, and they *do* share across forked workers.
> 2. **The largest latency event in the process is not the search — it is the garbage
>    collector.** One automatic gen-2 collection with a 125 000-row object index live costs
>    **58 ms** stop-the-world, and it lands on the event loop. `gc.freeze()` after loading the
>    index takes it to **0.4 ms**. That is one line, and nobody is going to think of it later.
> 3. **The doubles enumeration is the one place the document's constants do not transfer.**
>    C(15,3) x 3 is "tens of microseconds" in Go and **2.08 ms** in CPython — as expensive as
>    the entire candidate scan. Worse, it is cubic in `K`, so §9.9's "`K` moves, it is a config
>    change, not a rewrite" is false in Python: `K` 16 → 32 costs **10x**, and `K` = 64 costs
>    **169 ms**, which on its own would fire trigger 1.
>
> **And one thing the measurement settles cheaply:** if trigger 1 ever does fire, the first
> move is not extracting a service. A `ProcessPoolExecutor` whose workers hold their own copy
> of the index leaves event-loop lag at **0.9 ms p99** for +0.7 ms of latency. But the worker
> must *hold* the index: shipping the candidate block to it costs **5.3 ms of pickling on the
> event loop** and makes everything worse than doing the work inline.

### The headline numbers

| Quantity | Document (Go) | Measured (CPython 3.11.6) | Item |
| --- | --- | --- | --- |
| One search, 50 000-player city, one sport (31 250 rows, 2 386 in range) | **< 1 ms** total (§17) | **2.79 ms** plain objects · 3.44 ms packed columns · **0.22 ms** numpy · **0.09 ms** C | 1 |
| Rejecting a row on the bounding box | ~50 µs for the whole scan (§17) | **18.5 ns/row** → 0.58 ms for 31 250 rows | 1 |
| Eight terms on one surviving candidate | ~0.4 µs implied (§17) | **1.00 µs** (0.83 µs of it arithmetic) | 1 |
| Python multiplier over the same loop in C | — | **~30x** plain objects · **2.4x** numpy | 1 |
| Event-loop lag p99 at §17's peak (20 searches/s, 31 250 rows) | n/a — no event loop in the Go design | **6.1 ms** | 2 |
| Rate at which one worker collapses | n/a | **~300 searches/s** at 31 250 rows; **~75/s** at 125 000 | 2 |
| Thread offload | n/a | **does not help** — loop-lag p99 got worse, not better | 2 |
| Process offload, worker holds the index | n/a | **0.9 ms loop-lag p99**, +0.7 ms latency | 2 |
| Process offload, block is pickled across | n/a | **5.3 ms of pickle on the loop**, 658 KB, 15.4 ms total | 2 |
| Bytes per candidate row | **~160** (§7.2) | **782** objects · **1 929** naive dataclass · **43** packed | 3 |
| Whole 50 000-player index | **32 MB** (§7.2) | **98 MB** objects · **5 MB** packed — **per worker** | 3 |
| Gen-2 GC pause with the index live | n/a | **58 ms** → **0.4 ms** after `gc.freeze()` | 3 |
| Rebuild, 50 000 players, projection CPU only | **< 5 min** target (§7.4) | **1.0 s** — 959 000 events/s, one core | 5 |
| Doubles, C(15,3) x 3 pairings | **tens of µs** (§9.9) | **2.08 ms** plain · **0.05 ms** numpy | 6 |
| `CandidateSource` port, per search | n/a | **54 ns** — 0.002% of a search | 7 |
| §16 response, 20 seats x 8 terms | ~300 µs (§17) | 0.09 ms build + **0.035 ms** `orjson` | 7 |

---

## 1. The Python multiplier

**The work measured** is §9.2's Stage 2 and §9.3's Stage 3 as one loop, implemented the way a
competent implementer would: every searcher-side constant hoisted out of the loop, no
allocation for a rejected row, sport test then bounding box then index-local gates then
haversine then the eight terms. Evidence objects are *not* built in the hot loop — only the
shortlist gets them, and that cost is measured separately in item 7. The synthetic population
is a Kraków-shaped city (σ 9 km) carrying the §7.2 field list.

### Cost against row count [MEASURED]

Milliseconds for one search. `in range` is how many rows survive the box *and* the ring, which
is what the eight terms actually run over.

| shard rows | in range | (a) plain objects | (b) packed columns | (c) numpy, whole shard | (c) numpy, block only | C via `ctypes` | geo-cell buckets |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 500 | 206 | 0.231 | 0.287 | 0.068 | 0.058 | 0.010 | 0.243 |
| 12 500 | 985 | 1.125 | 1.398 | 0.125 | 0.100 | 0.038 | 1.005 |
| **31 250** | **2 386** | **2.790** | 3.443 | 0.224 | 0.170 | 0.094 | 2.388 |
| 125 000 | 9 602 | 12.174 | 14.095 | 0.832 | 0.570 | 0.607 | 10.057 |
| 250 000 | 19 330 | 26.486 | 28.747 | 1.692 | 1.110 | 1.558 | 21.347 |
| 1 000 000 | 76 947 | 111.137 | 113.382 | 6.862 | 4.491 | 6.939 | 107.051 |

31 250 rows is one sport of a 50 000-player city at §17's 2.5 rows per player; 125 000 rows is
that city's whole index, i.e. what a scan costs if it is not bucketed by sport first.

**Four things to read off it.**

- **The multiplier over native is 30x** at the realistic size (2.790 ms against 0.094 ms). Go
  sits somewhere between the C column and twice it, so the document's "under 1 ms" was itself
  conservative — and the honest Python number is **2.8 ms**, not the 30 ms a naive "Python is
  50x slower" rule of thumb predicts. The reason is that most of the scan is *rejection*, and
  rejecting a row is three attribute loads and two comparisons.
- **`array`-packed columns are slower, not faster** — 3.44 ms against 2.79 ms, about 23%
  worse. Every element access re-boxes a C float into a Python `float`, and the index
  arithmetic is not free. **Packed columns are a memory answer (item 3) and never a speed
  one.** Worth stating loudly, because the instinct is that they would be both.
- **numpy is the real escape route in pure-Python terms: 12x over the whole shard, improving
  as the shard grows** (16x at 1 M rows). At 1 M rows numpy matches C, because C is running a
  scalar loop and numpy is running SIMD over the box test.
- **The bounding-box early-out is not where the time goes.** Rejecting all 31 250 rows costs
  **0.58 ms** (18.5 ns a row); the 2 386 survivors cost **2.38 ms** (1.00 µs each). Four
  fifths of a search is the eight terms.

### Where the microsecond per candidate goes [MEASURED]

Each term timed in isolation over the same 3 048-row block, with the bare `for` loop
subtracted.

| §9.3 term | ns per candidate | share |
| --- | ---: | ---: |
| 8 Distance — **haversine** | **188** | **23%** |
| 5 Availability overlap | 132 | 16% |
| 7 Social vibe | 126 | 15% |
| 6 Playing style | 124 | 15% |
| 4 Reliability (six strands live) | 108 | 13% |
| 2 Predicted balance | 96 | 12% |
| 1 Level fit | 48 | 6% |
| 3 Intent alignment | 5 | 1% |
| **sum of the eight** | **826** | 100% |
| *8 Distance — equirectangular instead* | *81* | *(saves 13% of the loop)* |

Two things fall out. **Distance is the most expensive term and the cheapest to fix**: at metro
scale an equirectangular approximation is accurate to well under a hundred metres and costs
81 ns instead of 188. §9.3.8's soft edge already spans 45% of the radius, so no plausible
projection error changes a score. Second, **intent alignment really is the cheapest strong
term in the engine** — 5 ns, one list index — exactly as §9.3.3 claims, now with a number.

### At what row count does a search stop fitting inside a request? [ESTIMATED]

Three answers, because "fast enough" means three different things. Extrapolated from the
measured line, which is linear at **89 ns per shard row** of mixed reject-and-score work at
this in-range fraction.

| Constraint | Budget | Plain objects | numpy |
| --- | --- | ---: | ---: |
| §17's own server-side p99 for `POST /v1/searches` | 60 ms | **~670 000 rows** | ~8 M rows |
| Not visibly stealing the loop from sign-in (item 2's threshold) | 20 ms | **~220 000 rows** | ~2.8 M rows |
| §17's p50 of 8 ms | 8 ms | **~90 000 rows** | ~1.1 M rows |

Take a third to a half of those row counts for a small cloud instance. [ESTIMATED]

**So the honest ceiling for the plain-object implementation is a shard of roughly 220 000 rows
— about 88 000 players at 2.5 rows each — and that is the same number §9.2 already guesses at
("if a shard ever exceeds ~200 000 rows").** The document arrived at it for a different reason
and is right anyway.

### What a coarse geo-cell bucket map buys [MEASURED]

2 km cells keyed `(sport, cell_y, cell_x)`; a search visits only the cells its box touches.

| shard rows | linear scan | bucket map | saved |
| ---: | ---: | ---: | ---: |
| 31 250 | 2.790 ms | 2.388 ms | 14% |
| 125 000 | 12.174 ms | 10.057 ms | 17% |
| 1 000 000 | 111.137 ms | 107.051 ms | 4% |

**It is not worth its complexity at any size, and the reason generalises.** A bucket map can
only remove the 18.5 ns-a-row rejection work; it cannot touch the 1.00 µs-a-candidate scoring
work, and the scoring work is 80% of the search. **Adding a spatial index to make scoring
faster is optimising the wrong half.** §9.2's advice — "if a shard ever exceeds ~200 000 rows,
a coarse geo-cell bucket map is the cheap next step" — is a Go instinct: in Go, where the terms
are nearly free, rejection *is* the cost and the advice is right. In Python it is not.

**What would actually help, in order of return on effort:**

1. **Bucket by `(shard, sport)` first** — not spatial, just a dict of lists. Turns a
   125 000-row scan into a 31 250-row one: **4x**, for one line at index-build time.
2. **Equirectangular distance** — 13% of the loop, no accuracy anyone can observe.
3. **Cap the candidate block.** §9.9 already caps the doubles pool at `K` = 16; nothing caps
   the singles fit stage. A cheap pre-rank on level distance alone, then eight terms on the
   top few hundred, converts the dominant cost into the cheap one. This is a *product*
   decision — it changes which candidates get scored — and belongs to
   [#173](https://github.com/Raketa02/Raketa/issues/173), not here.
4. **numpy over the candidate block only** — 0.17 ms against 2.79 ms. But numpy is not a
   backend dependency, and adding one to solve a 2.8 ms problem is exactly the tax ADR-0093
   refused elsewhere. **Not recommended now**; recorded as the escape route with a price on it.
5. **A C or Rust extension.** The C column is the ceiling: 0.094 ms, 30x. It also shows the
   cost — a compiled artefact in the image, a second toolchain in CI, and a purity fence
   (`.importlinter`'s `engines-are-pure`) that would have to reason about a binary.
   **The gap between numpy and C is 2.4x; the gap between plain Python and numpy is 12x.**
   There is no size of this product at which the C extension is the right *first* move.

---

## 2. The event loop, and the trigger it defines

This item did not exist under the Go design, and ADR-0093 is right that it is the most
consequential thing the decision created. Measured against a real `uvicorn` worker running a
real FastAPI app, with two instruments: a `/ping` endpoint that does nothing — standing in for
sign-in and profile traffic — driven at 50 rps over a keep-alive socket, and, the honest one,
**a task inside the server that wants to wake every 5 ms and records how far it overslept**.
That second number is event-loop starvation with no client in the way.

### At §17's stated load [MEASURED]

31 250-row shard, one uvicorn worker, 8 s per case. Milliseconds.

| scoring mode | searches/s | loop-lag p99 | loop-lag p99.9 | loop-lag max | ping p50 | ping p99 | search p50 | search p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| none (baseline) | 0 | 2.80 | 45.10 | 54.98 | 1.48 | 2.86 | — | — |
| inline in `async def` | 1 | 1.97 | 11.35 | 14.06 | 1.24 | 2.36 | 7.8 | 15.7 |
| inline in `async def` | 5 | 10.35 | 15.34 | 18.82 | 0.90 | 6.03 | 7.7 | 23.6 |
| inline in `async def` | **20** | **6.10** | 7.66 | 8.43 | 0.73 | **3.78** | 6.6 | 11.4 |
| `def` endpoint → thread pool | 1 | 2.96 | 11.95 | 17.27 | 1.03 | 2.97 | 11.7 | 21.6 |
| `def` endpoint → thread pool | 5 | 11.13 | 12.82 | 13.02 | 1.14 | 2.96 | 12.8 | 17.3 |
| `def` endpoint → thread pool | 20 | 7.83 | 9.62 | 10.73 | 0.74 | 3.77 | 7.6 | 12.3 |
| process pool, **worker holds the index** | 1 | **0.86** | 1.01 | 1.98 | 1.48 | 2.39 | 14.7 | 22.3 |
| process pool, **worker holds the index** | 5 | **0.82** | 1.33 | 2.11 | 1.36 | 2.52 | 15.5 | 17.6 |
| process pool, **worker holds the index** | 20 | **0.94** | 1.29 | 10.09 | 0.77 | 1.75 | 10.5 | 12.6 |
| process pool, **block is pickled across** | 1 | 12.02 | 30.75 | 40.71 | 1.47 | 3.62 | 36.4 | 60.9 |
| process pool, **block is pickled across** | 5 | 19.90 | 24.24 | 25.57 | 0.69 | 9.87 | 34.7 | 46.2 |
| process pool, **block is pickled across** | 20 | 11.58 | 22.83 | 26.64 | 0.55 | 5.54 | 20.0 | 37.7 |

The baseline row's p99.9 and max are a start-up artefact — the first few hundred milliseconds
of a fresh worker — and the process-pool rows show what an undisturbed loop actually looks
like: **sub-millisecond p99**.

**At §17's peak of twenty searches a second, an unrelated request's p99 is 3.78 ms against a
2.86 ms idle baseline, and its p50 does not move at all.** Nobody notices that. The in-process
decision is not close to trouble at the load the document sizes.

### Does a thread offload help? No. [MEASURED]

`def` instead of `async def` moves the work to Starlette's anyio thread pool, and the GIL
follows it there. Loop-lag p99 was **worse in all three cases** (2.96 against 1.97; 11.13
against 10.35; 7.83 against 6.10) and the search itself got slower (11.7 ms against 7.8 ms p50
at 1 rps) because of the hand-off. **The only thing the thread pool buys is that the blocking
arrives in 5 ms GIL slices rather than one lump** — which spreads the damage rather than
reducing it, and adds a context switch to every search.

`sys.setswitchinterval()` would make those slices finer; [NOT MEASURED], and it trades
throughput for smoother tails process-wide, which is a large side effect for a small win.

### Does a process offload help? Yes — but only one shape of it. [MEASURED]

- **Worker holds its own copy of the index**: loop-lag p99 **0.82–0.94 ms** at every rate. The
  event loop is completely protected. The search pays about +0.7 ms of IPC.
- **Candidate block is pickled and sent**: the block for one search is 3 048 rows and
  **658 KB**, and `pickle.dumps` of it takes **5.3 ms on the event loop** — more than scoring
  it inline. Loop-lag p99 reaches 19.9 ms and the search takes 15.4 ms.

**That asymmetry is the finding.** The escape hatch from trigger 1 is cheap and it works — but
only if the worker already has the data. A process pool that has to be *fed* the candidates is
strictly worse than doing nothing, and "feed the worker" is the shape somebody reaches for
first, precisely because it avoids duplicating the index. The cost of duplicating it is item 3,
and packed columns make it 5 MB a worker.

### Where the knee is [MEASURED]

`/ping` at 50 rps throughout; scoring inline; utilisation is offered load times the unloaded
single-call cost.

| shard rows | searches/s | offered util | loop-lag p99 | loop-lag max | ping p99 | ping p50 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 31 250 | 1 | 0% | 1.30 | 5.26 | 2.34 | 0.72 |
| 31 250 | 20 | 7% | 5.82 | 8.60 | 5.46 | 0.76 |
| 31 250 | 50 | 16% | 4.51 | 5.79 | 6.74 | 0.65 |
| 31 250 | 100 | 33% | 3.50 | 6.91 | 12.45 | 0.54 |
| 31 250 | 200 | **65%** | **50.18** | 65.54 | 24.26 | 3.56 |
| 31 250 | **400** | **131%** | **6 879** | 6 914 | **222** | **193** |
| 125 000 | 20 | 27% | 21.10 | 78.08 | 17.82 | 0.54 |
| 125 000 | 50 | **67%** | **56.05** | 80.81 | 20.13 | 0.43 |
| 125 000 | **100** | **133%** | **7 857** | 7 882 | **900** | **158** |

Two regimes, and very little in between:

- **Below saturation the damage is bounded by one search.** A trivial request's p99 rises
  roughly with the duty cycle and never much exceeds the duration of one scoring call, because
  that is the longest the loop can be held. p50 does not move — most requests miss the
  blocking window entirely.
- **The knee is at about two-thirds utilisation**, where loop-lag p99 jumps by an order of
  magnitude (3.50 ms at 33% → 50.18 ms at 65%). **Above `λ × D = 1` the queue runs away and
  the process is gone**: seven seconds of loop lag and a 193 ms p50 on an endpoint that does
  nothing. There is no graceful degradation and no back-pressure; uvicorn keeps accepting.

### The threshold for ADR-0093 trigger 1

> **Trigger 1 — *"request latency measurably contends with scoring"* — has fired when either
> of these is observed on one worker over a fifteen-minute window:**
>
> - **the p99 of one synchronous scoring call exceeds 20 ms**, or
> - **the scoring duty cycle — searches per second × mean scoring seconds — exceeds 0.25.**

Why those two numbers:

- **20 ms** is the measured bound on what one blocking call can add to an unrelated request's
  p99, and it is a third of §17's whole 60 ms server-side p99 budget for the search itself.
  Below it the contention is real but invisible; above it, sign-in grows a tail a human can
  feel. At §17's stated load the measured value is **6.6 ms p50 / 11.4 ms p99**, so there is
  roughly a 2x margin today.
- **0.25** sits just below the measured knee. At 33% offered utilisation loop-lag p99 was
  3.5 ms; at 65% it was 50 ms; at 100% the process is unrecoverable, and there is nothing in
  between to warn you. A quarter of one core spent on scoring inside the request process leaves
  no headroom for a spike. At §17's stated load the measured value is **0.07**.

**Both are instrumentable with what the harness already does:** a histogram around the scoring
call, and a `PeriodicJob`-style task measuring its own oversleep. Neither needs a profiler,
neither needs a load test, and **the engine should ship with both** — a trigger that requires
somebody to go and measure is a trigger that fires late.

**Trigger 1 firing should not by itself mean "extract the service."** The measured ladder is:
bucket by `(shard, sport)` (4x) → equirectangular distance (13%) → cap the candidate block →
process pool with a *resident* index (loop fully protected). Only after those is extraction the
answer, and only that last step is ADR-0093's reversal.

---

## 3. The snapshot, per worker rather than per instance

### Bytes per row [MEASURED]

`tracemalloc` around building 31 250 rows, which counts every object the allocator handed out
rather than just the container. The last column is the whole 125 000-row index of a
50 000-player city at §17's 2.5 rows per player.

| representation | bytes/row | 125 000 rows |
| --- | ---: | ---: |
| dataclass with `uuid.UUID`, `datetime`, `str` shard key — **the naive spelling** | **1 929** | **241 MB** |
| plain class with `__dict__`, 32 fields | 3 447 | 431 MB |
| `__slots__` class, the §7.2 field list — **what a careful implementer writes** | **782** | **98 MB** |
| `array`-packed columns (exact `itemsize × len`) | **43** | **5 MB** |
| numpy columns (exact `.nbytes`) | 46 | 6 MB |
| *§7.2's claim, for comparison* | *160* | *20 MB* |

**A note on §7.2's own arithmetic — a fifth numbering quirk to add to the four
[#156](https://github.com/Raketa02/Raketa/issues/156) lists.** §7.2 says 160 bytes a row and
"a city of 50 000 players across four sports is roughly 32 MB", which is 200 000 rows — every
player rated in all four sports. §17's own capacity table says candidate rows are **2.5 ×
players**, which is 125 000 rows and 20 MB. And §17's ceiling paragraph says "roughly 10⁶ rows
per instance (~200 MB)", which is 200 bytes a row. Three numbers, three assumptions.
**Write the threshold in rows, never in players.**

### The multiplier, which is the real finding [MEASURED]

`backend/docker/api/startup.prod.sh` runs gunicorn with `--workers "${GUNICORN_WORKERS:-1}"`
and **no `--preload`**. So today the multiplier is 1 — and the day somebody sets
`GUNICORN_WORKERS=4` to use the instance's cores, the index memory quadruples silently.

| workers/instance | `__slots__` objects | packed columns |
| ---: | ---: | ---: |
| 1 | 98 MB | 5 MB |
| 2 | 196 MB | 11 MB |
| 4 | **391 MB** | 22 MB |
| 8 | 782 MB | 44 MB |

**And `--preload` does not rescue it.** Forking four workers after building the index, each one
then scanning it, measured by USS — memory that would be freed if that process died:

| representation | `gc.freeze()` before fork | parent USS | per-worker USS | total (parent + 4) |
| --- | --- | ---: | ---: | ---: |
| `__slots__` objects | no | 110 MB | 108 MB | **544 MB** |
| `__slots__` objects | **yes** | 110 MB | **109 MB** | **545 MB** |
| packed columns | no | 15 MB | 5 MB | **36 MB** |
| packed columns | yes | 14 MB | 6 MB | 36 MB |

**Copy-on-write buys nothing for an object index, and `gc.freeze()` does not change that.**
Worth being precise, because `gc.freeze()` is usually *recommended* for copy-on-write: it stops
the collector's mark phase writing to every object's GC header, but it cannot stop the
interpreter incrementing a refcount every time the scan reads an attribute, and that dirties
the same pages. One pass over the index un-shares essentially all of it. **For packed columns
the payload lives in one large buffer that scanning never writes to, and the sharing is real —
5 MB a worker instead of 108.**

`gc.freeze()` is still worth doing, for the next reason rather than this one.

### The garbage collector, which is the biggest single latency event [MEASURED]

A gen-2 collection walks every container object in the process, and the candidate index is the
largest pile of them: 125 000 rows makes 174 748 tracked objects.

| | median explicit `gc.collect(2)` |
| --- | ---: |
| 125 000-row object index live | **34.6 ms** |
| after `gc.freeze()` | **0.0 ms** |

And in the running server, with the *automatic* collector doing it — 20 searches/s plus
50 pings/s for 20 s against a 125 000-row index:

| `gc.freeze()` | gen-2 collections | gen-2 total | gen-2 max | loop-lag p99 | loop-lag **max** | ping **max** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no | 1 | 57.9 ms | **57.9 ms** | 18.4 ms | **84.4 ms** | **64.5 ms** |
| **yes** | 4 | 1.1 ms | **0.4 ms** | 18.5 ms | **28.7 ms** | 31.1 ms |

**One automatic gen-2 collection in twenty seconds, costing 58 ms, on the event loop** — an
order of magnitude more than the search it interrupted, and the single worst latency event
anywhere in this measurement. It is larger in the server than the 34.6 ms explicit figure
because a live FastAPI worker holds the framework's object graph and a search's worth of
garbage on top of the index. Every search allocates a shortlist and thousands of tuples, so the
gen-0 → gen-1 → gen-2 cascade fires on a schedule set by search traffic; `gc.get_threshold()`
is `(700, 10, 10)`.

> **Call `gc.freeze()` immediately after the index is loaded, and after every refresh.** One
> line. It moves the index into the permanent generation so no later collection scans it.
> Without it the matcher's p99 is set by the collector rather than by the algorithm, and
> [#173](https://github.com/Raketa02/Raketa/issues/173)'s freshness design ends up accounting
> for a 58 ms hiccup it did not cause.

### Refresh headroom [MEASURED]

§15.3's mechanism — build a new immutable snapshot, swap a pointer — is discarded by ADR-0093
as a *service* design, but the shape still applies inside the module. In Python:

- RSS holding one 125 000-row object index: **357 MB**
- RSS while old and new are both live: **461 MB** (+104 MB, i.e. **2x the index**)
- wall clock to build the replacement in-process: **0.90 s**, and the event loop is blocked for
  all of it unless it is built elsewhere
- after dropping the old copy the allocator returns 102 of the 104 MB

**A refresh therefore needs 2x the index in headroom and the better part of a second of pure
CPU.** With plain objects and four workers that is a 782 MB transient peak on a 391 MB steady
state; with packed columns it is 11 MB. An in-flight search holding the old snapshot extends
the window but does not raise the peak — the peak is set by the build, not by the readers.

One thing transfers for free: a Python "atomic pointer swap" is a module-level or attribute
rebind, which is atomic under the GIL. `self._snapshot = new_snapshot` genuinely is safe, and a
reader that already grabbed the old one keeps it for the life of its search. **§13's determinism
argument survives the port intact** — the index cannot move under a running search.

### The threshold for ADR-0093 trigger 4

> **Trigger 4 — *"the index no longer fits comfortably in memory beside the API"* — should be
> written in rows and workers, not megabytes, and it has fired when**
>
> **`bytes_per_row × rows × GUNICORN_WORKERS × 2` (the refresh peak) exceeds 50% of the
> container's memory limit.**
>
> For the shapes measured here, on a 1 GB container:
>
> | representation | 1 worker | 4 workers |
> | --- | ---: | ---: |
> | naive dataclass (1 929 B) | 130 000 rows (~52 000 players) | 32 000 rows (~13 000 players) |
> | `__slots__` objects (782 B) | **320 000 rows (~128 000 players)** | **80 000 rows (~32 000 players)** |
> | packed columns (43 B) | 5.8 M rows | 1.5 M rows |

[ESTIMATED] from the measured bytes/row, the measured 2x refresh peak, and a 50% budget so the
process has room left to serve requests.

**The consequence for the ADR is direct.** ADR-0093 says "§7.2 sizes a 50 000-player city at
32 MB; several cities at gigabyte scale expires the argument" and concludes "none of the four
can fire this year." With plain Python objects and four workers, **one city of 32 000 players
reaches the trigger** — and 32 000 players is not "several cities", it is the top of §17's own
10³–10⁴ range plus one good year.

**But the trigger is answered by a representation change, not by a service.** Packed columns
put the same index at 43 bytes a row — *below* the 160 the Go design assumed — and make
`--preload` sharing real. The price is the 23% slower scan from item 1: 2.79 ms → 3.44 ms.
**That trade is worth taking the moment `GUNICORN_WORKERS` goes above one, and not before.**
The decision to record is: *the index representation is an implementation detail behind the
`CandidateSource` port (item 7), chosen by the memory budget; the first version is plain
`__slots__` objects.*

---

## 4. Sharding by metro

### What routing on a shard key requires now [MEASURED + ESTIMATED]

In-process, routing on a shard key is a dict lookup: tens of nanoseconds, indistinguishable
from nothing. §17 treats "shard by `shard_key` and route on it at the backend" as free, and *as
a lookup* it is.

**What is not free is what a shard key does to deployment, and ADR-0093 makes that harder
rather than easier.** As a separate service, shards can be pinned to instances and a router in
front sends a search to the instance holding the shard. As a module inside the API, **every API
instance is also a matcher instance**, and an API instance must serve sign-in, profile and
onboarding for every city. So either:

- **every worker holds every shard** — the item-3 multiplier becomes `shards × workers`, and
  four cities on four workers is 1.6 GB of `__slots__` index per instance; or
- **shards are pinned to instances** — and the load balancer must route by city, which means
  the backend is no longer horizontally uniform, sign-in traffic has to be routed by a key the
  request does not carry, and one city's instance failing takes down that city's *sign-in* and
  not merely its matching.

**The second option is ADR-0093's extracted service arriving through the back door**, and it is
worth naming in [#165](https://github.com/Raketa02/Raketa/issues/165): **multi-city under
ADR-0093 fires trigger 4, not trigger 2.** The map's stated target — multi-city, one country,
with multi-country as "a config-and-capacity change" — is affordable with packed columns
(43 B/row: ten cities of 50 000 players is 54 MB a worker) and is not affordable with plain
objects (978 MB a worker). **Item 3's representation choice is therefore also the multi-city
decision.**

### The player who plays in two cities [ESTIMATED — a design question, not a measurement]

The document never mentions them, and §7.2's schema cannot express them: `shard_key` is a
single `string` on a row keyed `(player, sport)`.

Three shapes, with the memory arithmetic at a measured 782 bytes an object row:

| shape | identity | what a search from either city sees | cost |
| --- | --- | --- | --- |
| **one row, one shard** (§7.2 as written) | `(player, sport)` | they exist in one city, invisible in the other | 0 |
| **one row per shard** | `(player, sport, shard)` | correct in both | +782 B per extra city per sport, **and two rows that can disagree** |
| **one row, many buckets** | `(player, sport)`; the row appears in each shard's scan list | correct in both | **+8 bytes** — one more reference in a list |

**Only the third keeps the invariants.** A candidate's identity must stay `(player, sport)`,
because everything else the matcher owns is keyed on the player: the interest ledger ("Ania
said yes to Kuba" is not per-city), the exposure ledger (§14.2's "shown to nobody this week"
must not reset by crossing a boundary), suppression, and the newcomer window. Duplicating the
row duplicates all of those or lets them disagree, and §10's degradation rules assume one row
per player per sport.

The recommendation for [#173](https://github.com/Raketa02/Raketa/issues/173):

- **`shard_key` becomes `shard_keys`, a small set on the row** — a home metro plus any metro the
  player has opted into. It is still one row.
- **The index is a mapping from shard to a list of references** to those rows. A dual-city row
  is in two lists. The scan is unchanged; the memory cost is one pointer.
- **The shard is never a matching criterion and never a gate.** The radius gate already does the
  geographic work: a dual-city player reached through the "wrong" bucket is simply outside the
  searcher's radius and is gated there, exactly as §9.1 intends.
- **A search reads the *searcher's* shard, never a union of shards** — merging reintroduces
  precisely the scan cost the shard exists to avoid.

[NOT MEASURED] how a player declares a second city (a product question for
[#173](https://github.com/Raketa02/Raketa/issues/173)), and whether the availability grid
should be per-city — it probably should be, and the schema cannot express that either.

---

## 5. Rebuild

§7.4's safety property is *drop it and replay the event store*, targeting a 50 000-player city
in under five minutes and exercised in CI. Now that the replay runs against the backend's own
`event_store` rather than across a feed, the question is what actually sets the wall clock.

### The Python half is not the constraint [MEASURED]

Envelope decode (`orjson`) plus dispatch plus an idempotent projection into a dict keyed
`(player, sport)`, with the event mix of §7.3's table (dominated by `rating.updated`):

| | |
| --- | --- |
| Events per player, from §7.3's table | **19.9** |
| Throughput, single core | **959 000 events/s** |
| Cost per event | **1.04 µs** (of which `orjson` decode 0.24 µs, 23%) |
| 50 000-player city — 1.0 M events | **1.0 s** |
| Ten cities — 9.9 M events | **10 s** |

**The five-minute budget buys 288 million events of projection on one core.** Projection cost
does not determine the rebuild, at this size or at ten times it. [MEASURED]

### What does determine it [ESTIMATED, with the inputs]

Three things, none of them Python:

1. **Reading 1 M rows out of Postgres.** A `JSONB` payload of the shape these events carry is
   on the order of 200–500 bytes, so 1 M rows is 200–500 MB over the wire. With `asyncpg` and a
   server-side cursor, 100 000–300 000 rows/s is a reasonable expectation on a small instance:
   **4–10 s** for one city, **40–100 s** for ten. That is the dominant term and it is still
   comfortably inside five minutes.
2. **Writing the projection back.** ADR-0093's storage table puts the candidate index in the
   backend's database, so 125 000 rows have to be written. Batched (`COPY` or `executemany`) at
   20 000–50 000 rows/s that is **3–6 s**; one `INSERT` per row is twenty times that and would
   dominate the rebuild. **The rebuild path must batch its writes** — that is the one
   implementation decision the five-minute target actually rests on.
3. **`event_store` has no replay-ordered index.** From
   `backend/migrations/versions/0006_event_store.py`, the table's indexes are
   `(aggregate_type, aggregate_id, version)` and `(event_type)`, the primary key is a **UUID**,
   and `occurred_at` / `created_at` are unindexed. **A whole-store ordered replay therefore has
   nothing cheap to read in order:** `ORDER BY occurred_at` is an external sort of the entire
   table, and reading in primary-key order is reading in random order. Per-aggregate replay is
   indexed and cheap; whole-store replay is not.
   **This is concrete and cheap to fix before the rebuild path is written** — a `BIGSERIAL`
   global sequence column with an index, or an index on `(occurred_at, id)`. One migration now;
   a table rewrite later.

### At ten cities [ESTIMATED]

**40–120 s**, dominated by the read, still inside five minutes — *provided* the rebuild is
batched and ordered by an indexed column. **The number that would actually break it is not city
count but per-player event volume:** §7.3's mix assumes `rating.updated` fires about ten times
per player, and a mature player with 200 counted games generates 200 rating events of which the
projection keeps only the last. If replay volume ever becomes the constraint the answer is a
snapshot or a cursor, not a faster projection — and at 959 000 events/s the projection would
need 288 M events to spend the whole budget on its own.

---

## 6. The doubles enumeration

§9.9: take the top `K` = 16 after liveness, enumerate `C(15,3)` = 455 combinations of the three
non-viewer seats, three pairings each — "~1 400 cheap arithmetic evaluations — tens of
microseconds."

Implemented faithfully: `teamStrength`, the three-pairing `arrange`, `σ_group`, the forecast
clamp, and `w_bal·balance + w_seatfit·mean + w_minfit·min + w_intent·coherence +
w_tag·group_tag_coherence`. [MEASURED]

| K | C(K−1,3) | plain Python | µs/combination | numpy |
| ---: | ---: | ---: | ---: | ---: |
| 8 | 35 | 0.168 ms | 4.80 | 0.040 ms |
| 12 | 165 | 0.789 ms | 4.78 | 0.044 ms |
| **16** | **455** | **2.082 ms** | 4.58 | **0.052 ms** |
| 24 | 1 771 | 8.036 ms | 4.54 | 0.095 ms |
| 32 | 4 495 | **20.06 ms** | 4.46 | 0.166 ms |
| 48 | 16 215 | **68.97 ms** | 4.25 | 0.555 ms |
| 64 | 39 711 | **169.31 ms** | 4.26 | 1.277 ms |

*(The numpy column omits `group_tag_coherence`, whose bit-counting does not vectorise as
cleanly, so it is a lower bound — optimistic by perhaps 30%.)*

**Three findings.**

1. **2.08 ms at K = 16 against "tens of microseconds" — a 40–100x multiplier**, and it is *as
   expensive as the entire candidate scan*. A doubles line-up therefore costs about
   `2.8 + 2.1 = 4.9 ms`, not `1 ms`. Still fine; no longer negligible, and it belongs in the
   §17 budget rather than rounded away.
2. **The cost is cubic in K and the per-combination cost is flat at ~4.5 µs**, so the scaling is
   entirely `C(K−1,3)`. Moving `K` is not the cheap knob §9.9 says it is: **K = 32 costs 20 ms
   and K = 64 costs 169 ms**, and 169 ms is past this document's trigger-1 threshold on its own,
   before a single other request is served. §9.9's *"If that turns out to be false, `K` moves —
   it is a config change, not a rewrite"* is true in Go and **false in Python**. The ruleset
   carrying `K` should carry a **hard cap of 24**, with the cubic cost written beside it.
3. **This is the one place where vectorising is unambiguously worth it if the cap ever moves** —
   40x at K = 16, 130x at K = 64 — because unlike the candidate scan the group objective is
   dense arithmetic over a small fixed-shape array with no early exits. If numpy is ever added
   to the backend for anything, this is the thing to add it for. It is not needed at K = 16.

---

## 7. The index behind a port

**Is there a real cost to making the in-memory snapshot an adapter behind a `CandidateSource`
port rather than the architecture itself?** [MEASURED]

| port granularity | cost |
| --- | --- |
| **`snapshot(shard, sport)` returns the container — §15.2's shape** | **54 ns per search, 0.002% of one search** |
| `get(i)` per candidate row | +0.58 ms on a 2.8 ms search (+94% on the walk) |
| `mu(i)` per candidate field | +0.67 ms (+109% on the walk) |

**At §15.2's granularity the port is free to five significant figures.** Timing the whole search
through it shows a ±3% difference in either direction; that is run-to-run variance on a 2.8 ms
measurement, not the call. **The port costs one method call per search.**

The distinction that matters is *granularity*, and it is the thing to write down, because it is
easy to get wrong later: **the port hands back a container, never a row and never a field.** A
`CandidateSource` answering per-row questions doubles the cost of walking the index and would
make the port itself the reason the loop is slow. **§15.2's `Snapshot` shape survives ADR-0093
unchanged and should be adopted verbatim** — it is the one piece of the discarded §15 worth
keeping.

### What the port is insurance against, priced [MEASURED]

The alternative it makes swappable is a database query per search. Measured at its absolute
floor — sqlite, in memory, indexed on `(sport, lat, lng)`, returning raw tuples, no socket, no
wire protocol, no connection pool, no ORM:

- **2.80 ms** to return the 2 894 in-box rows
- against **2.80 ms** for the in-memory scan *including all eight terms*

**A query per search is not cheaper than the whole in-memory search even at the floor**, and a
real Postgres over a socket with a pool and asyncpg row decoding is a multiple of it. So the
port is insurance whose payout is doubtful and whose premium is 54 ns. **Take it** — but record
the honest reason: it is worth having because it makes the *representation* swappable (objects →
packed columns, item 3) and the *extraction* mechanical, **not** because a database is a
plausible answer to a slow search.

### The other half of "does it fit in a request" [MEASURED]

Building the §16 response — 20 seats, 8 terms each with evidence payloads, modifiers, liveness
reasons:

| | |
| --- | --- |
| Building the dicts | **0.090 ms** |
| `json.dumps` | 0.298 ms, 40 KiB |
| **`orjson.dumps`** | **0.035 ms**, 37 KiB |
| *§17's Go budget for this stage* | *0.300 ms* |

**Serialisation is the one stage where Python beats the document's Go budget**, by 8.5x, and
only because the backend already depends on `orjson`. FastAPI's default `JSONResponse` uses
`json.dumps`; the matcher's routes should use `ORJSONResponse`, which is worth 0.26 ms — a tenth
of a search — for one import.

---

## 8. The low end, which the document under-serves

§17's "candidates in range for one search: 10–500" is a launch-city figure. For a market with
**tens** of players the question is not performance at all; it is whether there is anything to
rank.

Simulated: 4 000 searches per row, one row per (player, sport) with players playing 2–3 sports,
the searcher's radius drawn from `{3, 5, 8, 8, 10, 15, 25}` km, a candidate counted if it shares
the sport and sits inside that radius. Two spatial models, because **the answer depends entirely
on which is true and the document names neither.** [MEASURED — of the model; the model itself is
the assumption]

### Players scattered over the metro (σ 9 km)

| players | rows | median in range | p10 | P(<3) | P(<5) | P(<10) | P(<5) after relaxing to 3× radius |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 53 | 3 | 0 | **49%** | **63%** | 86% | 15% |
| 40 | 103 | 5 | 0 | 37% | 48% | 70% | 7% |
| 80 | 203 | 10 | 1 | 24% | 35% | 50% | 4% |
| 150 | 383 | 17 | 2 | 13% | 21% | 37% | 1% |
| 300 | 756 | 37 | 4 | 6% | 11% | 22% | 0% |
| 600 | 1 513 | 71 | 9 | 3% | 6% | 11% | 0% |
| 1 200 | 2 986 | 146 | 18 | 1% | 3% | 5% | 0% |

### Players clustered around four clubs (σ 1.2 km each)

| players | rows | median in range | p10 | P(<3) | P(<5) | P(<10) | P(<5) after relaxing to 3× radius |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 54 | 7 | 2 | 22% | 40% | 68% | 3% |
| 40 | 106 | 11 | 5 | 3% | 6% | 47% | 0% |
| 80 | 205 | 26 | 11 | 0% | 1% | 5% | 0% |
| 150 | 388 | 49 | 21 | 0% | 0% | 1% | 0% |
| 300 | 758 | 94 | 42 | 0% | 0% | 0% | 0% |
| 1 200 | 3 000 | 386 | 167 | 0% | 0% | 0% | 0% |

**What this says for [Cold start](https://github.com/Raketa02/Raketa/issues/162) and
[The thin-pool experience](https://github.com/Raketa02/Raketa/issues/166):**

1. **At twenty players the empty state is the normal case, not the edge case.** Half of all
   searches return fewer than three candidates in the scattered model, and relaxation does not
   rescue it: even at three times the radius, 15% of searches still return fewer than five.
2. **Clustering is worth more than anything the matcher can do.** Twenty clustered players
   behave like eighty scattered ones; eighty clustered players behave like a solved problem
   (1% of searches below five). **Recruiting a city club by club is not a go-to-market
   preference, it is the single highest-leverage variable in the whole cold-start problem** —
   worth more at this size than every term in §9.3 combined.
3. **The threshold where the thin pool stops being the default experience is about 80 players
   clustered, or 300–600 scattered.** Below it, the honest empty state and the relaxation ladder
   *are* the product, not a fallback.
4. **The relaxation ladder does almost all of its work inside this range and then becomes
   irrelevant** — 63% → 15% at twenty players, 6% → 0% at three hundred. Its constants should be
   tuned against a twenty-player city, not a thousand-player one.

[NOT MEASURED] which spatial model is true of a real Polish metro. It is checkable from the
first hundred sign-ups' `area_cell` values, and it should be checked before
[#166](https://github.com/Raketa02/Raketa/issues/166) picks its relaxation constants.

---

## What this changes, in one page

**For [The scale posture](https://github.com/Raketa02/Raketa/issues/165):**

- Write trigger 1 as **p99 of one scoring call > 20 ms, or duty cycle > 0.25**, measured
  in-process by a lag monitor and a scoring histogram that ship with the engine.
- Write trigger 4 in **rows × workers × 2**, not megabytes. With `__slots__` objects and four
  workers, a 1 GB container is at the trigger at ~32 000 players — not "several cities".
- Record the escalation ladder that comes *before* the reversal: `(shard, sport)` buckets →
  equirectangular distance → candidate cap → process pool with a **resident** index. All four
  are measured to work.
- Note that **multi-city under ADR-0093 fires trigger 4, not trigger 2**, because every worker
  holds every shard unless the load balancer starts routing by city — which is the extracted
  service by another name.

**For [The matcher's picture of the city](https://github.com/Raketa02/Raketa/issues/173):**

- `CandidateSource.snapshot()` at container granularity, verbatim from §15.2. It costs 54 ns.
- Row identity is `(player, sport)`; `shard_keys` is a set on the row and the shard index holds
  references. A dual-city player costs 8 bytes, not a duplicate row.
- `gc.freeze()` after every index load and refresh. Budget 2x the index for the refresh peak,
  and build the replacement off the event loop — it takes 0.9 s.
- The representation lives behind the port and is chosen by the memory budget. Start with
  `__slots__` objects; move to packed columns when `GUNICORN_WORKERS` exceeds one.
- Bucket by `(shard, sport)`, not spatially. A geo-cell map is worth 14%; a sport bucket is 4x.

**For the engine's ruleset and the §17 budget:**

- `K` in §9.9 gets a hard cap of **24**, with the cubic cost written beside it.
- §17's cost table should be re-stated in CPython terms: ~0.6 ms generate, ~2.4 ms fit, ~2.1 ms
  group objective, ~0.13 ms serialise — **about 5 ms for a doubles line-up**, against the
  document's "< 1 ms".

**For the backend, independent of the matcher:**

- `event_store` needs a replay-ordered index (a `BIGSERIAL`, or `(occurred_at, id)`) before
  anything replays the whole store. One migration now, a table rewrite later.
- The matcher's routes should return `ORJSONResponse`, not FastAPI's default.

**For [Cold start](https://github.com/Raketa02/Raketa/issues/162) and
[The thin-pool experience](https://github.com/Raketa02/Raketa/issues/166):**

- Check the spatial model against real sign-ups before tuning relaxation constants. Clustered
  versus scattered is a 4x difference in effective pool size and it dominates everything else at
  the low end.
