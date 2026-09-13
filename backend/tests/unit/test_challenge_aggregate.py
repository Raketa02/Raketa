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

And a sixth, which arrived with ``docs/adr/0142``:

**One event announces a conclusion, and the rule that lets it is run here rather
than written down.** *An event may announce a conclusion only when no arrangement
of the seats could reach it.* ``WITHDRAWN`` is the one standing that passes, and
the last section of this module folds every arrangement of every court this
context can hold to prove that it still does.
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields
from datetime import datetime, timedelta, timezone
from itertools import product
from typing import Iterator

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.challenges.domain import events as challenge_events
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
    OnlyAHalfBuiltLineUpIsWithdrawn,
    SomebodyHasJoinedTheCourt,
    TheAnswerWindowHasPassed,
    TheChallengeIsOver,
    TheCourtIsNotThisSports,
    TheOrganiserHoldsASeat,
    TheSeatIsAlreadyAnswered,
    TheWithdrawIsTheOrganisers,
)
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatLeft,
    SeatsInvited,
)
from app.modules.challenges.domain.origins import SentFromSearch, SentOutsideASearch
from app.modules.challenges.domain.seats import (
    Seat,
    SeatAnswer,
    SeatPlan,
    Side,
    court_sides,
)
from app.modules.challenges.domain.standing import (
    ARRANGING,
    ENDED,
    Standing,
    ended_at_of,
    standing_of,
)
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
        by=challenge.organiser_id,
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
    assert not challenge.is_being_arranged_at(INSIDE)


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


def test_a_completed_line_up_releases_the_pair():
    """**The bug this rule was shipped with, and the sentence that names it.**

    ``games_match_history.py`` has always said *a game is never open in this
    sense: the pair rule releases the moment a challenge ends, and it ends when
    the line-up completes into a game*. Nothing implemented it: every seat
    accepted derives ``ON``, ``ON`` was not in ``ENDED``, and two people who
    finished arranging a game were an open pair for as long as the database
    existed — unable to challenge each other **in any sport**, and gone from each
    other's deck permanently ([#343](https://github.com/Raketa02/Raketa/issues/343)).

    What released it is not a sixth ending. It is the pair rule asking **its own
    question** (``docs/adr/0142`` §1): *are these two still arranging a game?*
    ``ON`` answers no because the arranging is finished, and that is a different
    reason from the two endings' *there is nothing left*.
    """

    challenge = a_tennis_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    assert challenge.standing_at(INSIDE) is Standing.ON
    assert challenge.players_in_it_at(INSIDE) == frozenset()
    # And it stays released, with no expiry and no sweep: the fold answers the
    # same a year on, which is exactly how long the old answer stayed wrong.
    assert challenge.players_in_it_at(at(24 * 365)) == frozenset()


def test_a_completed_line_up_has_become_a_game():
    """The other thing the aggregate answers, and the reason it is not the first.

    Releasing the pair rule on ``ON`` took the only guard out from under the
    mutual mint, and ``docs/adr/0152`` gave that path a question of its own —
    *has a mutual between these two already minted a game?* This is the half the
    aggregate can answer. It is not the complement of *are they arranging*: both
    are false while a challenge is being arranged, and both are false once one
    has ended.
    """

    challenge = a_tennis_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    assert challenge.players_in_it_at(INSIDE) == frozenset()
    assert not challenge.is_being_arranged_at(INSIDE)
    assert challenge.has_become_a_game()


def test_a_challenge_still_being_arranged_has_become_no_game_yet():
    """The half-built court holds its pair on the **pair rule** and on nothing
    else: nothing has been minted, so there is no game to be finished with."""

    challenge = a_tennis_challenge()

    assert challenge.is_being_arranged_at(INSIDE)
    assert not challenge.has_become_a_game()


def test_an_ended_challenge_stands_between_nobody_either():
    """Where the two readings meet again: nothing left is nothing on both.

    A challenge that ended without ever completing minted nothing, so it holds
    nobody on either question — which is what releases a pair whose doubles
    mutual was withdrawn half-built.
    """

    challenge = a_tennis_challenge()
    challenge.decline(ALICE, occurred_at=at(1))

    assert not challenge.has_become_a_game()
    assert challenge.players_in_it_at(INSIDE) == frozenset()


def test_on_is_not_an_ending_and_is_not_folded_into_one():
    """The release had one wrong way to get it, and this is the guard against it.

    Adding ``ON`` to ``ENDED`` would have released the pair too, and it would
    have said a challenge everybody accepted is **over** — which ``invite``
    reads to refuse a send, and which the client prints. The two sets answer two
    questions and this asserts they have not been collapsed into one.
    """

    challenge = a_tennis_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    assert Standing.ON not in ENDED
    assert Standing.ON not in ARRANGING
    assert challenge.standing_at(INSIDE) is Standing.ON
    assert not challenge.is_being_arranged_at(INSIDE)


def test_a_half_built_line_up_still_holds_its_pair():
    """The other half of ``ARRANGING``, and it is the half that must not move.

    A padel four whose acceptor is in and whose other seats have gone quiet is
    still being arranged — the organiser can fill the open seat — so the people
    in it are still a pair. Releasing here would let the same two be asked twice
    for one unfinished game.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    assert challenge.standing_at(OUTSIDE) is Standing.LINE_UP_INCOMPLETE
    assert challenge.is_being_arranged_at(OUTSIDE)
    assert challenge.players_in_it_at(OUTSIDE) == frozenset({ORGANISER, ALICE})


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
        by=challenge.organiser_id,
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
        by=challenge.organiser_id,
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
            by=challenge.organiser_id,
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
            by=challenge.organiser_id,
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
            by=challenge.organiser_id,
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
            by=challenge.organiser_id,
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
        by=challenge.organiser_id,
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
            by=challenge.organiser_id,
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
            by=challenge.organiser_id,
            occurred_at=OUTSIDE,
        )


def test_somebody_who_lapsed_is_not_asked_again_with_no_sweep_having_run():
    """**The same refusal, and it must not wait for a loop.**

    The test above sweeps first, so ``answered`` holds the lapsed player and the
    refusal comes off the set. Nothing on this platform guarantees the sweep has
    been past: a seat whose day ran out already reads as lapsed, its pair already
    releases and the standing already folds — *the sweep exists for the record,
    not for correctness*.

    So the two runs have to reach the same answer. Reading ``answered`` alone
    would let a fill re-invite somebody at 24 hours and refuse the identical fill
    at 25 because a loop happened to tick in between — and it is
    ``docs/adr/0150``'s fill that made this reachable, since ``invite`` had no
    caller before it.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    # No `challenge.lapse(...)`, deliberately: CAROL's day has simply run out.

    with pytest.raises(NobodyIsAskedTwice):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                SeatPlan(side=Side.A, player_id=ALICE),
                SeatPlan(side=Side.B, player_id=BOB),
                invited(CAROL, Side.B, 9),
            ),
            by=challenge.organiser_id,
            occurred_at=OUTSIDE,
        )


