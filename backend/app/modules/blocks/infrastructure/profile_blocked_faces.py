"""``BlockedFaces`` — a name from ``users``, a face from the Player profile.

``groups``' ``ProfileGroupFaces`` one context over, for the reason that adapter
gives: it reads **each provider's own port** and never its table or its bucket.
The name comes from ``users``, the first photograph from the profile, and the
link is signed by ``PhotoStorage`` — arithmetic, not a request
(``docs/adr/0107``), so a list costs no round trip to the store.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.modules.blocks.domain.ports import BlockedFace
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.users.domain.ports import UserRepository


class ProfileBlockedFaces:
    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
        photo_link_minutes: int,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._photos = photos
        self._photo_link_minutes = photo_link_minutes

    async def faces_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, BlockedFace]:
        wanted = sorted(set(player_ids))
        if not wanted:
            return {}
        namings = await self._users.find_namings_of(wanted)
        faces: dict[UUID, BlockedFace] = {}
        for player_id in wanted:
            naming = namings.get(player_id)
            if naming is None:
                # Nobody to draw: the profile is not read for an id `users`
                # cannot name.
                faces[player_id] = BlockedFace(player_id=player_id)
                continue
            photo_id = await self._first_photo(player_id)
            url = (
                None
                if photo_id is None
                else await self._photos.presigned_read_url(
                    PhotoRef(owner_id=player_id, photo_id=photo_id),
                    valid_for_seconds=self._photo_link_minutes * 60,
                )
            )
            faces[player_id] = BlockedFace(
                player_id=player_id,
                name=naming.name,
                photo_id=None if url is None else photo_id,
                photo_url=url,
            )
        return faces

    async def _first_photo(self, player_id: UUID) -> UUID | None:
        """The photograph a face shows — **the first**, because order is meaning
        in a player's photo list. ``None`` draws their initials."""

        profile = await self._profiles.load(player_id)
        if profile is None or not profile.photo_ids:
            return None
        return profile.photo_ids[0]
