"""One clock slot, one rule, and the one boundary it refuses to point at.

ADR-0073 gives a card exactly one countdown and fixes which moment fills it with
a rule rather than with thirty-six judgements: *the next moment at which
something happens to the viewer whether they act or not*. `kernel.card_clock`
is that rule, and this file is the four claims it makes — the examples the ADR
itself writes out, the empty slot, the claim that is not the viewer's, and the
agreement with the ladder that makes it one rule rather than a second list of
thresholds.
"""

from __future__ import annotations

import pytest

from app.kernel import (
    MatchKind,
    MatchRecord,
    SeatClaim,
    Situation,
    Vacancy,
    card_clock,
    deadlines,
    door_code_at,
    match_end,
    next_wake,
    result_window,
    situation,
    turned_up,
)

from tests.unit.match_records import OFFSETS, POLICIES, a_match, at

# --- the ADR's own five examples ------------------------------------------


def test_a_forming_match_counts_to_the_court_locking_in() -> None:
    record = a_match(paid=1)
    assert situation(record, None, at(-2000)) is Situation.FORMING
    assert card_clock(record, at(-2000)) == deadlines(record).commit


def test_a_full_match_counts_to_settlement() -> None:
    """*"a full one to settlement"* — the commitment deadline it settles at."""

    record = a_match(paid=4)
    assert situation(record, None, at(-2000)) is Situation.FULL
    assert card_clock(record, at(-2000)) == deadlines(record).commit


def test_a_match_about_to_start_counts_to_the_start() -> None:
    record = a_match(paid=4, committed_at=at(-1440))
    assert situation(record, None, at(-10)) is Situation.READY
    assert card_clock(record, at(-10)) == record.start


