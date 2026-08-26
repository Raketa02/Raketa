"""Ticket #161 item 6 — the doubles group objective, §9.9, in Python.

C(15,3) = 455 combinations, three pairings each. The document calls this "tens
of microseconds"; that is a Go claim. Measured here in plain Python and in
numpy, and swept over K so the cost of moving the candidate cap is visible.

Run: python doubles_bench.py
"""
from __future__ import annotations

import math
import os
import statistics
import sys
import time
from itertools import combinations

from population import Searcher, make_rows
from scoring import SearcherConstants, scan_objects

# §9.9 constants
W_COMP = dict(bal=40.0, seatfit=22.0, minfit=18.0, intent=12.0, tag=8.0)
W_FUN = dict(bal=20.0, seatfit=20.0, minfit=14.0, intent=18.0, tag=28.0)
PARTNER_STYLE_MULTIPLIER = 1.6
OPPONENT_STYLE_MULTIPLIER = 0.7
QUALITY_FLOOR = 0.0   # the floor is a ruleset number; 0 keeps every combo in


def team_strength(a, b):
    return 0.45 * max(a, b) + 0.55 * min(a, b)


def group_objective(seats, w, viewer):
    """seats: 3 tuples (mu, sigma, fit, intent_ok, tags). viewer is the 4th."""
    best = None
    v_mu, v_sig, _, _, v_tags = viewer
    for i in range(3):
        partner = seats[i]
        opp = [seats[j] for j in range(3) if j != i]
        a = team_strength(v_mu, partner[0])
        b = team_strength(opp[0][0], opp[1][0])
        gap = a - b
        if gap < 0:
            gap = -gap
        if best is None or gap < best[0]:
            best = (gap, i, a, b)
    gap, i, a, b = best
    sig_group = math.sqrt(v_sig * v_sig + sum(s[1] * s[1] for s in seats))
    pct = 100.0 - gap * 145.0 - sig_group * 32.0
    if pct < 35.0:
        pct = 35.0
    elif pct > 96.0:
        pct = 96.0
    bal = (pct - 35.0) / 61.0

    fits = [s[2] for s in seats]
    mean_fit = (fits[0] + fits[1] + fits[2]) / 300.0
    min_fit = min(fits) / 100.0

    misaligned = 3 - sum(s[3] for s in seats)
    intent_coh = 1.0 - (misaligned / 3.0) ** 0.8

    # group_tag_coherence: tags held by >= ceil(3n/4) = 3 of the 4 seats
    all_tags = [v_tags] + [s[4] for s in seats]
    counts = {}
    for t in all_tags:
        x = t
        while x:
            b_ = x & -x
            k = b_.bit_length() - 1
            counts[k] = counts.get(k, 0) + 1
            x ^= b_
    coh = 0.0
    for k, c in counts.items():
        if c >= 3:
            coh += 1.0 - 0.45 ** c
    tag_coh = coh / 4.0
    if tag_coh > 1.0:
        tag_coh = 1.0

    partner_clash = 0.0  # PARTNER_STYLE_MULTIPLIER lands in the seat fit above

    return (w["bal"] * bal + w["seatfit"] * mean_fit + w["minfit"] * min_fit
            + w["intent"] * intent_coh + w["tag"] * tag_coh
            - partner_clash), i, pct


def enumerate_lineups(pool, viewer, w):
    best = None
    for combo in combinations(pool, 3):
        g, pairing, pct = group_objective(combo, w, viewer)
        if best is None or g > best[0]:
            best = (g, combo, pairing, pct)
    return best


