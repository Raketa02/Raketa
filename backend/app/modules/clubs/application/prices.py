"""The club prices a court-hour per sport (#535, the mechanics §16.5, the
screens B3)."""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Sport
from app.modules.clubs.application.club_details import the_club
from app.modules.clubs.application.commands import SetPricesCommand
from app.modules.clubs.domain.ports import ClubCourtsRepository, ClubRepository
from app.modules.clubs.domain.prices import PriceBand, SportPrices, price_table

#: The price table as the desk reads it: every sport the club offers, in the
#: registry's order, and its prices — ``None`` where it has none yet.
PriceList = list[tuple[Sport, SportPrices | None]]


class ReadPrices:
    def __init__(self, *, clubs: ClubRepository, courts: ClubCourtsRepository) -> None:
        self._clubs = clubs
        self._courts = courts

    async def execute(self, club_id: UUID) -> PriceList:
        offered = (await the_club(self._clubs, club_id)).details.sports.sports
        return (await self._courts.load(club_id)).prices_of(offered)


class SetPrices:
    """The desk saves the whole price table. **New prices apply to new cards
    only** (the mechanics §16.5): a card already dealt was priced when it was
    dealt, and nothing here reaches it."""

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

    async def execute(self, command: SetPricesCommand) -> PriceList:
        offered = (await the_club(self._clubs, command.club_id)).details.sports.sports
        table = price_table(
            (
                (
                    row.sport,
                    row.price_grosze,
                    tuple(
                        PriceBand(
                            days=band.days,
                            opens=band.from_hour,
                            closes=band.until_hour,
                            grosze=band.price_grosze,
                        )
                        for band in row.bands
                    ),
                )
                for row in command.prices
            ),
            offered_sports=offered,
        )
        club = await self._courts.load(command.club_id)
        club.set_prices(table, occurred_at=self._clock.now())
        await self._courts.save(club)
        await self._uow.commit()
        return club.prices_of(offered)
