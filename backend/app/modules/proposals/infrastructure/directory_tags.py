"""``PlayersTags`` over the player directory (``docs/adr/0207`` §11, #830):
**one statement for everybody asked**, however many cards they are on.

The directory is Discovery's copy of what each Player profile holds — one row
per player and tag, written from the profile's events and held equal to a
rebuild (``docs/adr/0204`` §10) — read here through Discovery's own published
``PlayerDirectory.tags_of_each``, never its table. Reading the copy, rather than
replaying every named player's profile stream on every deck read, is why no new
table was made for the Social vibe: the copy already existed.

**What a lagging copy costs**: a tag edit reaches the directory when its event
is delivered, so for that moment a card shows the vibe of the tags before it,
and somebody with no entry yet carries none. Nothing is stored here, so the
read after the delivery is right.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.discovery.domain.ports import PlayerDirectory
from app.modules.player_profile.domain.social_tags import SocialTag


@final
class DirectoryPlayersTags:
    def __init__(self, directory: PlayerDirectory) -> None:
        self._directory = directory

    async def tags_of(
        self, players: Collection[UUID]
    ) -> Mapping[UUID, frozenset[SocialTag]]:
        held = await self._directory.tags_of_each(players)
        # An id is permanent (the vocabulary's own rule), so a stored one is
        # always one the enum still holds.
        return {
            player: frozenset(SocialTag(tag) for tag in tags)
            for player, tags in held.items()
        }
