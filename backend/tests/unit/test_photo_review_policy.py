"""What *shows a racket sport on a court* means, as arithmetic over floats.

**No model, no container, no network.** That is the point of putting the prompt
set, the scale and the threshold in the domain rather than in a service: the
whole of the rule is a pure function, so the interesting cases — the confident
yes, the confident no, the photo that lands on the line — are a list of numbers
here rather than a corpus somebody has to curate before anything can be
asserted.
"""

from __future__ import annotations

import pytest

from app.modules.player_profile.domain.photos import (
    OFF_COURT_PROMPTS,
    ON_COURT_CONFIDENCE_THRESHOLD,
    ON_COURT_PROMPTS,
    PHOTO_REVIEW_PROMPTS,
    PROMPT_SET_FINGERPRINT,
    PhotoReviewDecision,
    PhotoReviewUnavailability,
    on_court_confidence,
    review_note,
    verdict_from_similarities,
    verdict_when_unreviewable,
)

MODEL = "openai/clip-vit-base-patch32"


def similarities(*, on_court: float, off_court: float) -> list[float]:
    """One vector: every on-court prompt at one value, every other at another."""

    return [on_court] * len(ON_COURT_PROMPTS) + [off_court] * len(OFF_COURT_PROMPTS)


# ---------------------------------------------------------------------------
# The prompt set
# ---------------------------------------------------------------------------


def test_the_on_court_prompts_come_first() -> None:
    # The confidence is a slice, not a lookup — so the order is load-bearing and
    # is asserted rather than assumed by the function that relies on it.
    assert PHOTO_REVIEW_PROMPTS[: len(ON_COURT_PROMPTS)] == ON_COURT_PROMPTS
    assert PHOTO_REVIEW_PROMPTS[len(ON_COURT_PROMPTS) :] == OFF_COURT_PROMPTS


def test_every_rated_sport_is_named_in_the_on_court_prompts() -> None:
    """A padel court, a squash court and a badminton court do not look alike.

    One caption reading "a racket sport" would ask about the phrase rather than
    about the scene, and the sport with the most players would be the one it
    described worst.
    """

    asked = " ".join(ON_COURT_PROMPTS).lower()
    for sport in ("padel", "tennis", "squash", "badminton"):
        assert sport in asked


def test_no_prompt_is_asked_twice() -> None:
    # A duplicate caption is a silent thumb on the scale: it would take a share
    # of the probability mass twice on whichever side it sits.
    assert len(set(PHOTO_REVIEW_PROMPTS)) == len(PHOTO_REVIEW_PROMPTS)


def test_the_fingerprint_is_derived_from_the_prompts_as_asked() -> None:
    """Derived rather than declared — a version somebody must remember to bump
    is a version that eventually describes the wrong set."""

    from hashlib import sha256

    expected = sha256("\n".join(PHOTO_REVIEW_PROMPTS).encode("utf-8")).hexdigest()[:8]
    assert PROMPT_SET_FINGERPRINT == expected


# ---------------------------------------------------------------------------
# The confidence
# ---------------------------------------------------------------------------


def test_an_image_that_matches_only_the_on_court_prompts_is_near_certain() -> None:
    assert on_court_confidence(similarities(on_court=0.34, off_court=0.18)) > 0.99


def test_an_image_that_matches_only_the_other_prompts_is_near_zero() -> None:
    assert on_court_confidence(similarities(on_court=0.18, off_court=0.34)) < 0.01


def test_a_similarity_this_high_does_not_overflow() -> None:
    """The scale is 100, so `exp` on an unshifted logit is `exp(100)`.

    Subtracting the maximum first changes no output and is the only reason this
    returns a number at all rather than an infinity or a `ZeroDivisionError`.
    """

    assert 0.0 <= on_court_confidence(similarities(on_court=1.0, off_court=1.0)) <= 1.0


def test_the_confidence_is_a_share_and_never_leaves_the_unit_interval() -> None:
    ragged = [0.31, 0.12, 0.29, 0.05, 0.22, 0.30, 0.19, 0.27, 0.08, 0.24, 0.16]
    spread = [ragged[i % len(ragged)] for i in range(len(PHOTO_REVIEW_PROMPTS))]

    assert 0.0 <= on_court_confidence(spread) <= 1.0


