from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.clubs.application.commands import (
    ChangeClubDetailsCommand,
    ClubDetailsInput,
)
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.clubs.domain.value_objects import (
    City,
    ClubDetails,
    ClubName,
    District,
    MapPoint,
    OfferedSports,
)


def details_from(typed: ClubDetailsInput) -> ClubDetails:
    """The details as the domain holds them, refused field by field.

    Built **in the form's order** — name, district, city, sports, point — so the
    first refusal a desk meets is the first field it would read down to. Shared
    by the sign-up and the edit, which refuse the same five fields alike.
    """

    return ClubDetails(
        name=ClubName(typed.name),
        district=District(typed.district),
        city=City(typed.city),
        sports=OfferedSports.of(typed.sports),
        point=MapPoint(latitude=typed.latitude, longitude=typed.longitude),
    )


async def _the_club(clubs: ClubRepository, club_id: UUID) -> Club:
    club = await clubs.load(club_id)
    if club is None:
        # A Club account is opened in the same transaction as its club, so an
        # account whose club has no stream is a broken store, not a request.
        raise RuntimeError(f"club {club_id} has no stream behind its account")
    return club


class ReadClubDetails:
    """The club's details as its stream tells them — the club website's frame
    and its Club details page."""

    def __init__(self, *, clubs: ClubRepository) -> None:
        self._clubs = clubs

    async def execute(self, club_id: UUID) -> Club:
        return await _the_club(self._clubs, club_id)


class ChangeClubDetails:
    """The desk saves its club's details, at any time (``docs/adr/0182`` §5).

    A full replacement of all five, refused field by field exactly as the
    sign-up is. Saving them unchanged records nothing. The search row moves in
    the same transaction, so the next search already reads the new name.
    """

    def __init__(self, *, clubs: ClubRepository, uow: UnitOfWork, clock: Clock) -> None:
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangeClubDetailsCommand) -> Club:
        details = details_from(command.details)
        club = await _the_club(self._clubs, command.club_id)
        club.change_details(details, occurred_at=self._clock.now())
        await self._clubs.save(club)
        await self._uow.commit()
        return club
