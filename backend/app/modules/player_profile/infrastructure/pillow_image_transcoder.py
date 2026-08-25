"""Re-encode an uploaded image to the one stored format, with Pillow.

**The point of this adapter is what it does not carry across.** It decodes the
bytes to pixels and writes fresh JPEG from those pixels — so EXIF, XMP, IPTC,
ICC, thumbnails, maker notes and every other sidecar the original held are gone
because nothing copied them, rather than because a list of tags was deleted. A
scrubbing pass is a list somebody has to keep complete; this is structural
(``docs/adr/0091``). EXIF is not a detail here: it carries GPS, which is the
same class of data the product's privacy rules never show anybody.

**Orientation is applied before it is discarded.** A phone photo is very often
stored landscape with an EXIF tag saying *rotate this*. Dropping EXIF without
first honouring it would leave every such photo sideways — the bug that makes
naive metadata stripping look like it worked.
"""

from __future__ import annotations

import io

import anyio.to_thread
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from pillow_heif import register_heif_opener

from app.modules.player_profile.domain.errors import ImageTooLarge, UnreadableImage
from app.modules.player_profile.domain.photos import (
    MAX_DECODED_PIXELS,
    STORED_JPEG_QUALITY,
    STORED_MEDIA_TYPE,
    TranscodedImage,
    scaled_to_the_long_edge,
)

# HEIC is what an iPhone produces by default, and Pillow does not read it
# unaided. Registering the opener is a module-level side effect on purpose: it
# has to have happened before the first `Image.open`, and doing it per call
# would make the first decode's behaviour depend on construction order.
register_heif_opener()

# Pillow carries its own bomb guard, and left at its default it disagrees with
# ours in both directions: it *warns* at ~178 megapixels and decodes anyway,
# while an image this platform refuses at 40 passes it silently. Pointing it at
# our own cap makes the two agree by construction rather than by two numbers
# being maintained in step — Pillow then warns at exactly the size we refuse,
# and hard-errors at twice it, which is the backstop for a format whose declared
# size we somehow failed to read. That error is caught below and reported as the
# same refusal, so the backstop can never surface as a 500.
Image.MAX_IMAGE_PIXELS = MAX_DECODED_PIXELS


class PillowImageTranscoder:
    """Bytes in, capped EXIF-free JPEG out."""

    async def transcode(self, data: bytes) -> TranscodedImage:
        # Decoding and re-encoding a full-resolution photo is tens of
        # milliseconds of CPU. On the event loop that is tens of milliseconds
        # nothing else is served, per upload, so it goes to a worker thread —
        # which is also why the port is async while the work inside is not.
        return await anyio.to_thread.run_sync(self._transcode, data)

    def _transcode(self, data: bytes) -> TranscodedImage:
        try:
            with Image.open(io.BytesIO(data)) as source:
                # `Image.open` reads the header only, so the dimensions are known
                # before any pixel is allocated. That ordering is the whole
                # defence against a decompression bomb: a 40 KB PNG of uniform
                # colour can declare 30000x30000 and decode to 2.7 GB.
                width, height = source.size
                if width * height > MAX_DECODED_PIXELS:
                    raise ImageTooLarge()

                # Applied *before* it is discarded. A phone photo is very often
                # stored landscape with an EXIF tag saying *rotate this*, and
                # dropping the tag without honouring it leaves every such photo
                # sideways — the bug that makes naive stripping look like it
                # worked.
                upright = ImageOps.exif_transpose(source) or source

                target = scaled_to_the_long_edge(*upright.size)
                if target != upright.size:
                    upright = upright.resize(target, Image.Resampling.LANCZOS)

                # JPEG has no alpha channel and no palette. Converting rather
                # than letting the encoder guess is what keeps a transparent PNG
                # from arriving as noise: transparency is flattened onto white,
                # which is what a photo tile renders on.
                if upright.mode in ("RGBA", "LA", "PA"):
                    flattened = Image.new("RGB", upright.size, (255, 255, 255))
                    alpha = upright.convert("RGBA").getchannel("A")
                    flattened.paste(upright, mask=alpha)
                    upright = flattened
                elif upright.mode != "RGB":
                    upright = upright.convert("RGB")

                buffer = io.BytesIO()
                # No `exif=`, no `icc_profile=`, no `xmp=`. Pillow copies none of
                # them unless asked, and not asking is the mechanism.
                upright.save(
                    buffer,
                    format="JPEG",
                    quality=STORED_JPEG_QUALITY,
                    optimize=True,
                )
                return TranscodedImage(
                    data=buffer.getvalue(),
                    media_type=STORED_MEDIA_TYPE,
                    width=target[0],
                    height=target[1],
                )
        except DecompressionBombError as exc:
            # Pillow's backstop, above twice our cap. Same refusal as ours.
            raise ImageTooLarge() from exc
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            # A truncated upload, a file whose declared type is a lie, or bytes
            # that are not an image at all. `OSError` is Pillow's own spelling
            # for a broken file, so it cannot be narrowed further here.
            raise UnreadableImage() from exc