def test_who_has_already_been_asked_reads_the_same_either_side_of_a_sweep():
    """The one derivation both readers take, asserted as one answer.

    ``invite``'s refusal and the fill's own pool exclusion are two readers of
    this set (``docs/adr/0150`` §4). Two derivations would be two answers to
    *have they already been asked*, and the one that drifted would be the one
    that let somebody be asked twice.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))
    before = challenge.already_asked_at(OUTSIDE)

    recorded = challenge.lapse(now=OUTSIDE)

    assert recorded == 1, "CAROL's seat is the one with nothing in it"
    assert before == challenge.already_asked_at(OUTSIDE)
    assert before == frozenset({ALICE, BOB, CAROL})


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
            by=challenge.organiser_id,
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
        by=challenge.organiser_id,
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
        by=challenge.organiser_id,
        occurred_at=OUTSIDE,
    )

    assert replayed(challenge) == challenge


def test_the_opening_events_are_the_only_two_that_open_a_stream():
    """Seven events, and the two that can start a challenge are named."""

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


# ---------------------------------------------------------------------------
# The withdraw — *Remove the challenge*, while nobody has joined
# ---------------------------------------------------------------------------


def a_court_nobody_will_finish() -> Challenge:
    """A padel four with one acceptance on it and nobody left deciding.

    ``LINE_UP_INCOMPLETE``: the acceptor is in, two seats are open, and nothing
    about this challenge will ever end it on its own. It is the state the
    withdraw was written for (``docs/adr/0142`` §2) and the state it is now
    **refused** in (``docs/adr/0165`` §4): somebody has joined, so the court is
    as much theirs as the organiser's, and its exit is the departure — the
    organiser's included.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))
    challenge.decline(CAROL, occurred_at=at(3))
    return challenge


