"""Ticket #161 item 7 — what a `CandidateSource` port costs, honestly.

Three granularities are measured, because they differ by four orders of
magnitude and the ADR's insurance only works at one of them:

  * **per search** — the port hands back one snapshot object and the loop runs
    over it directly (§15.2's shape);
  * **per row, attribute access** — the loop asks the port for each row;
  * **per row, method call** — the loop asks the port for each field.

Also here, because they are the other half of "does a search fit in a
request": what the §16 response costs to build and serialise, and what a
database query per search costs at its absolute floor (sqlite, in memory, no
wire protocol) as a lower bound on the Postgres alternative the port buys.

Run: python port_bench.py
"""
from __future__ import annotations

import os
import sqlite3
import statistics
import sys
import time
from typing import Protocol

from population import Searcher, make_rows
from scoring import SearcherConstants, scan_objects

N = 31_250


class Snapshot(Protocol):
    def rows(self): ...


class InMemorySnapshot:
    __slots__ = ("_rows", "version")

    def __init__(self, rows, version=1):
        self._rows = rows
        self.version = version

    def rows(self):
        return self._rows


class CandidateSource(Protocol):
    def snapshot(self, shard: str, sport: int) -> Snapshot: ...


class InMemoryCandidateSource:
    def __init__(self, rows):
        self._snap = InMemorySnapshot(rows)

    def snapshot(self, shard, sport):
        return self._snap


class RowByRowSource:
    """The shape that would actually be expensive: a port per row."""

    def __init__(self, rows):
        self._rows = rows

    def ids(self):
        return range(len(self._rows))

    def get(self, i):
        return self._rows[i]

    def mu(self, i):
        return self._rows[i].mu


def med(fn, reps=None, budget=1.0):
    fn()
    if reps is None:
        t0 = time.perf_counter()
        fn()
        one = time.perf_counter() - t0
        reps = max(3, min(3000, int(budget / max(one, 1e-7))))
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts)


