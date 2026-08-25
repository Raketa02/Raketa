"""Hand back a short-lived URL for a photo the asking player owns.

**The bytes never pass through this application.** Serving them here would put a
multi-megabyte read on the API's event loop for every tile rendered, and it
would make the API the thing that has to scale with the photo corpus. A
presigned URL is the store answering directly, for a window, to whoever holds
the URL — which is why the window is short (``docs/adr/0091``).

Existence is checked before the URL is signed. Signing is pure computation in
every S3-compatible store, so an unchecked endpoint would happily hand back a
working-looking URL for a photo that is not there, and the failure would surface
as a broken image on a phone rather than as a 404 a client can act on.
"""

from __future__ import annotations

from app.kernel import Clock, minutes, shifted
from app.modules.player_profile.application.commands import GetPhotoCommand
from app.modules.player_profile.domain.errors import PhotoNotFound
from app.modules.player_profile.domain.photos import PhotoRef, PresignedPhoto
from app.modules.player_profile.domain.ports import PhotoStorage


class GetPhoto:
    def __init__(
        self,
        *,
        storage: PhotoStorage,
        clock: Clock,
        url_valid_for_minutes: int,
    ) -> None:
        self._storage = storage
        self._clock = clock
        self._url_valid_for_minutes = url_valid_for_minutes

    async def execute(self, command: GetPhotoCommand) -> PresignedPhoto:
        ref = PhotoRef(owner_id=command.owner_id, photo_id=command.photo_id)
        if not await self._storage.exists(ref):
            # The same answer a stranger's photo id gets — see `PhotoNotFound`.
            raise PhotoNotFound()

        issued_at = self._clock.now()
        url = await self._storage.presigned_read_url(
            ref, valid_for_seconds=self._url_valid_for_minutes * 60
        )
        return PresignedPhoto(
            url=url,
            expires_at=shifted(issued_at, minutes(self._url_valid_for_minutes)),
        )
