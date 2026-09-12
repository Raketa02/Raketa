"""Calling a game off — the fourth end, and the one an act reaches (``docs/adr/0163``).

**A game with a seat open can be called off**, and nothing else can. ``call_off``
writes ``GameCalledOff``; the standing reads it **first**, as ``challenges`` reads
``withdrawn_at``; it is an end — settled, and refusing every act — and it is
**neither played nor a ghost**. Driven on the aggregate and on the use case the
withdraw hands over to, with a hand-written repository, because what is under test
is *what the record does* rather than anything about a database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.games.application.call_off_game import CallOffGame
from app.modules.games.application.commands import CallOffGameCommand
from app.modules.games.domain.errors import (
    NotAGameToCallOff,
    TheGameIsNotOpenToSeating,
    TheGameWasCalledOff,
    TheResultIsSettled,
    YouWereNotOnThisCourt,
)
from app.modules.games.domain.events import GameCalledOff
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid

ANA, BO, CY, DEE, EVE = (new_uuid() for _ in range(5))
PLANNED_AT = instant(datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc))


def at(hours: int) -> datetime:
    return instant(PLANNED_AT + timedelta(hours=hours))


def _four(a=ANA, b=BO, c=CY, d=DEE) -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=a),
            Seating(side=GameSide.A, player_id=b),
            Seating(side=GameSide.B, player_id=c),
            Seating(side=GameSide.B, player_id=d),
        )
    )


def _a_game(line_up: LineUp | None = None) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.WEEKEND,
        line_up=line_up or _four(),
        occurred_at=PLANNED_AT,
    )


def _a_reopened_game() -> Game:
    game = _a_game()
    game.vacate(CY, occurred_at=at(1))
    return game


def _score() -> Score:
    return Score.of((SetScore(a=6, b=3), SetScore(a=6, b=4)))


# ---------------------------------------------------------------------------
# The fourth end
# ---------------------------------------------------------------------------


def test_a_game_with_a_seat_open_is_called_off_and_that_is_its_end():
    game = _a_reopened_game()

    game.call_off(by=ANA, occurred_at=at(2))

    assert game.called_off_at == at(2)
    assert game.standing_at(at(2)) is GameStanding.CALLED_OFF
    assert game.standing_at(at(24 * 365)) is GameStanding.CALLED_OFF, (
        "a decision, not a deadline: a year of clock moves nothing"
    )
    event = game.pull_events()[-1]
    assert isinstance(event, GameCalledOff)
    assert (event.game_id, event.called_by, event.occurred_at) == (game.id, ANA, at(2))


def test_called_off_is_read_before_the_clock_as_withdrawn_is_read_before_the_seats():
    """The entry window closing after the act changes nothing: the standing was
    decided by a person, and the fold asks about that first."""

    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )

    assert game.standing_at(past_the_window) is GameStanding.CALLED_OFF
    assert game.was_played_at(past_the_window) is False


def test_called_off_is_settled_and_not_played():
    assert GameStanding.CALLED_OFF in SETTLED
    assert GameStanding.CALLED_OFF not in PLAYED


def test_the_whole_life_replays_into_itself():
    game = _a_reopened_game()
    game.call_off(by=BO, occurred_at=at(2))
    events = game.pull_events()

    rebuilt = Game.from_history(events)

    assert rebuilt.called_off_at == at(2)
    assert rebuilt.standing_at(at(3)) is GameStanding.CALLED_OFF
    assert rebuilt.version == 3
    assert not rebuilt.line_up.is_complete, "the open seat is still on the record"


# ---------------------------------------------------------------------------
# What it refuses
# ---------------------------------------------------------------------------


def test_only_a_court_with_a_seat_open_can_be_called_off():
    """A full court that will not play lets its window lapse into *Never
    played*, as today (#411 rule 4)."""

    whole = _a_game()

    with pytest.raises(NotAGameToCallOff):
        whole.call_off(by=ANA, occurred_at=at(1))
    assert whole.standing_at(at(1)) is GameStanding.AWAITING_ENTRY


def test_a_game_that_has_ended_by_its_clock_cannot_be_called_off():
    """A ghost stays a ghost: a call-off that reached it would flip a standing
    the platform has already drawn, and un-charge a strand after the fact."""

    ghost = _a_reopened_game()
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )
    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED

    with pytest.raises(NotAGameToCallOff):
        ghost.call_off(by=ANA, occurred_at=past_the_window)
    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED


