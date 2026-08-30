"""The Challenge: one thing containing everybody, whose standing is never stored.

Five claims carry this module, and each of them is a decision from
[#221](https://github.com/Raketa02/Raketa/issues/221) rather than an
implementation detail:

**One aggregate per game, with seats inside it.** A doubles send is one Challenge
containing four, and *which side is short* is a fact it holds rather than one a
reader counts — so an empty seat is a seat, and the court is checked against the
sport's own fixed list.

**The organiser's seat is accepted from birth**, which is what makes *every seat
accepted* the whole of the completion rule, with no special case for singles.

**The standing is derived from the seats and the clock.** Nothing stores it, so
the same aggregate read at two instants answers differently with nothing having
happened in between — which is the whole gap between a deadline passing and a
sweep noticing, answered correctly without the sweep.

**A lapse is not a decline.** They do the same thing to the line-up and they are
different events, because *answers challenges* is a Strand over challenges that
got an answer inside their window and is unmeasurable if silence is filed as
judgement.

**Membership grows one acceptance at a time.** One event per accept and nothing
that says *the game is now on*: a chat built later subscribes to those and grows
its roster, and *Line-up incomplete* is not a waiting room.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import (
    AChallengeNeedsAnInvitee,
    AnAcceptedPlayerMayNotBeRemoved,
    CannotChallengeYourself,
    NobodyIsAskedTwice,
    NobodyNewToInvite,
    NotYourSeat,
    OnePersonToASeat,
    TheAnswerWindowHasPassed,
    TheChallengeIsOver,
    TheCourtIsNotThisSports,
    TheOrganiserHoldsASeat,
    TheSeatIsAlreadyAnswered,
)
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatsInvited,
)
from app.modules.challenges.domain.origins import SentFromSearch, SentOutsideASearch
from app.modules.challenges.domain.seats import SeatAnswer, SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid

ORGANISER = new_uuid()
ALICE = new_uuid()
BOB = new_uuid()
CAROL = new_uuid()
STRANGER = new_uuid()
SEARCH = new_uuid()


def at(hours: int = 0) -> Instant:
    """An instant, `hours` after the moment every send in this module is made."""

    return instant(
        datetime(2026, 8, 30, 12, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


SENT_AT = at(0)
#: One minute inside every window opened at the send, and one minute outside it.
INSIDE = at(23)
OUTSIDE = instant(SENT_AT + ANSWER_WINDOW + timedelta(minutes=1))


def invited(player_id, side: Side, position: int = 1) -> SeatPlan:
    return SeatPlan(
        side=side,
        player_id=player_id,
        origin=SentFromSearch(search_id=SEARCH, position=position),
    )


def padel_court(*, invitees=(ALICE, BOB, CAROL)) -> tuple[SeatPlan, ...]:
    """The organiser on side A, then whoever is filling the other three seats."""

    filled = list(invitees) + [None, None, None]
    return (
        SeatPlan(side=Side.A, player_id=ORGANISER),
        invited(filled[0], Side.A, 1) if filled[0] else SeatPlan(side=Side.A),
        invited(filled[1], Side.B, 2) if filled[1] else SeatPlan(side=Side.B),
        invited(filled[2], Side.B, 3) if filled[2] else SeatPlan(side=Side.B),
    )


def a_padel_challenge(
    *, invitees=(ALICE, BOB, CAROL), occurred_at=SENT_AT
) -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=ORGANISER,
        arrangement=padel_court(invitees=invitees),
        occurred_at=occurred_at,
    )


def a_tennis_challenge(*, occurred_at=SENT_AT) -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        mode=SearchMode.COMPETITIVE,
        window=Window.TODAY,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            invited(ALICE, Side.B),
        ),
        occurred_at=occurred_at,
    )


def replayed(challenge: Challenge) -> Challenge:
    return Challenge.from_history(challenge.pull_events())


# ---------------------------------------------------------------------------
# The court
# ---------------------------------------------------------------------------


def test_a_padel_court_is_four_seats_two_a_side():
    """`2 x seats_per_side(sport)`, and the shape is the sport's own."""

    challenge = a_padel_challenge()

    assert [seat.side for seat in challenge.seats] == [
        Side.A,
        Side.A,
        Side.B,
        Side.B,
    ]


