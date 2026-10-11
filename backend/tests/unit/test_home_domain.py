"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2; the screens A4.1, A8).

**A booked game's status is folded on every read** from the booking, its
ordinary Game's result and the clock — never stored. Booked until its hour; then
the result states, unchanged from today's cards. **The money line** is the share
every seat holds until the club's cut-off and takes at it — *free to leave
until* then, *Paid* from it on (#637). **The forecast** shows while
the game awaits its entry.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.games.domain.windows import scores_still_waiting_since
from app.modules.proposals.domain.club_bookings import (
    ClubStatus,
    called_off_for_the_club,
    club_status,
)
from app.modules.proposals.domain.home import (
    BookedGame,
    BookedMoney,
    BookedState,
    BookingStage,
    CalledOffReason,
    GameResult,
    HomeStatus,
    LateRefund,
    Leaving,
    ResultStage,
    ShareState,
    as_filling_again,
    leave_terms,
    money_of,
    needs_you,
    on_home,
    on_home_since,
    shows_forecast,
    state_of,
    status_of,
)
from app.modules.proposals.domain.proposal import Standing

WARSAW = ZoneInfo("Europe/Warsaw")
OLA, KUBA, EWA, TOMEK = (uuid4() for _ in range(4))


def warsaw(day: int, hour: int, minute: int = 0):
    return instant(datetime(2026, 10, day, hour, minute, tzinfo=WARSAW))


def a_booked_game(**changes) -> BookedGame:
    """Saturday 10 October at 17:00, 30 zł a seat, 28,55 zł back if you leave
    by Friday 17:00."""

    fields = dict(
        booking_id=uuid4(),
        pool_id=uuid4(),
        club_id=uuid4(),
        court_name="Court 2",
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=warsaw(10, 17),
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=warsaw(9, 17),
        game_id=uuid4(),
    )
    fields.update(changes)
    return BookedGame(**fields)


#: The card fee the payments estimate on a 30 zł share: 1.5 % and 1 zł.
#: What a late leaver paying by a business card would get back of a 30 zł
#: share: 1.9 % and 1 zł kept on their payment (#641).
A_BUSINESS_CARD_S = LateRefund(refund_grosze=28_43, fee_kept_grosze=1_57)

ENTRY_OPEN = GameResult(stage=ResultStage.ENTRY_OPEN, awaits_your_agreement=False)


# --------------------------------------------------------------------------- #
# The status
# --------------------------------------------------------------------------- #


def test_a_booked_game_is_booked_until_its_hour():
    game = a_booked_game()

    assert status_of(game, ENTRY_OPEN, now=warsaw(5, 8)) is HomeStatus.BOOKED
    assert status_of(game, ENTRY_OPEN, now=warsaw(10, 16, 59)) is HomeStatus.BOOKED


def test_from_its_hour_a_game_nobody_said_happened_needs_its_result():
    game = a_booked_game()

    assert status_of(game, ENTRY_OPEN, now=warsaw(10, 17)) is HomeStatus.NEEDS_RESULT


@pytest.mark.parametrize(
    ("stage", "status"),
    [
        (ResultStage.SCORE_TO_ANSWER, HomeStatus.CONFIRM_THE_RESULT),
        (ResultStage.CONFIRMED, HomeStatus.COUNTED),
        (ResultStage.UNSCORED, HomeStatus.UNCOUNTED),
        (ResultStage.NEVER_PLAYED, HomeStatus.NEVER_PLAYED),
        (ResultStage.CALLED_OFF, HomeStatus.CALLED_OFF),
    ],
)
def test_after_we_played_the_result_states_are_todays(stage, status):
    game = a_booked_game()
    result = GameResult(stage=stage, awaits_your_agreement=False)

    assert status_of(game, result, now=warsaw(10, 19)) is status


def test_a_game_whose_result_cannot_be_read_folds_on_the_clock_alone():
    """A booking opens its Game in its own transaction, so a missing one is a
    store that could not be read — the card stays drawn rather than dropped."""

    game = a_booked_game()

    assert status_of(game, None, now=warsaw(5, 8)) is HomeStatus.BOOKED
    assert status_of(game, None, now=warsaw(10, 18)) is HomeStatus.NEEDS_RESULT


# --------------------------------------------------------------------------- #
# What needs the player
# --------------------------------------------------------------------------- #


def test_a_result_to_enter_needs_you():
    assert needs_you(HomeStatus.NEEDS_RESULT, ENTRY_OPEN)


def test_a_score_needs_you_only_when_it_waits_on_your_agreement():
    theirs = GameResult(stage=ResultStage.SCORE_TO_ANSWER, awaits_your_agreement=True)
    yours = GameResult(stage=ResultStage.SCORE_TO_ANSWER, awaits_your_agreement=False)

    assert needs_you(HomeStatus.CONFIRM_THE_RESULT, theirs)
    assert not needs_you(HomeStatus.CONFIRM_THE_RESULT, yours)


def test_a_seat_open_in_your_game_needs_you():
    assert needs_you(HomeStatus.SEAT_OPEN, ENTRY_OPEN)


@pytest.mark.parametrize(
    "status",
    [
        HomeStatus.WAITING_FOR_THE_CLUB,
        HomeStatus.BOOKED,
        HomeStatus.COUNTED,
        HomeStatus.UNCOUNTED,
        HomeStatus.NEVER_PLAYED,
        HomeStatus.CALLED_OFF,
    ],
)
def test_nothing_else_needs_you(status):
    assert not needs_you(status, ENTRY_OPEN)


# --------------------------------------------------------------------------- #
# Which cards Home sends (#613)
# --------------------------------------------------------------------------- #

LIVE = (
    HomeStatus.WAITING_FOR_THE_CLUB,
    HomeStatus.WAITING_FOR_A_PAYMENT,
    HomeStatus.BOOKED,
    HomeStatus.SEAT_OPEN,
    HomeStatus.NEEDS_RESULT,
    HomeStatus.CONFIRM_THE_RESULT,
)
ENDED = (
    HomeStatus.COUNTED,
    HomeStatus.UNCOUNTED,
    HomeStatus.NEVER_PLAYED,
    HomeStatus.CALLED_OFF,
)


def a_state(status: HomeStatus, *, needs: bool = False) -> BookedState:
    return BookedState(
        status=status,
        needs_you=needs,
        money=BookedMoney(
            share_grosze=30_00,
            paid=True,
            free_to_leave_until=None,
        ),
    )


def test_every_status_is_live_or_ended():
    assert set(LIVE) | set(ENDED) == set(HomeStatus)


@pytest.mark.parametrize("status", LIVE)
def test_a_live_card_is_never_shelved(status):
    """Only an ended card leaves with time: a live one is sent for as long as
    the read finds it — which is from ``on_home_since`` on."""

    assert on_home(a_booked_game(), a_state(status), now=warsaw(31, 17))


@pytest.mark.parametrize("status", ENDED)
def test_an_ended_game_is_sent_until_a_day_after_its_hour_ends(status):
    game = a_booked_game()

    assert on_home(game, a_state(status), now=warsaw(11, 17, 59))
    assert not on_home(game, a_state(status), now=warsaw(11, 18))


def test_an_ended_game_that_needs_you_is_sent_past_its_day():
    """Story S-33's case (F-HOME-6.1): a report of not coming the reader may
    still dispute, on an *uncounted* card."""

    game = a_booked_game()
    disputable = a_state(HomeStatus.UNCOUNTED, needs=True)

    assert on_home(game, disputable, now=warsaw(12, 17, 59))


def test_home_reads_from_the_earliest_hour_a_game_can_still_ask_anything():
    """A game at Saturday 17:00: its entry closes Sunday 18:00, and a score made
    then waits — as a report made then can be disputed — until Monday 18:00."""

    assert on_home_since(warsaw(12, 18)) == warsaw(10, 17)


def test_home_reads_from_before_any_ended_card_the_phone_still_draws():
    now = warsaw(12, 18)
    since = on_home_since(now)
    game = a_booked_game(start=since - timedelta(minutes=1))

    assert not any(on_home(game, a_state(status), now=now) for status in ENDED)


def test_a_score_still_waits_if_it_was_put_on_the_table_inside_the_last_day():
    """Only such a score reaches further back than Home reads — a correction
    re-dates its side's, and may be made again while the other side has not
    answered."""

    assert scores_still_waiting_since(warsaw(13, 12)) == warsaw(12, 12)


# --------------------------------------------------------------------------- #
# The money line
# --------------------------------------------------------------------------- #


def test_before_the_cut_off_the_share_is_held_and_free_to_leave():
    """*30 zł · free to leave until Fri 17:00* (#637, Q113): the share is held
    on the card and taken at the cut-off, and nothing is paid until then."""

    money = money_of(a_booked_game(), now=warsaw(5, 8))

    assert money.share_grosze == 30_00
    assert money.paid is False
    assert money.share_state is ShareState.HELD
    assert money.taken_at == warsaw(9, 17)
    assert money.free_to_leave_until == warsaw(9, 17)
    assert money.refunded_grosze is None


def test_from_the_cut_off_on_the_share_is_taken_and_paid():
    money = money_of(a_booked_game(), now=warsaw(9, 17))

    assert money.paid
    assert money.share_state is ShareState.TAKEN
    assert money.taken_at == warsaw(9, 17)
    assert money.free_to_leave_until is None


def test_a_game_booked_after_its_cut_off_was_taken_when_it_was_booked():
    game = replace(a_booked_game(), booked_at=warsaw(9, 20))

    money = money_of(game, now=warsaw(10, 9))

    assert (money.paid, money.share_state) == (True, ShareState.TAKEN)
    assert money.taken_at == warsaw(9, 20)
    assert money.free_to_leave_until is None


@pytest.mark.parametrize(
    "stage", [BookingStage.BOOKED, BookingStage.SEAT_OPEN], ids=["booked", "seat"]
)
def test_before_the_cut_off_leaving_quotes_nothing_since_nothing_is_taken(stage):
    """The leave quote is null before the cut-off (#637): the hold is let go,
    and nothing comes back because nothing was taken."""

    game = a_booked_game(stage=stage)
    now = warsaw(5, 8)

    state = state_of(game, ENTRY_OPEN, now=now)
    terms = leave_terms(game, state.status, late_refund=A_BUSINESS_CARD_S, now=now)

    assert terms is not None
    assert terms.kind is Leaving.BEFORE_THE_CUT_OFF
    assert (terms.refund_grosze, terms.card_fee_grosze) == (None, None)


def test_after_the_cut_off_leaving_quotes_the_share_less_exactly_the_fee_kept():
    """*If someone takes your seat, you get 28,43 zł back (30 zł less the 1,57
    zł kept on your payment)* — the reader's own payment's fee (#641)."""

    game = a_booked_game()
    now = warsaw(9, 18)

    state = state_of(game, ENTRY_OPEN, now=now)
    terms = leave_terms(game, state.status, late_refund=A_BUSINESS_CARD_S, now=now)

    assert terms is not None
    assert terms.kind is Leaving.AFTER_THE_CUT_OFF
    assert (terms.refund_grosze, terms.card_fee_grosze) == (28_43, 1_57)


def test_after_the_cut_off_leaving_quotes_no_figure_while_the_fee_is_unknown():
    """Never an estimate (#641): no figure and no clause until the provider
    has said what it kept."""

    game = a_booked_game()
    now = warsaw(9, 18)

    state = state_of(game, ENTRY_OPEN, now=now)
    terms = leave_terms(game, state.status, late_refund=None, now=now)

    assert terms is not None
    assert terms.kind is Leaving.AFTER_THE_CUT_OFF
    assert (terms.refund_grosze, terms.card_fee_grosze) == (None, None)


def test_a_game_short_at_its_cut_off_took_nothing_and_refunds_nothing():
    game = replace(
        a_booked_game(stage=BookingStage.SEAT_OPEN), short_from=warsaw(9, 17)
    )

    money = money_of(game, now=warsaw(9, 18))

    assert (money.paid, money.share_state, money.refunded_grosze) == (
        False,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("cancelled_at", "refunded"),
    [(warsaw(7, 12), None), (warsaw(9, 18), 30_00)],
    ids=["before-the-cut-off", "after-it"],
)
def test_a_club_s_cancel_refunds_only_what_the_cut_off_had_taken(
    cancelled_at, refunded
):
    game = replace(
        a_booked_game(stage=BookingStage.CALLED_OFF),
        called_off=CalledOffReason.CANCELLED_BY_THE_CLUB,
        cancelled_at=cancelled_at,
    )

    money = money_of(game, now=warsaw(9, 20))

    assert (money.paid, money.share_state) == (False, None)
    assert money.refunded_grosze == refunded


# --------------------------------------------------------------------------- #
# The forecast
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("status", "shown"),
    [
        (HomeStatus.BOOKED, True),
        (HomeStatus.NEEDS_RESULT, True),
        (HomeStatus.SEAT_OPEN, False),
        (HomeStatus.WAITING_FOR_THE_CLUB, False),
        (HomeStatus.CONFIRM_THE_RESULT, False),
        (HomeStatus.COUNTED, False),
        (HomeStatus.CALLED_OFF, False),
    ],
)
def test_the_forecast_shows_while_a_full_game_awaits_its_entry(status, shown):
    assert shows_forecast(status) is shown


