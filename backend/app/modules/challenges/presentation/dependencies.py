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

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_challenge_directory,
    build_challenge_handles,
    build_challenge_repository,
    build_court_pairing_query,
    build_court_safety,
    build_open_challenge_query,
    build_origin_search_query,
    build_planned_game_opening,
)
from app.infrastructure.redis_client import get_redis
from app.modules.challenges.application.answer_seat import AcceptSeat, DeclineSeat
from app.modules.challenges.application.read_challenge import ReadChallenge
from app.modules.challenges.application.read_challenges import ReadChallenges
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    CourtPairingQuery,
)


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
    return ReadChallenges(
        directory=build_challenge_directory(db),
        handles=build_challenge_handles(db),
        clock=clock,
    )


ReadChallengesDep = Annotated[ReadChallenges, Depends(get_read_challenges)]

def get_ephemeral_store() -> Redis | None:
    """The process's Redis pool, or nothing where it never came up.

    **``None`` rather than a raise**, which is the one place this differs from
    the matcher's declaration of the same pool. A search that cannot read its
    ledgers is a search that cannot answer; this route answers regardless, and a
    store that is not there reaches the reader as *the pairing could not be
    read* (``docs/adr/0143`` §6) rather than as a failed screen. It stays a
    ``Depends`` so a test can override it.
    """

    try:
        return get_redis()
    except RuntimeError:
        return None


EphemeralStoreDep = Annotated[Redis | None, Depends(get_ephemeral_store)]


def get_court_pairing_query(
    request: Request,
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    settings: SettingsDep,
    store: EphemeralStoreDep,
) -> CourtPairingQuery:
    """The matcher's answer about the people on one court, per request.

    **The index is read off the running process rather than declared**, and it
    is read with ``getattr`` deliberately: this context may not name the
    matcher's types, and a process with no index is not a refusal here. A search
    with none says ``503`` because a search that cannot rank cannot answer; this
    screen answers regardless and the reader is told *the pairing could not be
    read* (``docs/adr/0143`` §6), because answering a challenge is not gated on
    the matcher.
    """

    return build_court_pairing_query(
        session=db,
        clock=clock,
        unit_of_work=uow,
        event_store=event_store,
        events=events,
        settings=settings,
        store=store,
        candidates=getattr(request.app.state, "candidate_source", None),
    )


def get_read_challenge(
    db: DbSession,
    clock: ClockDep,
    challenges: ChallengeRepositoryDep,
    pairings: Annotated[CourtPairingQuery, Depends(get_court_pairing_query)],
) -> ReadChallenge:
    """The detail read — the arrangement, the handles and the card block.

    It holds the aggregate repository the answers hold, because the screen and
    the acts on it read one challenge the same way; and it holds the pairing
    query, which is the expensive dependency this route exists to pay for and
    which no other surface in this context takes.
    """

    return ReadChallenge(
        challenges=challenges,
        handles=build_challenge_handles(db),
        pairings=pairings,
        clock=clock,
    )


ReadChallengeDep = Annotated[ReadChallenge, Depends(get_read_challenge)]


def get_accept_seat(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
) -> AcceptSeat:
    """The accept, and the one thing it asks somebody else to do.

    The game opening is declared here rather than inside the use case because
    *what opens a game* is a choice about wiring — and it is on **this** answer
    alone, because a decline empties a seat and can never fill the last one.
    """

    return AcceptSeat(
        challenges=challenges,
        handles=build_challenge_handles(db),
        uow=uow,
        clock=clock,
        planned_games=build_planned_game_opening(db),
    )


AcceptSeatDep = Annotated[AcceptSeat, Depends(get_accept_seat)]


def get_decline_seat(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
) -> DeclineSeat:
    return DeclineSeat(
        challenges=challenges,
        handles=build_challenge_handles(db),
        uow=uow,
        clock=clock,
    )


DeclineSeatDep = Annotated[DeclineSeat, Depends(get_decline_seat)]
