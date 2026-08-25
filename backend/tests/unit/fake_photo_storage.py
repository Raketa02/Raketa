"""An in-memory `PhotoStorage`, so no test needs MinIO running.

Shared rather than redefined per test file, for the reason the fake event store
is: a second fake is a second opinion about what the port promises, and the two
drift silently. The profile commit (#141) validates photo ids through this same
port and will want this same fake.

**What it deliberately does model:** ownership. Objects are keyed on the whole
`PhotoRef`, so asking for another player's photo id under your own identity
misses — which is the property the real adapter gets from putting the owner in
the key, and the one a test that keyed on the photo id alone would quietly lose.
"""

from __future__ import annotations

from typing import Mapping

from app.modules.player_profile.domain.photos import PhotoRef, TranscodedImage


class StoredObject:
    def __init__(self, image: TranscodedImage, metadata: Mapping[str, str]) -> None:
        self.image = image
        self.metadata = dict(metadata)


class InMemoryPhotoStorage:
    """Records what was stored, and signs URLs that are obviously fake."""

    #: What a presigned URL looks like here. Deliberately not a plausible S3 URL:
    #: a test that asserts on its *shape* is asserting on this fake rather than
    #: on the port, and it should be obvious in a failure message which it got.
    URL_PREFIX = "https://storage.invalid/"

    def __init__(self) -> None:
        self.objects: dict[PhotoRef, StoredObject] = {}
        #: Every `valid_for_seconds` this was asked for, in order, so a test can
        #: assert the window the caller requested without parsing a URL.
        self.signed_windows: list[int] = []
        #: Every ref `exists` was asked about, in order. Counted rather than
        #: inferred from the objects, because "asked and told no" and "never
        #: asked" are the same state of the dict and a different fact about the
        #: caller — the profile commit's ordering of its checks turns on it.
        self.existence_checks: list[PhotoRef] = []

    async def put(
        self,
        ref: PhotoRef,
        image: TranscodedImage,
        *,
        metadata: Mapping[str, str],
    ) -> None:
        self.objects[ref] = StoredObject(image, metadata)

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

    def only_stored(self) -> StoredObject:
        """The single stored object, or a failure naming how many there are."""

        assert len(self.objects) == 1, (
            f"expected one stored photo, got {len(self.objects)}"
        )
        return next(iter(self.objects.values()))
