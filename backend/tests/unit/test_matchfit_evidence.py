"""The engine's evidence union, and the two claims that keep it honest.

**Every term emits from the closed union, and an unknown kind is a named gap
rather than silence.** Both halves are structural rather than a convention:
``kind`` is a class attribute on every variant, so evidence under a kind that is
not one of the eight cannot be constructed at all; and the union is exhaustive
over ``EvidenceKind``, which is also what the wire union is checked against in
the composition root. Two spellings of the same set of facts exist on purpose —
one computes and one publishes — and these are the checks standing between them.

The second half of the file is the **complement arm**, which is the one piece of
the tag arithmetic the constant table does not fully specify. ``strength · dr(n)``
is written for a single discount and the shipped matrix has rows at parity beside
rows at the default, so the two properties that pin the extension down are
asserted rather than described: it reduces to the documented form when the
strengths are uniform, and adding a row never subtracts.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.engines.matchfit.core import (
    EvidenceKind,
    SearchMode,
    Seat,
    TagColumn,
    TagRelationshipKind,
    Term,
)
from app.engines.matchfit.evidence import EVIDENCE_VARIANTS, PlayingStyleEvidence
from app.engines.matchfit.v1 import (
    diminishing,
    diminishing_at_strengths,
    playing_style,
)
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.presentation.evidence import WIRE_EVIDENCE_KINDS
from app.modules.player_profile.domain.social_tags import SocialTag
from tests.unit.matchfit_builders import candidate, searcher


def test_the_union_carries_one_variant_per_evidence_kind() -> None:
    """Exhaustive and no wider — a variant with no kind, or two claiming one, is
    a term the client can never draw and a term drawn under the wrong heading."""

    kinds = [variant.kind for variant in EVIDENCE_VARIANTS]
    assert len(kinds) == len(set(kinds)) == len(EvidenceKind)
    assert set(kinds) == set(EvidenceKind)


def test_every_term_has_a_variant_to_answer_under() -> None:
    """Eight terms, eight kinds, and the mapping is the enum's rather than a table."""

    assert {term.evidence_kind for term in Term} == set(EvidenceKind)


def test_the_engine_and_the_wire_publish_the_same_set_of_kinds() -> None:
    """The one check standing between the two serialisations.

    Storage stays open where the wire is closed, and the two are allowed to
    differ in *shape*. They may never differ in **membership**: an evidence kind
    the engine can emit and the schema does not publish renders as nothing at
    all, on the one screen whose entire promise is that it shows its working —
    where a missing reason line looks identical to a term that stood down.
    """

    assert {variant.kind for variant in EVIDENCE_VARIANTS} == WIRE_EVIDENCE_KINDS


def test_a_variants_kind_is_a_property_of_the_type_and_not_an_argument() -> None:
    """Which is what makes *an unknown kind* unconstructable rather than refused.

    A ``kind`` somebody passes in is a ``kind`` somebody can pass wrongly; a class
    attribute is one the type carries. So the union cannot grow a ninth member by
    accident — it grows by an edit to ``EvidenceKind``, which is an API release.
    """

    for variant in EVIDENCE_VARIANTS:
        assert "kind" not in {field.name for field in dataclasses.fields(variant)}
        with pytest.raises(TypeError):
            variant(kind=EvidenceKind.DISTANCE)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# The complement arm
# ---------------------------------------------------------------------------

PHI = LIVE_RULESET.tags.phi


@pytest.mark.parametrize("count", range(0, 7))
@pytest.mark.parametrize("strength", [0.5, 0.70, 1.00])
def test_the_complement_arm_reduces_to_the_documented_form_at_one_strength(
    count: int, strength: float
) -> None:
    """``strength · dr(n)``, exactly, whenever every row carries that strength.

    The extension exists because the shipped matrix does **not** carry one
    strength; the property that keeps it honest is that it changes nothing where
    the constant table's own formula applies.
    """

    assert diminishing_at_strengths([strength] * count, PHI) == pytest.approx(
        strength * diminishing(count, PHI)
    )


def test_a_further_complement_row_never_subtracts_from_the_arm() -> None:
    """Strongest first, which is what makes that true.

    Pair a weaker claim with a larger increment and a second complement could
    *lower* the score — a pairing punished for having one more thing in common,
    which is not a reading anybody could defend on a card.
    """

    rows: list[float] = []
    running = 0.0
    for strength in (0.70, 1.00, 0.70, 1.00, 0.85):
        rows.append(strength)
        total = diminishing_at_strengths(rows, PHI)
        assert total >= running
        running = total


def test_the_arm_is_read_in_strength_order_and_not_in_the_matrixs() -> None:
    """The order rows happen to be authored in must not move a score."""

    assert diminishing_at_strengths([0.70, 1.00], PHI) == pytest.approx(
        diminishing_at_strengths([1.00, 0.70], PHI)
    )


def test_a_complement_at_parity_is_worth_more_than_one_at_the_discount() -> None:
    """Parity is the most an editorial claim can be worth against two people's
    agreement, and the two rows that take it are supposed to be felt."""

    at_parity = diminishing_at_strengths([1.00], PHI)
    discounted = diminishing_at_strengths([LIVE_RULESET.tags.complement_strength], PHI)
    assert at_parity > discounted


def test_the_evidence_names_every_row_that_fired_in_the_matrixs_own_order() -> None:
    """Ids only, and in a stable order — the row's strength is a ruleset number
    the player is not shown, and what is owed is *which two things about you two
    this reads*."""

    both = (
        SocialTag.HERE_TO_IMPROVE.value,
        SocialTag.WARMS_UP_PROPERLY.value,
        SocialTag.PLAYS_TO_WIN.value,
    )
    reading = playing_style(
        searcher(tags=both, mode=SearchMode.COMPETITIVE),
        candidate(tags=both),
        Seat.OPPONENT,
        LIVE_RULESET.tags,
    )
    assert reading is not None
    assert isinstance(reading.evidence, PlayingStyleEvidence)
    pairs = [(pair.a, pair.b) for pair in reading.evidence.complementary]
    # Both sides hold all three ids, so every STYLE complement row over them
    # fires — and the list must read in the matrix's own order rather than in
    # whatever order a set happened to yield.
    assert pairs == [
        (row.a, row.b)
        for row in LIVE_RULESET.tags.relationship_matrix
        if row.kind is TagRelationshipKind.COMPLEMENT
        and row.column is TagColumn.STYLE
        and SearchMode.COMPETITIVE in row.modes
        and {row.a, row.b} <= set(both)
    ]
    assert len(pairs) == 2
