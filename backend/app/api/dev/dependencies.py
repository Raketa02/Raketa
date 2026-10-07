"""Request-scoped declarations the console needs and no context declares.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``), as for every other
surface. Everything else the console takes — the proposals' repository and
directory, the group directory, the seat charges, a yes and a deck, the club's
answers, the payment provider — it takes through the context's own
declaration, so a test that replaces one replaces it for the console too.

**Two are jobs' and the outbox's units of work** (#591): the On request
timeout the ``request-timeout`` job runs, and the step the outbox runs for a
seat's money — each over this request's session and its clock, which is the
real *now*.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
)
from app.bootstrap.composition import (
    build_booking_repository,
    build_check_in_codes,
    build_club_terms,
    build_court_hours,
    build_deck_people,
    build_expire_unanswered_requests,
    build_pools,
    build_proposal_player_names,
    build_propose_games,
    build_saved_methods,
    build_settle_seat_charges,
    build_where_pools_play,
)
from app.modules.bookings.domain.ports import BookingRepository, CheckInCodes
from app.modules.payments.application.handlers.settle_seat_charges import (
    SettleSeatCharges,
)
from app.modules.payments.presentation.dependencies import PaymentProviderDep
from app.modules.proposals.application.club_requests import (
    ExpireUnansweredRequests,
)
from app.modules.proposals.application.propose_games import ProposeGames
from app.modules.proposals.domain.ports import (
    ClubTerms,
    CourtHours,
    DeckPeople,
    PlayerNames,
    Pools,
    SavedMethods,
    WherePoolsPlay,
)
from app.modules.proposals.presentation.dependencies import BookedGamesDep


def get_booking_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> BookingRepository:
    return build_booking_repository(db, event_store=event_store, events=events)


BookingRepositoryDep = Annotated[BookingRepository, Depends(get_booking_repository)]


def get_deck_people(db: DbSession, settings: SettingsDep) -> DeckPeople:
    """A row's name, face and Level — what a card draws of a person."""
    return build_deck_people(db, settings=settings)


DeckPeopleDep = Annotated[DeckPeople, Depends(get_deck_people)]


def get_player_names(db: DbSession) -> PlayerNames:
    return build_proposal_player_names(db)


PlayerNamesDep = Annotated[PlayerNames, Depends(get_player_names)]


def get_club_terms(db: DbSession) -> ClubTerms:
    """Whether each club sells, its cut-off, and whether it confirms each game."""
    return build_club_terms(db)


ClubTermsDep = Annotated[ClubTerms, Depends(get_club_terms)]


def get_saved_methods(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> SavedMethods:
    return build_saved_methods(db, event_store=event_store, events=events)


SavedMethodsDep = Annotated[SavedMethods, Depends(get_saved_methods)]


def get_propose_games(
    db: DbSession, clock: ClockDep, booked: BookedGamesDep
) -> ProposeGames:
    """The proposer the jobs run, over this request's clock — the real *now*."""
    return build_propose_games(db, clock=clock, booked=booked)


ProposeGamesDep = Annotated[ProposeGames, Depends(get_propose_games)]


def get_pools(db: DbSession) -> Pools:
    return build_pools(db)


PoolsDep = Annotated[Pools, Depends(get_pools)]


def get_where_pools_play(db: DbSession) -> WherePoolsPlay:
    """A group's home club, and the clubs its games may also use."""
    return build_where_pools_play(db)


WherePoolsPlayDep = Annotated[WherePoolsPlay, Depends(get_where_pools_play)]


def get_court_hours(db: DbSession) -> CourtHours:
    """What a club sells at an hour, at a given *now* — the backdated one a
    situation writes its history on, too."""
    return build_court_hours(db)


CourtHoursDep = Annotated[CourtHours, Depends(get_court_hours)]


def get_check_in_codes(settings: SettingsDep) -> CheckInCodes:
    """Each seat's code, as the phone shows it and the desk recomputes it."""
    return build_check_in_codes(settings)


CheckInCodesDep = Annotated[CheckInCodes, Depends(get_check_in_codes)]


def get_expire_unanswered_requests(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> ExpireUnansweredRequests:
    """The ``request-timeout`` job's unit of work, over the real *now*."""
    return build_expire_unanswered_requests(db, clock=clock, settings=settings)


ExpireUnansweredRequestsDep = Annotated[
    ExpireUnansweredRequests, Depends(get_expire_unanswered_requests)
]


def get_settle_seat_charges(
    db: DbSession, provider: PaymentProviderDep, clock: ClockDep
) -> SettleSeatCharges:
    """The outbox's step for a seat's money, over the provider this process
    moves money through."""
    return build_settle_seat_charges(db, provider=provider, clock=clock)


SettleSeatChargesDep = Annotated[SettleSeatCharges, Depends(get_settle_seat_charges)]
