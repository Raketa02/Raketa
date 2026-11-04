"""The Player profile's ``ClubPoints``, over this context's own published
directory (``docs/adr/0200`` §10).

**Signed here, in ``clubs/infrastructure/``**, because the arrow already runs
``clubs → player_profile`` (a club's hours are the profile's week); an adapter in
``player_profile/infrastructure/`` reading ``ClubDirectory`` would point it back,
and ``.importlinter``'s ``player-profile-does-not-know-clubs`` refuses that.

It reads ``ClubDirectory`` and never the ``clubs`` table, as ``groups``'
``HomeClubs`` does: the search projection is where a club's point is published,
and a second reader of its schema would be a second opinion about it. **The
point is the club's precise one**, as its desk dropped it; rounding it to a
player's cell is the profile's rule, applied there.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.clubs.domain.ports import ClubDirectory
from app.modules.player_profile.domain.ports import ClubPoint


class DirectoryClubPoints:
    def __init__(self, clubs: ClubDirectory) -> None:
        self._clubs = clubs

    async def point_of(self, club_id: UUID) -> ClubPoint | None:
        listing = (await self._clubs.listed([club_id])).get(club_id)
        if listing is None:
            return None
        return ClubPoint(latitude=listing.latitude, longitude=listing.longitude)
