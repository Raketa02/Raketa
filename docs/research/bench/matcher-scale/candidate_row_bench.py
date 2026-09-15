"""Ticket #276 item 1 — what the row that **actually ships** costs.

``memory_bench.py`` measures §7.2's field list, which is what
``docs/specs/matchmaking/matchmaking-engine.md`` *specified*. It is not what
``app/modules/matchmaking/domain/candidate_index.py`` holds, and has not been
since that module was written: §7.2 packs availability and tags into two ``int``
bitmasks, keeps the area as ``(cell, lat, lng)`` scalars, spells the timestamps
as epoch ints and carries a shard key. The shipping row holds two tuples of
strings, a tuple of ``IndexedArea`` objects, four real ``datetime`` objects and
no shard key at all. **782 bytes a row was quoted about this type from the day
the constant was written, and was never measured against it.**

So this file measures *this* type, imported rather than copied — there is exactly
one row here and the bench cannot drift from it — with the same ``tracemalloc``
method and the same RSS cross-check as ``memory_bench.py``, so the two numbers
are comparable rather than being two methodologies' answers.

**The import is the point, and it is the one exception to the rule in
``README.md``.** The product still may not import from this directory. This
direction is safe because the module reached for is domain: ``candidate_index``
imports ``app.kernel`` and one value object, both of which are stdlib-only, so
nothing here needs the backend's dependencies or its virtualenv.

Run: ``PYTHONPATH=../../../../backend python candidate_row_bench.py``, or just
``python candidate_row_bench.py`` — the path insert below finds the backend
relative to this file.
"""
from __future__ import annotations

import datetime as dt
import gc
import os
import random
import sys
import tracemalloc
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "backend"))

from app.modules.matchmaking.domain.candidate_index import (  # noqa: E402
    CandidateRow,
    IndexedArea,
)
from app.modules.player_profile.domain.intro import INTRO_MAX_CHARACTERS  # noqa: E402

N = 31_250  # one sport of a 50 000-player city — memory_bench's own n
CITY_ROWS = 125_000  # the whole 50 000-player city index

SEED = 20260901

#: Fewer rows for the density sweep — it builds seven populations, and the
#: per-row figure is stable well below 31 250.
SWEEP_ROWS = 20_000

# Kraków, the same worked example population.py uses.
CITY_LAT, CITY_LNG = 50.05, 19.94
AREA_SPREAD_DEG = 0.08  # ~1 sigma, at the two decimal places the platform keeps

# Every closed vocabulary below is the live one, spelled as the projection
# stores it. Weighted where the real distribution is lopsided.
SPORTS = ("PADEL", "TENNIS", "SQUASH", "BADMINTON")
RATING_STATUS = ("RATED", "RATED", "RATED", "INITIAL_ESTIMATE")
CALIBRATION_PRIORITY = ("STANDARD", "STANDARD", "URGENT")
DECLARED_INTENT = ("COMPETITIVE", "FOR_FUN", None)
GENDERS = ("WOMAN", "MAN", "PREFER_NOT_TO_SAY", None)
GENDER_PREFERENCES = ("ANY", "ANY", "ANY", "SAME_GENDER")
BANDS = ("Newcomer", "Improver", "Steady", "Strong", "Advanced")
SOCIAL_TAGS = (
    "STAYS_FOR_A_DRINK", "STRAIGHT_HOME_AFTER", "TALKS_THROUGH_THE_MATCH",
    "SETTLES_UP_ON_THE_SPOT", "BOOKS_THE_NEXT_ONE", "SHARES_A_LIFT",
    "PLAYS_TO_WIN", "LAUGHS_OFF_MISTAKES", "ENCOURAGES_A_PARTNER",
    "GENEROUS_ON_LINE_CALLS", "QUIET_AND_FOCUSED", "WARMS_UP_PROPERLY",
    "HERE_TO_IMPROVE", "HERE_TO_COMPETE", "HERE_FOR_THE_EXERCISE",
    "HERE_TO_MEET_PLAYERS", "HERE_FOR_A_REGULAR_GAME",
    "HERE_TO_GET_BACK_INTO_IT", "OPEN_TO_MEET_SOMEONE",
)
#: The twenty-one cells, as ``AvailabilitySlot.code`` writes them.
AVAILABILITY_CODES = tuple(
    f"{day}:{part}"
    for day in range(1, 8)
    for part in ("MORNING", "AFTERNOON", "EVENING")
)

