"""The backfill: a photo nobody looked at gets looked at, once.

**Three properties carry this file**, and each of them is a way the job could be
wrong that no amount of it running would reveal:

1. *It does not rewrite what it already fixed.* An S3 metadata update is a copy
   of the object onto itself, so a re-runnable job that re-stamps a reviewed
   photo pays for the whole corpus every tick, for ever.
2. *It is not a second reviewer.* The verdict comes back through the same
   `PhotoReview` port the upload path holds, and this stores what it is handed.
   A batch that thresholded for itself could disagree with the upload path about
   one image, and nothing downstream would be able to tell which was right.
3. *It leaves a photo alone when the reviewer cannot be asked.* Stamping a fresh
   `unavailable` over an old one is work that looks like progress and is not.

The transcoder is **real**, as it is on the upload path and for the same reason:
faking it would fake away the decode that says the stored bytes are still an
image at all.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

import pytest

import app.modules.player_profile.application.review_unreviewed_photos as backfill
from app.modules.player_profile.application.review_unreviewed_photos import (
    ReviewUnreviewedPhotos,
)
from app.modules.player_profile.domain.photos import (
    PROMPT_SET_FINGERPRINT,
    REVIEW_METADATA_KEY,
    REVIEW_NOTE_METADATA_KEY,
    PhotoRef,
    PhotoReviewDecision,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    TranscodedImage,
    review_metadata,
    verdict_from_similarities,
    verdict_when_unreviewable,
)
from app.modules.player_profile.infrastructure.passthrough_photo_review import (
    PassThroughPhotoReview,
)
from app.modules.player_profile.infrastructure.pillow_image_transcoder import (
    PillowImageTranscoder,
)
from app.shared.ids import new_uuid
from tests.unit import image_fixtures as fixtures
from tests.unit.fake_photo_storage import InMemoryPhotoStorage, StoredObject

ALICE = UUID("11111111-1111-1111-1111-111111111111")

MODEL = "openai/clip-vit-base-patch32"

#: Confidently on-court, and confidently not. Both are *reviewed* answers — the
#: distinction this job cares about is whether anybody looked, not what they saw.
ON_COURT = [0.9] * 5 + [0.1] * 8
OFF_COURT = [0.1] * 5 + [0.9] * 8


class ScoringReviewer:
    """The real rule, over similarities a test chose.

    **Not a stub verdict.** The point of property 2 above is that the batch does
    not decide anything, and a fake that returned a ready-made
    `PhotoReviewVerdict` would let a use case that re-thresholded pass. This
    stands exactly where `ClipSidecarPhotoReview` stands — it holds the numbers
    the sidecar would have answered and calls `verdict_from_similarities`, which
    is the one function the upload path uses.
    """

    def __init__(self, similarities: Sequence[float] = ON_COURT) -> None:
        self.similarities = list(similarities)
        self.images: list[TranscodedImage] = []

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        self.images.append(image)
        return verdict_from_similarities(model=MODEL, similarities=self.similarities)


class UnreachableReviewer:
    """A sidecar that is down. Every ask fails open, exactly as the real one."""

    def __init__(
        self, why: PhotoReviewUnavailability = PhotoReviewUnavailability.TRANSPORT
    ) -> None:
        self.why = why
        self.asks = 0

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        self.asks += 1
        return verdict_when_unreviewable(self.why)


class SweptDuringTheWalk(InMemoryPhotoStorage):
    """A store where the sweep deletes each photo just after it is listed.

    The one race between these two jobs: both are periodic loops with no lock
    between them (``docs/adr/0092``), and the sweep's delete is what the backfill
    meets between listing a photo and reading its bytes.
    """

    async def read(self, ref: PhotoRef) -> bytes | None:
        self.objects.pop(ref, None)
        return await super().read(ref)


@pytest.fixture(autouse=True)
def no_real_pausing(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records what the job asked to sleep for instead of sleeping.

    The pacing is load-bearing — one sidecar, one worker, a live API beside it —
    so it is asserted rather than waited out.
    """

    slept: list[float] = []

    async def record(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(backfill, "sleep", record)
    return slept


def store_photo(
    storage: InMemoryPhotoStorage,
    *,
    verdict: PhotoReviewVerdict,
    owner_id: UUID = ALICE,
) -> PhotoRef:
    """One photo in the store, carrying the metadata that verdict would write."""

    ref = PhotoRef(owner_id=owner_id, photo_id=new_uuid())
    storage.objects[ref] = _stored(storage, review_metadata(verdict))
    return ref


def _stored(storage: InMemoryPhotoStorage, metadata: dict[str, str]) -> StoredObject:
    image = TranscodedImage(
        data=fixtures.plain_jpeg(), media_type="image/jpeg", width=60, height=40
    )
    return StoredObject(image, metadata, storage.now)


def pass_through_photo(storage: InMemoryPhotoStorage) -> PhotoRef:
    """A photo from before the checker existed: allowed, and no note."""

    return store_photo(
        storage, verdict=PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED)
    )


