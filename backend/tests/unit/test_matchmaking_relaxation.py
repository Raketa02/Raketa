"""The ladder: three rungs, real counts, and the floor left exactly where it was.

``docs/adr/0099`` rebuilt §9.8's four rungs into three over the searcher's **own
asks**, offered rather than applied. What is asserted here is the whole of that
record's substance:

- the ceiling, which is the profile slider's own and never this module's;
- the counts, which come from re-running the search and never from arithmetic
  over the strict answer;
- **monotonicity only where it holds** — ``B ⊆ C``, and both ``⊇`` the strict
  set. It is false of rung A, which is asserted too, with the eviction that makes
  it false written out rather than left as a caveat in a docstring;
- and the floor, which no rung moves, so *nobody tonight* stays a real answer.
"""

from __future__ import annotations

import pytest

from app.engines.matchfit.v1 import MatchFitV1
from app.kernel import InvariantViolated
from app.modules.matchmaking.domain.relaxation import (
    RADIUS_MULTIPLIERS,
    RelaxationAsk,
    Rung,
    RungOffer,
    radius_ladder,
)
from app.modules.matchmaking.domain.shortlist import run
from app.modules.matchmaking.domain.widening import cleared_floor, ladder_for
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS
from app.modules.player_profile.domain.weekly_hours import Window
from tests.unit.matchmaking_builders import (
    CENTRE,
    SEARCHER_SLOTS,
    context,
    row,
    searcher,
)

ENGINE = MatchFitV1()

#: Two tags on the sociable side of the style/vibe split, so a candidate can be
#: made to score low **without** moving their Level — which the tenth gate would
#: notice long before the floor did.
SOCIABLE = ("HERE_FOR_THE_SOCIAL", "PLAYS_FOR_FUN")

#: A cell the searcher has not ticked, and the only one anybody in these fixtures
#: holds outside their grid. Rung A's whole choice.
UNTICKED = "2:19"


def ladder(ctx):
    """The ladder for one context, priced against that context's own strict run."""

    strict = run(ctx, ENGINE)
    return strict, ladder_for(
        ctx, ENGINE, strict_above_floor=strict.counts.n_cleared_floor
    )


# ---------------------------------------------------------------------------
# The ceiling — the profile slider's own, and never this module's
# ---------------------------------------------------------------------------


def test_the_ladder_is_two_radius_multipliers_and_there_is_no_third():
    assert [rung for rung, _ in RADIUS_MULTIPLIERS] == [Rung.B, Rung.C]
    assert [multiplier for _, multiplier in RADIUS_MULTIPLIERS] == [1.5, 2.0]


def test_an_ordinary_radius_gets_both_rungs_and_no_clamp():
    offered = radius_ladder(10)

    assert [(rung.rung, rung.radius_km) for rung in offered.rungs] == [
        (Rung.B, 15),
        (Rung.C, 20),
    ]
    assert offered.clamped is False


def test_a_searcher_at_the_ceiling_gets_no_radius_rung_at_all():
    """**Never an offer that cannot happen.** The honest empty state arrives
    sooner for them, correctly: there is nothing left to offer."""

    offered = radius_ladder(SEARCH_RADIUS_BOUNDS.maximum_km)

    assert offered.rungs == ()
    # And the bit is still set, because *how many searchers are already at the
    # ceiling* is the question it exists to answer.
    assert offered.clamped is True


def test_two_multipliers_that_clamp_to_one_radius_are_offered_once():
    """A rung that would duplicate another rung's radius is not offered twice."""

    offered = radius_ladder(40)

    assert [(rung.rung, rung.radius_km) for rung in offered.rungs] == [(Rung.B, 50)]
    assert offered.clamped is True


def test_a_rung_may_never_offer_a_radius_the_player_could_not_set():
    for radius_km in range(1, SEARCH_RADIUS_BOUNDS.maximum_km + 1):
        for rung in radius_ladder(radius_km).rungs:
            assert rung.radius_km <= SEARCH_RADIUS_BOUNDS.maximum_km
            assert rung.radius_km > radius_km


