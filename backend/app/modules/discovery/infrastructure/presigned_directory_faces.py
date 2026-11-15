"""``DirectoryFaces`` — a link signed by ``PhotoStorage`` for a photograph the
directory names, over the same port every face is signed through — a
signature, never a round trip, as the record's link is."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import PhotoStorage


@final
class PresignedDirectoryFaces:
    def __init__(self, *, photos: PhotoStorage, photo_link_minutes: int) -> None:
        self._photos = photos
        self._photo_link_minutes = photo_link_minutes

    async def photo_url(self, player_id: UUID, photo_id: UUID) -> str:
        return await self._photos.presigned_read_url(
            PhotoRef(owner_id=player_id, photo_id=photo_id),
            valid_for_seconds=self._photo_link_minutes * 60,
        )
