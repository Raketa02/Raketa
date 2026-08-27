"""Ticket #161 item 5 — what a rebuild actually costs, and what determines it.

The replay now runs inside the backend against its own event store, so the
work is: read envelopes -> decode payload -> dispatch to a projection ->
mutate a row. This measures the Python half of that (decode + dispatch +
apply) exactly, and states the read half as an estimate with its inputs,
because there is no production-sized event store to read from.

Run: python rebuild_bench.py
"""
from __future__ import annotations

import os
import random
import statistics
import sys
import time
import uuid

try:
    import orjson as _j

    def dumps(o):
        return _j.dumps(o)

    def loads(b):
        return _j.loads(b)
    JSON = "orjson"
except ImportError:
    import json as _j

    def dumps(o):
        return _j.dumps(o).encode()

    def loads(b):
        return _j.loads(b)
    JSON = "json"

from population import CandidateRow

PLAYERS = 50_000
SPORTS_PER_PLAYER = 2.5

# events per player, from §7.3's table
EVENTS_PER_PLAYER = {
    "player_profile.created": 1,
    "player_profile.social_tags_changed": 1.5,
    "player_profile.availability_changed": 2.0,
    "player_profile.location_changed": 0.3,
    "player_profile.search_radius_changed": 0.4,
    "player_profile.proposals_opt_in_answered": 1,
    "player_profile.play_intent_declared": 1.2,
    "rating.created": SPORTS_PER_PLAYER,
    "rating.updated": SPORTS_PER_PLAYER * 4,   # one per counted game, capped
}


def make_envelopes(n_players, seed=11):
    rng = random.Random(seed)
    env = []
    for p in range(n_players):
        pid = p
        for etype, per in EVENTS_PER_PLAYER.items():
            k = int(per) + (1 if rng.random() < (per - int(per)) else 0)
            for _ in range(k):
                if etype.startswith("rating"):
                    payload = {"player_id": pid, "sport": rng.randrange(4),
                               "mu": rng.uniform(1, 5), "sigma": rng.uniform(.05, .6),
                               "confidence": rng.randrange(100),
                               "counted_games": rng.randrange(200),
                               "status": "ESTABLISHED"}
                elif etype == "player_profile.created":
                    payload = {"player_id": pid, "tags": rng.getrandbits(18),
                               "grid": rng.getrandbits(21),
                               "lat": 50.0 + rng.random(), "lng": 19.9 + rng.random(),
                               "radius_km": rng.choice((5, 8, 10)),
                               "opt_in": True, "intent": rng.randrange(3),
                               "shard": "krakow"}
                else:
                    payload = {"player_id": pid, "value": rng.getrandbits(21)}
                env.append((str(uuid.uuid4()), etype, 1, dumps(payload),
                            1_756_000_000 + rng.randrange(10_000_000)))
    rng.shuffle(env)
    return env


def build_index(envelopes):
    """The projection: one dict keyed (player, sport), idempotent per §7.3."""
    index = {}
    for event_id, etype, ver, payload, occurred in envelopes:
        d = loads(payload)
        pid = d["player_id"]
        if etype.startswith("rating"):
            key = (pid, d["sport"])
            row = index.get(key)
            if row is None:
                row = index[key] = CandidateRow(player_id=pid, sport=d["sport"],
                                                shard_key="krakow", tags=0, grid=0,
                                                grid_bits=0)
            if getattr(row, "rating_updated_at", 0) or 0 <= occurred:
                row.mu = d["mu"]
                row.sigma = d["sigma"]
                row.confidence = d["confidence"]
                row.counted_games = d["counted_games"]
                row.rating_status = 0
                row.rating_updated_at = occurred
        elif etype == "player_profile.created":
            for sp in range(4):
                key = (pid, sp)
                row = index.get(key)
                if row is None:
                    row = index[key] = CandidateRow(player_id=pid, sport=sp,
                                                    shard_key=d["shard"])
                row.tags = d["tags"]
                row.grid = d["grid"]
                row.grid_bits = int(d["grid"]).bit_count()
                row.area_lat = d["lat"]
                row.area_lng = d["lng"]
                row.search_radius_km = d["radius_km"]
                row.proposals_opt_in = d["opt_in"]
                row.play_intent = d["intent"]
                row.profile_updated_at = occurred
        else:
            for sp in range(4):
                row = index.get((pid, sp))
                if row is None:
                    continue
                if (getattr(row, "profile_updated_at", 0) or 0) <= occurred:
                    row.grid = d["value"]
                    row.grid_bits = int(d["value"]).bit_count()
                    row.profile_updated_at = occurred
    return index


def main():
    print(f"# rebuild_bench — CPython {sys.version.split()[0]} on {os.uname().machine}, "
          f"{JSON}")
    print()
    n = 5_000
    env = make_envelopes(n)
    per_player = len(env) / n
    t0 = time.perf_counter()
    idx = build_index(env)
    dt = time.perf_counter() - t0
    print(f"- events per player, from §7.3's table: **{per_player:.1f}**")
    print(f"- {n:,} players -> {len(env):,} events -> {len(idx):,} index rows")
    print(f"- decode + dispatch + apply, single-threaded: **{dt:.2f} s** "
          f"= {dt / len(env) * 1e6:.2f} us/event")
    rate = len(env) / dt

    # decode alone, so the split is visible
    payloads = [e[3] for e in env[:200_000]]
    t0 = time.perf_counter()
    for p in payloads:
        loads(p)
    t_dec = time.perf_counter() - t0
    print(f"- of which {JSON} decode alone: {t_dec / len(payloads) * 1e6:.2f} us/event "
          f"({t_dec / len(payloads) / (dt / len(env)) * 100:.0f}%)")
    print()
    print("## Extrapolation")
    print()
    print("| city size | players | events | projection CPU (single core) |")
    print("|---|---|---|---|")
    for label, players in (("§7.4's target", 50_000), ("ten cities", 500_000)):
        ev = players * per_player
        print(f"| {label} | {players:,} | {ev / 1e6:.2f} M | "
              f"{ev / rate:.0f} s = {ev / rate / 60:.1f} min |")
    print()
    print(f"Measured projection throughput: **{rate:,.0f} events/s** on one core.")
    print(f"The five-minute budget therefore buys "
          f"**{rate * 300 / 1e6:.1f} M events** of projection on one core, "
          f"before any time is spent reading them.")


if __name__ == "__main__":
    main()
