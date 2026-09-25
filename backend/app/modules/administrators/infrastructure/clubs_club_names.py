"""``ClubNames`` over the clubs' published directory — never their table."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.modules.clubs.domain.ports import ClubDirectory


class ClubsClubNames:
    def __init__(self, directory: ClubDirectory) -> None:
        self._directory = directory

    async def names_of(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        listed = await self._directory.listed(club_ids)
        return {club_id: listing.name for club_id, listing in listed.items()}