def a_court_the_organiser_is_alone_on_again() -> Challenge:
    """A padel four somebody joined and then left, with the others still deciding.

    ALICE accepted and took her yes back; BOB and CAROL have not answered. The
    court is ``AWAITING_ANSWERS`` with nobody besides the organiser on it, which
    is the second of the two states the withdraw is admitted in — and the one
    with a room to destroy, since ALICE's yes opened one.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.leave(ALICE, occurred_at=at(2))
    return challenge


def test_the_organiser_removes_a_challenge_nobody_has_answered():
    """``docs/adr/0165`` §4 reverses ``docs/adr/0142`` §2's Phase 1 refusal:
    before anybody answers, the challenge is the organiser's to remove, and the
    re-ask that refusal guarded against is an accepted risk with its falsifier
    named there."""

    challenge = a_padel_challenge()
    assert challenge.standing_at(at(1)) is Standing.AWAITING_ANSWERS

    challenge.withdraw(ORGANISER, occurred_at=at(1))

    assert challenge.standing_at(at(1)) is Standing.WITHDRAWN
    assert isinstance(challenge.pull_events()[-1], ChallengeWithdrawn)


def test_the_organiser_removes_a_court_they_are_alone_on_again():
    """Somebody joined and left; the others are still deciding. Nobody besides
    the organiser holds an accepted seat, so the act is admitted again — the
    seats still awaiting an answer notwithstanding."""

    challenge = a_court_the_organiser_is_alone_on_again()
    assert challenge.standing_at(at(3)) is Standing.AWAITING_ANSWERS

    challenge.withdraw(ORGANISER, occurred_at=at(3))

    assert challenge.standing_at(at(3)) is Standing.WITHDRAWN
    assert isinstance(challenge.pull_events()[-1], ChallengeWithdrawn)


def test_a_court_somebody_has_joined_is_nobodys_to_end_for_the_others():
    """The refusal ``docs/adr/0165`` §4 puts where ``docs/adr/0142`` §2 put the
    act. The people who agreed did nothing wrong, so from here the organiser
    leaves like anybody else and the court ends by itself when one is left."""

    challenge = a_court_nobody_will_finish()

    with pytest.raises(SomebodyHasJoinedTheCourt):
        challenge.withdraw(ORGANISER, occurred_at=at(4))

    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE


def test_one_yes_beside_seats_still_deciding_is_somebody_having_joined():
    """The rule reads the seats and never the standing: ``AWAITING_ANSWERS``
    with one acceptance on it is refused exactly as ``LINE_UP_INCOMPLETE`` is,
    because what matters is that a person is in, not what the others owe."""

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    assert challenge.standing_at(at(2)) is Standing.AWAITING_ANSWERS

    with pytest.raises(SomebodyHasJoinedTheCourt):
        challenge.withdraw(ORGANISER, occurred_at=at(2))


def test_a_withdrawn_challenge_stays_withdrawn_at_every_instant():
    """It is not a deadline and there is no clock in it.

    The other two endings arrive because time passed or somebody answered; this
    one arrived because a person decided, so a year of clock moves nothing —
    and the seats still awaiting an answer when it was removed never lapse it
    into something else.
    """

    challenge = a_court_the_organiser_is_alone_on_again()
    challenge.withdraw(ORGANISER, occurred_at=at(3))

    assert challenge.standing_at(at(3)) is Standing.WITHDRAWN
    assert challenge.standing_at(at(24 * 365)) is Standing.WITHDRAWN


def test_the_withdraw_is_the_organisers_and_an_invitee_is_told_so():
    """**Forbidden and not not-found**: they can see this challenge already.
    Whoever they are — somebody who joined, somebody still deciding."""

    joined = a_court_nobody_will_finish()
    with pytest.raises(TheWithdrawIsTheOrganisers):
        joined.withdraw(ALICE, occurred_at=at(4))
    assert joined.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    deciding = a_padel_challenge()
    with pytest.raises(TheWithdrawIsTheOrganisers):
        deciding.withdraw(BOB, occurred_at=at(1))
    assert deciding.standing_at(at(1)) is Standing.AWAITING_ANSWERS


def test_whose_act_it_is_is_asked_before_what_the_standing_is():
    """An invitee is never told which standings they cannot end.

    Asking the standing first would answer *is this challenge withdrawable* for
    somebody who may not withdraw it either way — the send's own rule, that a
    fact about the caller is checked ahead of anything it would have to read.
    Here that means an invitee on a court somebody joined hears *not yours*
    and never *somebody has joined*.
    """

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    with pytest.raises(TheWithdrawIsTheOrganisers):
        challenge.withdraw(BOB, occurred_at=at(2))
    with pytest.raises(TheWithdrawIsTheOrganisers):
        challenge.withdraw(ALICE, occurred_at=at(2))


def test_an_organiser_who_left_no_longer_holds_the_exit():
    """The organiser is a player in the ending rule (``docs/adr/0165`` §3), and
    in this one: the act is the organiser's **on the court**, and a seat they
    left is not on it. A court they walked out of is proposed by nobody and
    ends by its own clocks."""

    challenge = a_padel_challenge()
    challenge.leave(ORGANISER, occurred_at=at(1))
    assert challenge.standing_at(at(2)) is Standing.AWAITING_ANSWERS

    with pytest.raises(TheWithdrawIsTheOrganisers):
        challenge.withdraw(ORGANISER, occurred_at=at(2))


def test_a_challenge_that_ended_by_itself_has_no_withdraw():
    """The organiser alone with nobody deciding is over already — ``DECLINED``
    where somebody left or said no, ``LAPSED`` where everybody was silent — and
    an ended challenge is refused as every other act refuses one, with
    ``challenge_is_over`` and never with a word about who has joined."""

    declined = a_court_nobody_will_finish()
    declined.leave(ALICE, occurred_at=at(4))
    assert declined.standing_at(at(5)) is Standing.DECLINED
    with pytest.raises(TheChallengeIsOver):
        declined.withdraw(ORGANISER, occurred_at=at(5))

    lapsed = a_padel_challenge()
    assert lapsed.standing_at(OUTSIDE) is Standing.LAPSED
    with pytest.raises(TheChallengeIsOver):
        lapsed.withdraw(ORGANISER, occurred_at=OUTSIDE)


def test_a_completed_line_up_has_no_withdraw():
    """`ON` has become a game, and a whole court has no seat to call it off
    for: a full court that will not play lets its window lapse."""

    challenge = a_tennis_challenge()
    challenge.accept(ALICE, occurred_at=at(1))

    with pytest.raises(OnlyAHalfBuiltLineUpIsWithdrawn):
        challenge.withdraw(ORGANISER, occurred_at=at(2))


def test_a_withdrawal_does_not_come_back():
    """Irreversible, and the second press is refused by the rule every act
    refuses an ended challenge with: it is over."""

    challenge = a_court_the_organiser_is_alone_on_again()
    challenge.withdraw(ORGANISER, occurred_at=at(3))

    with pytest.raises(TheChallengeIsOver):
        challenge.withdraw(ORGANISER, occurred_at=at(4))


def test_a_withdraw_ends_the_whole_challenge_and_removes_nobody():
    """**The seats are left exactly as they were.**

    Per-seat would be the organiser taking out somebody, which
    ``AnAcceptedPlayerMayNotBeRemoved`` refuses and keeps refusing. So the seat
    that was left still reads ``LEFT``, and the two still deciding still hold
    their question and their deadline: what ended is the arrangement, and
    ``standing_at`` reads the withdrawal before it reads any of them.
    """

    challenge = a_court_the_organiser_is_alone_on_again()
    before = challenge.seats

    challenge.withdraw(ORGANISER, occurred_at=at(3))

    assert challenge.seats == before
    assert challenge.seat_of(ALICE).answer is SeatAnswer.LEFT
    assert challenge.seat_of(BOB).answer is None
    assert challenge.seat_of(BOB).answer_by == instant(SENT_AT + ANSWER_WINDOW)


def test_a_withdrawn_challenge_releases_its_pair():
    """A send holds its pairs for as long as an answer is owed — up to a day —
    and removing it releases them on the instant. ``WITHDRAWN`` is in ``ENDED``
    and in nothing else, so the arranging stops and everybody on the court is a
    stranger again."""

    challenge = a_padel_challenge()
    assert challenge.players_in_it_at(at(1)) == frozenset(
        {ORGANISER, ALICE, BOB, CAROL}
    )

    challenge.withdraw(ORGANISER, occurred_at=at(1))

    assert Standing.WITHDRAWN in ENDED
    assert Standing.WITHDRAWN not in ARRANGING
    assert not challenge.is_being_arranged_at(at(1))
    assert challenge.players_in_it_at(at(1)) == frozenset()


def test_a_withdrawn_challenge_never_became_a_game():
    """It ended without reaching ``ON``, so it minted nothing and holds nobody
    on either question the aggregate answers."""

    challenge = a_padel_challenge()
    challenge.withdraw(ORGANISER, occurred_at=at(1))

    assert not challenge.has_become_a_game()


def test_a_withdrawn_challenge_takes_no_more_invitations():
    """Its standing is settled; filling a seat would be a proposal to a
    different set of people, which is a **new** challenge."""

    challenge = a_court_the_organiser_is_alone_on_again()
    challenge.withdraw(ORGANISER, occurred_at=at(3))

    with pytest.raises(TheChallengeIsOver):
        challenge.invite(
            (
                SeatPlan(side=Side.A, player_id=ORGANISER),
                invited(STRANGER, Side.A, 7),
                SeatPlan(side=Side.B, player_id=BOB),
                SeatPlan(side=Side.B, player_id=CAROL),
            ),
            by=challenge.organiser_id,
            occurred_at=at(5),
        )


def test_a_withdrawn_challenge_takes_no_more_answers():
    """**A reach that did not exist, and the refusal it needs.** The withdraw
    used to be legal only where no seat was awaiting, so an answer on a
    withdrawn challenge always met the seat's own refusal first. A removed send
    holds seats still inside their window, and a yes on one of them would open
    a room for a court that is over — so the seat that has nothing of its own
    to refuse is refused as every act refuses an ended challenge.

    **The seat's own facts still come first.** A seat whose day ran out is told
    that whether the challenge stands or not, because the same act refused two
    ways depending on the other seats is the thing ``_answerable_seat``'s order
    exists to prevent.
    """

    challenge = a_padel_challenge()
    challenge.withdraw(ORGANISER, occurred_at=at(1))

    with pytest.raises(TheChallengeIsOver):
        challenge.accept(ALICE, occurred_at=at(2))
    with pytest.raises(TheChallengeIsOver):
        challenge.decline(BOB, occurred_at=at(2))
    with pytest.raises(TheAnswerWindowHasPassed):
        challenge.accept(CAROL, occurred_at=OUTSIDE)
    assert challenge.seat_of(ALICE).answer is None
    assert challenge.standing_at(at(2)) is Standing.WITHDRAWN


def test_a_sweep_records_no_lapse_for_a_day_the_removal_cut_short():
    """``docs/adr/0142`` §5 on the write side: an invitation whose challenge was
    removed before its day ran out is neither answered nor lapsed. The seat's
    day still passes on the clock — the seat reads as lapsed, and nothing
    downstream of a withdrawn challenge minds — but the sweep writes no record
    of it, because the record is the denominator *answers challenges* counts
    and this was not silence.

    A day that had **already** run out when the organiser removed the challenge
    was silence, and is recorded as before — which is what makes ``0142`` §5
    and ``event_sourced_challenge_history.py``'s walk agree seat by seat.
    """

    challenge = a_staggered_padel_court()
    assert challenge.seat_of(ALICE).is_lapsed_at(at(49))
    assert challenge.seat_of(BOB).is_awaiting_at(at(49))

    challenge.withdraw(ORGANISER, occurred_at=at(49))

    assert challenge.lapse(now=at(60)) == 1
    assert challenge.seat_of(ALICE).answer is SeatAnswer.LAPSED
    assert challenge.seat_of(BOB).answer is None
    assert challenge.seat_of(CAROL).answer is None
    assert challenge.lapse(now=at(61)) == 0


def test_a_withdrawal_replays_into_itself():
    challenge = a_court_the_organiser_is_alone_on_again()
    challenge.withdraw(ORGANISER, occurred_at=at(3))

    assert replayed(challenge) == challenge


# ---------------------------------------------------------------------------
# When it ended — the second half of the same fold
# ---------------------------------------------------------------------------


def a_staggered_padel_court() -> Challenge:
    """A padel four holding two different deadlines, with nobody in it yet.

    ALICE was asked at the send; the other two were asked by a fill six hours
    later, so ``answer_by`` differs across the court. That is the only way one
    challenge holds two — a seat filled later starts its own day and cannot
    inherit a deadline from a send it was not part of (``answer_window.py``) —
    and it is what makes *which deadline ended it* a question with an answer.
    """

    challenge = a_padel_challenge(invitees=(ALICE,))
    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(BOB, Side.B, 2),
            invited(CAROL, Side.B, 3),
        ),
        by=ORGANISER,
        occurred_at=at(6),
    )
    return challenge


def test_a_challenge_that_still_stands_is_dated_by_nothing():
    """``None`` on the three standings that are not endings, and the absence is
    the answer rather than a gap: *this challenge has not ended.*"""

    awaiting = a_padel_challenge()
    assert awaiting.standing_at(at(1)) is Standing.AWAITING_ANSWERS
    assert awaiting.ended_at(at(1)) is None

    half_built = a_court_nobody_will_finish()
    assert half_built.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert half_built.ended_at(INSIDE) is None

    on = a_tennis_challenge()
    on.accept(ALICE, occurred_at=at(1))
    assert on.standing_at(at(2)) is Standing.ON
    assert on.ended_at(at(2)) is None


def test_a_lapse_is_dated_by_the_deadline_that_passed_and_needs_no_sweep():
    """**Exact, and the wire could always have said so.** The lapse *is* the
    window closing, so the instant is already on the seat — which is why this
    ending needs nothing recorded and no loop to have run."""

    challenge = a_tennis_challenge()
    deadline = challenge.seat_of(ALICE).answer_by

    assert challenge.standing_at(OUTSIDE) is Standing.LAPSED
    assert challenge.ended_at(OUTSIDE) == deadline
    assert deadline == instant(SENT_AT + ANSWER_WINDOW)
    assert challenge.ended_at(OUTSIDE) != challenge.updated_at


def test_a_lapsed_court_ends_on_the_last_of_its_deadlines_and_not_the_first():
    """A court whose seats were invited on different days ended when the **last**
    of them ran out.

    The stagger comes from a fill, which is the only way one court holds two
    deadlines: ``answer_by`` is dated when *that* seat was invited, so a seat
    filled later starts its own day (``answer_window.py``).
    """

    challenge = a_staggered_padel_court()
    first = challenge.seat_of(ALICE).answer_by
    last = challenge.seat_of(BOB).answer_by

    assert challenge.standing_at(at(55)) is Standing.LAPSED
    assert challenge.ended_at(at(55)) == last
    assert first < last
    assert challenge.ended_at(at(55)) != challenge.updated_at


def test_a_decline_is_dated_by_the_tighter_of_the_two_bounds_it_has():
    """**An upper bound, and the schema says so.**

    Nothing records *when* somebody declined: dating an answer is the history
    walk's job and deliberately not the fold's — an answer happened to the court
    as it stood then, and ``event_sourced_challenge_history.py`` is where that
    walk lives. So the fold uses the two facts it does hold, and here the
    stream's own instant is the tighter one and is exact, because the decline is
    the last thing that happened to it.
    """

    challenge = a_tennis_challenge()
    challenge.decline(ALICE, occurred_at=at(5))

    assert challenge.standing_at(at(6)) is Standing.DECLINED
    assert challenge.ended_at(at(6)) == at(5)
    assert at(5) < challenge.seat_of(ALICE).answer_by


def test_the_ending_instant_does_not_move_when_the_sweep_runs():
    """**The sweep buys a record and not a reading**, and this is a reading it
    must not touch (``lapse_expired_seats.py``).

    It is also the decline bound's other branch. A court somebody declined can
    hold a seat that ran out unanswered, so a sweep may append a ``SeatLapsed``
    to it weeks later and move ``updated_at``; the declining seat's own deadline
    is the smaller of the two and holds the answer still.
    """

    challenge = a_padel_challenge(invitees=(ALICE, BOB))
    challenge.decline(ALICE, occurred_at=at(5))
    ended = challenge.seat_of(BOB).answer_by

    assert challenge.standing_at(at(49)) is Standing.DECLINED
    assert challenge.ended_at(at(49)) == ended

    assert challenge.lapse(now=at(60)) == 1
    assert challenge.updated_at == at(60)
    assert challenge.ended_at(at(61)) == ended


def test_a_declined_court_ends_when_its_last_seat_leaves_not_when_the_no_arrived():
    """**The standing says which ending it was. It does not say when.**

    A no outranks silence whatever order the two arrived in
    (:func:`_how_it_ended`), so a court can read ``DECLINED`` and have gone on
    standing for two days after the no — until the last seat still deciding ran
    out. Dating the whole challenge from the decline would retire the row while
    the court was still live.
    """

    challenge = a_staggered_padel_court()
    challenge.decline(BOB, occurred_at=at(7))
    last = challenge.seat_of(CAROL).answer_by

    assert challenge.standing_at(at(55)) is Standing.DECLINED
    assert challenge.ended_at(at(55)) == last
    assert challenge.ended_at(at(55)) > at(7)


def test_a_withdrawal_is_dated_by_the_act_and_not_by_what_happened_after_it():
    """**Exact**, because it is the one ending a recorded decision puts there and
    the decision carries its own instant (``docs/adr/0142``).

    And it is emphatically **not** the last thing that happened to the stream. A
    withdraw is admitted while seats are still awaiting an answer, and one of
    them may already have run out with nothing in it and nothing having swept
    it — so a sweep can append a ``SeatLapsed`` *after* a legal withdrawal, and
    does here. ``event_sourced_challenge_history.py`` writes the same
    reachability down for its own denominator's sake.
    """

    challenge = a_staggered_padel_court()
    assert challenge.seat_of(ALICE).is_lapsed_at(at(49)), "unswept"
    assert challenge.standing_at(at(49)) is Standing.AWAITING_ANSWERS

    challenge.withdraw(ORGANISER, occurred_at=at(49))

    assert challenge.ended_at(at(50)) == at(49)
    assert challenge.ended_at(at(50)) != challenge.opened_at

    assert challenge.lapse(now=at(60)) == 1
    assert challenge.updated_at == at(60)
    assert challenge.ended_at(at(61)) == at(49)


def test_the_withdrawal_instant_survives_a_replay():
    """It is folded off the event and stored nowhere else, so the rebuilt
    aggregate answers what the live one did — the shape ``opened_at`` already
    has, and the reason ``withdrawn`` stopped being a bare ``bool``."""

    challenge = a_court_the_organiser_is_alone_on_again()
    challenge.withdraw(ORGANISER, occurred_at=at(4))

    assert replayed(challenge).ended_at(at(5)) == at(4)


def test_every_court_that_has_ended_can_say_when_and_every_one_that_stands_cannot():
    """**A total function over every arrangement**, on the exemption test's own
    machinery below and for a related reason: the two halves of one fold have to
    agree about every court this context can hold, and a standing whose instant
    raises inside a read is worse than one that has none.

    It reaches the two edges nothing above can get to through the aggregate: a
    court whose non-organiser seats are all empty, which folds to ``LAPSED``
    with nobody to have departed, and a seat carrying no deadline.
    """

    updated = at(70)
    for sport in (Sport.TENNIS, Sport.PADEL):
        for seats, game_opened in _every_arrangement_of(sport):
            standing = standing_of(
                seats,
                now=INSIDE,
                withdrawn=False,
                game_opened=game_opened,
            )
            ended = ended_at_of(
                seats,
                now=INSIDE,
                updated_at=updated,
                withdrawn_at=None,
                game_opened=game_opened,
                departed_at=_departures_of(seats),
            )

            assert (ended is not None) == (standing in ENDED), (standing, seats)


def test_a_withdrawal_is_dated_by_the_act_whatever_the_seats_say():
    """The one ending no arrangement of the seats reaches is also the one whose
    instant no arrangement of the seats can argue with."""

    for sport in (Sport.TENNIS, Sport.PADEL):
        for seats, game_opened in _every_arrangement_of(sport):
            assert (
                ended_at_of(
                    seats,
                    now=INSIDE,
                    updated_at=at(70),
                    withdrawn_at=at(30),
                    game_opened=game_opened,
                    departed_at=_departures_of(seats),
                )
                == at(30)
            ), seats


# ---------------------------------------------------------------------------
# Leaving a game — the line-up is frozen until somebody leaves it (ADR-0162)
# ---------------------------------------------------------------------------


def a_completed_four() -> Challenge:
    challenge = a_padel_challenge()
    for who in (ALICE, BOB, CAROL):
        challenge.accept(who, occurred_at=at(1))
    assert challenge.standing_at(INSIDE) is Standing.ON
    return challenge


def test_leaving_reopens_the_seat_and_the_court_is_half_built_again():
    """The seat carries ``LEFT`` with its occupant still on it, the fold
    re-derives ``LINE_UP_INCOMPLETE`` with no change to its rungs, and the one
    who left is a stranger to the others again — out of the pair, and out of
    this court's own pool."""

    challenge = a_completed_four()
    challenge.leave(CAROL, occurred_at=at(2))

    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert challenge.seat_of(CAROL).answer is SeatAnswer.LEFT
    assert challenge.players_in_it_at(INSIDE) == {ORGANISER, ALICE, BOB}
    assert CAROL in challenge.already_asked_at(INSIDE)
    assert challenge.is_being_arranged_at(INSIDE)
    assert isinstance(challenge.pull_events()[-1], SeatLeft)


