"""Delete photos that were uploaded and never committed to a profile.

**Uploading is not attaching.** A photo id becomes part of a profile only when a
commit names it (``domain/errors.py`` — ``TooManyPhotos``), so every upload
leaves behind an object that nothing references yet, and the ones whose commit
never came reference nothing forever. They are paid-for storage holding a
stranger's face attached to no account state, and without this they accumulate
for the life of the platform (``docs/adr/0091``).

**The window is what makes the question answerable at all.** *Is this photo
about to be committed* is unknowable; *was this photo uploaded more than a day
ago* is a fact the store already holds. The social part of onboarding takes
minutes, so the two questions only disagree for a client that was paused
overnight mid-step — and the cost of being wrong there is re-picking a photo
(``domain/photos.py`` — ``UNCOMMITTED_PHOTO_RETENTION_HOURS``).

**Referenced is asked of the profile, per owner, once.** The candidates arrive
grouped by owner because the store lists them that way, so one replay answers
for all of that player's photos. A profile stream is written every time somebody
adjusts their week, for years (``domain/profile.py``), and replaying one per
candidate would cost the corpus times the stream.

**Idempotent and safe beside itself, with no lock anywhere.** Every step is a
question about state the sweep does not own: the listing is a read, the
reference check is a read, and deleting an object that is already gone is
success in every S3-compatible store. Two sweeps handed the same orphan both
finish; a second run over a swept bucket finds nothing to examine. That is why
ADR-0092 could put this on an interval in every API process rather than
inventing a leader election for it.

**The race it does not close, stated rather than hidden.** A commit that names a
photo *between* this sweep's reference check and its delete would lose that
photo. Closing it would mean a lock over the object store and the profile
stream together — and the window it would close is microseconds wide, reachable
only by a client that uploaded a photo, waited a full day, and then committed
during them. The refusal to build that is deliberate; the recovery, if it ever
happens, is that the player's tile is empty and they pick the photo again.
"""

from __future__ import annotations

from contextlib import aclosing
from dataclasses import dataclass
from uuid import UUID

from app.kernel import Clock, hours, instant, shifted
from app.modules.player_profile.domain.photos import (
    UNCOMMITTED_PHOTO_RETENTION_HOURS,
)
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)


@dataclass(frozen=True, slots=True)
class PhotoSweepReport:
    """What one run did, for the log line that is its only output.

    ``examined`` counts the photos that were **old enough to be asked about**,
    not everything in the bucket — a listing the sweep never had to judge is not
    work it did. The pair is what makes a run readable at a glance: a steady
    ``examined`` with a zero ``deleted`` is a bucket of committed photos and
    healthy; a ``deleted`` that never falls is onboarding being abandoned, which
    is a product signal rather than a storage one.
    """

    examined: int
    deleted: int


class SweepUncommittedPhotos:
    def __init__(
        self,
        *,
        storage: PhotoStorage,
        profiles: PlayerProfileRepository,
        clock: Clock,
    ) -> None:
        self._storage = storage
        self._profiles = profiles
        self._clock = clock

    async def execute(self) -> PhotoSweepReport:
        # One clock read for the whole run. A cutoff that moved while the bucket
        # was being walked would make *how old is old* depend on how far through
        # the listing a photo happened to be.
        cutoff = shifted(
            instant(self._clock.now()), hours(-UNCOMMITTED_PHOTO_RETENTION_HOURS)
        )

        # Owner -> the photo ids their committed profile currently names. Grown
        # as the listing walks, and bounded by the number of players holding an
        # old photo rather than by the corpus.
        referenced: dict[UUID, frozenset[UUID]] = {}
        examined = 0
        deleted = 0

        # `aclosing` rather than a bare `async for`, and it is not decoration.
        # The listing is an async generator holding an open store client; a
        # `delete` or a replay that raises inside this loop would abandon it
        # un-closed, leaving that client to be finalised whenever the loop got
        # round to it. The job above swallows the failure and ticks again, so
        # the leak would be one client per failed run rather than one ever.
        async with aclosing(self._storage.stored_before(cutoff)) as candidates:
            async for candidate in candidates:
                examined += 1
                owner_id = candidate.ref.owner_id
                if owner_id not in referenced:
                    referenced[owner_id] = await self._photos_named_by(owner_id)

                if candidate.ref.photo_id in referenced[owner_id]:
                    continue

                await self._storage.delete(candidate.ref)
                deleted += 1

        return PhotoSweepReport(examined=examined, deleted=deleted)

    async def _photos_named_by(self, owner_id: UUID) -> frozenset[UUID]:
        """The photo ids this player's profile holds **now**.

        The current list, not every id the stream ever mentioned. A photo
        dropped from a profile is as unreachable as one that was never
        committed — nothing can render it and no later read can explain it — so
        it is the same orphan and gets the same answer.

        No profile at all is the ordinary state of an abandoned onboarding, and
        it means nothing is referenced rather than that something went wrong.
        """

        profile = await self._profiles.load(owner_id)
        return frozenset(profile.photo_ids) if profile is not None else frozenset()
