"""``RankedFaces`` — a nickname from ``users``, the first photograph from the
Player profile, a link signed by ``PhotoStorage``: Friends' faces, read here
through the same three providers, each over its own port."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.rankings.domain.ports import RankedFace
from app.modules.users.domain.ports import UserRepository


@final
class ProfileRankedFaces:
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

    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, RankedFace]:
        wanted = sorted(set(player_ids), key=str)
        if not wanted:
            return {}
        nicknames = await self._users.find_nicknames_of(wanted)
        faces: dict[UUID, RankedFace] = {}
        for player_id in wanted:
            nickname = nicknames.get(player_id)
            if nickname is None:
                faces[player_id] = RankedFace(player_id=player_id)
                continue
            profile = await self._profiles.load(player_id)
            photo_id = (
                profile.photo_ids[0]
                if profile is not None and profile.photo_ids
                else None
            )
            url = (
                None
                if photo_id is None
                else await self._photos.presigned_read_url(
                    PhotoRef(owner_id=player_id, photo_id=photo_id),
                    valid_for_seconds=self._photo_link_minutes * 60,
                )
            )
            faces[player_id] = RankedFace(
                player_id=player_id,
                nickname=nickname,
                photo_id=None if url is None else photo_id,
                photo_url=url,
            )
        return faces
