"""The Booking repository and directory: the stream, and the two projections
written beside it.

The same shape as the other aggregate repositories (``docs/adr/0018``), and,
like a proposal's, **its projections are written by ``save``, in the caller's
transaction, and flushed** — so the court hour is gone from what the club
sells, and the game counted in the player's week, the moment the fill commits.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Instant
from app.modules.bookings.domain.booking import Booking
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.domain.events import BookingConfirmed
from app.modules.bookings.domain.ports import HeldCourtHour
from app.modules.bookings.infrastructure.booking_models import (
    BookingORM,
    BookingSeatORM,
)

BOOKING_AGGREGATE = "booking"


@final
class EventSourcedBookingRepository:
    """``BookingRepository`` over ``DomainEventStore`` and the projections."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, booking_id: UUID) -> Booking | None:
        stored = await self._event_store.load_stream(
            aggregate_type=BOOKING_AGGREGATE, aggregate_id=booking_id
        )
        if not stored:
            return None
        booking = Booking.from_history(record.event for record in stored)
        self._versions[booking_id] = booking.version
        return booking

    async def save(self, booking: Booking) -> None:
        pending = booking.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=BOOKING_AGGREGATE,
            aggregate_id=booking.booking_id,
            expected_version=self._versions.get(booking.booking_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for event in pending:
            if isinstance(event, BookingConfirmed):
                self._project(event)
        try:
            await self._session.flush()
        except IntegrityError as taken:
            # Two games at one hour that read one court free: the second claim
            # meets the court hour's unique index. The transaction is spent.
            raise CourtTaken() from taken
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[booking.booking_id] = booking.version

    def _project(self, event: BookingConfirmed) -> None:
        self._session.add(
            BookingORM(
                id=event.booking_id,
                pool_id=event.pool_id,
                club_id=event.club_id,
                court_id=event.court_id,
                sport=event.sport,
                start=event.start,
                share_grosze=event.share_grosze,
                cut_off=event.cut_off,
                game_id=event.game_id,
                booked_at=event.occurred_at,
            )
        )
        for side, players in (("A", event.first_side), ("B", event.second_side)):
            for player_id in players:
                self._session.add(
                    BookingSeatORM(
                        booking_id=event.booking_id, player_id=player_id, side=side
                    )
                )


@final
class SqlAlchemyBookingDirectory:
    """``BookingDirectory`` over the projections."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def held_at(
        self, club_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[HeldCourtHour]:
        query = select(BookingORM.court_id, BookingORM.start, BookingORM.id).where(
            BookingORM.club_id == club_id, BookingORM.start >= start
        )
        if end is not None:
            query = query.where(BookingORM.start < end)
        rows = await self._session.execute(query)
        return [
            HeldCourtHour(
                court_id=court_id, start=stored_instant(at), booking_id=booking_id
            )
            for court_id, at, booking_id in rows.all()
        ]

    async def starts_for(
        self, player_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[Instant]:
        query = (
            select(BookingORM.start)
            .join(BookingSeatORM, BookingSeatORM.booking_id == BookingORM.id)
            .where(BookingSeatORM.player_id == player_id, BookingORM.start >= start)
            .order_by(BookingORM.start)
        )
        if end is not None:
            query = query.where(BookingORM.start < end)
        rows = await self._session.scalars(query)
        return [stored_instant(at) for at in rows.all()]
