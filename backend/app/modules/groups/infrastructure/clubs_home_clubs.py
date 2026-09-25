"""``HomeClubs`` over the clubs' own published directory.

**It reads ``ClubDirectory`` and never the ``clubs`` table**: where a club's
search copy lives and how it is folded are that context's business, and a second
reader of its schema would be a second opinion about both.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from uuid import UUID

from app.modules.clubs.domain.ports import ClubDirectory, ClubListing
from app.modules.groups.domain.ports import HomeClub


class ClubsHomeClubs:
    def __init__(self, clubs: ClubDirectory) -> None:
        self._clubs = clubs

    async def by_id(self, club_ids: Collection[UUID]) -> Mapping[UUID, HomeClub]:
        listed = await self._clubs.listed(club_ids)
        return {club_id: _home(listing) for club_id, listing in listed.items()}

    async def matching(self, text: str) -> Sequence[HomeClub]:
        return [_home(listing) for listing in await self._clubs.matching(text)]


def _home(listing: ClubListing) -> HomeClub:
    return HomeClub(
        id=listing.id,
        name=listing.name,
        district=listing.district,
        sports=listing.sports,
        latitude=listing.latitude,
        longitude=listing.longitude,
    )
