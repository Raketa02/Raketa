"""Request-scoped declarations the console needs and no context declares.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``), as for every other
surface. Everything else the console takes — the proposals' repository and
directory, the group directory, the seat charges, a yes and a deck — it takes
through the context's own declaration, so a test that replaces one replaces it
for the console too.
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
    build_club_terms,
    build_deck_people,
    build_proposal_player_names,
    build_propose_games,
    build_saved_methods,
)
from app.modules.bookings.domain.ports import BookingRepository
from app.modules.proposals.application.propose_games import ProposeGames
from app.modules.proposals.domain.ports import (
    ClubTerms,
    DeckPeople,
    PlayerNames,
    SavedMethods,
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
