"""What a photo is on its way in, and what the platform agrees to hold.

A player attaches up to three photos to their Player profile, or none
(``../../../../CONTEXT.md`` — *Profile photo*). This module is the policy that
governs the bytes: which formats a client may hand over, what is stored, how
large either may be, and how a stored photo is named.

**One format goes out, whatever came in.** Everything is re-encoded to JPEG on
receipt. That is not a storage optimisation — it is how EXIF is stripped
*reliably* rather than best-effort, and EXIF carries GPS, which the product's
own privacy rules put in the row nobody ever sees (``docs/adr/0091``). A
metadata-scrubbing pass over the original bytes would be a list of tags somebody
has to keep complete; a decode-and-re-encode carries nothing across that the
decoder did not understand as a pixel.

**Both caps are here rather than in configuration**, because both are rules a
domain test can observe. The environment may select configuration; it may never
select behaviour — a photo that is too large on a laptop and accepted in
production would be exactly that.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final
from uuid import UUID

from app.kernel import Instant

#: What a client may hand over. HEIC/HEIF is on the list because it is what an
#: iPhone produces by default, so leaving it off would refuse the majority of
#: photos taken on the platform's primary device.
#:
#: The two HEIF spellings are both here deliberately: iOS reports
#: ``image/heic``, some pickers and desktop tooling report ``image/heif``, and
#: they are the same container.
ACCEPTED_MEDIA_TYPES: Final = frozenset(
    {"image/jpeg", "image/png", "image/heic", "image/heif"}
)

#: What is stored. Always, for every accepted input — see the module docstring.
STORED_MEDIA_TYPE: Final = "image/jpeg"

#: The largest request body one photo may arrive in, before decoding. Eight
#: mebibytes is comfortably above a modern phone's full-resolution JPEG and far
#: below what would let one upload exhaust a container's memory.
MAX_UPLOAD_BYTES: Final = 8 * 1024 * 1024

#: The largest edge a stored photo may have. A profile photo is rendered at a
#: few hundred points on a phone; 1600 leaves room for a retina full-bleed and
#: nothing beyond it.
MAX_STORED_LONG_EDGE_PX: Final = 1600

#: The largest image the transcoder will decode, in pixels.
#:
#: **This is a separate cap from `MAX_UPLOAD_BYTES`, and it has to be.** Both
#: PNG and HEIF compress uniform data enormously, so a file well inside the byte
#: cap can decode to tens of gigabytes of raw pixels — the decompression bomb.
#: The byte cap cannot see it, because the file really is small; only a cap on
#: the *declared dimensions*, read before any pixel is decoded, can.
MAX_DECODED_PIXELS: Final = 40_000_000

#: How long a photo that no profile references is kept before it is swept
#: (``docs/adr/0091``, ``docs/adr/0092``).
#:
#: **Here rather than in configuration, with the two caps above and for the same
#: reason:** it is a rule a domain test can observe. A window that were 24 hours
#: on a laptop and one hour in production would be a *behaviour* the environment
#: selected, and the deletion it decides is not reversible.
#:
#: Twenty-four hours is not a tuned number and is not trying to be. The social
#: part of onboarding takes minutes, so anything an order of magnitude beyond
#: that belongs to a commit that never happened; the distance between *minutes*
#: and *a day* is what makes a wrong answer here need a client to have been
#: paused overnight mid-step, and even then the cost is re-picking a photo.
UNCOMMITTED_PHOTO_RETENTION_HOURS: Final = 24

#: Quality of the stored JPEG. High enough that re-encoding is not visible at
#: the size a photo is rendered, low enough that a stored photo is a fraction of
#: what arrived.
STORED_JPEG_QUALITY: Final = 85


@dataclass(frozen=True, slots=True)
class PhotoRef:
    """Which photo, and whose.

    **Every storage operation takes one of these, never a bare photo id**, so
    ownership is part of the port's contract rather than a check each caller has
    to remember. An adapter renders the pair however its store wants — the S3
    one puts the owner in the key prefix — and the consequence is the same
    either way: asking for another player's photo id under your own identity
    reaches an object that does not exist, rather than one you are not supposed
    to see.
    """

    owner_id: UUID
    photo_id: UUID


@dataclass(frozen=True, slots=True)
class TranscodedImage:
    """The bytes as the platform agreed to hold them: JPEG, capped, EXIF-free.

    Carries its dimensions because the reviewer and the storage adapter both
    want them and neither should have to decode the image again to find out.
    """

    data: bytes
    media_type: str
    width: int
    height: int


class PhotoReviewDecision(StrEnum):
    """What the review port concluded about an image.

    Two values, and there is deliberately no ``REJECTED``. The real on-court
    check **soft-warns rather than hard-blocks** (``docs/adr/0091``): in a
    product where a false reject stops a real player on their first day and a
    passed photo is currently seen by nobody, the two errors are not symmetric.
    Adding a blocking value later is an addition; shipping one now would be a
    behaviour nothing has earned.
    """

    ALLOWED = "allowed"
    FLAGGED = "flagged"


@dataclass(frozen=True, slots=True)
class PhotoReviewVerdict:
    """The review port's answer, recorded alongside the stored bytes.

    ``note`` is a machine-readable reason from the reviewer, never copy shown to
    a player — the backend emits codes and never display text
    (``docs/adr/0022``).
    """

    decision: PhotoReviewDecision
    note: str | None = None

    @property
    def is_flagged(self) -> bool:
        return self.decision is PhotoReviewDecision.FLAGGED


@dataclass(frozen=True, slots=True)
class StoredPhoto:
    """A photo the store is holding, and when it took it.

    What a listing yields, and the only thing the sweep needs about a candidate:
    which photo it is, whose it is, and whether it is old enough to be asked
    about. ``stored_at`` is the **store's** stamp — it is not carried in an
    event and there is nowhere else to read it from, which is why the port
    answers this question rather than the profile stream.

    Deliberately carries no size and no metadata. A sweep that could read the
    review verdict would invite a rule about flagged photos, and *whether a
    photo is referenced* is the only question this job is allowed to ask.
    """

    ref: PhotoRef
    stored_at: Instant


@dataclass(frozen=True, slots=True)
class PresignedPhoto:
    """A URL that grants read access to one photo, and when it stops working.

    Short-lived and per-photo, because a photo has a scoped audience in this
    product and a public object URL is an unscoped one — a difference that is
    not recoverable once the URLs are in the wild.
    """

    url: str
    expires_at: Instant


def scaled_to_the_long_edge(width: int, height: int) -> tuple[int, int]:
    """`(width, height)` scaled so the longer edge is at the cap, aspect kept.

    Pure, so the rule is testable without a decoder, and so the transcoder
    adapter holds no arithmetic of its own. Never upscales — an image already
    inside the cap comes back unchanged. Neither edge is ever rounded to zero: a
    very long, one-pixel-tall image stays one pixel tall rather than becoming
    an image with no area.
    """

    longest = max(width, height)
    if longest <= MAX_STORED_LONG_EDGE_PX:
        return width, height
    ratio = MAX_STORED_LONG_EDGE_PX / longest
    return max(1, round(width * ratio)), max(1, round(height * ratio))