def main():
    print(f"# port_bench — CPython {sys.version.split()[0]} on {os.uname().machine}")
    print()
    rows = make_rows(N)
    s = Searcher(radius_km=8, mode=0)
    k = SearcherConstants(s)

    direct = med(lambda: scan_objects(rows, s, k=k))
    src = InMemoryCandidateSource(rows)
    via_port = med(lambda: scan_objects(src.snapshot("krakow", 0).rows(), s, k=k))

    rbr = RowByRowSource(rows)

    def row_by_row():
        acc = 0.0
        get = rbr.get
        for i in rbr.ids():
            acc += get(i).mu
        return acc

    def field_by_field():
        acc = 0.0
        mu = rbr.mu
        for i in rbr.ids():
            acc += mu(i)
        return acc

    def inline_attr():
        acc = 0.0
        for r in rows:
            acc += r.mu
        return acc

    t_rbr = med(row_by_row)
    t_fbf = med(field_by_field)
    t_inl = med(inline_attr)

    print("| port granularity | ms per search | overhead vs direct |")
    print("|---|---|---|")
    print(f"| none — the loop owns the list | {direct * 1e3:.3f} | — |")
    print(f"| **per search** — `snapshot()` returns the list | {via_port * 1e3:.3f} | "
          f"{(via_port - direct) * 1e6:+.1f} us ({(via_port / direct - 1) * 100:+.2f}%) |")
    print(f"| per row — `get(i)` per candidate | "
          f"{(direct + t_rbr - t_inl) * 1e3:.3f} | "
          f"{(t_rbr - t_inl) * 1e3:+.2f} ms ({(t_rbr / t_inl - 1) * 100:+.0f}% on the walk) |")
    print(f"| per field — `mu(i)` per candidate | "
          f"{(direct + t_fbf - t_inl) * 1e3:.3f} | "
          f"{(t_fbf - t_inl) * 1e3:+.2f} ms ({(t_fbf / t_inl - 1) * 100:+.0f}% on the walk) |")
    print()
    print(f"(bare attribute walk over {N:,} rows: {t_inl * 1e6:.0f} us; "
          f"via `get(i)`: {t_rbr * 1e6:.0f} us; via `mu(i)`: {t_fbf * 1e6:.0f} us)")

    # The per-search row above is one extra call on a 2.9 ms measurement, i.e.
    # inside the noise. Time the call itself instead.
    import timeit
    per_call = timeit.timeit(lambda: src.snapshot("krakow", 0).rows(),
                             number=1_000_000) / 1_000_000
    print(f"\nThe `snapshot()` call measured on its own: **{per_call * 1e9:.0f} ns** "
          f"— {per_call / direct * 100:.5f}% of one search. Whatever sign the "
          f"per-search row above carries is run-to-run variance, not the port.")

    # ── the alternative the port buys: a query per search ──────────────────
    print()
    print("## What the port is insurance against: a query per search")
    con = sqlite3.connect(":memory:")
    con.execute("""CREATE TABLE cand (player_id INTEGER PRIMARY KEY, sport INT,
                   mu REAL, sigma REAL, lat REAL, lng REAL, tags INT, grid INT,
                   grid_bits INT, intent INT, stale REAL, ok INT)""")
    con.executemany(
        "INSERT INTO cand VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(r.player_id, r.sport, r.mu, r.sigma, r.area_lat, r.area_lng, r.tags,
          r.grid, r.grid_bits, r.play_intent, r.grid_staleness,
          1 if (r.photo_ok and r.rating_status != 2) else 0) for r in rows])
    con.execute("CREATE INDEX ix ON cand (sport, lat, lng)")
    q = ("SELECT player_id, mu, sigma, lat, lng, tags, grid, grid_bits, intent, "
         "stale FROM cand WHERE sport=? AND lat BETWEEN ? AND ? "
         "AND lng BETWEEN ? AND ? AND ok=1")
    args = (s.sport, k.lat_lo, k.lat_hi, k.lng_lo, k.lng_hi)
    n_rows = len(con.execute(q, args).fetchall())

    def query():
        return con.execute(q, args).fetchall()

    t_q = med(query)
    print(f"- sqlite, in-memory, indexed, returning {n_rows} rows: "
          f"**{t_q * 1e3:.2f} ms** — and that is the floor: no socket, no wire "
          f"protocol, no connection pool, no row objects built.")
    print(f"- the in-memory scan that replaces it: {direct * 1e3:.2f} ms.")

    # ── §16 response construction and serialisation ────────────────────────
    print()
    print("## Building and serialising the §16 response")
    scored = sorted(scan_objects(rows, s, k=k), reverse=True)[:20]
    by_id = {r.player_id: r for r in rows}
    TERMS = ("LEVEL_FIT", "PREDICTED_BALANCE", "INTENT_ALIGNMENT", "RELIABILITY",
             "AVAILABILITY_OVERLAP", "PLAYING_STYLE", "SOCIAL_VIBE", "DISTANCE")

    def build_response():
        seats = []
        for fit, pid in scored:
            r = by_id[pid]
            seats.append({
                "player_id": str(pid),
                "relationship": "OPPONENT",
                "fit": round(fit),
                "terms": [
                    {"term": t, "weight": w, "value": round(0.5 + i * 0.01, 4),
                     "contribution": round(w * 0.5, 2),
                     "evidence": {"kind": t.lower(), "their_mu": r.mu,
                                  "my_mu": s.mu, "delta": abs(r.mu - s.mu),
                                  "direction": "above"}}
                    for i, (t, w) in enumerate(zip(TERMS, (26, 17, 14, 13, 11, 9, 6, 4)))],
                "modifiers": [{"modifier": "CALIBRATION_VALUE", "points": 3,
                               "evidence": {"kind": "calibration_value",
                                            "their_sigma": r.sigma,
                                            "my_sigma": s.sigma}}],
                "liveness_reasons": [{"kind": "interest_received", "days_ago": 2}],
                "inclusion_reason": None,
            })
        return {"search_id": "x", "ruleset_version": "2026.08.26-a",
                "snapshot_version": 918233, "optimised_for": "searcher",
                "relaxation": {"rungs_applied": [], "radius_km_used": 8},
                "pool": {"in_range": len(scored), "gated_out": 3, "below_floor": 2},
                "seats": seats}

    t_build = med(build_response)
    payload = build_response()
    import json as _json
    t_json = med(lambda: _json.dumps(payload).encode())
    n_json = len(_json.dumps(payload).encode())
    try:
        import orjson
        t_orjson = med(lambda: orjson.dumps(payload))
        n_or = len(orjson.dumps(payload))
    except ImportError:
        t_orjson, n_or = float("nan"), 0
    print(f"- building 20 seats x 8 terms with evidence: **{t_build * 1e3:.3f} ms**")
    print(f"- `json.dumps`: {t_json * 1e3:.3f} ms, {n_json / 1024:.0f} KiB")
    if n_or:
        print(f"- `orjson.dumps`: **{t_orjson * 1e3:.3f} ms**, {n_or / 1024:.0f} KiB "
              f"(the backend already depends on orjson)")
    print(f"- §17 budgets 300 us for this stage in Go.")


if __name__ == "__main__":
    main()
