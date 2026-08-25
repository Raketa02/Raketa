"""What the transcoder keeps, what it drops, and what it refuses.

**The load-bearing one is the GPS test.** A photo taken on a phone carries the
coordinates it was taken at, and the product's privacy rules put a player's
precise location in the row nobody ever sees. Stripping it is not a nice-to-have
here, it is the reason bytes are re-encoded at all rather than stored as they
arrived (``docs/adr/0091``).

Every fixture is built in memory by `tests/unit/image_fixtures.py`, and each one
is checked to actually carry the property it is testing *before* it is
transcoded — a fixture that silently stopped carrying EXIF would make the
stripping assertion pass by proving nothing.
"""

from __future__ import annotations

import io

import pytest
from PIL import ExifTags, Image

from app.modules.player_profile.domain.errors import ImageTooLarge, UnreadableImage
from app.modules.player_profile.domain.photos import (
    MAX_STORED_LONG_EDGE_PX,
    STORED_MEDIA_TYPE,
)
from app.modules.player_profile.infrastructure.pillow_image_transcoder import (
    PillowImageTranscoder,
)
from tests.unit import image_fixtures as fixtures


def opened(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


# ---------------------------------------------------------------------------
# Metadata: the point of the whole adapter
# ---------------------------------------------------------------------------


async def test_the_fixture_really_carries_gps_before_it_is_transcoded() -> None:
    # The guard on every assertion below it. Without this, a fixture that
    # quietly stopped writing EXIF would turn the stripping test into a test
    # that an image with no metadata has no metadata.
    original = opened(fixtures.jpeg_with_gps_and_orientation())
    gps = original.getexif().get_ifd(ExifTags.IFD.GPSInfo)
    assert gps, "fixture no longer carries GPS — the tests below prove nothing"
    assert gps[ExifTags.GPS.GPSLatitudeRef] == "N"


async def test_gps_does_not_survive_the_transcode() -> None:
    image = await PillowImageTranscoder().transcode(
        fixtures.jpeg_with_gps_and_orientation()
    )

    stored = opened(image.data)
    assert stored.getexif().get_ifd(ExifTags.IFD.GPSInfo) == {}


async def test_no_exif_of_any_kind_survives_the_transcode() -> None:
    """Not only GPS. The make, the model, the timestamps — none of it.

    A stripper written as a list of tags is a list somebody has to keep
    complete; this asserts the structural claim instead, which is that nothing
    was carried across at all.
    """

    image = await PillowImageTranscoder().transcode(
        fixtures.jpeg_with_gps_and_orientation()
    )

    stored = opened(image.data)
    assert dict(stored.getexif()) == {}
    assert b"Exif\x00\x00" not in image.data


async def test_the_orientation_tag_is_applied_before_it_is_dropped() -> None:
    """The bug that makes naive stripping look like it worked.

    Orientation 6 means *rotate 90° to display*. A 60x40 file therefore means a
    40x60 photo, and a transcoder that dropped the tag without honouring it
    would store it 60x40 — sideways, forever, with no tag left to recover from.
    """

    image = await PillowImageTranscoder().transcode(
        fixtures.jpeg_with_gps_and_orientation(width=60, height=40, orientation=6)
    )

    assert (image.width, image.height) == (40, 60)


# ---------------------------------------------------------------------------
# Format: one goes out
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_fixture",
    [fixtures.plain_jpeg, fixtures.png_with_alpha, fixtures.heic],
    ids=["jpeg", "png", "heic"],
)
async def test_every_accepted_format_is_stored_as_jpeg(make_fixture) -> None:
    image = await PillowImageTranscoder().transcode(make_fixture())

    assert image.media_type == STORED_MEDIA_TYPE
    assert opened(image.data).format == "JPEG"


async def test_heic_decodes_at_all() -> None:
    """Proves the adapter registered the HEIF opener.

    The fixture encodes through ``pillow_heif`` directly and never registers the
    Pillow plugin, so this failing means the *adapter* forgot to — which is a
    silent, iPhone-only outage otherwise.
    """

    image = await PillowImageTranscoder().transcode(fixtures.heic(80, 50))

    assert (image.width, image.height) == (80, 50)


async def test_transparency_is_flattened_rather_than_encoded_as_noise() -> None:
    """JPEG has no alpha channel, and an unconverted RGBA image encodes wrong.

    The transparent half of the fixture must come out white — the colour a photo
    tile is rendered on — rather than as whatever the encoder made of an alpha
    channel it does not have.
    """

    image = await PillowImageTranscoder().transcode(
        fixtures.png_with_alpha(width=60, height=40)
    )

    stored = opened(image.data).convert("RGB")
    assert stored.mode == "RGB"
    red, green, blue = stored.getpixel((5, 5))
    assert min(red, green, blue) > 240


# ---------------------------------------------------------------------------
# Size
# ---------------------------------------------------------------------------


async def test_a_large_image_is_capped_on_its_long_edge() -> None:
    image = await PillowImageTranscoder().transcode(
        fixtures.plain_jpeg(width=2400, height=1200)
    )

    assert image.width == MAX_STORED_LONG_EDGE_PX
    assert image.height == MAX_STORED_LONG_EDGE_PX // 2
    assert opened(image.data).size == (image.width, image.height)


async def test_a_small_image_is_not_upscaled() -> None:
    image = await PillowImageTranscoder().transcode(fixtures.plain_jpeg(60, 40))

    assert (image.width, image.height) == (60, 40)


async def test_a_decompression_bomb_is_refused_without_being_decoded() -> None:
    """A 200-byte file that declares 30000x30000 — 2.7 GB of pixels.

    The refusal has to come from the *header*, before a pixel is allocated. If
    this test ever runs slowly or the process grows, the check has moved to the
    wrong side of the decode.
    """

    forged = fixtures.png_declaring(30_000, 30_000)
    assert len(forged) < 1024

    with pytest.raises(ImageTooLarge):
        await PillowImageTranscoder().transcode(forged)


async def test_an_image_just_past_the_decode_cap_is_refused() -> None:
    # 45 megapixels: inside Pillow's own hard error, outside this platform's
    # cap. It is the band that only our own check covers.
    with pytest.raises(ImageTooLarge):
        await PillowImageTranscoder().transcode(fixtures.png_declaring(9_000, 5_000))


# ---------------------------------------------------------------------------
# Bytes that are not an image
# ---------------------------------------------------------------------------


async def test_bytes_that_are_not_an_image_are_refused() -> None:
    with pytest.raises(UnreadableImage):
        await PillowImageTranscoder().transcode(fixtures.not_an_image())


async def test_a_truncated_upload_is_refused() -> None:
    # A real JPEG cut off part-way: the connection dropped mid-upload. It is
    # `unreadable_image` rather than `unsupported_image_format`, because the
    # client's recovery is to try the same photo again.
    with pytest.raises(UnreadableImage):
        await PillowImageTranscoder().transcode(fixtures.truncated_jpeg())


async def test_an_empty_body_is_refused() -> None:
    with pytest.raises(UnreadableImage):
        await PillowImageTranscoder().transcode(b"")
