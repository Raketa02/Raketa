from __future__ import annotations

from app.modules.groups.application.commands import SearchHomeClubsCommand
from app.modules.groups.application.views import (
    ClubCard,
    HomeClubResults,
    at_club,
    rated_among,
)
from app.modules.groups.domain.home_club_search import (
    in_card_order,
    in_search_order,
    page_of,
)
from app.modules.groups.domain.ports import (
    GroupDirectory,
    HomeClubs,
    RatedGroupMembers,
    ReaderAreas,
)
from app.modules.groups.domain.value_objects import SearchText


class SearchHomeClubs:
    """*New group*'s home club field: clubs whose name or district holds what
    was typed, nearest first, each with every group already there
    (``docs/adr/0183`` §9).

    **A blank field is not a search** and answers nothing (``SearchText``).

    The whole match is ordered before a page is cut, because *nearest first* is
    a property of the answer and not of a page. Only the page's clubs have their
    groups read, and the ratings behind their dots are one question about every
    member of every one of those groups.
    """

    def __init__(
        self,
        *,
        clubs: HomeClubs,
        areas: ReaderAreas,
        directory: GroupDirectory,
        ratings: RatedGroupMembers,
    ) -> None:
        self._clubs = clubs
        self._areas = areas
        self._directory = directory
        self._ratings = ratings

    async def execute(self, command: SearchHomeClubsCommand) -> HomeClubResults:
        typed = SearchText(command.text)
        if typed.is_blank:
            return HomeClubResults(clubs=(), next_page=None)

        page = page_of(
            in_search_order(
                await self._clubs.matching(typed.value),
                await self._areas.of(command.reader_id),
            ),
            command.page,
        )
        groups_at = await self._directory.listings_at(
            [placed.club.id for placed in page.clubs]
        )
        rated = await rated_among(
            self._ratings,
            [listing for groups in groups_at.values() for listing in groups],
        )
        return HomeClubResults(
            clubs=tuple(
                ClubCard(
                    club=placed.club,
                    distance_km=placed.distance_km,
                    groups=tuple(
                        at_club(listing, rated, command.reader_id)
                        for listing in in_card_order(groups_at.get(placed.club.id, ()))
                    ),
                )
                for placed in page.clubs
            ),
            next_page=page.next_page,
        )
