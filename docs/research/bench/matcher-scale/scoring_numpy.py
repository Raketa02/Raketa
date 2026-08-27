"""(c) numpy vectorisation over the shard, and over the candidate block only.

Two shapes are measured, because they answer different questions:

  * ``scan_numpy_full``   — the whole shard stays as numpy columns; the box test
    is a vectorised mask over every row, and the eight terms run over the
    survivors. This is what "hold the index as numpy" costs.
  * ``scan_numpy_block``  — the box test has already produced an index array
    (e.g. from a geo-cell bucket map) and only the candidate block is scored.
    This is what "vectorise the scoring, keep the generation cheap" costs.
"""
from __future__ import annotations

import numpy as np

from scoring import (CLASH_CAP, DR, EARTH_R, FUN_FREE_BAND, INTENT,
                     LEVEL_TOL_COMP, LEVEL_TOL_FUN, PROX, STYLE_MASK,
                     VIBE_MASK, W_COMP, W_FUN, searcher_masks)

DR_A = np.asarray(DR, dtype=np.float32)
PROX_A = np.asarray(PROX, dtype=np.float32)


class NpColumns:
    """The §7.2 row set as numpy columns."""

    def __init__(self, rows):
        self.n = len(rows)
        self.player_id = np.fromiter((r.player_id for r in rows), np.uint32, self.n)
        self.sport = np.fromiter((r.sport for r in rows), np.uint8, self.n)
        self.mu = np.fromiter((r.mu for r in rows), np.float32, self.n)
        self.sigma = np.fromiter((r.sigma for r in rows), np.float32, self.n)
        self.lat = np.fromiter((r.area_lat for r in rows), np.float32, self.n)
        self.lng = np.fromiter((r.area_lng for r in rows), np.float32, self.n)
        self.tags = np.fromiter((r.tags for r in rows), np.uint32, self.n)
        self.grid = np.fromiter((r.grid for r in rows), np.uint32, self.n)
        self.grid_bits = np.fromiter((r.grid_bits for r in rows), np.uint8, self.n)
        self.intent = np.fromiter((r.play_intent for r in rows), np.uint8, self.n)
        self.stale = np.fromiter((r.grid_staleness for r in rows), np.float32, self.n)
        self.tag_stale = np.fromiter((r.tag_staleness for r in rows), np.float32, self.n)
        self.ok = np.fromiter(
            (r.photo_ok and r.rating_status != 2 for r in rows), np.bool_, self.n)
        for name, attr in (("s_shows", "strand_shows_up"),
                           ("s_answers", "strand_answers"),
                           ("s_confirms", "strand_confirms"),
                           ("s_plans", "strand_keeps_plans"),
                           ("s_settles", "strand_settles_up"),
                           ("s_sport", "strand_sportsmanship")):
            setattr(self, name, np.fromiter(
                (getattr(r, attr) or 0 for r in rows), np.uint8, self.n))

    def nbytes(self):
        return sum(v.nbytes for v in self.__dict__.values()
                   if isinstance(v, np.ndarray))


