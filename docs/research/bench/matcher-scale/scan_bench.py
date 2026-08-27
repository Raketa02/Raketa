"""Ticket #161 item 1 — what a search costs, four ways, against row count.

Also answers the geo-cell sub-question: what a coarse bucket map buys, and at
what row count it is worth its complexity.

Run: python scan_bench.py
"""
from __future__ import annotations

import ctypes
import math
import os
import statistics
import sys
import time

from population import Searcher, Columns, make_rows
from scoring import SearcherConstants, scan_columns, scan_objects, searcher_masks

HERE = os.path.dirname(os.path.abspath(__file__))

ROW_COUNTS = [2_500, 12_500, 31_250, 125_000, 250_000, 1_000_000]
# 31_250 == one sport of a 50 000-player city (2.5 rows/player / 4 sports)
# 125_000 == the whole 50 000-player city index


def timeit(fn, *args, reps=None, budget=1.5, **kw):
    """Return (median_seconds, n_reps). Warms up, then runs to a time budget."""
    fn(*args, **kw)
    if reps is None:
        t0 = time.perf_counter()
        fn(*args, **kw)
        one = time.perf_counter() - t0
        reps = max(3, min(2000, int(budget / max(one, 1e-6))))
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn(*args, **kw)
        times.append(time.perf_counter() - t0)
    return statistics.median(times), reps


# ── the geo-cell bucket map (§9.2's "cheap next step") ─────────────────────
CELL_KM = 2.0


def build_cells(rows, cell_km=CELL_KM):
    buckets = {}
    for r in rows:
        key = (r.sport,
               int(r.area_lat * 110.574 / cell_km),
               int(r.area_lng * 111.320 * math.cos(math.radians(r.area_lat)) / cell_km))
        b = buckets.get(key)
        if b is None:
            buckets[key] = [r]
        else:
            b.append(r)
    return buckets


def scan_cells(buckets, s, cell_km=CELL_KM, k=None):
    k = k or SearcherConstants(s)
    ky0 = int(s.lat * 110.574 / cell_km)
    kx0 = int(s.lng * 111.320 * math.cos(math.radians(s.lat)) / cell_km)
    span = int(s.radius_km / cell_km) + 1
    out = []
    get = buckets.get
    for dy in range(-span, span + 1):
        for dx in range(-span, span + 1):
            b = get((s.sport, ky0 + dy, kx0 + dx))
            if b:
                out.extend(scan_objects(b, s, k=k))
    return out


