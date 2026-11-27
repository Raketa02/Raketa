"""Images built in memory, so no test depends on a binary checked into git.

A fixture file answers *does this one photo survive*. A generator answers *does
an image with this property survive* — and the properties are what the rules are
about: EXIF carrying GPS, an orientation tag, an alpha channel, a long edge past
the cap, and a header declaring dimensions that would decode to gigabytes.

Pillow authors the EXIF here rather than a second library doing it. Using the
same library the transcoder uses to *write* the metadata it must then fail to
find is deliberate: if Pillow could not really put GPS in the file, the stripping
test would pass by proving nothing.
"""

from __future__ import annotations

import io
import struct
import zlib
from fractions import Fraction

import pillow_heif
from PIL import ExifTags, Image

#: Somewhere in Warsaw. Any coordinate would do — what matters is that it is
#: really in the file before the transcoder sees it.
_LATITUDE = (Fraction(52), Fraction(13), Fraction(56))
_LONGITUDE = (Fraction(21), Fraction(0), Fraction(30))


def _gradient(width: int, height: int, mode: str = "RGB") -> Image.Image:
    """A non-uniform image, so JPEG cannot compress it to almost nothing.

    A solid colour would make every size assertion below meaningless — it
    encodes to a few hundred bytes at any dimension.
    """

    image = Image.new(mode, (width, height))
    pixels = image.load()
    assert pixels is not None
    for y in range(height):
        for x in range(width):
            value = ((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256)
            pixels[x, y] = value if mode == "RGB" else value + (255,)
    return image


def jpeg_with_gps_and_orientation(
    width: int = 60,
    height: int = 40,
    orientation: int = 6,
) -> bytes:
    """A JPEG carrying a GPS position, a camera make, and an orientation tag.

    Orientation 6 means *rotate 90° clockwise to display*, which is what a phone
    held upright writes. It is here so one fixture proves both halves of the
    rule: the tag is honoured, and then it is gone.
    """

    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = orientation
    exif[ExifTags.Base.Make] = "RakietaPhone"
    exif[ExifTags.Base.Model] = "Court 1"
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSLatitudeRef] = "N"
    gps[ExifTags.GPS.GPSLatitude] = _LATITUDE
    gps[ExifTags.GPS.GPSLongitudeRef] = "E"
    gps[ExifTags.GPS.GPSLongitude] = _LONGITUDE

    buffer = io.BytesIO()
    _gradient(width, height).save(buffer, "JPEG", exif=exif.tobytes())
    return buffer.getvalue()


def plain_jpeg(width: int = 60, height: int = 40) -> bytes:
    buffer = io.BytesIO()
    _gradient(width, height).save(buffer, "JPEG")
    return buffer.getvalue()


def png_with_alpha(width: int = 60, height: int = 40) -> bytes:
    """A PNG with a real alpha channel, half of it fully transparent."""

    image = _gradient(width, height, mode="RGBA")
    pixels = image.load()
    assert pixels is not None
    for y in range(height):
        for x in range(width // 2):
            pixels[x, y] = (0, 0, 0, 0)
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def heic(width: int = 60, height: int = 40) -> bytes:
    """A HEIF file — what an iPhone produces by default.

    Encoded through ``pillow_heif`` directly rather than through Pillow's save
    plugin, and that is the load-bearing detail: registering the HEIF opener is
    a global side effect, so a fixture that registered it would make the
    transcoder's own registration untestable — the decode would succeed either
    way. Written this way, a HEIC test failing to open is the adapter having
    forgotten to register, which is exactly what it should mean.
    """

    buffer = io.BytesIO()
    pillow_heif.from_pillow(_gradient(width, height)).save(buffer, format="HEIF")
    return buffer.getvalue()


def png_declaring(width: int, height: int) -> bytes:
    """A tiny PNG whose header *claims* `width` x `height`.

    The decompression bomb, made cheaply. A real 30000x30000 image would need
    2.7 GB to construct, which is precisely the allocation the transcoder must
    refuse — so the fixture forges the header instead and leaves the pixel data
    deliberately unusable. Nothing here is ever decoded: if the transcoder gets
    as far as reading a pixel, it has already failed the test it is in.
    """

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b"\x00" * 16))
        + chunk(b"IEND", b"")
    )


def not_an_image() -> bytes:
    return b"this is not an image, it is a sentence about one"


def truncated_jpeg() -> bytes:
    """A real JPEG cut off part-way — an upload that lost its connection."""

    whole = plain_jpeg(200, 200)
    return whole[: len(whole) // 3]
