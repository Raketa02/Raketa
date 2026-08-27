"""Ticket #161 item 8 — the low end the document under-serves.

For a market with tens of players: how many candidates are actually in range
for a typical search, and how often is that below a shortlist minimum?

Two spatial models, because the answer depends on one and the document names
neither:

  * **spread** — players scattered over the metro (sigma 9 km), the model the
    scan benchmarks use;
  * **clubbed** — players cluster around a handful of clubs, which is what a
    tens-of-players market actually looks like, since people join because
    somebody at their club told them to.

Feeds https://github.com/Raketa02/Raketa/issues/162 (Cold start).

Run: python lowend_bench.py
"""
from __future__ import annotations

import math
import random
import statistics
import sys

KM_LAT = 110.574
CITY_LAT = 50.048
KM_LNG = 111.320 * math.cos(math.radians(CITY_LAT))
SIGMA_KM = 9.0
CLUBS = 4
CLUB_SIGMA_KM = 1.2
RADII = (3, 5, 8, 8, 10, 15, 25)     # the population's declared radii
SPORT_SHARE = (0.45, 0.30, 0.10, 0.15)  # padel, tennis, squash, badminton
ROWS_PER_PLAYER = 2.5
TRIALS = 4000
MINIMA = (3, 5, 10)
# §9.8's relaxation ladder, as radius multipliers
RUNGS = (1.0, 1.5, 2.0, 3.0)


def place(rng, model, clubs):
    if model == "spread":
        return rng.gauss(0, SIGMA_KM), rng.gauss(0, SIGMA_KM)
    cx, cy = clubs[rng.randrange(len(clubs))]
    return cx + rng.gauss(0, CLUB_SIGMA_KM), cy + rng.gauss(0, CLUB_SIGMA_KM)


def simulate(players, model, seed=7):
    """Returns, per trial, the in-range same-sport candidate count at each rung."""
    rng = random.Random(seed)
    clubs = [(rng.gauss(0, SIGMA_KM), rng.gauss(0, SIGMA_KM)) for _ in range(CLUBS)]
    # one row per (player, sport); a player plays ROWS_PER_PLAYER sports
    pts = []
    for _ in range(players):
        x, y = place(rng, model, clubs)
        n_sports = 3 if rng.random() < (ROWS_PER_PLAYER - 2) else 2
        sports = rng.sample(range(4), n_sports)
        for sp in sports:
            pts.append((x, y, sp))
    counts = {r: [] for r in RUNGS}
    for _ in range(TRIALS):
        i = rng.randrange(len(pts))
        sx, sy, ssp = pts[i]
        radius = rng.choice(RADII)
        for rung in RUNGS:
            r = radius * rung
            rr = r * r
            n = 0
            for j, (x, y, sp) in enumerate(pts):
                if j == i or sp != ssp:
                    continue
                dx, dy = x - sx, y - sy
                if dx * dx + dy * dy <= rr:
                    n += 1
            counts[rung].append(n)
    return counts, len(pts)


def main():
    print(f"# lowend_bench — CPython {sys.version.split()[0]}")
    print()
    print(f"{TRIALS} simulated searches per row. A candidate counts if it shares "
          f"the searcher's sport and sits inside the searcher's declared radius "
          f"(one of {RADII} km).")
    for model in ("spread", "clubbed"):
        print()
        print(f"## {model} model"
              + (f" ({CLUBS} clubs, sigma {CLUB_SIGMA_KM} km)"
                 if model == "clubbed" else f" (sigma {SIGMA_KM} km)"))
        print()
        print("| players | rows | median in range | p10 | p90 | P(<3) | P(<5) | "
              "P(<10) | median after relax x3 | P(<5) after relax x3 |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for players in (20, 40, 80, 150, 300, 600, 1200):
            counts, nrows = simulate(players, model)
            base = sorted(counts[1.0])
            relaxed = sorted(counts[3.0])

            def q(xs, p):
                return xs[min(len(xs) - 1, int(p / 100 * (len(xs) - 1)))]

            def below(xs, m):
                return sum(1 for x in xs if x < m) / len(xs)

            print(f"| {players} | {nrows} | {statistics.median(base):.0f} | "
                  f"{q(base,10)} | {q(base,90)} | {below(base,3)*100:.0f}% | "
                  f"{below(base,5)*100:.0f}% | {below(base,10)*100:.0f}% | "
                  f"{statistics.median(relaxed):.0f} | "
                  f"{below(relaxed,5)*100:.0f}% |")


if __name__ == "__main__":
    main()