def use_case(
    storage: InMemoryPhotoStorage,
    reviewer: object,
    *,
    batch_limit: int = 10,
    pause_seconds: float = 1.0,
) -> ReviewUnreviewedPhotos:
    return ReviewUnreviewedPhotos(
        storage=storage,
        transcoder=PillowImageTranscoder(),
        review=reviewer,  # type: ignore[arg-type]
        batch_limit=batch_limit,
        pause_seconds=pause_seconds,
    )


# ---------------------------------------------------------------------------
# Population 1 — the pass-through era
# ---------------------------------------------------------------------------


async def test_a_photo_the_pass_through_waved_through_is_reviewed() -> None:
    storage = InMemoryPhotoStorage()
    ref = pass_through_photo(storage)
    reviewer = ScoringReviewer(ON_COURT)

    report = await use_case(storage, reviewer).execute()

    assert report.examined == 1
    assert report.updated == 1
    metadata = storage.objects[ref].metadata
    assert metadata[REVIEW_METADATA_KEY] == "allowed"
    assert metadata[REVIEW_NOTE_METADATA_KEY].startswith("clip;m=")


async def test_the_bytes_are_left_exactly_as_they_were() -> None:
    # A metadata update is a copy of the object onto itself, and a backfill that
    # re-encoded the pixels would be quietly degrading every photo it touched.
    storage = InMemoryPhotoStorage()
    ref = pass_through_photo(storage)
    before = storage.objects[ref].image

    await use_case(storage, ScoringReviewer()).execute()

    assert storage.objects[ref].image is before


async def test_the_verdict_is_stored_as_the_reviewer_gave_it() -> None:
    # Property 2: the batch does not re-decide. A flagged photo is stored
    # flagged, by the same function the upload path calls.
    storage = InMemoryPhotoStorage()
    ref = pass_through_photo(storage)
    expected = verdict_from_similarities(model=MODEL, similarities=OFF_COURT)

    await use_case(storage, ScoringReviewer(OFF_COURT)).execute()

    assert storage.objects[ref].metadata == review_metadata(expected)
    assert expected.decision is PhotoReviewDecision.FLAGGED


# ---------------------------------------------------------------------------
# Population 2 — the sidecar was down when the photo arrived
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("why", list(PhotoReviewUnavailability))
async def test_a_photo_that_arrived_during_an_outage_is_reviewed(
    why: PhotoReviewUnavailability,
) -> None:
    storage = InMemoryPhotoStorage()
    ref = store_photo(storage, verdict=verdict_when_unreviewable(why))

    report = await use_case(storage, ScoringReviewer()).execute()

    assert report.updated == 1
    assert "unavailable" not in storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY]


# ---------------------------------------------------------------------------
# Not rewriting what is already right
# ---------------------------------------------------------------------------


async def test_an_already_reviewed_photo_is_never_read_reviewed_or_rewritten() -> None:
    storage = InMemoryPhotoStorage()
    ref = store_photo(
        storage, verdict=verdict_from_similarities(model=MODEL, similarities=ON_COURT)
    )
    before = dict(storage.objects[ref].metadata)
    reviewer = ScoringReviewer()

    report = await use_case(storage, reviewer).execute()

    assert report.examined == 1
    assert report.updated == 0
    assert reviewer.images == []
    assert storage.reads == []
    assert storage.metadata_writes == []
    assert storage.objects[ref].metadata == before


