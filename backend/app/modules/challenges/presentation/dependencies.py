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
    build_challenge_directory,
    build_challenge_handles,
    build_challenge_repository,
    build_court_pairing_query,
    build_court_safety,
    build_open_challenge_query,
    build_origin_search_query,
    build_planned_game_handover,
    build_seatable_game_query,
)
from app.modules.challenges.application.answer_seat import AcceptSeat, DeclineSeat
from app.modules.challenges.application.fill_seats import FillSeats
from app.modules.challenges.application.leave_game import LeaveGame
from app.modules.challenges.application.read_challenge import ReadChallenge
from app.modules.challenges.application.read_challenges import ReadChallenges
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.application.withdraw_challenge import WithdrawChallenge
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    CourtPairingQuery,
)
from app.modules.challenges.domain.seatable_game import SeatableGameQuery


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

def get_court_pairing_query(
    request: Request,
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    settings: SettingsDep,
    store: StoreOrNothingDep,
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


def get_seatable_game_query(db: DbSession) -> SeatableGameQuery:
    """*May a seat on this court still change?* — read off ``games``, per request."""

    return build_seatable_game_query(db)


SeatableGameQueryDep = Annotated[SeatableGameQuery, Depends(get_seatable_game_query)]


def get_accept_seat(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
    games: SeatableGameQueryDep,
) -> AcceptSeat:
    """The accept, and the one thing it asks somebody else to do.

    The game hand-over is declared here rather than inside the use case because
    *what opens a game* is a choice about wiring — and it is on **this** answer
    alone, because a decline empties a seat and can never fill the last one.
    The seatable-court read is here for the same reason: an acceptance into a
    court that has been a game is a re-seat, and the moment guards it.
    """

    return AcceptSeat(
        challenges=challenges,
        handles=build_challenge_handles(db),
        uow=uow,
        clock=clock,
        planned_games=build_planned_game_handover(db),
        games=games,
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


def get_withdraw_challenge(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
) -> WithdrawChallenge:
    """The withdraw, and it is the decline's four collaborators exactly.

    **No game opening here**, and the absence is the same statement ``DeclineSeat``
    makes: only an accept can fill the last seat, and a withdraw is the act for a
    line-up that never will.
    """

    return WithdrawChallenge(
        challenges=challenges, handles=build_challenge_handles(db), uow=uow, clock=clock
    )


WithdrawChallengeDep = Annotated[WithdrawChallenge, Depends(get_withdraw_challenge)]


def get_leave_game(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
    games: SeatableGameQueryDep,
) -> LeaveGame:
    """The departure: an act on one challenge, and the game is told.

    It holds the accept's hand-over and the accept's moment guard, because it is
    the accept's mirror — a seat moving on a court that has been a game, told to
    the game in the same transaction — and the court's safety gates, because a
    departure writes a line into a room other people are in and the hold is read
    through the same fail-closed gate the send and the fill read it through.
    """

    return LeaveGame(
        challenges=challenges,
        handles=build_challenge_handles(db),
        safety=build_court_safety(db),
        games=games,
        uow=uow,
        clock=clock,
        planned_games=build_planned_game_handover(db),
    )


LeaveGameDep = Annotated[LeaveGame, Depends(get_leave_game)]


def get_fill_seats(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    challenges: ChallengeRepositoryDep,
    games: SeatableGameQueryDep,
) -> FillSeats:
    """The fill: an act on one challenge, holding the send's three extra reads.

    **It is both of the shapes in this file at once**, which is what it is: an
    act on a challenge of yours — load, write, commit, redraw — that re-verifies
    everything a send does, because growing a court puts two more people in front
    of each other exactly as minting one does.

    The three come from the same builders the send's do, so a fill and a send
    cannot end up wired to two different answers about who may share a court.
    """

    return FillSeats(
        challenges=challenges,
        handles=build_challenge_handles(db),
        open_challenges=build_open_challenge_query(db),
        origins=build_origin_search_query(db),
        safety=build_court_safety(db),
        games=games,
        uow=uow,
        clock=clock,
    )


FillSeatsDep = Annotated[FillSeats, Depends(get_fill_seats)]