def test_a_court_that_has_been_a_game_says_so_after_the_seat_is_given_away():
    """**The fact the seats cannot hold.** A re-seat gives the departed's
    position to somebody else, and a court whose newcomer then declined has no
    seat left saying it was once a game — so it is folded off the completion
    and kept (``docs/adr/0165`` §2), and ``has_become_a_game`` keeps answering
    yes."""

    challenge = a_completed_four()
    challenge.leave(CAROL, occurred_at=at(2))
    challenge.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            SeatPlan(side=Side.B, player_id=BOB),
            invited(STRANGER, Side.B, 4),
        ),
        by=ALICE,
        occurred_at=at(3),
    )
    challenge.decline(STRANGER, occurred_at=at(4))

    assert all(seat.answer is not SeatAnswer.LEFT for seat in challenge.seats)
    rebuilt = replayed(challenge)
    assert rebuilt.game_opened
    assert rebuilt.has_become_a_game()
    assert rebuilt.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE


def test_the_organiser_alone_on_a_court_that_has_been_a_game_is_not_an_ending():
    """``docs/adr/0162`` §2 — the singles case. Without ``game_opened`` the fold
    would file the organiser alone as ``DECLINED`` now (a departure is a no);
    with it, the court stands ``LINE_UP_INCOMPLETE`` and the game it became is
    what ends — one layer up, off ``is_deserted_at``. And the organiser may
    leave too."""

    challenge = a_tennis_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.leave(ALICE, occurred_at=at(2))

    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert challenge.ended_at(INSIDE) is None

    other = a_tennis_challenge()
    other.accept(ALICE, occurred_at=at(1))
    other.leave(ORGANISER, occurred_at=at(2))

    assert other.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert other.players_in_it_at(INSIDE) == {ALICE}
    assert other.organiser_seat_required(INSIDE) is None


