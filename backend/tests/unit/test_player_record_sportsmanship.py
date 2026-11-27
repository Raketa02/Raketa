"""What other players said, at the seam — one answer, and where it may reach.

``player_record`` declares its own types rather than reusing another context's
(``docs/adr/0159``), and this is the fourth time that costs a second spelling —
after ``OnCourtVerdict`` beside ``PhotoReviewDecision``, ``GameOutcome`` beside
``Outcome`` and the variety pair. The translation is a rename and nothing else,
and what is pinned is that it stays one: the two halves keep their places, and
neither shape grows a field the other would drop.

**The asymmetry this file used to hold is gone with the band** (``docs/adr/0179``
§5). The subject's own sheet used to be answered off a second method that could
not say the figure; it is answered off the same method as anybody's now, and the
adapter has one. What remains to pin about *where* the figure reaches is the
contract walk at the bottom: it names exactly one response type, and the band's
field is on none.
"""

from __future__ import annotations

import json
from uuid import UUID, uuid4

import pytest

from app.kernel import InvariantViolated
from app.modules.player_record.domain.record import WhatPlayersSaid
from app.modules.player_record.infrastructure.published_subject_sportsmanship import (
    PublishedSubjectSportsmanship,
)
from app.modules.sportsmanship.domain.published import PublishedSportsmanship

SUBJECT = uuid4()


class Published:
    """``sportsmanship``'s published fold, as a stub. **It records the ask.**"""

    def __init__(self, figure: PublishedSportsmanship | None = None) -> None:
        self.figure = figure
        self.asked_for_the_figure: list[UUID] = []

    async def published_for(self, subject_id: UUID) -> PublishedSportsmanship | None:
        self.asked_for_the_figure.append(subject_id)
        return self.figure


# ---------------------------------------------------------------------------
# The translation is a rename
# ---------------------------------------------------------------------------


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
# Absence
# ---------------------------------------------------------------------------


async def test_a_measured_nothing_stays_nothing():
    """**One spelling for absence, all the way out.** Nobody has been unpleasant
    who has never been on a court with anybody, and no layer between the fold and
    the response turns that into a nought on the way past."""

    published = Published()

    assert (
        await PublishedSubjectSportsmanship(published).what_players_said(SUBJECT)
        is None
    )


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
        build_surface_spec("Rakieta Player API", player_api_router)
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


def test_the_band_is_on_no_response_shape_in_the_emitted_document():
    """**Retired from the wire, asserted over the document** (``docs/adr/0179``
    §5). `sportsmanship_band` was the subject's three-step answer; it is gone
    from the record's shape and from the components a client generates from —
    a property under that name anywhere, or a schema for the enum it carried,
    would be the band shipping again under the drift check's nose.
    """

    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router

    document = build_surface_spec("Rakieta Player API", player_api_router)
    schemas = document["components"]["schemas"]
    assert schemas, "the walk found no schemas, so it would pass for ever"

    carrying = sorted(
        name
        for name, schema in schemas.items()
        if "sportsmanship_band" in (schema.get("properties") or {})
    )

    assert carrying == []
    assert "OpinionBand" not in schemas
    assert "sportsmanship_band" not in json.dumps(document)
