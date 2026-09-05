"""What the on-court line would flag, at any line, over the corpus already held.

**The threshold shipping today is a placeholder that says so** — half, meaning
*the on-court captions won* — and choosing the real one is a fact about a corpus
of real photographs (``domain/photos.py`` — `ON_COURT_CONFIDENCE_THRESHOLD`,
``docs/adr/0129``). This is the read that makes that choice cheap.

**No image is re-scored.** Every verdict recorded the raw similarity vector it
was taken from, one value per caption, beside the fingerprint of the caption set
those were (`review_note`). So *what would the flag rate be at 0.55* is
arithmetic over object metadata: a listing, one ``HEAD`` per photograph, and a
softmax per row. Nothing is written, no bytes are read and the sidecar is not
asked anything. That property is not an accident — it is what ADR-0129 built the
note for, what ADR-0133 declined to put on the wire for, and what ADR-0132's
backfill extended over the whole corpus rather than the recent half.

**What it does not do is choose.** Where the flag rate should sit is a product
judgement, and so is whether the corpus is yet big enough for a rate to mean
anything; both are outside what any walk over stored numbers can answer (#316).
This reports the curve and the size of the population it was measured over, and
the number it would be picked from goes into `photos.py` by hand — never into
configuration, because a threshold the environment could select is a photograph
flagged on a laptop and allowed in production.

**Three populations are not evidence, and they are counted rather than
skipped.** A photo nobody looked at, a photo that arrived while the sidecar was
unreachable, and a photo scored against captions that have since moved are all
things the platform holds and none of them says anything about a line — see
`PhotoReviewStanding` and `judged_against_a_superseded_set`. A run that dropped
them quietly would report a rate over a denominator nobody could see.

**And there is no budget.** The backfill stops on one because a bounded run
still makes progress; a rate over a prefix of the bucket is not a rate, so this
one walks the corpus or reports nothing.
"""

from __future__ import annotations

from collections import Counter
from contextlib import aclosing
from dataclasses import dataclass
from typing import Sequence

from app.modules.player_profile.domain.photos import (
    ON_COURT_CONFIDENCE_THRESHOLD,
    PROMPT_SET_FINGERPRINT,
    PhotoReviewStanding,
    flagged_at,
    judged_against_a_superseded_set,
    on_court_confidence,
    recorded_score_in,
    review_standing,
)
from app.modules.player_profile.domain.ports import PhotoStorage


@dataclass(frozen=True, slots=True)
class FlagRateAtThreshold:
    """One row of the curve: a candidate line, and what it would do.

    ``would_change`` is measured against the threshold **in force**, and it is
    here because moving the line is not the whole of the change. A photograph
    already stamped keeps its stamp until something re-reviews it, and the
    prompt-set fingerprint does not move, so ADR-0132's job will not pick it up
    either: whether to re-stamp the corpus under a new line is a second
    decision, and this is its size in photographs.
    """

    threshold: float
    flagged: int
    rate: float
    would_change: int


@dataclass(frozen=True, slots=True)
class MeasuredUnder:
    """How many of the measured photographs one reviewer scored.

    **Two corpora scored by two models are two corpora**, and the report says so
    rather than blending them into one rate. The instance this exists for is not
    a model upgrade: the workbench's seeded photographs carry *declared* verdicts
    written through the real constructors (``app/seeds/photos.py``), so their
    notes are well-formed, current-fingerprint and counted like any other. A run
    on a laptop would otherwise print a perfectly plausible rate over fixtures,
    which is the one way this exercise can mislead the decision it exists for.
    """

    model: str
    photographs: int


@dataclass(frozen=True, slots=True)
class OnCourtCorpusReading:
    """The curve, and the population it was measured over.

    **The four exclusions are as much of the answer as the rates are.** A run
    over a corpus that is nine-tenths ``never_asked`` has measured a tenth of
    the platform's photographs, and the shape of the curve says nothing about
    that — so the counts travel beside it rather than in a log line somewhere.

    ``rates`` is **empty when nothing could be measured**, rather than a table
    of zeroes. Zero flagged out of zero photographs renders as *nothing would be
    flagged*, which is the opposite of what happened and is exactly the answer a
    run against the wrong bucket gives.
    """

    #: The caption set every measured photo was scored under. A vector means
    #: nothing without it, so the reading names it rather than implying it.
    prompt_set: str

    #: Every photograph the walk saw, whether or not it could say anything.
    examined: int

    #: The photographs the curve is over: really scored, against these captions,
    #: with a vector today's arithmetic can be applied to.
    comparable: int

    #: Population 1 — no note, or a note nothing can read. Nobody looked.
    never_asked: int

    #: Population 2 — the reviewer was asked and could not answer.
    unavailable: int

    #: Population 3 — really scored, against captions that have since moved.
    superseded: int

    #: Scored under these captions, and carrying a vector that will not parse or
    #: will not score. A note this application did not write.
    unreadable_evidence: int

    #: Who scored the measured photographs, most first. Empty when nothing was
    #: measured — see `MeasuredUnder` for why a rate without this can mislead.
    measured_by: tuple[MeasuredUnder, ...]

    rates: tuple[FlagRateAtThreshold, ...]