def test_a_booked_game_names_its_players_side_by_side():
    game = a_booked_game()

    assert game.players == (OLA, KUBA, EWA, TOMEK)
    assert game.has_a_seat_for(EWA)
    assert not game.has_a_seat_for(UUID(int=7))


def test_a_player_reads_their_own_side_first_with_themselves_first_on_it():
    game = a_booked_game()

    assert game.seen_by(KUBA).yours == (KUBA, OLA)
    assert game.seen_by(KUBA).theirs == (EWA, TOMEK)
    assert game.seen_by(TOMEK).yours == (TOMEK, EWA)
    assert game.seen_by(TOMEK).theirs == (OLA, KUBA)


# --------------------------------------------------------------------------- #
# Waiting for the club, and called off by it (#543)
# --------------------------------------------------------------------------- #


def a_request(**changes) -> BookedGame:
    """The same game, put to an On request club: no Game yet."""

    return a_booked_game(
        game_id=None, stage=BookingStage.WAITING_FOR_THE_CLUB, **changes
    )


def test_a_game_its_club_has_not_answered_is_waiting_and_nobody_paid():
    game = a_request()

    assert status_of(game, None, now=warsaw(5, 8)) is HomeStatus.WAITING_FOR_THE_CLUB
    money = money_of(game, now=warsaw(5, 8))
    assert (
        money.paid,
        money.free_to_leave_until,
        money.share_state,
    ) == (False, None, None)
    assert game.court_given is False
    assert needs_you(HomeStatus.WAITING_FOR_THE_CLUB, None) is False


