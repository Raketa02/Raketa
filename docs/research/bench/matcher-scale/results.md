# Captured run

```
python   : 3.11.6 (v3.11.6:8b6ee5ba3b, Oct  2 2023, 11:18:21) [Clang 13.0.0 (clang-1300.0.29.30)]
platform : macOS-15.7.1-arm64-arm-64bit
machine  : arm64
Darwin PL-D4K1W3VX0R 24.6.0 Darwin Kernel Version 24.6.0: Mon Aug 11 21:11:04 PDT 2025; root:xnu-11417.140.69.701.11~1/RELEASE_ARM64_T6031 arm64
Apple M3 Max
14
38654705664
```


---

# scan_bench — CPython 3.11.6 on arm64

| rows | in-box | objects | columns | np-full | np-block | C | cells |
|---|---|---|---|---|---|---|---|
| 2,500 | 206 | 0.231 | 0.287 | 0.068 | 0.058 | 0.010 | 0.243 |
| 12,500 | 985 | 1.125 | 1.398 | 0.125 | 0.100 | 0.038 | 1.005 |
| 31,250 | 2386 | 2.790 | 3.443 | 0.224 | 0.170 | 0.094 | 2.388 |
| 125,000 | 9602 | 12.174 | 14.095 | 0.832 | 0.570 | 0.607 | 10.057 |
| 250,000 | 19330 | 26.486 | 28.747 | 1.692 | 1.110 | 1.558 | 21.347 |
| 1,000,000 | 76947 | 111.137 | 113.382 | 6.862 | 4.491 | 6.939 | 107.051 |

decomposition at 31,250 rows, 2386 survivors (0.002955s total):
  reject-only scan (box misses every row):    577.2 us = 18.5 ns/row
  eight terms on survivors:                  2377.9 us = 1.00 us/survivor

| radius km | in-box+in-ring | objects ms | us/survivor |
|---|---|---|---|
| 3 | 375 | 1.103 | 1.40 |
| 5 | 1060 | 1.798 | 1.15 |
| 8 | 2386 | 3.083 | 1.05 |
| 15 | 5510 | 6.006 | 0.99 |
| 25 | 7204 | 7.490 | 0.96 |
| 60 | 7355 | 7.558 | 0.95 |

---

# terms_bench — CPython 3.11.6 on arm64

block = 3048 candidate rows; the bare `for` loop over it costs 27 us (9 ns/row) and is subtracted from every row below.

| §9.3 term | us over the block | ns per candidate | share of the eight |
|---|---|---|---|
| 1 level fit | 145 | 48 | 6% |
| 2 predicted balance | 292 | 96 | 12% |
| 3 intent alignment | 16 | 5 | 1% |
| 4 reliability (6 strands live) | 330 | 108 | 13% |
| 5 availability overlap | 402 | 132 | 16% |
| 6 playing style | 379 | 124 | 15% |
| 7 social vibe | 383 | 126 | 15% |
| 8 distance — haversine | 572 | 188 | 23% |
| 8 distance — equirectangular | 248 | 81 |  |
| **sum of the eight (haversine)** | **2518** | **826** | 100% |

---

# doubles_bench — CPython 3.11.6 on arm64

| K | C(K-1,3) combos | plain Python ms | us/combo | numpy ms |
|---|---|---|---|---|
| 8 | 35 | 0.168 | 4.80 | 0.040 |
| 12 | 165 | 0.789 | 4.78 | 0.044 |
| 16 | 455 | 2.082 | 4.58 | 0.052 |
| 24 | 1771 | 8.036 | 4.54 | 0.095 |
| 32 | 4495 | 20.057 | 4.46 | 0.166 |
| 48 | 16215 | 68.966 | 4.25 | 0.555 |
| 64 | 39711 | 169.310 | 4.26 | 1.277 |

---

# memory_bench — CPython 3.11.6 on arm64

n = 31,250 rows measured; the last column extrapolates to the 125,000-row index of a 50 000-player city (§7.2).

