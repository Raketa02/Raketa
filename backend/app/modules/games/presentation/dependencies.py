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

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_game_directory,
    build_game_repository,
    build_player_handles,
)
from app.modules.games.application.answer_result import AcceptResult, StateResult
from app.modules.games.application.read_games import ReadGames
from app.modules.games.domain.ports import GameRepository, PlayerHandles


def get_game_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> GameRepository:
    return build_game_repository(
        session=db, event_store=event_store, events=events
    )


GameRepositoryDep = Annotated[GameRepository, Depends(get_game_repository)]


def get_player_handles(db: DbSession) -> PlayerHandles:
    """Per request, and **not** per unit of work.

    It reads and never writes, and a game's court is frozen at the plan — so
    unlike the repository beside it, it remembers nothing it would have to commit
    and outlives no transaction it was built for.
    """
    return build_player_handles(db)


PlayerHandlesDep = Annotated[PlayerHandles, Depends(get_player_handles)]


def get_read_games(
    db: DbSession, handles: PlayerHandlesDep, clock: ClockDep
) -> ReadGames:
    return ReadGames(games=build_game_directory(db), handles=handles, clock=clock)


ReadGamesDep = Annotated[ReadGames, Depends(get_read_games)]


def get_state_result(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
    handles: PlayerHandlesDep,
) -> StateResult:
    return StateResult(games=games, handles=handles, uow=uow, clock=clock)


StateResultDep = Annotated[StateResult, Depends(get_state_result)]


def get_accept_result(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
    handles: PlayerHandlesDep,
) -> AcceptResult:
    return AcceptResult(games=games, handles=handles, uow=uow, clock=clock)


AcceptResultDep = Annotated[AcceptResult, Depends(get_accept_result)]
