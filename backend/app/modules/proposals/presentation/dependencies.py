"""Request-scoped declarations for the Proposals context.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_booked_games,
    build_games_and_money_repository,
    build_proposal_club_names,
    build_proposal_directory,
    build_proposal_guards,
    build_proposal_repository,
    build_read_group_deck,
)
from app.modules.proposals.application.answers import SayNo, SayYes, WithdrawYes
from app.modules.proposals.application.games_and_money import (
    ReadGamesAndMoney,
    SetGamesAndMoney,
)
from app.modules.proposals.application.group_deck import ReadGroupDeck
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.application.live_yeses import ReadLiveYeses
from app.modules.proposals.domain.ports import (
    BookedGames,
    ClubNames,
    GamesAndMoneyRepository,
    ProposalDirectory,
    ProposalRepository,
)


def get_proposal_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ProposalRepository:
    return build_proposal_repository(db, event_store=event_store, events=events)


ProposalRepositoryDep = Annotated[ProposalRepository, Depends(get_proposal_repository)]


def get_proposal_directory(db: DbSession) -> ProposalDirectory:
    return build_proposal_directory(db)


ProposalDirectoryDep = Annotated[ProposalDirectory, Depends(get_proposal_directory)]


def get_proposal_club_names(db: DbSession) -> ClubNames:
    return build_proposal_club_names(db)


ProposalClubNamesDep = Annotated[ClubNames, Depends(get_proposal_club_names)]


def get_guards(db: DbSession) -> Guards:
    return build_proposal_guards(db)


GuardsDep = Annotated[Guards, Depends(get_guards)]


def get_say_yes(
    proposals: ProposalRepositoryDep,
    guards: GuardsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SayYes:
    return SayYes(proposals=proposals, guards=guards, uow=uow, clock=clock)


SayYesDep = Annotated[SayYes, Depends(get_say_yes)]


def get_say_no(
    proposals: ProposalRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> SayNo:
    return SayNo(proposals=proposals, uow=uow, clock=clock)


SayNoDep = Annotated[SayNo, Depends(get_say_no)]


def get_withdraw_yes(
    proposals: ProposalRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> WithdrawYes:
    return WithdrawYes(proposals=proposals, uow=uow, clock=clock)


WithdrawYesDep = Annotated[WithdrawYes, Depends(get_withdraw_yes)]


def get_read_live_yeses(
    directory: ProposalDirectoryDep, clubs: ProposalClubNamesDep, clock: ClockDep
) -> ReadLiveYeses:
    return ReadLiveYeses(directory=directory, clubs=clubs, clock=clock)


ReadLiveYesesDep = Annotated[ReadLiveYeses, Depends(get_read_live_yeses)]


def get_games_and_money_repository(
    event_store: DomainEventStoreDep, events: EventPublisherDep
) -> GamesAndMoneyRepository:
    return build_games_and_money_repository(event_store=event_store, events=events)


GamesAndMoneyRepositoryDep = Annotated[
    GamesAndMoneyRepository, Depends(get_games_and_money_repository)
]


def get_read_games_and_money(
    settings: GamesAndMoneyRepositoryDep,
) -> ReadGamesAndMoney:
    return ReadGamesAndMoney(settings=settings)


ReadGamesAndMoneyDep = Annotated[ReadGamesAndMoney, Depends(get_read_games_and_money)]


def get_set_games_and_money(
    settings: GamesAndMoneyRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> SetGamesAndMoney:
    return SetGamesAndMoney(settings=settings, uow=uow, clock=clock)


SetGamesAndMoneyDep = Annotated[SetGamesAndMoney, Depends(get_set_games_and_money)]


def get_booked_games() -> BookedGames:
    """The games a player has booked — none until bookings exist (#541); a test
    stands in for them by overriding this."""
    return build_booked_games()


BookedGamesDep = Annotated[BookedGames, Depends(get_booked_games)]


def get_read_group_deck(
    db: DbSession, settings: SettingsDep, clock: ClockDep, booked: BookedGamesDep
) -> ReadGroupDeck:
    return build_read_group_deck(db, settings=settings, clock=clock, booked=booked)


ReadGroupDeckDep = Annotated[ReadGroupDeck, Depends(get_read_group_deck)]
