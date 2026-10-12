"""A full booked game nobody recorded was played (#655; ``docs/adr/0195`` §2).

Marta, Ivan, Oscar and Paula play Tuesday 13 October at 19:00 and nobody
records it. When its entry window closes — 20:00 on Wednesday, a day after the
hour's end — the game reads **Played · no score**: an end, played for all four,
with no score, no outcome and no Level. *Never played* retires: every game is
opened by a booking, so there is no unbooked plan left to dissolve.

**Played means full.** A court whose window closes with a seat open is not a
game anybody played: a booked one has already *started short* at its hour, and
a stream with no hour reads the same once its window closes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.games.domain.attendance import ClubVerdict
from app.modules.games.domain.errors import (
    TheEntryWindowHasClosed,
    TheGameIsNotOpenToSeating,
    TheTapWindowHasClosed,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.shared.ids import new_uuid

MARTA, IVAN, OSCAR, PAULA, EVE = (new_uuid() for _ in range(5))
BOOKED_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
#: Tuesday 13 October, 19:00 in Kraków.
STARTS_AT = instant(datetime(2026, 10, 13, 17, tzinfo=timezone.utc))
#: Wednesday 14 October, 20:00 in Kraków — a day after the hour's end.
WEDNESDAY_EIGHT = instant(datetime(2026, 10, 14, 18, tzinfo=timezone.utc))


def _four() -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=MARTA),
            Seating(side=GameSide.A, player_id=IVAN),
            Seating(side=GameSide.B, player_id=OSCAR),
            Seating(side=GameSide.B, player_id=PAULA),
        )
    )


def _booked(kind: GameKind = GameKind.COUNTED) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=kind,
        window=None,
        line_up=_four(),
        occurred_at=BOOKED_AT,
        starts_at=STARTS_AT,
    )


def _score() -> Score:
    return Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3)))


def test_its_window_closing_on_nobody_reads_played_no_score():
    game = _booked()

    assert game.entry_closes_at == WEDNESDAY_EIGHT
    assert (
        game.standing_at(WEDNESDAY_EIGHT - timedelta(seconds=1))
        is GameStanding.AWAITING_ENTRY
    )
    assert game.standing_at(WEDNESDAY_EIGHT) is GameStanding.PLAYED_NO_SCORE


def test_it_is_an_end_and_an_evening():
    """Settled — nothing more will happen to it — and played: the four were on
    a court together, which every tally reads off ``PLAYED``."""

    game = _booked()

    assert GameStanding.PLAYED_NO_SCORE in SETTLED
    assert GameStanding.PLAYED_NO_SCORE in PLAYED
    assert game.was_played_at(WEDNESDAY_EIGHT)
    assert game.became_history_at(WEDNESDAY_EIGHT) == WEDNESDAY_EIGHT


def test_it_has_no_score_no_outcome_and_nothing_left_in_dispute():
    """**No Level moves**: an evening with no score is not evidence about
    skill, so nothing the rating context reads is on it."""

    game = _booked()

    assert game.confirmed_score_at(WEDNESDAY_EIGHT) is None
    assert game.confirmed_at(WEDNESDAY_EIGHT) is None
    assert game.settled_by_agreement_at(WEDNESDAY_EIGHT) is None
    assert game.left_in_dispute_by(WEDNESDAY_EIGHT) == frozenset()
    assert game.score_put_to_a_side_at(WEDNESDAY_EIGHT) is None
    assert all(
        game.outcome_for(player, now=WEDNESDAY_EIGHT) is None
        for player in game.line_up.players
    )


def test_a_score_after_it_is_told_the_window_has_closed():
    """The end it is does not change the refusal: *we played* was sayable
    until the window closed, and is not now."""

    game = _booked()

    with pytest.raises(TheEntryWindowHasClosed):
        game.state_result(by=MARTA, score=_score(), occurred_at=WEDNESDAY_EIGHT)
    with pytest.raises(TheTapWindowHasClosed):
        game.note_absent(
            by=MARTA,
            absent=OSCAR,
            where=ClubVerdict(at_the_club=True, club_name=None),
            occurred_at=WEDNESDAY_EIGHT,
        )
    assert game.standing_at(WEDNESDAY_EIGHT) is GameStanding.PLAYED_NO_SCORE


def test_a_for_fun_game_nobody_recorded_is_played_no_score_too():
    """For fun asks nothing (#654), so an evening nobody scored is the
    ordinary ending of one."""

    game = _booked(GameKind.FRIENDLY)

    assert game.standing_at(WEDNESDAY_EIGHT) is GameStanding.PLAYED_NO_SCORE


def test_a_court_whose_window_closes_with_a_seat_open_was_not_played():
    """**Played · no score is the end of a full game.** A stream with no hour
    has no moment to start short at, so its window closing finds the seat
    open: it went ahead short — in no tally — and never as played."""

    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=_four(),
        occurred_at=BOOKED_AT,
    )
    game.vacate(OSCAR, occurred_at=instant(BOOKED_AT + timedelta(hours=1)))
    closes = instant(BOOKED_AT + PLAN_HORIZON + ENTRY_GRACE)

    assert (
        game.standing_at(closes - timedelta(seconds=1)) is GameStanding.AWAITING_ENTRY
    )
    assert game.standing_at(closes) is GameStanding.STARTED_SHORT
    assert not game.was_played_at(closes)
    assert game.became_history_at(closes + timedelta(days=3)) == closes
    with pytest.raises(TheGameIsNotOpenToSeating):
        game.take_seat(EVE, side=GameSide.B, occurred_at=closes)