@pytest.mark.parametrize(
    "reason",
    [CalledOffReason.REFUSED, CalledOffReason.NO_ANSWER],
)
def test_a_request_turned_down_or_withdrawn_is_called_off_with_nobody_paid(reason):
    game = a_booked_game(game_id=None, stage=BookingStage.CALLED_OFF, called_off=reason)

    assert status_of(game, None, now=warsaw(5, 8)) is HomeStatus.CALLED_OFF
    assert money_of(game, now=warsaw(5, 8)).paid is False
    assert game.court_given is False


def test_a_waiting_game_says_when_its_club_must_answer_until_that_moment():
    """*Bonarka answers by 08:30* — and from 08:30 on, when the club can no
    longer say yes, only *nobody pays until Bonarka confirms* (Q98)."""

    game = a_request(answer_by=warsaw(5, 8, 30))

    before = state_of(game, None, now=warsaw(5, 8))
    at = state_of(game, None, now=warsaw(5, 8, 30))

    assert before.answer_by == warsaw(5, 8, 30)
    assert at.answer_by is None


@pytest.mark.parametrize(
    "answered",
    [
        a_booked_game(answer_by=warsaw(5, 8, 30)),
        a_booked_game(
            game_id=None,
            stage=BookingStage.CALLED_OFF,
            called_off=CalledOffReason.REFUSED,
            answer_by=warsaw(5, 8, 30),
        ),
    ],
    ids=["accepted", "refused"],
)
def test_a_game_its_club_answered_keeps_its_deadline_off_the_line(answered):
    state = state_of(answered, None, now=warsaw(5, 8))

    assert state.answer_by is None