def test_two_may_leave_and_the_second_leaves_a_court_already_half_built():
    challenge = a_completed_four()
    challenge.leave(BOB, occurred_at=at(2))
    challenge.leave(CAROL, occurred_at=at(3))

    assert [seat.answer for seat in challenge.seats].count(SeatAnswer.LEFT) == 2
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE


def test_an_ended_court_and_a_seat_that_is_not_yours_cannot_be_left():
    """An ended challenge has nobody to leave, and only an accepted seat has
    anything to leave. *Not a game yet* used to be a third refusal here and is
    gone (``docs/adr/0165`` §1): a yes can be taken back before the court is
    whole, which ``test_a_yes_can_be_taken_back_before_the_court_is_whole``
    drives."""

    ended = a_tennis_challenge()
    ended.decline(ALICE, occurred_at=at(1))
    with pytest.raises(TheChallengeIsOver):
        ended.leave(ORGANISER, occurred_at=INSIDE)

    game = a_completed_four()
    with pytest.raises(NotYourSeat):
        game.leave(STRANGER, occurred_at=at(2))
    game.leave(CAROL, occurred_at=at(2))
    with pytest.raises(NotYourSeat):
        game.leave(CAROL, occurred_at=at(3))


def test_a_court_that_has_been_a_game_is_called_off_by_the_organiser():
    """``docs/adr/0163`` §1 — the withdraw reaches a reopened court. The game is
    told one layer up; here the challenge ends as any withdrawn one does, with
    the seats left as they were and the pair released."""

    challenge = a_completed_four()
    challenge.leave(CAROL, occurred_at=at(2))
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    challenge.withdraw(ORGANISER, occurred_at=at(3))

    assert challenge.standing_at(INSIDE) is Standing.WITHDRAWN
    assert challenge.ended_at(INSIDE) == at(3)
    assert challenge.has_become_a_game(), "the game it became is still a fact"
    assert challenge.players_in_it_at(INSIDE) == frozenset()
    assert challenge.seat_of(CAROL).answer is SeatAnswer.LEFT
    assert isinstance(challenge.pull_events()[-1], ChallengeWithdrawn)


def test_any_player_on_a_court_that_has_been_a_game_holds_the_exit():
    """``docs/adr/0165`` §5 — *Call it off* is any player's on the court, with
    the organiser still in and no fallback to wait for. A group that has given
    up on a game ends it in one act rather than three departures."""

    challenge = a_completed_four()
    challenge.leave(CAROL, occurred_at=at(2))
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    challenge.withdraw(BOB, occurred_at=at(3))

    assert challenge.standing_at(INSIDE) is Standing.WITHDRAWN
    assert challenge.ended_at(INSIDE) == at(3)


