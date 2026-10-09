"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2, §15.1; the screens A4.1, A8).

**A booked game's status is folded on every read** from the booking, its
ordinary Game's result and the clock — never stored. Booked until its hour; then
the result states, unchanged from today's cards. **The money line** is the share
every seat paid, and — while the club's cut-off is still ahead — until when it
is free to leave. **The forecast** shows while the game awaits its entry, and
**the check-in code** on the game's day, while the game stands.
"""

from __future__ import annotations

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
    ResultStage,
    check_in_shown,
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
    """Saturday 10 October at 17:00, 30 zł a seat, free to leave until Friday
    17:00."""

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
        money=BookedMoney(share_grosze=30_00, paid=True, free_to_leave_until=None),
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


def test_before_the_cut_off_the_share_is_paid_and_free_to_leave_until_it():
    money = money_of(a_booked_game(), now=warsaw(5, 8))

    assert money.share_grosze == 30_00
    assert money.paid
    assert money.free_to_leave_until == warsaw(9, 17)


def test_from_the_cut_off_on_it_is_only_paid():
    money = money_of(a_booked_game(), now=warsaw(9, 17))

    assert money.paid
    assert money.free_to_leave_until is None


def test_a_game_that_filled_inside_its_cut_off_was_never_free_to_leave():
    game = a_booked_game(cut_off=warsaw(9, 17))

    assert money_of(game, now=warsaw(10, 9)).free_to_leave_until is None


# --------------------------------------------------------------------------- #
# The forecast and the check-in code
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


def test_the_check_in_code_shows_on_the_game_day_only():
    start = warsaw(10, 17)

    assert check_in_shown(HomeStatus.BOOKED, start=start, now=warsaw(10, 6))
    assert check_in_shown(HomeStatus.NEEDS_RESULT, start=start, now=warsaw(10, 18))
    assert not check_in_shown(HomeStatus.BOOKED, start=start, now=warsaw(9, 23, 59))
    assert not check_in_shown(
        HomeStatus.NEEDS_RESULT, start=start, now=warsaw(11, 0, 1)
    )


@pytest.mark.parametrize(
    "status", [HomeStatus.WAITING_FOR_THE_CLUB, HomeStatus.CALLED_OFF]
)
def test_a_game_that_does_not_stand_has_no_check_in_code(status):
    start = warsaw(10, 17)

    assert not check_in_shown(status, start=start, now=warsaw(10, 9))


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
    assert (money.paid, money.free_to_leave_until) == (False, None)
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
    shown = check_in_shown(HomeStatus.CALLED_OFF, start=game.start, now=game.start)
    assert shown is False


def test_a_waiting_game_says_when_its_club_must_answer_until_that_moment():
    """*Bonarka answers by 08:30* — and from 08:30 on, when the club can no
    longer say yes, only *nobody pays until Bonarka confirms* (Q98)."""

    game = a_request(answer_by=warsaw(5, 8, 30))

    assert state_of(game, None, now=warsaw(5, 8)).answer_by == warsaw(5, 8, 30)
    assert state_of(game, None, now=warsaw(5, 8, 30)).answer_by is None


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
    assert state_of(answered, None, now=warsaw(5, 8)).answer_by is None


def test_a_game_its_club_accepted_is_booked_on_the_court_it_gave():
    game = a_booked_game()

    assert game.stage is BookingStage.BOOKED
    assert game.court_given is True
    assert money_of(game, now=warsaw(5, 8)).paid is True