# --- how much of the grid an ordinary player fills -------------------------
#
# **The one input to this bench that moves the answer by more than a rounding,
# and it is an assumption rather than a measurement.** ``availability`` is the
# most expensive field on the row — a tuple plus one string per ticked cell —
# so the number of cells a player ticks sets the total. The sweep at the bottom
# of the run prints the elasticity rather than leaving it implied: 3 cells is
# ~1 790 bytes a row and 21 cells is ~2 920.
#
# ``population.py`` ticks a grid with ``rng.getrandbits(21)`` — a mean of 10.5
# of 21. That was free there: §7.2's grid is one ``int`` bitmask and the bit
# count costs nothing. Carrying it here would be **the same error this bench
# exists to correct**, a parameter imported from a context where it did not
# matter into the one place where it dominates.
#
# So the density comes from the only place in this repository that states one:
# ``app/seeds/cohort.py``, whose ``MEMBER_EXTRA_CELLS`` is commented *"how much
# of the grid an ordinary player fills"*. Its rule gives an ordinary member
# ``SHARED_CELLS_FLOOR`` 2 cells plus 1–4 more, every seventh member 2–5
# elsewhere, and every ninth the whole week — **mean 6.2, median 5**. It is a
# workbench fixture and not a population study; there are no real players to
# measure. It is a stated assumption from the repo's own vocabulary rather than
# a silent one carried in from a bench where it was weightless.
CELLS_IN_THE_GRID = 21
COHORT_SHARED_CELLS_FLOOR = 2  # app/seeds/cohort.py SHARED_CELLS_FLOOR
COHORT_EXTRA_CELLS = (1, 4)  # MEMBER_EXTRA_CELLS
COHORT_CELLS_ELSEWHERE = (2, 5)  # MEMBER_CELLS_ELSEWHERE
COHORT_EVERY_NTH_FILLS_THE_WEEK = 9  # EVERY_NTH_IS_LOPSIDED
COHORT_EVERY_NTH_SHARES_NO_WEEK = 7  # EVERY_NTH_SHARES_NO_WEEK


def cells_ticked(rng: random.Random, position: int) -> int:
    """How many of the twenty-one cells this member ticks.

    ``app/seeds/cohort.py``'s ``_slots`` rule as a **density**, which is all
    this bench needs of it: the overlap structure exists so the availability
    term has something to read, and none of it changes a byte count.
    """

    if position % COHORT_EVERY_NTH_FILLS_THE_WEEK == 5:
        return CELLS_IN_THE_GRID
    if position % COHORT_EVERY_NTH_SHARES_NO_WEEK == 4:
        return rng.randint(*COHORT_CELLS_ELSEWHERE)
    return COHORT_SHARED_CELLS_FLOOR + rng.randint(*COHORT_EXTRA_CELLS)


# **How many players write an intro, and how long it is** — the second stated
# assumption, added with ``docs/adr/0170``. There are no real players to measure
# and the ADR's own forecast is *most players will have none*, so the share is
# ``app/seeds/cohort.py``'s again: seven of forty-one members carry a line, and
# their lines average the length below. A line is one ``str`` on the row — up to
# ``INTRO_MAX_CHARACTERS``, imported so the cap cannot drift — and ``None`` for
# everybody else, so the whole cost is the share times the string, and the sweep
# below prices both ends.
COHORT_INTRO_SHARE = 7 / 41
COHORT_INTRO_MEAN_CHARACTERS = 54


