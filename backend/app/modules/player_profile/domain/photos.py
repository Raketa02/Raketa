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
from math import exp, isfinite
from typing import Final, Mapping, Sequence
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

    There is also no value for *the reviewer could not be asked*, and there is
    now a third state rather than two. This enum says what the reviewer
    **concluded** about an image; *nobody looked* is not a conclusion about an
    image, so it is spelled as the **absence** of one of these — ``None`` on a
    verdict, no key on the object, no field on the wire (``docs/adr/0138``).
    ADR-0133 already spelled the uploader's third state that way rather than
    folding it into ``allowed`` at the boundary that knows least; the stored
    verdict is the boundary that was folded, and this is where it is unfolded.
    See `verdict_when_unreviewable` and `decision_on_record`.
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

    #: What the reviewer concluded, or ``None`` for **nobody looked**. Three
    #: answers rather than two, and only the first two were ever a conclusion:
    #: an unreachable reviewer used to record ``ALLOWED``, which was the right
    #: trade while the verdict was a warning nobody else saw and the wrong one
    #: the day it became a badge on a stranger's card (``docs/adr/0138``).
    decision: PhotoReviewDecision | None
    note: str | None = None

    @property
    def is_flagged(self) -> bool:
        """Whether this photo should be warned about. **A verdict with no
        decision is not one** — silence is what an outage costs, on both sides
        of it."""

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
class NotedPhoto:
    """A photo the store is holding, and what it says about its review.

    The other thing a listing yields, and the mirror image of `StoredPhoto`:
    that one carries the stamp and deliberately no metadata, this one carries
    the metadata and deliberately no stamp. Two shapes rather than one wide one,
    because the sweep may not be able to read a verdict — a sweep that could
    would invite a rule about flagged photos — and the backfill has no business
    with an age.

    ``note`` is absent for every photo stored before the checker existed, and
    that absence is the signal rather than a gap: see `review_standing`.
    """

    ref: PhotoRef
    note: str | None


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

    @property
    def is_about_the_reviewer(self) -> bool:
        """Whether this says *the reviewer is down* or *it failed this request*.

        **Two of these four describe the container and two describe one call to
        it**, and a batch re-reviewing a corpus has to tell them apart. A timeout
        and a transport error mean the sidecar is not answering, so the next
        photo will get the same answer and there is nothing to do but come back
        later. A status or a malformed body mean it *answered* — perhaps about
        this one image, which may be the only image it cannot handle. Treating
        those as *the reviewer is down* would let one photo end every run at the
        same place for ever, and nothing after it in the listing would be looked
        at again.

        Nothing on the upload path reads this: a single upload fails open
        whichever it was, and the note records which. It is the re-review pass
        that has a next photo to decide about.
        """

        return self in {
            PhotoReviewUnavailability.TIMEOUT,
            PhotoReviewUnavailability.TRANSPORT,
        }


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
#: honest placeholder — *the on-court captions won*.
#:
#: **It no longer costs nothing, and this comment used to say it did.** ADR-0129
#: wrote *"nothing reads the decision: no route returns it and no copy shows
#: it"*, which stopped being true twice: ``docs/adr/0133`` made this line a
#: sentence shown to the photograph's owner, and ``docs/adr/0138`` made it a
#: shield shown to twenty people who are not. A genuine on-court photo scoring
#: 0.49 now leaves its owner silently unbadged on other people's screens, with no
#: copy to soften it. That is the sharpest cost this number has, and it is
#: **#316** — the one place a reader meets the value should not also be the one
#: place claiming it is inconsequential.
#:
#: What makes the placeholder safe to replace at all is that every verdict records
#: the similarities it was computed from, so the threshold is re-derivable over
#: the stored corpus without re-running inference on a single image. That is now
#: a command rather than a promise — ``make photo-flag-rate`` prints the flag rate
#: each candidate line would have produced, over the photographs the platform
#: already holds. **What it cannot do is choose**: where the rate should sit, and
#: whether the corpus is yet large enough for one to mean anything, are product
#: judgements, which is why #316 is `ready-for-human` and why the number a run
#: argues for is typed here by hand.
#:
#: **Moving it changes what stored verdicts mean without changing them.** A photo
#: stamped under this value keeps that stamp until something re-reviews it, and
#: the fingerprint does not move, so ``docs/adr/0132``'s backfill will not pick it
#: up either. Whether to re-stamp the corpus under a new line is a second decision
#: — *a new record, not a configuration change* — and the run prints its size.
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


