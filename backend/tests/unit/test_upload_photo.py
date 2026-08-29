"""Accepting one photo: what is checked, in what order, and what is recorded.

Storage is faked; **the transcoder is real**. Faking it would fake away the
EXIF stripping and the caps, which are the only interesting things that happen
to an uploaded photo — and re-encoding needs no container, so there is nothing
to gain by it.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.modules.player_profile.application.commands import UploadPhotoCommand
from app.modules.player_profile.application.upload_photo import (
    UploadPhoto,
)
from app.modules.player_profile.domain.errors import (
    ImageTooLarge,
    UnsupportedImageFormat,
)
from app.modules.player_profile.domain.photos import (
    MAX_UPLOAD_BYTES,
    REVIEW_METADATA_KEY,
    REVIEW_NOTE_METADATA_KEY,
    STORED_MEDIA_TYPE,
    PhotoReviewDecision,
    PhotoReviewVerdict,
    TranscodedImage,
)
from app.modules.player_profile.infrastructure.passthrough_photo_review import (
    PassThroughPhotoReview,
)
from app.modules.player_profile.infrastructure.pillow_image_transcoder import (
    PillowImageTranscoder,
)
from app.shared.ids import new_uuid
from tests.unit import image_fixtures as fixtures
from tests.unit.fake_event_store import FrozenClock, utc
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

NOW = utc(2026, 8, 25)
URL_MINUTES = 5


class FlaggingReview:
    """A reviewer that flags everything, so the flagged path has a driver."""

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        return PhotoReviewVerdict(
            decision=PhotoReviewDecision.FLAGGED, note="not_a_court"
        )


def use_case(
    *,
    storage: InMemoryPhotoStorage | None = None,
    review: object | None = None,
) -> UploadPhoto:
    return UploadPhoto(
        storage=storage or InMemoryPhotoStorage(),
        transcoder=PillowImageTranscoder(),
        review=review or PassThroughPhotoReview(),  # type: ignore[arg-type]
        clock=FrozenClock(at=NOW),
        url_valid_for_minutes=URL_MINUTES,
    )


def command(data: bytes | None = None, media_type: str = "image/jpeg"):
    return UploadPhotoCommand(
        owner_id=new_uuid(),
        data=fixtures.plain_jpeg() if data is None else data,
        declared_media_type=media_type,
    )


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------


async def test_a_photo_is_stored_under_the_uploading_player() -> None:
    storage = InMemoryPhotoStorage()

    uploaded = await use_case(storage=storage).execute(
        cmd := command(),
    )

    assert uploaded.ref.owner_id == cmd.owner_id
    assert uploaded.ref in storage.objects


async def test_what_is_stored_is_the_transcoded_bytes_not_what_arrived() -> None:
    storage = InMemoryPhotoStorage()
    original = fixtures.jpeg_with_gps_and_orientation()

    await use_case(storage=storage).execute(command(original))

    stored = storage.only_stored()
    assert stored.image.data != original
    assert stored.image.media_type == STORED_MEDIA_TYPE
    assert b"Exif\x00\x00" not in stored.image.data


async def test_every_upload_gets_its_own_id() -> None:
    # Two uploads of the identical bytes are two photos. Deduplicating by
    # content would make removing one photo remove another player's.
    storage = InMemoryPhotoStorage()
    uploader = use_case(storage=storage)
    data = fixtures.plain_jpeg()

    first = await uploader.execute(command(data))
    second = await uploader.execute(command(data))

    assert first.ref.photo_id != second.ref.photo_id
    assert len(storage.objects) == 2


async def test_a_url_is_returned_with_the_window_the_settings_asked_for() -> None:
    storage = InMemoryPhotoStorage()

    uploaded = await use_case(storage=storage).execute(command())

    assert uploaded.presigned.url.startswith(InMemoryPhotoStorage.URL_PREFIX)
    assert storage.signed_windows == [URL_MINUTES * 60]


async def test_the_expiry_is_the_clock_plus_the_window() -> None:
    # Read off the injected clock, never off a wall clock — which is what makes
    # the value assertable at all.
    uploaded = await use_case().execute(command())

    assert uploaded.presigned.expires_at == NOW + timedelta(minutes=URL_MINUTES)


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "media_type",
    ["image/gif", "image/webp", "application/pdf", "text/plain", ""],
)
async def test_a_format_outside_the_accepted_list_is_refused(media_type: str) -> None:
    with pytest.raises(UnsupportedImageFormat):
        await use_case().execute(command(media_type=media_type))


async def test_the_declared_format_is_read_case_insensitively() -> None:
    # `Image/JPEG` is a legal spelling of the same media type, and refusing it
    # would be refusing a correct client.
    uploaded = await use_case().execute(command(media_type="Image/JPEG"))

    assert uploaded.ref.photo_id is not None


async def test_the_declared_format_is_checked_before_the_bytes_are_touched() -> None:
    """A refused format never reaches the decoder.

    Asserted by handing it bytes that would crash a decoder: if the order ever
    inverts, this raises ``UnreadableImage`` instead and says so.
    """

    with pytest.raises(UnsupportedImageFormat):
        await use_case().execute(command(b"not an image", media_type="image/gif"))


async def test_a_body_past_the_byte_cap_is_refused() -> None:
    with pytest.raises(ImageTooLarge):
        await use_case().execute(command(b"\x00" * (MAX_UPLOAD_BYTES + 1)))


async def test_a_refused_upload_stores_nothing() -> None:
    storage = InMemoryPhotoStorage()

    with pytest.raises(UnsupportedImageFormat):
        await use_case(storage=storage).execute(command(media_type="image/gif"))

    assert storage.objects == {}


# ---------------------------------------------------------------------------
# The review seam
# ---------------------------------------------------------------------------


async def test_the_pass_through_reviewer_records_an_allowed_verdict() -> None:
    storage = InMemoryPhotoStorage()

    uploaded = await use_case(storage=storage).execute(command())

    assert uploaded.review.decision is PhotoReviewDecision.ALLOWED
    assert storage.only_stored().metadata == {REVIEW_METADATA_KEY: "allowed"}


async def test_a_flagged_photo_is_stored_rather_than_refused() -> None:
    """Soft-warn, never hard-block — `docs/adr/0091`.

    A false reject stops a real player on their first day, and a passed photo is
    currently seen by nobody, so the two errors are not symmetric.
    """

    storage = InMemoryPhotoStorage()

    uploaded = await use_case(storage=storage, review=FlaggingReview()).execute(
        command()
    )

    assert uploaded.review.is_flagged
    assert uploaded.ref in storage.objects


async def test_a_flagged_verdict_rides_on_the_object() -> None:
    # Beside the bytes rather than in a table of its own: a second store is a
    # second thing that can disagree about what was flagged.
    storage = InMemoryPhotoStorage()

    await use_case(storage=storage, review=FlaggingReview()).execute(command())

    assert storage.only_stored().metadata == {
        REVIEW_METADATA_KEY: "flagged",
        REVIEW_NOTE_METADATA_KEY: "not_a_court",
    }


async def test_a_verdict_without_a_note_writes_no_note_key() -> None:
    # Absent rather than empty: an empty string is a note that says nothing,
    # and something downstream would eventually render it.
    storage = InMemoryPhotoStorage()

    await use_case(storage=storage).execute(command())

    assert REVIEW_NOTE_METADATA_KEY not in storage.only_stored().metadata
