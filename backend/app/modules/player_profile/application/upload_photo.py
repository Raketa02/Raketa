"""Accept one photo: check it, re-encode it, review it, store it, hand back a URL.

**One photo per request, and the id is the only thing that reaches the profile
commit.** Three multi-megabyte images inside that commit would turn an
idempotent JSON POST into a multipart upload whose failure took the whole part's
answers with it (``docs/adr/0091``). Separated, a failed upload costs one photo
and the step's retry is per tile.

The order of the five steps is load-bearing and each one is cheap before the one
after it: the declared type is rejected without touching the bytes, the byte cap
without decoding, the decode cap without allocating pixels, and only an image
that survives all three is reviewed and stored.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.kernel import Clock, minutes, shifted
from app.modules.player_profile.application.commands import UploadPhotoCommand
from app.modules.player_profile.domain.errors import (
    ImageTooLarge,
    UnsupportedImageFormat,
)
from app.modules.player_profile.domain.photos import (
    ACCEPTED_MEDIA_TYPES,
    MAX_UPLOAD_BYTES,
    PhotoRef,
    PhotoReviewVerdict,
    PresignedPhoto,
)
from app.modules.player_profile.domain.ports import (
    ImageTranscoder,
    PhotoReview,
    PhotoStorage,
)
from app.shared.ids import new_uuid

#: The metadata key the review verdict is stored under, beside the bytes.
REVIEW_METADATA_KEY = "review"

#: The metadata key the reviewer's machine-readable note is stored under, when
#: it gave one. Absent rather than empty when it did not.
REVIEW_NOTE_METADATA_KEY = "review-note"


@dataclass(frozen=True, slots=True)
class UploadedPhoto:
    """What the caller gets back: the id the commit will carry, and a URL now.

    The URL is here so that the step can render the tile it has just filled
    without a second round trip.
    """

    ref: PhotoRef
    presigned: PresignedPhoto
    review: PhotoReviewVerdict


class UploadPhoto:
    def __init__(
        self,
        *,
        storage: PhotoStorage,
        transcoder: ImageTranscoder,
        review: PhotoReview,
        clock: Clock,
        url_valid_for_minutes: int,
    ) -> None:
        self._storage = storage
        self._transcoder = transcoder
        self._review = review
        self._clock = clock
        self._url_valid_for_minutes = url_valid_for_minutes

    async def execute(self, command: UploadPhotoCommand) -> UploadedPhoto:
        if command.declared_media_type.lower() not in ACCEPTED_MEDIA_TYPES:
            raise UnsupportedImageFormat()
        if len(command.data) > MAX_UPLOAD_BYTES:
            raise ImageTooLarge()

        image = await self._transcoder.transcode(command.data)
        verdict = await self._review.review(image)

        # A flagged photo is **stored**, not refused. The real checker soft-warns
        # rather than hard-blocks (`docs/adr/0091`), and the verdict rides on the
        # object so that a moderation queue built later can find what it flagged
        # without a second table that can disagree with the blobs.
        metadata = {REVIEW_METADATA_KEY: verdict.decision.value}
        if verdict.note is not None:
            metadata[REVIEW_NOTE_METADATA_KEY] = verdict.note

        ref = PhotoRef(owner_id=command.owner_id, photo_id=new_uuid())
        await self._storage.put(ref, image, metadata=metadata)

        # One clock read for the whole command: the moment the window is measured
        # from is the moment it is reported from, so the two cannot disagree.
        issued_at = self._clock.now()
        url = await self._storage.presigned_read_url(
            ref, valid_for_seconds=self._url_valid_for_minutes * 60
        )
        return UploadedPhoto(
            ref=ref,
            presigned=PresignedPhoto(
                url=url,
                expires_at=shifted(issued_at, minutes(self._url_valid_for_minutes)),
            ),
            review=verdict,
        )