def test_somebody_off_the_court_is_told_the_act_is_not_theirs_and_reads_no_standing():
    """*On the court* means an accepted seat: somebody who left, a stranger, the
    organiser who left, and a newcomer still deciding on a fill are all told
    the act is not theirs — before the fold is consulted, so the one still
    deciding hears *not yours* and never which standing they could not end."""

    left = a_completed_four()
    left.leave(ORGANISER, occurred_at=at(2))
    left.leave(CAROL, occurred_at=at(3))
    with pytest.raises(TheWithdrawIsTheOrganisers):
        left.withdraw(CAROL, occurred_at=at(4))
    with pytest.raises(TheWithdrawIsTheOrganisers):
        left.withdraw(STRANGER, occurred_at=at(4))
    # **The organiser who left is not on the court either**: the exit belongs
    # to the people still on it, and a stranger to them now does not end their
    # game.
    with pytest.raises(TheWithdrawIsTheOrganisers):
        left.withdraw(ORGANISER, occurred_at=at(4))
    assert left.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    filling = a_completed_four()
    filling.leave(CAROL, occurred_at=at(2))
    filling.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            SeatPlan(side=Side.B, player_id=BOB),
            invited(STRANGER, Side.B, 4),
        ),
        by=ALICE,
        occurred_at=at(3),
    )
    assert filling.standing_at(at(4)) is Standing.AWAITING_ANSWERS
    with pytest.raises(TheWithdrawIsTheOrganisers):
        filling.withdraw(STRANGER, occurred_at=at(4))


def test_a_game_is_called_off_only_while_a_seat_is_open_and_nobody_is_deciding():
    """The game's own invariant, kept on the challenge's side: a whole court has
    no seat to call it off for, and a court whose open seat somebody is deciding
    on is not half built yet — one code for the two, because they are one
    sentence and the fold already told the caller which."""

    whole = a_completed_four()
    with pytest.raises(OnlyAHalfBuiltLineUpIsWithdrawn):
        whole.withdraw(ALICE, occurred_at=at(2))
    assert whole.standing_at(INSIDE) is Standing.ON

    filling = a_completed_four()
    filling.leave(CAROL, occurred_at=at(2))
    filling.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            SeatPlan(side=Side.B, player_id=BOB),
            invited(STRANGER, Side.B, 4),
        ),
        by=ALICE,
        occurred_at=at(3),
    )
    with pytest.raises(OnlyAHalfBuiltLineUpIsWithdrawn):
        filling.withdraw(ALICE, occurred_at=at(4))
    assert filling.standing_at(at(4)) is Standing.AWAITING_ANSWERS


def test_the_exit_is_held_after_the_organisers_seat_was_given_away():
    """A re-seat gives the departed's position to the newcomer, so the organiser
    holds no seat at all — and whoever is on the court holds the exit exactly as
    they did while the organiser's seat still said ``LEFT``."""

    challenge = a_completed_four()
    challenge.leave(ORGANISER, occurred_at=at(2))
    challenge.invite(
        (
            invited(STRANGER, Side.A, 4),
            SeatPlan(side=Side.A, player_id=ALICE),
            SeatPlan(side=Side.B, player_id=BOB),
            SeatPlan(side=Side.B, player_id=CAROL),
        ),
        by=ALICE,
        occurred_at=at(3),
    )
    challenge.decline(STRANGER, occurred_at=at(4))
    assert challenge.seat_of(ORGANISER) is None
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    challenge.withdraw(CAROL, occurred_at=at(5))

    assert challenge.standing_at(INSIDE) is Standing.WITHDRAWN


def test_a_court_that_has_been_a_game_is_the_only_one_a_non_organiser_may_end():
    """*Call it off* is any player's; *Remove the challenge* is the organiser's.
    A court that was never a game is the organiser's alone to withdraw, whatever
    its seats say — and somebody who joined it leaves it instead."""

    challenge = a_court_nobody_will_finish()

    with pytest.raises(TheWithdrawIsTheOrganisers):
        challenge.withdraw(ALICE, occurred_at=at(4))


def test_the_departed_are_not_asked_again_and_the_seat_goes_to_somebody_new():
    challenge = a_completed_four()
    challenge.leave(CAROL, occurred_at=at(2))
    court = (
        SeatPlan(side=Side.A, player_id=ORGANISER),
        SeatPlan(side=Side.A, player_id=ALICE),
        SeatPlan(side=Side.B, player_id=BOB),
    )

    with pytest.raises(NobodyIsAskedTwice):
        challenge.invite(
            (*court, invited(CAROL, Side.B, 4)), by=ALICE, occurred_at=at(3)
        )
    challenge.invite(
        (*court, invited(STRANGER, Side.B, 4)), by=ALICE, occurred_at=at(3)
    )
    challenge.accept(STRANGER, occurred_at=at(4))

    assert challenge.standing_at(INSIDE) is Standing.ON
    assert CAROL in challenge.already_asked_at(INSIDE)


def test_a_court_the_organiser_left_is_filled_without_them():
    """``refuse_a_bad_court``'s organiser rule is asked only while the organiser
    is still on the court; once they have left, the court is proposed by nobody
    and filled by whoever is still on it."""

    challenge = a_completed_four()
    challenge.leave(ORGANISER, occurred_at=at(2))

    challenge.invite(
        (
            invited(STRANGER, Side.A, 4),
            SeatPlan(side=Side.A, player_id=ALICE),
            SeatPlan(side=Side.B, player_id=BOB),
            SeatPlan(side=Side.B, player_id=CAROL),
        ),
        by=ALICE,
        occurred_at=at(3),
    )

    assert challenge.standing_at(INSIDE) is Standing.AWAITING_ANSWERS
    assert challenge.organiser_id == ORGANISER


# ---------------------------------------------------------------------------
# A court is over when one is left, and a yes can be taken back (ADR-0165)
# ---------------------------------------------------------------------------


def test_a_yes_can_be_taken_back_before_the_court_is_whole():
    """``docs/adr/0165`` §1 — the departure is admitted on a court that has not
    been a game. The seat carries ``LEFT``, the leaver is a stranger to the
    others and out of this court's own pool, and the court is half built — or
    still awaiting, if somebody is deciding."""

    half_built = a_padel_challenge()
    half_built.accept(ALICE, occurred_at=at(1))
    half_built.accept(BOB, occurred_at=at(2))
    half_built.decline(CAROL, occurred_at=at(3))
    assert half_built.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    half_built.leave(ALICE, occurred_at=at(4))

    assert half_built.seat_of(ALICE).answer is SeatAnswer.LEFT
    assert half_built.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert half_built.players_in_it_at(INSIDE) == {ORGANISER, BOB}
    assert ALICE in half_built.already_asked_at(INSIDE)
    assert not half_built.has_become_a_game()
    assert isinstance(half_built.pull_events()[-1], SeatLeft)

    awaiting = a_padel_challenge()
    awaiting.accept(ALICE, occurred_at=at(1))
    awaiting.leave(ALICE, occurred_at=at(2))
    assert awaiting.standing_at(INSIDE) is Standing.AWAITING_ANSWERS


