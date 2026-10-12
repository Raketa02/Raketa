"""The club cancels a booked game, whole or with a seat open (#547; the
mechanics §16.9): it is called off by nobody, as the hour calls off a court left
short — and only while the game is still ahead of its hour.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.games.domain.events import GameCalledOff
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.standing import GameStanding
from app.shared.ids import new_uuid

ANA, BO, CY, DEE = (new_uuid() for _ in range(4))
BOOKED_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
STARTS_AT = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))


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
