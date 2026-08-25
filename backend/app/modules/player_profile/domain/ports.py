"""The three seams the photo path is built on.

Each is here rather than in ``app/application/ports/`` because each is the
Player profile context's own: a photo belongs to a profile, and no other context
has one. Cross-cutting ports — the unit of work, the event store, the publisher
— stay where they are.

**Nothing in this file names a vendor.** ``PhotoStorage`` says *put these bytes
under this reference and give me a short-lived URL for them*; whether that is
MinIO on a laptop or S3 in a deployed environment is the composition root's
answer and is invisible from here (``docs/adr/0091``).
"""

from __future__ import annotations

from typing import Mapping, Protocol

from app.modules.player_profile.domain.photos import (
    PhotoRef,
    PhotoReviewVerdict,
    TranscodedImage,
)


class PhotoStorage(Protocol):
    """Where a photo's bytes live.

    Every method takes a ``PhotoRef``, which carries the owner — so a store
    cannot be asked a question that is not scoped to a player, and an adapter
    cannot forget to scope one.
    """

    async def put(
        self,
        ref: PhotoRef,
        image: TranscodedImage,
        *,
        metadata: Mapping[str, str],
    ) -> None:
        """Store `image` at `ref`, replacing anything already there.

        ``metadata`` is small, non-pixel context the store keeps beside the
        bytes — today the review verdict, so a photo the reviewer flagged is
        findable later without a second table to keep in step with the blobs.
        """
        ...

    async def exists(self, ref: PhotoRef) -> bool:
        """Whether this player has a photo with this id.

        The profile commit re-validates every photo id it is handed through this
        (``docs/adr/0089``): a client that sends an id it never uploaded, or one
        belonging to somebody else, must be refused rather than trusted.
        """
        ...

    async def presigned_read_url(self, ref: PhotoRef, *, valid_for_seconds: int) -> str:
        """A URL that reads this photo and stops working after the window.

        Pure computation in every S3-compatible store — a signature, not a round
        trip — so it says nothing about whether the object is there. Callers
        that need to know ask ``exists`` first.
        """
        ...


class ImageTranscoder(Protocol):
    """Bytes in, the one stored format out.

    A port rather than a function call because it is the only thing on the
    upload path that needs an imaging library, and a use case that imported one
    would be an application layer depending on an adapter. It stays *real* in
    tests while storage is faked: re-encoding is pure and needs no container, and
    faking it would fake away the EXIF stripping that is the point of it.
    """

    async def transcode(self, data: bytes) -> TranscodedImage:
        """Decode `data`, apply its orientation, cap its long edge, re-encode.

        Raises the module's ``UnreadableImage`` for bytes no supported decoder
        understands, and ``ImageTooLarge`` for an image whose declared
        dimensions exceed the decode cap — checked before any pixel is read, so
        a decompression bomb is refused rather than decoded.
        """
        ...


class PhotoReview(Protocol):
    """Whether a photo looks like the product's rule says it should.

    The rule is that a photo shows a racket sport on a court. **Nothing enforces
    it today** — the pass-through adapter allows everything, and the screen's
    copy states the rule without claiming an enforcement that is not running
    (``docs/adr/0091``). The seam exists from day one so that adding the real
    checker changes no call site.
    """

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict: ...
