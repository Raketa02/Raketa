"""Player reliability at the seam, where a set read becomes one person's panel
(#659; ``docs/adr/0195`` §1).

``player_score`` publishes the figure in points, *New* and the counts; the record
prints them. Nothing is computed here, which is the property this file pins: the
points, the band, *New* and every count are ``PlayerScore``'s **copied**, so the
record and a group's Members list cannot print two figures for one person.

Asserted here rather than over HTTP, because none of it is visible in a response
body that happens to be right:

- **The band is the provider's and never re-derived** — the engine's floors,
  read once, on the other side.
- **Everybody has a panel**: a player nothing has happened to reads *100 · New*.
- **One player is asked about, at the instant handed down.**
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from typing import Collection, Mapping
from uuid import UUID, uuid4

import pytest

from app.engines.matchfit.core import ReliabilityBand
from app.kernel import Instant, InvariantViolated, instant
from app.modules.player_record.domain.record import ReliabilityPanel
from app.modules.player_record.infrastructure.score_subject_reliability import (
    ScoreSubjectReliability,
)
from app.modules.player_score.domain.points import PlayerScore, ReliabilityCounts

NOW: Instant = instant(datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc))

SUBJECT = uuid4()


def a_score(points: int, *, is_new: bool = False, **counts: int) -> PlayerScore:
    zero = dict(
        turned_up=0, turned_up_of=0, late=0, kept=0, kept_of=0, left_in_dispute=0
    )
    return PlayerScore(
        points=points, is_new=is_new, counts=ReliabilityCounts(**{**zero, **counts})
    )


class PublishedScores:
    """``player_score``'s own read, as a stub. **It records what it was asked.**"""

    def __init__(self, answer: Mapping[UUID, PlayerScore]) -> None:
        self.answer = dict(answer)
        self.asked: list[tuple[frozenset[UUID], Instant]] = []

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        self.asked.append((frozenset(player_ids), now))
        return {player_id: self.answer[player_id] for player_id in player_ids}


async def test_the_figure_its_band_new_and_the_counts_cross_copied():
    """Sergio after his autumn: 75, High, and turned up 3 of 4."""

    scores = PublishedScores(
        {
            SUBJECT: a_score(
                75,
                turned_up=3,
                turned_up_of=4,
                late=1,
                kept=4,
                kept_of=5,
                left_in_dispute=2,
            )
        }
    )

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert panel == ReliabilityPanel(
        player_score=75,
        band=ReliabilityBand.HIGH,
        is_new=False,
        turned_up=3,
        turned_up_of=4,
        late=1,
        kept=4,
        kept_of=5,
        left_in_dispute=2,
    )


async def test_a_player_nothing_has_happened_to_reads_a_hundred_and_new():
    scores = PublishedScores({SUBJECT: a_score(100, is_new=True)})

    panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert (panel.player_score, panel.band, panel.is_new) == (
        100,
        ReliabilityBand.VERY_HIGH,
        True,
    )
    assert (panel.turned_up, panel.turned_up_of) == (0, 0)


async def test_the_band_is_the_providers_and_never_a_second_derivation():
    """The panel's band is ``PlayerScore.band`` — the engine's floors — for
    every figure either side of each edge."""

    for points in (90, 89, 75, 74, 50, 49):
        score = a_score(points)
        scores = PublishedScores({SUBJECT: score})

        panel = await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

        assert panel.band is score.band


async def test_one_player_is_asked_about_and_the_instant_is_handed_down():
    scores = PublishedScores({SUBJECT: a_score(100, is_new=True)})

    await ScoreSubjectReliability(scores).reliability_of(SUBJECT, now=NOW)

    assert scores.asked == [(frozenset({SUBJECT}), NOW)]


def test_a_figure_off_the_scale_cannot_be_built():
    with pytest.raises(InvariantViolated):
        ReliabilityPanel(
            player_score=101,
            band=ReliabilityBand.VERY_HIGH,
            is_new=False,
            turned_up=0,
            turned_up_of=0,
            late=0,
            kept=0,
            kept_of=0,
            left_in_dispute=0,
        )


def test_a_count_larger_than_what_it_is_of_cannot_be_built():
    with pytest.raises(InvariantViolated):
        ReliabilityPanel(
            player_score=100,
            band=ReliabilityBand.VERY_HIGH,
            is_new=False,
            turned_up=3,
            turned_up_of=2,
            late=0,
            kept=0,
            kept_of=0,
            left_in_dispute=0,
        )


def test_no_strand_ratio_or_weight_crosses_this_seam_in_any_shape():
    """The strands, their ratios and the weights left with ADR-0195 §1: the
    panel is points, a band, *New* and four counts — and, on your own record,
    your reliability filter (§6, #661) — and nothing else."""

    assert {field.name for field in fields(ReliabilityPanel)} == {
        "player_score",
        "band",
        "is_new",
        "turned_up",
        "turned_up_of",
        "late",
        "kept",
        "kept_of",
        "left_in_dispute",
        "filter",
    }