def test_one_left_with_nobody_deciding_ends_it_and_a_departure_is_a_no():
    """``docs/adr/0165`` §3 — the organiser alone after B accepted and left is
    ``DECLINED``: somebody made a judgement about this court, and a no outranks
    silence whichever order the two arrived in. Dated by the departure."""

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))
    challenge.decline(CAROL, occurred_at=at(3))
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    challenge.leave(ALICE, occurred_at=at(4))

    assert challenge.standing_at(INSIDE) is Standing.DECLINED
    assert challenge.ended_at(INSIDE) == at(4)
    assert challenge.players_in_it_at(INSIDE) == frozenset()

    # And it outranks silence: two lapsed unanswered, one accepted and left.
    silent = a_padel_challenge()
    silent.accept(ALICE, occurred_at=at(1))
    silent.leave(ALICE, occurred_at=OUTSIDE)
    assert silent.standing_at(OUTSIDE) is Standing.DECLINED, "a departure is a no"
    assert silent.ended_at(OUTSIDE) == OUTSIDE, "the departure, not a deadline"


def test_one_left_with_somebody_deciding_is_still_arranging():
    """The other direction: a court with one on it is not over while a seat is
    still awaiting an answer. And once that answer is a yes, two are on it."""

    challenge = a_padel_challenge()
    challenge.decline(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))

    assert challenge.standing_at(INSIDE) is Standing.AWAITING_ANSWERS
    assert challenge.ended_at(INSIDE) is None

    challenge.accept(CAROL, occurred_at=at(3))
    assert challenge.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE


def test_the_ending_rule_is_organiser_blind():
    """The organiser is a player in the rule. B alone after the organiser left is
    ``DECLINED``; B alone with C still deciding is still arranging, and the
    organiser's departure is what dates the ending when it comes."""

    alone = a_padel_challenge()
    alone.accept(ALICE, occurred_at=at(1))
    alone.decline(BOB, occurred_at=at(2))
    alone.decline(CAROL, occurred_at=at(3))
    alone.leave(ORGANISER, occurred_at=at(4))
    assert alone.standing_at(INSIDE) is Standing.DECLINED
    assert alone.ended_at(INSIDE) == at(4)
    assert alone.players_in_it_at(INSIDE) == frozenset()

    four = a_padel_challenge()
    four.accept(ALICE, occurred_at=at(1))
    four.decline(BOB, occurred_at=at(2))
    four.leave(ORGANISER, occurred_at=at(3))
    assert four.standing_at(INSIDE) is Standing.AWAITING_ANSWERS
    assert four.players_in_it_at(INSIDE) == {ALICE, CAROL}

    four.decline(CAROL, occurred_at=at(4))
    assert four.standing_at(INSIDE) is Standing.DECLINED
    assert four.ended_at(INSIDE) == at(4), "the last person asked to have left"


def test_a_no_and_a_departure_read_the_same_off_hand_built_seats():
    """The rule on the fold itself, for the seats the aggregate reaches in
    several steps: one accepted seat with the rest open is over, whoever holds
    it; one accepted seat beside a seat still deciding is not."""

    organiser_alone = (
        Seat(side=Side.A, player_id=ORGANISER, answer=SeatAnswer.ACCEPTED),
        _asked(Side.A, ALICE, SeatAnswer.LEFT, OUTSIDE),
        _asked(Side.B, BOB, SeatAnswer.LAPSED, OUTSIDE),
        Seat(side=Side.B),
    )
    alice_alone = (
        Seat(side=Side.A, player_id=ORGANISER, answer=SeatAnswer.LEFT),
        _asked(Side.A, ALICE, SeatAnswer.ACCEPTED, OUTSIDE),
        _asked(Side.B, BOB, None, SENT_AT),
        Seat(side=Side.B),
    )
    alice_and_a_decider = (
        Seat(side=Side.A, player_id=ORGANISER, answer=SeatAnswer.LEFT),
        _asked(Side.A, ALICE, SeatAnswer.ACCEPTED, OUTSIDE),
        _asked(Side.B, BOB, None, OUTSIDE),
        Seat(side=Side.B),
    )

    def folded(seats):
        return standing_of(seats, now=INSIDE, withdrawn=False, game_opened=False)

    assert folded(organiser_alone) is Standing.DECLINED
    assert folded(alice_alone) is Standing.DECLINED
    assert folded(alice_and_a_decider) is Standing.AWAITING_ANSWERS


def test_a_departure_dates_the_ending_exactly_and_the_sweep_does_not_move_it():
    """**Exact, off the event** — the reason the fold holds ``departed_at``. A court
    can be deserted while a seat's day has run out unswept, so a sweep may
    append a ``SeatLapsed`` *after* the departure and move ``updated_at``; the
    ending stays where the departure put it, and it survives a replay."""

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.decline(BOB, occurred_at=at(2))
    left = instant(OUTSIDE + timedelta(hours=1))
    challenge.leave(ALICE, occurred_at=left)

    assert challenge.standing_at(left) is Standing.DECLINED
    assert challenge.ended_at(left) == left
    assert challenge.lapse(now=at(60)) == 1
    assert challenge.updated_at == at(60)
    assert challenge.ended_at(at(61)) == left
    assert replayed(challenge).ended_at(at(61)) == left


def test_has_become_a_game_is_folded_off_completion_and_not_off_a_departure():
    """``docs/adr/0165`` §2 — true at the acceptance that completes the line-up
    and false after a departure from a court that never completed; and a
    mutual-born singles is a game from birth where a mutual-born padel is not."""

    challenge = a_padel_challenge()
    challenge.accept(ALICE, occurred_at=at(1))
    challenge.accept(BOB, occurred_at=at(2))
    assert not challenge.has_become_a_game()
    challenge.accept(CAROL, occurred_at=at(3))
    assert challenge.has_become_a_game()
    assert replayed(challenge).has_become_a_game()

    left_early = a_padel_challenge()
    left_early.accept(ALICE, occurred_at=at(1))
    left_early.leave(ALICE, occurred_at=at(2))
    assert not left_early.has_become_a_game()
    assert not replayed(left_early).has_become_a_game()

    singles = Challenge.opened_from_mutual_interest(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        organiser_id=ORGANISER,
        other_player_id=ALICE,
        occurred_at=SENT_AT,
    )
    assert singles.has_become_a_game()
    doubles = Challenge.opened_from_mutual_interest(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        organiser_id=ORGANISER,
        other_player_id=ALICE,
        occurred_at=SENT_AT,
    )
    assert not doubles.has_become_a_game()


def test_a_court_that_has_been_a_game_is_deserted_but_not_ended_by_its_seats():
    """``docs/adr/0165`` §3 on a game — the fold still does not end it
    (``docs/adr/0162`` §2 stands), so the use case asks the rule itself: the
    departure that leaves one player with nobody deciding is the one that ends
    it, however many fills came between."""

    game = a_completed_four()
    game.leave(BOB, occurred_at=at(2))
    assert not game.is_deserted_at(INSIDE)
    game.leave(CAROL, occurred_at=at(3))
    assert not game.is_deserted_at(INSIDE)
    game.leave(ALICE, occurred_at=at(4))

    assert game.is_deserted_at(INSIDE)
    assert game.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE
    assert game.ended_at(INSIDE) is None

    two = a_tennis_challenge()
    two.accept(ALICE, occurred_at=at(1))
    two.leave(ALICE, occurred_at=at(2))
    assert two.is_deserted_at(INSIDE)
    assert two.standing_at(INSIDE) is Standing.LINE_UP_INCOMPLETE

    # A fill pending keeps it from being deserted: only the challenge can tell
    # an open seat from one that is asked, which is why the rule lives here.
    filled = a_completed_four()
    filled.leave(BOB, occurred_at=at(2))
    filled.leave(CAROL, occurred_at=at(3))
    filled.invite(
        (
            SeatPlan(side=Side.A, player_id=ORGANISER),
            SeatPlan(side=Side.A, player_id=ALICE),
            invited(STRANGER, Side.B, 4),
            SeatPlan(side=Side.B),
        ),
        by=ALICE,
        occurred_at=at(4),
    )
    filled.leave(ALICE, occurred_at=at(5))
    assert not filled.is_deserted_at(INSIDE)
    filled.decline(STRANGER, occurred_at=at(6))
    assert filled.is_deserted_at(INSIDE)