def test_a_game_its_club_accepted_is_booked_on_the_court_it_gave():
    game = a_booked_game()

    assert game.stage is BookingStage.BOOKED
    assert game.court_given is True
    # Held until the cut-off, taken at it (#637).
    assert money_of(game, now=warsaw(5, 8)).share_state is ShareState.HELD
    assert money_of(game, now=warsaw(9, 17)).paid is True


# --------------------------------------------------------------------------- #
# A full game that went back to filling (#624, Q106)
# --------------------------------------------------------------------------- #

ANIA = uuid4()


def a_game_filling_again(**changes) -> BookedGame:
    """The same game at an On request club, whose request was taken back when
    Kuba left: the others keep their places, nobody paid, and there is no Game."""

    fields = dict(
        game_id=None,
        stage=BookingStage.FILLING_AGAIN,
        first_side=(OLA,),
        second_side=(EWA, TOMEK),
        answer_by=warsaw(5, 8, 30),
    )
    fields.update(changes)
    return a_booked_game(**fields)


def test_a_full_game_that_fell_back_is_seat_open_and_nobody_paid():
    game = as_filling_again(
        a_game_filling_again(), in_=(OLA, EWA, TOMEK), standing=Standing.FILLING
    )

    state = state_of(game, None, now=warsaw(5, 9))

    assert game.filling_again is True
    assert (state.status, state.called_off, state.answer_by) == (
        HomeStatus.SEAT_OPEN,
        None,
        None,
    )
    assert game.open_seats == 1
    assert (
        state.money.paid,
        state.money.free_to_leave_until,
        state.money.share_state,
        state.money.refunded_grosze,
    ) == (False, None, None, None)
    # It asks nothing of those still In: Home's badge does not count it.
    assert state.needs_you is False


