"""Stage 2 (generate) + Stage 3 (the eight Fit terms), three ways.

The maths is §9.2 and §9.3.1-§9.3.8 of the design document, implemented as a
competent implementer would: every searcher-side constant hoisted out of the
loop, no allocation per rejected row, bounding-box early-out before anything
numeric.

Evidence objects are NOT built in the hot loop; the shortlist is re-scored with
evidence afterwards, which is what makes the eight-term loop worth measuring on
its own. serialise_bench.py measures the evidence half separately.
"""
from __future__ import annotations

from math import asin, cos, exp, radians, sin, sqrt

# -- §9.3 constants (ruleset "bench", stand-ins for the real numbers) --------
LEVEL_TOL_COMP = 0.55
FUN_FREE_BAND = 0.25
LEVEL_TOL_FUN = 0.90
PROX_TAU = 5.0
PHI = 0.45
CLASH_CAP = 0.25
SCORE_MIN = 70

W_COMP = (26.0, 17.0, 14.0, 13.0, 11.0, 9.0, 6.0, 4.0)
W_FUN = (11.0, 6.0, 14.0, 9.0, 16.0, 11.0, 11.0, 22.0)

STYLE_MASK = 0b000000000000111111       # tags 0-5, the ON_THE_COURT group
VIBE_MASK = 0b111111111111000000        # AFTER_THE_MATCH + WHY_YOU_ARE_HERE

