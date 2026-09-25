from __future__ import annotations

from uuid import UUID

from app.modules.groups.application.views import (
    MyGroup,
    NamedClub,
    rated_among,
    row_of,
)
from app.modules.groups.domain.ports import GroupDirectory, HomeClubs, RatedGroupMembers


class ReadMyGroups:
    """The groups the reader belongs to, **newest joined first**, so a group
    they have just joined is at the top (#500 story 7).

    Three reads whatever the length of the list: the reader's groups with
    their members, the home clubs' names, and the ratings behind the dots.
    """

    def __init__(
        self,
        *,
        directory: GroupDirectory,
        clubs: HomeClubs,
        ratings: RatedGroupMembers,
    ) -> None:
        self._directory = directory
        self._clubs = clubs
        self._ratings = ratings

    async def execute(self, reader_id: UUID) -> tuple[MyGroup, ...]:
        newest_first = await self._directory.groups_of(reader_id)
        listings = await self._directory.listings(newest_first)
        ordered = [
            listings[group_id] for group_id in newest_first if group_id in listings
        ]
        clubs = await self._clubs.by_id({listing.home_club_id for listing in ordered})
        rated = await rated_among(self._ratings, ordered)
        return tuple(
            MyGroup(
                row=row_of(listing, rated),
                home_club=NamedClub(
                    id=listing.home_club_id,
                    name=clubs[listing.home_club_id].name,
                ),
            )
            for listing in ordered
        )