| representation | MB @ 31 250 rows | bytes/row | MB @ 125 000 rows |
|---|---|---|---|
| dataclass, uuid + datetime + str shard (the naive spelling) | 60.3 | 1929 | 241 |
| plain class with __dict__, 32 int fields | 107.7 | 3447 | 431 |
| __slots__ class, 32 fields (20 int, 4 float, 8 None) | 29.8 | 953 | 119 |
| __slots__ CandidateRow as benchmarked | 24.4 | 782 | 98 |
| array/struct-packed columns | 1.4 | 44 | 6 |
| numpy columns (exact `.nbytes`) | 1.4 | 46 | 6 |
| array-packed columns (exact `itemsize x len`) | 1.3 | 43 | 5 |

| (re-measure) packed | 1.4 | 44 | 6 |
| (re-measure) objects | 24.4 | 782 | 98 |

| workers/instance | objects, whole-city index | packed columns |
|---|---|---|
| 1 | 98 MB | 6 MB |
| 2 | 196 MB | 11 MB |
| 4 | 391 MB | 22 MB |
| 8 | 782 MB | 44 MB |

## GC, with the index live
- objects tracked by the collector: 174,748
- median full `gc.collect(2)` pause with a 125,000-row object index live: **34.6 ms**
- after `gc.freeze()`: **0.0 ms** (138286.8x cheaper)
- `gc.get_threshold()` = (700, 10, 10)

## Refresh headroom (§15.3's snapshot swap, in Python)
- RSS with one 125,000-row index: 357 MB
- RSS while both old and new are live: 461 MB (+104 MB)
- wall clock to build the replacement in-process: 0.90 s — during which the loop is blocked unless it is built off-thread
- RSS after dropping the old copy: 360 MB (the allocator returns 102 MB)

---

# fork_bench — CPython 3.11.6 on arm64, 125,000-row index, 4 forked workers each scanning it 5 times

| representation | gc.freeze() before fork | parent USS MB | per-worker USS MB | total MB (parent + 4) |
|---|---|---|---|---|
| objects | no | 110 | 108 | 544 |
| objects | yes | 110 | 109 | 545 |
| packed | no | 15 | 5 | 36 |
| packed | yes | 14 | 6 | 36 |

---

# port_bench — CPython 3.11.6 on arm64

| port granularity | ms per search | overhead vs direct |
|---|---|---|
| none — the loop owns the list | 2.795 | — |
| **per search** — `snapshot()` returns the list | 2.772 | -23.3 us (-0.83%) |
| per row — `get(i)` per candidate | 3.374 | +0.58 ms (+94% on the walk) |
| per field — `mu(i)` per candidate | 3.467 | +0.67 ms (+109% on the walk) |

(bare attribute walk over 31,250 rows: 618 us; via `get(i)`: 1197 us; via `mu(i)`: 1290 us)

The `snapshot()` call measured on its own: **54 ns** — 0.00192% of one search. Whatever sign the per-search row above carries is run-to-run variance, not the port.

## What the port is insurance against: a query per search
- sqlite, in-memory, indexed, returning 2894 rows: **2.80 ms** — and that is the floor: no socket, no wire protocol, no connection pool, no row objects built.
- the in-memory scan that replaces it: 2.80 ms.

## Building and serialising the §16 response
- building 20 seats x 8 terms with evidence: **0.090 ms**
- `json.dumps`: 0.298 ms, 40 KiB
- `orjson.dumps`: **0.035 ms**, 37 KiB (the backend already depends on orjson)
- §17 budgets 300 us for this stage in Go.

---

# rebuild_bench — CPython 3.11.6 on arm64, orjson

- events per player, from §7.3's table: **19.9**
- 5,000 players -> 99,518 events -> 20,000 index rows
- decode + dispatch + apply, single-threaded: **0.10 s** = 1.04 us/event
- of which orjson decode alone: 0.24 us/event (23%)

## Extrapolation

| city size | players | events | projection CPU (single core) |
|---|---|---|---|
| §7.4's target | 50,000 | 1.00 M | 1 s = 0.0 min |
| ten cities | 500,000 | 9.95 M | 10 s = 0.2 min |

Measured projection throughput: **959,086 events/s** on one core.
The five-minute budget therefore buys **287.7 M events** of projection on one core, before any time is spent reading them.

---

# lowend_bench — CPython 3.11.6

