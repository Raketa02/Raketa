"""``ClubDistances`` over the Player profile and the Club directory (#542).

**From the reader's Location area to the club's point, printed as every distance
on the platform is** — the matcher's great-circle ``distance_km`` and
``shown_kilometres`` (``matchmaking/domain/geography.py``), one decimal and never
below a tenth — so the WHERE line and a group's club search cannot print two
readings of one distance (``docs/adr/0182`` §6). **The Location area and nothing
finer**, because nothing finer exists: the profile coarsens a fix on the way in.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.clubs.domain.ports import ClubDirectory
from app.modules.matchmaking.domain.geography import (
    Point,
    distance_km,
    shown_kilometres,
)
from app.modules.player_profile.domain.ports import PlayerProfileRepository


@final
class ProfileClubDistances:
    def __init__(
        self, *, profiles: PlayerProfileRepository, clubs: ClubDirectory
    ) -> None:
        self._profiles = profiles
        self._clubs = clubs

    async def from_player(
        self, player_id: UUID, club_ids: Collection[UUID]
    ) -> Mapping[UUID, float]:
        if not club_ids:
            return {}
        profile = await self._profiles.load(player_id)
        if profile is None:
            return {}
        here = Point(
            latitude=profile.location.latitude, longitude=profile.location.longitude
        )
        listed = await self._clubs.listed(club_ids)
        return {
            club_id: shown_kilometres(
                distance_km(
                    here, Point(latitude=club.latitude, longitude=club.longitude)
                )
            )
            for club_id, club in listed.items()
        }
