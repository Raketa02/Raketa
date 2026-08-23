"""The pure half of the ranked funnel: eligibility, order, diversity, floors.

Everything here is a function of values — no clock read, no repository, no
engine — which is exactly what ``funnel.py`` was split out to make possible. The
composer's own suite (``test_compose_shelves.py``) exercises the reach; this one
exercises the rules, where a case can be written as a sentence about two
candidates rather than as a fixture with a database behind it.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.kernel import Sport

from app.modules.now.domain.funnel import (
    BEST_FIT_CAP,
    BEST_FIT_FLOOR,
    CANDIDATE_HORIZON_DAYS,
    CANDIDATE_LIMIT,
    COMMON_RULES,
    FULL_CAP,
    FULL_FLOOR,
    MAX_PER_CLUB_HOUR,
    Exclusion,
    Fit,
    Lane,
    Scored,
    Viewer,
    cap_for,
    clamp_badge,
    code_for,
    diversify,
    exclusions,
    feed_key,
    floor_for,
    hour_bucket,
    keep,
    rules_for,
)
from app.modules.now.domain.vocabulary import ShelfCode
from tests.unit.match_records import START, at
from tests.unit.shelf_doubles import a_club, a_context, a_match

SPORTS = frozenset({Sport.PADEL})


def scored(fit: int, *, starts: int = 0, club=None, coverage: int = 90) -> Scored:
    return Scored(
        context=a_context(record=a_match(paid=1, starts=starts), club=club or a_club()),
        fit=fit,
        coverage=coverage,
        badge=Fit(score=clamp_badge(fit)),
        has_free_seat=True,
    )


# --- 1 · eligibility is exhaustive, and it is exactly the delta's set ------


def test_the_rule_set_is_exactly_the_one_the_delta_lists() -> None:
    """Eight common rules, one seat rule each, and no travel ceiling.

    ``WithinTravelCeiling`` is in **neither** lane — travel is a weight-8 term
    that never excludes at any distance — and a rule set that quietly grew one
    would filter out a good match twenty minutes away with nothing red.
    """

    assert COMMON_RULES == (
        Exclusion.NOT_ALREADY_MINE,
        Exclusion.STARTS_IN_FUTURE,
        Exclusion.BEFORE_JOIN_CUTOFF,
        Exclusion.NOT_CANCELLED,
        Exclusion.SPORT_MATCHES_FILTER,
        Exclusion.NO_SCHEDULE_CONFLICT,
        Exclusion.NOT_SUPPRESSED,
        Exclusion.NOT_ON_STANDBY,
    )
    assert rules_for(Lane.OPEN) == (*COMMON_RULES, Exclusion.HAS_FREE_SEAT)
    assert rules_for(Lane.FULL) == (*COMMON_RULES, Exclusion.IS_FULL)
    assert not {rule.value for rule in Exclusion} & {"withinTravelCeiling"}


def test_every_rule_is_evaluated_even_once_one_has_already_failed() -> None:
    """The whole point of answering a set rather than a boolean.

    A candidate that is both already hers *and* full reports both, because the
    operational story *"seven of them already full"* is a different story from
    *"seven of them already mine"* and a short-circuit throws the difference
    away.
    """

    mine = uuid4()
    context = a_context(match_id=mine, record=a_match(paid=4))

    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4(), mine=frozenset({mine})),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )

    assert Exclusion.NOT_ALREADY_MINE in failed
    assert Exclusion.HAS_FREE_SEAT in failed


@pytest.mark.parametrize(
    "lane,expected",
    [(Lane.OPEN, Exclusion.HAS_FREE_SEAT), (Lane.FULL, Exclusion.IS_FULL)],
)
def test_the_two_lanes_differ_in_exactly_one_rule(lane, expected) -> None:
    full = a_context(record=a_match(paid=4))
    open_one = a_context(record=a_match(paid=1))
    who = Viewer(player_id=uuid4())

    on_full = exclusions(full, viewer=who, sports=SPORTS, lane=lane, now=at(-240))
    on_open = exclusions(open_one, viewer=who, sports=SPORTS, lane=lane, now=at(-240))

    assert (expected in on_full) is (lane is Lane.OPEN)
    assert (expected in on_open) is (lane is Lane.FULL)


def test_a_match_that_has_started_is_out() -> None:
    context = a_context(record=a_match(paid=1))
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4()),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(1),
    )
    assert Exclusion.STARTS_IN_FUTURE in failed


def test_a_match_past_its_join_cutoff_is_out_while_it_has_not_started() -> None:
    """The two clock rules are different rules and both have to be here.

    A match starting in ten minutes at a club whose cutoff is thirty has not
    started and cannot be joined, which no *StartsInFuture* test would notice.
    """

    context = a_context(record=a_match(paid=1))
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4()),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-10),
    )
    assert Exclusion.BEFORE_JOIN_CUTOFF in failed
    assert Exclusion.STARTS_IN_FUTURE not in failed


def test_a_cancelled_match_is_out() -> None:
    context = a_context(record=a_match(paid=1, club_cancelled=True))
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4()),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )
    assert Exclusion.NOT_CANCELLED in failed


def test_a_match_in_another_sport_is_out() -> None:
    context = a_context(record=a_match(sport=Sport.TENNIS, paid=1))
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4()),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )
    assert Exclusion.SPORT_MATCHES_FILTER in failed


def test_a_match_overlapping_one_she_already_holds_is_out() -> None:
    """The rule the specification called the one players notice immediately."""

    context = a_context(record=a_match(paid=1))
    clash = (at(-30), at(30))
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4(), busy=(clash,)),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )
    assert Exclusion.NO_SCHEDULE_CONFLICT in failed


def test_a_match_that_begins_exactly_as_hers_ends_does_not_clash() -> None:
    """Half-open on both sides: two abutting bookings are two games."""

    context = a_context(record=a_match(paid=1))
    abutting = (at(-180), START)
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4(), busy=(abutting,)),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )
    assert Exclusion.NO_SCHEDULE_CONFLICT not in failed


def test_a_match_she_is_queued_for_is_out() -> None:
    queued = uuid4()
    context = a_context(match_id=queued, record=a_match(paid=1))
    failed = exclusions(
        context,
        viewer=Viewer(player_id=uuid4(), on_standby=frozenset({queued})),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )
    assert Exclusion.NOT_ON_STANDBY in failed


def test_the_suppression_slot_is_evaluated_and_passes() -> None:
    """A v2 slot that is *in* the set rather than waiting to be added to it.

    Impression capping and dismissals land here, and declaring it now means
    adding them is one rule rather than a refactor of the pipeline. A slot
    nobody evaluates is a slot somebody has to remember to wire up.
    """

    assert Exclusion.NOT_SUPPRESSED in rules_for(Lane.OPEN)
    failed = exclusions(
        a_context(record=a_match(paid=1)),
        viewer=Viewer(player_id=uuid4()),
        sports=SPORTS,
        lane=Lane.OPEN,
        now=at(-240),
    )
    assert Exclusion.NOT_SUPPRESSED not in failed


def test_an_ordinary_candidate_fails_nothing() -> None:
    assert (
        exclusions(
            a_context(record=a_match(paid=1)),
            viewer=Viewer(player_id=uuid4()),
            sports=SPORTS,
            lane=Lane.OPEN,
            now=at(-240),
        )
        == frozenset()
    )


# --- 2 · FEED_ORDER ---------------------------------------------------------


def test_fit_descends_before_anything_else_is_read() -> None:
    strong_late = scored(90, starts=600)
    weak_early = scored(70, starts=60)

    assert feed_key(strong_late, distance_km=None) < feed_key(
        weak_early, distance_km=None
    )


def test_the_sooner_match_wins_a_tie_on_fit() -> None:
    early = scored(80, starts=60)
    late = scored(80, starts=600)

    assert feed_key(early, distance_km=None) < feed_key(late, distance_km=None)


def test_the_nearer_club_wins_a_tie_on_fit_and_start() -> None:
    near = scored(80)
    far = scored(80)

    assert feed_key(near, distance_km=3) < feed_key(far, distance_km=40)


def test_an_unknown_distance_sorts_last_and_never_first() -> None:
    """A club the platform cannot place is not thereby the nearest one."""

    placed = scored(80)
    unplaced = scored(80)

    assert feed_key(placed, distance_km=99) < feed_key(unplaced, distance_km=None)


def test_the_fourth_comparator_is_total() -> None:
    """Two distinct candidates never compare equal through the whole chain.

    Without it the order falls back on retrieval order, which is the query plan,
    and two identical requests reshuffle the shelf under the player's thumb.
    """

    one = scored(80)
    two = scored(80)

    assert feed_key(one, distance_km=None) != feed_key(two, distance_km=None)


# --- 3 · diversity reorders and never shortens ------------------------------


def test_diversity_defers_a_third_card_from_one_club_and_hour() -> None:
    club = a_club()
    crowd = [scored(90 - n, club=club) for n in range(4)]
    elsewhere = scored(50, club=a_club())

    out = diversify([*crowd, elsewhere])

    assert out[:MAX_PER_CLUB_HOUR] == tuple(crowd[:MAX_PER_CLUB_HOUR])
    assert out[MAX_PER_CLUB_HOUR] is elsewhere


def test_diversity_is_a_permutation_and_never_drops_a_card() -> None:
    """The prototype's defect, named in the delta: it returned fewer than the cap.

    ``MaxPerClubHour`` used to ``continue`` past a blocked candidate, so a shelf
    could come back three cards short with three cards still waiting. A variety
    rule that had already got its way was then also shortening the shelf.
    """

    club = a_club()
    crowd = [scored(90 - n, club=club) for n in range(6)]

    out = diversify(crowd)

    assert sorted(one.match_id for one in out) == sorted(one.match_id for one in crowd)
    assert len(out) == len(crowd)


def test_diversity_is_idempotent() -> None:
    club = a_club()
    ranked = [scored(90 - n, club=club) for n in range(5)]

    once = diversify(ranked)

    assert diversify(once) == once


def test_the_same_club_at_a_different_hour_is_not_crowded() -> None:
    """Two per club **per hour**, not two per club.

    A club running a Tuesday evening and a Thursday morning is offering two
    different things, and a rule that ignored the hour would push the second
    evening down for a match nine hours away from the first.
    """

    club = a_club()
    evening = [scored(90 - n, club=club, starts=0) for n in range(2)]
    later = [scored(80 - n, club=club, starts=180) for n in range(2)]

    out = diversify([*evening, *later])

    # Nothing moved: four cards, two hours, two per hour.
    assert out == (*evening, *later)
    assert hour_bucket(later[0].start) != hour_bucket(evening[0].start)


def test_a_third_card_in_the_same_hour_goes_behind_a_later_hours_cards() -> None:
    """The deferral is visible only against a card it can be pushed behind."""

    club = a_club()
    evening = [scored(90 - n, club=club, starts=0) for n in range(3)]
    later = scored(60, club=club, starts=180)

    out = diversify([*evening, later])

    assert out == (evening[0], evening[1], later, evening[2])


# --- 4 · floors, caps and the retitle ---------------------------------------


def test_the_two_floors_and_the_two_caps_are_the_decided_numbers() -> None:
    """23 cards across four lanes is what 6 · 3 · 8 · 6 adds up to."""

    assert (BEST_FIT_FLOOR, FULL_FLOOR) == (70, 80)
    assert (BEST_FIT_CAP, FULL_CAP) == (6, 3)
    assert cap_for(Lane.OPEN) == BEST_FIT_CAP
    assert cap_for(Lane.FULL) == FULL_CAP


def test_the_retrieval_bounds_are_the_decided_numbers() -> None:
    """Pinned to their **literals**, because a widening is a decision.

    Every other test that reads them compares the funnel's behaviour against the
    constant itself, so it cannot see the constant move — which is exactly how a
    two-week suggestion horizon quietly becomes a three-month one, and how a
    safety valve stops being one.
    """

    # Thirty days, bounded from below by when a match is posted: the seeded
    # world posts one a fortnight before it is played, so a fourteen-day horizon
    # made a match invisible on the day it went up.
    assert CANDIDATE_HORIZON_DAYS == 30
    # Far above what survives eligibility on any realistic screen, which is what
    # makes reaching it a signal rather than a routine truncation.
    assert CANDIDATE_LIMIT == 300


def test_the_retitled_shelf_drops_its_floor_and_the_waitlist_never_does() -> None:
    assert floor_for(Lane.OPEN, retitled=False) == BEST_FIT_FLOOR
    assert floor_for(Lane.OPEN, retitled=True) is None
    assert floor_for(Lane.FULL, retitled=False) == FULL_FLOOR
    assert floor_for(Lane.FULL, retitled=True) == FULL_FLOOR


def test_the_shelf_codes_are_the_three_the_client_holds_a_title_for() -> None:
    assert code_for(Lane.OPEN, retitled=False) is ShelfCode.BEST_FIT
    assert code_for(Lane.OPEN, retitled=True) is ShelfCode.SAME_LEVEL
    assert code_for(Lane.FULL, retitled=False) is ShelfCode.FULL_WORTH_WAITING


def test_the_cap_is_the_only_pass_that_removes_a_card() -> None:
    ranked = [scored(90 - n) for n in range(9)]

    assert len(keep(ranked, cap=BEST_FIT_CAP)) == BEST_FIT_CAP
    assert len(diversify(ranked)) == len(ranked)


# --- 5 · the badge's display clamp ------------------------------------------


@pytest.mark.parametrize(
    "fit,shown", [(0, 20), (3, 20), (19, 20), (20, 20), (55, 55), (99, 99), (100, 99)]
)
def test_the_badge_is_clamped_at_display_and_never_in_the_model(fit, shown) -> None:
    """*A score of 3 is not more useful than a score of 20 — both mean no.*

    And never 100, because certainty is never warranted. The engine keeps its
    true 0–100 range and that value is what ranks the list, which is why the
    clamp lives here and not in the arithmetic.
    """

    assert clamp_badge(fit) == shown


def test_the_true_score_ranks_and_the_clamped_one_does_not() -> None:
    """Two matches a clamp would tie still rank in the order they scored."""

    hopeless = scored(3)
    bad = scored(15)

    assert clamp_badge(hopeless.fit) == clamp_badge(bad.fit)
    assert feed_key(bad, distance_km=None) < feed_key(hopeless, distance_km=None)