def flagged_at(*, confidence: float, threshold: float) -> bool:
    """Whether a photo scoring `confidence` is warned about at `threshold`.

    **One comparison, spelled once, for both the threshold in force and any
    threshold somebody is thinking about.** ADR-0132 makes the argument in its
    own setting — a batch with its own copy of the rule is a second reviewer,
    able to disagree with the upload path about one image — and it is sharper
    here, because the caller with the other copy would be the derivation that
    chooses the next value (#316). A rate computed with `<=` where the verdict
    uses `<` differs by exactly the photos sitting on the line, reads as
    measured, and nothing downstream could tell.

    **Exactly on the line is allowed**, at a candidate threshold as much as at
    the shipping one: the check soft-warns and the tie belongs to the player.

    **Spelled ``not (>=)`` rather than ``<``, and the difference is one value.**
    A ``nan`` confidence compares false against both, so ``<`` would call it
    *allowed* — which under ``docs/adr/0138`` is a shield shown to strangers
    about a photograph whose score is nonsense — while this calls it flagged.
    It is reachable: a cosine similarity of ``nan`` passes the sidecar adapter's
    number check and ``json`` decodes a bare ``NaN`` by default, so the
    arithmetic below yields one. The tie belongs to the player; a number that is
    not a number is not a tie, and the soft warning is the cheap side to be
    wrong on. (The derivation never meets one — `recorded_score_in`
    refuses a non-finite vector before it can enter a distribution.)

    Both arguments are keyword-only, because they are two floats in the same
    unit interval and a swapped pair would be silent at every call site.

    Monotone in `threshold` over the finite values, which is not a detail: it is
    what lets a table of rates be read as one distribution rather than as
    unrelated numbers.
    """

    return not confidence >= threshold


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
        PhotoReviewDecision.FLAGGED
        if flagged_at(
            confidence=confidence, threshold=ON_COURT_CONFIDENCE_THRESHOLD
        )
        else PhotoReviewDecision.ALLOWED
    )
    return PhotoReviewVerdict(
        decision=decision,
        note=review_note(model=model, similarities=similarities),
    )


def verdict_when_unreviewable(why: PhotoReviewUnavailability) -> PhotoReviewVerdict:
    """The verdict for a photo the reviewer could not be asked about.

    **No decision, and the note says which outage produced none.** Fail-open is
    unchanged and is now spelled honestly: the check soft-warns rather than
    hard-blocks (``docs/adr/0091``), so a reviewer that turned its own outage
    into a failed upload would refuse a real player's photo for a reason that has
    nothing to do with the photo — worse than the false reject the soft-warn rule
    already refuses to pay. What has changed is the other side of it. Until
    ``docs/adr/0138`` this returned ``ALLOWED``, which said *nothing to warn
    about* in the only vocabulary it had; a card reading the same word would say
    *this photograph was checked and passed*, about an image nothing looked at,
    to twenty people who are not its owner.

    So an outage costs **silence in both directions** — no warning to the
    uploader, no shield to a stranger — and there is still no third value on
    ``PhotoReviewDecision``. That enum says what the reviewer *concluded*, and
    *the reviewer was unreachable* is not a conclusion about an image: it is an
    absence of one, beside evidence a re-review pass can find by prefix.
    """

    return PhotoReviewVerdict(
        decision=None,
        note=f"clip;p={PROMPT_SET_FINGERPRINT};unavailable={why.value}",
    )


# ---------------------------------------------------------------------------
# What the store already says about a photo, and who still owes a look
# ---------------------------------------------------------------------------
#
# Everything above decides what a *new* photo's verdict is. What follows reads
# the verdict already sitting beside an object, because the platform holds
# photos from three different eras and they are not the same job
# (``docs/adr/0132``): the ones the pass-through waved through with no note, the
# ones that arrived while the sidecar was unreachable, and the ones that were
# really looked at.
#
# **The encoder and the decoder are here together, deliberately.** The upload
# path writes this metadata and the backfill reads it; two modules spelling the
# same key is the pair that drifts, and a backfill that misspelled it would
# silently find no population at all.


#: The metadata key the review decision is stored under, beside the bytes.
REVIEW_METADATA_KEY: Final = "review"

#: The metadata key the reviewer's machine-readable note is stored under, when
#: it gave one. **Absent rather than empty when it did not**, which is the whole
#: of how a pass-through-era photo is told apart from a reviewed one.
REVIEW_NOTE_METADATA_KEY: Final = "review-note"

