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
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_proposal_club_names,
    build_proposal_directory,
    build_proposal_guards,
    build_proposal_repository,
)
from app.modules.proposals.application.answers import SayNo, SayYes, WithdrawYes
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.application.live_yeses import ReadLiveYeses
from app.modules.proposals.domain.ports import (
    ClubNames,
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
