"""**The club is told its new bookings once a day** (#548; the mechanics §16.12;
the screens B9).

A new booking is not worth an email of its own — the Bookings page shows it the
moment it is made — but a desk that is not watching the website should still
hear of it. So at the **close of each club day**, the desk is sent every game
booked at the club since the close before — filled, or accepted by the club
itself — the soonest first, whatever each has come to since; and nothing on a
day nothing was booked.

**Safe beside itself with no lock**: a club's day is summed up in a stream of
its own whose id is the club and the day (``domain/summary.py``), born in the
transaction that queues the email — so a second process collides on it, rolls
its email back with it, and is counted.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.application.ports.mail import MailQueue
from app.kernel import SPORT_SPECS, Clock, Instant, instant, invariant
from app.modules.bookings.application.request_emails import (
    NewBooking,
    new_bookings_email,
)
from app.modules.bookings.domain.booking import BookingState
from app.modules.bookings.domain.ports import (
    BookingDirectory,
    BookingRepository,
    ClubDesks,
    SummaryRepository,
)
from app.modules.bookings.domain.summary import NewBookingsSummary, summary_id_for
from app.modules.clubs.domain.court_hours import day_closes_at, last_closed_day


@final
@dataclass(frozen=True, slots=True)
class Summed:
    """How many clubs one run told their day, and how many another process
    reached first."""

    clubs: int
    conflicts: int


@final
class SummariseNewBookings:
    def __init__(
        self,
        *,
        bookings: BookingRepository,
        directory: BookingDirectory,
        summaries: SummaryRepository,
        desks: ClubDesks,
        mail: MailQueue,
        uow: UnitOfWork,
        clock: Clock,
        bookings_page: str,
    ) -> None:
        self._bookings = bookings
        self._directory = directory
        self._summaries = summaries
        self._desks = desks
        self._mail = mail
        self._uow = uow
        self._clock = clock
        self._bookings_page = bookings_page

    async def execute(self) -> Summed:
        now = instant(self._clock.now())
        day = last_closed_day(now)
        booked = await self._directory.booked_between(
            start=day_closes_at(day - timedelta(days=1)), end=day_closes_at(day)
        )
        told = conflicts = 0
        for club_id in sorted(booked):
            try:
                if await self._tell(club_id, booked[club_id], day=day, now=now):
                    await self._uow.commit()
                    told += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return Summed(clubs=told, conflicts=conflicts)

    async def _tell(
        self, club_id: UUID, booking_ids: Sequence[UUID], *, day: date, now: Instant
    ) -> bool:
        if await self._summaries.load(summary_id_for(club_id, day)) is not None:
            return False
        desk = await self._desks.of(club_id)
        if desk is None:
            return False
        games: list[NewBooking] = []
        for booking_id in booking_ids:
            booking = invariant(
                await self._bookings.load(booking_id), f"no booking {booking_id}"
            )
            games.append(
                NewBooking(
                    court=booking.court.name,
                    sport=booking.sport,
                    starts_at=booking.start,
                    price_grosze=booking.share_grosze
                    * SPORT_SPECS[booking.sport].players,
                    called_off=booking.state is BookingState.CALLED_OFF,
                )
            )
        await self._summaries.save(
            NewBookingsSummary.sent(
                club_id=club_id, day=day, booking_ids=tuple(booking_ids), at=now
            )
        )
        await self._mail.enqueue(
            new_bookings_email(
                to=desk.email,
                club=desk.club_name,
                day=day,
                booked=tuple(games),
                link=self._bookings_page,
            ),
            at=now,
        )
        return True
