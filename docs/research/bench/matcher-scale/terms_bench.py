"""Ticket #161 item 1, decomposition — where the microsecond per candidate goes.

Each term is timed in isolation over the same survivor block, with the cost of
the bare `for` loop subtracted. Useful for one decision only: if the loop ever
needs to be cheaper, this says which term to attack first.

Run: python terms_bench.py
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from math import asin, cos, radians, sin, sqrt

from population import Searcher, make_rows
from scoring import (CLASH_CAP, DR, EARTH_R, INTENT, PROX, SearcherConstants,
                     STYLE_MASK, VIBE_MASK, searcher_masks)


def med(fn, budget=1.0):
    fn()
    t0 = time.perf_counter()
    fn()
    one = time.perf_counter() - t0
    reps = max(5, min(3000, int(budget / max(one, 1e-7))))
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts)


def main():
    print(f"# terms_bench — CPython {sys.version.split()[0]} on {os.uname().machine}")
    print()
    s = Searcher(radius_km=8, mode=0)
    k = SearcherConstants(s)
    rows = make_rows(31_250)
    block = [c for c in rows
             if c.sport == k.sport
             and k.lat_lo <= c.area_lat <= k.lat_hi
             and k.lng_lo <= c.area_lng <= k.lng_hi]
    n = len(block)

    mu0, sig0sq = k.mu0, k.sig0sq
    grid0, gb0, inv_mine = k.grid0, k.grid0_bits, k.inv_mine
    lat0r, lng0, cos_lat0 = k.lat0r, k.lng0, cos(k.lat0r)
    comp, clash = searcher_masks(s.tags)
    ts_, tv_ = s.tags & STYLE_MASK, s.tags & VIBE_MASK
    cs_, cv_ = comp & STYLE_MASK, comp & VIBE_MASK
    ks_, kv_ = clash & STYLE_MASK, clash & VIBE_MASK
    intent_row = k.intent_row
    d_hi, d_span = k.d_hi, k.d_span

    def empty():
        a = 0.0
        for c in block:
            a += 1.0
        return a

    def level():
        a = 0.0
        for c in block:
            d = c.mu - mu0
            if d < 0.0:
                d = -d
            v = 1.0 - d * 1.8181818
            a += v if v > 0.0 else 0.0
        return a

    def balance():
        a = 0.0
        for c in block:
            d = c.mu - mu0
            if d < 0.0:
                d = -d
            cs = c.sigma
            pct = 100.0 - d * 145.0 - sqrt(sig0sq + cs * cs) * 32.0
            if pct < 35.0:
                pct = 35.0
            elif pct > 96.0:
                pct = 96.0
            a += (pct - 35.0) * 0.016393
        return a

    def intent():
        a = 0.0
        for c in block:
            a += intent_row[c.play_intent]
        return a

    rel_rows = make_rows(31_250, with_player_score=True)
    rel_block = rel_rows[:len(block)]

    def rel_empty():
        a = 0.0
        for c in rel_block:
            a += 1.0
        return a

    def reliability():
        a = 0.0
        for c in rel_block:
            ss = c.strand_shows_up
            if ss is not None:
                a += (25 * ss + 22 * c.strand_answers + 24 * c.strand_confirms
                      + 14 * c.strand_keeps_plans + 10 * c.strand_settles_up
                      + 5 * c.strand_sportsmanship) * 0.0001
        return a

    def availability():
        a = 0.0
        for c in block:
            sh = grid0 & c.grid
            if sh:
                n_sh = sh.bit_count()
                theirs = c.grid_bits
                a += (0.55 * (n_sh * inv_mine)
                      + 0.25 * (n_sh / (theirs if theirs < gb0 else gb0))
                      + 0.20 * PROX[(sh & -sh).bit_length() - 1]) * c.grid_staleness
        return a

    def style():
        a = 0.0
        for c in block:
            ct = c.tags
            st = DR[(ts_ & ct).bit_count()] + 0.7 * DR[(cs_ & ct).bit_count()]
            pen = (ks_ & ct).bit_count() * 0.15
            st -= CLASH_CAP if pen > CLASH_CAP else pen
            if st > 1.0:
                st = 1.0
            elif st < 0.0:
                st = 0.0
            a += st * c.tag_staleness
        return a

    def vibe():
        a = 0.0
        for c in block:
            ct = c.tags
            vb = DR[(tv_ & ct).bit_count()] + 0.7 * DR[(cv_ & ct).bit_count()]
            pen = (kv_ & ct).bit_count() * 0.15
            vb -= CLASH_CAP if pen > CLASH_CAP else pen
            if vb > 1.0:
                vb = 1.0
            elif vb < 0.0:
                vb = 0.0
            a += vb * c.tag_staleness
        return a

    def distance_haversine():
        a = 0.0
        for c in block:
            clatr = radians(c.area_lat)
            sla = sin((clatr - lat0r) * 0.5)
            slo = sin(radians(c.area_lng - lng0) * 0.5)
            km = 2.0 * EARTH_R * asin(
                sqrt(sla * sla + cos_lat0 * cos(clatr) * slo * slo))
            v = (d_hi - km) * d_span
            a += 1.0 if v > 1.0 else (0.0 if v < 0.0 else v)
        return a

    def distance_equirect():
        a = 0.0
        kx = 111.320 * cos_lat0
        for c in block:
            dx = (c.area_lng - lng0) * kx
            dy = (c.area_lat - k.lat0) * 110.574
            km = sqrt(dx * dx + dy * dy)
            v = (d_hi - km) * d_span
            a += 1.0 if v > 1.0 else (0.0 if v < 0.0 else v)
        return a

    base = med(empty)
    print(f"block = {n} candidate rows; the bare `for` loop over it costs "
          f"{base * 1e6:.0f} us ({base / n * 1e9:.0f} ns/row) and is subtracted "
          f"from every row below.")
    print()
    print("| §9.3 term | us over the block | ns per candidate | share of the eight |")
    print("|---|---|---|---|")
    results = []
    for label, fn in (("1 level fit", level),
                      ("2 predicted balance", balance),
                      ("3 intent alignment", intent),
                      ("4 reliability (6 strands live)", reliability),
                      ("5 availability overlap", availability),
                      ("6 playing style", style),
                      ("7 social vibe", vibe),
                      ("8 distance — haversine", distance_haversine),
                      ("8 distance — equirectangular", distance_equirect)):
        b = med(rel_empty) if label.startswith("4 ") else base
        t = max(0.0, med(fn) - b)
        results.append((label, t))
    total = sum(t for lb, t in results if not lb.startswith("8 distance — equi"))
    for label, t in results:
        share = "" if label.startswith("8 distance — equi") else \
            f"{t / total * 100:.0f}%"
        print(f"| {label} | {t * 1e6:.0f} | {t / n * 1e9:.0f} | {share} |")
    print(f"| **sum of the eight (haversine)** | **{total * 1e6:.0f}** | "
          f"**{total / n * 1e9:.0f}** | 100% |")


if __name__ == "__main__":
    main()