async def test_a_second_run_over_what_the_first_fixed_does_nothing() -> None:
    storage = InMemoryPhotoStorage()
    pass_through_photo(storage)
    job = use_case(storage, ScoringReviewer())

    first = await job.execute()
    second = await job.execute()

    assert first.updated == 1
    assert second.updated == 0
    assert len(storage.metadata_writes) == 1


# ---------------------------------------------------------------------------
# `unavailable` is a failure mode of the fix, too
# ---------------------------------------------------------------------------


async def test_a_run_against_a_dead_sidecar_leaves_the_old_note_alone() -> None:
    storage = InMemoryPhotoStorage()
    ref = store_photo(
        storage,
        verdict=verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT),
    )
    before = dict(storage.objects[ref].metadata)

    report = await use_case(storage, UnreachableReviewer()).execute()

    assert report.updated == 0
    assert storage.metadata_writes == []
    assert storage.objects[ref].metadata == before


@pytest.mark.parametrize(
    "why", [PhotoReviewUnavailability.TIMEOUT, PhotoReviewUnavailability.TRANSPORT]
)
async def test_an_unreachable_sidecar_ends_the_run_rather_than_spending_the_budget(
    why: PhotoReviewUnavailability,
) -> None:
    # Every ask costs a full timeout, and the answer will be the same for all of
    # them. The next tick is the retry.
    storage = InMemoryPhotoStorage()
    for _ in range(5):
        pass_through_photo(storage)
    reviewer = UnreachableReviewer(why)

    report = await use_case(storage, reviewer, batch_limit=5).execute()

    assert reviewer.asks == 1
    assert report.stopped_unreviewable
    assert report.unavailable is why
    assert report.updated == 0


@pytest.mark.parametrize(
    "why", [PhotoReviewUnavailability.STATUS, PhotoReviewUnavailability.MALFORMED]
)
async def test_a_refusal_about_one_image_is_stepped_over_not_treated_as_an_outage(
    why: PhotoReviewUnavailability,
) -> None:
    # **The stall this job could have had.** A status or a malformed body may be
    # about the photo in hand; ending the run on one would end every run at the
    # same object for ever, and nothing past it would ever be looked at again.
    storage = InMemoryPhotoStorage()
    for _ in range(3):
        pass_through_photo(storage)
    reviewer = UnreachableReviewer(why)

    report = await use_case(storage, reviewer, batch_limit=5).execute()

    assert reviewer.asks == 3
    assert report.refused == 3
    assert not report.stopped_unreviewable
    assert storage.metadata_writes == []


async def test_one_photo_the_reviewer_refuses_does_not_hide_the_ones_behind_it() -> (
    None
):
    # The same claim from the other side, and the one that matters: the walk
    # gets past it, in this run rather than a later one.
    storage = InMemoryPhotoStorage()
    pass_through_photo(storage)
    pass_through_photo(storage)

    class RefusesTheFirst:
        def __init__(self) -> None:
            self.asks = 0

        async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
            self.asks += 1
            if self.asks == 1:
                return verdict_when_unreviewable(PhotoReviewUnavailability.MALFORMED)
            return verdict_from_similarities(model=MODEL, similarities=ON_COURT)

    report = await use_case(storage, RefusesTheFirst()).execute()

    # Both were asked about in this run, and the one behind the refusal was
    # written — the walk did not end at it.
    assert report.examined == 2
    assert report.refused == 1
    assert report.updated == 1
    assert len(storage.metadata_writes) == 1


# ---------------------------------------------------------------------------
# Rate
# ---------------------------------------------------------------------------


async def test_the_reviewer_is_asked_at_most_the_budget_and_says_there_is_more() -> (
    None
):
    storage = InMemoryPhotoStorage()
    for _ in range(5):
        pass_through_photo(storage)
    reviewer = ScoringReviewer()

    report = await use_case(storage, reviewer, batch_limit=2).execute()

    assert len(reviewer.images) == 2
    assert report.updated == 2
    assert report.stopped_on_budget


