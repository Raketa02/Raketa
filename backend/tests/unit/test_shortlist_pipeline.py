"""The pipeline's own properties — the ones that are about the *list*.

The engine's stages have their own suites one directory over. What is asserted
here is what only exists once the stages are composed: that a gated player never
reaches an answer whatever moves around them, that Liveness reorders **without
moving a printed number**, that the order is total, and that the two bounds — the
shortlist's cap and the near-miss band's — hold.

``docs/adr/0126`` is why the liveness property is stated here rather than at stage
6: *the roster test is a test about stage 6, and the stage that broke its
guarantee ran one stage later and left it green.*
"""

from __future__ import annotations

import pytest

from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.domain.searches import SortOption
from app.modules.matchmaking.domain.shortlist import run
from app.modules.matchmaking.domain.sorting import sorts_available
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()


def _run(context):
    return run(context, ENGINE)


def _ids(rows) -> list[str]:
    return [row.player_id for row in rows]


def test_a_gated_player_never_appears_in_either_band():
    """Not in the shortlist, and **not in the near-miss band either**.

    The second half matters more than it looks: layer 3 is engine-internal, so a
    gated player leaking into it would be invisible to every test that reads a
    response — and it is a durable row about somebody who should not have been
    considered at all.
    """

    gated = build.row(1)
    ordinary = build.row(2)
    shortlist = _run(
        build.context(
            (gated, ordinary), blocked=frozenset({gated.player_id})
        )
    )

    everybody = _ids(shortlist.returned) + _ids(shortlist.near_misses)
    assert gated.player_id not in everybody
    assert ordinary.player_id in everybody


def test_liveness_reorders_the_list_and_never_moves_a_printed_fit():
    """**The one number a player is asked to trust.**

    The same two pairings are scored twice, with only Liveness inputs changed.
    Every Fit is identical; the order is not.
    """

    rows = (build.row(1), build.row(2))
    still = _run(build.context(rows))
    moved = _run(
        build.context(
            rows,
            # A fact about *them*, not about the list: one of them has a full
            # inbox, and the other has been shown to nobody this week.
            open_challenge_counts={build.player(1): 9, build.player(2): 0},
            times_shown={build.player(1): 12, build.player(2): 0},
            busy_threshold=5,
        )
    )

    assert {row.player_id: row.modified.points for row in still.returned} == {
        row.player_id: row.modified.points for row in moved.returned
    }
    assert _ids(still.returned) != _ids(moved.returned)


def test_the_order_is_total_and_ends_on_the_player_id():
    """**A set is never the source of an order.** Two candidates who are
    identical in every scored fact still come back in one order, on every process
    and every run."""

    twins = tuple(build.row(number) for number in range(1, 6))
    first = _ids(_run(build.context(twins)).returned)
    again = _ids(_run(build.context(tuple(reversed(twins)))).returned)

    assert first == again == sorted(first)


def test_the_shortlist_is_capped_and_the_cap_is_the_rulesets():
    """Bounded and unpaginated: there is no page two, and the bound is ruleset
    data rather than a number written into the pipeline."""

    crowd = tuple(build.row(number) for number in range(1, 40))
    shortlist = _run(build.context(crowd))

    assert len(shortlist.returned) == LIVE_RULESET.shape.shortlist_max
    assert shortlist.counts.n_returned == len(shortlist.returned)
    assert shortlist.counts.n_cleared_floor > len(shortlist.returned), (
        "the cap did not bind, so this asserts nothing"
    )