def test_an_offer_carries_the_payload_its_ask_uses_and_never_the_other():
    with pytest.raises(InvariantViolated):
        RungOffer(
            rung=Rung.B,
            ask=RelaxationAsk.RADIUS,
            candidates_above_floor=1,
            window=Window.ANY,
            slot=UNTICKED,
        )
    with pytest.raises(InvariantViolated):
        RungOffer(
            rung=Rung.A,
            ask=RelaxationAsk.TIMES,
            candidates_above_floor=1,
            window=Window.ANY,
            radius_km=15,
        )


# ---------------------------------------------------------------------------
# The counts — a genuine re-run, and its own window
# ---------------------------------------------------------------------------


def a_city_that_widening_helps():
    """One person inside the ring, one past it, one past that.

    Twelve and eighteen kilometres north, which are inside ×1.5 and ×2.0 of a
    ten-kilometre radius and outside the ring itself.
    """

    return context(
        (
            row(1, latitude=CENTRE.latitude),
            row(2, latitude=51.62),
            row(3, latitude=51.67),
        )
    )


def test_a_radius_rung_carries_a_real_count_from_a_real_re_run():
    strict, offered = ladder(a_city_that_widening_helps())

    assert strict.counts.n_cleared_floor == 1
    counts = {
        rung.rung: rung.offer.candidates_above_floor for rung in offered.rungs
    }
    assert counts == {Rung.B: 2, Rung.C: 3}


def test_the_radius_rungs_are_monotone_and_both_contain_the_strict_set():
    """**Asserted only where it holds.** §20.2's *rung n+1's set is a superset of
    rung n's* is true of the radius rungs and false of rung A."""

    ctx = a_city_that_widening_helps()
    strict = frozenset(cleared_floor(ctx, ENGINE))
    _, offered = ladder(ctx)
    by_rung = {rung.rung: frozenset(rung.above_floor) for rung in offered.rungs}

    assert by_rung[Rung.B] <= by_rung[Rung.C]
    assert strict <= by_rung[Rung.B]
    assert strict <= by_rung[Rung.C]


def test_every_offer_carries_its_own_window():
    """A challenge sliding from ``WEEKEND`` to ``THIS_WEEK`` is part of what
    widening costs, and the player sees it before paying it."""

    _, offered = ladder(a_city_that_widening_helps())

    assert offered.rungs
    for rung in offered.rungs:
        assert isinstance(rung.offer.window, Window)


def test_a_times_rung_moves_the_window_when_the_grid_it_adds_to_does():
    """The searcher who plays one evening a week is asked about a second one, and
    the window that comes back is the widened grid's, not the profile's."""

    ctx = context(
        (row(1, mu=3.22, slots=(UNTICKED,)), row(2, mu=3.22, slots=(UNTICKED,))),
        facts=searcher(slots=("3:19",)),
    )
    _, offered = ladder(ctx)
    times = next(rung for rung in offered.rungs if rung.rung is Rung.A)

    # One ticked day, lightly, is that day; two days is simply this week.
    assert ctx.searcher.grid.hours[0].code == "3:19"
    assert times.offer.window is Window.THIS_WEEK
    assert times.offer.slot == UNTICKED


# ---------------------------------------------------------------------------
# Rung A — the one that evicts
# ---------------------------------------------------------------------------


def a_city_where_one_more_evening_costs_somebody():
    """Two people free only on the unticked evening, and one who shares the week.

    The sharer clears the floor by a point, on four shared cells out of four.
    Adding a fifth cell to the searcher's grid takes them to four out of five —
    ``s/m`` to ``s/(m+1)`` — and that is enough to put them under.
    """

    return context(
        (
            row(1, mu=3.22, slots=(UNTICKED,)),
            row(2, mu=3.22, slots=(UNTICKED,)),
            row(3, mu=3.30, tags=SOCIABLE, slots=SEARCHER_SLOTS),
        )
    )


