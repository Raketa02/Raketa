"""Read a club. Always as of now — the domain never reads the past.

``Series.as_of`` exists for a human reconstructing an outcome (ADR-0077 names
Raketa ops as the only v1 audience), and it is deliberately not what any use case
here calls. A club is loaded whole, and every question the domain asks of it —
the hold ladder's policy, the price of a category, which courts exist — is
answered from the row in force.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository


class GetClub:
    def __init__(self, clubs: ClubRepository) -> None:
        self._clubs = clubs

    async def execute(self, club_id: UUID) -> Club:
        club = await self._clubs.get(club_id)
        if club is None:
            raise ClubNotFound()
        return club


class ListClubs:
    def __init__(self, clubs: ClubRepository) -> None:
        self._clubs = clubs

    async def execute(self) -> list[Club]:
        return await self._clubs.find_all()
