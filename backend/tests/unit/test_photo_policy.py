"""The photo rules that need no decoder, no store and no request.

These are the ones the profile commit will re-check and a sweep will rely on, so
they are asserted where they can be read in one screen rather than inferred from
an HTTP flow.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.player_profile.domain.photos import (
    ACCEPTED_MEDIA_TYPES,
    MAX_DECODED_PIXELS,
    MAX_STORED_LONG_EDGE_PX,
    MAX_UPLOAD_BYTES,
    STORED_MEDIA_TYPE,
    PhotoRef,
    PhotoReviewDecision,
    PhotoReviewVerdict,
    scaled_to_the_long_edge,
)
from app.modules.player_profile.infrastructure.s3_photo_storage import object_key_for

ALICE = UUID("11111111-1111-1111-1111-111111111111")
BOB = UUID("22222222-2222-2222-2222-222222222222")
PHOTO = UUID("33333333-3333-3333-3333-333333333333")


# ---------------------------------------------------------------------------
# What may arrive, and what is kept
# ---------------------------------------------------------------------------


def test_the_accepted_formats_are_the_four_a_phone_produces() -> None:
    # Written out rather than derived: adding a format is a decision about what
    # the platform will decode, and it should be argued with here first.
    assert ACCEPTED_MEDIA_TYPES == {
        "image/jpeg",
        "image/png",
        "image/heic",
        "image/heif",
    }


def test_heic_is_accepted_because_an_iphone_produces_it() -> None:
    # Called out on its own: dropping it would refuse the majority of photos
    # taken on the platform's primary device, and it would look like tidying.
    assert "image/heic" in ACCEPTED_MEDIA_TYPES
    assert "image/heif" in ACCEPTED_MEDIA_TYPES


def test_only_one_format_is_ever_stored() -> None:
    assert STORED_MEDIA_TYPE == "image/jpeg"


def test_the_decode_cap_is_a_separate_question_from_the_byte_cap() -> None:
    """A file inside the byte cap can still decode to gigabytes.

    Both PNG and HEIF compress uniform data enormously, so the two caps are not
    substitutes and neither implies the other. This asserts they are genuinely
    different numbers in different units, which is the shape of that claim.
    """

    assert MAX_UPLOAD_BYTES == 8 * 1024 * 1024
    assert MAX_DECODED_PIXELS == 40_000_000
    # A 40-megapixel image is far more than 8 MiB of raw pixels, which is the
    # whole reason the second cap has to exist.
    assert MAX_DECODED_PIXELS * 3 > MAX_UPLOAD_BYTES


# ---------------------------------------------------------------------------
# The long-edge rule
# ---------------------------------------------------------------------------


def test_an_image_inside_the_cap_is_unchanged() -> None:
    assert scaled_to_the_long_edge(800, 600) == (800, 600)


def test_an_image_exactly_at_the_cap_is_unchanged() -> None:
    assert scaled_to_the_long_edge(MAX_STORED_LONG_EDGE_PX, 900) == (
        MAX_STORED_LONG_EDGE_PX,
        900,
    )


def test_a_landscape_image_is_scaled_by_its_width() -> None:
    assert scaled_to_the_long_edge(4000, 2000) == (MAX_STORED_LONG_EDGE_PX, 800)


def test_a_portrait_image_is_scaled_by_its_height() -> None:
    assert scaled_to_the_long_edge(2000, 4000) == (800, MAX_STORED_LONG_EDGE_PX)


def test_a_small_image_is_never_upscaled() -> None:
    # Upscaling would spend storage inventing detail that is not in the file.
    assert scaled_to_the_long_edge(40, 30) == (40, 30)


def test_an_extreme_aspect_ratio_keeps_at_least_one_pixel() -> None:
    # A panorama's short edge rounds towards zero, and an image with no area is
    # one the encoder refuses — a crash rather than a refusal.
    width, height = scaled_to_the_long_edge(100000, 3)
    assert (width, height) == (MAX_STORED_LONG_EDGE_PX, 1)


# ---------------------------------------------------------------------------
# The review verdict
# ---------------------------------------------------------------------------


def test_the_review_has_no_blocking_decision() -> None:
    """Soft-warn, never hard-block — `docs/adr/0091`.

    A ``REJECTED`` member appearing here would be a behaviour change hiding in an
    enum, so the closed set is asserted rather than assumed.
    """

    assert {member.value for member in PhotoReviewDecision} == {"allowed", "flagged"}


def test_a_verdict_knows_whether_it_was_flagged() -> None:
    assert not PhotoReviewVerdict(PhotoReviewDecision.ALLOWED).is_flagged
    assert PhotoReviewVerdict(PhotoReviewDecision.FLAGGED, note="no_court").is_flagged


# ---------------------------------------------------------------------------
# Where a photo lives
# ---------------------------------------------------------------------------


def test_the_object_key_is_scoped_to_the_owner() -> None:
    """The same photo id under two players is two different objects.

    This is what makes *somebody else's photo id* answer *not found* rather than
    reaching an object the asking player has no business seeing — and it is a
    property of the key, so no caller can forget it.
    """

    assert object_key_for(ALICE, PHOTO) != object_key_for(BOB, PHOTO)
    assert str(ALICE) in object_key_for(ALICE, PHOTO)
    assert str(PHOTO) in object_key_for(ALICE, PHOTO)


def test_the_object_key_ends_in_the_stored_extension() -> None:
    # Everything is stored as JPEG, so a key that said `.png` would be a lie a
    # download tool would repeat.
    assert object_key_for(ALICE, PHOTO).endswith(".jpg")


def test_a_ref_is_hashable_and_compares_by_value() -> None:
    # The in-memory fake keys a dict on it, and so does anything else that wants
    # to hold a set of photos.
    assert PhotoRef(ALICE, PHOTO) == PhotoRef(ALICE, PHOTO)
    assert len({PhotoRef(ALICE, PHOTO), PhotoRef(ALICE, PHOTO)}) == 1
    assert PhotoRef(ALICE, PHOTO) != PhotoRef(BOB, PHOTO)
