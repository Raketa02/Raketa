"""Replace a player's photographs, whole and in order.

**The You tab's write** (``docs/adr/0179`` §6, §8), shipped with the tags' and
the intro's so that none of the three is editable while the others are frozen.
**Photos write on every change**: a player rearranging three photographs sends
three of these, each idempotent, and the last one is the state — the row is the
truth and a draft of it would be a second one (ADR-0179's consequences).

**Every id is re-checked against the same port the upload used, by the same
function the commit runs** (``owned_photos.py``): a ``PhotoRef`` carrying the
owner, so ownership is the port's contract, and another player's photo id
answers exactly as an imaginary one does. The check is paid on every write, the
same order included — the cost is a metadata request per photograph, at most
three, and a write that skipped it on the no-op path would be this layer
deciding what the aggregate decides.

**An empty list is a real answer and clears.** A profile may hold no
photograph; the poster returns on the card, and the photographs it let go of
become what the uncommitted-photo sweep collects — *referenced* is asked of the
profile, and they are no longer.

**The pure refusals come first.** ``photo_order`` refuses a duplicate and a
list over the cap before the object store is asked anything, so the ids
checked against storage are exactly the ids that will be recorded.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import ChangePhotosCommand
from app.modules.player_profile.application.owned_photos import (
    check_photos_are_the_callers,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.player_profile.domain.profile import PlayerProfile, photo_order


class ChangePhotos:
    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._profiles = profiles
        self._photos = photos
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangePhotosCommand) -> PlayerProfile:
        # Ordered and counted before anything is loaded or asked: a duplicate
        # refused after three existence checks would have been three checks
        # nobody needed.
        photo_ids = photo_order(command.photo_ids)

        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        await check_photos_are_the_callers(self._photos, command.player_id, photo_ids)

        profile.change_photos(photo_ids, occurred_at=instant(self._clock.now()))
        await self._profiles.save(profile)
        await self._uow.commit()
        return profile
