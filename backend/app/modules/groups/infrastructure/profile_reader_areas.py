"""``ReaderAreas`` over the Player profile's own repository.

**The Location area and nothing finer**, because nothing finer exists: the
profile coarsens a device's fix on the way in (``player_profile/domain/
location.py``), so the distance to a club is measured from the reader's cell.
A player with no committed profile has no Location area and gets ``None``.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.groups.domain.ports import ReaderArea
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class ProfileReaderAreas:
    def __init__(self, profiles: PlayerProfileRepository) -> None:
        self._profiles = profiles

    async def of(self, player_id: UUID) -> ReaderArea | None:
        profile = await self._profiles.load(player_id)
        if profile is None:
            return None
        return ReaderArea(
            latitude=profile.location.latitude,
            longitude=profile.location.longitude,
        )