def test_a_vector_of_the_wrong_length_is_refused_rather_than_scored() -> None:
    """A reviewer that answered a different number of questions than it was
    asked has not answered these ones, and a misaligned vector would produce a
    confident verdict about the wrong captions."""

    with pytest.raises(ValueError):
        on_court_confidence([0.3] * (len(PHOTO_REVIEW_PROMPTS) - 1))


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def test_a_court_photo_is_allowed() -> None:
    verdict = verdict_from_similarities(
        model=MODEL, similarities=similarities(on_court=0.34, off_court=0.18)
    )

    assert verdict.decision is PhotoReviewDecision.ALLOWED
    assert not verdict.is_flagged


def test_a_photo_of_something_else_is_flagged() -> None:
    verdict = verdict_from_similarities(
        model=MODEL, similarities=similarities(on_court=0.18, off_court=0.34)
    )

    assert verdict.is_flagged


def test_the_threshold_is_inclusive_on_the_allowed_side() -> None:
    """Exactly at the line is allowed, not flagged.

    Stated so it is a decision rather than whichever comparison got typed: the
    check soft-warns and the tie belongs to the player.
    """

    equal = [0.2] * len(PHOTO_REVIEW_PROMPTS)
    confidence = on_court_confidence(equal)
    assert confidence == pytest.approx(
        len(ON_COURT_PROMPTS) / len(PHOTO_REVIEW_PROMPTS)
    )
    assert (confidence >= ON_COURT_CONFIDENCE_THRESHOLD) == (
        verdict_from_similarities(model=MODEL, similarities=equal).decision
        is PhotoReviewDecision.ALLOWED
    )


# ---------------------------------------------------------------------------
# The note — the evidence, not the reason
# ---------------------------------------------------------------------------


def test_the_note_records_every_raw_similarity() -> None:
    """The threshold above is provisional and the note is why that is safe: a
    better one is re-derivable by reading stored objects, without re-running
    inference on a single image."""

    scores = [round(0.11 + i / 100, 4) for i in range(len(PHOTO_REVIEW_PROMPTS))]

    note = review_note(model=MODEL, similarities=scores)

    recorded = [float(value) for value in note.split(";s=")[1].split(",")]
    assert recorded == scores


def test_the_note_names_the_model_and_the_prompt_set() -> None:
    # A similarity vector means nothing without the captions it was measured
    # against and the model that measured it. Both travel with it.
    note = review_note(
        model=MODEL, similarities=similarities(on_court=0.3, off_court=0.2)
    )

    assert f"m={MODEL}" in note
    assert f"p={PROMPT_SET_FINGERPRINT}" in note


def test_an_allowed_verdict_carries_its_note_too() -> None:
    # Not only the flagged ones: the corpus a threshold is chosen over is every
    # photo, and one made only of the photos that failed the current line would
    # be the wrong corpus.
    verdict = verdict_from_similarities(
        model=MODEL, similarities=similarities(on_court=0.34, off_court=0.18)
    )

    assert verdict.note is not None and verdict.note.startswith("clip;")


def test_the_note_is_ascii_and_fits_beside_the_object() -> None:
    """It travels as an HTTP header on the way into the store."""

    note = review_note(
        model=MODEL, similarities=similarities(on_court=0.31, off_court=0.19)
    )

    assert note.isascii()
    assert "\n" not in note and "\r" not in note
    assert len(note.encode("utf-8")) < 512


# ---------------------------------------------------------------------------
# When the reviewer could not be asked
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("why", list(PhotoReviewUnavailability))
def test_an_unreviewable_photo_is_allowed_and_says_so(
    why: PhotoReviewUnavailability,
) -> None:
    """Fail open — an outage must not refuse a real player's first photo — and
    say which outage, so a re-review pass can find them."""

    verdict = verdict_when_unreviewable(why)

    assert verdict.decision is PhotoReviewDecision.ALLOWED
    assert verdict.note == f"clip;p={PROMPT_SET_FINGERPRINT};unavailable={why.value}"


def test_an_unreviewable_note_is_distinguishable_from_a_reviewed_one() -> None:
    # Which is the whole of what makes the backfill possible: `review: allowed`
    # alone cannot tell a photo that passed from one nobody looked at.
    reviewed = review_note(
        model=MODEL, similarities=similarities(on_court=0.34, off_court=0.18)
    )
    unreviewed = verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT).note

    assert "unavailable=" not in reviewed
    assert unreviewed is not None and "unavailable=" in unreviewed
