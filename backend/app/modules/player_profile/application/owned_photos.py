"""One check, for the two writes that name photographs: each is the caller's.

The commit and the You tab's photos write both take a list of ids a client
holds and both must refuse an id the player never uploaded — or one belonging
to somebody else — rather than store a dangling reference no later read can
explain. It is written once here so that *exactly as the commit checks it* is
true by construction rather than by two loops kept in step.

**Through the same port and the same ``PhotoRef`` the upload used**, so
ownership is the port's contract rather than a check written twice: the ref
carries the owner, and another player's photo id answers exactly as an
imaginary one does (``domain/errors.py`` — ``PhotoNotFound`` says why the two
are one answer).
"""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from app.modules.player_profile.domain.errors import PhotoNotFound
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import PhotoStorage


async def check_photos_are_the_callers(
    photos: PhotoStorage, owner_id: UUID, photo_ids: Iterable[UUID]
) -> None:
    """Raise ``PhotoNotFound`` at the first id that is not this player's.

    Callers order and count the list first (``photo_order``), so the ids asked
    about are exactly the ids that will be recorded — a duplicate refused after
    three round trips would have been three round trips nobody needed.
    """

    for photo_id in photo_ids:
        if not await photos.exists(PhotoRef(owner_id=owner_id, photo_id=photo_id)):
            raise PhotoNotFound()