def test_a_singles_court_is_one_seat_a_side():
    challenge = a_tennis_challenge()

    assert [seat.side for seat in challenge.seats] == [Side.A, Side.B]


def test_an_empty_seat_is_a_seat_and_says_which_side_is_short():
    """Absence would push *which side is short* onto a reader that has to count."""

    challenge = a_padel_challenge(invitees=(ALICE,))

    empty = [seat for seat in challenge.seats if seat.player_id is None]
    assert [seat.side for seat in empty] == [Side.B, Side.B]


def test_a_court_that_is_not_the_sports_is_refused():
    with pytest.raises(TheCourtIsNotThisSports):
        Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.PADEL,
            mode=SearchMode.FOR_FUN,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ALICE, Side.B),
            ),
            occurred_at=SENT_AT,
        )


def test_two_sends_between_the_same_people_are_two_challenges():
    """Identity is its own, not the pair's — the same people may be asked again."""

    first = a_tennis_challenge()
    second = a_tennis_challenge()

    assert first.id != second.id


# ---------------------------------------------------------------------------
# The organiser, and who is on the court
# ---------------------------------------------------------------------------


def test_the_organisers_seat_is_accepted_from_birth():
    """They are the one proposing; nobody asks them whether they want to play."""

    challenge = a_padel_challenge()

    organiser_seat = next(seat for seat in challenge.seats if seat.holds(ORGANISER))
    assert organiser_seat.answer is SeatAnswer.ACCEPTED
    assert organiser_seat.answer_by is None
    assert organiser_seat.origin is None


def test_a_challenge_with_no_invitee_is_refused():
    """The organiser alone is indistinguishable from never having sent."""

    with pytest.raises(AChallengeNeedsAnInvitee):
        a_padel_challenge(invitees=())


def test_the_organiser_cannot_be_among_their_own_invitees():
    with pytest.raises(CannotChallengeYourself):
        Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.TENNIS,
            mode=None,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ORGANISER, Side.B),
            ),
            occurred_at=SENT_AT,
        )


def test_a_send_the_organiser_is_not_in_is_refused():
    with pytest.raises(TheOrganiserHoldsASeat):
        Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.TENNIS,
            mode=None,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(invited(ALICE, Side.A), invited(BOB, Side.B)),
            occurred_at=SENT_AT,
        )


def test_one_person_holds_one_seat():
    with pytest.raises(OnePersonToASeat):
        a_padel_challenge(invitees=(ALICE, ALICE, BOB))


def test_an_invitation_that_cannot_say_where_it_came_from_cannot_be_built():
    """No default: a seat with no origin is a denominator that would lie."""

    with pytest.raises(InvariantViolated):
        Challenge.sent(
            challenge_id=new_uuid(),
            sport=Sport.TENNIS,
            mode=None,
            window=Window.ANY,
            organiser_id=ORGANISER,
            arrangement=(
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.B, player_id=ALICE),
            ),
            occurred_at=SENT_AT,
        )


def test_the_origin_is_per_seat_and_not_per_challenge():
    """Three invitees from one search at three positions, each kept."""

    challenge = a_padel_challenge()

    positions = [
        seat.origin.position
        for seat in challenge.seats
        if isinstance(seat.origin, SentFromSearch)
    ]
    assert positions == [1, 2, 3]


# ---------------------------------------------------------------------------
# The arrangement, and the window
# ---------------------------------------------------------------------------


def test_the_arrangement_the_organiser_built_is_recorded_with_the_challenge():
    """Sides only — the forecast follows from them and a stored copy goes stale."""

    challenge = a_padel_challenge()

    assert replayed(challenge).seats == challenge.seats


def test_the_window_is_stamped_at_the_send_and_replays_as_itself():
    challenge = a_padel_challenge()

    assert replayed(challenge).window is Window.WEEKEND


def test_a_mode_less_surface_sends_without_one():
    """The deck has no mode, and a null is the honest record of that."""

    challenge = Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        mode=None,
        window=Window.ANY,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.B, player_id=ALICE, origin=SentOutsideASearch()),
        ),
        occurred_at=SENT_AT,
    )

    assert replayed(challenge).mode is None


