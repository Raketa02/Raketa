"""The club's courts, as the desk lists them for Raketa (#535, the mechanics
§16.4–§16.5, the screens B3).

Every act loads the club's one stream, records through the aggregate and saves
it in the request's unit of work. The club is the signed-in desk's own, so it
always exists; its **Club courts** stream may not yet, and loads unwritten.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, shifted
from app.kernel import hours as whole_hours
from app.modules.clubs.application.commands import (
    AddCourtCommand,
    ChangeCourtCommand,
    RemoveCourtCommand,
    SetRakietaHoursCommand,
)
from app.modules.clubs.application.club_details import the_club
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.courts import Court, CourtName
from app.modules.clubs.domain.errors import CourtHasBookings
from app.modules.clubs.domain.setup import SetupChecklist, checklist_of
from app.modules.clubs.domain.ports import (
    ClubCourtsRepository,
    ClubRepository,
    CourtBookings,
)
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.shared.ids import new_uuid


class ReadClubCourts:
    """The club's courts and terms as its stream tells them — every section of
    Courts & prices and Rakieta settings is drawn from this one read."""

    def __init__(self, *, courts: ClubCourtsRepository) -> None:
        self._courts = courts

    async def execute(self, club_id: UUID) -> ClubCourts:
        return await self._courts.load(club_id)


class ReadSetup:
    """The Overview's setup checklist, read off the club's stream."""

    def __init__(self, *, courts: ClubCourtsRepository) -> None:
        self._courts = courts

    async def execute(self, club_id: UUID) -> SetupChecklist:
        return checklist_of(await self._courts.load(club_id))


class AddCourt:
    """The desk adds a court. It is born offered, with no hours."""

    def __init__(
        self,
        *,
        clubs: ClubRepository,
        courts: ClubCourtsRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._clubs = clubs
        self._courts = courts
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AddCourtCommand) -> Court:
        name = CourtName(command.name)
        offered = (await the_club(self._clubs, command.club_id)).details.sports
        club = await self._courts.load(command.club_id)
        court = club.add_court(
            court_id=new_uuid(),
            name=name,
            sport=command.sport,
            indoor=command.indoor,
            offered_sports=offered.sports,
            occurred_at=self._clock.now(),
        )
        await self._courts.save(club)
        await self._uow.commit()
        return court


async def _refuse_a_booking_ahead(
    bookings: CourtBookings, club_id: UUID, court_id: UUID, *, now: Instant
) -> None:
    """``court_has_bookings`` while a booking holds an hour of this court that
    is not over yet — **a game in progress included**, since it is a game on
    this court; one that ends exactly now is over."""

    taken = await bookings.taken(club_id, start=shifted(now, whole_hours(-1)))
    if any(
        hour.court_id == court_id and shifted(hour.start, whole_hours(1)) > now
        for hour in taken
    ):
        raise CourtHasBookings()


class ChangeCourt:
    """The desk saves a court's edit form, switching it off or on included.

    **A new sport is refused while a booking is ahead of the court** — a booked
    padel game cannot find itself on a tennis court — and switching the court
    off is not: it stops the court selling anything new, and a game already
    booked is played as booked (the mechanics §16.4).
    """

    def __init__(
        self,
        *,
        clubs: ClubRepository,
        courts: ClubCourtsRepository,
        bookings: CourtBookings,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._clubs = clubs
        self._courts = courts
        self._bookings = bookings
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangeCourtCommand) -> Court:
        name = CourtName(command.name)
        now = self._clock.now()
        club = await self._courts.load(command.club_id)
        if club.court(command.court_id).sport != command.sport:
            await _refuse_a_booking_ahead(
                self._bookings, command.club_id, command.court_id, now=now
            )
        offered = (await the_club(self._clubs, command.club_id)).details.sports
        court = club.change_court(
            command.court_id,
            name=name,
            sport=command.sport,
            indoor=command.indoor,
            offered=command.offered,
            offered_sports=offered.sports,
            occurred_at=now,
        )
        await self._courts.save(club)
        await self._uow.commit()
        return court


class RemoveCourt:
    """The desk deletes a court — **refused while a booking is ahead of it**;
    switching it off is the answer then (the screens B3)."""

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

    async def execute(self, command: RemoveCourtCommand) -> None:
        now = self._clock.now()
        club = await self._courts.load(command.club_id)
        club.court(command.court_id)
        await _refuse_a_booking_ahead(
            self._bookings, command.club_id, command.court_id, now=now
        )
        club.remove_court(command.court_id, occurred_at=now)
        await self._courts.save(club)
        await self._uow.commit()


class SetRakietaHours:
    """The desk saves *Weekly hours for Rakieta* for one court or several.

    **Nothing is refused over a booking or a card**: the pattern is what the
    club offers from now on, a booked game is played as booked whatever the
    pattern says, and a card on an hour the pattern no longer offers moves or
    disappears (the mechanics §16.5). A blank week is a court offering nothing.
    """

    def __init__(
        self, *, courts: ClubCourtsRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._courts = courts
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SetRakietaHoursCommand) -> ClubCourts:
        week = WeeklyHours.edited(command.hours)
        club = await self._courts.load(command.club_id)
        club.set_hours(
            dict.fromkeys(command.court_ids), week, occurred_at=self._clock.now()
        )
        await self._courts.save(club)
        await self._uow.commit()
        return club
