"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2; the screens A4.1, A8).

**A booked game's status is folded on every read** from the booking, its
ordinary Game's result and the clock — never stored. Booked until its hour; then
the result states, unchanged from today's cards. **The money line** is the share
every seat holds until the club's cut-off and takes at it — *free to leave
until* then, *Paid* from it on (#637). **The forecast** shows while
the game awaits its entry. **A full game waiting for one payment** has no
booking — it is read off its proposal — and is *Waiting for one payment*, then
*Seat open* once it went back to filling (#625, Q106).
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
    leave_terms,
    money_of,
    needs_you,
    on_home,
    on_home_since,
    shows_forecast,
    state_of,
    status_of,
)

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
        (ResultStage.DISPUTED, HomeStatus.UNCOUNTED),
        (ResultStage.NOT_HERE_YET, HomeStatus.NEEDS_RESULT),
        (ResultStage.DIDNT_COME, HomeStatus.UNCOUNTED),
        (ResultStage.PLAYED_NO_SCORE, HomeStatus.PLAYED_NO_SCORE),
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
    assert needs_you(HomeStatus.NEEDS_RESULT, ENTRY_OPEN, kind=SearchMode.COMPETITIVE)


def test_a_score_needs_you_only_when_it_waits_on_your_agreement():
    theirs = GameResult(stage=ResultStage.SCORE_TO_ANSWER, awaits_your_agreement=True)
    yours = GameResult(stage=ResultStage.SCORE_TO_ANSWER, awaits_your_agreement=False)

    assert needs_you(HomeStatus.CONFIRM_THE_RESULT, theirs, kind=SearchMode.COMPETITIVE)
    assert not needs_you(
        HomeStatus.CONFIRM_THE_RESULT, yours, kind=SearchMode.COMPETITIVE
    )


def test_a_for_fun_game_past_its_hour_with_no_score_needs_nobody():
    """For fun asks nothing (#654): a score may be added, and none is owed."""

    assert not needs_you(HomeStatus.NEEDS_RESULT, ENTRY_OPEN, kind=SearchMode.FOR_FUN)


def test_a_seat_open_in_your_game_needs_you():
    assert needs_you(HomeStatus.SEAT_OPEN, ENTRY_OPEN, kind=SearchMode.COMPETITIVE)


def test_a_game_somebody_didn_t_come_to_needs_whoever_a_late_claim_waits_on():
    """Their own *I was there* to say, or somebody else's to confirm (#657)."""

    waits = GameResult(
        stage=ResultStage.DIDNT_COME,
        awaits_your_agreement=False,
        attendance_waits_on_you=True,
    )
    done = replace(waits, attendance_waits_on_you=False)

    assert needs_you(HomeStatus.UNCOUNTED, waits, kind=SearchMode.COMPETITIVE)
    assert not needs_you(HomeStatus.UNCOUNTED, done, kind=SearchMode.COMPETITIVE)


def test_while_somebody_is_not_here_yet_only_they_are_needed():
    """No score is taken while somebody is awaited, so the court is asked for
    nothing — the player awaited is asked for *I'm here* (#657)."""

    awaited = GameResult(
        stage=ResultStage.NOT_HERE_YET,
        awaits_your_agreement=False,
        attendance_waits_on_you=True,
    )
    present = replace(awaited, attendance_waits_on_you=False)

    assert needs_you(HomeStatus.NEEDS_RESULT, awaited, kind=SearchMode.COMPETITIVE)
    assert not needs_you(HomeStatus.NEEDS_RESULT, present, kind=SearchMode.COMPETITIVE)


@pytest.mark.parametrize(
    "status",
    [
        HomeStatus.BOOKED,
        HomeStatus.COUNTED,
        HomeStatus.UNCOUNTED,
        HomeStatus.PLAYED_NO_SCORE,
        HomeStatus.CALLED_OFF,
    ],
)
def test_nothing_else_needs_you(status):
    assert not needs_you(status, ENTRY_OPEN, kind=SearchMode.COMPETITIVE)


# --------------------------------------------------------------------------- #
# Which cards Home sends (#613)
# --------------------------------------------------------------------------- #

LIVE = (
    HomeStatus.WAITING_FOR_A_PAYMENT,
    HomeStatus.BOOKED,
    HomeStatus.SEAT_OPEN,
    HomeStatus.NEEDS_RESULT,
    HomeStatus.CONFIRM_THE_RESULT,
)
ENDED = (
    HomeStatus.COUNTED,
    HomeStatus.UNCOUNTED,
    HomeStatus.PLAYED_NO_SCORE,
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


def test_a_booked_game_is_given_its_court_and_holds_its_shares():
    game = a_booked_game()

    assert game.stage is BookingStage.BOOKED
    assert game.court_given is True
    # Held until the cut-off, taken at it (#637).
    assert money_of(game, now=warsaw(5, 8)).share_state is ShareState.HELD
    assert money_of(game, now=warsaw(9, 17)).paid is True


# --------------------------------------------------------------------------- #
# A full game that went back to filling (#625, Q106)
# --------------------------------------------------------------------------- #


def a_game_filling_again(**changes) -> BookedGame:
    """The same game, full and waiting for Tomek's payment when Kuba left: it
    has no booking, the others keep their places, nobody paid, and there is no
    Game — as its proposal folds it (``without_a_booking``)."""

    fields = dict(
        game_id=None,
        stage=BookingStage.FILLING_AGAIN,
        first_side=(OLA,),
        second_side=(EWA, TOMEK),
    )
    fields.update(changes)
    return a_booked_game(**fields)


def test_a_full_game_that_fell_back_is_seat_open_and_nobody_paid():
    game = a_game_filling_again()

    state = state_of(game, None, now=warsaw(5, 9))

    assert game.filling_again is True
    assert (state.status, state.called_off) == (HomeStatus.SEAT_OPEN, None)
    assert game.open_seats == 1
    assert (
        state.money.paid,
        state.money.free_to_leave_until,
        state.money.share_state,
        state.money.refunded_grosze,
    ) == (False, None, None, None)
    # It asks nothing of those still In: Home's badge does not count it.
    assert state.needs_you is False


@pytest.mark.parametrize(
    "reason",
    [
        CalledOffReason.BOOK_BY_PASSED,
        CalledOffReason.COURT_HOUR_LOST,
        CalledOffReason.PAYMENT_NOT_IN_TIME,
    ],
)
def test_a_game_that_fell_back_and_ended_first_is_called_off_nobody_paid(reason):
    game = a_game_filling_again(called_off=reason)

    state = state_of(game, None, now=warsaw(10, 16))

    assert (state.status, state.called_off) == (HomeStatus.CALLED_OFF, reason)
    assert (state.money.paid, state.money.refunded_grosze) == (False, None)
    assert state.needs_you is False
    assert game.open_seats == 0


def test_a_game_that_fell_back_has_no_leave_of_its_own():
    """Its way out is the one a game still filling has: *Withdraw*, free."""

    game = a_game_filling_again()

    assert (
        leave_terms(
            game, HomeStatus.SEAT_OPEN, late_refund=A_BUSINESS_CARD_S, now=warsaw(5, 9)
        )
        is None
    )


# --------------------------------------------------------------------------- #
# Waiting for one payment (#625; Q111)
# --------------------------------------------------------------------------- #


def a_game_waiting_for_a_payment(**changes) -> BookedGame:
    """Tomek's share was refused as the game filled; he has until 08:40."""

    return a_booked_game(
        **{
            "stage": BookingStage.WAITING_FOR_A_PAYMENT,
            "game_id": None,
            "paying": {TOMEK: warsaw(5, 8, 40)},
            **changes,
        }
    )


def test_a_game_waiting_for_a_payment_is_its_own_status_and_asks_nothing():
    state = state_of(a_game_waiting_for_a_payment(), None, now=warsaw(5, 8, 10))

    assert state.status is HomeStatus.WAITING_FOR_A_PAYMENT
    assert state.pay_by == warsaw(5, 8, 40)
    # Nobody paid.
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
    assert (terms.kind, terms.refund_grosze) == (
        Leaving.WHILE_WAITING_FOR_A_PAYMENT,
        0,
    )


def test_a_game_gone_back_to_filling_keeps_the_payer_s_time():
    game = a_game_filling_again(paying={TOMEK: warsaw(5, 8, 40)})

    state = state_of(game, None, now=warsaw(5, 8, 10))

    assert game.pay_by == warsaw(5, 8, 40)
    assert state.status is HomeStatus.SEAT_OPEN
    # Only *Waiting for one payment* says it: the others read *Seat open*.
    assert state.pay_by is None
