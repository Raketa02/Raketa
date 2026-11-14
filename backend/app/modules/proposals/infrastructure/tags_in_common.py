"""``TagsInCommon`` over the Player profile — the tags' one owner, asked live
(#795): a request from *Same vibe players* says *6 things in common* as the
two stand when the card is read, never as they stood when it was sent."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.player_profile.domain.ports import PlayerProfileRepository


@final
class ProfileTagsInCommon:
    def __init__(self, profiles: PlayerProfileRepository) -> None:
        self._profiles = profiles

    async def in_common(
        self, reader: UUID, others: Collection[UUID]
    ) -> Mapping[UUID, int]:
        if not others:
            return {}
        mine = await self._tags_of(reader)
        return {other: len(mine & await self._tags_of(other)) for other in others}

    async def _tags_of(self, player_id: UUID) -> frozenset[str]:
        profile = await self._profiles.load(player_id)
        return frozenset(()) if profile is None else frozenset(profile.social_tags.ids)
