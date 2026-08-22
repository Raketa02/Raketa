"""The facts one pure function reads, and the five deadlines it reads them against.

Small, and every claim here is one a card downstream prints as a number. The
counting rules in particular: **seats paid and seats held-but-unpaid are two
numbers, never one** (``Raketa02/Raketa#74``), because folding them together is
how four people are told a match is complete while a seat may still lapse.
"""

from __future__ import annotations

import pytest

from app.kernel import (
    HoldPolicy,
    InvariantViolated,
    MatchRecord,
    Sport,
    Vacancy,
    born_late,
    committed_on_fill,
    court_named_at,
    deadlines,
    door_code_at,
    filled,
    held_unpaid,
    hours,
    is_full,
    is_terminal,
    match_end,
    minutes,
    result_window,
    seat_count,
    vacancy_expires_at,
)
from tests.unit.match_records import DURATION, START, a_match, at, seats


def test_a_held_seat_nobody_paid_for_is_its_own_number() -> None:
    two_paid_one_held = a_match(paid=2, held=1)

    assert seat_count(two_paid_one_held) == 4
    assert filled(two_paid_one_held) == 2
    assert held_unpaid(two_paid_one_held) == 1
    assert not is_full(two_paid_one_held)


def test_a_match_is_full_only_when_every_seat_is_paid() -> None:
    assert is_full(a_match(paid=4))
    assert not is_full(a_match(paid=3, held=1))


def test_only_the_four_cancellations_are_terminal() -> None:
    """A played match still moves: `needsResult -> confirmResult -> completed`."""

    for fact in (
        "inventory_lost",
        "club_cancelled",
        "weather",
        "form_cancelled",
        "checkpoint_cancelled",
    ):
        assert is_terminal(a_match(paid=2, **{fact: True}))

    assert not is_terminal(a_match(paid=4, result_agreed=True))
    assert not is_terminal(a_match(paid=4, no_show=True))


def test_the_five_deadlines_are_all_relative_to_the_start() -> None:
    doubles = a_match(paid=2)
    when = deadlines(doubles)

    assert when.play == START
    assert when.check == at(-120)
    assert when.join_cut == at(-30)
    assert when.rescue == at(-240)
    assert when.commit == at(-1440)
    assert not when.singles


def test_a_singles_court_starts_looking_two_hours_sooner() -> None:
    """It loses the whole game rather than a quarter of it."""

    singles = a_match(sport=Sport.TENNIS, paid=1)
    when = deadlines(singles)

    assert when.singles
    assert when.rescue == at(-360)


def test_commitment_is_the_earlier_of_the_club_window_and_the_backstop() -> None:
    """A club may bring commitment forward, and can never push it back.

    A club needing two days' notice binds everybody two days out; one needing
    four hours still binds them at the platform's twelve, because the backstop
    is a floor under the marketplace's promise and not a default a club edits.
    """

    needs_two_days_notice = a_match(paid=2, policy=HoldPolicy(window=hours(48)))
    needs_four_hours = a_match(paid=2, policy=HoldPolicy(window=hours(4)))
    exactly_the_backstop = a_match(paid=2, policy=HoldPolicy(window=hours(12)))

    assert deadlines(needs_two_days_notice).commit == at(-2880)
    assert deadlines(needs_four_hours).commit == at(-720)
    assert deadlines(exactly_the_backstop).commit == at(-720)


def test_the_door_code_and_the_two_moments_after_the_last_point() -> None:
    played = a_match(paid=4)

    assert door_code_at(played) == at(-15)
    assert match_end(played) == at(DURATION)
    assert result_window(played) == at(DURATION + 24 * 60)


def test_the_court_is_named_at_the_same_moment_the_door_code_is() -> None:
    """One constant, two readers. `courtAssigned` — the only state that names a
    specific court (ADR-0035) — and *ready to play* are the same instant seen
    from Courts and from Matches, so computing `start - 15min` twice is the
    failure this layer exists to make unreachable.

    `court_named_at` takes a **start** rather than a record, because Courts has
    no `MatchRecord` to hand: a club's own block on a Tuesday morning is a
    reservation with a start and no match behind it at all.
    """

    played = a_match(paid=4)

    assert court_named_at(START) == at(-15)
    assert court_named_at(played.start) == door_code_at(played)


def test_committing_on_the_spot_is_told_apart_from_committing_at_the_deadline() -> None:
    """A minute of tolerance, so a match that filled a moment early has not raced."""

    at_the_deadline = a_match(paid=4, committed_at=at(-1440))
    a_moment_after = a_match(paid=4, committed_at=at(-1439))
    on_the_spot = a_match(paid=4, committed_at=at(-100))

    assert not committed_on_fill(at_the_deadline)
    assert not committed_on_fill(a_moment_after)
    assert committed_on_fill(on_the_spot)


def test_a_match_that_never_committed_did_not_commit_on_fill() -> None:
    assert not committed_on_fill(a_match(paid=4))


def test_born_late_is_about_the_posting_and_not_about_the_clock() -> None:
    """*Posted after its own deadline* is a different sentence from *the deadline
    has passed*, and telling its creator the second would warn her about
    something she did on purpose."""

    ordinary = a_match(paid=2, created=-4320)
    posted_late = a_match(paid=2, created=-1400)

    assert not born_late(ordinary)
    assert born_late(posted_late)


def test_the_newest_hole_is_the_one_that_describes_the_match() -> None:
    """Two departures, one thirty hours ago and one an hour ago, is a match that
    lost a player an hour ago."""

    none_at_all = a_match(paid=2)
    two_holes = a_match(
        paid=1,
        open_vacancies=(Vacancy(at(-1800)), Vacancy(at(-60))),
    )

    assert vacancy_expires_at(none_at_all) is None
    assert vacancy_expires_at(two_holes) == at(-60 + 24 * 60)


def test_a_record_whose_seats_disagree_with_its_sport_is_refused() -> None:
    with pytest.raises(InvariantViolated, match="sold in"):
        MatchRecord(
            sport=Sport.PADEL,
            start=START,
            duration=DURATION,
            created=at(-4320),
            seats=seats(2),
        )


def test_a_match_of_no_length_is_refused() -> None:
    with pytest.raises(InvariantViolated, match="duration"):
        MatchRecord(
            sport=Sport.PADEL,
            start=START,
            duration=minutes(0),
            created=at(-4320),
            seats=seats(4),
        )


def test_more_seats_opened_than_the_court_is_sold_for_is_refused() -> None:
    with pytest.raises(InvariantViolated, match="seats opened"):
        a_match(paid=1, open_seats=5)


def test_a_club_policy_that_cannot_mean_anything_is_refused() -> None:
    with pytest.raises(InvariantViolated, match="cancellation window"):
        HoldPolicy(window=minutes(0))
    with pytest.raises(InvariantViolated, match="join cutoff"):
        HoldPolicy(join_cut=minutes(-1))
    with pytest.raises(InvariantViolated, match="maximum hold age"):
        HoldPolicy(max_hold_age=minutes(-1))


def test_a_club_may_decline_to_hold_speculatively_at_all() -> None:
    """Zero is a decision, and there is no platform floor under it."""

    assert HoldPolicy(max_hold_age=minutes(0)).max_hold_age == 0
