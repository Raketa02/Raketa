"""``python -m app.modules.player_profile.infrastructure.flag_rate_cli`` — the curve.

What ``make photo-flag-rate`` runs: the flag rate the on-court check would have
produced at each of a set of candidate thresholds, over the photographs the
platform already holds (#316). **Read-only in the strongest sense** — no image
is re-scored, no metadata is written and the sidecar is not reachable from here
at all; the evidence is the similarity vector every verdict recorded beside its
bytes.

A one-shot command rather than a job, and rather than a route. It answers a
question somebody asks while deciding a number, not one anything in the product
asks — so ``docs/adr/0092``'s register is the wrong home (that is for loops),
and an admin endpoint would be a button that prints a distribution of everybody's
photographs to whoever pressed it.

Thin on purpose, like ``rebuild_cli`` beside it: the store comes out of the
composition root, so this walks the same bucket a request does rather than a
second opinion about where photographs live. It lives under ``app/`` for the
same blunt reason that one does — the container image copies ``app/`` and not
``scripts/``, and the bucket is reachable from the container.

**It prints the population beside the curve, and says out loud what it cannot
decide.** Where the flag rate should sit, and whether the corpus is yet large
enough for a rate to mean anything, are product judgements; the reason #316 is
``ready-for-human`` is that no walk over stored numbers can make either.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Sequence

from app.bootstrap.composition import build_photo_storage
from app.core.config import get_settings
from app.modules.player_profile.application.measure_on_court_flag_rates import (
    MeasureOnCourtFlagRates,
    OnCourtCorpusReading,
)
from app.modules.player_profile.domain.photos import ON_COURT_CONFIDENCE_THRESHOLD

#: The lines asked about when nobody names any. A twentieth of the interval,
#: which is fine enough to see the shape and coarse enough to read, plus the
#: threshold in force however it is spelled — a curve that did not include
#: today's line would leave a reader unable to see where they already are.
DEFAULT_CANDIDATES: tuple[float, ...] = tuple(
    sorted(
        {round(step / 20, 2) for step in range(1, 20)}
        | {ON_COURT_CONFIDENCE_THRESHOLD}
    )
)


async def measure(candidates: Sequence[float]) -> OnCourtCorpusReading:
    settings = get_settings()
    storage = build_photo_storage(settings)
    return await MeasureOnCourtFlagRates(storage=storage).execute(
        candidates=candidates
    )


def main(argv: Sequence[str] | None = None) -> int:
    candidates = _parse(argv)
    reading = asyncio.run(measure(candidates))
    for line in _report(reading):
        print(line)
    # **Non-zero when nothing could be measured.** A run against an empty bucket,
    # or against one whose every photograph predates the checker, prints a
    # perfectly well-formed report about no photographs — and the reader who
    # exits 0 goes away believing the corpus said something.
    return 0 if reading.comparable else 1


def _parse(argv: Sequence[str] | None) -> tuple[float, ...]:
    parser = argparse.ArgumentParser(
        prog="flag_rate_cli",
        description=(
            "The on-court flag rate at each candidate threshold, over the "
            "similarity vectors already stored beside the photographs. "
            "Reads only: nothing is re-scored and nothing is written."
        ),
    )
    parser.add_argument(
        "thresholds",
        nargs="*",
        type=_a_share,
        help=(
            "candidate lines to report, as shares of the probability mass on "
            "the on-court captions. Defaults to a twentieth-interval sweep."
        ),
    )
    parsed = parser.parse_args(argv)
    return tuple(parsed.thresholds) or DEFAULT_CANDIDATES


def _a_share(value: str) -> float:
    """A candidate threshold is a share, so it lives in the unit interval.

    Refused here rather than reported as a row of zeroes: a line at 1.5 flags
    every photograph on the platform and a line at -1 flags none, and both are
    somebody having typed a percentage.
    """

    share = float(value)
    if not 0.0 <= share <= 1.0:
        raise argparse.ArgumentTypeError(
            f"a confidence is a share between 0 and 1, got {value}"
        )
    return share


def _report(reading: OnCourtCorpusReading) -> list[str]:
    """What the operator reads.

    The exclusions are printed **before** the curve, deliberately. A rate is a
    number over a denominator, and a reader who meets the table first has
    already formed an opinion by the time they find out it was measured over a
    tenth of the bucket.
    """

    lines = [
        "on-court flag rate over the stored corpus",
        f"  prompt set            {reading.prompt_set}",
        f"  photographs seen      {reading.examined}",
        f"  measured              {reading.comparable}",
        f"  never asked           {reading.never_asked}"
        "   (nobody looked — ADR-0132 population 1)",
        f"  unavailable           {reading.unavailable}"
        "   (the sidecar could not be asked — population 2)",
        f"  superseded            {reading.superseded}"
        "   (scored against captions that have moved — population 3)",
        f"  unreadable evidence   {reading.unreadable_evidence}"
        "   (a note this application did not write)",
        "",
    ]
    if not reading.by_reviewer:
        lines.append(
            "  nothing could be measured — there is no rate over no photographs"
        )
        return lines

    # One table per reviewer, never one blended. Two models are two corpora, and
    # a rate across both is a fact about neither — see `ReviewerCorpus`.
    for corpus in reading.by_reviewer:
        lines.extend(
            [
                f"  scored by {corpus.model} — {corpus.photographs} photographs",
                "    threshold   flagged      rate   would re-stamp",
            ]
        )
        for row in corpus.rates:
            in_force = (
                "   <- in force"
                if row.threshold == ON_COURT_CONFIDENCE_THRESHOLD
                else ""
            )
            lines.append(
                f"    {row.threshold:>9.2f}   {row.flagged:>7}   {row.rate:>7.1%}"
                f"   {row.would_change:>14}{in_force}"
            )
        lines.append("")

    lines.extend(
        [
            "  'would re-stamp' is how many stored verdicts the move would make"
            " wrong.",
            "  A photograph keeps the stamp it was given until something"
            " re-reviews it, and",
            "  the prompt set does not move, so ADR-0132's backfill will not"
            " pick it up: whether",
            "  to re-stamp the corpus is a second decision (#316).",
            "",
            "  Where the rate should sit, and whether any of these corpora is"
            " large enough for",
            "  one to mean anything, are the two judgements this cannot make."
            " Read the reviewer",
            "  each table is headed by first: a corpus scored by a workbench's"
            " declared fixtures",
            "  is a well-formed rate about nothing.",
        ]
    )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