# ---------------------------------------------------------------------------
# The exemption — run rather than written down
# ---------------------------------------------------------------------------

def _asked(side: Side, who, answer: SeatAnswer | None, deadline: Instant) -> Seat:
    """An invited seat: somebody, their answer or the absence of one, and their
    own day. The origin is the same for all of them because it is the one field
    on a seat that no standing reads."""

    return Seat(
        side=side,
        player_id=who,
        answer=answer,
        answer_by=deadline,
        origin=SentFromSearch(search_id=SEARCH, position=1),
    )


#: Every state one seat of a court can be in, as a factory taking the side and
#: whoever sits there. Seven and not six: a seat whose day has run out with no
#: sweep having been past reads as lapsed, and it is a *different* arrangement
#: from one the sweep recorded — folding both is what makes the enumeration
#: below an enumeration of the states this context can hold rather than of the
#: ones it happens to write down. The seventh is a seat somebody **left**
#: (``docs/adr/0162``) — on a court that has been a game or, since
#: ``docs/adr/0165`` §1, on one that has not.
_SEAT_STATES = (
    lambda side, who: Seat(side=side),
    lambda side, who: _asked(side, who, None, OUTSIDE),
    lambda side, who: _asked(side, who, None, SENT_AT),
    lambda side, who: _asked(side, who, SeatAnswer.ACCEPTED, OUTSIDE),
    lambda side, who: _asked(side, who, SeatAnswer.DECLINED, OUTSIDE),
    lambda side, who: _asked(side, who, SeatAnswer.LAPSED, OUTSIDE),
    lambda side, who: _asked(side, who, SeatAnswer.LEFT, OUTSIDE),
)

#: The organiser's two states: accepted from birth, and gone from it. A left
#: seat carries no deadline here because the organiser was never asked, which
#: is the one such seat the enumeration above cannot produce.
_ORGANISER_STATES = (
    lambda side: Seat(side=side, player_id=ORGANISER, answer=SeatAnswer.ACCEPTED),
    lambda side: Seat(side=side, player_id=ORGANISER, answer=SeatAnswer.LEFT),
)


#: When everybody who left, in the enumeration below, did so. The fold hands
#: the instant of each departure to ``ended_at_of`` off the event, so the
#: hand-built courts have to say when theirs happened too.
LEFT_AT = at(40)


def _departures_of(seats: tuple[Seat, ...]) -> dict:
    return {
        seat.player_id: LEFT_AT
        for seat in seats
        if seat.answer is SeatAnswer.LEFT and seat.player_id is not None
    }


def _every_arrangement_of(sport: Sport) -> Iterator[tuple[tuple[Seat, ...], bool]]:
    """Every court this sport can hold, with the organiser on the first seat,
    **and whether it has been a game**.

    The organiser's seat is fixed because it is fixed everywhere: accepted from
    birth, because they are the one proposing — or left. Every other position
    takes each of the seven states in turn, and a distinct person, so no
    arrangement here is one the aggregate would have refused for a reason having
    nothing to do with what is being asked.

    The second half of each pair is the fact the seats cannot hold, and **every
    arrangement is yielded both ways**: a court with a left seat may have been a
    game or not (``docs/adr/0165`` §1), and a court without one may have been
    re-seated since or never completed.
    """

    sides = court_sides(sport)
    people = [new_uuid() for _ in sides[1:]]
    for organiser in _ORGANISER_STATES:
        for states in product(_SEAT_STATES, repeat=len(sides) - 1):
            seats = (organiser(sides[0]),) + tuple(
                state(side, who)
                for state, side, who in zip(states, sides[1:], people, strict=True)
            )
            yield seats, True
            yield seats, False


def test_an_event_may_announce_a_conclusion_only_when_the_seats_cannot_reach_it():
    """**The exemption, as a test rather than as a sentence** (`docs/adr/0142`).

    Every standing but one is a reading of the seats and the clock, so an event
    announcing one would be a *second* place for it to be true — and the one a
    subscriber would believe. `WITHDRAWN` is exempt because there is no first
    place: no arrangement of any court this context can hold folds to it.

    This is the test the next person to add an event has to pass. It goes red
    two ways, and both of them are the failure: a standing that stops being
    reachable from the seats, and a standing added to the enum without an event
    or a fold that can produce it.
    """

    reachable = {
        standing_of(
            seats,
            now=INSIDE,
            withdrawn=False,
            game_opened=game_opened,
        )
        for sport in (Sport.TENNIS, Sport.PADEL)
        for seats, game_opened in _every_arrangement_of(sport)
    }

    assert reachable == set(Standing) - {Standing.WITHDRAWN}


def test_a_court_that_has_been_a_game_reaches_neither_ending_by_its_seats():
    """``docs/adr/0162`` §2 — the organiser alone on a court whose opponent left
    is a game with a seat to fill, not a send nobody answered. Whatever the
    seats say, such a court folds to one of the three that are not endings."""

    for sport in (Sport.TENNIS, Sport.PADEL):
        for seats, game_opened in _every_arrangement_of(sport):
            if not game_opened:
                continue
            standing = standing_of(
                seats,
                now=INSIDE,
                withdrawn=False,
                game_opened=True,
            )
            assert standing not in ENDED, (standing, seats)


def test_the_one_event_that_is_not_about_a_seat_is_the_withdrawal():
    """The other half of the same rule, read off the events module itself.

    An event carrying a seat or a player is a fact the fold already has; an
    event carrying neither is announcing something about the challenge as a
    whole, which is the shape a conclusion takes here. There is exactly one, and
    a ``GameOn`` added tomorrow is caught without anybody having to remember to
    add it to a list.

    **It is a proxy and it is deliberately blunt.** A whole-challenge event that
    announced *no* conclusion would fail this too, and that is the intended
    outcome rather than a false positive: the exemption above is what makes an
    event of that shape legal in this context, so the second one has to be
    argued for in writing rather than discovered later. The precise rule is the
    test above; this one is what stops it being reached around.
    """

    declared = [
        value
        for name, value in vars(challenge_events).items()
        if isinstance(value, type)
        and not name.startswith("_")
        and value.__module__ == challenge_events.__name__
    ]
    about_a_seat = {
        event
        for event in declared
        if {"seats", "player_id"} & {one.name for one in dataclass_fields(event)}
    }

    assert set(declared) - about_a_seat == {ChallengeWithdrawn}
