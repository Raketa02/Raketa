"""The reading — the radar's terminal stage, at the pure seam.

``docs/adr/0174`` §1, §3 and §5: a bound ``SearchContext`` in, every player the
radar may draw out, no I/O. What is asserted here is what the radar decides that
the deck does not — **five gates asked and four not asked**, no floor, no order
but the distance, a bearing on every row, and the chip computed by the deck's
own rule over the deck's own gates.
"""

from __future__ import annotations

from math import isclose

from app.engines.matchfit.core import DegradedReason, Term
from app.engines.matchfit.v1 import MatchFitV1
from app.kernel import Sport
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.deck import INHERITED_ON_THE_DECK
from app.modules.matchmaking.domain.gates import (
    GATE_ROSTER,
    GateCode,
    asked_on,
    gate_of,
)
from app.modules.matchmaking.domain.geography import (
    Point,
    bearing_deg,
    distance_km,
    drawn_spot,
)
from app.modules.matchmaking.domain.radar import ratings_across, read
from app.modules.matchmaking.domain.searches import (
    InclusionReason,
    RatedSportRecord,
    SearchInitiation,
    SearchSurface,
)
from app.modules.matchmaking.domain.shortlist import generate
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from tests.unit import matchmaking_builders as build

ENGINE = MatchFitV1()

#: The five the radar asks, and the reach beside them — which is the circle
#: bounding the population rather than a judgement about anybody in it.
ASKED_ON_THE_RADAR = frozenset(
    {
        GateCode.BLOCKED,
        GateCode.HELD_ACCOUNT,
        GateCode.ACCOUNT_INACTIVE,
        GateCode.GENDER_PREFERENCE,
        GateCode.NOT_RATED,
        GateCode.OUTSIDE_RADIUS,
    }
)


def _on_the_radar(candidate, **context_kwargs):
    context = build.context((candidate,), surface=SearchSurface.RADAR, **context_kwargs)
    return gate_of(candidate, context, distance_km=0.0)


# ---------------------------------------------------------------------------
# The gates
# ---------------------------------------------------------------------------


def test_the_radar_asks_five_gates_and_the_reach_and_every_other_surface_asks_ten():
    """``the-radar.md`` §3's table, asserted against the roster rather than
    against prose. The four not asked are **not relaxed** — ADR-0099 forbids
    that — they are not asked, because the surface has no question for them."""

    assert asked_on(SearchSurface.RADAR) == ASKED_ON_THE_RADAR
    for surface in SearchSurface:
        if surface is not SearchSurface.RADAR:
            assert asked_on(surface) == frozenset(GATE_ROSTER), surface


def test_the_four_the_radar_does_not_ask_exclude_nobody_on_it():
    """An open court, a far Level, an opt-out under an engine push: all drawn.

    The opt-out is asked under ``ENGINE`` initiation, which is the one case
    the gate fires anywhere — a ``HUMAN`` reading would pass by construction."""

    with_a_court = build.row(1)
    assert (
        _on_the_radar(with_a_court, open_challenges=frozenset({with_a_court.player_id}))
        is None
    )
    assert _on_the_radar(build.row(2, mu=build.SEARCHER_MU + 2.0)) is None
    opted_out = build.row(3, proposals_opt_in=False)
    assert _on_the_radar(opted_out, initiation=SearchInitiation.ENGINE) is None
    assert (
        gate_of(
            opted_out,
            build.context((opted_out,), initiation=SearchInitiation.ENGINE),
            distance_km=0.0,
        )
        is GateCode.PROPOSALS_OPT_OUT
    ), "the same row under a shortlist, so the radar's None is not the gate's"


def test_the_five_the_radar_asks_still_exclude_on_it():
    candidate = build.row(1)
    assert (
        _on_the_radar(candidate, blocked=frozenset({candidate.player_id}))
        is GateCode.BLOCKED
    )
    assert (
        _on_the_radar(candidate, held=frozenset({candidate.player_id}))
        is GateCode.HELD_ACCOUNT
    )
    assert (
        _on_the_radar(candidate, unshowable=frozenset({candidate.player_id}))
        is GateCode.ACCOUNT_INACTIVE
    )
    assert _on_the_radar(build.row(2, rating_status="")) is GateCode.NOT_RATED
    assert (
        _on_the_radar(build.row(3, gender="MAN", gender_preference="SAME_GENDER_ONLY"))
        is GateCode.GENDER_PREFERENCE
    )