#: What separates one field of a note from the next, and a field's name from its
#: value. Named because the note is written here and parsed here, and a
#: separator written twice is one that eventually disagrees with itself.
_NOTE_FIELD_SEPARATOR: Final = ";"
_NOTE_VALUE_SEPARATOR: Final = "="

#: The field a note carries the prompt-set fingerprint in. Every note shape has
#: it — a verdict names what it was judged against, and an outage names what it
#: would have been judged against.
_PROMPT_SET_FIELD: Final = "p"

#: The field that says the reviewer was never asked, and why.
_UNAVAILABLE_FIELD: Final = "unavailable"

#: The field naming the reviewer that produced the vector. Two corpora scored by
#: different models are two corpora, and a note that could not say which is a
#: vector nobody can place.
_MODEL_FIELD: Final = "m"

#: The field the raw similarity vector rides in — one value per prompt, in the
#: order they were asked. **The only field on a note that is evidence rather
#: than a conclusion**, and the reason a threshold can be re-derived over the
#: stored corpus without paying for inference twice (#316).
_SIMILARITIES_FIELD: Final = "s"

#: What separates one similarity from the next inside that field.
_NOTE_LIST_SEPARATOR: Final = ","

#: What a note must carry to count as *this image was actually scored*: the
#: model, the prompt set, the confidence and the raw vector. All four, because
#: any three of them is a note this application never wrote.
_REVIEWED_FIELDS: Final = frozenset(
    {_MODEL_FIELD, _PROMPT_SET_FIELD, "c", _SIMILARITIES_FIELD}
)


class PhotoReviewStanding(StrEnum):
    """Whether anybody has actually looked at this photo yet.

    Read off the note the store holds, and **not** the same question as
    `PhotoReviewDecision`: a photo can be ``allowed`` because a model scored it
    and a photo can be ``allowed`` because nothing was asked, and until #181
    landed nothing distinguished the two.

    Three values because there are three populations, and only the first two are
    work (``docs/adr/0132``).
    """

    #: No note, or a note nothing can read. The pass-through era, and the
    #: population that is fixed and only shrinks.
    NEVER_ASKED = "never-asked"

    #: The reviewer was asked and could not answer — down, slow, or wrong. This
    #: population keeps growing, which is why the fix is a loop and not a script.
    UNAVAILABLE = "unavailable"

    #: Scored against a real image. The prompt set it was scored under is in the
    #: note; whether that set is still the one being asked is a separate
    #: question, and `judged_against_a_superseded_set` is the one that asks it.
    REVIEWED = "reviewed"


def review_metadata(verdict: PhotoReviewVerdict) -> dict[str, str]:
    """The metadata one verdict is stored under, beside the bytes.

    A flagged photo is **stored**, not refused — the check soft-warns rather
    than hard-blocks (``docs/adr/0091``) — and the verdict rides on the object
    so that what the reviewer concluded is findable later without a second table
    to keep in step with the blobs.

    The note key is **omitted** rather than written empty when there is none.
    That is not tidiness: it is the signal, and `review_standing` reads it.

    **The decision key is omitted the same way, and for a sharper reason.** A
    photo nobody could look at gets no verdict written beside it at all
    (``docs/adr/0138``), so ``review: allowed`` stops being a word this
    application writes about an unexamined image. Every object still carrying
    one is from before that record — the pass-through era, or an outage under
    ADR-0133 — and `decision_on_record` is what refuses to believe them until
    ADR-0132's job has been round.
    """

    metadata: dict[str, str] = {}
    if verdict.decision is not None:
        metadata[REVIEW_METADATA_KEY] = verdict.decision.value
    if verdict.note is not None:
        metadata[REVIEW_NOTE_METADATA_KEY] = verdict.note
    return metadata


def review_note_in(metadata: Mapping[str, str]) -> str | None:
    """The reviewer's note out of one object's metadata, or ``None``.

    ``None`` for *this object carries no note*, which is what every photo stored
    before the checker existed looks like.
    """

    return metadata.get(REVIEW_NOTE_METADATA_KEY)