def test_every_invited_seat_is_dated_a_day_from_the_send():
    challenge = a_padel_challenge()

    invited_seats = [seat for seat in challenge.seats if seat.answer_by is not None]
    assert len(invited_seats) == 3
    assert all(seat.answer_by == SENT_AT + ANSWER_WINDOW for seat in invited_seats)


def test_a_seat_filled_later_starts_its_own_day():
    """AC-153's later invitees cannot inherit a deadline they were not part of."""

    challenge = a_padel_challenge(invitees=(ALICE,))
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(BOB, Side.B, 7),
            invited(CAROL, Side.B, 8),
        ),
        occurred_at=at(10),
    )

    late = next(seat for seat in challenge.seats if seat.holds(BOB))
    assert late.answer_by == at(10) + ANSWER_WINDOW
    assert late.answer_by != SENT_AT + ANSWER_WINDOW


# ---------------------------------------------------------------------------
# The standing — derived from the seats and the clock
# ---------------------------------------------------------------------------


def test_a_fresh_send_is_awaiting_answers():
    assert a_padel_challenge().standing_at(INSIDE) is Standing.AWAITING_ANSWERS


def test_a_challenge_is_on_only_when_the_last_seat_accepts():
    challenge = a_padel_challenge()

    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    assert challenge.standing_at(INSIDE) is Standing.AWAITING_ANSWERS

    challenge.accept(CAROL, occurred_at=at(3))
    assert challenge.standing_at(INSIDE) is Standing.ON


def test_a_singles_accept_is_on_with_no_special_case():
    """The organiser's seat being accepted from birth is what buys this."""

    challenge = a_tennis_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    assert challenge.standing_at(INSIDE) is Standing.ON


def test_a_decline_reopens_one_seat_and_disturbs_nothing_else():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))

    challenge.decline(CAROL, occurred_at=at(3))

    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert next(seat for seat in challenge.seats if seat.holds(ALICE)).is_accepted()
    assert next(seat for seat in challenge.seats if seat.holds(BOB)).is_accepted()
    assert next(seat for seat in challenge.seats if seat.holds(CAROL)).is_open_at(
        INSIDE
    )


def test_awaiting_outranks_line_up_incomplete():
    """A half-built court is not re-entered into the builder mid-decision."""

    challenge = a_padel_challenge(invitees=(ALICE, BOB))

    assert challenge.standing_at(INSIDE) is Standing.AWAITING_ANSWERS


def test_a_one_to_one_padel_send_reads_incomplete_once_it_is_answered():
    """*Accepting it produces Line-up incomplete* — the builder's re-entry state."""

    challenge = a_padel_challenge(invitees=(ALICE,))
    challenge.accept(ALICE, occurred_at=at(1))

    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE


def test_a_singles_decline_ends_the_challenge():
    """Nobody is left to keep faith with; re-offering is a *new* challenge."""

    challenge = a_tennis_challenge()
    challenge.decline(ALICE, occurred_at=at(1))

    assert challenge.standing_at(INSIDE) is Standing.DECLINED
    assert not challenge.is_open_at(INSIDE)


def test_a_singles_silence_ends_it_as_a_lapse_and_not_as_a_decline():
    challenge = a_tennis_challenge()

    assert challenge.standing_at(OUTSIDE) is Standing.LAPSED


def test_a_no_outranks_silence_in_how_it_ended():
    """Which clock ran out first is an accident; somebody's judgement is not."""

    challenge = a_padel_challenge(invitees=(ALICE, BOB))
    challenge.decline(ALICE, occurred_at=at(1))

    assert challenge.standing_at(OUTSIDE) is Standing.DECLINED


def test_a_lapse_among_accepted_seats_reads_line_up_incomplete():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))

    assert challenge.standing_at(OUTSIDE) is Standing.LINE_UP_INCOMPLETE


def test_a_seat_past_its_window_reads_lapsed_with_no_sweep_having_run():
    """Correctness does not depend on a loop running."""

    challenge = a_padel_challenge()

    seat = next(seat for seat in challenge.seats if seat.holds(ALICE))
    assert not seat.is_lapsed_at(INSIDE)
    assert seat.is_lapsed_at(OUTSIDE)


