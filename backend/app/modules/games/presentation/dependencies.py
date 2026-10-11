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
    build_game_court_pairing,
    build_game_directory,
    build_game_repository,
    build_player_names,
)
from app.modules.games.application.answer_result import AcceptResult, StateResult
from app.modules.games.application.no_shows import DisputeANoShow, ReportANoShow
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


def get_report_a_no_show(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
    names: PlayerNamesDep,
) -> ReportANoShow:
    return ReportANoShow(games=games, names=names, uow=uow, clock=clock)


ReportANoShowDep = Annotated[ReportANoShow, Depends(get_report_a_no_show)]


def get_dispute_a_no_show(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    games: GameRepositoryDep,
    names: PlayerNamesDep,
) -> DisputeANoShow:
    return DisputeANoShow(games=games, names=names, uow=uow, clock=clock)


DisputeANoShowDep = Annotated[DisputeANoShow, Depends(get_dispute_a_no_show)]


def get_court_pairing(db: DbSession) -> CourtPairing:
    """The engine's and the rating context's answer about a game's court, per
    request.

    **Over the request's session and nothing else** (#575): the court is read
    side against side from the people's Levels, so the Redis store is not asked
    for — a game screen is not gated on the matcher (``docs/adr/0161``).
    """

    return build_game_court_pairing(db)


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
