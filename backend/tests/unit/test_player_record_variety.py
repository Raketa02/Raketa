"""Opponent variety at the seam, where two counts change their names.

``player_record`` declares its own types rather than reusing another context's
(``docs/adr/0155``), and this is the third time that costs a second spelling —
after ``OnCourtVerdict`` beside ``PhotoReviewDecision`` and ``GameOutcome``
beside ``Outcome``. This pair is different in kind from those two: the words do
**not** agree, deliberately. ``games`` measured ``distinct_counterparts`` over
``times_on_court`` — everybody who was on a court with them, on that context's own
rule that a pair is anybody you have played — and the record prints
``distinct_opponents`` over ``times_on_court``, which is what the row is called on
screen.

That is precisely why it is pinned here rather than left to the database-backed
demand. Two enums that drift are caught by comparing their values; two **numbers
that swap places** would pass every type checker, satisfy both protocols, and
publish a person's games as their opponents — so what this file asserts is that
the right number arrives under the right name, and that neither type has grown a
field the other silently drops.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.kernel import Instant, instant
from app.modules.games.domain.ports import OpponentVariety as Measured
from app.modules.player_record.domain.record import OpponentVariety as Printed
from app.modules.player_record.infrastructure.games_subject_variety import (
    GamesSubjectVariety,
)

NOW: Instant = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))
SUBJECT = uuid4()


class PublishedVariety:
    """``games``' own fold, as a stub. **It records what it was asked.**"""

    def __init__(self, answer: Measured | None) -> None:
        self.answer = answer
        self.asked: list[UUID] = []

    async def variety_of(
        self, player_id: UUID, *, now: Instant
    ) -> Measured | None:
        self.asked.append(player_id)
        return self.answer


async def test_the_two_counts_keep_their_places_when_they_change_their_names():
    """**The bug this file exists for.** Both halves are integers, so a mapping
    that swapped them would type-check, satisfy both protocols and publish
    somebody's evenings as their acquaintances.

    The two numbers are chosen to be different from each other on purpose: equal
    ones would let a swap pass.
    """

    games = PublishedVariety(Measured(distinct_counterparts=14, times_on_court=20))

    printed = await GamesSubjectVariety(games).variety_of(SUBJECT, now=NOW)

    assert printed == Printed(distinct_opponents=14, times_on_court=20)
    assert games.asked == [SUBJECT]


async def test_a_measured_nothing_stays_nothing_across_the_seam():
    """**One spelling for absence, all the way out.** A player no counted game
    was recorded for has no habit to describe, and no layer between the fold and
    the response turns that into a nought on the way past."""

    games = PublishedVariety(None)

    assert await GamesSubjectVariety(games).variety_of(SUBJECT, now=NOW) is None


def test_neither_shape_has_grown_a_field_the_other_would_drop():
    """**The rename is total, and a third number would be a decision.**

    The adapter names both fields rather than spreading them, so a field added on
    the provider's side is silently absent from the sheet — which is the right
    default and the wrong thing to discover from a blank row. This is where the
    day that happens is a red build instead.
    """

    assert [one.name for one in fields(Measured)] == [
        "distinct_counterparts",
        "times_on_court",
    ]
    assert [one.name for one in fields(Printed)] == [
        "distinct_opponents",
        "times_on_court",
    ]
