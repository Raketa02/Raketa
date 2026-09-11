"""What other players said, at the seam — and the one answer that must not cross.

``player_record`` declares its own types rather than reusing another context's
(``docs/adr/0159``), and this is the fourth time that costs a second spelling —
after ``OnCourtVerdict`` beside ``PhotoReviewDecision``, ``GameOutcome`` beside
``Outcome`` and the variety pair. Here the words **do** agree, so what is pinned
is that they keep agreeing: a band renamed on one side and not the other would
hand a client one word for a record and another for the same record next
release, and nothing would go red.

**The rest of this file is about the asymmetry**, which is the part no type
system holds. The subject's answer is folded from the same window as the
reader's, and it must arrive carrying **neither** the figure nor the count — a
published average beside a published count in front of the person it is about is
a subtraction that names each new rating exactly, and they know who they played
(``docs/adr/0158``). The adapter is the last place that could go wrong quietly:
a ``band_for`` written as *fetch the figure, coarsen it, drop the rest* would
satisfy every protocol here and would have had the figure in hand.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.kernel import InvariantViolated
from app.modules.player_record.domain.record import (
    OpinionBand as Printed,
)
from app.modules.player_record.domain.record import (
    WhatPlayersSaid,
)
from app.modules.player_record.infrastructure.published_subject_sportsmanship import (
    PublishedSubjectSportsmanship,
)
from app.modules.sportsmanship.domain.published import (
    PublishedSportsmanship,
)
from app.modules.sportsmanship.domain.published import (
    SportsmanshipBand as Measured,
)

SUBJECT = uuid4()


class Published:
    """``sportsmanship``'s published fold, as a stub. **It records both asks.**"""

    def __init__(
        self,
        figure: PublishedSportsmanship | None = None,
        band: Measured | None = None,
    ) -> None:
        self.figure = figure
        self.band = band
        self.asked_for_the_figure: list[UUID] = []
        self.asked_for_the_band: list[UUID] = []

    async def published_for(self, subject_id: UUID) -> PublishedSportsmanship | None:
        self.asked_for_the_figure.append(subject_id)
        return self.figure

    async def band_for(self, subject_id: UUID) -> Measured | None:
        self.asked_for_the_band.append(subject_id)
        return self.band


# ---------------------------------------------------------------------------
# The two vocabularies keep agreeing
# ---------------------------------------------------------------------------


def test_the_two_spellings_of_the_band_name_the_same_three_steps():
    """A second spelling that drifts is worse than an import: a client reading a
    record would be told one word this release and another the next, and the
    build would stay green through it."""

    assert {one.value for one in Printed} == {one.value for one in Measured}


async def test_the_figure_and_its_count_keep_their_places_across_the_seam():
    """Both halves are numbers, so a mapping that swapped them would type-check,
    satisfy both protocols, and publish *seventeen out of five, over 4,7
    people*. The two are chosen to be different from each other on purpose."""

    published = Published(PublishedSportsmanship(average=4.7, raters=17))

    said = await PublishedSubjectSportsmanship(published).what_players_said(SUBJECT)

    assert said == WhatPlayersSaid(average=4.7, raters=17)
    assert published.asked_for_the_figure == [SUBJECT]


def test_neither_shape_has_grown_a_field_the_other_would_drop():
    """The translation is total. A third number on either side is a decision
    somebody makes here rather than one that silently stops crossing."""

    from dataclasses import fields

    assert [one.name for one in fields(PublishedSportsmanship)] == [
        one.name for one in fields(WhatPlayersSaid)
    ]


# ---------------------------------------------------------------------------
# What the subject is told, and what they are not
# ---------------------------------------------------------------------------


async def test_the_subjects_band_is_read_through_the_method_that_has_no_figure():
    """**The rule this file exists for.** Coarsening the figure here would
    satisfy the protocol and would mean this process had held an average and a
    count about somebody, one line away from a sheet titled *How others see
    you*. So the band comes off its own method, and the figure's is never
    called."""

    published = Published(
        PublishedSportsmanship(average=4.7, raters=17), band=Measured.GOOD
    )

    band = await PublishedSubjectSportsmanship(published).band_for(SUBJECT)

    assert band is Printed.GOOD
    assert published.asked_for_the_band == [SUBJECT]
    assert published.asked_for_the_figure == []


async def test_a_reader_is_never_answered_off_the_subjects_method():
    """The mirror of the rule above, and it is worth pinning: a figure derived
    from a band would be three values wearing a decimal point."""

    published = Published(PublishedSportsmanship(average=2.5, raters=4))

    await PublishedSubjectSportsmanship(published).what_players_said(SUBJECT)

    assert published.asked_for_the_figure == [SUBJECT]
    assert published.asked_for_the_band == []


# ---------------------------------------------------------------------------
# Absence
# ---------------------------------------------------------------------------


async def test_a_measured_nothing_stays_nothing_on_both_methods():
    """**One spelling for absence, all the way out.** Nobody has been unpleasant
    who has never been on a court with anybody, and no layer between the fold and
    the response turns that into a nought or a bottom band on the way past."""

    published = Published()
    adapter = PublishedSubjectSportsmanship(published)

    assert await adapter.what_players_said(SUBJECT) is None
    assert await adapter.band_for(SUBJECT) is None


def test_a_figure_over_nobody_is_refused_rather_than_drawn():
    """The absence is a ``None``, never a row with a nought in it — asserted at
    the type, because an adapter that constructed one would be publishing a
    verdict nobody gave."""

    with pytest.raises(InvariantViolated):
        WhatPlayersSaid(average=4.0, raters=0)


# ---------------------------------------------------------------------------
# It reaches the record and no card
# ---------------------------------------------------------------------------


def test_no_search_result_card_carries_what_players_said():
    """**Not on a card, and this is where that decision is checked.**

    A card is built for twenty people at once and frozen into a search record
    kept for ever (``docs/adr/0107``), and this figure must be current — a
    recorded one would be a human opinion about somebody, drawn to twenty
    strangers who never asked for it, at whatever value it held in August. The
    import contract beside this refuses the matcher the *engine* path; nothing
    would stop a helpful field on a card, in a diff where nothing looks wrong.

    So the claim is made over the emitted contract rather than over a class:
    the words reach exactly one response type on the whole player surface.
    """

    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router
    from tests.unit.test_no_response_carries_a_forbidden_fact import (
        schemas_reachable_from_responses,
    )

    schemas = schemas_reachable_from_responses(
        build_surface_spec("Raketa Player API", player_api_router)
    )
    assert schemas, "the walk found no schemas, so it would pass for ever"

    naming = sorted(
        name
        for name, schema in schemas.items()
        if any(
            "sportsmanship" in field.lower()
            for field in (schema.get("properties") or {})
        )
    )

    assert naming == ["PlayerRecordResponse"]