def test_the_near_miss_band_is_the_best_few_and_no_more():
    """Layer 3 is ``NEAR_MISS_RECORDED`` rows of the best that did not clear,
    ordered on the number the floor actually read."""

    # Nothing declared, no tags and no grid, so four of the seven live terms
    # have nothing to read for any of them.
    thin = tuple(
        build.row(
            number,
            declared_intent=None,
            tags=(),
            slots=(),
            mu=build.SEARCHER_MU + 0.5 - number * 0.001,
        )
        for number in range(1, 20)
    )
    shortlist = _run(build.context(thin))

    assert shortlist.returned == ()
    assert len(shortlist.near_misses) == LIVE_RULESET.telemetry.near_miss_recorded
    fits = [row.modified.points for row in shortlist.near_misses]
    assert fits == sorted(fits, reverse=True)
    assert shortlist.best_withheld_fit == pytest.approx(fits[0])
    assert shortlist.counts.n_near_miss_recorded == len(shortlist.near_misses)


def test_nothing_withheld_is_a_null_best_fit_and_not_a_zero():
    """``None`` means nothing was withheld, which is not the same as ``0`` — and
    a zero here would read as *the best we could do was nothing*."""

    assert _run(build.context((build.row(1),))).best_withheld_fit is None


def test_the_counters_describe_the_same_search_the_rows_do():
    crowd = tuple(build.row(number) for number in range(1, 6))
    gated = build.row(6)
    shortlist = _run(
        build.context(crowd + (gated,), held=frozenset({gated.player_id}))
    )

    counts = shortlist.counts
    assert counts.n_generated == 6
    assert sum(counts.excluded_by_gate.values()) == 1
    assert counts.n_scored == 5
    assert counts.n_cleared_floor == len(shortlist.returned)
    assert shortlist.players_in_range == 5


def test_a_sort_that_would_reorder_nothing_is_not_offered():
    """A visible control that reorders nothing is the product lying quietly."""

    alone = _run(build.context((build.row(1),)))
    assert sorts_available(alone.returned) == ()

    identical = _run(build.context(tuple(build.row(n) for n in range(1, 4))))
    assert SortOption.CLOSEST not in sorts_available(identical.returned), (
        "three candidates at the same address cannot be sorted by distance"
    )


def test_a_sort_whose_readings_are_all_equal_is_never_offered():
    """The failure a naive check misses, and the one *Most reliable* is.

    Every sort ends on the player id, so a sort whose readings are all equal
    resorts the list into **id order** — a different order, carrying nothing.
    Drawn, that control offers the player a reshuffle by player id and calls it
    *most reliable*.

    The rows below are deliberately in an order the ids do not agree with, which
    is what makes the naive check say *yes* here.
    """

    descending = (
        build.row(1, mu=build.SEARCHER_MU - 0.4),
        build.row(2, mu=build.SEARCHER_MU - 0.2),
        build.row(3, mu=build.SEARCHER_MU),
    )
    returned = _run(build.context(descending)).returned

    assert _ids(returned) != sorted(_ids(returned)), (
        "the fixture agrees with id order, so it asserts nothing"
    )
    offered = sorts_available(returned)
    assert SortOption.MOST_RELIABLE not in offered, (
        "the reliability term stands down for everybody, so nothing tells these "
        "rows apart"
    )
    assert SortOption.CLOSEST not in offered, "they are all at the same address"


def test_closest_is_offered_when_it_would_actually_reorder():
    """And *Most reliable* is not, for as long as the reliability term stands
    down for everybody — a fact re-derived per search rather than hardcoded."""

    spread = (
        build.row(1, latitude=51.55),
        build.row(2, latitude=51.51),
        build.row(3, latitude=51.53),
    )
    offered = sorts_available(_run(build.context(spread)).returned)

    assert SortOption.CLOSEST in offered
    assert SortOption.MOST_RELIABLE not in offered
    assert SortOption.EVENEST not in offered


def test_the_evidence_gate_excludes_nobody_on_todays_inputs():
    """**Live and inert, on purpose.** It is standing insurance, in place before
    the day *we know nothing about this person* could quietly become a passing
    score — and a test says so, so that the day it starts biting is a diff."""

    ordinary = _run(build.context(tuple(build.row(n) for n in range(1, 6))))

    assert all(row.admission.admitted for row in ordinary.returned)
    assert all(
        row.withheld_reason is None for row in ordinary.returned
    )
