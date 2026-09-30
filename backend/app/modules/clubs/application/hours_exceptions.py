"""The club closes hours without touching its pattern, and opens them again
(#535, the mechanics §16.5, the screens B3)."""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.clubs.application.commands import (
    AddExceptionCommand,
    RemoveExceptionCommand,
)
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.court_hours import hour_start, local_day
from app.modules.clubs.domain.errors import CourtBookedThen
from app.modules.clubs.domain.hours_exceptions import (
    ClosedHours,
    ExceptionReason,
    HoursException,
)
from app.modules.clubs.domain.ports import ClubCourtsRepository, CourtBookings
from app.shared.ids import new_uuid


class ReadExceptions:
    """The exceptions the desk's list shows: every one not over yet, at the
    club, by the day it starts."""

    def __init__(self, *, courts: ClubCourtsRepository, clock: Clock) -> None:
        self._courts = courts
        self._clock = clock

    async def execute(self, club_id: UUID) -> list[HoursException]:
        club = await self._courts.load(club_id)
        return club.exceptions_not_over(today=local_day(self._clock.now()))


class AddException:
    """The desk closes an hour, a day or a run of days, on every court or some.

    **Refused over a booking** (``court_booked_then``, naming it), and allowed
    over an hour that only has cards on it — those move to another court or
    disappear, and nobody was charged (the mechanics §16.5). Refused in the
    form's order: the reason, the hours, the days, the courts, whether it is
    over; and only then is anything booked asked about.
    """

    def __init__(
        self,
        *,
        courts: ClubCourtsRepository,
        bookings: CourtBookings,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._courts = courts
        self._bookings = bookings
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AddExceptionCommand) -> HoursException:
        reason = ExceptionReason(command.reason)
        hours = ClosedHours.of(command.from_hour, command.until_hour)
        exception = HoursException(
            id=new_uuid(),
            court_ids=command.court_ids,
            first_day=command.first_day,
            last_day=command.last_day,
            hours=hours,
            reason=reason,
        )
        now = self._clock.now()
        today = local_day(now)
        club = await self._courts.load(command.club_id)
        club.admit_exception(exception, today=today)
        await self._refuse_a_booked_hour(club, exception)
        added = club.add_exception(exception, today=today, occurred_at=now)
        await self._courts.save(club)
        await self._uow.commit()
        return added

    async def _refuse_a_booked_hour(
        self, club: ClubCourts, exception: HoursException
    ) -> None:
        """The first booked hour the exception would close, by its start and
        then the club's order of courts — the same one whatever order bookings
        answered in. Asked over the run's first and last court hour; ``covers``
        decides the hours between."""

        opens, closes = exception.span
        taken = await self._bookings.taken(
            club.club_id,
            start=hour_start(exception.first_day, opens),
            end=hour_start(exception.last_day, closes),
        )
        order = {court_id: place for place, court_id in enumerate(club.courts)}
        closed = sorted(
            (hour for hour in taken if exception.covers(hour.court_id, hour.start)),
            key=lambda hour: (hour.start, order.get(hour.court_id, len(order))),
        )
        if closed:
            first = closed[0]
            raise CourtBookedThen(
                court_id=str(first.court_id),
                booking_id=str(first.booking_id),
                starts_at=first.start.isoformat(),
            )


class RemoveException:
    """The desk removes an exception, and its hours are the pattern's again."""

    def __init__(
        self, *, courts: ClubCourtsRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._courts = courts
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RemoveExceptionCommand) -> None:
        club = await self._courts.load(command.club_id)
        club.remove_exception(command.exception_id, occurred_at=self._clock.now())
        await self._courts.save(club)
        await self._uow.commit()