def test_the_standing_moves_with_the_clock_alone():
    """Two reads of one unchanged aggregate, and they disagree. That is the point."""

    challenge = a_tennis_challenge()

    assert challenge.standing_at(INSIDE) is Standing.AWAITING_ANSWERS
    assert challenge.standing_at(OUTSIDE) is Standing.LAPSED


def test_a_departed_seat_makes_that_person_a_stranger_again():
    """What the one-open-challenge-per-pair rule reads, and when it releases."""

    challenge = a_padel_challenge()

    assert challenge.players_in_it_at(INSIDE) == frozenset(
        {ORGANISER, ALICE, BOB, CAROL}
    )
    challenge.decline(CAROL, occurred_at=at(1))
    assert CAROL not in challenge.players_in_it_at(INSIDE)


def test_an_ended_challenge_holds_nobody():
    challenge = a_tennis_challenge()
    challenge.decline(ALICE, occurred_at=at(1))

    assert challenge.players_in_it_at(INSIDE) == frozenset()


# ---------------------------------------------------------------------------
# Answering
# ---------------------------------------------------------------------------


def test_answering_a_seat_you_do_not_hold_is_refused():
    challenge = a_tennis_challenge()

    with pytest.raises(NotYourSeat):
        challenge.accept(STRANGER, occurred_at=at(1))


def test_answering_twice_is_refused():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    with pytest.raises(TheSeatIsAlreadyAnswered):
        challenge.decline(ALICE, occurred_at=at(2))


def test_a_late_answer_is_refused():
    """The seat already reads as lapsed and may have been offered to somebody."""

    challenge = a_padel_challenge()

    with pytest.raises(TheAnswerWindowHasPassed):
        challenge.accept(ALICE, occurred_at=OUTSIDE)


def test_a_late_answer_is_refused_the_same_either_side_of_a_sweep():
    """Correctness does not depend on the loop running, and neither does the code
    on the wire: refusing with *you already answered* after a sweep and *your
    window has passed* before one would be the same act refused two ways."""

    unswept = a_padel_challenge()
    swept = a_padel_challenge()
    swept.lapse(now=OUTSIDE)

    with pytest.raises(TheAnswerWindowHasPassed):
        unswept.accept(ALICE, occurred_at=OUTSIDE)
    with pytest.raises(TheAnswerWindowHasPassed):
        swept.accept(ALICE, occurred_at=OUTSIDE)


def test_one_event_per_acceptance_and_nothing_says_the_game_is_on():
    """A chat opens on the first accept and grows with each one."""

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    challenge.accept(CAROL, occurred_at=at(3))

    events = challenge.pull_events()
    assert [type(event) for event in events] == [
        ChallengeSent,
        SeatAccepted,
        SeatAccepted,
        SeatAccepted,
    ]


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


def test_the_sweep_records_a_lapse_and_never_a_decline():
    challenge = a_padel_challenge()
    challenge.pull_events()

    challenge.lapse(now=OUTSIDE)

    events = challenge.pull_events()
    assert {type(event) for event in events} == {SeatLapsed}
    assert {event.player_id for event in events} == {ALICE, BOB, CAROL}


def test_the_sweep_says_how_many_seats_it_wrote_down():
    """The one thing about a sweep that cannot be recovered afterwards.

    The seats read the same either side of it, so a caller counting by comparing
    before and after would find nothing to compare — and the figure is what
    gives *answers challenges* a denominator.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    assert challenge.lapse(now=INSIDE) == 0
    assert challenge.lapse(now=OUTSIDE) == 2
    assert challenge.lapse(now=OUTSIDE) == 0


def test_the_sweep_leaves_an_answered_seat_alone():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))
    challenge.pull_events()

    challenge.lapse(now=OUTSIDE)

    assert [event.player_id for event in challenge.pull_events()] == [CAROL]


def test_a_second_sweep_appends_nothing():
    """Idempotent by the aggregate no-op'ing an answered seat, not by a lock."""

    challenge = a_padel_challenge()
    challenge.lapse(now=OUTSIDE)
    challenge.pull_events()

    challenge.lapse(now=OUTSIDE)

    assert challenge.pull_events() == []