class MeasureOnCourtFlagRates:
    def __init__(self, *, storage: PhotoStorage) -> None:
        self._storage = storage

    async def execute(self, *, candidates: Sequence[float]) -> OnCourtCorpusReading:
        """Walk the stored notes and answer for each candidate line.

        The candidates are the question rather than the wiring, which is why
        they arrive here and not in the constructor: the walk is a request per
        photograph and the arithmetic over it is free, so one walk answers as
        many lines as somebody wants to ask about.
        """

        confidences: list[float] = []
        reviewers: Counter[str] = Counter()
        examined = 0
        never_asked = 0
        unavailable = 0
        superseded = 0
        unreadable_evidence = 0

        # `aclosing` for the reason the backfill uses it: the adapter holds an
        # open store client across the yields, and this walk can end on an
        # exception from the arithmetic as easily as on the end of the listing.
        async with aclosing(self._storage.with_review_notes()) as photos:
            async for photo in photos:
                examined += 1
                standing = review_standing(photo.note)
                if standing is PhotoReviewStanding.NEVER_ASKED:
                    never_asked += 1
                    continue
                if standing is PhotoReviewStanding.UNAVAILABLE:
                    unavailable += 1
                    continue
                if judged_against_a_superseded_set(photo.note):
                    superseded += 1
                    continue

                score = recorded_score_in(photo.note)
                if score is None:
                    unreadable_evidence += 1
                    continue
                try:
                    confidence = on_court_confidence(score.similarities)
                except ValueError:
                    # A vector that is not one value per caption. The domain
                    # refuses to score it rather than slicing whatever it was
                    # handed, and the refusal is caught rather than re-checked
                    # here so that *how many numbers a verdict has* stays in one
                    # place. A note this application did not write, so it joins
                    # the one it cannot parse rather than getting a count of its
                    # own.
                    unreadable_evidence += 1
                    continue
                confidences.append(confidence)
                reviewers[score.model] += 1

        return OnCourtCorpusReading(
            prompt_set=PROMPT_SET_FINGERPRINT,
            examined=examined,
            comparable=len(confidences),
            never_asked=never_asked,
            unavailable=unavailable,
            superseded=superseded,
            unreadable_evidence=unreadable_evidence,
            # Most-scored first, then alphabetically — so the reviewer that
            # produced most of the corpus is the first thing read, and a rerun
            # over an unchanged bucket prints the same order.
            measured_by=tuple(
                MeasuredUnder(model=model, photographs=count)
                for model, count in sorted(
                    reviewers.items(), key=lambda pair: (-pair[1], pair[0])
                )
            ),
            rates=flag_rates(confidences, candidates),
        )


def flag_rates(
    confidences: Sequence[float], candidates: Sequence[float]
) -> tuple[FlagRateAtThreshold, ...]:
    """The curve over one set of confidences. Pure, and the whole of the maths.

    **Every comparison goes through `flagged_at`**, which is the one the upload
    path applies: a rate computed with its own copy of the operator differs by
    exactly the photographs sitting on the line, reads as measured, and nothing
    downstream could tell (``docs/adr/0132`` makes the argument for the batch
    reviewer; it is the same one).

    Sorted and deduplicated, so the table is a curve rather than a list in
    whatever order somebody typed, and asking about a line twice costs one row.
    """

    if not confidences:
        return ()
    in_force = [
        flagged_at(confidence=c, threshold=ON_COURT_CONFIDENCE_THRESHOLD)
        for c in confidences
    ]
    rows = []
    for threshold in sorted(set(candidates)):
        at_candidate = [
            flagged_at(confidence=c, threshold=threshold) for c in confidences
        ]
        rows.append(
            FlagRateAtThreshold(
                threshold=threshold,
                flagged=sum(at_candidate),
                rate=sum(at_candidate) / len(confidences),
                would_change=sum(
                    now != then
                    for now, then in zip(at_candidate, in_force, strict=True)
                ),
            )
        )
    return tuple(rows)
