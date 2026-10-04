from __future__ import annotations

from app.modules.groups.application.views import LinkedGroup, rated_among, row_of
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.ports import GroupDirectory, HomeClubs, RatedGroupMembers
from app.modules.groups.domain.value_objects import GroupCode


class ReadGroupByLink:
    """The group a link carries, for the public site's page — **anybody may
    ask, and nobody signs in** (``docs/adr/0187`` §4).

    What it answers is the least that page needs (§5): the group's row — its
    name, tile, dots and size, drawn by the one function every list's row comes
    out of, so the page and the app cannot disagree about a dot — and its club
    and district. **Never who is in it**: the members are read for the dots and
    the count, and no face or name is asked for.

    A code that could be no group's, one no group has, and a deleted group's
    are one answer, ``group_not_found``: a link that leads nowhere
    (``docs/adr/0183`` §4).
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

    async def execute(self, code: str) -> LinkedGroup:
        read = GroupCode.read(code)
        listing = None if read is None else await self._directory.with_code(read)
        if listing is None:
            raise GroupNotFound()
        rated = await rated_among(self._ratings, [listing])
        club = (await self._clubs.by_id([listing.home_club_id]))[listing.home_club_id]
        return LinkedGroup(
            row=row_of(listing, rated),
            club_name=club.name,
            club_district=club.district,
        )
