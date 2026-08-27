"""Ticket #161 item 3 — what §7.2's "~160 bytes per row" costs in Python.

Measures the same field list in six representations, with tracemalloc (which
counts every object the allocator handed out, not just the container), and
cross-checks against process RSS. Then the multiplier that actually matters:
the index is held once per *worker*, not once per instance.

Finally the boundary behaviour: gen-2 GC pause with the index live, whether
gc.freeze() helps, and the headroom a refresh needs while in-flight searches
still hold the old copy.

Run: python memory_bench.py
"""
from __future__ import annotations

import datetime as dt
import gc
import os
import statistics
import sys
import time
import tracemalloc
import uuid
from array import array
from dataclasses import dataclass

from population import Columns, make_rows

N = 31_250          # one sport of a 50 000-player city
CITY_ROWS = 125_000  # the whole 50 000-player city index

FIELDS_INT = 20      # small ints / enums / uint8 strands
FIELDS_FLOAT = 4     # mu, sigma, lat, lng


# ── the same §7.2 row, in the shapes a Python implementer would reach for ──
class SlotsRow:
    __slots__ = tuple(f"f{i}" for i in range(32))


@dataclass
class DataclassRow:
    player_id: object
    sport: int
    mu: float
    sigma: float
    confidence: int
    counted_games: int
    calibration_priority: int
    rating_status: int
    rating_updated_at: object
    play_intent: int
    tags: int
    tags_updated_at: object
    grid: int
    grid_updated_at: object
    area_cell: int
    area_lat: float
    area_lng: float
    search_radius_km: int
    proposals_opt_in: object
    profile_updated_at: object
    player_score: object
    strand_shows_up: object
    strand_settles_up: object
    strand_answers: object
    strand_confirms: object
    strand_keeps_plans: object
    strand_sportsmanship: object
    opponent_variety: object
    last_active_at: object
    open_challenges: int
    first_seen_at: object
    shard_key: str