async def test_the_next_run_makes_progress_past_what_the_last_one_fixed() -> None:
    storage = InMemoryPhotoStorage()
    for _ in range(5):
        pass_through_photo(storage)
    job = use_case(storage, ScoringReviewer(), batch_limit=2)

    first = await job.execute()
    second = await job.execute()
    third = await job.execute()

    assert [first.updated, second.updated, third.updated] == [2, 2, 1]
    assert not third.stopped_on_budget
    assert len(storage.metadata_writes) == 5


async def test_the_calls_are_spaced_rather_than_fired_in_a_tight_loop(
    no_real_pausing: list[float],
) -> None:
    # One sidecar, one worker by design, and a live API beside it. The pause is
    # between reviews — not before the first, which would delay every run for a
    # gap nothing is in.
    storage = InMemoryPhotoStorage()
    for _ in range(3):
        pass_through_photo(storage)

    await use_case(storage, ScoringReviewer(), pause_seconds=0.25).execute()

    assert no_real_pausing == [0.25, 0.25]


async def test_a_run_with_nothing_to_do_never_pauses(
    no_real_pausing: list[float],
) -> None:
    storage = InMemoryPhotoStorage()
    store_photo(
        storage, verdict=verdict_from_similarities(model=MODEL, similarities=ON_COURT)
    )

    await use_case(storage, ScoringReviewer()).execute()

    assert no_real_pausing == []


# ---------------------------------------------------------------------------
# What the walk meets that is not a photo to review
# ---------------------------------------------------------------------------


async def test_a_photo_the_sweep_deleted_mid_walk_is_counted_and_stepped_over() -> None:
    storage = SweptDuringTheWalk()
    pass_through_photo(storage)
    pass_through_photo(storage)

    report = await use_case(storage, ScoringReviewer()).execute()

    assert report.vanished == 2
    assert report.updated == 0
    assert storage.metadata_writes == []


async def test_an_object_no_decoder_understands_is_counted_and_left_alone() -> None:
    # It cannot be reviewed by anything, and stamping a verdict nobody took
    # would be worse than leaving it visible in the report. A run must not die
    # on it either — a job that did would never get past it, on any tick.
    storage = InMemoryPhotoStorage()
    ref = pass_through_photo(storage)
    storage.objects[ref].image = TranscodedImage(
        data=fixtures.not_an_image(), media_type="image/jpeg", width=1, height=1
    )
    good = pass_through_photo(storage)

    report = await use_case(storage, ScoringReviewer()).execute()

    assert report.unreadable == 1
    assert report.updated == 1
    assert storage.metadata_writes == [good]


async def test_a_verdict_against_a_prompt_set_that_moved_is_counted_never_redone() -> (
    None
):
    # Population 3 (``docs/adr/0132``): whether it is worth re-running is a
    # judgement nobody has made, and the count is what makes it answerable.
    storage = InMemoryPhotoStorage()
    ref = store_photo(
        storage, verdict=verdict_from_similarities(model=MODEL, similarities=ON_COURT)
    )
    note = storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY]
    storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY] = note.replace(
        f"p={PROMPT_SET_FINGERPRINT}", "p=deadbeef"
    )
    reviewer = ScoringReviewer()

    report = await use_case(storage, reviewer).execute()

    assert report.superseded == 1
    assert report.updated == 0
    assert reviewer.images == []


# ---------------------------------------------------------------------------
# The seam the pass-through still holds
# ---------------------------------------------------------------------------


async def test_the_pass_through_reviewer_leaves_the_population_where_it_was() -> None:
    # `PassThroughPhotoReview` concludes nothing and gives no note, so a
    # backfill wired to it must not mark anything as reviewed — which is the
    # same assertion as *the note is the signal*, made from the other side.
    storage = InMemoryPhotoStorage()
    ref = pass_through_photo(storage)

    report = await use_case(storage, PassThroughPhotoReview()).execute()

    assert report.updated == 0
    assert report.stopped_unreviewable
    # A reviewer that concluded nothing gave no reason either, and the report
    # says so rather than inventing one.
    assert report.unavailable is None
    assert REVIEW_NOTE_METADATA_KEY not in storage.objects[ref].metadata
