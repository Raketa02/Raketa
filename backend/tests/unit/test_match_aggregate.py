"""What a match is: five kinds of stored fact, a version, and nothing derived.

Six claims, each of which is a different system if it changes.

1. **Nothing derived is stored.** How full the match is, whether a court is
   held, whether it has been played and the situation itself are computed from
   the record and the clock, every time (ADR-0034).
2. **Enrolment is a relationship**, not an object: a seat names a player or it
   does not, and one player holds at most one seat.
3. **`start` is mutable** and moving it is an ordinary write — every deadline
   moves with it, because none of the five is stored (ADR-0032).
4. **Commitment is a Crossing**: derivable once, then frozen, and it never
   un-happens when a fourth player leaves.
5. **A vacancy and the departure that caused it are independent**, so a hole
   carries no amount and refilling it changes nothing about a settlement
   (ADR-0033).
6. **The four cancellations are four different stories**, and the record is the
   explanation — which is what lets Matches keep no history at all.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.kernel import (
    HoldPolicy,
    MatchKind,
    PayModel,
    SeatShare,
    Situation,
    Sport,
    filled,
    grosze,
    held_unpaid,
    hours,
    instant,
    is_full,
    keeping_a_court,
    live_outcome,
    minutes,
    situation,
)
from app.modules.matches.domain.errors import (
    CourtAlreadyHeld,
    MatchAlreadySettled,
    MatchAlreadyStarted,
    MatchIsFull,
    MatchNotPlayed,
    MatchNotPrivate,
    NoCourtHeld,
    NoScoreOnTheTable,
    PlayerAlreadyHoldsASeat,
    ResultAlreadyAgreed,
    ResultWindowClosed,
    SeatAlreadyPaid,
    SeatNotFound,
    SeatNotTaken,
    StartMustBeInTheFuture,
)
from app.modules.matches.domain.events import SeatVacated
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.score import Score, SetScore

CLUB = uuid4()
CATEGORY = uuid4()

SHARE = SeatShare(grosze(3800))
POLICY = HoldPolicy(window=hours(24), join_cut=minutes(30))


def at(day: int, hour: int = 12, minute: int = 0):
    return instant(datetime(2026, 9, day, hour, minute, tzinfo=timezone.utc))


POSTED = at(1)
START = at(8, 18)


def leaves(match, player, *, when):
    """A departure quoted at whatever the record says it is worth right then.

    The quote is the caller's (ADR-0033), and this suite is not about it — a
    **stale** quote is `tests/unit/test_match_departures.py`'s subject. Read off
    the live record here, which is what the route will do.
    """

    return match.depart(player, quote=live_outcome(match.as_record(), when), at=when)


def a_match(**overrides):
    kwargs = dict(
        match_id=uuid4(),
        club_id=CLUB,
        category_id=CATEGORY,
        sport=Sport.PADEL,
        start=START,
        duration=hours(1),
        share=SHARE,
        policy=POLICY,
        at=POSTED,
    )
    kwargs.update(overrides)
    return Match.post(**kwargs)


def a_full_match(*, when=POSTED, **overrides):
    """Four players on, all paid — the shortest route to a complete match."""

    match = a_match(**overrides)
    match.pull_events()
    for _ in range(4):
        player = uuid4()
        match.take_seat(player, at=when)
        match.pay_seat(player, at=when)
    match.pull_events()
    return match


# --- 1 · nothing derived is stored -----------------------------------------


def test_a_fresh_match_has_every_seat_the_sport_is_sold_for_and_all_are_empty():
    match = a_match()

    assert len(match.seats) == 4
    assert [seat.index for seat in match.seats] == [0, 1, 2, 3]
    assert all(seat.is_free for seat in match.seats)
    assert filled(match.as_record()) == 0


def test_a_sport_sold_in_two_seats_gets_two():
    match = a_match(sport=Sport.SQUASH)

    assert len(match.seats) == 2


def test_how_full_it_is_is_counted_and_never_stored():
    """There is no `filled` on the record. The count is over the seats."""

    match = a_match()
    alice, bob = uuid4(), uuid4()
    match.take_seat(alice, at=POSTED)
    match.take_seat(bob, at=POSTED)
    match.pay_seat(alice, at=POSTED)

    record = match.as_record()
    assert filled(record) == 1
    assert held_unpaid(record) == 1
    assert not is_full(record)
    assert not hasattr(match, "filled")


def test_the_record_resolves_a_situation_with_no_further_read():
    """AC: *the kernel resolves a situation from the stored record*.

    The aggregate hands the kernel a `MatchRecord` and the kernel answers. No
    club is fetched, no reservation is looked up, nothing is rehydrated — which
    is the whole of ADR-0034's *"the busiest object in the product is the
    cheapest to read"*.
    """

    match = a_match()

    assert situation(match.as_record(), None, at(2)) is Situation.FORMING


def test_the_policy_travels_with_the_match_so_a_situation_needs_no_club():
    """The four hold-policy fields are Constitutive, copied at posting.

    ADR-0077 puts a value that must be honoured *as booked* on the match record
    rather than in a temporal query, and this is what that buys: the deadline a
    situation is resolved against is the match's own.
    """

    tight = a_match(policy=HoldPolicy(window=hours(48), join_cut=minutes(30)))

    assert tight.as_record().policy.window == hours(48)
    # 48 hours out, a 48-hour club is already past its commitment deadline.
    assert situation(tight.as_record(), None, at(7, 18)) is Situation.FORMING_LATE


# --- 2 · enrolment is a relationship ----------------------------------------


def test_a_seat_names_a_player_and_there_is_no_enrolment_object():
    match = a_match()
    alice = uuid4()

    seat = match.take_seat(alice, at=POSTED)

    assert seat.player_id == alice
    assert match.seat_of(alice) is seat
    assert seat.taken_at == POSTED


def test_taking_a_seat_is_not_paying_for_it():
    match = a_match()
    alice = uuid4()

    seat = match.take_seat(alice, at=POSTED)

    assert seat.is_taken
    assert not seat.paid
    assert held_unpaid(match.as_record()) == 1
    assert filled(match.as_record()) == 0


def test_one_player_holds_at_most_one_seat():
    match = a_match()
    alice = uuid4()
    match.take_seat(alice, at=POSTED)

    with pytest.raises(PlayerAlreadyHoldsASeat):
        match.take_seat(alice, at=POSTED)


def test_a_full_match_refuses_a_fifth_player():
    match = a_full_match()

    with pytest.raises(MatchIsFull):
        match.take_seat(uuid4(), at=POSTED)


def test_paying_twice_is_refused():
    match = a_match()
    alice = uuid4()
    match.take_seat(alice, at=POSTED)
    match.pay_seat(alice, at=POSTED)

    with pytest.raises(SeatAlreadyPaid):
        match.pay_seat(alice, at=POSTED)


def test_paying_for_a_seat_nobody_holds_is_refused():
    match = a_match()

    with pytest.raises(SeatNotTaken):
        match.pay_seat(uuid4(), at=POSTED)


def test_a_seat_index_the_match_does_not_have_is_refused():
    match = a_match()

    with pytest.raises(SeatNotFound):
        match.seat_at(9)


def test_nobody_joins_a_match_that_has_started():
    match = a_match()

    with pytest.raises(MatchAlreadyStarted):
        match.take_seat(uuid4(), at=START)


# --- 3 · start is mutable ---------------------------------------------------


def test_moving_the_start_moves_every_deadline_with_it():
    """None of the five deadlines is stored, so there is nothing to recompute."""

    match = a_match()
    before = match.as_record()

    match.move_start(at(9, 18), at=POSTED)

    assert match.start == at(9, 18)
    assert match.as_record().start != before.start


def test_a_match_cannot_be_moved_into_the_past():
    match = a_match()

    with pytest.raises(StartMustBeInTheFuture):
        match.move_start(at(1, 6), at=POSTED)


def test_a_match_that_has_started_cannot_be_moved():
    match = a_match()

    with pytest.raises(MatchAlreadyStarted):
        match.move_start(at(9, 18), at=START)


def test_moving_a_match_to_the_hour_it_already_has_changes_nothing():
    match = a_match()
    match.pull_events()

    match.move_start(START, at=POSTED)

    assert match.pull_events() == []


# --- 4 · commitment is a Crossing -------------------------------------------


def test_a_match_that_fills_before_its_deadline_has_not_committed():
    match = a_full_match(when=POSTED)

    assert match.committed_at is None


def test_a_match_that_fills_past_its_deadline_commits_on_the_spot():
    """`commit` is `start - 24h` here, so filling at T-6h commits at once."""

    late = at(8, 12)
    match = a_full_match(when=late)

    assert match.committed_at == late


def test_commitment_survives_the_fourth_player_leaving():
    """Derivable **once**, then frozen: re-deriving would release three people."""

    late = at(8, 12)
    match = a_full_match(when=late)
    leaver = match.seats[0].player_id

    leaves(match, leaver, when=at(8, 13))

    assert match.committed_at == late
    assert not is_full(match.as_record())


def test_committing_is_idempotent():
    late = at(8, 12)
    match = a_full_match(when=late)

    assert match.commit_if_due(at=at(8, 14)) is False
    assert match.committed_at == late


def test_a_match_that_is_not_full_does_not_commit_at_its_deadline():
    match = a_match()
    match.take_seat(uuid4(), at=POSTED)

    assert match.commit_if_due(at=at(8, 12)) is False


# --- 5 · a vacancy is its own fact ------------------------------------------


def test_leaving_a_seat_opens_a_hole_that_carries_no_amount():
    match = a_full_match(when=at(8, 12))
    leaver = match.seats[1].player_id

    departure = leaves(match, leaver, when=at(8, 13))
    vacancy = match.vacancies[-1]

    assert departure.seat_index == vacancy.seat_index
    assert vacancy.is_open
    assert vacancy.seat_index == 1
    assert vacancy.vacated_at == at(8, 13)
    assert not hasattr(vacancy, "amount")
    assert not hasattr(vacancy, "outcome")


def test_a_filler_closes_the_oldest_hole_and_the_newest_still_describes_the_match():
    """Two departures and one filler is a match that lost somebody recently."""

    match = a_full_match(when=at(1, 12))
    first, second = match.seats[0].player_id, match.seats[1].player_id
    leaves(match, first, when=at(2))
    leaves(match, second, when=at(6))

    match.take_seat(uuid4(), at=at(6, 12, 30))

    still_open = match.open_vacancies
    assert len(still_open) == 1
    assert still_open[0].vacated_at == at(6)


def test_a_refilled_match_carries_no_open_hole_at_all():
    """The defect the prototype shipped: a flag set and never cleared."""

    match = a_full_match(when=at(1, 12))
    leaver = match.seats[0].player_id
    leaves(match, leaver, when=at(2))

    match.take_seat(uuid4(), at=at(3))

    assert match.open_vacancies == []
    assert match.as_record().open_vacancies == ()


def test_a_leaver_who_had_paid_is_distinguishable_from_one_who_had_not():
    match = a_match()
    paid, held = uuid4(), uuid4()
    match.take_seat(paid, at=POSTED)
    match.pay_seat(paid, at=POSTED)
    match.take_seat(held, at=POSTED)
    match.pull_events()

    leaves(match, paid, when=at(2))
    leaves(match, held, when=at(2))

    vacated = [
        event for event in match.pull_events() if isinstance(event, SeatVacated)
    ]
    assert [event.was_paid for event in vacated] == [True, False]


def test_leaving_a_seat_nobody_holds_is_refused():
    match = a_match()

    with pytest.raises(SeatNotTaken):
        leaves(match, uuid4(), when=POSTED)


# --- 6 · the four cancellations are four stories ----------------------------


@pytest.mark.parametrize(
    "cancel, flag",
    [
        ("cancel_by_club", "club_cancelled"),
        ("cancel_for_weather", "weather"),
        ("settle_incomplete_cancellation", "form_cancelled"),
        ("settle_checkpoint_cancellation", "checkpoint_cancelled"),
    ],
)
def test_each_cancellation_sets_its_own_flag_and_ends_the_match(cancel, flag):
    match = a_match()

    getattr(match, cancel)(at=at(2))

    assert getattr(match, flag) is True
    assert match.is_settled


def test_the_four_cancellations_are_four_different_flags():
    """One flag with a reason column would make *why did this cancel* a lookup.

    The record **is** the explanation, which is the sentence that lets this
    context keep no history.
    """

    flags = set()
    for cancel in (
        "cancel_by_club",
        "cancel_for_weather",
        "settle_incomplete_cancellation",
        "settle_checkpoint_cancellation",
    ):
        match = a_match()
        getattr(match, cancel)(at=at(2))
        flags.add(
            (
                match.club_cancelled,
                match.weather,
                match.form_cancelled,
                match.checkpoint_cancelled,
            )
        )

    assert len(flags) == 4


def test_losing_inventory_ends_the_match_too():
    match = a_match()

    match.lose_inventory(at=at(2))

    assert match.is_settled
    assert situation(match.as_record(), None, at(2)) is Situation.INVENTORY_LOST


def test_a_settled_match_refuses_every_further_write():
    match = a_match()
    match.cancel_by_club(at=at(2))

    for call in (
        lambda: match.take_seat(uuid4(), at=at(3)),
        lambda: match.move_start(at(9, 18), at=at(3)),
        lambda: match.hold_court(at=at(3)),
        lambda: match.lock_court(at=at(3)),
        lambda: match.cancel_for_weather(at=at(3)),
        lambda: match.record_no_show(at=at(9)),
    ):
        with pytest.raises(MatchAlreadySettled):
            call()


def test_a_played_match_is_not_settled():
    """`needsResult → confirmResult → completed` still moves."""

    match = a_full_match(when=at(8, 12))

    assert not match.is_settled
    assert situation(match.as_record(), None, at(9)) is Situation.NEEDS_RESULT


# --- the court hold: the match's own fact, and never which court ------------


def test_holding_a_court_records_since_when_and_names_no_court():
    match = a_match()

    match.hold_court(at=at(2))

    assert match.held_since == at(2)
    assert not hasattr(match, "court_id")
    assert not hasattr(match, "reservation_id")


def test_a_second_hold_is_refused_and_a_release_needs_one():
    match = a_match()

    with pytest.raises(NoCourtHeld):
        match.release_court(at=at(2))

    match.hold_court(at=at(2))
    with pytest.raises(CourtAlreadyHeld):
        match.hold_court(at=at(3))


def test_releasing_a_court_keeps_the_receipt_and_the_age_it_was_reclaimed_on():
    """The court has gone; the hold's age has not.

    The club's cap is measured from `held_since`, so clearing it here would reset
    the clock that had just fired — the ladder would grant again on the next look
    and reclaim again a cap later, for ever. `keeping_a_court` is what says a
    court has gone back, and it reads the two fields together.
    """

    match = a_match()
    match.hold_court(at=at(2))

    match.release_court(at=at(3))

    assert match.held_since == at(2)
    assert match.released_at == at(3)
    assert not keeping_a_court(match.as_record())


def test_a_court_can_be_held_again_after_it_was_given_back():
    """Staleness is never latched, so a re-grant is ordinary and not a mistake."""

    match = a_match()
    match.hold_court(at=at(2))
    match.release_court(at=at(3))

    match.hold_court(at=at(4))

    assert keeping_a_court(match.as_record())
    assert match.held_since == at(4)
    assert match.released_at is None


# --- private courts ---------------------------------------------------------


def test_only_a_private_court_can_open_seats():
    match = a_match()

    with pytest.raises(MatchNotPrivate):
        match.open_seats_to_the_marketplace(2, at=POSTED)


def test_a_private_court_with_no_seats_open_is_reserved_to_its_group():
    match = a_match(kind=MatchKind.PRIVATE, pay_model=PayModel.SOLO)

    assert situation(match.as_record(), None, at(2)) is Situation.PRIVATE_RESERVED


def test_opening_seats_puts_the_private_court_on_the_marketplace():
    """`privateOpen` — a different sentence from a court still reserved."""

    match = a_match(kind=MatchKind.PRIVATE)
    match.pull_events()

    match.open_seats_to_the_marketplace(2, at=POSTED)

    assert match.open_seats == 2
    assert situation(match.as_record(), None, at(2)) is Situation.PRIVATE_OPEN


def test_opening_the_seats_that_are_already_open_changes_nothing():
    match = a_match(kind=MatchKind.PRIVATE, open_seats=2)
    match.pull_events()

    match.open_seats_to_the_marketplace(2, at=POSTED)

    assert match.pull_events() == []


# --- the score: four facts, never a list ------------------------------------

SCORE = Score((SetScore(6, 4), SetScore(7, 6)))


def test_a_score_cannot_be_entered_before_the_match_is_played():
    match = a_full_match(when=at(8, 12))

    with pytest.raises(MatchNotPlayed):
        match.propose_score(SCORE, by=uuid4(), at=at(8, 18))


def test_a_proposal_records_the_score_who_put_it_there_and_a_count():
    match = a_full_match(when=at(8, 12))
    alice = match.seats[0].player_id

    match.propose_score(SCORE, by=alice, at=at(8, 20))

    assert match.score == SCORE
    assert match.score_by == alice
    assert match.proposals == 1
    assert not match.result_agreed
    assert situation(match.as_record(), None, at(8, 21)) is Situation.CONFIRM_RESULT


def test_a_counter_replaces_the_score_and_counts_up():
    """A count, not a sequence — the conversation is in the announcements."""

    match = a_full_match(when=at(8, 12))
    alice, bob = match.seats[0].player_id, match.seats[2].player_id
    match.propose_score(SCORE, by=alice, at=at(8, 20))

    countered = Score((SetScore(4, 6), SetScore(6, 7)))
    match.propose_score(countered, by=bob, at=at(8, 21))

    assert match.score == countered
    assert match.score_by == bob
    assert match.proposals == 2
    assert not hasattr(match, "proposal_history")


def test_agreeing_settles_it_and_a_second_agreement_is_refused():
    match = a_full_match(when=at(8, 12))
    match.propose_score(SCORE, by=match.seats[0].player_id, at=at(8, 20))

    match.agree_result(at=at(8, 20, 25))

    assert match.result_agreed
    assert situation(match.as_record(), None, at(8, 20, 26)) is Situation.COMPLETED
    with pytest.raises(ResultAlreadyAgreed):
        match.agree_result(at=at(8, 20, 30))


def test_agreeing_with_nothing_on_the_table_is_refused():
    match = a_full_match(when=at(8, 12))

    with pytest.raises(NoScoreOnTheTable):
        match.agree_result(at=at(8, 20))


def test_a_score_is_refused_once_the_twenty_four_hours_are_up():
    """Past `result_window` the ladder answers `playedNoScore` (ADR-0048/0049)."""

    match = a_full_match(when=at(8, 12))

    with pytest.raises(ResultWindowClosed):
        match.propose_score(SCORE, by=match.seats[0].player_id, at=at(9, 20))

    assert situation(match.as_record(), None, at(9, 20)) is Situation.PLAYED_NO_SCORE


def test_a_settled_score_cannot_be_reopened():
    match = a_full_match(when=at(8, 12))
    match.propose_score(SCORE, by=match.seats[0].player_id, at=at(8, 20))
    match.agree_result(at=at(8, 20, 25))

    with pytest.raises(ResultAlreadyAgreed):
        match.propose_score(SCORE, by=match.seats[1].player_id, at=at(8, 20, 30))


# --- the shape refuses what it cannot mean ----------------------------------


def test_a_paid_seat_with_nobody_on_it_is_refused_at_the_door():
    from app.modules.matches.domain.seat import Seat

    with pytest.raises(ValueError):
        Seat(index=0, player_id=None, paid=True)


def test_a_match_whose_seats_disagree_with_its_sport_is_refused():
    from app.modules.matches.domain.seat import Seat

    with pytest.raises(ValueError):
        Match(
            id=uuid4(),
            club_id=CLUB,
            category_id=CATEGORY,
            sport=Sport.PADEL,
            duration=hours(1),
            share=SHARE,
            counted=True,
            created=POSTED,
            kind=MatchKind.OPEN,
            pay_model=PayModel.SPLIT,
            policy=POLICY,
            start=START,
            seats=[Seat(index=0), Seat(index=1)],
        )


def test_a_score_with_no_sets_is_refused():
    with pytest.raises(ValueError):
        Score(())


def test_a_set_with_a_negative_side_is_refused():
    with pytest.raises(ValueError):
        SetScore(-1, 6)
