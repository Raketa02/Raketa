"""The two live strands at the seam, where a set read becomes one person's rows.

``player_score`` publishes *the strands this platform can say anything about*
and the blend over them; the record prints them as the rows behind its pill.
Nothing is computed here, which is the property this file exists to pin: the
figure on each row is ``StrandRatio.value`` **copied**, and the figure on the
panel is ``PlayerScore.published`` **copied**, so a card, a profile and this
sheet cannot print three roundings of one record.

Three things are asserted here rather than over HTTP, because none of them is
visible in a response body that happens to be right:

- **The weights never cross this seam.** The blend arrives already taken. A
  ``StrandRow`` that carried a weight would be a client able to re-derive the
  published number — a fourth rounding of a figure the matcher acts on, and an
  invitation to draw one strand as *worth more* than another on a screen that
  makes no such claim.
- **The rows walk the vocabulary and never the mapping.** Two processes reading
  the same record must draw the same sheet (``docs/adr/0105``).
- **A player with no strand is ``None`` and never a panel of noughts**, which is
  the one rule the whole reliability chain is written around: *no record* is not
  *a bad record*.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from typing import Collection, Mapping
from uuid import UUID, uuid4

import pytest

from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant, InvariantViolated, instant
from app.modules.player_record.domain.record import ReliabilityPanel, StrandRow
from app.modules.player_record.infrastructure.score_subject_reliability import (
    ScoreSubjectReliability,
)
from app.modules.player_score.domain.strands import (
    PUBLISHED_WEIGHTS,
    PlayerScore,
    StrandRatio,
    out_of_a_hundred,
)

NOW: Instant = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))
EARLIER: Instant = instant(datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc))

SUBJECT = uuid4()


def a_ratio(good: int, opportunities: int) -> StrandRatio:
    return StrandRatio(good=good, opportunities=opportunities, last_at=EARLIER)


class PublishedScores:
    """``player_score``'s own read, as a stub. **It records what it was asked.**"""

    def __init__(self, answer: Mapping[UUID, PlayerScore] | None = None) -> None:
        self.answer = dict(answer or {})
        self.asked: list[tuple[frozenset[UUID], Instant]] = []

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        self.asked.append((frozenset(player_ids), now))
        return {
            player_id: score
            for player_id, score in self.answer.items()
            if player_id in set(player_ids)
        }


def reading(strands: Mapping[ReliabilityStrand, StrandRatio]) -> PublishedScores:
    return PublishedScores({SUBJECT: PlayerScore(strands=dict(strands))})


async def test_each_strand_crosses_as_its_two_counts_and_the_figure_shown():
    """**The raw pair, and the figure derived from it — all three.**

    A perfect record over nine opportunities and one over forty are different
    claims, which a bar alone hides; and the figure is served rather than left to
    a client's division, because it is the number the platform *acts* on and a
    second rounding of it would disagree by a point on exactly the values a
    player notices.
    """

    scores = reading(
        {
            ReliabilityStrand.SHOWS_UP: a_ratio(9, 9),
            ReliabilityStrand.ANSWERS_CHALLENGES: a_ratio(7, 11),
        }
    )

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert panel is not None
    assert panel.strands == (
        StrandRow(
            strand=ReliabilityStrand.SHOWS_UP, good=9, opportunities=9, pct=100
        ),
        StrandRow(
            strand=ReliabilityStrand.ANSWERS_CHALLENGES,
            good=7,
            opportunities=11,
            pct=64,
        ),
    )


async def test_the_published_figure_is_the_providers_and_the_rows_reproduce_it():
    """**Copied, not recomputed** — and a reader with the published weights in
    hand gets the same number back out of the rows.

    That is the honesty the sheet promises: the pill is the weighted mean of the
    figures printed beneath it, rather than a number arrived at somewhere else
    and stated over them.
    """

    strands = {
        ReliabilityStrand.SHOWS_UP: a_ratio(9, 10),
        ReliabilityStrand.ANSWERS_CHALLENGES: a_ratio(7, 11),
    }
    scores = reading(strands)

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert panel is not None
    assert panel.player_score == PlayerScore(strands=strands).published
    weighted = sum(PUBLISHED_WEIGHTS[row.strand] * row.pct for row in panel.strands)
    basis = sum(PUBLISHED_WEIGHTS[row.strand] for row in panel.strands)
    assert panel.player_score == out_of_a_hundred(weighted, 100 * basis)