def test_a_game_already_called_off_cannot_be_called_off_again():
    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))

    with pytest.raises(NotAGameToCallOff):
        game.call_off(by=BO, occurred_at=at(3))


def test_only_somebody_on_the_court_can_call_it_off():
    game = _a_reopened_game()

    with pytest.raises(YouWereNotOnThisCourt):
        game.call_off(by=EVE, occurred_at=at(2))
    with pytest.raises(YouWereNotOnThisCourt):
        game.call_off(by=CY, occurred_at=at(2))
    assert game.standing_at(at(2)) is GameStanding.AWAITING_ENTRY


def test_a_called_off_game_refuses_every_act():
    """The entry names the end it met, with its own code, as a ghost's entry
    does; the acceptance meets the umbrella, as it does on a ghost; and nothing
    on the line-up moves."""

    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))

    with pytest.raises(TheGameWasCalledOff):
        game.state_result(by=ANA, score=_score(), occurred_at=at(3))
    with pytest.raises(TheResultIsSettled):
        game.accept_result(by=DEE, occurred_at=at(3))
    with pytest.raises(TheGameIsNotOpenToSeating):
        game.vacate(ANA, occurred_at=at(3))
    with pytest.raises(TheGameIsNotOpenToSeating):
        game.reseat(_four(ANA, BO, EVE, DEE), occurred_at=at(3))
    assert game.outcome_for(ANA, now=at(3)) is None
    assert game.confirmed_score_at(at(3)) is None


# ---------------------------------------------------------------------------
# The hand-over
# ---------------------------------------------------------------------------


class _Remembering:
    def __init__(self, *games: Game) -> None:
        self.games: dict[UUID, Game] = {}
        for game in games:
            game.pull_events()
            self.games[game.id] = game

    async def load(self, game_id: UUID) -> Game | None:
        return self.games.get(game_id)

    async def for_challenge(self, challenge_id: UUID) -> Game | None:
        for game in self.games.values():
            if game.challenge_id == challenge_id:
                return game
        return None

    async def save(self, game: Game) -> None:
        game.pull_events()
        self.games[game.id] = game


async def test_the_withdraw_hands_over_and_the_game_is_called_off():
    game = _a_reopened_game()
    games = _Remembering(game)

    await CallOffGame(games=games).execute(
        CallOffGameCommand(challenge_id=game.challenge_id, called_by=ANA),
        occurred_at=at(2),
    )

    assert game.standing_at(at(2)) is GameStanding.CALLED_OFF


async def test_a_game_that_has_already_ended_by_its_clock_is_stepped_over():
    """``docs/adr/0163`` §6 — a reopened court can outlive its game's window.
    The withdraw still ends the challenge, and the ghost stands as the end it
    already is rather than the act raising and holding the pair for ever."""

    ghost = _a_reopened_game()
    games = _Remembering(ghost)
    past_the_window = instant(
        PLANNED_AT + PLAN_HORIZON + ENTRY_GRACE + timedelta(hours=1)
    )

    await CallOffGame(games=games).execute(
        CallOffGameCommand(challenge_id=ghost.challenge_id, called_by=ANA),
        occurred_at=past_the_window,
    )

    assert ghost.standing_at(past_the_window) is GameStanding.NEVER_PLAYED
    assert ghost.called_off_at is None


async def test_only_a_ghost_is_stepped_over_and_any_other_end_raises():
    """The leniency is one standing wide: a game that reached any other end
    is unreachable from a challenge the withdraw admits, so the aggregate's
    refusal fires and rolls the withdrawal back."""

    game = _a_reopened_game()
    game.call_off(by=ANA, occurred_at=at(2))
    games = _Remembering(game)

    with pytest.raises(NotAGameToCallOff):
        await CallOffGame(games=games).execute(
            CallOffGameCommand(challenge_id=game.challenge_id, called_by=BO),
            occurred_at=at(3),
        )


async def test_a_call_off_for_a_challenge_with_no_game_is_a_broken_precondition():
    with pytest.raises(InvariantViolated):
        await CallOffGame(games=_Remembering()).execute(
            CallOffGameCommand(challenge_id=new_uuid(), called_by=ANA),
            occurred_at=at(1),
        )
