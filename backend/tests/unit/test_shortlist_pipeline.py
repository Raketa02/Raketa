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

from datetime import timedelta

import pytest

from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.domain.searches import SearchSurface, SortOption
from app.modules.matchmaking.domain.shortlist import run
from app.modules.matchmaking.domain.sorting import of_scored, sorts_available
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()


def _run(context):
    return run(context, ENGINE)


def _ids(rows) -> list[str]:
    return [row.player_id for row in rows]


def _offered(returned):
    """The controls this answer can honestly draw.

    ``sorts_available`` reads a :class:`Sortable` rather than a scored row, so
    that the search that just ran and the search read back an hour later reach
    one implementation. ``of_scored`` is the search's own half of that mapping.
    """

    return sorts_available(
        tuple(of_scored(row) for row in returned),
        surface=SearchSurface.SHORTLIST,
    )


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
    assert _offered(alone.returned) == ()

    identical = _run(build.context(build.rows_printing_one_distance(3)))
    assert SortOption.CLOSEST not in _offered(identical.returned), (
        "three candidates whose cards print one distance cannot be sorted by it"
    )


def test_closest_reads_the_print_and_the_print_is_spot_to_spot():
    """Three people in one cell **can** be told apart by *Closest* now, exactly
    when their one-decimal prints differ (``docs/adr/0174`` §2). Offerability is
    a claim about what the client could do with the rows it holds, and the
    client holds the print — so the control follows the number on the card and
    never the cell the term read."""

    returned = _run(build.context(tuple(build.row(n) for n in range(1, 21)))).returned
    prints = [row.shown_distance_km for row in returned]

    assert len(set(prints)) > 1, "twenty ids in one cell all printed one number"
    assert SortOption.CLOSEST in _offered(returned)


def test_a_sort_whose_readings_are_all_equal_is_never_offered():
    """The failure a naive check misses, and the one *Most reliable* is.

    Every sort ends on the player id, so a sort whose readings are all equal
    resorts the list into **id order** — a different order, carrying nothing.
    Drawn, that control offers the player a reshuffle by player id and calls it
    *most reliable*.

    The rows below are deliberately in an order the ids do not agree with, which
    is what makes the naive check say *yes* here.
    """

    descending = build.rows_printing_one_distance(
        3, mus=(build.SEARCHER_MU - 0.4, build.SEARCHER_MU - 0.2, build.SEARCHER_MU)
    )
    returned = _run(build.context(descending)).returned

    assert _ids(returned) != sorted(_ids(returned)), (
        "the fixture agrees with id order, so it asserts nothing"
    )
    offered = _offered(returned)
    assert SortOption.MOST_RELIABLE not in offered, (
        "the reliability term stands down for everybody, so nothing tells these "
        "rows apart"
    )
    assert SortOption.CLOSEST not in offered, "their cards all print one distance"


def test_closest_is_offered_when_it_would_actually_reorder():
    """And *Most reliable* is not, for as long as the reliability term stands
    down for everybody — a fact re-derived per search rather than hardcoded."""

    spread = (
        build.row(1, latitude=51.55),
        build.row(2, latitude=51.51),
        build.row(3, latitude=51.53),
    )
    offered = _offered(_run(build.context(spread)).returned)

    assert SortOption.CLOSEST in offered
    assert SortOption.MOST_RELIABLE not in offered
    assert SortOption.EVENEST not in offered


def test_most_reliable_is_offered_on_a_search_whose_candidates_have_a_record():
    """The other half of the same derivation, and the one that had never fired.

    ``MOST_RELIABLE``'s condition is a fact about **this search** rather than
    about the platform: the moment two candidates carry published scores that
    tell them apart, the control is honest and is drawn. Most searches still do
    not draw it, because most people have no record — which is the derivation
    working rather than a gap.
    """

    rows = (
        build.row(1, mu=build.SEARCHER_MU),
        build.row(2, mu=build.SEARCHER_MU - 0.2),
        build.row(3, mu=build.SEARCHER_MU - 0.4),
    )
    # Deliberately not in Fit order, so *Most reliable* is a genuine reorder
    # rather than the returned order under another name.
    scores = {
        build.player(1): build.published_score(41),
        build.player(2): build.published_score(88),
        build.player(3): build.published_score(63),
    }

    offered = _offered(_run(build.context(rows, player_scores=scores)).returned)

    assert SortOption.MOST_RELIABLE in offered


