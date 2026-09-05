"""What the metadata already on a photo says about whether anybody looked at it.

**The whole of #197 rests on this file being true.** *Which photos need
re-reviewing* is a question about stored notes, and if the answer were a guess
the backfill would be a second reviewer with its own opinion — re-running
inference over a corpus it could not tell apart. The three populations
``docs/adr/0132`` names are three shapes of one string, so they are decided here,
with no store, no model and no network.

The direction of the doubt is the opposite of the sweep's, and that is
deliberate. The sweep refuses to act on a key it cannot parse because its action
is a delete. This reads a note it cannot parse as *nobody looked*, because its
action is a re-read: being wrong costs one inference and leaves a note that
parses.
"""

from __future__ import annotations

import pytest

from app.modules.player_profile.domain.photos import (
    PROMPT_SET_FINGERPRINT,
    REVIEW_METADATA_KEY,
    REVIEW_NOTE_METADATA_KEY,
    PhotoReviewDecision,
    PhotoReviewStanding,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    awaits_review,
    decision_on_record,
    judged_against_a_superseded_set,
    on_court_confidence,
    prompt_set_in,
    recorded_score_in,
    review_metadata,
    review_note_in,
    review_standing,
    unavailability_in,
    verdict_from_similarities,
    verdict_when_unreviewable,
)

MODEL = "openai/clip-vit-base-patch32"

#: A vector that is confidently on-court, and one that is confidently not. The
#: numbers themselves are irrelevant here — what matters is that both produce a
#: note of the *reviewed* shape, whichever way the verdict went.
ON_COURT = [0.9] * 5 + [0.1] * 8
OFF_COURT = [0.1] * 5 + [0.9] * 8


def reviewed_note(similarities: list[float]) -> str:
    note = verdict_from_similarities(model=MODEL, similarities=similarities).note
    assert note is not None
    return note


# ---------------------------------------------------------------------------
# Reading the metadata an object carries
# ---------------------------------------------------------------------------


def test_the_pass_through_era_left_a_decision_and_no_note() -> None:
    # The population #197 exists for. `PassThroughPhotoReview` allowed
    # everything by construction and gave no note, so the object says `allowed`
    # and nothing looked at the image.
    metadata = review_metadata(PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED))

    assert metadata == {REVIEW_METADATA_KEY: "allowed"}
    assert review_note_in(metadata) is None


def test_what_the_upload_path_writes_is_what_this_reads_back() -> None:
    # One encoder and one decoder, beside each other, because a batch that
    # spelled the key itself is a batch that can miss a population.
    verdict = verdict_from_similarities(model=MODEL, similarities=ON_COURT)

    metadata = review_metadata(verdict)

    assert metadata[REVIEW_METADATA_KEY] == verdict.decision.value
    assert metadata[REVIEW_NOTE_METADATA_KEY] == verdict.note
    assert review_note_in(metadata) == verdict.note


def test_a_photo_with_no_metadata_at_all_reads_as_no_note() -> None:
    assert review_note_in({}) is None


# ---------------------------------------------------------------------------
# What may be shown about a photo, and what may only be believed
# ---------------------------------------------------------------------------
#
# `review_standing` answers *has anybody looked*, for a backfill that is going
# to look. `decision_on_record` answers *what was concluded*, for a card that is
# going to draw a shield on twenty strangers' screens — and the two are asked of
# the same string for opposite purposes, which is why the second believes
# nothing the first calls unreviewed (``docs/adr/0138``).


@pytest.mark.parametrize(
    ("similarities", "expected"),
    [(ON_COURT, PhotoReviewDecision.ALLOWED), (OFF_COURT, PhotoReviewDecision.FLAGGED)],
)
def test_a_scored_photo_puts_its_decision_on_record(
    similarities: list[float], expected: PhotoReviewDecision
) -> None:
    metadata = review_metadata(
        verdict_from_similarities(model=MODEL, similarities=similarities)
    )

    assert decision_on_record(metadata) is expected


@pytest.mark.parametrize("why", list(PhotoReviewUnavailability))
def test_an_outage_writes_no_decision_and_reads_back_as_none(
    why: PhotoReviewUnavailability,
) -> None:
    # The whole of #307's second half: what the store holds must not say
    # `allowed` about an image nothing looked at, because a card would draw it.
    metadata = review_metadata(verdict_when_unreviewable(why))

    assert REVIEW_METADATA_KEY not in metadata
    assert decision_on_record(metadata) is None


def test_the_pass_through_eras_allowed_is_not_a_decision_anybody_took() -> None:
    """The population ``docs/adr/0132`` was written for, read the way #307 needs.

    `PassThroughPhotoReview` wrote ``review: allowed`` and no note. The backfill
    fixes those objects on a clock measured in hours; **this** is what makes the
    shield safe on the first commit rather than on the last object of the last
    run.
    """

    metadata = review_metadata(PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED))

    assert metadata[REVIEW_METADATA_KEY] == "allowed"
    assert decision_on_record(metadata) is None


