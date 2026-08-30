"""Request-scoped declarations for the challenges context.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

**The repository is built beside the unit of work it will commit through**, for
the reason every aggregate repository in this codebase is: it remembers the stream
versions it loaded, so it must never outlive the transaction it was built for —
one send's versions must never answer for another's.

**The court's safety gates are declared once and shared by both surfaces.** The
send and the mutual-born mint ask the same four questions, and a surface that
decided for itself where a gate came from is how one of them ends up wired to a
different answer.
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
    build_challenge_directory,
    build_challenge_repository,
    build_court_safety,
    build_open_challenge_query,
    build_origin_search_query,
)
from app.modules.challenges.application.answer_seat import AcceptSeat, DeclineSeat
from app.modules.challenges.application.read_challenges import ReadChallenges
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.domain.ports import ChallengeRepository


def get_challenge_repository(
    event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ChallengeRepository:
    return build_challenge_repository(event_store=event_store, events=events)


ChallengeRepositoryDep = Annotated[
    ChallengeRepository, Depends(get_challenge_repository)
]


def get_send_challenge(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
) -> SendChallenge:
    """The send, assembled per request — one transaction, five facts."""

    return SendChallenge(
        challenges=challenges,
        open_challenges=build_open_challenge_query(db),
        origins=build_origin_search_query(db),
        safety=build_court_safety(db),
        uow=uow,
        clock=clock,
    )


SendChallengeDep = Annotated[SendChallenge, Depends(get_send_challenge)]


def get_read_challenges(db: DbSession, clock: ClockDep) -> ReadChallenges:
    return ReadChallenges(directory=build_challenge_directory(db), clock=clock)


ReadChallengesDep = Annotated[ReadChallenges, Depends(get_read_challenges)]


def get_accept_seat(
    clock: ClockDep, uow: UnitOfWorkDep, challenges: ChallengeRepositoryDep
) -> AcceptSeat:
    return AcceptSeat(challenges=challenges, uow=uow, clock=clock)


AcceptSeatDep = Annotated[AcceptSeat, Depends(get_accept_seat)]


def get_decline_seat(
    clock: ClockDep, uow: UnitOfWorkDep, challenges: ChallengeRepositoryDep
) -> DeclineSeat:
    return DeclineSeat(challenges=challenges, uow=uow, clock=clock)


DeclineSeatDep = Annotated[DeclineSeat, Depends(get_decline_seat)]