def test_a_game_that_fell_back_asks_its_club_again_when_it_is_full():
    game = as_filling_again(
        a_game_filling_again(), in_=(OLA, EWA, TOMEK), standing=Standing.FILLING
    )

    assert game.club_confirms is True
    assert a_booked_game(answer_by=None).club_confirms is False


def test_somebody_in_since_it_fell_back_takes_the_first_place_free():
    game = as_filling_again(
        a_game_filling_again(first_side=(OLA,), second_side=(EWA,)),
        in_=(OLA, EWA, ANIA),
        standing=Standing.FILLING,
    )

    assert (game.first_side, game.second_side) == ((OLA, ANIA), (EWA,))
    assert game.open_seats == 1


def test_a_player_who_took_their_yes_back_since_is_off_its_sides():
    game = as_filling_again(
        a_game_filling_again(), in_=(OLA, EWA), standing=Standing.FILLING
    )

    assert (game.first_side, game.second_side) == ((OLA,), (EWA,))
    assert game.open_seats == 2
    assert not game.has_a_seat_for(TOMEK)


@pytest.mark.parametrize(
    ("standing", "reason"),
    [
        (Standing.EXPIRED, CalledOffReason.BOOK_BY_PASSED),
        (Standing.COURT_HOUR_LOST, CalledOffReason.COURT_HOUR_LOST),
    ],
)
def test_a_game_that_fell_back_and_ended_first_is_called_off_nobody_paid(
    standing, reason
):
    game = as_filling_again(
        a_game_filling_again(), in_=(OLA, EWA, TOMEK), standing=standing
    )

    state = state_of(game, None, now=warsaw(10, 16))

    assert (state.status, state.called_off) == (HomeStatus.CALLED_OFF, reason)
    assert (state.money.paid, state.money.refunded_grosze) == (False, None)
    assert state.needs_you is False
    assert game.open_seats == 0