def test_the_reach_is_the_circle_on_the_radar_too():
    """Not a gate on the population but its bound — and it is the circle the
    deck uses, measured cell to cell, so the radar reaches exactly as far as
    the deck deals."""

    far = build.row(1, latitude=build.CENTRE.latitude + 0.2)
    context = build.context((far,), surface=SearchSurface.RADAR)
    assert gate_of(far, context, distance_km=22.0) is GateCode.OUTSIDE_RADIUS


def test_a_reading_records_every_gate_it_did_not_ask_as_a_zero():
    """The histogram keeps all ten keys on every surface, so the four the
    radar does not ask are recorded zeros — which ``search-telemetry.md``
    reads as *not asked* on a ``RADAR`` row, never as *nobody was excluded*."""

    with_a_court = build.row(1)
    generated = generate(
        build.context(
            (with_a_court,),
            surface=SearchSurface.RADAR,
            open_challenges=frozenset({with_a_court.player_id}),
        )
    )
    assert set(generated.excluded_by_gate) == {code.value for code in GATE_ROSTER}
    assert generated.excluded_by_gate[GateCode.OPEN_CHALLENGE.value] == 0
    assert len(generated.admitted) == 1


# ---------------------------------------------------------------------------
# The ruler, the bearing and the reading
# ---------------------------------------------------------------------------


def a_reading(rows, **context):
    return read(
        build.context(
            rows,
            facts=build.searcher(mode=INHERITED_ON_THE_DECK),
            surface=SearchSurface.RADAR,
            **context,
        ),
        ENGINE,
    )


def drawn_ids(reading):
    return [row.scored.player_id for row in reading.rows]


def test_the_intent_term_stands_down_on_the_radar_as_it_does_on_the_deck():
    """One ruler for every viewer (``docs/adr/0174`` §3 by way of ADR-0169 §2),
    so the same pair prints the same Fit on the deck and on the radar."""

    reading = a_reading((build.row(1, declared_intent="COMPETITIVE"),))

    (row,) = reading.rows
    assert Term.INTENT_ALIGNMENT not in {term.term for term in row.scored.fit.terms}
    assert {stood.term: stood.reason for stood in row.scored.fit.degraded_terms}[
        Term.INTENT_ALIGNMENT
    ] is DegradedReason.NOT_READ_ON_THIS_SURFACE


def test_a_bearing_is_north_nought_clockwise_and_a_whole_degree():
    origin = Point(latitude=51.5, longitude=-0.1)
    assert bearing_deg(origin, Point(latitude=51.6, longitude=-0.1)) == 0
    assert bearing_deg(origin, Point(latitude=51.5, longitude=0.0)) == 90
    assert bearing_deg(origin, Point(latitude=51.4, longitude=-0.1)) == 180
    assert bearing_deg(origin, Point(latitude=51.5, longitude=-0.2)) == 270
    # Just west of north rounds up to the top of the compass and wraps to 0,
    # never 360.
    assert bearing_deg(origin, Point(latitude=52.5, longitude=-0.1001)) == 0


def test_everyone_inside_the_reach_is_drawn_with_a_fit_floor_or_no_floor():
    """Karol with a court, Magda passed on, a Level the deck would never deal,
    and a pairing under the floor: all four drawn, each with a Fit."""

    with_a_court = build.row(1)
    level_far = build.row(2, mu=build.SEARCHER_MU + 2.0)
    poor = build.row(3, tags=(), slots=("2:MORNING",))

    reading = a_reading(
        (with_a_court, level_far, poor),
        open_challenges=frozenset({with_a_court.player_id}),
    )

    assert set(drawn_ids(reading)) == {
        with_a_court.player_id,
        level_far.player_id,
        poor.player_id,
    }
    assert reading.counts.n_scored == 3
    assert reading.counts.n_returned == 3
    assert reading.counts.n_near_miss_recorded == 0
    assert reading.near_misses == ()
    assert reading.best_withheld_fit is None
    assert all(0 <= row.scored.modified.points <= 100 for row in reading.rows)