def _terms(c, idx, s, k, live_reliability):
    """The eight terms, vectorised over the rows selected by ``idx``."""
    mode = s.mode
    (w_lvl, w_bal, w_int, w_rel, w_avl, w_sty, w_vib, w_dst) = (
        W_COMP if mode == 0 else W_FUN)
    mu = c.mu[idx]
    sigma = c.sigma[idx]
    lat = c.lat[idx].astype(np.float64)
    lng = c.lng[idx].astype(np.float64)
    tags = c.tags[idx]
    grid = c.grid[idx]

    lat0r = np.radians(s.lat)
    latr = np.radians(lat)
    sla = np.sin((latr - lat0r) * 0.5)
    slo = np.sin(np.radians(lng - s.lng) * 0.5)
    km = 2.0 * EARTH_R * np.arcsin(
        np.sqrt(sla * sla + np.cos(lat0r) * np.cos(latr) * slo * slo))
    inring = km <= s.radius_km
    v_dst = np.clip((1.15 * s.radius_km - km) / (0.45 * s.radius_km), 0.0, 1.0)

    d = np.abs(mu - s.mu)
    if mode == 0:
        v_lvl = np.clip(1.0 - d / LEVEL_TOL_COMP, 0.0, 1.0)
    else:
        v_lvl = np.clip(
            1.0 - np.maximum(0.0, d - FUN_FREE_BAND) / (LEVEL_TOL_FUN - FUN_FREE_BAND),
            0.0, 1.0)

    pct = np.clip(100.0 - d * 145.0
                  - np.sqrt(s.sigma * s.sigma + sigma * sigma) * 32.0, 35.0, 96.0)
    v_bal = (pct - 35.0) / 61.0

    v_int = np.asarray(INTENT[mode], dtype=np.float32)[c.intent[idx]]

    sh = np.bitwise_and(grid, np.uint32(s.grid))
    n_sh = np.bitwise_count(sh).astype(np.float32)
    theirs = np.maximum(c.grid_bits[idx], 1).astype(np.float32)
    lb = np.bitwise_and(sh, np.bitwise_not(sh) + np.uint32(1))   # lowest set bit
    slot = np.minimum(np.bitwise_count(lb - np.uint32(1)), 20)
    v_avl = np.where(
        sh == 0, 0.0,
        (0.55 * (n_sh / max(s.grid_bits, 1))
         + 0.25 * (n_sh / np.minimum(theirs, s.grid_bits))
         + 0.20 * PROX_A[slot]) * c.stale[idx])

    comp, clash = searcher_masks(s.tags)
    ts = np.uint32(s.tags & STYLE_MASK)
    tv = np.uint32(s.tags & VIBE_MASK)
    cs_ = np.uint32(comp & STYLE_MASK)
    cv_ = np.uint32(comp & VIBE_MASK)
    ks_ = np.uint32(clash & STYLE_MASK)
    kv_ = np.uint32(clash & VIBE_MASK)
    v_sty = np.clip(
        DR_A[np.bitwise_count(np.bitwise_and(tags, ts))]
        + 0.7 * DR_A[np.bitwise_count(np.bitwise_and(tags, cs_))]
        - np.minimum(CLASH_CAP,
                     np.bitwise_count(np.bitwise_and(tags, ks_)) * 0.15),
        0.0, 1.0) * c.tag_stale[idx]
    v_vib = np.clip(
        DR_A[np.bitwise_count(np.bitwise_and(tags, tv))]
        + 0.7 * DR_A[np.bitwise_count(np.bitwise_and(tags, cv_))]
        - np.minimum(CLASH_CAP,
                     np.bitwise_count(np.bitwise_and(tags, kv_)) * 0.15),
        0.0, 1.0) * c.tag_stale[idx]

    acc = (w_lvl * v_lvl + w_bal * v_bal + w_int * v_int
           + w_sty * v_sty + w_vib * v_vib + w_dst * v_dst)
    wsum = np.full(acc.shape, w_lvl + w_bal + w_int + w_sty + w_vib + w_dst,
                   dtype=np.float64)
    has_avl = sh != 0
    acc = acc + np.where(has_avl, w_avl * v_avl, 0.0)
    wsum = wsum + np.where(has_avl, w_avl, 0.0)

    if live_reliability:
        rel = (25 * c.s_shows[idx].astype(np.float32)
               + 22 * c.s_answers[idx] + 24 * c.s_confirms[idx]
               + 14 * c.s_plans[idx] + 10 * c.s_settles[idx]
               + 5 * c.s_sport[idx]) * 0.0001
        acc = acc + w_rel * rel
        wsum = wsum + w_rel

    fit = acc / wsum * 100.0
    return fit[inring], c.player_id[idx][inring]


def scan_numpy_full(c, s, live_reliability=False, k=None):
    """Box test vectorised over the whole shard, then terms on survivors."""
    dlat = s.radius_km / 110.574
    dlng = s.radius_km / (111.320 * np.cos(np.radians(s.lat)))
    m = ((c.sport == s.sport)
         & (c.lat >= s.lat - dlat) & (c.lat <= s.lat + dlat)
         & (c.lng >= s.lng - dlng) & (c.lng <= s.lng + dlng)
         & c.ok)
    idx = np.flatnonzero(m)
    return _terms(c, idx, s, k, live_reliability)


def scan_numpy_block(c, s, idx, live_reliability=False, k=None):
    """Terms only, over a candidate block someone else selected."""
    return _terms(c, idx, s, k, live_reliability)