def intros_written(share: float, mean_characters: float, spread: float = 18):
    """A rule for who wrote a line and how long it is, at a stated share.

    Named so the sweep can vary it and a reader can disagree with it, the way
    ``cells_ticked`` is for the grid. Lengths are drawn around ``mean_characters``
    and clamped to the cap; at ``spread == 0`` every line is exactly the mean,
    which is what the sweep's *everybody at the cap* row asks for.
    """

    def rule(rng: random.Random, position: int) -> str | None:
        if rng.random() >= share:
            return None
        length = max(1, min(INTRO_MAX_CHARACTERS,
                            int(round(rng.gauss(mean_characters, spread)))))
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz ")
                       for _ in range(length))

    return rule


intro_written = intros_written(COHORT_INTRO_SHARE, COHORT_INTRO_MEAN_CHARACTERS)


def uninterned_copy(value: str | None) -> str | None:
    """The same characters as a **distinct object**, which is what ships.

    ``candidate_snapshot_source._decode`` copies whatever the driver handed it,
    and neither asyncpg nor SQLAlchemy interns: two rows of the same sport hold
    two ``"PADEL"`` objects. #276's own framing — *the string fields are cheap,
    because an enum's ``.value`` is one shared object and a row holds a pointer*
    — describes a row nobody builds, and it is wrong by ~1 200 bytes a row.

    The bench measures both, because the gap between them is the size of the
    fix and somebody has to be able to see it before spending it.
    """

    return None if value is None else value.encode().decode()


def make_rows(
    n: int,
    *,
    seed: int = SEED,
    shared_vocabulary: bool = False,
    cells=cells_ticked,
    intro=intro_written,
) -> list[CandidateRow]:
    """``n`` rows of one city, as the projection would decode them.

    ``shared_vocabulary`` is the counterfactual: every closed-vocabulary column
    a pointer to one object, which is what the row would cost if ``_decode``
    routed those columns through their own vocabularies. Nothing else changes,
    so the two rows of the table differ by exactly that.

    ``cells`` is the grid-density assumption, named so the sweep can vary it and
    a reader can disagree with it. See ``cells_ticked`` above. ``intro`` is the
    second one — who wrote a line, and how long — see ``intro_written``.
    """

    rng = random.Random(seed)
    base = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    text = (lambda v: v) if shared_vocabulary else uninterned_copy
    rows = []
    for i in range(n):
        mu = rng.uniform(1.0, 5.0)
        sigma = rng.uniform(0.05, 0.60)
        ticked = (
            rng.randint(1, CELLS_IN_THE_GRID) if cells is None
            else cells(rng, i)
        )
        rows.append(CandidateRow(
            # A UUID as the string the engine ties break on — 36 characters,
            # and the one string on this row that cannot be shared.
            player_id=str(uuid.UUID(int=rng.getrandbits(128))),
            sport=text(rng.choice(SPORTS)),
            mu=mu,
            sigma=sigma,
            confidence=rng.randint(0, 100),
            range_low=round(max(1.0, mu - sigma), 2),
            range_high=round(min(7.0, mu + sigma), 2),
            band=text(rng.choice(BANDS)),
            band_lower=round(rng.uniform(1.0, 6.0), 2),
            band_upper=round(rng.uniform(1.0, 6.0) + 0.5, 2),
            rating_status=text(rng.choice(RATING_STATUS)),
            calibration_priority=text(rng.choice(CALIBRATION_PRIORITY)),
            declared_intent=text(rng.choice(DECLARED_INTENT)),
            social_tags=tuple(
                text(tag) for tag in rng.sample(SOCIAL_TAGS, rng.randint(2, 6))
            ),
            tags_updated_at=base - dt.timedelta(seconds=rng.randrange(30_000_000)),
            # A player's own words are the one string on this row that no
            # vocabulary could ever share.
            intro=intro(rng, i),
            availability=tuple(
                text(code)
                for code in sorted(rng.sample(AVAILABILITY_CODES, ticked))
            ),
            grid_updated_at=base - dt.timedelta(seconds=rng.randrange(30_000_000)),
            areas=(IndexedArea(
                latitude=round(CITY_LAT + rng.gauss(0, AREA_SPREAD_DEG), 2),
                longitude=round(CITY_LNG + rng.gauss(0, AREA_SPREAD_DEG), 2),
            ),),
            search_radius_km=rng.choice((3, 5, 8, 8, 10, 15, 25)),
            proposals_opt_in=rng.choice((True, True, True, False, None)),
            gender=text(rng.choice(GENDERS)),
            gender_preference=text(rng.choice(GENDER_PREFERENCES)),
            profile_created_at=base - dt.timedelta(seconds=rng.randrange(60_000_000)),
            last_active_at=(
                None if rng.random() < 0.1
                else base - dt.timedelta(seconds=rng.randrange(2_000_000))
            ),
            applied_through_sequence_no=1_000_000 + i,
        ))
    return rows