def test_one_published_score_among_three_still_tells_the_rows_apart():
    """Two readings — a number and an absence — is two readings.

    The absent one sorts **last** rather than at zero, which is ``CLOSEST``'s
    rule for ``CLOSEST``'s reason, and the control is offered because the order
    it produces is genuinely different.
    """

    rows = (
        build.row(1, mu=build.SEARCHER_MU),
        build.row(2, mu=build.SEARCHER_MU - 0.2),
        build.row(3, mu=build.SEARCHER_MU - 0.4),
    )
    scores = {build.player(3): build.published_score(88)}

    offered = _offered(_run(build.context(rows, player_scores=scores)).returned)

    assert SortOption.MOST_RELIABLE in offered


def test_the_evidence_gate_excludes_nobody_on_todays_inputs():
    """**Live and inert, on purpose.** It is standing insurance, in place before
    the day *we know nothing about this person* could quietly become a passing
    score — and a test says so, so that the day it starts biting is a diff."""

    ordinary = _run(build.context(tuple(build.row(n) for n in range(1, 6))))

    assert all(row.admission.admitted for row in ordinary.returned)
    assert all(
        row.withheld_reason is None for row in ordinary.returned
    )


# ---------------------------------------------------------------------------
# The one lift that admits
# ---------------------------------------------------------------------------


def _a_poor_pairing(number: int, **overrides):
    """Somebody the engine would not show: opposed intent, nothing shared, far off.

    Built to sit below the quality floor rather than pinned to a number, so a
    ruleset release that moves the floor moves this fixture with it. Every test
    below states the state it is in first, so a pairing that stopped being poor
    fails loudly instead of quietly testing nothing.
    """

    return build.row(
        number,
        mu=build.SEARCHER_MU + 0.25,
        declared_intent="FOR_FUN",
        tags=("HERE_FOR_THE_SOCIAL", "PLAYS_FOR_FUN"),
        slots=(),
        latitude=51.59,
        **overrides,
    )


def test_only_an_interest_lift_admits_somebody_below_the_floor():
    """*An interest lift is a human's own yes and outranks the engine's opinion.*

    ``docs/adr/0099`` as amended: it is the **only** guaranteed inclusion left,
    and it is the only reason that reaches the wire — because it is the only one
    that can be why somebody is on the screen at all.
    """

    poor = _a_poor_pairing(1)
    without = _run(build.context((poor, build.row(2))))
    assert poor.player_id in _ids(without.near_misses), (
        "the fixture stopped being a poor pairing, so nothing below is tested"
    )

    with_a_yes = _run(
        build.context(
            (poor, build.row(2)),
            interest_days_ago={build.player(1): 18},
        )
    )

    lifted = next(
        row for row in with_a_yes.returned if row.player_id == poor.player_id
    )
    assert lifted.inclusion_reason.value == "INTEREST_LIFT"
    assert "INTEREST_RECEIVED" in {
        move.signal.value for move in lifted.liveness.reasons
    }, "the lift admitted somebody and did not say why"


def test_the_newcomer_and_zero_exposure_lifts_reorder_and_never_admit():
    """**Exposure fairness is not a reason to show somebody a bad evening.**

    Both fire on this candidate — they are new, and nobody has been shown them
    all week — and neither puts them on a screen. The store records why they
    would have been lifted; the floor still decides whether they are there.
    """

    newly = build.NOW - timedelta(days=1)
    poor = _a_poor_pairing(1, profile_created_at=newly)

    shortlist = _run(build.context((poor, build.row(2)), times_shown={}))

    assert poor.player_id in _ids(shortlist.near_misses), (
        "the newcomer or the zero-exposure lift admitted somebody below the floor"
    )
    assert poor.player_id not in _ids(shortlist.returned)


def test_the_lift_does_not_move_the_number_it_admitted_on():
    """The Fit on the card is the Fit the engine computed, lift or no lift.

    ``rank_key`` is where the ``+14`` lands, and ``rank_key`` never crosses the
    wire in any shape — which is what lets *Why 78?* keep adding up for a
    candidate who is only there because somebody said yes.
    """

    poor = _a_poor_pairing(1)
    withheld = next(
        row
        for row in _run(build.context((poor, build.row(2)))).near_misses
        if row.player_id == poor.player_id
    )

    lifted = next(
        row
        for row in _run(
            build.context(
                (poor, build.row(2)), interest_days_ago={build.player(1): 2}
            )
        ).returned
        if row.player_id == poor.player_id
    )

    assert lifted.modified.points == pytest.approx(withheld.modified.points)
    assert lifted.rank_key > lifted.modified.points, "the +14 landed nowhere"