def decision_on_record(metadata: Mapping[str, str]) -> PhotoReviewDecision | None:
    """What was concluded about this photo, **believing nothing the note cannot
    prove**. ``None`` for *nobody looked*.

    The mirror of `review_metadata`, and the one thing on the read side that is
    allowed to cross to somebody who is not the photograph's owner
    (``docs/adr/0138``). ``review_note_in`` beside it answers *what does the
    store say*; this answers *what may be drawn*, and the difference between the
    two questions is the whole of this function.

    **A stored decision counts only where the note proves an image was really
    scored** — model, prompt set, confidence and raw vector, all four
    (`review_standing`). Two populations say ``allowed`` and mean nothing of the
    kind: the pass-through era, which allowed everything by construction, and
    every upload that arrived while the sidecar was unreachable before
    ADR-0138. ADR-0132's job drains both, on a clock measured in hours over a
    listing that is one ``HEAD`` per object — and *a tick on a photo nobody
    checked* is not a thing to be wrong about for as long as that takes. So the
    proof is required at the point of reading rather than assumed to have been
    written, and the backfill makes the metadata honest at its own pace instead
    of being the thing a shield waits on.

    **An unrecognised code is nothing, not a guess.** The backend publishes
    codes (``docs/adr/0022``) and a value outside the enum is one this
    application never wrote; naming it would be inventing the third decision
    `PhotoReviewDecision` deliberately does not have.

    **A score under a prompt set that has since moved still counts**, and that is
    a decision rather than an oversight. `judged_against_a_superseded_set` is
    population 3, which ``docs/adr/0132`` **counts and deliberately leaves
    alone** — whether captions moved far enough to be worth re-running is a
    judgement nobody has made. Refusing those photos here would take that
    judgement by the back door and would silently unbadge everybody scored before
    the last comma changed in a caption; showing them says only *somebody looked
    at this image*, which is what a shield claims. The day population 3 is
    re-run, or judged not worth re-running, is the day to re-open this line — and
    the count is already in the backfill's log.
    """

    if review_standing(review_note_in(metadata)) is not PhotoReviewStanding.REVIEWED:
        return None
    recorded = metadata.get(REVIEW_METADATA_KEY)
    if recorded is None:
        return None
    try:
        return PhotoReviewDecision(recorded)
    except ValueError:
        return None


def _note_fields(note: str) -> dict[str, str]:
    """One note's ``name=value`` fields. Anything else in it is ignored.

    Lenient on purpose, and the leniency is bounded by what the callers do with
    it: a note is only ever read as *reviewed* when all four of the fields that
    prove a score are present, so a truncated or corrupted string falls short of
    that and is re-reviewed rather than trusted.
    """

    fields: dict[str, str] = {}
    for part in note.split(_NOTE_FIELD_SEPARATOR):
        name, separator, value = part.partition(_NOTE_VALUE_SEPARATOR)
        if separator:
            fields[name] = value
    return fields


def review_standing(note: str | None) -> PhotoReviewStanding:
    """Which of the three populations the photo carrying `note` is in.

    **A note this cannot read is ``NEVER_ASKED``, not an error**, and that is
    the opposite of how the sweep treats a key it cannot parse. The sweep
    refuses to guess because its action is a delete and a wrong answer destroys
    something a player cannot get back; here the action is a re-review, so a
    wrong answer costs one inference and leaves behind a note that does parse.
    """

    if note is None:
        return PhotoReviewStanding.NEVER_ASKED
    fields = _note_fields(note)
    if _UNAVAILABLE_FIELD in fields:
        return PhotoReviewStanding.UNAVAILABLE
    if _REVIEWED_FIELDS <= fields.keys():
        return PhotoReviewStanding.REVIEWED
    return PhotoReviewStanding.NEVER_ASKED


def awaits_review(note: str | None) -> bool:
    """Whether this photo still owes a look. Populations 1 and 2 together.

    The two are one question at the point of doing the work — *has anything
    scored this image* — and two different facts about how the platform got
    there, which is why the standing keeps them apart and this does not.
    """

    return review_standing(note) is not PhotoReviewStanding.REVIEWED


def unavailability_in(note: str | None) -> PhotoReviewUnavailability | None:
    """Why the reviewer could not be asked, if this note says it could not.

    **The closed set earns its keep here** (`PhotoReviewUnavailability`): a
    backfill that stops because the sidecar is unreachable and one that stops
    because the sidecar is rejecting its requests want two different people
    looking, and the difference is one field of a string nobody had to keep a
    table of.

    ``None`` for every other note, and for a reason outside the set — which is a
    note this application did not write, and naming it would be inventing a
    value the enum deliberately does not have.
    """

    if note is None:
        return None
    reason = _note_fields(note).get(_UNAVAILABLE_FIELD)
    if reason is None:
        return None
    try:
        return PhotoReviewUnavailability(reason)
    except ValueError:
        return None


