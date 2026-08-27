"""What a photo is on its way in, and what the platform agrees to hold.

A player attaches up to three photos to their Player profile, or none
(``../../../../CONTEXT.md`` — *Profile photo*). This module is the policy that
governs the bytes: which formats a client may hand over, what is stored, how
large either may be, how a stored photo is named, and — at the foot of the file
— what *shows a racket sport on a court* means when a machine is asked it.

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
from hashlib import sha256
from math import exp
from typing import Final, Sequence
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

    Two values, and there is deliberately no ``REJECTED``. The on-court check
    **soft-warns rather than hard-blocks** (``docs/adr/0091``): a false reject
    stops a real player on their first day, and that cost does not fall now that
    the other side of the trade has got heavier. Adding a blocking value later is
    an addition; shipping one now would be a behaviour nothing has earned.

    There is also no value for *the reviewer could not be asked*. This enum says
    what the reviewer **concluded** about an image, and an outage is not a
    conclusion about an image — see `verdict_when_unreviewable`.
    """

    ALLOWED = "allowed"
    FLAGGED = "flagged"


@dataclass(frozen=True, slots=True)
class PhotoReviewVerdict:
    """The review port's answer, recorded alongside the stored bytes.

    ``note`` is machine-readable and is never copy shown to a player — the
    backend emits codes and never display text (``docs/adr/0022``). It carries
    the reviewer's **evidence**, not only its reason: the numbers the decision
    was taken from, so that a better threshold can be chosen later by reading
    what was stored rather than by paying for inference twice. See
    `review_note`.
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


# ---------------------------------------------------------------------------
# The on-court check
# ---------------------------------------------------------------------------
#
# The product rule is that a profile photo shows a racket sport on a court. What
# follows is that rule expressed as something a machine can be asked: a closed
# set of phrased captions, the arithmetic that turns one image's similarity to
# each of them into a single confidence, and the line below which the photo is
# flagged.
#
# **All of it is here rather than in `app/core/config.py`, and that is the same
# rule the two caps above are here for.** A threshold the environment could
# select would be a photo flagged on a laptop and allowed in production — the
# definition of behaviour selected by environment. What *is* configuration is
# where the checker is reachable and how long it may take to answer; those two
# are in the settings, and neither can change a verdict.


class PhotoReviewUnavailability(StrEnum):
    """Why a review did not happen. A closed set, because it is queried.

    A photo whose review never ran is recorded as ``ALLOWED`` with one of these
    in its note — see `verdict_when_unreviewable`. The set is closed so that
    *which photos need re-reviewing, and why* is a prefix scan over stored
    metadata rather than a guess at what string an adapter wrote that day.
    """

    TIMEOUT = "timeout"
    TRANSPORT = "transport"
    STATUS = "status"
    MALFORMED = "malformed"


#: The captions that mean *this is the photo the rule asks for*. One per sport
#: the platform rates, because a padel court, a squash court and a badminton
#: court do not look alike and a single "racket sport" caption asks about the
#: word rather than about the scene — plus one that names the racket without a
#: sport, for the photos taken close enough that the court is out of frame.
ON_COURT_PROMPTS: Final = (
    "a photo of a person playing padel on a padel court",
    "a photo of a person playing tennis on a tennis court",
    "a photo of a person playing squash on a squash court",
    "a photo of a person playing badminton on a badminton court",
    "a photo of a person holding a racket on a court",
)

#: The captions that mean *this is some other photo*.
#:
#: **Zero-shot CLIP scores an image against the captions it is given and nothing
#: else**, so these are not decoration: without them every image would be some
#: percentage of *on a court* with nothing to be a percentage of. They are the
#: photos people actually put on a profile instead — a selfie, a night out, a
#: holiday, a pet — rather than an attempt to enumerate what a photo can be.
#:
#: This set is deliberately not a content-moderation list. The rule being
#: checked is *does this show a racket sport on a court*; whether a photo is
#: otherwise unacceptable is a different question with a different answer, and
#: asking one model both would make each answer harder to read.
OFF_COURT_PROMPTS: Final = (
    "a selfie of a person indoors",
    "a photo of a group of people at a party",
    "a photo of a landscape with no people in it",
    "a photo of a pet animal",
    "a photo of a car",
    "a screenshot of text on a screen",
    "a photo of food on a plate",
    "a photo of a person lifting weights in a gym",
)

#: What the reviewer is asked, in the order the answer comes back in. The
#: on-court captions come first, which is what lets the confidence below be a
#: slice rather than a lookup.
PHOTO_REVIEW_PROMPTS: Final = ON_COURT_PROMPTS + OFF_COURT_PROMPTS

#: CLIP's own trained temperature, applied to cosine similarities before they
#: are turned into probabilities. Raw cosine similarities from CLIP sit in a
#: narrow band around 0.2–0.35 whatever the image is, so a threshold on one of
#: them would be reading noise; the scale is what spreads that band into
#: something a line can be drawn through. It is the model's number rather than a
#: tuned one, and the tuned number is the threshold below it.
PHOTO_REVIEW_LOGIT_SCALE: Final = 100.0

#: Below this share of the probability mass on the on-court captions, a photo is
#: flagged.
#:
#: **Provisional, and it is written down as provisional.** The value that belongs
#: here is the one that puts the flag rate where the product wants it, and that
#: is a fact about a corpus of real photos which does not exist yet. Half is the
#: honest placeholder — *the on-court captions won* — and it costs nothing today
#: because nothing reads the decision: no route returns it and no copy shows it.
#: What makes the placeholder safe to replace later is that every verdict records
#: the similarities it was computed from, so the threshold is re-derivable over
#: the stored corpus without re-running inference on a single image.
ON_COURT_CONFIDENCE_THRESHOLD: Final = 0.5


def _prompt_set_fingerprint() -> str:
    """A short digest of the prompts, exactly as they are asked.

    **Derived rather than declared, because a declared version number is a thing
    somebody forgets to bump.** It goes into every note, and it is what makes a
    stored corpus re-readable: a similarity vector means nothing without the
    captions it was measured against, and this says which set those were. Change
    a comma in a prompt and yesterday's notes stop claiming to be comparable
    with today's, which is the correct answer rather than an inconvenience.
    """

    joined = "\n".join(PHOTO_REVIEW_PROMPTS).encode("utf-8")
    return sha256(joined).hexdigest()[:8]


#: See above. Computed at import, so it cannot disagree with the set beside it.
PROMPT_SET_FINGERPRINT: Final = _prompt_set_fingerprint()


def on_court_confidence(similarities: Sequence[float]) -> float:
    """The share of the probability mass sitting on the on-court captions.

    Pure, so the whole of the rule is testable with a list of floats and no
    model, no container and no network — which matters here more than anywhere
    else on the photo path, because the alternative is a rule only an
    integration test can see.

    Softmax over the scaled similarities, summed across the on-court block. The
    maximum is subtracted first, which changes no output and is what keeps
    ``exp`` from overflowing on a scale of 100.
    """

    if len(similarities) != len(PHOTO_REVIEW_PROMPTS):
        raise ValueError(
            f"expected {len(PHOTO_REVIEW_PROMPTS)} similarities, "
            f"one per prompt, got {len(similarities)}"
        )

    logits = [PHOTO_REVIEW_LOGIT_SCALE * s for s in similarities]
    ceiling = max(logits)
    weights = [exp(logit - ceiling) for logit in logits]
    total = sum(weights)
    return sum(weights[: len(ON_COURT_PROMPTS)]) / total


def review_note(*, model: str, similarities: Sequence[float]) -> str:
    """The evidence, compact enough to ride on the object as metadata.

    **The raw similarities are recorded, not only the decision**, and that is the
    point of this function rather than a detail of it. The threshold above is a
    placeholder waiting on a corpus; storing what it was applied to is what lets
    a better one be chosen later by reading stored objects, instead of paying for
    inference over every photo the platform holds a second time.

    Machine-readable and never shown to anybody: the backend emits codes, never
    display text (``docs/adr/0022``). Four decimal places on ten prompts is
    around 150 bytes, comfortably inside what an S3-compatible store will keep
    beside an object, and every character is ASCII because user metadata travels
    as an HTTP header.
    """

    scores = ",".join(f"{s:.4f}" for s in similarities)
    return (
        f"clip;m={model};p={PROMPT_SET_FINGERPRINT}"
        f";c={on_court_confidence(similarities):.4f};s={scores}"
    )


def verdict_from_similarities(
    *, model: str, similarities: Sequence[float]
) -> PhotoReviewVerdict:
    """What the reviewer concluded, and the numbers it concluded it from.

    Raises ``ValueError`` if the answer is not one similarity per prompt. A
    reviewer that answered a different number of questions than it was asked has
    not answered these ones, and scoring a misaligned vector would produce a
    confident verdict about the wrong captions.
    """

    confidence = on_court_confidence(similarities)
    decision = (
        PhotoReviewDecision.ALLOWED
        if confidence >= ON_COURT_CONFIDENCE_THRESHOLD
        else PhotoReviewDecision.FLAGGED
    )
    return PhotoReviewVerdict(
        decision=decision,
        note=review_note(model=model, similarities=similarities),
    )


def verdict_when_unreviewable(why: PhotoReviewUnavailability) -> PhotoReviewVerdict:
    """The verdict for a photo the reviewer could not be asked about.

    **``ALLOWED``, and the note is what says it was never really looked at.** The
    check soft-warns rather than hard-blocks (``docs/adr/0091``); a reviewer that
    turned its own outage into a failed upload would refuse a real player's photo
    for a reason that has nothing to do with the photo, which is worse than the
    false reject the soft-warn rule already refuses to pay.

    There is deliberately no third decision for it. ``PhotoReviewDecision`` says
    what the reviewer *concluded*, and *the reviewer was unreachable* is not a
    conclusion about an image — it belongs in the evidence, where a re-review
    pass can find every one of them by prefix.
    """

    return PhotoReviewVerdict(
        decision=PhotoReviewDecision.ALLOWED,
        note=f"clip;p={PROMPT_SET_FINGERPRINT};unavailable={why.value}",
    )