4000 simulated searches per row. A candidate counts if it shares the searcher's sport and sits inside the searcher's declared radius (one of (3, 5, 8, 8, 10, 15, 25) km).

## spread model (sigma 9.0 km)

| players | rows | median in range | p10 | p90 | P(<3) | P(<5) | P(<10) | median after relax x3 | P(<5) after relax x3 |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 53 | 3 | 0 | 10 | 49% | 63% | 86% | 11 | 15% |
| 40 | 103 | 5 | 0 | 20 | 37% | 48% | 70% | 22 | 7% |
| 80 | 203 | 10 | 1 | 40 | 24% | 35% | 50% | 44 | 4% |
| 150 | 383 | 17 | 2 | 73 | 13% | 21% | 37% | 82 | 1% |
| 300 | 756 | 37 | 4 | 161 | 6% | 11% | 22% | 172 | 0% |
| 600 | 1513 | 71 | 9 | 318 | 3% | 6% | 11% | 346 | 0% |
| 1200 | 2986 | 146 | 18 | 598 | 1% | 3% | 5% | 686 | 0% |

## clubbed model (4 clubs, sigma 1.2 km)

| players | rows | median in range | p10 | p90 | P(<3) | P(<5) | P(<10) | median after relax x3 | P(<5) after relax x3 |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 54 | 7 | 2 | 14 | 22% | 40% | 68% | 11 | 3% |
| 40 | 106 | 11 | 5 | 26 | 3% | 6% | 47% | 24 | 0% |
| 80 | 205 | 26 | 11 | 50 | 0% | 1% | 5% | 49 | 0% |
| 150 | 388 | 49 | 21 | 95 | 0% | 0% | 1% | 94 | 0% |
| 300 | 758 | 94 | 42 | 185 | 0% | 0% | 0% | 185 | 0% |
| 600 | 1493 | 195 | 82 | 368 | 0% | 0% | 0% | 368 | 0% |
| 1200 | 3000 | 386 | 167 | 738 | 0% | 0% | 0% | 738 | 0% |

---

# loop_bench — CPython 3.11.6, uvicorn 1 worker, 31250 rows, /ping at 50/s for 8s per case

| endpoint | single-call ms (median of 15) |
|---|---|
| `/score/inline` | 4.00 |
| `/score/thread` | 3.45 |
| `/score/process_resident` | 3.54 |
| `/score/process_block` | 15.42 |

process_block detail: {'n': 2386, 'block': 3048, 'pickle_bytes': 657642, 'pickle_ms': 5.308374762535095}

| scoring mode | rps | loop-lag p50 | p99 | p99.9 | max | ping p50 | ping p99 | ping max | score p50 | score p99 |
|---|---|---|---|---|---|---|---|---|---|---|
| none (baseline) | 0 | 0.66 | 2.80 | 45.10 | 54.98 | 1.48 | 2.86 | 59.62 | — | — |
| `/score/inline` | 1 | 0.61 | 1.97 | 11.35 | 14.06 | 1.24 | 2.36 | 3.61 | 7.8 | 15.7 |
| `/score/inline` | 5 | 0.60 | 10.35 | 15.34 | 18.82 | 0.90 | 6.03 | 13.56 | 7.7 | 23.6 |
| `/score/inline` | 20 | 0.59 | 6.10 | 7.66 | 8.43 | 0.73 | 3.78 | 4.62 | 6.6 | 11.4 |
| `/score/thread` | 1 | 0.60 | 2.96 | 11.95 | 17.27 | 1.03 | 2.97 | 3.74 | 11.7 | 21.6 |
| `/score/thread` | 5 | 0.60 | 11.13 | 12.82 | 13.02 | 1.14 | 2.96 | 4.06 | 12.8 | 17.3 |
| `/score/thread` | 20 | 0.60 | 7.83 | 9.62 | 10.73 | 0.74 | 3.77 | 4.93 | 7.6 | 12.3 |
| `/score/process_resident` | 1 | 0.62 | 0.86 | 1.01 | 1.98 | 1.48 | 2.39 | 4.28 | 14.7 | 22.3 |
| `/score/process_resident` | 5 | 0.61 | 0.82 | 1.33 | 2.11 | 1.36 | 2.52 | 5.76 | 15.5 | 17.6 |
| `/score/process_resident` | 20 | 0.59 | 0.94 | 1.29 | 10.09 | 0.77 | 1.75 | 14.23 | 10.5 | 12.6 |
| `/score/process_block` | 1 | 0.62 | 12.02 | 30.75 | 40.71 | 1.47 | 3.62 | 27.94 | 36.4 | 60.9 |
| `/score/process_block` | 5 | 0.59 | 19.90 | 24.24 | 25.57 | 0.69 | 9.87 | 12.27 | 34.7 | 46.2 |
| `/score/process_block` | 20 | 0.59 | 11.58 | 22.83 | 26.64 | 0.55 | 5.54 | 18.00 | 20.0 | 37.7 |

