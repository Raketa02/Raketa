"""The three answers a card can carry about a photograph, and how a seed reaches
them.

``docs/adr/0138`` gives a card three states and only two of them are a word: a
photo the check passed draws the shield, a photo it flagged draws nothing, and a
photo **nobody looked at** draws nothing either — spelled as the *absence* of a
verdict rather than as a third value on ``PhotoReviewDecision``. Two of the three
are therefore indistinguishable on the wire and distinguishable only in the
store, which is exactly the shape a fixture exists for: a developer meeting the
missing shield has no way to tell *flagged* from *unchecked* unless a database
holds one of each to compare.

**The reviewer is a port and the verdict is declared, which is the same move the
run already makes with the clock** (``app/seeds/clock.py``). A seeded photograph
is not a photograph of a real court, so asking the real sidecar what it thinks
would exhibit whichever states that model happened to reach on a synthetic image
— and *whichever* is the one thing a workbench may not be. What is declared is
the *conclusion*; how a conclusion becomes metadata is the domain's, through its
own constructors, so a seeded shield is one ``decision_on_record`` agrees to
believe rather than a string this module spelled.

**The bytes are generated rather than committed, and generated with the standard
library.** A photograph in the repository would be a binary blob in a diff, a
licence question, and a face; a flat square drawn here is none of those and
answers the only question the upload path asks of it — that it decodes. It is
deliberately not a picture of anything: nothing in this fixture should ever be
mistaken for evidence about what the check does.

**No imaging library, and that is the rule rather than an economy.** ADR-0091
puts the re-encode behind ``ImageTranscoder`` and fences ``PIL`` out of the
layers that must not know one exists; a fixture reaching for it to *make* an
image would be the only such import outside that adapter, and nothing would name
the exception. A PNG is a signature and three chunks with a CRC apiece, which
``zlib`` and ``struct`` write between them — and the platform's own transcoder
then turns it into the JPEG that is actually stored, which is the point of
handing it something to decode at all.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Collection
from contextlib import aclosing
from enum import Enum
from typing import Final, final
from uuid import NAMESPACE_URL, UUID, uuid5

from app.modules.player_profile.domain.photos import (
    ACCEPTED_MEDIA_TYPES,
    ON_COURT_PROMPTS,
    PHOTO_REVIEW_PROMPTS,
    PhotoRef,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    TranscodedImage,
    recorded_score_in,
    verdict_from_similarities,
    verdict_when_unreviewable,
)
from app.modules.player_profile.domain.ports import PhotoStorage

#: What the seed says reviewed its photographs. A name rather than a model, and
#: it says so: nothing scored these images, and the note a card's shield is
#: believed on carries this string where a real model's name would be.
SEED_REVIEW_MODEL: Final = "seed-declared"

#: Why the one unreviewed photograph was not reviewed. ``TRANSPORT`` because
#: that is the shape of the population this state was written for — a photo that
#: arrived while the sidecar was unreachable — and the code is what
#: ``docs/adr/0132``'s re-review pass finds them by.
SEED_REVIEW_OUTAGE: Final = PhotoReviewUnavailability.TRANSPORT

#: The two similarities a declared verdict is built from, as the share of the
#: probability mass the on-court captions carry. **Far from the threshold on
#: both sides**, so a retune of ``ON_COURT_CONFIDENCE_THRESHOLD`` moves the
#: number rather than flipping this fixture's states — which is the same reason
#: the cohort's two commit windows are both clear of ADR-0113's fourteen days.
CLEARLY_ON_A_COURT: Final = 4.0
CLEARLY_NOT_A_COURT: Final = -4.0

#: The image the seed uploads: one flat square, large enough that the transcoder
#: has something to decode and small enough that thirty of them would still be
#: nothing. Not a picture of a court, on purpose.
SEED_IMAGE_EDGE_PX: Final = 64
SEED_IMAGE_COLOUR: Final = (94, 126, 88)

#: What every PNG starts with, and the two chunks that bracket the pixels.
#: Written out because this module writes a PNG rather than asking a library to.
_PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
#: 8-bit colour, no interlace — the plainest of the format's fifteen combinations
#: and the one every decoder has always read.
_PNG_BIT_DEPTH: Final = 8
_PNG_TRUECOLOUR: Final = 2
#: The three trailing header fields, each of which the format defines exactly one
#: value for: deflate, adaptive filtering, no interlace. Named rather than left as
#: three bare zeros in a ``struct.pack``, where a reader cannot tell which is
#: which and a transposition would be invisible.
_PNG_DEFLATE: Final = 0
_PNG_ADAPTIVE_FILTERING: Final = 0
_PNG_NO_INTERLACE: Final = 0
#: The scanline filter this writer uses. A PNG row may be encoded against the row
#: above it; a flat square gains nothing from that, and a reader of `an_image`
#: should not have to know which of the five was chosen.
_PNG_FILTER_NONE: Final = 0


@final
class DeclaredVerdict(str, Enum):
    """What this fixture says the check concluded about one photograph.

    **Three names where ``PhotoReviewDecision`` has two**, and the third is the
    one that carries no decision at all. It is a *seed* vocabulary rather than a
    second spelling of the platform's: the enum a card reads has two values
    because *nobody looked* is not a conclusion about an image, and what is named
    here is the three **states a card can be in**, which is one more thing than
    the reviewer can conclude.
    """

    #: The check passed, and the card draws the shield.
    ON_A_COURT = "ON_A_COURT"
    #: The check flagged it, and the card draws nothing.
    NOT_A_COURT = "NOT_A_COURT"
    #: Nothing ever looked at it, and the card draws nothing — the same silence
    #: as above, from the opposite cause.
    NOBODY_LOOKED = "NOBODY_LOOKED"


def verdict_for(declared: DeclaredVerdict) -> PhotoReviewVerdict:
    """The platform's own verdict object for one declared state.

    Built through ``verdict_from_similarities`` and ``verdict_when_unreviewable``
    rather than by naming a decision and writing a note beside it. A shield is
    only drawn where the stored note proves a score was taken — model, prompt
    set, confidence and raw vector, all four — so a fixture that assembled the
    note by hand would be a fixture asserting its own spelling of somebody else's
    format, and it would rot silently the day that format grew a field.
    """

    if declared is DeclaredVerdict.NOBODY_LOOKED:
        return verdict_when_unreviewable(SEED_REVIEW_OUTAGE)
    return verdict_from_similarities(
        model=SEED_REVIEW_MODEL, similarities=_similarities(declared)
    )


def _similarities(declared: DeclaredVerdict) -> tuple[float, ...]:
    """One similarity per prompt, weighted onto the block the state names.

    ``verdict_from_similarities`` refuses an answer that is not one number per
    caption — a reviewer that answered a different number of questions than it
    was asked has not answered *these* — so the vector is built from the live
    prompt set rather than written out, and a prompt added to either block moves
    this with it.
    """

    on_court = (
        CLEARLY_ON_A_COURT
        if declared is DeclaredVerdict.ON_A_COURT
        else CLEARLY_NOT_A_COURT
    )
    return tuple(
        on_court if index < len(ON_COURT_PROMPTS) else -on_court
        for index in range(len(PHOTO_REVIEW_PROMPTS))
    )


@final
class DeclaredPhotoReview:
    """``PhotoReview``, answering what this fixture declared about this photo.

    One reviewer per photograph rather than a map from bytes to verdicts,
    because the upload use case hands the port an *image* and two seeded images
    are byte-identical — the fixture's declaration is about the member, and the
    member is what the caller knows.
    """

    def __init__(self, declared: DeclaredVerdict) -> None:
        self._verdict = verdict_for(declared)

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        return self._verdict


def an_image() -> bytes:
    """The bytes one seeded photograph arrives as. **A flat PNG square.**

    Generated rather than committed, and declared as one of the media types a
    client may hand over — the upload refuses anything else before it touches
    the bytes, so a fixture whose image was not on that list would be refused
    for the wrong reason. What is *stored* is the JPEG the platform's own
    transcoder makes of it, which is the whole point of handing the upload path
    something to decode.
    """

    # One filter byte per scanline, then that row's pixels three bytes apiece.
    row = bytes([_PNG_FILTER_NONE]) + bytes(SEED_IMAGE_COLOUR) * SEED_IMAGE_EDGE_PX
    header = struct.pack(
        ">IIBBBBB",
        SEED_IMAGE_EDGE_PX,
        SEED_IMAGE_EDGE_PX,
        _PNG_BIT_DEPTH,
        _PNG_TRUECOLOUR,
        _PNG_DEFLATE,
        _PNG_ADAPTIVE_FILTERING,
        _PNG_NO_INTERLACE,
    )
    return (
        _PNG_SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(row * SEED_IMAGE_EDGE_PX))
        + _chunk(b"IEND", b"")
    )


def _chunk(name: bytes, payload: bytes) -> bytes:
    """One PNG chunk: its length, its name, its bytes and a CRC over both.

    The CRC is over the **name and the payload** and not over the length, which
    is the one thing about the format that is easy to get subtly wrong — and a
    chunk whose CRC is wrong is an image every decoder refuses, which would
    surface as an upload the platform rejected rather than as a fixture bug.
    """

    return (
        struct.pack(">I", len(payload))
        + name
        + payload
        + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
    )


#: The photograph the probe below asks about. **Nobody's, and nothing wrote
#: it**, so the store's honest answer is *no* — which is what makes the question
#: *can you answer at all* rather than *is this here*.
NOBODY: Final = uuid5(NAMESPACE_URL, "https://raketa.example/seeds/no-such-photo")


async def the_store_answers(photos: PhotoStorage) -> bool:
    """Whether the object store can be reached. **Asked once, for the whole run.**

    An unreachable store is the **environment** and never the fixture, and the
    two have to be told apart out loud: a seed run that died on a photograph
    would take a whole population with it because a container was not up, and one
    that quietly wrote no photographs would leave a developer looking for the
    shield on a card that never had one. So the question is asked once, the
    photographs are skipped when the answer is no, and the run says so on its
    report.

    **It catches broadly, deliberately**, exactly as ``fail_soft_ledgers`` does:
    a store that refuses a connection, one that times out and one that answers
    something the adapter cannot read are the same event here — it could not be
    consulted — and there is no vendor exception this package is allowed to name
    anyway, because the adapter is somebody else's and the seed may not import
    its internals.
    """

    try:
        await photos.exists(PhotoRef(owner_id=NOBODY, photo_id=NOBODY))
    except Exception:
        return False
    return True


async def reviewed_since_the_seed(
    photos: PhotoStorage, photo_ids: Collection[UUID]
) -> tuple[str, ...]:
    """The reviewers other than this seed that have scored one of these
    photographs, by model name. **Empty while every note is still the seed's.**

    *Nobody looked* is not a state this fixture can keep. ``SEED_REVIEW_OUTAGE``
    is the code ``docs/adr/0132``'s backfill finds unexamined photos by, and the
    backfill is a job in the API process whose first run is at startup — every
    uvicorn reload included — and then hourly. Whichever of those comes first
    after the commit asks the real sidecar, and the note then names that model.
    So the store, and never the card, is what tells *the backfill has been
    round* from *this database predates the photographs*: the card draws the
    same decision either way.

    A note the seed wrote with a declared decision is never in the answer. The
    backfill does not rewrite a note that proves a score, so ``seed-declared``
    stays on those for good.
    """

    models: set[str] = set()
    async with aclosing(photos.with_review_notes()) as listing:
        async for photo in listing:
            if photo.ref.photo_id not in photo_ids:
                continue
            score = recorded_score_in(photo.note)
            if score is not None and score.model != SEED_REVIEW_MODEL:
                models.add(score.model)
    return tuple(sorted(models))


#: What the seed declares its bytes are, checked against the served list at
#: import rather than trusted: the upload rejects a declared type it does not
#: serve without decoding anything, and that refusal would name the media type
#: rather than the fixture.
SEED_IMAGE_MEDIA_TYPE: Final = "image/png"

if SEED_IMAGE_MEDIA_TYPE not in ACCEPTED_MEDIA_TYPES:  # pragma: no cover
    raise RuntimeError(
        f"the seed uploads '{SEED_IMAGE_MEDIA_TYPE}' and the upload path serves "
        f"{sorted(ACCEPTED_MEDIA_TYPES)}."
    )


__all__ = [
    "DeclaredPhotoReview",
    "DeclaredVerdict",
    "SEED_IMAGE_MEDIA_TYPE",
    "SEED_REVIEW_MODEL",
    "an_image",
    "reviewed_since_the_seed",
    "the_store_answers",
    "verdict_for",
]
