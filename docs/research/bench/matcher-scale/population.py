"""Synthetic candidate population for the matcher-scale benchmarks.

Field list is §7.2 of docs/specs/matchmaking/matchmaking-engine.md, verbatim.
Everything is seeded, so every number in docs/research/matcher-scale-in-python.md
is reproducible.
"""
from __future__ import annotations

import math
import random
from array import array

SPORTS = ("PADEL", "TENNIS", "SQUASH", "BADMINTON")
INTENTS = (0, 1, 2)  # COMPETITIVE, FOR_FUN, NO_PREFERENCE

# Kraków, the document's own worked example.
CITY_LAT, CITY_LNG = 50.048, 19.944
CITY_SPREAD_KM = 9.0  # ~1 sigma of the population around the centre

KM_PER_DEG_LAT = 110.574


def km_per_deg_lng(lat: float) -> float:
    return 111.320 * math.cos(math.radians(lat))


class CandidateRow:
    """The §7.2 row as an ordinary Python object with __slots__.

    __slots__ rather than a dict-carrying class or a dataclass, because that is
    the cheapest plain-object form; the memory bench measures the others too.
    """

    __slots__ = (
        "player_id", "sport",
        "mu", "sigma", "confidence", "counted_games",
        "calibration_priority", "rating_status", "rating_updated_at",
        "play_intent", "tags", "tags_updated_at", "grid", "grid_updated_at",
        "area_cell", "area_lat", "area_lng", "search_radius_km",
        "proposals_opt_in", "profile_updated_at",
        "player_score", "strand_shows_up", "strand_settles_up",
        "strand_answers", "strand_confirms", "strand_keeps_plans",
        "strand_sportsmanship", "opponent_variety",
        "last_active_at", "open_challenges", "first_seen_at",
        "shard_key",
        # derived at index-build time, not part of §7.2's wire shape
        "grid_bits", "tag_staleness", "grid_staleness", "photo_ok",
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def make_rows(n: int, seed: int = 20260826, with_player_score: bool = False,
              shard: str = "krakow"):
    """n candidate rows for one shard, sports mixed as the document's 2.5x."""
    rng = random.Random(seed)
    rows = []
    base_ts = 1_756_000_000  # epoch seconds, late Aug 2026
    for i in range(n):
        lat = CITY_LAT + rng.gauss(0, CITY_SPREAD_KM / KM_PER_DEG_LAT)
        lng = CITY_LNG + rng.gauss(0, CITY_SPREAD_KM / km_per_deg_lng(CITY_LAT))
        grid = rng.getrandbits(21)
        tags = 0
        for _ in range(rng.randint(2, 6)):
            tags |= 1 << rng.randrange(18)
        ps = rng.randint(55, 100) if with_player_score else None
        rows.append(CandidateRow(
            player_id=i,
            sport=rng.randrange(4),
            mu=rng.uniform(1.0, 5.0),
            sigma=rng.uniform(0.05, 0.60),
            confidence=rng.randint(0, 100),
            counted_games=rng.randint(0, 200),
            calibration_priority=rng.randrange(3),
            rating_status=rng.choice((0, 0, 0, 1)),  # 1 == INITIAL_ESTIMATE
            rating_updated_at=base_ts - rng.randrange(3_000_000),
            play_intent=rng.randrange(3),
            tags=tags,
            tags_updated_at=base_ts - rng.randrange(30_000_000),
            grid=grid,
            grid_updated_at=base_ts - rng.randrange(30_000_000),
            area_cell=rng.randrange(1 << 24),
            area_lat=lat,
            area_lng=lng,
            search_radius_km=rng.choice((3, 5, 8, 8, 10, 15, 25)),
            proposals_opt_in=rng.choice((True, True, True, False, None)),
            profile_updated_at=base_ts - rng.randrange(30_000_000),
            player_score=ps,
            strand_shows_up=rng.randint(40, 100) if with_player_score else None,
            strand_settles_up=rng.randint(40, 100) if with_player_score else None,
            strand_answers=rng.randint(40, 100) if with_player_score else None,
            strand_confirms=rng.randint(40, 100) if with_player_score else None,
            strand_keeps_plans=rng.randint(40, 100) if with_player_score else None,
            strand_sportsmanship=rng.randint(40, 100) if with_player_score else None,
            opponent_variety=rng.randint(0, 100) if with_player_score else None,
            last_active_at=base_ts - rng.randrange(2_000_000),
            open_challenges=rng.randrange(6),
            first_seen_at=base_ts - rng.randrange(60_000_000),
            shard_key=shard,
            grid_bits=grid.bit_count(),
            tag_staleness=1.0 - rng.random() * 0.4,
            grid_staleness=1.0 - rng.random() * 0.4,
            photo_ok=rng.random() > 0.05,
        ))
    return rows


class Columns:
    """The same population as array/struct-packed columns (escape route b)."""

    __slots__ = ("n", "sport", "mu", "sigma", "lat", "lng", "tags", "grid",
                 "grid_bits", "intent", "radius", "flags", "staleness",
                 "s_shows", "s_settles", "s_answers", "s_confirms",
                 "s_plans", "s_sport", "player_id")

    def __init__(self, rows):
        self.n = len(rows)
        self.player_id = array("I", (r.player_id for r in rows))
        self.sport = array("B", (r.sport for r in rows))
        self.mu = array("f", (r.mu for r in rows))
        self.sigma = array("f", (r.sigma for r in rows))
        self.lat = array("f", (r.area_lat for r in rows))
        self.lng = array("f", (r.area_lng for r in rows))
        self.tags = array("I", (r.tags for r in rows))
        self.grid = array("I", (r.grid for r in rows))
        self.grid_bits = array("B", (r.grid_bits for r in rows))
        self.intent = array("B", (r.play_intent for r in rows))
        self.radius = array("B", (r.search_radius_km for r in rows))
        # bit 0 photo_ok, bit 1 proposals_opt_in is False, bit 2 rated
        self.flags = array("B", (
            (1 if r.photo_ok else 0)
            | (2 if r.proposals_opt_in is False else 0)
            | (4 if r.rating_status != 2 else 0)
            for r in rows))
        self.staleness = array("f", (r.grid_staleness for r in rows))
        self.s_shows = array("B", (r.strand_shows_up or 0 for r in rows))
        self.s_settles = array("B", (r.strand_settles_up or 0 for r in rows))
        self.s_answers = array("B", (r.strand_answers or 0 for r in rows))
        self.s_confirms = array("B", (r.strand_confirms or 0 for r in rows))
        self.s_plans = array("B", (r.strand_keeps_plans or 0 for r in rows))
        self.s_sport = array("B", (r.strand_sportsmanship or 0 for r in rows))


class Searcher:
    __slots__ = ("mu", "sigma", "lat", "lng", "radius_km", "tags", "grid",
                 "grid_bits", "mode", "sport")

    def __init__(self, mu=2.71, sigma=0.16, lat=CITY_LAT, lng=CITY_LNG,
                 radius_km=8, tags=0b000000101000010101, grid=0b001001001000011111011,
                 mode=0, sport=0):
        self.mu, self.sigma = mu, sigma
        self.lat, self.lng = lat, lng
        self.radius_km = radius_km
        self.tags, self.grid = tags, grid
        self.grid_bits = grid.bit_count()
        self.mode, self.sport = mode, sport
