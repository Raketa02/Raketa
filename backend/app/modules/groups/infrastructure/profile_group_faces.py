"""``GroupFaces`` — a name from ``users``, a face from the Player profile.

The conversations' ``ProfileMemberFaces`` one context over, for the reason that
port gives for being a third spelling: it reads **each provider's own port** and
never its table or its bucket. The name comes from ``users``, which owns what an
account is called — the nickname beside it is left here, because a handle is
drawn on a record and said nowhere (``docs/adr/0171`` §4); the photo id comes
from the profile, which owns which photograph a person leads with; and the link
is signed by ``PhotoStorage``, which owns where the bytes live.

**Signing is arithmetic, not a request** (``docs/adr/0107``), so the faces a
group page draws cost no round trip to the store. A profile is a stream folded
per person, and a page asks for at most a court's worth per sport.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.modules.groups.domain.ports import GroupFace
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.users.domain.ports import UserRepository


class ProfileGroupFaces:
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

    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, GroupFace]:
        wanted = sorted(set(player_ids))
        if not wanted:
            return {}
        namings = await self._users.find_namings_of(wanted)
        faces: dict[UUID, GroupFace] = {}
        for player_id in wanted:
            naming = namings.get(player_id)
            photo_id = await self._first_photo(player_id)
            url = (
                None
                if photo_id is None
                else await self._photos.presigned_read_url(
                    PhotoRef(owner_id=player_id, photo_id=photo_id),
                    valid_for_seconds=self._photo_link_minutes * 60,
                )
            )
            faces[player_id] = GroupFace(
                player_id=player_id,
                name=None if naming is None else naming.name,
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
