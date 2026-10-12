"""A booked game whose hour comes with a seat open (#544; the mechanics §14.1,
§19): somebody left after the club's cut-off and nobody took the seat, so the
game went ahead short. **It cannot take a result, and it ends uncounted — a
seat was empty**: no Level moves, and it is not an evening the players had, so
it is in no tally.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.games.domain.errors import (
    TheGameIsNotOpenToSeating,
    TheGameStartedShort,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.shared.ids import new_uuid

ANA, BO, CY, DEE, EVE = (new_uuid() for _ in range(5))
BOOKED_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
STARTS_AT = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))


def _booked_game() -> Game:
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
        starts_at=STARTS_AT,
    )


def _score() -> Score:
    return Score.of((SetScore(a=6, b=3), SetScore(a=6, b=4)))


def test_a_booked_game_with_a_seat_open_at_its_hour_started_short():
    game = _booked_game()
    game.vacate(CY, occurred_at=STARTS_AT - timedelta(hours=2))

    assert (
        game.standing_at(STARTS_AT - timedelta(seconds=1))
        is GameStanding.AWAITING_ENTRY
    )
    assert game.standing_at(STARTS_AT) is GameStanding.STARTED_SHORT
    assert GameStanding.STARTED_SHORT in SETTLED
    assert GameStanding.STARTED_SHORT not in PLAYED
    assert game.became_history_at(STARTS_AT + timedelta(hours=3)) == STARTS_AT


def test_a_game_that_started_short_takes_no_result_and_no_newcomer():
    game = _booked_game()
    game.vacate(CY, occurred_at=STARTS_AT - timedelta(hours=2))

    with pytest.raises(TheGameStartedShort):
        game.state_result(
            by=ANA, score=_score(), occurred_at=STARTS_AT + timedelta(hours=1)
        )
    with pytest.raises(TheGameIsNotOpenToSeating):
        game.vacate(DEE, occurred_at=STARTS_AT + timedelta(minutes=5))


def test_a_whole_booked_game_awaits_its_entry_past_its_hour_as_today():
    game = _booked_game()

    assert (
        game.standing_at(STARTS_AT + timedelta(hours=2)) is GameStanding.AWAITING_ENTRY
    )
