"""The address a record's photograph is drawn from, signed per response.

``RecordPhotoLink`` over the Player profile's own store, exactly as the card's
links are over theirs: where a photograph lives is that context's business, and a
key template written here would be a second answer to it that parts company on
the first layout change.

**Signing is arithmetic, not a request** — a signature over a request that is
never sent — so a record costs no round trip for its link, and this context can
go on storing nothing at all rather than keeping an address that dies within the
hour.

**And it never asks whether the object is still there.** That would be a round
trip before the response to turn a photograph removed since into a poster, and
the link expires in minutes in any case; a client that cannot survive an image
failing to load is already broken on the photograph it can see.

**The window is read from the platform's one photo setting**, so a record, a card
and ``GET /photos/{id}`` cannot come to three answers about how long a link may
live — and the route that declares this adapter does not get to name a number.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import PhotoStorage


@final
class PresignedRecordPhoto:
    """``RecordPhotoLink`` over the Player profile's photo store."""

    def __init__(self, *, storage: PhotoStorage, valid_for_minutes: int) -> None:
        self._storage = storage
        self._valid_for_minutes = valid_for_minutes

    async def link_for(self, *, owner_id: UUID, photo_id: UUID) -> str:
        """A short-lived URL for that photo, signed as **its owner**.

        The store keys the whole reference, so ownership is the port's contract
        rather than a check this caller has to remember: a link signed under the
        reader's id would reach an object that does not exist.
        """

        return await self._storage.presigned_read_url(
            PhotoRef(owner_id=owner_id, photo_id=photo_id),
            valid_for_seconds=self._valid_for_minutes * 60,
        )


__all__ = ["PresignedRecordPhoto"]
