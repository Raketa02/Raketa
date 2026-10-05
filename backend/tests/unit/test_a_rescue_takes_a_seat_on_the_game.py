"""A rescue takes an open seat on a booked game's court (#545; the mechanics
§10.1, §14.3). **The court now is the court with them on it** — the same
``LineUpReseated`` a completed line-up arriving writes, so the room, whose
members are the line-up, takes them in and the stream reads find them on the
court — but one seat at a time: a doubles that lost two players is short of
one after the first rescue.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.games.domain.errors import (
    TheGameIsNotOpenToSeating,
    YouWereNotOnThisCourt,
)
from app.modules.games.domain.events import LineUpReseated
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.standing import GameStanding
from app.shared.ids import new_uuid

ANA, BO, CY, DEE, EVE, FAY = (new_uuid() for _ in range(6))
BOOKED_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
STARTS_AT = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))
BEFORE = STARTS_AT - timedelta(hours=3)


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


def test_a_rescue_sits_on_the_open_seat_of_its_side_and_the_court_is_whole():
    game = _booked_game()
    game.vacate(CY, occurred_at=BEFORE)
    game.pull_events()

    game.take_seat(EVE, side=GameSide.B, occurred_at=BEFORE + timedelta(minutes=5))

    assert game.line_up.is_complete
    assert game.line_up.side_of(EVE) is GameSide.B
    assert game.line_up.side_of(CY) is None
    [event] = game.pull_events()
    assert isinstance(event, LineUpReseated)
    assert game.standing_at(STARTS_AT) is GameStanding.AWAITING_ENTRY


def test_one_rescue_of_two_open_seats_leaves_the_court_short_of_one():
    game = _booked_game()
    game.vacate(BO, occurred_at=BEFORE)
    game.vacate(CY, occurred_at=BEFORE)

    game.take_seat(EVE, side=GameSide.A, occurred_at=BEFORE)

    assert not game.line_up.is_complete
    assert game.line_up.players_on(GameSide.A) == frozenset({ANA, EVE})
    game.take_seat(FAY, side=GameSide.B, occurred_at=BEFORE)
    assert game.line_up.is_complete
    # Nothing was pulled yet: the whole stream, from its opening.
    replayed = Game.from_history(game.pull_events())
    assert replayed.line_up == game.line_up


def test_a_seat_is_taken_only_on_a_side_with_one_open():
    game = _booked_game()
    game.vacate(CY, occurred_at=BEFORE)

    with pytest.raises(InvariantViolated):
        game.take_seat(EVE, side=GameSide.A, occurred_at=BEFORE)
    with pytest.raises(InvariantViolated):
        game.take_seat(ANA, side=GameSide.B, occurred_at=BEFORE)


def test_no_seat_is_taken_on_a_game_that_is_no_longer_ahead():
    game = _booked_game()
    game.vacate(CY, occurred_at=BEFORE)

    with pytest.raises(TheGameIsNotOpenToSeating):
        game.take_seat(EVE, side=GameSide.B, occurred_at=STARTS_AT)


def test_the_rescue_may_act_on_the_court_and_the_leaver_may_not():
    game = _booked_game()
    game.vacate(CY, occurred_at=BEFORE)
    game.take_seat(EVE, side=GameSide.B, occurred_at=BEFORE)

    assert EVE in game.line_up.players
    with pytest.raises(YouWereNotOnThisCourt):
        game.dismiss(by=CY, occurred_at=STARTS_AT)