---

# gc_bench — CPython 3.11.6, uvicorn 1 worker, 125,000-row index, 20 searches/s + 50 pings/s for 20s

| gc.freeze() | gen2 collections | gen2 total ms | gen2 max ms | gen1 n | gen1 max ms | loop-lag p99 | loop-lag max | ping p99 | ping max | search p99 |
|---|---|---|---|---|---|---|---|---|---|---|
| no | 1 | 57.9 | 57.9 | 335 | 0.1 | 18.38 | 84.37 | 11.46 | 64.54 | 23.7 |
<!-- frozen objects: 0, gen0 n=3685 max=0.18ms -->
| yes | 4 | 1.1 | 0.4 | 335 | 0.2 | 18.54 | 28.74 | 11.77 | 31.14 | 22.3 |
<!-- frozen objects: 171770, gen0 n=3686 max=0.15ms -->

---

# saturation_bench — CPython 3.11.6, uvicorn 1 worker, /ping at 50/s, 6s per point

## 31,250 rows in the shard, inline scoring (unloaded single call: 3.27 ms)
| searches/s | offered util | loop-lag p99 ms | loop-lag max ms | ping p50 ms | ping p99 ms | ping max ms | search p50 ms | search p99 ms |
|---|---|---|---|---|---|---|---|---|
| 1 | 0% | 1.30 | 5.26 | 0.72 | 2.34 | 4.69 | 4.9 | 10.2 |
| 5 | 2% | 3.46 | 8.97 | 0.74 | 5.49 | 9.34 | 6.4 | 13.9 |
| 20 | 7% | 5.82 | 8.60 | 0.76 | 5.46 | 7.31 | 6.7 | 10.2 |
| 50 | 16% | 4.51 | 5.79 | 0.65 | 6.74 | 13.54 | 5.4 | 11.0 |
| 100 | 33% | 3.50 | 6.91 | 0.54 | 12.45 | 16.74 | 4.3 | 10.5 |
| 200 | 65% | 50.18 | 65.54 | 3.56 | 24.26 | 32.85 | 3.5 | 28.4 |
| 400 | 131% | 6879.12 | 6914.01 | 193.28 | 222.25 | 222.25 | 195.7 | 222.5 |

## 125,000 rows in the shard, inline scoring (unloaded single call: 13.35 ms)
| searches/s | offered util | loop-lag p99 ms | loop-lag max ms | ping p50 ms | ping p99 ms | ping max ms | search p50 ms | search p99 ms |
|---|---|---|---|---|---|---|---|---|
| 1 | 1% | 17.60 | 32.53 | 1.17 | 11.52 | 14.61 | 25.9 | 34.6 |
| 5 | 7% | 20.39 | 27.39 | 0.69 | 10.83 | 17.27 | 22.3 | 31.3 |
| 20 | 27% | 21.10 | 78.08 | 0.54 | 17.82 | 44.29 | 18.1 | 28.9 |
| 50 | 67% | 56.05 | 80.81 | 0.43 | 20.13 | 31.41 | 13.8 | 33.1 |
| 100 | 133% | 7857.35 | 7882.23 | 157.79 | 900.03 | 900.03 | 830.5 | 923.4 |
| 200 | 267% | 16717.94 | 16747.82 | 853.71 | 890.36 | 890.36 | 856.7 | 913.8 |
| 400 | 534% | 42086.96 | 42111.86 | 882.02 | 899.44 | 899.44 | 876.2 | 971.5 |