def prompt_set_in(note: str | None) -> str | None:
    """Which prompt set this note was written under, or ``None`` if it says no.

    The fingerprint is what makes a stored corpus re-readable at all: a
    similarity vector means nothing without the captions it was measured
    against (`PROMPT_SET_FINGERPRINT`).
    """

    if note is None:
        return None
    return _note_fields(note).get(_PROMPT_SET_FIELD)


@dataclass(frozen=True, slots=True)
class RecordedScore:
    """What a note says about an image that was really looked at.

    The two facts travel together because a similarity vector is only readable
    beside the things that say what produced it: `prompt_set_in` names the
    captions, and this names the reviewer. **A corpus scored by one model and a
    corpus scored by another are two corpora**, and a rate derived across both
    without noticing is the failure mode a threshold derivation has (#316) — the
    sharpest instance being a workbench's declared fixtures, which carry a
    perfectly well-formed note and are not evidence about anything.
    """

    model: str
    similarities: tuple[float, ...]


def recorded_score_in(note: str | None) -> RecordedScore | None:
    """What this photo was scored as, and by what. ``None`` if it was not.

    **The read #316 is built on.** Every verdict records the numbers it was
    computed from (`review_note`), so choosing a better threshold is a walk over
    stored metadata and arithmetic — not a second pass of inference over every
    photograph the platform holds. This is the decoder for that, and it lives
    beside the encoder for the reason the section above gives: two modules
    spelling one format is the pair that drifts silently.

    **The vector rather than the recorded ``c=``, deliberately.** The
    fingerprint pins the *captions* and nothing else — the scale and the softmax
    are today's arithmetic — so a stored confidence is what some version of this
    module concluded, while the vector is what the model actually said. A rate
    has to be a fact about the line being tried, which means re-deriving through
    `on_court_confidence` rather than believing a number that may predate it.

    ``None`` for populations 1 and 2: neither was applied to an image, so there
    is nothing to re-derive, and an empty vector would read as *scored against
    nothing*. ``None`` too for a field that will not parse — **the sweep's
    direction of doubt rather than the backfill's**, because the action here is
    to put a number into a distribution nothing downstream can audit. Dropping
    one photo costs a row of the corpus; guessing costs the rate.

    **``nan`` and ``inf`` parse, and are refused with the rest.** A cosine
    similarity is a number in ``[-1, 1]``; the two that are not are the two that
    survive `float` and then poison every aggregate computed from them without
    raising anywhere — a ``nan`` confidence compares false against every
    threshold, so the photo would silently count as allowed at all of them.

    A note judged against a prompt set that has since moved **does** yield its
    vector. Whether those numbers belong in a corpus is
    `judged_against_a_superseded_set`'s question, and a caller that could not
    read them could not count what it dropped either.
    """

    if note is None or review_standing(note) is not PhotoReviewStanding.REVIEWED:
        return None
    fields = _note_fields(note)
    # Both are guaranteed present by `review_standing` — they are two of the
    # four fields that make a note *reviewed* — and are read as if they were
    # not, because the guarantee lives in a frozenset one edit away.
    model = fields.get(_MODEL_FIELD)
    recorded = fields.get(_SIMILARITIES_FIELD)
    if model is None or recorded is None:
        return None
    try:
        vector = tuple(
            float(value) for value in recorded.split(_NOTE_LIST_SEPARATOR)
        )
    except ValueError:
        return None
    if not all(isfinite(value) for value in vector):
        return None
    return RecordedScore(model=model, similarities=vector)


def judged_against_a_superseded_set(note: str | None) -> bool:
    """Whether this photo was really scored, against captions that have moved.

    **Population 3, and it is a question rather than a job** (``docs/adr/0132``).
    Re-running it is a judgement about how far the set moved, which nothing here
    can make; what this buys is that the judgement is *answerable* — the size of
    the population is a count rather than a guess.

    False for anything that awaits review. An outage's note carries a
    fingerprint too, and an old one is still the sidecar having been down rather
    than a verdict worth re-deciding — counting it here would hide it from the
    population that is actually work.
    """

    if review_standing(note) is not PhotoReviewStanding.REVIEWED:
        return False
    return prompt_set_in(note) != PROMPT_SET_FINGERPRINT