# diminishing returns dr(n) = 1 - phi**n, precomputed for 0..18 tags
DR = tuple(1.0 - PHI ** n for n in range(19))
# proximity exp(-days/PROX_TAU), precomputed for the 21 grid slots (3 per day)
PROX = tuple(exp(-(i // 3) / PROX_TAU) for i in range(21))
# intent alignment table: [mode][their_intent]
INTENT = ((1.0, 0.15, 0.6), (0.15, 1.0, 0.6), (0.6, 0.6, 1.0))

EARTH_R = 6371.0088


def searcher_masks(tags: int):
    """Complement and clash masks for this searcher's tags, per §9.3.6.

    A real ruleset ships the pair tables; here they are derived
    deterministically from the tag ids so the *shape* of the work is right
    (one AND + one popcount per group, per candidate).
    """
    comp = clash = 0
    t = tags
    while t:
        b = t & -t
        i = b.bit_length() - 1
        comp |= (1 << ((i + 5) % 18)) | (1 << ((i + 11) % 18))
        clash |= 1 << ((i + 9) % 18)
        t ^= b
    return comp, clash


class SearcherConstants:
    """Everything hoisted out of the per-row loop, computed once per search."""

    __slots__ = ("mode", "w", "intent_row", "r_km", "lat0", "lng0", "lat_lo",
                 "lat_hi", "lng_lo", "lng_hi", "mu0", "sig0sq", "grid0",
                 "grid0_bits", "inv_mine", "comp_sty", "comp_vib", "clash_sty",
                 "clash_vib", "tags0_sty", "tags0_vib", "inv_tol", "fun_span",
                 "d_hi", "d_span", "lat0r", "sport")

    def __init__(self, s):
        self.mode = s.mode
        self.w = W_COMP if s.mode == 0 else W_FUN
        self.intent_row = INTENT[s.mode]
        self.r_km = r_km = s.radius_km
        self.lat0, self.lng0 = s.lat, s.lng
        dlat = r_km / 110.574
        dlng = r_km / (111.320 * cos(radians(s.lat)))
        self.lat_lo, self.lat_hi = s.lat - dlat, s.lat + dlat
        self.lng_lo, self.lng_hi = s.lng - dlng, s.lng + dlng
        self.mu0 = s.mu
        self.sig0sq = s.sigma * s.sigma
        self.grid0 = s.grid
        self.grid0_bits = s.grid_bits
        self.inv_mine = 1.0 / s.grid_bits if s.grid_bits else 0.0
        comp, clash = searcher_masks(s.tags)
        self.comp_sty, self.comp_vib = comp & STYLE_MASK, comp & VIBE_MASK
        self.clash_sty, self.clash_vib = clash & STYLE_MASK, clash & VIBE_MASK
        self.tags0_sty = s.tags & STYLE_MASK
        self.tags0_vib = s.tags & VIBE_MASK
        self.inv_tol = 1.0 / LEVEL_TOL_COMP
        self.fun_span = 1.0 / (LEVEL_TOL_FUN - FUN_FREE_BAND)
        self.d_hi = 1.15 * r_km
        self.d_span = 1.0 / (0.45 * r_km)
        self.lat0r = radians(s.lat)
        self.sport = s.sport


# -- (a) plain Python objects ------------------------------------------------
def scan_objects(rows, s, live_reliability=False, k=None):
    """Linear scan with box early-out, then eight terms on survivors."""
    k = k or SearcherConstants(s)
    mode = k.mode
    (w_lvl, w_bal, w_int, w_rel, w_avl, w_sty, w_vib, w_dst) = k.w
    intent_row = k.intent_row
    r_km, lat0r, lng0 = k.r_km, k.lat0r, k.lng0
    lat_lo, lat_hi, lng_lo, lng_hi = k.lat_lo, k.lat_hi, k.lng_lo, k.lng_hi
    mu0, sig0sq = k.mu0, k.sig0sq
    grid0, grid0_bits, inv_mine = k.grid0, k.grid0_bits, k.inv_mine
    comp_sty, comp_vib = k.comp_sty, k.comp_vib
    clash_sty, clash_vib = k.clash_sty, k.clash_vib
    tags0_sty, tags0_vib = k.tags0_sty, k.tags0_vib
    inv_tol, fun_span = k.inv_tol, k.fun_span
    d_hi, d_span, sport = k.d_hi, k.d_span, k.sport
    cos_lat0 = cos(lat0r)

    out = []
    ap = out.append
    for c in rows:
        # -- Stage 2: shard is the bucket; sport and the box are the scan --
        if c.sport != sport:
            continue
        clat = c.area_lat
        if clat < lat_lo or clat > lat_hi:
            continue
        clng = c.area_lng
        if clng < lng_lo or clng > lng_hi:
            continue
        # -- Stage 1 gates that are index-local (§9.1) --
        if not c.photo_ok:
            continue
        if c.rating_status == 2:            # NO_RATING
            continue
        if c.proposals_opt_in is False and mode == 2:
            continue

        # -- §9.3.8 distance (the ring itself is a gate, §9.1) --
        clatr = radians(clat)
        la = clatr - lat0r
        lo = radians(clng - lng0)
        sla = sin(la * 0.5)
        slo = sin(lo * 0.5)
        km = 2.0 * EARTH_R * asin(sqrt(sla * sla + cos_lat0 * cos(clatr) * slo * slo))
        if km > r_km:
            continue
        v_dst = (d_hi - km) * d_span
        if v_dst > 1.0:
            v_dst = 1.0
        elif v_dst < 0.0:
            v_dst = 0.0

        wsum = 0.0
        acc = 0.0

        # -- §9.3.1 level fit --
        d = c.mu - mu0
        if d < 0.0:
            d = -d
        if mode == 0:
            v = 1.0 - d * inv_tol
        else:
            v = 1.0 - (d - FUN_FREE_BAND) * fun_span if d > FUN_FREE_BAND else 1.0
        if v < 0.0:
            v = 0.0
        acc += w_lvl * v
        wsum += w_lvl

        # -- §9.3.2 predicted balance --
        csig = c.sigma
        pct = 100.0 - d * 145.0 - sqrt(sig0sq + csig * csig) * 32.0
        if pct < 35.0:
            pct = 35.0
        elif pct > 96.0:
            pct = 96.0
        acc += w_bal * ((pct - 35.0) * 0.01639344262295082)
        wsum += w_bal

        # -- §9.3.3 intent alignment --
        acc += w_int * intent_row[c.play_intent]
        wsum += w_int

        # -- §9.3.4 reliability (NoEvidence until the player_score context) --
        if live_reliability:
            ss = c.strand_shows_up
            if ss is not None:
                rel = (25 * ss + 22 * c.strand_answers + 24 * c.strand_confirms
                       + 14 * c.strand_keeps_plans + 10 * c.strand_settles_up
                       + 5 * c.strand_sportsmanship) * 0.0001
                acc += w_rel * rel
                wsum += w_rel
                if c.player_score < SCORE_MIN:
                    acc -= 12.0

        # -- §9.3.5 availability overlap --
        sh = grid0 & c.grid
        if sh and grid0_bits:
            n_sh = sh.bit_count()
            theirs = c.grid_bits
            v = (0.55 * (n_sh * inv_mine)
                 + 0.25 * (n_sh / (theirs if theirs < grid0_bits else grid0_bits))
                 + 0.20 * PROX[(sh & -sh).bit_length() - 1]) * c.grid_staleness
            acc += w_avl * v
            wsum += w_avl

        # -- §9.3.6 playing style --
        ct = c.tags
        st = DR[(tags0_sty & ct).bit_count()] + 0.7 * DR[(comp_sty & ct).bit_count()]
        pen = (clash_sty & ct).bit_count() * 0.15
        st -= CLASH_CAP if pen > CLASH_CAP else pen
        if st > 1.0:
            st = 1.0
        elif st < 0.0:
            st = 0.0
        acc += w_sty * st * c.tag_staleness
        wsum += w_sty

        # -- §9.3.7 social vibe --
        vb = DR[(tags0_vib & ct).bit_count()] + 0.7 * DR[(comp_vib & ct).bit_count()]
        pen = (clash_vib & ct).bit_count() * 0.15
        vb -= CLASH_CAP if pen > CLASH_CAP else pen
        if vb > 1.0:
            vb = 1.0
        elif vb < 0.0:
            vb = 0.0
        acc += w_vib * vb * c.tag_staleness
        wsum += w_vib

        acc += w_dst * v_dst
        wsum += w_dst

        ap((acc / wsum * 100.0, c.player_id))
    return out


# -- (b) array/struct-packed columns -----------------------------------------
def scan_columns(cols, s, live_reliability=False, k=None):
    k = k or SearcherConstants(s)
    mode = k.mode
    (w_lvl, w_bal, w_int, w_rel, w_avl, w_sty, w_vib, w_dst) = k.w
    intent_row = k.intent_row
    r_km, lat0r, lng0 = k.r_km, k.lat0r, k.lng0
    lat_lo, lat_hi, lng_lo, lng_hi = k.lat_lo, k.lat_hi, k.lng_lo, k.lng_hi
    mu0, sig0sq = k.mu0, k.sig0sq
    grid0, grid0_bits, inv_mine = k.grid0, k.grid0_bits, k.inv_mine
    comp_sty, comp_vib = k.comp_sty, k.comp_vib
    clash_sty, clash_vib = k.clash_sty, k.clash_vib
    tags0_sty, tags0_vib = k.tags0_sty, k.tags0_vib
    inv_tol, fun_span = k.inv_tol, k.fun_span
    d_hi, d_span, sport = k.d_hi, k.d_span, k.sport
    cos_lat0 = cos(lat0r)

    a_sport, a_lat, a_lng = cols.sport, cols.lat, cols.lng
    a_mu, a_sigma, a_tags, a_grid = cols.mu, cols.sigma, cols.tags, cols.grid
    a_gb, a_int, a_flags, a_stale = (cols.grid_bits, cols.intent, cols.flags,
                                     cols.staleness)
    a_pid = cols.player_id
    s_shows, s_ans, s_conf = cols.s_shows, cols.s_answers, cols.s_confirms
    s_plans, s_set, s_sp = cols.s_plans, cols.s_settles, cols.s_sport

    out = []
    ap = out.append
    for i in range(cols.n):
        if a_sport[i] != sport:
            continue
        clat = a_lat[i]
        if clat < lat_lo or clat > lat_hi:
            continue
        clng = a_lng[i]
        if clng < lng_lo or clng > lng_hi:
            continue
        f = a_flags[i]
        if not (f & 1) or not (f & 4):
            continue
        if (f & 2) and mode == 2:
            continue

        clatr = radians(clat)
        la = clatr - lat0r
        lo = radians(clng - lng0)
        sla = sin(la * 0.5)
        slo = sin(lo * 0.5)
        km = 2.0 * EARTH_R * asin(sqrt(sla * sla + cos_lat0 * cos(clatr) * slo * slo))
        if km > r_km:
            continue
        v_dst = (d_hi - km) * d_span
        if v_dst > 1.0:
            v_dst = 1.0
        elif v_dst < 0.0:
            v_dst = 0.0

        wsum = 0.0
        acc = 0.0
        d = a_mu[i] - mu0
        if d < 0.0:
            d = -d
        if mode == 0:
            v = 1.0 - d * inv_tol
        else:
            v = 1.0 - (d - FUN_FREE_BAND) * fun_span if d > FUN_FREE_BAND else 1.0
        if v < 0.0:
            v = 0.0
        acc += w_lvl * v
        wsum += w_lvl

        cs = a_sigma[i]
        pct = 100.0 - d * 145.0 - sqrt(sig0sq + cs * cs) * 32.0
        if pct < 35.0:
            pct = 35.0
        elif pct > 96.0:
            pct = 96.0
        acc += w_bal * ((pct - 35.0) * 0.01639344262295082)
        wsum += w_bal

        acc += w_int * intent_row[a_int[i]]
        wsum += w_int

        if live_reliability:
            rel = (25 * s_shows[i] + 22 * s_ans[i] + 24 * s_conf[i]
                   + 14 * s_plans[i] + 10 * s_set[i] + 5 * s_sp[i]) * 0.0001
            acc += w_rel * rel
            wsum += w_rel

        sh = grid0 & a_grid[i]
        if sh and grid0_bits:
            n_sh = sh.bit_count()
            theirs = a_gb[i]
            v = (0.55 * (n_sh * inv_mine)
                 + 0.25 * (n_sh / (theirs if theirs < grid0_bits else grid0_bits))
                 + 0.20 * PROX[(sh & -sh).bit_length() - 1]) * a_stale[i]
            acc += w_avl * v
            wsum += w_avl

        ct = a_tags[i]
        st = DR[(tags0_sty & ct).bit_count()] + 0.7 * DR[(comp_sty & ct).bit_count()]
        pen = (clash_sty & ct).bit_count() * 0.15
        st -= CLASH_CAP if pen > CLASH_CAP else pen
        if st > 1.0:
            st = 1.0
        elif st < 0.0:
            st = 0.0
        acc += w_sty * st
        wsum += w_sty

        vb = DR[(tags0_vib & ct).bit_count()] + 0.7 * DR[(comp_vib & ct).bit_count()]
        pen = (clash_vib & ct).bit_count() * 0.15
        vb -= CLASH_CAP if pen > CLASH_CAP else pen
        if vb > 1.0:
            vb = 1.0
        elif vb < 0.0:
            vb = 0.0
        acc += w_vib * vb
        wsum += w_vib

        acc += w_dst * v_dst
        wsum += w_dst
        ap((acc / wsum * 100.0, a_pid[i]))
    return out
