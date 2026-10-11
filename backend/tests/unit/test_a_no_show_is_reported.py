"""Somebody did not turn up to a booked game (#547; the mechanics §15.3, §15.4,
§19).

**The players who came say so where they would enter the result** — *Kuba
didn't come* — and Kuba has **twenty-four hours to dispute it**; after that it
stands. Nothing at a club's desk is asked: desk check-in is removed (#651).
**The game does not count**, nobody's Level moves,
and a no-show that stood is the strongest mark on a record. **A dispute is not
arbitrated**: the report falls, and a game nobody agrees about is an evening
that proves nothing — uncounted, on nobody's record.

And **the club cancels a booked game** whole or with a seat open: it is called
off by nobody, as the hour calls off a court left short.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.games.domain.errors import (
    ANoShowIsReported,
    AResultIsAlreadyEntered,
    NobodyReportedYou,
    NoShowsAreForBookedGames,
    NotOnThisCourt,
    TheDisputeWindowHasClosed,
    TheEntryWindowHasClosed,
    TheGameHasNotStarted,
    TheResultIsSettled,
    YouCannotReportYourself,
    YouWereNotOnThisCourt,
    YouWereReportedAsANoShow,
)
from app.modules.games.domain.events import (
    GameCalledOff,
    NoShowDisputed,
    NoShowReported,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import NO_SHOW_DISPUTE_WINDOW
from app.shared.ids import new_uuid

ANA, BO, CY, DEE, EVE = (new_uuid() for _ in range(5))
BOOKED_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
STARTS_AT = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))
#: Back home after the game, entering the result.
AFTER = instant(STARTS_AT + timedelta(hours=2))


def _game(*, starts_at=STARTS_AT) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=ANA),
                Seating(side=GameSide.A, player_id=BO),
                Seating(side=GameSide.B, player_id=CY),
                Seating(side=GameSide.B, player_id=DEE),
            )
        ),
        occurred_at=BOOKED_AT,
        starts_at=starts_at,
    )


def _reported(game: Game, absent=BO, *, by=ANA, at=AFTER) -> None:
    game.report_no_show(by=by, absent=absent, occurred_at=at)


def _score() -> Score:
    return Score.of((SetScore(a=6, b=3), SetScore(a=6, b=4)))


def _replayed(game: Game) -> Game:
    return Game.from_history(game.pull_events())


# --------------------------------------------------------------------------- #
# The report, and its day
# --------------------------------------------------------------------------- #


def test_a_player_who_came_reports_one_who_did_not_and_it_waits_out_its_day():
    game = _game()

    _reported(game)

    assert game.standing_at(AFTER) is GameStanding.NO_SHOW_REPORTED
    assert GameStanding.NO_SHOW_REPORTED not in SETTLED
    assert GameStanding.NO_SHOW_REPORTED not in PLAYED
    assert game.confirmed_no_shows_at(AFTER) == frozenset()
    *_, event = game.pull_events()
    assert isinstance(event, NoShowReported)
    assert (event.player_id, event.reported_by) == (BO, ANA)


def test_a_report_nobody_disputes_in_its_day_stands_and_the_game_does_not_count():
    game = _game()
    _reported(game)
    stands_at = instant(AFTER + NO_SHOW_DISPUTE_WINDOW)

    assert NO_SHOW_DISPUTE_WINDOW == timedelta(hours=24)
    replayed = _replayed(game)
    assert (
        replayed.standing_at(stands_at - timedelta(seconds=1))
        is GameStanding.NO_SHOW_REPORTED
    )
    assert replayed.standing_at(stands_at) is GameStanding.NO_SHOW
    assert GameStanding.NO_SHOW in SETTLED
    assert GameStanding.NO_SHOW not in PLAYED
    assert replayed.confirmed_no_shows_at(stands_at) == frozenset({BO})
    assert replayed.confirmed_score_at(stands_at) is None
    assert replayed.outcome_for(ANA, now=stands_at) is None
    assert replayed.became_history_at(stands_at) == AFTER


def test_a_dispute_in_the_day_brings_the_report_down_and_nobody_arbitrates():
    game = _game()
    _reported(game)
    disputed_at = instant(AFTER + timedelta(hours=3))

    game.dispute_no_show(by=BO, occurred_at=disputed_at)

    later = instant(AFTER + timedelta(days=3))
    assert game.standing_at(disputed_at) is GameStanding.UNSCORED
    assert GameStanding.UNSCORED in PLAYED
    assert game.confirmed_no_shows_at(later) == frozenset()
    assert game.became_history_at(later) == AFTER
    *_, event = game.pull_events()
    assert isinstance(event, NoShowDisputed)
    assert event.player_id == BO


def test_a_dispute_after_the_day_is_too_late_and_one_by_anybody_else_is_nobody_s():
    game = _game()
    _reported(game)

    with pytest.raises(NobodyReportedYou):
        game.dispute_no_show(by=CY, occurred_at=AFTER + timedelta(hours=1))
    with pytest.raises(TheDisputeWindowHasClosed):
        game.dispute_no_show(by=BO, occurred_at=AFTER + NO_SHOW_DISPUTE_WINDOW)


def test_a_second_dispute_writes_nothing():
    game = _game()
    _reported(game)
    game.dispute_no_show(by=BO, occurred_at=AFTER + timedelta(hours=1))
    game.pull_events()

    game.dispute_no_show(by=BO, occurred_at=AFTER + timedelta(hours=2))

    assert game.pull_events() == []


def test_in_doubles_two_may_not_have_come_and_each_report_has_its_own_day():
    game = _game()
    _reported(game, BO, by=ANA)
    _reported(game, CY, by=ANA, at=AFTER + timedelta(hours=1))
    game.dispute_no_show(by=CY, occurred_at=AFTER + timedelta(hours=2))

    bo_stands = instant(AFTER + NO_SHOW_DISPUTE_WINDOW)
    assert game.standing_at(bo_stands) is GameStanding.NO_SHOW
    assert game.confirmed_no_shows_at(bo_stands) == frozenset({BO})


def test_the_game_is_settled_only_once_every_report_has_had_its_day():
    game = _game()
    _reported(game, BO, by=ANA)
    _reported(game, CY, by=ANA, at=AFTER + timedelta(hours=1))

    bo_stands = instant(AFTER + NO_SHOW_DISPUTE_WINDOW)
    # Cy's day still runs: they may still dispute.
    assert game.standing_at(bo_stands) is GameStanding.NO_SHOW_REPORTED
    game.dispute_no_show(by=CY, occurred_at=bo_stands)
    assert game.standing_at(bo_stands) is GameStanding.NO_SHOW


def test_only_the_reported_player_may_dispute_and_only_inside_their_own_day():
    game = _game()
    _reported(game, BO, by=ANA)
    _reported(game, CY, by=ANA, at=AFTER + timedelta(hours=3))
    bo_s_day_over = instant(AFTER + NO_SHOW_DISPUTE_WINDOW)

    assert game.may_dispute(BO, now=AFTER) is True
    assert game.may_dispute(ANA, now=AFTER) is False
    # Cy's day still runs, and the game waits for it; Bo's is over.
    assert game.standing_at(bo_s_day_over) is GameStanding.NO_SHOW_REPORTED
    assert game.may_dispute(BO, now=bo_s_day_over) is False
    assert game.may_dispute(CY, now=bo_s_day_over) is True
    game.dispute_no_show(by=CY, occurred_at=bo_s_day_over)
    assert game.may_dispute(CY, now=bo_s_day_over) is False


def test_reporting_somebody_twice_writes_nothing():
    game = _game()
    _reported(game, BO, by=ANA)
    game.pull_events()

    _reported(game, BO, by=CY, at=AFTER + timedelta(minutes=5))

    assert game.pull_events() == []


# --------------------------------------------------------------------------- #
# Who may be reported, by whom, and when
# --------------------------------------------------------------------------- #


def test_only_the_people_on_the_court_report_and_only_each_other():
    game = _game()

    with pytest.raises(YouWereNotOnThisCourt):
        _reported(game, BO, by=EVE)
    with pytest.raises(NotOnThisCourt):
        _reported(game, EVE, by=ANA)
    with pytest.raises(YouCannotReportYourself):
        _reported(game, ANA, by=ANA)


def test_a_player_reported_disputes_rather_than_reports_back():
    game = _game()
    _reported(game, BO, by=ANA)

    with pytest.raises(YouWereReportedAsANoShow):
        _reported(game, ANA, by=BO, at=AFTER + timedelta(minutes=1))


def test_nobody_is_reported_before_the_hour_or_after_the_entry_window():
    game = _game()

    with pytest.raises(TheGameHasNotStarted):
        _reported(game, at=STARTS_AT - timedelta(minutes=1))
    with pytest.raises(TheEntryWindowHasClosed):
        _reported(game, at=game.entry_closes_at)


def test_a_no_show_is_a_booked_game_s_and_never_one_a_line_up_opened():
    game = _game(starts_at=None)

    with pytest.raises(NoShowsAreForBookedGames):
        _reported(game)


def test_a_score_and_a_report_never_stand_on_one_game():
    scored = _game()
    scored.state_result(by=ANA, score=_score(), occurred_at=AFTER)
    with pytest.raises(AResultIsAlreadyEntered):
        _reported(scored, at=AFTER + timedelta(minutes=1))

    reported = _game()
    _reported(reported)
    with pytest.raises(ANoShowIsReported):
        reported.state_result(
            by=CY, score=_score(), occurred_at=AFTER + timedelta(minutes=1)
        )
    stands_at = instant(AFTER + NO_SHOW_DISPUTE_WINDOW)
    with pytest.raises(TheResultIsSettled):
        reported.state_result(by=CY, score=_score(), occurred_at=stands_at)
    with pytest.raises(TheResultIsSettled):
        _reported(reported, CY, by=ANA, at=stands_at)


# --------------------------------------------------------------------------- #
# The club cancels the booked game
# --------------------------------------------------------------------------- #


def test_the_club_s_cancel_calls_a_whole_booked_game_off_by_nobody():
    game = _game()
    cancelled_at = instant(STARTS_AT - timedelta(days=1))

    game.call_off_whole(occurred_at=cancelled_at)

    assert game.standing_at(cancelled_at) is GameStanding.CALLED_OFF
    assert game.called_off_by is None
    *_, event = game.pull_events()
    assert isinstance(event, GameCalledOff)


def test_only_a_booked_game_still_ahead_of_its_hour_is_cancelled():
    with pytest.raises(InvariantViolated):
        _game(starts_at=None).call_off_whole(occurred_at=BOOKED_AT)
    with pytest.raises(InvariantViolated):
        _game().call_off_whole(occurred_at=STARTS_AT)
