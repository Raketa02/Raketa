"""Request-scoped declarations for the games context.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

**The repository is built beside the unit of work it will commit through**, for
the reason every aggregate repository in this codebase is: it remembers the
stream versions it loaded, so it must never outlive the transaction it was built
for.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    StoreOrNothingDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_game_court_pairing,
    build_game_directory,
    build_game_repository,
    build_player_names,
)
from app.modules.games.application.answer_result import AcceptResult, StateResult
from app.modules.games.application.dismiss_game import DismissGame
from app.modules.games.application.read_game_pairing import ReadGamePairing
from app.modules.games.application.read_games import ReadGames
from app.modules.games.domain.ports import (
    CourtPairing,
    GameRepository,
    PlayerNames,
)


def get_game_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> GameRepository:
    return build_game_repository(
        session=db, event_store=event_store, events=events
    )


GameRepositoryDep = Annotated[GameRepository, Depends(get_game_repository)]


def get_player_names(db: DbSession) -> PlayerNames:
    """Per request, and **not** per unit of work.

    It reads and never writes, and a game's court is frozen at the plan — so
    unlike the repository beside it, it remembers nothing it would have to commit
    and outlives no transaction it was built for.
    """
    return build_player_names(db)


PlayerNamesDep = Annotated[PlayerNames, Depends(get_player_names)]


def get_read_games(
    db: DbSession, names: PlayerNamesDep, clock: ClockDep
) -> ReadGames:
    return ReadGames(games=build_game_directory(db), names=names, clock=clock)


ReadGamesDep = Annotated[ReadGames, Depends(get_read_games)]


def get_state_result(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
    names: PlayerNamesDep,
) -> StateResult:
    return StateResult(games=games, names=names, uow=uow, clock=clock)


StateResultDep = Annotated[StateResult, Depends(get_state_result)]


def get_accept_result(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
    names: PlayerNamesDep,
) -> AcceptResult:
    return AcceptResult(games=games, names=names, uow=uow, clock=clock)


AcceptResultDep = Annotated[AcceptResult, Depends(get_accept_result)]


def get_dismiss_game(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
) -> DismissGame:
    """The dismissal: the result acts' repository and unit of work, and no
    names — it answers nothing, so there is nobody to name."""

    return DismissGame(games=games, uow=uow, clock=clock)


DismissGameDep = Annotated[DismissGame, Depends(get_dismiss_game)]


def get_court_pairing(
    request: Request,
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    settings: SettingsDep,
    store: StoreOrNothingDep,
) -> CourtPairing:
    """The matcher's and the rating context's answer about a game's court, per
    request.

    **The index is read off the running process rather than declared**, and it
    is read with ``getattr`` deliberately: this context may not name the
    matcher's types, and a process with no index is not a refusal here. A
    search with none says ``503``; this screen answers regardless — the seats'
    Levels and the stakes are the rating context's and are read whatever the
    matcher's state, and the forecast is simply not drawn — because a game
    screen is not gated on the matcher (``docs/adr/0161``).
    """

    return build_game_court_pairing(
        session=db,
        clock=clock,
        unit_of_work=uow,
        event_store=event_store,
        events=events,
        settings=settings,
        store=store,
        candidates=getattr(request.app.state, "candidate_source", None),
    )


def get_read_game_pairing(
    clock: ClockDep,
    games: GameRepositoryDep,
    pairings: Annotated[CourtPairing, Depends(get_court_pairing)],
) -> ReadGamePairing:
    """The pairing read — the game of yours, the standing, and the port.

    It holds the aggregate repository the acts hold, because *the game of
    yours* is one question asked the same way by a read and by an act; and it
    holds the pairing port, which is the expensive dependency this route
    exists to pay for and which no other route in this context takes.
    """

    return ReadGamePairing(games=games, pairings=pairings, clock=clock)


ReadGamePairingDep = Annotated[ReadGamePairing, Depends(get_read_game_pairing)]
