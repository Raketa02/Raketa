"""``OpenToNewPeople`` over the Player profile — *Show me to new people*, read
live off the profile's stream (``docs/adr/0204`` §2, #791), so a switch turned
off closes the record to strangers on the next tap."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.player_profile.domain.ports import PlayerProfileRepository


@final
class ProfileOpenToNewPeople:
    def __init__(self, profiles: PlayerProfileRepository) -> None:
        self._profiles = profiles

    async def open_to_new_people(self, subject_id: UUID) -> bool:
        profile = await self._profiles.load(subject_id)
        return profile is not None and profile.show_me_to_new_people


__all__ = ["ProfileOpenToNewPeople"]