def test_the_sweep_changes_no_reading():
    """It buys the record, not correctness — the standing was already right."""

    before = a_padel_challenge()
    after = a_padel_challenge()
    after.lapse(now=OUTSIDE)

    assert before.standing_at(OUTSIDE) == after.standing_at(OUTSIDE)
    assert before.players_in_it_at(OUTSIDE) == after.players_in_it_at(OUTSIDE)


# ---------------------------------------------------------------------------
# Completing a half-built game
# ---------------------------------------------------------------------------


def a_half_built_game() -> Challenge:
    challenge = a_padel_challenge(invitees=(ALICE,))
    challenge.accept(ALICE, occurred_at=at(1))
    return challenge


def test_only_the_newly_seated_are_invited():
    challenge = a_half_built_game()

    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(BOB, Side.B, 7),
            invited(CAROL, Side.B, 8),
        ),
        occurred_at=at(10),
    )

    invitation = next(
        event for event in challenge.pull_events() if isinstance(event, SeatsInvited)
    )
    assert set(invitation.newly_invited) == {str(BOB), str(CAROL)}


def test_an_accepted_player_may_cross_the_net_and_keep_their_acceptance():
    """An acceptance is to the game, not to the side."""

    challenge = a_half_built_game()

    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            invited(BOB, Side.A, 7),
            SeatPlan(side=Side.B, player_id=ALICE),
            invited(CAROL, Side.B, 8),
        ),
        occurred_at=at(10),
    )

    alice = next(seat for seat in challenge.seats if seat.holds(ALICE))
    assert alice.side is Side.B
    assert alice.is_accepted()


def test_an_accepted_player_may_not_be_removed():
    challenge = a_half_built_game()

    with pytest.raises(AnAcceptedPlayerMayNotBeRemoved):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(BOB, Side.A, 7),
                invited(CAROL, Side.B, 8),
                SeatPlan(side=Side.B),
            ),
            occurred_at=at(10),
        )


def test_a_send_with_nobody_new_is_refused():
    """Which is why a rearrangement on its own is not a thing this context has."""

    challenge = a_half_built_game()

    with pytest.raises(NobodyNewToInvite):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ALICE),
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.B),
                SeatPlan(side=Side.B),
            ),
            occurred_at=at(10),
        )


def test_once_the_court_is_full_the_sides_are_frozen():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    challenge.accept(CAROL, occurred_at=at(3))

    with pytest.raises(NobodyNewToInvite):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=BOB),
                SeatPlan(side=Side.B, player_id=ALICE),
                SeatPlan(side=Side.B, player_id=CAROL),
            ),
            occurred_at=at(4),
        )


def test_a_challenge_that_is_over_takes_no_more_invitations():
    challenge = a_padel_challenge(invitees=(ALICE,))
    challenge.decline(ALICE, occurred_at=at(1))

    with pytest.raises(TheChallengeIsOver):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(BOB, Side.A, 7),
                invited(CAROL, Side.B, 8),
                SeatPlan(side=Side.B),
            ),
            occurred_at=at(2),
        )


def test_a_reopened_seat_can_be_offered_to_somebody_else():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    challenge.decline(CAROL, occurred_at=at(3))

    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            SeatPlan(side=Side.B, player_id=BOB),
            invited(STRANGER, Side.B, 9),
        ),
        occurred_at=at(4),
    )

    assert challenge.standing_at(at(5)) is Standing.AWAITING_ANSWERS
    assert CAROL not in challenge.players_in_it_at(at(5))
    assert STRANGER in challenge.players_in_it_at(at(5))


