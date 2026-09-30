"""The game's side of a departure — the two acts that move a line-up after the
plan, and what an open seat refuses (``docs/adr/0162``).

**The line-up is frozen until somebody leaves it.** ``vacate`` opens one seat and
``reseat`` replaces the whole court; ``planned_at`` never moves; a court with a
seat open is still awaiting its entry and refuses a score. Driven on the
aggregate and on the use case that hands a completed line-up over, with a
hand-written repository, because what is under test is *what the record does*
rather than anything about a database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.challenges.domain.seatable_game import LineUpChange
from app.modules.challenges.infrastructure.games_seatable_game import (
    GamesSeatableGame,
)
from app.modules.games.application.commands import (
    OpenPlannedGameCommand,
    VacateSeatCommand,
)
from app.modules.games.application.open_planned_game import OpenPlannedGame
from app.modules.games.application.vacate_seat import VacateSeat
from app.modules.games.domain.errors import (
    TheCourtHasAnOpenSeat,
    TheGameIsNotOpenToSeating,
    YouWereNotOnThisCourt,
)
from app.modules.games.domain.events import (
    GamePlanned,
    LineUpReseated,
    SeatVacated,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.ports import SeatChange
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.standing import GameStanding
from app.modules.player_profile.domain.weekly_hours import Window
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


def _score() -> Score:
    return Score.of((SetScore(a=6, b=3), SetScore(a=6, b=4)))


# ---------------------------------------------------------------------------
# The line-up
# ---------------------------------------------------------------------------


def test_a_seat_is_open_after_a_departure_and_is_never_dropped():
    game = _a_game()
    game.vacate(CY, occurred_at=at(1))

    assert [seating.player_id for seating in game.line_up.seatings] == [
        ANA,
        BO,
        None,
        DEE,
    ]
    assert game.line_up.players == {ANA, BO, DEE}
    assert not game.line_up.is_complete
    assert game.line_up.side_of(CY) is None
    assert game.line_up.counterparts_of(ANA) == {BO, DEE}
    assert game.planned_at == PLANNED_AT
    assert game.standing_at(at(2)) is GameStanding.AWAITING_ENTRY
    assert isinstance(game.pull_events()[-1], SeatVacated)


def test_a_re_seat_replaces_the_whole_court_and_does_not_re_date_the_game():
    game = _a_game()
    game.vacate(CY, occurred_at=at(1))
    game.reseat(_four(ANA, DEE, BO, EVE), occurred_at=at(2))

    assert game.line_up.is_complete
    assert game.line_up.players_on(GameSide.A) == {ANA, DEE}
    assert game.line_up.players_on(GameSide.B) == {BO, EVE}
    assert game.planned_at == PLANNED_AT
    assert isinstance(game.pull_events()[-1], LineUpReseated)


def test_the_whole_life_replays_into_itself():
    game = _a_game()
    game.vacate(CY, occurred_at=at(1))
    game.vacate(DEE, occurred_at=at(2))
    game.reseat(_four(ANA, BO, EVE, new_uuid()), occurred_at=at(3))
    events = game.pull_events()

    rebuilt = Game.from_history(events)

    assert isinstance(events[0], GamePlanned)
    assert rebuilt.line_up == game.line_up
    assert rebuilt.planned_at == PLANNED_AT
    assert rebuilt.version == 4


def test_only_somebody_on_the_court_can_leave_it():
    game = _a_game()

    with pytest.raises(YouWereNotOnThisCourt):
        game.vacate(EVE, occurred_at=at(1))
    game.vacate(CY, occurred_at=at(1))
    with pytest.raises(YouWereNotOnThisCourt):
        game.vacate(CY, occurred_at=at(2))


def test_a_game_that_has_happened_or_never_will_is_not_open_to_seating():
    played = _a_game()
    played.state_result(by=ANA, score=_score(), occurred_at=at(1))
    with pytest.raises(TheGameIsNotOpenToSeating):
        played.vacate(CY, occurred_at=at(2))

    ghost = _a_game()
    ghost.vacate(CY, occurred_at=at(1))
    assert ghost.standing_at(at(24 * 9)) is GameStanding.NEVER_PLAYED
    with pytest.raises(TheGameIsNotOpenToSeating):
        ghost.reseat(_four(ANA, BO, EVE, DEE), occurred_at=at(24 * 9))


def test_a_re_seat_is_a_completed_court_on_a_court_with_a_seat_open():
    """Both halves are broken preconditions rather than states: the hand-over
    answers ``None`` for a court standing whole, and hands over only completed
    line-ups."""

    whole = _a_game()
    with pytest.raises(InvariantViolated):
        whole.reseat(_four(ANA, BO, EVE, DEE), occurred_at=at(1))

    reopened = _a_game()
    reopened.vacate(CY, occurred_at=at(1))
    with pytest.raises(InvariantViolated):
        reopened.reseat(
            LineUp.of(
                (
                    Seating(side=GameSide.A, player_id=ANA),
                    Seating(side=GameSide.A, player_id=BO),
                    Seating(side=GameSide.B, player_id=None),
                    Seating(side=GameSide.B, player_id=DEE),
                )
            ),
            occurred_at=at(2),
        )


def test_a_court_with_a_seat_open_refuses_a_score_and_a_ghost_is_still_a_ghost():
    """The window is asked first, so a ghost is told it is a ghost rather than
    that a seat is open."""

    game = _a_game()
    game.vacate(CY, occurred_at=at(1))

    with pytest.raises(TheCourtHasAnOpenSeat):
        game.state_result(by=ANA, score=_score(), occurred_at=at(2))
    assert game.outcome_for(CY, now=at(2)) is None
    assert game.standing_at(at(24 * 9)) is GameStanding.NEVER_PLAYED


def test_an_open_seat_travels_as_a_side_and_nothing_else():
    assert Seating(side=GameSide.B, player_id=None).code == "B|"
    assert Seating.from_code("B|") == Seating(side=GameSide.B, player_id=None)


# ---------------------------------------------------------------------------
# The hand-over
# ---------------------------------------------------------------------------


class _Remembering:
    """A ``GameRepository`` over a dict, keyed both ways the port is asked."""

    def __init__(self) -> None:
        self.games: dict[UUID, Game] = {}

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


def _court(*seatings: tuple[str, UUID]) -> tuple[tuple[str, UUID], ...]:
    return seatings


async def test_a_completed_line_up_opens_once_re_seats_an_open_court_and_retries():
    games = _Remembering()
    opening = OpenPlannedGame(games=games)
    departures = VacateSeat(games=games)
    challenge_id = new_uuid()
    command = OpenPlannedGameCommand(
        challenge_id=challenge_id,
        sport=Sport.PADEL,
        counted=True,
        window="WEEKEND",
        line_up=_court(("A", ANA), ("A", BO), ("B", CY), ("B", DEE)),
    )

    opened = await opening.execute(command, occurred_at=PLANNED_AT)
    assert opened is not None
    assert await opening.execute(command, occurred_at=at(1)) is None, "a retry"

    await departures.execute(
        VacateSeatCommand(challenge_id=challenge_id, player_id=CY), occurred_at=at(2)
    )
    (game,) = games.games.values()
    assert not game.line_up.is_complete

    reseated = await opening.execute(
        OpenPlannedGameCommand(
            challenge_id=challenge_id,
            sport=Sport.PADEL,
            counted=True,
            window="WEEKEND",
            line_up=_court(("A", ANA), ("A", BO), ("B", EVE), ("B", DEE)),
        ),
        occurred_at=at(3),
    )

    assert reseated == opened, "the same game, re-seated"
    assert game.line_up.players == {ANA, BO, EVE, DEE}
    assert game.planned_at == PLANNED_AT


async def test_a_departure_from_a_challenge_with_no_game_is_a_broken_precondition():
    departures = VacateSeat(games=_Remembering())

    with pytest.raises(InvariantViolated):
        await departures.execute(
            VacateSeatCommand(challenge_id=new_uuid(), player_id=ANA),
            occurred_at=at(1),
        )


# ---------------------------------------------------------------------------
# The two spellings of the guard's answer agree
# ---------------------------------------------------------------------------


def test_the_challenges_spelling_of_a_seat_change_is_the_games_spelling():
    """``LineUpChange`` is ``challenges``' own word for ``games``' ``SeatChange``,
    equal by name on purpose so the adapter is identity rather than a table —
    asserted, on the repository's rule for a second spelling, so a value added
    on one side goes red rather than being a ``ValueError`` on somebody's
    departure."""

    assert {one.value for one in LineUpChange} == {one.value for one in SeatChange}


async def test_the_adapter_translates_word_for_word_and_keeps_the_absence():
    class _Answering:
        def __init__(self, answer):
            self._answer = answer

        async def seat_change_on(self, challenge_id, *, now):
            return self._answer

    for change in SeatChange:
        translated = await GamesSeatableGame(_Answering(change)).line_up_change_on(
            new_uuid(), now=at(1)
        )
        assert translated is LineUpChange(change.value)
    assert (
        await GamesSeatableGame(_Answering(None)).line_up_change_on(
            new_uuid(), now=at(1)
        )
        is None
    )
