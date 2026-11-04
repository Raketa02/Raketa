"""A Location area from where the player said they play: a reading of the
phone, or a club picked in its place (``docs/adr/0200`` §10).

**One function for both writes** — the commit and the move — so a club picked at
sign-up and one picked later from *You › Where you play* reach the same cell by
the same rule, and so does a reading. A club's point is **rounded to the cell
exactly as a reading is**, by ``LocationArea.around``: the precise point the
club's desk dropped never reaches this player's stream, the same promise a
phone's fix gets.

**Nothing records which of the two it was.** The area is a cell, whatever set
it, so a later reading in another cell replaces a club-picked area the way it
replaces an older reading — the cold start's rule, unchanged
(``docs/adr/0174`` §6).
"""

from __future__ import annotations

from app.modules.player_profile.application.commands import (
    LocationSource,
    PhoneReading,
    PickedClub,
)
from app.modules.player_profile.domain.errors import LocationClubUnknown
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.ports import ClubPoints


async def area_of(source: LocationSource, clubs: ClubPoints) -> LocationArea:
    """The cell ``source`` falls in. A reading asks nothing of anybody; a picked
    club asks where the club is, and an id that names no club is
    ``location_club_unknown``."""

    match source:
        case PhoneReading(latitude=latitude, longitude=longitude):
            return LocationArea.around(latitude, longitude)
        case PickedClub(club_id=club_id):
            point = await clubs.point_of(club_id)
            if point is None:
                raise LocationClubUnknown()
            return LocationArea.around(point.latitude, point.longitude)