def test_a_game_that_fell_back_has_no_leave_of_its_own():
    """Its way out is the one a game still filling has: *Withdraw*, free."""

    game = as_filling_again(
        a_game_filling_again(), in_=(OLA, EWA, TOMEK), standing=Standing.FILLING
    )

    assert (
        leave_terms(
            game, HomeStatus.SEAT_OPEN, late_refund=A_BUSINESS_CARD_S, now=warsaw(5, 9)
        )
        is None
    )


# --------------------------------------------------------------------------- #
# Waiting for one payment (#625, #626; Q111)
# --------------------------------------------------------------------------- #


def a_game_waiting_for_a_payment(**changes) -> BookedGame:
    """Tomek's share was refused at the club's yes; he has until 08:40."""

    return a_booked_game(
        **{
            "stage": BookingStage.WAITING_FOR_A_PAYMENT,
            "game_id": None,
            "answer_by": warsaw(5, 8, 30),
            "paying": {TOMEK: warsaw(5, 8, 40)},
            **changes,
        }
    )


def test_a_game_waiting_for_a_payment_is_its_own_status_and_asks_nothing():
    state = state_of(a_game_waiting_for_a_payment(), None, now=warsaw(5, 8, 10))

    assert state.status is HomeStatus.WAITING_FOR_A_PAYMENT
    assert state.pay_by == warsaw(5, 8, 40)
    # The club answered: no *answers by*; and nobody paid.
    assert state.answer_by is None
    assert state.money.paid is False
    assert state.money.free_to_leave_until is None
    assert state.needs_you is False


def test_leaving_a_game_waiting_for_a_payment_withdraws_the_yes():
    game = a_game_waiting_for_a_payment()
    state = state_of(game, None, now=warsaw(5, 8, 10))

    terms = leave_terms(
        game, state.status, late_refund=A_BUSINESS_CARD_S, now=warsaw(5, 8, 10)
    )

    assert terms is not None
    assert (terms.kind, terms.refund_grosze) == (Leaving.WHILE_WAITING_FOR_THE_CLUB, 0)


def test_a_game_gone_back_to_filling_keeps_the_payer_s_time():
    game = a_booked_game(stage=BookingStage.FILLING_AGAIN, game_id=None)

    folded = as_filling_again(
        game,
        in_=(OLA, EWA, TOMEK),
        standing=Standing.FILLING,
        paying={TOMEK: warsaw(5, 8, 40)},
    )

    assert folded.paying == {TOMEK: warsaw(5, 8, 40)}
    assert status_of(folded, None, now=warsaw(5, 8, 10)) is HomeStatus.SEAT_OPEN


def test_the_club_reads_a_payment_its_yes_waits_on_and_its_lapse_off_the_clock():
    """*Accepted · waiting for one player's payment* — never *waiting for
    you*, the club having answered — and *called off* from the moment the
    payment's time is up, whether or not the job has recorded it (#626)."""

    game = a_game_waiting_for_a_payment()

    # Past the club's own answer window: the club answered, so no *no answer*.
    assert club_status(game, now=warsaw(5, 8, 35)) is ClubStatus.WAITING_FOR_A_PAYMENT
    assert club_status(game, now=warsaw(5, 8, 40)) is ClubStatus.CALLED_OFF
    assert (
        called_off_for_the_club(game, now=warsaw(5, 8, 40))
        is CalledOffReason.PAYMENT_NOT_IN_TIME
    )