def test_rung_a_admits_the_people_who_share_the_evening_it_adds():
    strict, offered = ladder(a_city_where_one_more_evening_costs_somebody())
    times = next(rung for rung in offered.rungs if rung.rung is Rung.A)

    assert times.offer.ask is RelaxationAsk.TIMES
    assert times.offer.slot == UNTICKED
    assert times.offer.candidates_above_floor == 2
    assert strict.counts.n_cleared_floor == 1


def test_rung_a_can_evict_and_the_offered_count_says_so_honestly():
    """**Nothing is hidden**, because the count is a real re-run and not the
    strict count plus something. The shape is recorded here rather than
    discovered in production."""

    ctx = a_city_where_one_more_evening_costs_somebody()
    strict = frozenset(cleared_floor(ctx, ENGINE))
    _, offered = ladder(ctx)
    times = next(rung for rung in offered.rungs if rung.rung is Rung.A)

    assert not strict <= frozenset(times.above_floor)
    # The evicted person is the one who shared the whole week and cleared the
    # floor by less than the denominator costs.
    assert strict - frozenset(times.above_floor)


def test_a_times_rung_is_not_offered_when_no_evening_would_help():
    """An offer that admits nobody would be inviting a player to widen a week
    they may not truthfully be free in, for nothing — and a ghost is worse than a
    decline."""

    _, offered = ladder(a_city_that_widening_helps())

    assert [rung.rung for rung in offered.rungs] == [Rung.B, Rung.C]


# ---------------------------------------------------------------------------
# The floor, which no rung moves
# ---------------------------------------------------------------------------


def test_no_rung_admits_anybody_below_the_quality_floor():
    """**The quality floor is never relaxed, at any rung**, so *nobody tonight*
    stays a real answer."""

    ctx = a_city_where_one_more_evening_costs_somebody()
    floor = ctx.ruleset.floors.quality_floor
    _, offered = ladder(ctx)

    for rung in offered.rungs:
        widened = (
            ctx
            if rung.radius_km is None
            else context(
                ctx.snapshot.rows,
                facts=searcher(radius_km=rung.radius_km),
            )
        )
        for scored in run(widened, ENGINE).returned:
            if scored.player_id in rung.above_floor:
                assert scored.modified.points >= floor


def test_a_thin_city_offers_every_rung_and_admits_nobody():
    """The honest empty state, with the offers computed and worth nothing. It is
    an empty answer either way, and the counts are what say so."""

    # One person in range, next door, who shares half the searcher's week and
    # wants a different evening out of it. **No rung reaches them.** A wider ring
    # is worth nothing to somebody already inside 70% of the current one, and
    # there is no evening to add that they hold and the searcher does not.
    ctx = context((row(1, mu=3.30, tags=SOCIABLE, slots=("1:19", "3:19")),))
    strict, offered = ladder(ctx)

    assert strict.returned == ()
    # No times rung at all: the one person in range shares the whole week
    # already, so there is no evening left to offer that anybody holds.
    assert [rung.rung for rung in offered.rungs] == [Rung.B, Rung.C]
    assert [rung.offer.candidates_above_floor for rung in offered.rungs] == [0, 0]


# ---------------------------------------------------------------------------
# Stage 5 does not loop
# ---------------------------------------------------------------------------


def test_the_pipeline_knows_nothing_about_relaxation():
    """§9's ``too few above it → relax one rung, GOTO 2`` is **struck**.

    The strict answer returns carrying offers, and there is no path in the
    pipeline that widens anything and goes back to stage 2. Asserted over the
    source because it is the absence of a branch — a behavioural test can only
    fail to find one, where this fails when somebody adds it.
    """

    import ast
    from pathlib import Path

    import app.modules.matchmaking.domain.shortlist as pipeline

    source = Path(pipeline.__file__).read_text()
    imported = {
        node.module or ""
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
    }
    assert not any(module.endswith((".relaxation", ".widening")) for module in imported)
    # And nothing here calls the ladder, which is the other half of the same
    # statement: the pipeline is priced *by* relaxation and never prices itself.
    for called in ("ladder_for", "radius_ladder"):
        assert called not in source
