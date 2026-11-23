"""``TagsOnTheCourt`` over the player directory (``docs/adr/0207`` §11, #835):
**one statement for the whole court.**

The directory is Discovery's copy of what each Player profile holds — one row
per player and tag, written from the profile's events and held equal to a
rebuild (``docs/adr/0204`` §10) — read here through Discovery's own published
``PlayerDirectory.tags_of_each``, never its table: the same copy, and the same
read, a For-fun card's vibe is worked out from (Proposals' ``PlayersTags``), so
the booked game and the card it was cannot read two different tag sets.
Replaying four profile streams on every pairing read is what the copy spares.

**What a lagging copy costs**: a tag edit reaches the directory when its event
is delivered, so for that moment the game shows the vibe of the tags before
it, and somebody with no entry yet carries none. Nothing is stored here, so
the read after the delivery is right.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.discovery.domain.ports import PlayerDirectory
from app.modules.player_profile.domain.social_tags import SocialTag


@final
class DirectoryTagsOnTheCourt:
    def __init__(self, directory: PlayerDirectory) -> None:
        self._directory = directory

    async def held_by(
        self, players: Collection[UUID]
    ) -> Mapping[UUID, frozenset[SocialTag]]:
        held = await self._directory.tags_of_each(players)
        # An id is permanent (the vocabulary's own rule), so a stored one is
        # always one the enum still holds.
        return {
            player: frozenset(SocialTag(tag) for tag in tags)
            for player, tags in held.items()
        }


__all__ = ["DirectoryTagsOnTheCourt"]