def test_an_allowed_stamped_over_an_outage_is_not_believed_either() -> None:
    # What every photo that arrived during a sidecar outage before #307 carries:
    # the old fail-open decision, beside a note saying nothing looked.
    note = verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT).note
    assert note is not None
    legacy = {REVIEW_METADATA_KEY: "allowed", REVIEW_NOTE_METADATA_KEY: note}

    assert decision_on_record(legacy) is None


def test_a_note_that_proves_a_score_without_a_decision_reports_none() -> None:
    # Half a write, or an object somebody edited. There is a scored note and no
    # verdict beside it, and inventing one from the note would be a second
    # threshold in a second place.
    metadata = {REVIEW_NOTE_METADATA_KEY: reviewed_note(ON_COURT)}

    assert decision_on_record(metadata) is None


def test_a_decision_outside_the_enum_is_not_invented() -> None:
    # A value this application never wrote. Codes cross, so an unknown code is
    # nothing rather than a guess.
    metadata = {
        REVIEW_METADATA_KEY: "rejected",
        REVIEW_NOTE_METADATA_KEY: reviewed_note(ON_COURT),
    }

    assert decision_on_record(metadata) is None


def test_a_photo_with_no_metadata_at_all_has_no_decision_on_record() -> None:
    assert decision_on_record({}) is None


# ---------------------------------------------------------------------------
# The three populations
# ---------------------------------------------------------------------------


def test_no_note_means_the_reviewer_was_never_asked() -> None:
    assert review_standing(None) is PhotoReviewStanding.NEVER_ASKED
    assert awaits_review(None)


@pytest.mark.parametrize("why", list(PhotoReviewUnavailability))
def test_an_unavailable_note_means_the_reviewer_could_not_be_asked(
    why: PhotoReviewUnavailability,
) -> None:
    # Population 2, and the one that keeps growing: every upload that arrived
    # while the sidecar was down or slow lands here.
    note = verdict_when_unreviewable(why).note

    assert review_standing(note) is PhotoReviewStanding.UNAVAILABLE
    assert awaits_review(note)


@pytest.mark.parametrize("similarities", [ON_COURT, OFF_COURT])
def test_a_verdict_taken_from_an_image_is_reviewed_whichever_way_it_went(
    similarities: list[float],
) -> None:
    # A flagged photo was *looked at*. Re-reviewing it would be paying for the
    # same answer, which is the mistake the standing exists to prevent.
    note = reviewed_note(similarities)

    assert review_standing(note) is PhotoReviewStanding.REVIEWED
    assert not awaits_review(note)


def test_a_note_nothing_can_parse_is_read_as_nobody_looked() -> None:
    # The inversion of the sweep's rule, argued in this module's docstring: an
    # unreadable key is left alone there because the action is a delete, and
    # re-reviewed here because the action is a re-read.
    for unreadable in ["", "clip", "clip;m=x", "not-a-note", "clip;c=0.9;s=1,2"]:
        assert review_standing(unreadable) is PhotoReviewStanding.NEVER_ASKED
        assert awaits_review(unreadable)


# ---------------------------------------------------------------------------
# Population 3 — reviewed honestly, against captions nobody asks any more
# ---------------------------------------------------------------------------


def test_both_note_shapes_name_the_prompt_set_they_were_written_under() -> None:
    assert prompt_set_in(reviewed_note(ON_COURT)) == PROMPT_SET_FINGERPRINT
    assert (
        prompt_set_in(verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT).note)
        == PROMPT_SET_FINGERPRINT
    )
    assert prompt_set_in(None) is None


def test_a_verdict_against_a_prompt_set_that_moved_is_reviewed_and_superseded() -> None:
    # The population this job deliberately does not touch: it was looked at, and
    # what it was asked is no longer what is being asked (``docs/adr/0132``).
    stale = reviewed_note(ON_COURT).replace(f"p={PROMPT_SET_FINGERPRINT}", "p=deadbeef")

    assert review_standing(stale) is PhotoReviewStanding.REVIEWED
    assert not awaits_review(stale)
    assert judged_against_a_superseded_set(stale)


def test_a_verdict_against_the_current_prompt_set_is_not_superseded() -> None:
    assert not judged_against_a_superseded_set(reviewed_note(ON_COURT))


def test_a_photo_that_was_never_looked_at_is_never_population_three() -> None:
    # An `unavailable` note carries a fingerprint too, and an old one is still
    # the sidecar being down rather than a judgement worth re-deciding. Counting
    # it as superseded would hide it from the population that is actually work.
    stale = verdict_when_unreviewable(PhotoReviewUnavailability.TRANSPORT).note
    assert stale is not None
    stale = stale.replace(f"p={PROMPT_SET_FINGERPRINT}", "p=deadbeef")

    assert awaits_review(stale)
    assert not judged_against_a_superseded_set(stale)
    assert not judged_against_a_superseded_set(None)


# ---------------------------------------------------------------------------
# Why the reviewer could not be asked
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("why", list(PhotoReviewUnavailability))
def test_the_reason_an_outage_note_carries_is_readable_back(
    why: PhotoReviewUnavailability,
) -> None:
    # The closed set is closed so that it can be queried, and this is the query.
    assert unavailability_in(verdict_when_unreviewable(why).note) is why