def enumerate_lineups_np(pool, viewer, w, idx3):
    import numpy as np
    mu = np.array([p[0] for p in pool], dtype=np.float64)
    sg = np.array([p[1] for p in pool], dtype=np.float64)
    ft = np.array([p[2] for p in pool], dtype=np.float64)
    ok = np.array([p[3] for p in pool], dtype=np.float64)
    v_mu, v_sig = viewer[0], viewer[1]
    A, B, C = idx3[:, 0], idx3[:, 1], idx3[:, 2]
    mus = np.stack([mu[A], mu[B], mu[C]])          # 3 x n
    sgs = np.stack([sg[A], sg[B], sg[C]])
    fts = np.stack([ft[A], ft[B], ft[C]])
    oks = np.stack([ok[A], ok[B], ok[C]])
    gaps = np.empty((3, idx3.shape[0]))
    for i in range(3):
        j, k = [x for x in range(3) if x != i]
        a = 0.45 * np.maximum(v_mu, mus[i]) + 0.55 * np.minimum(v_mu, mus[i])
        b = 0.45 * np.maximum(mus[j], mus[k]) + 0.55 * np.minimum(mus[j], mus[k])
        gaps[i] = np.abs(a - b)
    gap = gaps.min(axis=0)
    sig_group = np.sqrt(v_sig ** 2 + (sgs ** 2).sum(axis=0))
    pct = np.clip(100.0 - gap * 145.0 - sig_group * 32.0, 35.0, 96.0)
    bal = (pct - 35.0) / 61.0
    mean_fit = fts.mean(axis=0) / 100.0
    min_fit = fts.min(axis=0) / 100.0
    intent_coh = 1.0 - ((3 - oks.sum(axis=0)) / 3.0) ** 0.8
    g = (w["bal"] * bal + w["seatfit"] * mean_fit + w["minfit"] * min_fit
         + w["intent"] * intent_coh)
    return int(g.argmax())


def main():
    print(f"# doubles_bench — CPython {sys.version.split()[0]} on {os.uname().machine}")
    print()
    s = Searcher(radius_km=8, mode=0)
    rows = make_rows(31_250)
    scored = sorted(scan_objects(rows, s, k=SearcherConstants(s)), reverse=True)
    by_id = {r.player_id: r for r in rows}

    print("| K | C(K-1,3) combos | plain Python ms | us/combo | numpy ms |")
    print("|---|---|---|---|---|")
    try:
        import numpy as np
    except ImportError:
        np = None

    for K in (8, 12, 16, 24, 32, 48, 64):
        top = scored[:K]
        viewer_row = (s.mu, s.sigma, 100.0, 1, s.tags)
        pool = []
        for fit, pid in top[1:]:
            r = by_id[pid]
            pool.append((r.mu, r.sigma, fit, 1 if r.play_intent == 0 else 0,
                         r.tags))
        n_combos = math.comb(len(pool), 3)

        # warm
        enumerate_lineups(pool, viewer_row, W_COMP)
        ts = []
        reps = max(3, min(500, int(0.7 / max(1e-6, _one(pool, viewer_row)))))
        for _ in range(reps):
            t0 = time.perf_counter()
            enumerate_lineups(pool, viewer_row, W_COMP)
            ts.append(time.perf_counter() - t0)
        t = statistics.median(ts)

        t_np = float("nan")
        if np is not None and n_combos:
            idx3 = np.array(list(combinations(range(len(pool)), 3)),
                            dtype=np.int64)
            enumerate_lineups_np(pool, viewer_row, W_COMP, idx3)
            tsn = []
            for _ in range(50):
                t0 = time.perf_counter()
                enumerate_lineups_np(pool, viewer_row, W_COMP, idx3)
                tsn.append(time.perf_counter() - t0)
            t_np = statistics.median(tsn)

        print(f"| {K} | {n_combos} | {t * 1e3:.3f} | "
              f"{t / max(n_combos, 1) * 1e6:.2f} | "
              f"{'—' if t_np != t_np else f'{t_np * 1e3:.3f}'} |")


def _one(pool, viewer):
    t0 = time.perf_counter()
    enumerate_lineups(pool, viewer, W_COMP)
    return time.perf_counter() - t0


if __name__ == "__main__":
    main()
