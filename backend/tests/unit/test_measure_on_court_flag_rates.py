"""The threshold's corpus: what the stored notes already say, at any line.

**Read-only, and that is the whole shape of it** (#316). Every verdict recorded
the similarity vector it was taken from, so *what would the flag rate be at
0.55* is arithmetic over metadata the platform already holds — no image is
re-scored, nothing is written, and the sidecar is not asked anything.

Three properties carry this file, and each is a way a rate could be wrong in a
way no amount of running it would reveal:

1. *It measures the line the upload path applies.* The rate at the threshold in
   force has to equal the share `verdict_from_similarities` actually flagged, or
   every other row of the table is measured against a rule nobody ships.
2. *It counts what it dropped.* Three populations cannot be in a corpus — nobody
   looked, the sidecar was down, the captions have moved — and a run that
   silently skipped them would report a rate over an unknown denominator.
3. *No photos means no rate.* A rate of zero over an empty corpus reads as
   *nothing is flagged*, which is the opposite of *nothing was measured*.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence
from uuid import UUID

import pytest

import app.modules.player_profile.infrastructure.flag_rate_cli as cli
from app.modules.player_profile.application.measure_on_court_flag_rates import (
    FlagRateAtThreshold,
    MeasureOnCourtFlagRates,
    MeasuredUnder,
    OnCourtCorpusReading,
)
from app.modules.player_profile.domain.photos import (
    OFF_COURT_PROMPTS,
    ON_COURT_CONFIDENCE_THRESHOLD,
    ON_COURT_PROMPTS,
    PROMPT_SET_FINGERPRINT,
    REVIEW_NOTE_METADATA_KEY,
    PhotoRef,
    PhotoReviewDecision,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    TranscodedImage,
    on_court_confidence,
    review_metadata,
    verdict_from_similarities,
    verdict_when_unreviewable,
)
from app.shared.ids import new_uuid
from tests.unit import image_fixtures as fixtures
from tests.unit.fake_photo_storage import InMemoryPhotoStorage, StoredObject

ALICE = UUID("11111111-1111-1111-1111-111111111111")

MODEL = "openai/clip-vit-base-patch32"


def similarities(on_court: float, off_court: float = 0.20) -> list[float]:
    """One vector: every on-court prompt at one value, every other at another."""

    return [on_court] * len(ON_COURT_PROMPTS) + [off_court] * len(OFF_COURT_PROMPTS)


def store(storage: InMemoryPhotoStorage, verdict: PhotoReviewVerdict) -> PhotoRef:
    ref = PhotoRef(owner_id=ALICE, photo_id=new_uuid())
    image = TranscodedImage(
        data=fixtures.plain_jpeg(), media_type="image/jpeg", width=60, height=40
    )
    storage.objects[ref] = StoredObject(image, review_metadata(verdict), storage.now)
    return ref


def scored(
    storage: InMemoryPhotoStorage, on_court: float, *, model: str = MODEL
) -> float:
    """One reviewed photo in the store. Returns the confidence it was scored at."""

    vector = similarities(on_court)
    store(storage, verdict_from_similarities(model=model, similarities=vector))
    return on_court_confidence(vector)


async def reading(
    storage: InMemoryPhotoStorage, candidates: Sequence[float] = (0.5,)
) -> OnCourtCorpusReading:
    return await MeasureOnCourtFlagRates(storage=storage).execute(
        candidates=candidates
    )


# ---------------------------------------------------------------------------
# The corpus, and what cannot be in it
# ---------------------------------------------------------------------------


async def test_a_reviewed_photo_is_one_row_of_the_corpus() -> None:
    storage = InMemoryPhotoStorage()
    scored(storage, 0.34)
    scored(storage, 0.10)

    result = await reading(storage)

    assert result.examined == 2
    assert result.comparable == 2
    assert result.prompt_set == PROMPT_SET_FINGERPRINT


async def test_the_three_populations_that_cannot_be_measured_are_counted() -> None:
    """Counted rather than skipped, because the denominator is the whole point.

    A rate over *the photos that happened to parse* is a number with no stated
    population behind it. Each of these three is a different reason a photograph
    the platform holds is not evidence about a threshold, and the reader has to
    be able to see how much of the corpus each one took.
    """

    storage = InMemoryPhotoStorage()
    scored(storage, 0.34)
    # Nobody ever looked: the pass-through era, allowed by construction.
    store(storage, PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED))
    # The sidecar was down, so there is no vector to re-derive anything from.
    store(storage, verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT))

    result = await reading(storage)

    assert result.examined == 3
    assert result.comparable == 1
    assert result.never_asked == 1
    assert result.unavailable == 1
    assert result.superseded == 0


async def test_a_photo_judged_against_captions_that_moved_is_not_evidence() -> None:
    """Population 3, and the fingerprint is what makes it visible at all.

    A similarity vector means nothing without the captions it was measured
    against. Mixing one scored under a superseded set into the distribution
    would put a number measured against different questions on the same axis as
    the rest, and nothing about the resulting rate would look wrong.
    """

    storage = InMemoryPhotoStorage()
    scored(storage, 0.34)
    ref = store(
        storage,
        verdict_from_similarities(model=MODEL, similarities=similarities(0.34)),
    )
    stale = storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY]
    storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY] = stale.replace(
        f"p={PROMPT_SET_FINGERPRINT}", "p=deadbeef"
    )

    result = await reading(storage)

    assert result.comparable == 1
    assert result.superseded == 1


async def test_evidence_that_will_not_score_is_dropped_and_counted() -> None:
    # A note this application did not write — the vector is short, so today's
    # arithmetic cannot be applied to it. Dropping it costs one row; scoring it
    # anyway would put a confident number about the wrong captions in the table.
    storage = InMemoryPhotoStorage()
    scored(storage, 0.34)
    ref = store(
        storage,
        verdict_from_similarities(model=MODEL, similarities=similarities(0.34)),
    )
    note = storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY]
    storage.objects[ref].metadata[REVIEW_NOTE_METADATA_KEY] = (
        note[: note.index(";s=")] + ";s=0.31,0.29"
    )

    result = await reading(storage)

    assert result.comparable == 1
    assert result.unreadable_evidence == 1


async def test_the_reading_names_the_reviewers_the_corpus_was_scored_by() -> None:
    """Two corpora scored by two models are two corpora.

    The sharpest instance is not a model upgrade: the workbench's own seeded
    photographs carry declared verdicts written through the real constructors
    (``app/seeds/photos.py``), so their notes are well-formed, current-fingerprint
    and **counted**. A run on a laptop therefore prints a perfectly plausible
    rate over fixtures unless the report says whose numbers those were.
    """

    storage = InMemoryPhotoStorage()
    scored(storage, 0.34)
    scored(storage, 0.10)
    scored(storage, 0.22, model="seed-declared")

    result = await reading(storage)

    assert result.measured_by == (
        MeasuredUnder(model=MODEL, photographs=2),
        MeasuredUnder(model="seed-declared", photographs=1),
    )


async def test_a_corpus_nobody_could_measure_names_no_reviewer() -> None:
    storage = InMemoryPhotoStorage()
    store(storage, PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED))

    assert (await reading(storage)).measured_by == ()


# ---------------------------------------------------------------------------
# The rate
# ---------------------------------------------------------------------------


async def test_the_rate_at_the_line_in_force_is_what_the_upload_path_flagged() -> None:
    """Property 1. If this row is wrong every other row is measured against a
    rule nobody ships."""

    storage = InMemoryPhotoStorage()
    flagged_by_the_upload_path = 0
    for on_court in (0.34, 0.28, 0.22, 0.19, 0.10):
        vector = similarities(on_court)
        store(storage, verdict_from_similarities(model=MODEL, similarities=vector))
        if verdict_from_similarities(model=MODEL, similarities=vector).is_flagged:
            flagged_by_the_upload_path += 1

    result = await reading(storage, candidates=(ON_COURT_CONFIDENCE_THRESHOLD,))

    assert result.rates[0].flagged == flagged_by_the_upload_path
    assert result.rates[0].rate == pytest.approx(flagged_by_the_upload_path / 5)


async def test_the_rate_at_a_candidate_is_the_share_below_it() -> None:
    storage = InMemoryPhotoStorage()
    confidences = [scored(storage, on_court) for on_court in (0.34, 0.22, 0.10)]

    result = await reading(storage, candidates=(0.2, 0.8))

    for row in result.rates:
        expected = sum(1 for c in confidences if c < row.threshold)
        assert row.flagged == expected
        assert row.rate == pytest.approx(expected / len(confidences))


async def test_a_candidate_is_asked_once_and_the_table_climbs() -> None:
    # Sorted and deduplicated, so the table reads as one curve — the rates are
    # monotone in the threshold, and a caller that passed 0.5 twice gets one row.
    storage = InMemoryPhotoStorage()
    for on_court in (0.34, 0.22, 0.10):
        scored(storage, on_court)

    result = await reading(storage, candidates=(0.9, 0.1, 0.5, 0.5))

    assert [row.threshold for row in result.rates] == [0.1, 0.5, 0.9]
    assert [row.flagged for row in result.rates] == sorted(
        row.flagged for row in result.rates
    )


async def test_the_table_sizes_the_re_stamp_the_move_would_need() -> None:
    """What moving the line would cost, in photographs.

    A stored verdict does not change when the threshold does — it keeps the
    stamp it was given until something re-reviews it, and the fingerprint does
    not move, so ADR-0132's job will not pick it up either. Whether to re-stamp
    the corpus is a second decision, and this is its size.
    """

    storage = InMemoryPhotoStorage()
    confidences = [scored(storage, on_court) for on_court in (0.34, 0.22, 0.10)]

    result = await reading(
        storage, candidates=(ON_COURT_CONFIDENCE_THRESHOLD, 0.9, 0.1)
    )
    at_the_line = {row.threshold: row for row in result.rates}

    assert at_the_line[ON_COURT_CONFIDENCE_THRESHOLD].would_change == 0
    for threshold in (0.9, 0.1):
        expected = sum(
            1
            for c in confidences
            if (c < threshold) != (c < ON_COURT_CONFIDENCE_THRESHOLD)
        )
        assert at_the_line[threshold].would_change == expected


async def test_no_photos_means_no_rate_rather_than_a_rate_of_zero() -> None:
    """Property 3. Zero flagged out of zero photos reads as *nothing is
    flagged*, which is the opposite of *nothing was measured* — and it is the
    answer a run against the wrong bucket gives."""

    storage = InMemoryPhotoStorage()
    store(storage, PhotoReviewVerdict(decision=PhotoReviewDecision.ALLOWED))

    result = await reading(storage, candidates=(0.1, 0.5, 0.9))

    assert result.comparable == 0
    assert result.rates == ()


async def test_nothing_is_written_and_no_bytes_are_read() -> None:
    """Property of the whole exercise: it is a walk over metadata.

    Re-scoring is what this issue exists to avoid, and reading the bytes is the
    first half of doing it. The listing already carries the note, so a run that
    touched an object at all would be paying for something it does not need.
    """

    storage = InMemoryPhotoStorage()
    scored(storage, 0.34)

    await reading(storage)

    assert storage.reads == []
    assert storage.metadata_writes == []
    assert storage.deletions == []


# ---------------------------------------------------------------------------
# The command that asks it
# ---------------------------------------------------------------------------


def test_the_default_sweep_includes_the_line_in_force() -> None:
    """A curve that did not include today's line would leave a reader unable to
    see where they already are — which is the first thing they need."""

    assert ON_COURT_CONFIDENCE_THRESHOLD in cli.DEFAULT_CANDIDATES
    assert list(cli.DEFAULT_CANDIDATES) == sorted(set(cli.DEFAULT_CANDIDATES))


def test_a_threshold_outside_the_unit_interval_is_refused() -> None:
    # A confidence is a share. A line at 1.5 flags every photograph and a line
    # at -1 flags none; both are somebody having typed a percentage, and both
    # would render as a perfectly plausible row.
    for typed in ("1.5", "-0.2", "50"):
        with pytest.raises(argparse.ArgumentTypeError):
            cli._a_share(typed)

    assert cli._parse(["0.55", "0.6"]) == (0.55, 0.6)
    assert cli._parse([]) == cli.DEFAULT_CANDIDATES


def test_the_report_names_the_population_before_the_curve() -> None:
    """A rate is a number over a denominator, and a reader who meets the table
    first has formed an opinion before finding out what it was measured on."""

    lines = cli._report(
        OnCourtCorpusReading(
            prompt_set="deadbeef",
            examined=10,
            comparable=4,
            never_asked=3,
            unavailable=2,
            superseded=1,
            unreadable_evidence=0,
            measured_by=(MeasuredUnder(model="seed-declared", photographs=4),),
            rates=(
                FlagRateAtThreshold(
                    threshold=ON_COURT_CONFIDENCE_THRESHOLD,
                    flagged=1,
                    rate=0.25,
                    would_change=0,
                ),
            ),
        )
    )
    rendered = "\n".join(lines)

    assert rendered.index("never asked") < rendered.index("threshold   flagged")
    assert rendered.index("seed-declared") < rendered.index("threshold   flagged")
    assert "in force" in rendered
    assert "4 photographs is enough" in rendered


def test_measuring_nothing_says_so_and_exits_non_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run against an empty bucket prints a well-formed report about no
    photographs, and a reader who exits 0 goes away believing it said
    something."""

    empty = OnCourtCorpusReading(
        prompt_set=PROMPT_SET_FINGERPRINT,
        examined=0,
        comparable=0,
        never_asked=0,
        unavailable=0,
        superseded=0,
        unreadable_evidence=0,
        measured_by=(),
        rates=(),
    )

    async def measured(candidates: Sequence[float]) -> OnCourtCorpusReading:
        return empty

    monkeypatch.setattr(cli, "measure", measured)

    assert cli.main([]) == 1
    assert "no rate over no photographs" in "\n".join(cli._report(empty))


def test_the_makefile_runs_this_module() -> None:
    # The command and the target are two spellings of one path, and a rename
    # that moved only the module would leave a target that fails at import.
    makefile = (
        Path(__file__).resolve().parents[2] / "Makefile"
    ).read_text(encoding="utf-8")

    assert "photo-flag-rate:" in makefile
    assert "app.modules.player_profile.infrastructure.flag_rate_cli" in makefile