def main():
    plat = f"CPython {sys.version.split()[0]} on {os.uname().machine}"
    print(f"# scan_bench — {plat}")
    print()

    s = Searcher(radius_km=8, mode=0)
    k = SearcherConstants(s)

    # native library, if it has been built
    lib = None
    dylib = os.path.join(HERE, "native", "libscan.dylib")
    so = os.path.join(HERE, "native", "libscan.so")
    path = dylib if os.path.exists(dylib) else (so if os.path.exists(so) else None)
    if path:
        lib = ctypes.CDLL(path)
        lib.scan.restype = ctypes.c_int32
        lib.scan.argtypes = [
            ctypes.c_void_p, ctypes.c_int32,
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_uint32, ctypes.c_int32,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.c_int32, ctypes.c_uint8,
            ctypes.c_void_p, ctypes.c_void_p]

    try:
        import numpy as np
        from scoring_numpy import NpColumns, scan_numpy_block, scan_numpy_full
    except ImportError:
        np = None

    ROW_DT = None
    if np is not None:
        ROW_DT = np.dtype([("mu", "f4"), ("sigma", "f4"), ("lat", "f4"),
                           ("lng", "f4"), ("stale", "f4"), ("tag_stale", "f4"),
                           ("tags", "u4"), ("grid", "u4"), ("player_id", "u4"),
                           ("sport", "u1"), ("grid_bits", "u1"),
                           ("intent", "u1"), ("ok", "u1")])
        assert ROW_DT.itemsize == 40, ROW_DT.itemsize

    hdr = ("rows", "in-box", "objects", "columns", "np-full", "np-block",
           "C", "cells")
    print("| " + " | ".join(hdr) + " |")
    print("|" + "|".join(["---"] * len(hdr)) + "|")

    for n in ROW_COUNTS:
        rows = make_rows(n)
        cols = Columns(rows)
        survivors = len(scan_objects(rows, s, k=k))

        t_obj, _ = timeit(scan_objects, rows, s, k=k)
        t_col, _ = timeit(scan_columns, cols, s, k=k)

        t_npf = t_npb = float("nan")
        if np is not None:
            npc = NpColumns(rows)
            t_npf, _ = timeit(scan_numpy_full, npc, s)
            dlat = s.radius_km / 110.574
            dlng = s.radius_km / (111.320 * math.cos(math.radians(s.lat)))
            m = ((npc.sport == s.sport)
                 & (npc.lat >= s.lat - dlat) & (npc.lat <= s.lat + dlat)
                 & (npc.lng >= s.lng - dlng) & (npc.lng <= s.lng + dlng)
                 & npc.ok)
            idx = np.flatnonzero(m)
            t_npb, _ = timeit(scan_numpy_block, npc, s, idx)

        t_c = float("nan")
        if lib is not None and np is not None:
            arr = np.zeros(n, dtype=ROW_DT)
            arr["mu"] = [r.mu for r in rows]
            arr["sigma"] = [r.sigma for r in rows]
            arr["lat"] = [r.area_lat for r in rows]
            arr["lng"] = [r.area_lng for r in rows]
            arr["stale"] = [r.grid_staleness for r in rows]
            arr["tag_stale"] = [r.tag_staleness for r in rows]
            arr["tags"] = [r.tags for r in rows]
            arr["grid"] = [r.grid for r in rows]
            arr["player_id"] = [r.player_id for r in rows]
            arr["sport"] = [r.sport for r in rows]
            arr["grid_bits"] = [r.grid_bits for r in rows]
            arr["intent"] = [r.play_intent for r in rows]
            arr["ok"] = [1 if (r.photo_ok and r.rating_status != 2) else 0
                         for r in rows]
            out_fit = np.zeros(n, dtype=np.float64)
            out_id = np.zeros(n, dtype=np.uint32)
            comp, clash = searcher_masks(s.tags)

            def call_c():
                return lib.scan(arr.ctypes.data, n, s.mu, s.sigma, s.lat, s.lng,
                                float(s.radius_km), s.grid, s.grid_bits, s.tags,
                                comp, clash, s.mode, s.sport,
                                out_fit.ctypes.data, out_id.ctypes.data)
            t_c, _ = timeit(call_c)

        buckets = build_cells(rows)
        t_cells, _ = timeit(scan_cells, buckets, s, k=k)

        def ms(t):
            return "—" if t != t else f"{t * 1e3:.3f}"
        print(f"| {n:,} | {survivors} | {ms(t_obj)} | {ms(t_col)} | {ms(t_npf)} "
              f"| {ms(t_npb)} | {ms(t_c)} | {ms(t_cells)} |")

    # ── per-row and per-survivor decomposition at the realistic size ───────
    print()
    n = 31_250
    rows = make_rows(n)
    surv = len(scan_objects(rows, s, k=k))
    t_full, _ = timeit(scan_objects, rows, s, k=k)
    # a scan that rejects everything: box outside the city
    s_far = Searcher(radius_km=8, mode=0, lat=0.0, lng=0.0)
    t_reject, _ = timeit(scan_objects, rows, s_far)
    print(f"decomposition at {n:,} rows, {surv} survivors "
          f"({(t_full):.6f}s total):")
    print(f"  reject-only scan (box misses every row): {t_reject*1e6:8.1f} us "
          f"= {t_reject/n*1e9:.1f} ns/row")
    print(f"  eight terms on survivors:                "
          f"{(t_full - t_reject)*1e6:8.1f} us "
          f"= {(t_full - t_reject)/max(surv,1)*1e6:.2f} us/survivor")

    # ── survivor-count sweep at fixed shard size ───────────────────────────
    print()
    print("| radius km | in-box+in-ring | objects ms | us/survivor |")
    print("|---|---|---|---|")
    for r in (3, 5, 8, 15, 25, 60):
        sr = Searcher(radius_km=r, mode=0)
        kr = SearcherConstants(sr)
        cnt = len(scan_objects(rows, sr, k=kr))
        t, _ = timeit(scan_objects, rows, sr, k=kr)
        print(f"| {r} | {cnt} | {t*1e3:.3f} | "
              f"{(t - t_reject)/max(cnt,1)*1e6:.2f} |")


if __name__ == "__main__":
    main()
