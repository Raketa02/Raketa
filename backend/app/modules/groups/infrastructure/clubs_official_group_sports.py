"""``OfficialGroupSports``, answered by the Groups context — the one thing a
club's details edit asks of it (``docs/adr/0182`` §5).

**The demand is clubs' and the signature is here**, as ``games``' *agreed
moment* is signed by the Plan: ``groups`` already reads ``clubs``, and an
adapter living in ``clubs`` would point the arrow back the other way. It reads
this context's own directory, and **decides by kind** — a player group plays
whatever its members are rated in and declares nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.modules.clubs.domain.ports import DeclaringGroup
from app.modules.groups.domain.ports import GroupDirectory


class GroupsOfficialGroupSports:
    def __init__(self, directory: GroupDirectory) -> None:
        self._directory = directory

    async def declared_at(self, club_id: UUID) -> Sequence[DeclaringGroup]:
        listings = (await self._directory.listings_at([club_id])).get(club_id, ())
        return [
            DeclaringGroup(
                name=listing.name.value, sports=listing.declared_sports.sports
            )
            for listing in listings
            if listing.is_official and listing.declared_sports is not None
        ]
