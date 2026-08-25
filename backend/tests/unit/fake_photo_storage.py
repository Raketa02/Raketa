"""An in-memory `PhotoStorage`, so no test needs MinIO running.

Shared rather than redefined per test file, for the reason the fake event store
is: a second fake is a second opinion about what the port promises, and the two
drift silently. The profile commit (#141) validates photo ids through this same
port and will want this same fake.

**What it deliberately does model:** ownership. Objects are keyed on the whole
`PhotoRef`, so asking for another player's photo id under your own identity
misses — which is the property the real adapter gets from putting the owner in
the key, and the one a test that keyed on the photo id alone would quietly lose.

**And the stamp.** A real store records when it took each object, and the sweep
(#142) is nothing but a question about that stamp — so this fake keeps one too,
read from a `now` a test may move rather than from the host's clock. Ageing a
photo here is setting `now` before storing it, which is the same act as
"this was uploaded yesterday" and needs no sleeping.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator, Mapping

from app.kernel import Instant, instant
from app.modules.player_profile.domain.photos import (
    PhotoRef,
    StoredPhoto,
    TranscodedImage,
)

#: What this store thinks the time is until a test says otherwise. A fixed
#: instant rather than the host clock, so a sweep test's arithmetic is readable
#: in the test rather than relative to whenever it happened to run.
DEFAULT_NOW: Instant = instant(datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc))


class StoredObject:
    def __init__(
        self,
        image: TranscodedImage,
        metadata: Mapping[str, str],
        stored_at: Instant,
    ) -> None:
        self.image = image
        self.metadata = dict(metadata)
        self.stored_at = stored_at


class InMemoryPhotoStorage:
    """Records what was stored, and signs URLs that are obviously fake."""

    #: What a presigned URL looks like here. Deliberately not a plausible S3 URL:
    #: a test that asserts on its *shape* is asserting on this fake rather than
    #: on the port, and it should be obvious in a failure message which it got.
    URL_PREFIX = "https://storage.invalid/"

    def __init__(self, *, now: Instant = DEFAULT_NOW) -> None:
        #: What this store stamps the next `put` with. A plain attribute a test
        #: assigns, because the port has no time argument and must not grow one:
        #: when an object was taken is the *store's* fact, not the caller's.
        self.now = now
        self.objects: dict[PhotoRef, StoredObject] = {}
        #: Every `valid_for_seconds` this was asked for, in order, so a test can
        #: assert the window the caller requested without parsing a URL.
        self.signed_windows: list[int] = []
        #: Every ref `exists` was asked about, in order. Counted rather than
        #: inferred from the objects, because "asked and told no" and "never
        #: asked" are the same state of the dict and a different fact about the
        #: caller — the profile commit's ordering of its checks turns on it.
        self.existence_checks: list[PhotoRef] = []
        #: Every ref `delete` was called on, in order and including the ones
        #: that were already gone. "Asked to delete something absent" is the
        #: concurrent-sweep case, and it is invisible in the objects dict.
        self.deletions: list[PhotoRef] = []

    async def put(
        self,
        ref: PhotoRef,
        image: TranscodedImage,
        *,
        metadata: Mapping[str, str],
    ) -> None:
        self.objects[ref] = StoredObject(image, metadata, self.now)

    async def exists(self, ref: PhotoRef) -> bool:
        self.existence_checks.append(ref)
        return ref in self.objects

    async def presigned_read_url(self, ref: PhotoRef, *, valid_for_seconds: int) -> str:
        # Signs whether or not the object is there, exactly as a real store does:
        # presigning is a signature, not a lookup. A `GetPhoto` that forgot to
        # check existence would therefore still get a URL back here, which is
        # what makes the not-found test meaningful.
        self.signed_windows.append(valid_for_seconds)
        return f"{self.URL_PREFIX}{ref.owner_id}/{ref.photo_id}"

    async def stored_before(
        self, cutoff: Instant
    ) -> AsyncGenerator[StoredPhoto, None]:
        # Yielded in owner-then-photo order, which is the order a real
        # S3 listing arrives in: keys are lexicographic and the owner is the
        # first variable component of one. A sweep that only reads each owner's
        # profile once relies on that grouping, so a fake that shuffled would
        # make the test pass for a reason production does not have.
        ordered = sorted(
            self.objects.items(),
            key=lambda item: (str(item[0].owner_id), str(item[0].photo_id)),
        )
        for ref, stored in ordered:
            if stored.stored_at < cutoff:
                yield StoredPhoto(ref=ref, stored_at=stored.stored_at)

    async def delete(self, ref: PhotoRef) -> None:
        # Absent is success, exactly as `DeleteObject` is: two sweeps racing on
        # the same orphan must both finish, and the loser deleting nothing is
        # the normal outcome rather than an error.
        self.deletions.append(ref)
        self.objects.pop(ref, None)

    def only_stored(self) -> StoredObject:
        """The single stored object, or a failure naming how many there are."""

        assert len(self.objects) == 1, (
            f"expected one stored photo, got {len(self.objects)}"
        )
        return next(iter(self.objects.values()))