def test_the_order_is_the_drawn_distance_then_the_player_id_and_nothing_else():
    """No rank, no bands, no Liveness in the order — and a set is never the
    source of one (``docs/adr/0105``): ties break on the id."""

    near = build.row(1)
    further = build.row(2, latitude=build.CENTRE.latitude + 0.03)
    furthest = build.row(3, latitude=build.CENTRE.latitude + 0.06)
    same_cell = build.rows_printing_one_distance(2)

    reading = a_reading((furthest, further, near))
    assert drawn_ids(reading) == [near.player_id, further.player_id, furthest.player_id]

    tied = a_reading(same_cell)
    assert drawn_ids(tied) == sorted(row.player_id for row in same_cell)


def test_every_row_carries_its_bearing_spot_to_spot():
    east = build.row(1, longitude=build.CENTRE.longitude + 0.05)
    reading = a_reading((east,))

    (row,) = reading.rows
    viewer = drawn_spot(build.SEARCHER_ID, build.CENTRE)
    theirs = drawn_spot(
        build.player(1), Point(build.CENTRE.latitude, build.CENTRE.longitude + 0.05)
    )
    assert row.bearing_deg == bearing_deg(viewer, theirs)
    assert 45 <= row.bearing_deg <= 135
    assert isclose(row.scored.generated.drawn_distance_km, distance_km(viewer, theirs))


def test_somebody_who_said_yes_is_drawn_where_their_distance_puts_them_and_says_so():
    """The lift admits nobody here — there is no floor to admit under — and it
    moves nobody; what survives is the reason, which the sheet's *Wants to
    play you* line reads."""

    liker = build.row(2, latitude=build.CENTRE.latitude + 0.03)
    nearer = build.row(1)

    reading = a_reading((liker, nearer), interest_days_ago={build.player(2): 2})

    assert drawn_ids(reading) == [nearer.player_id, liker.player_id]
    by_id = {row.scored.player_id: row for row in reading.rows}
    assert (
        by_id[liker.player_id].scored.inclusion_reason is InclusionReason.INTEREST_LIFT
    )
    assert by_id[nearer.player_id].scored.inclusion_reason is not (
        InclusionReason.INTEREST_LIFT
    )


def test_a_reading_has_no_count_cap_and_no_nearest_n():
    """The population is bounded by the reach and by nothing else
    (``docs/adr/0174`` §1): more people than a shortlist may carry, all drawn."""

    more_than_a_shortlist = LIVE_RULESET.shape.shortlist_max + 5
    rows = tuple(build.row(n) for n in range(1, more_than_a_shortlist + 1))

    reading = a_reading(rows)

    assert len(reading.rows) == more_than_a_shortlist
    assert reading.counts.n_returned == more_than_a_shortlist


def test_the_sport_chips_are_read_across_every_partition_in_registry_order():
    """``ratings[]`` is every sport the player is rated in, off the index's
    partitions, walked in the sport registry's own order (``docs/adr/0105``)
    — never a set's — and a player rated in nothing reads as empty."""

    padel = build.row(1, mu=2.8)
    tennis = build.row(1, mu=3.1, sport=Sport.TENNIS.value)
    somebody_else = build.row(2, mu=2.0)
    snapshots = {
        Sport.PADEL: CandidateSnapshot(
            partition=Partition.for_sport(Sport.PADEL),
            rows=(padel, somebody_else),
            snapshot_version=1,
            caught_up_at=build.NOW,
        ),
        Sport.TENNIS: CandidateSnapshot(
            partition=Partition.for_sport(Sport.TENNIS),
            rows=(tennis,),
            snapshot_version=1,
            caught_up_at=build.NOW,
        ),
    }

    chips = ratings_across(
        snapshots, (build.player(1), build.player(2), build.player(3))
    )

    assert chips[build.player(1)] == (
        RatedSportRecord(sport=Sport.PADEL, level=2.8),
        RatedSportRecord(sport=Sport.TENNIS, level=3.1),
    )
    assert chips[build.player(2)] == (RatedSportRecord(sport=Sport.PADEL, level=2.0),)
    assert chips[build.player(3)] == ()