def test_nobody_is_asked_twice():
    """A reopened seat goes to somebody new, never back to the person who left.

    The seats alone cannot enforce it — a re-seated position forgets who left it
    — so the aggregate remembers everybody who has ever answered.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    challenge.decline(CAROL, occurred_at=at(3))

    with pytest.raises(NobodyIsAskedTwice):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=ALICE),
                SeatPlan(side=Side.B, player_id=BOB),
                invited(CAROL, Side.B, 9),
            ),
            occurred_at=at(4),
        )


def test_somebody_who_lapsed_is_not_asked_again_either():
    """A second lapse from one person on one challenge would count twice in the
    denominator *answers challenges* is supposed to have."""

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    challenge.lapse(now=OUTSIDE)

    with pytest.raises(NobodyIsAskedTwice):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=ALICE),
                SeatPlan(side=Side.B, player_id=BOB),
                invited(CAROL, Side.B, 9),
            ),
            occurred_at=OUTSIDE,
        )


def test_a_plan_may_not_carry_an_invitation_for_somebody_already_in():
    """An origin means *this seat is being asked now*, and they are not."""

    challenge = a_half_built_game()

    with pytest.raises(InvariantViolated):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(ALICE, Side.A, 7),
                invited(BOB, Side.B, 8),
                invited(CAROL, Side.B, 9),
            ),
            occurred_at=at(10),
        )


# ---------------------------------------------------------------------------
# Born from a mutual yes
# ---------------------------------------------------------------------------


def a_mutual(sport: Sport = Sport.TENNIS) -> Challenge:
    return Challenge.opened_from_mutual_interest(
        challenge_id=new_uuid(),
        sport=sport,
        organiser_id=ORGANISER,
        other_player_id=ALICE,
        occurred_at=SENT_AT,
    )


def test_a_mutual_yes_opens_a_challenge_born_accepted_with_no_deadline():
    """A nullable `answer_by` is how a later reader invents one that never was."""

    challenge = a_mutual()

    assert all(seat.answer_by is None for seat in challenge.seats)
    assert all(seat.is_accepted() for seat in challenge.seats)
    assert challenge.standing_at(OUTSIDE) is Standing.ON


def test_a_mutual_carries_no_mode_and_no_window():
    """Nobody picked a kind of evening and no grid was proposed from."""

    challenge = replayed(a_mutual())

    assert challenge.mode is None
    assert challenge.window is None


def test_a_one_to_one_padel_challenge_is_half_a_game():
    challenge = a_mutual(Sport.PADEL)

    assert [seat.side for seat in challenge.seats if seat.player_id] == [
        Side.A,
        Side.A,
    ]
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE


def test_a_mutual_with_yourself_is_refused():
    with pytest.raises(CannotChallengeYourself):
        Challenge.opened_from_mutual_interest(
            challenge_id=new_uuid(),
            sport=Sport.TENNIS,
            organiser_id=ORGANISER,
            other_player_id=ORGANISER,
            occurred_at=SENT_AT,
        )


def test_a_mutual_padel_game_can_be_completed_from_the_builder():
    challenge = a_mutual(Sport.PADEL)

    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(BOB, Side.B, 1),
            invited(CAROL, Side.B, 2),
        ),
        occurred_at=at(48),
    )

    assert challenge.standing_at(at(49)) is Standing.AWAITING_ANSWERS


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        a_padel_challenge,
        a_tennis_challenge,
        lambda: a_mutual(Sport.PADEL),
    ],
    ids=["padel", "tennis", "mutual"],
)
def test_a_challenge_replays_into_itself(build):
    challenge = build()

    assert replayed(challenge) == challenge


def test_a_whole_life_replays_into_itself():
    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))
    challenge.lapse(now=OUTSIDE)
    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(STRANGER, Side.B, 7),
            invited(new_uuid(), Side.B, 8),
        ),
        occurred_at=OUTSIDE,
    )

    assert replayed(challenge) == challenge


def test_the_opening_events_are_the_only_two_that_open_a_stream():
    """Six events, and the two that can start a challenge are named."""

    assert isinstance(a_padel_challenge().pull_events()[0], ChallengeSent)
    assert isinstance(a_mutual().pull_events()[0], ChallengeOpenedFromMutualInterest)


def test_a_decline_is_not_a_lapse():
    """Two events, because *answers challenges* cannot count one of them."""

    declined = a_tennis_challenge()
    declined.decline(ALICE, occurred_at=at(1))
    lapsed = a_tennis_challenge()
    lapsed.lapse(now=OUTSIDE)

    assert isinstance(declined.pull_events()[-1], SeatDeclined)
    assert isinstance(lapsed.pull_events()[-1], SeatLapsed)