def test_a_note_with_no_outage_in_it_names_no_reason() -> None:
    assert unavailability_in(reviewed_note(ON_COURT)) is None
    assert unavailability_in(None) is None


def test_a_reason_outside_the_closed_set_is_not_invented() -> None:
    # A note this application did not write. It still awaits review — nothing
    # in it claims a verdict — but there is no value to report for it.
    note = f"clip;p={PROMPT_SET_FINGERPRINT};unavailable=solar-flare"

    assert review_standing(note) is PhotoReviewStanding.UNAVAILABLE
    assert unavailability_in(note) is None


def test_two_of_the_four_reasons_are_about_the_reviewer_and_two_are_not() -> None:
    # The split a re-review pass turns on: unreachable means the next photo gets
    # the same answer, and a refusal may be about the one image in hand. Every
    # value is named, so a fifth reason cannot be added without deciding which
    # it is.
    about_the_reviewer = {
        why for why in PhotoReviewUnavailability if why.is_about_the_reviewer
    }

    assert about_the_reviewer == {
        PhotoReviewUnavailability.TIMEOUT,
        PhotoReviewUnavailability.TRANSPORT,
    }
    assert not PhotoReviewUnavailability.STATUS.is_about_the_reviewer
    assert not PhotoReviewUnavailability.MALFORMED.is_about_the_reviewer


# ---------------------------------------------------------------------------
# The evidence a reviewed note carries
# ---------------------------------------------------------------------------


def test_the_vector_a_note_was_scored_from_reads_back() -> None:
    """The whole of #316 rests on this: the corpus is already on the objects.

    A threshold is re-derivable without re-running inference only if the numbers
    the last one was applied to can be read back off the metadata. This is that
    read, and it is here beside the writer for the reason the module's foot
    argues: two modules spelling one format is the pair that drifts.
    """

    score = recorded_score_in(reviewed_note(ON_COURT))
    assert score is not None
    assert score.similarities == pytest.approx(tuple(ON_COURT))
    assert score.model == MODEL


def test_the_vector_re_derives_the_confidence_rather_than_trusting_the_note() -> None:
    """Why the vector is read and the recorded ``c=`` is not.

    The fingerprint pins the *captions*, and nothing else: the scale and the
    softmax are today's arithmetic, and a note written before either moved would
    carry a confidence today's rule would not produce. Re-deriving from the raw
    vector is what makes a rate a fact about the line being tried rather than
    about the line that was.
    """

    score = recorded_score_in(reviewed_note(OFF_COURT))
    assert score is not None

    assert on_court_confidence(score.similarities) == pytest.approx(
        on_court_confidence(OFF_COURT)
    )


def test_a_note_nobody_scored_carries_no_vector() -> None:
    # Populations 1 and 2. Neither was applied to an image, so there is nothing
    # to re-derive and `None` is the honest answer rather than an empty vector —
    # which would read as *scored against nothing*.
    assert recorded_score_in(None) is None
    assert (
        recorded_score_in(
            verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT).note
        )
        is None
    )
    assert recorded_score_in("clip;garbage") is None


def test_a_vector_that_will_not_parse_is_no_vector_rather_than_a_guess() -> None:
    # The direction of the doubt here is the *sweep's*, not the backfill's: a
    # number this cannot read must not become a number in a distribution, because
    # nothing downstream would ever find out. Dropping the photo costs one row of
    # a corpus; guessing costs the rate.
    note = reviewed_note(ON_COURT)
    corrupt = note[: note.index(";s=")] + ";s=0.31,,0.29"

    assert review_standing(corrupt) is PhotoReviewStanding.REVIEWED
    assert recorded_score_in(corrupt) is None


def test_a_superseded_note_still_yields_its_vector() -> None:
    """Comparability is the caller's judgement, not this reader's.

    Population 3 was really scored and its numbers really are on the object;
    what is no longer true is that they were measured against today's captions.
    `judged_against_a_superseded_set` is the question that decides whether they
    belong in a corpus, and folding that decision in here would leave a caller
    unable to count what it dropped.
    """

    stale = reviewed_note(ON_COURT).replace(f"p={PROMPT_SET_FINGERPRINT}", "p=deadbeef")

    score = recorded_score_in(stale)
    assert score is not None
    assert score.similarities == pytest.approx(tuple(ON_COURT))
    assert judged_against_a_superseded_set(stale)


def test_a_similarity_that_is_not_a_number_poisons_nothing() -> None:
    """``nan`` and ``inf`` parse, and are the two that would never raise.

    A cosine similarity is a number in ``[-1, 1]``. These two survive `float`,
    reach the softmax and come back out as a confidence that compares false
    against every threshold — so the photograph would count as allowed at all of
    them, in an aggregate nothing downstream can audit.
    """

    note = reviewed_note(ON_COURT)
    for poison in ("nan", "inf", "-inf"):
        corrupt = note[: note.index(";s=")] + f";s=0.31,{poison}" + ",0.2" * 11

        assert review_standing(corrupt) is PhotoReviewStanding.REVIEWED
        assert recorded_score_in(corrupt) is None