async def test_the_figure_is_the_providers_rounding_and_not_a_second_one():
    """**Where *copied, never derived* stops being a promise and starts being a
    test.** A half is the only place two roundings visibly part company, so the
    counts here are chosen to land on one.

    ``out_of_a_hundred`` rounds halves **up** — one of eight is 13 — while
    Python's own ``round`` rounds them to even and would answer 12, and a
    truncating division would answer 12 as well. Any of the obvious ways to
    re-derive this figure here rather than copy it lands somewhere this
    assertion is not.
    """

    scores = reading({ReliabilityStrand.SHOWS_UP: a_ratio(1, 8)})

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert panel is not None
    assert panel.strands[0].pct == out_of_a_hundred(1, 8) == 13
    assert round(100 * 1 / 8) == 12, "the half this test turns on has moved"


async def test_the_rows_walk_the_vocabulary_and_never_the_mapping():
    """**The registry's order, never the answer's** (``docs/adr/0105``).

    The mapping is built the wrong way round here on purpose: a walk over its
    keys would publish the rows in the order the provider happened to fill them,
    and two processes would draw one record two ways.
    """

    scores = reading(
        {
            ReliabilityStrand.ANSWERS_CHALLENGES: a_ratio(7, 11),
            ReliabilityStrand.SHOWS_UP: a_ratio(9, 9),
        }
    )

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert panel is not None
    assert [row.strand for row in panel.strands] == [
        ReliabilityStrand.SHOWS_UP,
        ReliabilityStrand.ANSWERS_CHALLENGES,
    ]


async def test_a_strand_that_stands_down_is_absent_from_the_rows():
    """A name with no provider is not a row at nought. Three of the five have
    nothing behind them today, and the sheet says nothing about them at all."""

    scores = reading({ReliabilityStrand.SHOWS_UP: a_ratio(3, 4)})

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert panel is not None
    assert [row.strand for row in panel.strands] == [ReliabilityStrand.SHOWS_UP]
    assert panel.player_score == 75


async def test_a_player_the_platform_watched_nothing_of_has_no_panel_at_all():
    """**Absent, and never a section of noughts.** Nobody has failed to turn up
    who was never due to, and the whole zone is omitted rather than drawn
    empty."""

    reliability = ScoreSubjectReliability(PublishedScores())

    assert await reliability.reliability_of(SUBJECT, now=NOW) is None


async def test_one_player_is_asked_about_and_the_instant_is_handed_down():
    """The provider's read is set-shaped because its other caller holds five
    hundred rows; this one holds one person, and takes the clock it was given
    rather than reading a second one."""

    scores = reading({ReliabilityStrand.SHOWS_UP: a_ratio(1, 1)})

    await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert scores.asked == [(frozenset({SUBJECT}), NOW)]


def test_a_panel_with_no_row_on_it_cannot_be_built():
    """The absence has one spelling, and it is the panel not being there. A panel
    holding an empty list would be a second one, and the first reader to draw a
    heading over it would state that the platform watched somebody and saw
    nothing."""

    with pytest.raises(InvariantViolated):
        ReliabilityPanel(player_score=0, strands=())


def test_a_strand_cannot_be_printed_twice_on_one_sheet():
    """Two rows for one name would draw the same fact twice and double its weight
    in any recomputation a reader made from them."""

    row = StrandRow(
        strand=ReliabilityStrand.SHOWS_UP, good=1, opportunities=1, pct=100
    )

    with pytest.raises(InvariantViolated):
        ReliabilityPanel(player_score=100, strands=(row, row))


def test_a_row_claiming_more_good_outcomes_than_opportunities_is_refused():
    with pytest.raises(InvariantViolated):
        StrandRow(
            strand=ReliabilityStrand.SHOWS_UP, good=4, opportunities=3, pct=100
        )


def test_no_weight_crosses_this_seam_in_any_shape():
    """**The strand weights stay on ``player_score``'s side.**

    They are the player's own blend and never the matcher's, and a weight on a
    row would let a client re-derive the pill — a fourth rounding of a number the
    matcher acts on — and invite a sheet that drew one strand as worth more than
    another, which no screen here claims.
    """

    assert [one.name for one in fields(StrandRow)] == [
        "strand",
        "good",
        "opportunities",
        "pct",
    ]
    assert [one.name for one in fields(ReliabilityPanel)] == [
        "player_score",
        "strands",
    ]