def test_a_match_wanting_a_score_counts_to_the_twenty_four_hours() -> None:
    record = a_match(paid=4)
    played = int((match_end(record) - record.start).total_seconds() // 60) + 1
    assert situation(record, None, at(played)) is Situation.NEEDS_RESULT
    assert card_clock(record, at(played)) == result_window(record)


def test_a_committed_match_short_a_player_counts_to_the_rescue_window() -> None:
    record = a_match(
        paid=3,
        committed_at=at(-1440),
        open_vacancies=(Vacancy(vacated_at=at(-1400)),),
    )
    assert situation(record, None, at(-1000)) is Situation.REPLACEMENT
    assert card_clock(record, at(-1000)) == deadlines(record).rescue


# --- the empty slot -------------------------------------------------------


@pytest.mark.parametrize(
    "ending",
    [
        {"inventory_lost": True, "club_cancelled": True},
        {"club_cancelled": True},
        {"weather": True},
        {"form_cancelled": True},
        {"checkpoint_cancelled": True},
    ],
)
def test_a_cancelled_card_counts_to_nothing(ending: dict[str, bool]) -> None:
    """Over or cancelled *counts to nothing*, never to zero."""

    record = a_match(paid=2, **ending)
    assert card_clock(record, at(-2000)) is None


def test_a_card_past_its_result_window_counts_to_nothing() -> None:
    record = a_match(paid=4)
    past = int((result_window(record) - record.start).total_seconds() // 60) + 1
    assert situation(record, None, at(past)) is Situation.PLAYED_NO_SCORE
    assert card_clock(record, at(past)) is None


def test_the_moment_is_strictly_ahead_so_a_card_never_counts_to_now() -> None:
    """A boundary exactly at `now` has happened, and a countdown to it is zero.

    The same strictness `next_wake` uses, and for the sharper reason here: a
    clock reading 0:00 for ever is the frozen number ADR-0053 calls *broken
    rather than static*.
    """

    record = a_match(paid=4)
    commit = deadlines(record).commit
    assert card_clock(record, commit) != commit


# --- the claim, which is the viewer's and not the match's ------------------


def test_the_viewers_own_claim_takes_the_slot() -> None:
    """Five minutes to pay beats every deadline the match has."""

    record = a_match(paid=1)
    mine = at(-1995)
    assert card_clock(record, at(-2000), claim_expires_at=mine) == mine


def test_a_lapsed_claim_of_the_viewers_own_gives_the_slot_back() -> None:
    record = a_match(paid=1)
    assert (
        card_clock(record, at(-2000), claim_expires_at=at(-2001))
        == deadlines(record).commit
    )


def test_a_stranger_s_claim_never_points_the_viewers_countdown() -> None:
    """The one difference between this and `next_wake`, and the whole of it.

    A claim is about the person buying the seat. On the record it is a wake —
    the reaper has to run — and on a card it would be five minutes of somebody
    else's payment counting down under a player who is not paying for anything.
    """

    strangers = SeatClaim(seat_index=3, expires_at=at(-2399))
    record = a_match(paid=1, claims=(strangers,))

    assert next_wake(record, at(-2400)) is not None
    assert next_wake(record, at(-2400)).at == strangers.expires_at  # type: ignore[union-attr]
    assert card_clock(record, at(-2400)) == deadlines(record).commit


# --- one rule, agreeing with the ladder -----------------------------------


def _grid() -> list[tuple[MatchRecord, int]]:
    records = [
        a_match(paid=paid, held=held, policy=policy, **facts)
        for policy in POLICIES
        for paid, held in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (1, 1), (3, 1))
        for facts in (
            {},
            {"committed_at": at(-1440)},
            {"open_vacancies": (Vacancy(vacated_at=at(-1400)),)},
            {"kind": MatchKind.PRIVATE},
            {"released_at": at(-1000)},
        )
        # A hole is a seat nobody is on, so a full match cannot carry one — the
        # record refuses it at the door rather than resolving it into a lying
        # card.
        if paid + held < 4 or "open_vacancies" not in facts
    ]
    return [(record, offset) for record in records for offset in OFFSETS]


def test_the_clock_is_always_a_moment_the_ladder_itself_reads() -> None:
    """Never a threshold invented for the countdown.

    The grid is the ladder suite's own — every policy, every seat count, every
    court fact, at every offset either side of every threshold — and the claim
    is that the countdown is drawn from the ladder's boundaries rather than
    from a second list beside them. A rule cannot drift from a list it *is*.
    """

    for record, offset in _grid():
        moment = card_clock(record, at(offset))
        if moment is None:
            continue
        assert moment > at(offset)
        wake = next_wake(record, at(offset))
        assert wake is not None
        assert moment >= wake.at


def test_every_card_that_is_not_over_has_something_to_count_to() -> None:
    """An empty slot means *over*, and never *we had nothing to say*.

    The contrapositive is what matters: if a live card could return `None` the
    client would have to tell *nothing is happening* from *the match is done*,
    and the phone tells them apart by the situation rather than by a blank.
    """

    for record, offset in _grid():
        if card_clock(record, at(offset)) is not None:
            continue
        assert at(offset) >= result_window(record) or _is_over(record)


def _is_over(record: MatchRecord) -> bool:
    return (
        record.inventory_lost
        or record.club_cancelled
        or record.weather
        or record.form_cancelled
        or record.checkpoint_cancelled
    )


def test_the_grid_is_not_empty() -> None:
    """A walk over nothing passes silently."""

    assert len(_grid()) >= 500


# --- how many turned up ---------------------------------------------------


def test_a_played_match_counts_the_seats_that_were_paid_for() -> None:
    assert turned_up(a_match(paid=4)) == 4


def test_a_no_show_is_one_person_and_the_count_says_three() -> None:
    """Sent as three and four, never as *four, now take one off*."""

    record = a_match(paid=4, no_show=True)
    assert turned_up(record) == 3


def test_a_match_short_two_seats_counts_the_two_that_paid() -> None:
    """The case that breaks *n − 1* on the phone: two people played, not three."""

    record = a_match(paid=2)
    assert turned_up(record) == 2
    assert situation(record, None, at(120)) is Situation.PLAYED_SHORT


def test_the_door_code_is_still_the_moment_a_full_match_becomes_ready() -> None:
    """A cross-check on the example above, so *ready* is not a coincidence."""

    record = a_match(paid=4, committed_at=at(-1440))
    assert door_code_at(record) == at(-15)
