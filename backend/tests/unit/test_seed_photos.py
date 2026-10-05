"""The three answers a card can carry about a photograph, and how a seed reaches
them.

**The claim that matters is the round trip, not the enum.** A shield is drawn
only where the stored note proves an image was really scored — model, prompt set,
confidence and raw vector, all four (`docs/adr/0138`) — so a fixture that named a
decision and wrote a note beside it by hand would be asserting its own spelling
of somebody else's format, and would rot silently the day that format grew a
field. What is checked here is that the platform's own reader believes what the
seed's own writer produced.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.player_profile.infrastructure.pillow_image_transcoder import (
    PillowImageTranscoder,
)
from app.modules.player_profile.domain.photos import (
    ACCEPTED_MEDIA_TYPES,
    STORED_MEDIA_TYPE,
    ON_COURT_CONFIDENCE_THRESHOLD,
    PHOTO_REVIEW_PROMPTS,
    PhotoRef,
    PhotoReviewDecision,
    decision_on_record,
    on_court_confidence,
    review_metadata,
    verdict_from_similarities,
)
from app.seeds.photos import (
    SEED_IMAGE_EDGE_PX,
    SEED_IMAGE_MEDIA_TYPE,
    DeclaredPhotoReview,
    DeclaredVerdict,
    an_image,
    reviewed_since_the_seed,
    the_store_answers,
    verdict_for,
)
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

#: What a card is allowed to draw for each of the three declared states. Two of
#: them are the **same silence** and that is the point of the table: they differ
#: only in the store, so a fixture holding one proves nothing about the other.
DRAWN = {
    DeclaredVerdict.ON_A_COURT: PhotoReviewDecision.ALLOWED,
    DeclaredVerdict.NOT_A_COURT: PhotoReviewDecision.FLAGGED,
    DeclaredVerdict.NOBODY_LOOKED: None,
}


@pytest.mark.parametrize("declared", list(DeclaredVerdict))
def test_a_declared_verdict_survives_the_round_trip_the_card_makes(declared):
    """Written as metadata by the domain, read back by the one function a card
    is allowed to believe."""

    assert decision_on_record(review_metadata(verdict_for(declared))) is DRAWN[
        declared
    ]


def test_the_three_states_are_three_answers():
    """A table that collapsed two states onto one answer would leave the fixture
    unable to tell *flagged* from *never looked at* — which is the only reason it
    holds photographs at all."""

    assert len(set(DeclaredVerdict)) == 3
    assert len({(declared, DRAWN[declared]) for declared in DeclaredVerdict}) == 3


def test_an_unreviewed_photograph_writes_no_decision_key_at_all():
    """*Nobody looked* is an **absence** and not a third word: no decision on the
    verdict, no key on the object, no field on the wire."""

    metadata = review_metadata(verdict_for(DeclaredVerdict.NOBODY_LOOKED))

    assert "review" not in metadata, metadata
    assert metadata, "an unreviewed photo records no evidence of why"


@pytest.mark.parametrize(
    "declared, clear",
    [(DeclaredVerdict.ON_A_COURT, True), (DeclaredVerdict.NOT_A_COURT, False)],
)
def test_a_declared_score_is_clear_of_the_threshold_on_both_sides(declared, clear):
    """**Far from the line on purpose**, so a retune of the threshold moves the
    number rather than flipping this fixture's states — the same argument the
    cohort's two commit windows make about ADR-0113's fourteen days."""

    note = review_metadata(verdict_for(declared))["review-note"]
    scores = [float(one) for one in note.split(";s=")[1].split(",")]

    assert len(scores) == len(PHOTO_REVIEW_PROMPTS)
    confidence = on_court_confidence(scores)
    assert (confidence > ON_COURT_CONFIDENCE_THRESHOLD) is clear, confidence
    assert abs(confidence - ON_COURT_CONFIDENCE_THRESHOLD) > 0.4, confidence


async def test_the_declared_reviewer_answers_what_the_fixture_declared():
    """`PhotoReview` is a port and the seed supplies one, exactly as it supplies
    a clock: what a check concluded about a synthetic image is a thing this
    fixture has to choose rather than discover."""

    class _AnyImage:
        data = b""
        media_type = SEED_IMAGE_MEDIA_TYPE
        width = 1
        height = 1

    for declared in DeclaredVerdict:
        verdict = await DeclaredPhotoReview(declared).review(_AnyImage())
        assert verdict.decision is DRAWN[declared]


def test_the_seeded_bytes_are_a_type_the_upload_path_serves():
    """The upload rejects a declared type it does not serve **before** it touches
    the bytes, so a fixture off that list would be refused for a reason that has
    nothing to do with the fixture."""

    assert SEED_IMAGE_MEDIA_TYPE in ACCEPTED_MEDIA_TYPES
    assert an_image().startswith(b"\x89PNG"), "the seeded bytes are not a PNG"


async def test_the_seeded_bytes_are_what_the_platform_agrees_to_hold():
    """**Written with the standard library and re-encoded by the platform's own
    transcoder**, which is the whole reason a fixture hands the upload path bytes
    rather than an object: ADR-0091 puts the re-encode behind `ImageTranscoder`,
    and a chunk whose CRC this module got wrong would surface as an upload the
    platform rejected rather than as a fixture bug.
    """

    stored = await PillowImageTranscoder().transcode(an_image())

    assert stored.media_type == STORED_MEDIA_TYPE
    assert (stored.width, stored.height) == (SEED_IMAGE_EDGE_PX, SEED_IMAGE_EDGE_PX)


async def test_a_store_that_answers_is_told_apart_from_one_that_cannot():
    """An unreachable store is the **environment** and never the fixture, and the
    run has to be able to say which — a seed that died on a photograph would take
    a whole population with it because a container was not up."""

    class _Unreachable:
        async def exists(self, ref):
            raise OSError("nodename nor servname provided")

    assert await the_store_answers(InMemoryPhotoStorage()) is True
    assert await the_store_answers(_Unreachable()) is False


async def test_a_photograph_the_backfill_has_since_scored_is_told_apart():
    """*Nobody looked* lasts until ``docs/adr/0132``'s backfill looks, and the
    store is what says that it has: the note then names a real reviewer rather
    than this seed. A photograph the seed declared reviewed keeps the seed's
    name, because the backfill never rewrites a note that proves a score."""

    storage = InMemoryPhotoStorage()
    unlooked = PhotoRef(owner_id=uuid4(), photo_id=uuid4())
    declared = PhotoRef(owner_id=uuid4(), photo_id=uuid4())
    storage.already_holding(
        unlooked, review_metadata(verdict_for(DeclaredVerdict.NOBODY_LOOKED))
    )
    storage.already_holding(
        declared, review_metadata(verdict_for(DeclaredVerdict.ON_A_COURT))
    )
    both = {unlooked.photo_id, declared.photo_id}

    assert await reviewed_since_the_seed(storage, both) == ()

    await storage.replace_metadata(
        unlooked,
        review_metadata(
            verdict_from_similarities(
                model="openai/clip-vit-base-patch32",
                similarities=(0.0,) * len(PHOTO_REVIEW_PROMPTS),
            )
        ),
    )

    assert await reviewed_since_the_seed(storage, both) == (
        "openai/clip-vit-base-patch32",
    )
    assert await reviewed_since_the_seed(storage, {declared.photo_id}) == ()