class DictRow:
    """A plain class with __dict__ — the default if nobody thinks about it."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def vars_of_arrays(obj):
    for name in obj.__slots__:
        v = getattr(obj, name, None)
        if isinstance(v, array):
            yield v


def measure(build, label, n):
    gc.collect()
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    obj = build(n)
    cur, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    total = cur - base
    print(f"| {label} | {total / 1e6:.1f} | {total / n:.0f} | "
          f"{total / n * CITY_ROWS / 1e6:.0f} |")
    return obj, total


def build_slots(n):
    rng = __import__("random").Random(1)
    out = []
    for i in range(n):
        r = SlotsRow()
        for j in range(FIELDS_INT):
            setattr(r, f"f{j}", rng.randrange(1 << 20))
        for j in range(FIELDS_INT, FIELDS_INT + FIELDS_FLOAT):
            setattr(r, f"f{j}", rng.random())
        for j in range(FIELDS_INT + FIELDS_FLOAT, 32):
            setattr(r, f"f{j}", None)
        out.append(r)
    return out


def build_realistic(n):
    """§7.2 spelled the way a first implementation spells it: uuid, datetime,
    str shard key, one object per nullable strand."""
    rng = __import__("random").Random(2)
    now = dt.datetime(2026, 8, 26, tzinfo=dt.timezone.utc)
    shard = "krakow"
    out = []
    for i in range(n):
        out.append(DataclassRow(
            player_id=uuid.uuid4(), sport=rng.randrange(4),
            mu=rng.random() * 4 + 1, sigma=rng.random(),
            confidence=rng.randrange(100), counted_games=rng.randrange(200),
            calibration_priority=rng.randrange(3), rating_status=rng.randrange(3),
            rating_updated_at=now, play_intent=rng.randrange(3),
            tags=rng.getrandbits(18), tags_updated_at=now,
            grid=rng.getrandbits(21), grid_updated_at=now,
            area_cell=rng.getrandbits(24), area_lat=rng.random() * 50,
            area_lng=rng.random() * 20, search_radius_km=rng.randrange(30),
            proposals_opt_in=True, profile_updated_at=now,
            player_score=None, strand_shows_up=None, strand_settles_up=None,
            strand_answers=None, strand_confirms=None, strand_keeps_plans=None,
            strand_sportsmanship=None, opponent_variety=None,
            last_active_at=now, open_challenges=rng.randrange(6),
            first_seen_at=now, shard_key=shard))
    return out


def build_dictrow(n):
    rng = __import__("random").Random(3)
    return [DictRow(**{f"f{j}": rng.randrange(1 << 20) for j in range(32)})
            for _ in range(n)]


def build_population(n):
    return make_rows(n)


def build_columns(n):
    return Columns(make_rows(n))


def build_np(n):
    import numpy as np
    from scoring_numpy import NpColumns
    return NpColumns(make_rows(n))


def main():
    print(f"# memory_bench — CPython {sys.version.split()[0]} on {os.uname().machine}")
    print()
    print(f"n = {N:,} rows measured; the last column extrapolates to the "
          f"{CITY_ROWS:,}-row index of a 50 000-player city (§7.2).")
    print()
    print("| representation | MB @ 31 250 rows | bytes/row | MB @ 125 000 rows |")
    print("|---|---|---|---|")

    measure(build_realistic, "dataclass, uuid + datetime + str shard "
                             "(the naive spelling)", N)
    measure(build_dictrow, "plain class with __dict__, 32 int fields", N)
    measure(build_slots, "__slots__ class, 32 fields (20 int, 4 float, 8 None)", N)
    rows, _ = measure(build_population, "__slots__ CandidateRow as benchmarked", N)
    measure(build_columns, "array/struct-packed columns", N)
    try:
        npc = build_np(N)
        nb = npc.nbytes()
        print(f"| numpy columns (exact `.nbytes`) | {nb / 1e6:.1f} | "
              f"{nb / N:.0f} | {nb / N * CITY_ROWS / 1e6:.0f} |")
        del npc
    except ImportError:
        print("| numpy columns | (numpy not installed) | | |")
    cols = build_columns(N)
    exact = sum(a.itemsize * len(a) for a in vars_of_arrays(cols))
    print(f"| array-packed columns (exact `itemsize x len`) | {exact / 1e6:.1f} | "
          f"{exact / N:.0f} | {exact / N * CITY_ROWS / 1e6:.0f} |")
    del cols

    # ── the multiplier: N workers per instance ─────────────────────────────
    print()
    _, packed = measure(lambda n: Columns(make_rows(n)), "(re-measure) packed", N)
    _, objs = measure(lambda n: make_rows(n), "(re-measure) objects", N)
    print()
    print("| workers/instance | objects, whole-city index | packed columns |")
    print("|---|---|---|")
    for w in (1, 2, 4, 8):
        per_worker_obj = objs / N * CITY_ROWS
        per_worker_pk = packed / N * CITY_ROWS
        print(f"| {w} | {w * per_worker_obj / 1e6:.0f} MB | "
              f"{w * per_worker_pk / 1e6:.0f} MB |")

    # ── GC behaviour with a large long-lived structure ─────────────────────
    print()
    print("## GC, with the index live")
    del rows
    gc.collect()
    idx = make_rows(CITY_ROWS)
    gc.collect()

    def gen2_pause():
        ts = []
        for _ in range(5):
            t0 = time.perf_counter()
            gc.collect(2)
            ts.append((time.perf_counter() - t0) * 1e3)
        return statistics.median(ts)

    print(f"- objects tracked by the collector: {len(gc.get_objects()):,}")
    p_before = gen2_pause()
    print(f"- median full `gc.collect(2)` pause with a {CITY_ROWS:,}-row object "
          f"index live: **{p_before:.1f} ms**")
    gc.freeze()
    p_after = gen2_pause()
    print(f"- after `gc.freeze()`: **{p_after:.1f} ms** "
          f"({p_before / max(p_after, 1e-9):.1f}x cheaper)")
    gc.unfreeze()

    # what the automatic gen-2 threshold means in practice
    print(f"- `gc.get_threshold()` = {gc.get_threshold()}")

    # ── refresh headroom ───────────────────────────────────────────────────
    print()
    print("## Refresh headroom (§15.3's snapshot swap, in Python)")
    try:
        import psutil
        p = psutil.Process()
        rss0 = p.memory_info().rss
        t0 = time.perf_counter()
        new = make_rows(CITY_ROWS, seed=99)
        build_s = time.perf_counter() - t0
        rss1 = p.memory_info().rss
        print(f"- RSS with one {CITY_ROWS:,}-row index: {rss0 / 1e6:.0f} MB")
        print(f"- RSS while both old and new are live: {rss1 / 1e6:.0f} MB "
              f"(+{(rss1 - rss0) / 1e6:.0f} MB)")
        print(f"- wall clock to build the replacement in-process: {build_s:.2f} s "
              f"— during which the loop is blocked unless it is built off-thread")
        del new
        gc.collect()
        rss2 = p.memory_info().rss
        print(f"- RSS after dropping the old copy: {rss2 / 1e6:.0f} MB "
              f"(the allocator returns {max(0, rss1 - rss2) / 1e6:.0f} MB)")
    except ImportError:
        print("- psutil not installed; RSS not measured")


if __name__ == "__main__":
    main()