def measure(build, label: str, n: int) -> tuple[list[CandidateRow], int]:
    """``memory_bench.measure``, verbatim, so the two tables are one table."""

    gc.collect()
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    obj = build(n)
    current, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    total = current - base
    print(f"| {label} | {total / 1e6:.1f} | {total / n:.0f} | "
          f"{total / n * CITY_ROWS / 1e6:.0f} |")
    return obj, total


def deep_bytes(value: object, seen: set[int]) -> int:
    """``sys.getsizeof`` down one level, counting an object once.

    Not a second methodology — the totals below are ``tracemalloc``'s, and this
    is only how the row is broken up into fields so a reader can see *which*
    ones cost. A tuple's own footprint plus its elements', an ``IndexedArea``
    plus its two floats, and nothing deeper because the row goes no deeper.
    """

    if id(value) in seen:
        return 0
    seen.add(id(value))
    total = sys.getsizeof(value)
    if isinstance(value, tuple):
        for element in value:
            total += deep_bytes(element, seen)
    if isinstance(value, IndexedArea):
        total += sys.getsizeof(value.latitude) + sys.getsizeof(value.longitude)
    return total


def main() -> None:
    print(f"# candidate_row_bench — CPython {sys.version.split()[0]} "
          f"on {os.uname().machine}")
    print()
    print(f"The **shipping** `CandidateRow`, imported from `backend/`. n = {N:,} "
          f"rows measured; the last column extrapolates to the {CITY_ROWS:,}-row "
          f"index of a 50 000-player city.")
    print()
    print("| representation | MB @ 31 250 rows | bytes/row | MB @ 125 000 rows |")
    print("|---|---|---|---|")

    rows, shipped = measure(
        lambda n: make_rows(n),
        "shipping CandidateRow, vocabulary strings as a driver returns them",
        N,
    )
    _, shared = measure(
        lambda n: make_rows(n, shared_vocabulary=True),
        "the same rows, closed-vocabulary strings shared (not what ships)",
        N,
    )
    print()
    print(f"Sharing the closed vocabularies would save "
          f"**{(shipped - shared) / N:.0f} bytes a row**, "
          f"{100 * (shipped - shared) / shipped:.0f}% of the row.")

    # ── where the bytes go ────────────────────────────────────────────────
    print()
    print("## One row, field by field")
    print()
    sample = rows[1]
    print(f"A row with {len(sample.availability)} of the 21 cells ticked and "
          f"{len(sample.social_tags)} tags.")
    print()
    print("| field | bytes |")
    print("|---|---:|")
    tally = sys.getsizeof(sample)
    print(f"| the object itself, {len(CandidateRow.__slots__)} slots | {tally} |")
    for field in CandidateRow.__slots__:
        value = getattr(sample, field)
        size = 0 if value is None else deep_bytes(value, set())
        tally += size
        print(f"| `{field}` | {size} |")
    print(f"| **total** | **{tally}** |")

    # ── the assumption, priced ────────────────────────────────────────────
    print()
    print("## What the grid-density assumption is worth")
    print()
    print("`availability` is the most expensive field on the row, so the number of "
          "cells a player ticks sets the total. The headline above is "
          "`app/seeds/cohort.py`'s own density (**mean 6.2 of 21**); this is what "
          "believing something else would cost. `population.py`'s "
          "`getrandbits(21)` — free there, because §7.2's grid is one `int` — is "
          "the 10.5 row.")
    print()
    print("| mean cells ticked | bytes/row | trigger 4, 4 workers on 1 GB |")
    print("|---|---:|---:|")
    for mean in (3, 5, 6.2, 7, 10.5, 14, 21):
        def fixed(rng, position, mean=mean):
            drawn = int(round(rng.gauss(mean, 1.5)))
            return max(1, min(CELLS_IN_THE_GRID, drawn))

        gc.collect()
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        sample = make_rows(SWEEP_ROWS, cells=fixed)
        current, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        per_row = (current - base) / SWEEP_ROWS
        players = int(0.5e9 // (per_row * 4) / 2.5)
        marker = " **(the assumption above)**" if mean == 6.2 else ""
        print(f"| {mean}{marker} | {per_row:.0f} | ~{players:,} players |")
        del sample
        gc.collect()

    # ── the second assumption, priced ────────────────────────────────────
    print()
    print("## What the intro assumption is worth")
    print()
    print("`intro` is one `str` or `None` (`docs/adr/0170`), so its cost is the "
          "share of players who wrote one times the line. The headline above is "
          "`app/seeds/cohort.py`'s share (**seven of forty-one, mean 54 "
          "characters**); the last row is every player at the cap, which is the "
          "most the field can ever cost.")
    print()
    print("| who wrote a line | bytes/row | trigger 4, 4 workers on 1 GB |")
    print("|---|---:|---:|")
    for label, share, length in (
        ("nobody", 0.0, 0),
        ("the cohort's share, at its mean length", COHORT_INTRO_SHARE,
         COHORT_INTRO_MEAN_CHARACTERS),
        ("one in three, at the mock's ~60", 1 / 3, 60),
        ("everybody, at the 100-character cap", 1.0, INTRO_MAX_CHARACTERS),
    ):
        gc.collect()
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        sample = make_rows(
            SWEEP_ROWS, intro=intros_written(share, length, spread=0)
        )
        current, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        per_row = (current - base) / SWEEP_ROWS
        players = int(0.5e9 // (per_row * 4) / 2.5)
        marker = " **(the assumption above)**" if share == COHORT_INTRO_SHARE else ""
        print(f"| {label}{marker} | {per_row:.0f} | ~{players:,} players |")
        del sample
        gc.collect()

    # ── the RSS cross-check, exactly as memory_bench takes it ─────────────
    print()
    print("## RSS cross-check")
    del rows
    gc.collect()
    try:
        import psutil
    except ImportError:
        print("- psutil not installed; RSS not measured")
        return
    process = psutil.Process()
    rss0 = process.memory_info().rss
    index = make_rows(CITY_ROWS)
    gc.collect()
    rss1 = process.memory_info().rss
    grew = rss1 - rss0
    print(f"- RSS before: {rss0 / 1e6:.0f} MB")
    print(f"- RSS with one {CITY_ROWS:,}-row index live: {rss1 / 1e6:.0f} MB "
          f"(+{grew / 1e6:.0f} MB, **{grew / CITY_ROWS:.0f} bytes a row**)")
    print(f"- `tracemalloc` said {shipped / N:.0f}; the two agree to "
          f"{100 * abs(grew / CITY_ROWS - shipped / N) / (shipped / N):.0f}%")
    print(f"- objects tracked by the collector: {len(gc.get_objects()):,}")
    del index


if __name__ == "__main__":
    main()
