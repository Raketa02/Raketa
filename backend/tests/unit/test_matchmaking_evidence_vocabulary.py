"""The evidence union: closed, discriminated, and checked against the ruleset.

``docs/adr/0106`` splits the matcher's serialisation in two — the store stays
open, the wire is closed — and puts **one check** between them. These are that
check and the properties it depends on.

The negative cases matter more than the positive ones here. A wire union that
silently stopped being exhaustive would fail in production as a **blank line on
a card**, on the one screen whose whole promise is that it shows its working, and
it would look identical to a term that stood down.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType, NoneType
from typing import Union, get_args, get_origin

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.bootstrap.matchmaking import verify_ruleset
from app.engines.matchfit.core import EvidenceKind, Term
from app.engines.matchfit.ruleset import Ruleset, validate_ruleset
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.presentation.evidence import (
    EVIDENCE_VARIANTS,
    WIRE_EVIDENCE_KINDS,
    AvailabilityOverlapEvidence,
    Evidence,
    PlayingStyleEvidence,
    ReliabilityEvidence,
    SocialVibeEvidence,
)
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagGroup,
)

_EVIDENCE = TypeAdapter(Evidence)


# ---------------------------------------------------------------------------
# The union is closed and keyed by kind


def test_every_variant_is_keyed_by_a_kind_from_the_engines_own_enum() -> None:
    """One vocabulary, not two. The engine decides which kind a term emits; the
    schema decides what that kind's payload looks like. A second spelling of the
    discriminator is how the two halves begin disagreeing about the same word."""

    assert WIRE_EVIDENCE_KINDS <= set(EvidenceKind)
    assert len(EVIDENCE_VARIANTS) == len(WIRE_EVIDENCE_KINDS)


def test_the_union_publishes_a_variant_for_every_term() -> None:
    assert WIRE_EVIDENCE_KINDS == {term.evidence_kind for term in Term}


def test_an_unknown_kind_is_refused_rather_than_parsed_loosely() -> None:
    """This is what *closed* buys. An open blob would generate into TypeScript as
    ``Record<string, unknown>`` and the client would hand-write the types after
    all — ``docs/adr/0006``'s exact failure, through a hole in the schema."""

    with pytest.raises(ValidationError):
        _EVIDENCE.validate_python({"kind": "vibes", "shared_count": 4})


def test_a_variant_round_trips_under_its_own_kind() -> None:
    parsed = _EVIDENCE.validate_python(
        {
            "kind": "availability_overlap",
            "shared_count": 4,
            "next_slot": {"day": 2, "part": "EVENING"},
        }
    )
    assert isinstance(parsed, AvailabilityOverlapEvidence)
    assert parsed.shared_count == 4


# ---------------------------------------------------------------------------
# Absence has two spellings


def test_a_measured_nothing_is_required_and_nullable() -> None:
    """Both grids were read and there is no next shared slot. That is a recorded
    fact, not an inapplicable field, and it generates as ``next_slot: T | null``
    so the client is forced to render it as one."""

    parsed = _EVIDENCE.validate_python(
        {"kind": "availability_overlap", "shared_count": 0, "next_slot": None}
    )
    assert isinstance(parsed, AvailabilityOverlapEvidence)
    assert parsed.next_slot is None

    schema = AvailabilityOverlapEvidence.model_json_schema()
    assert "next_slot" in schema["required"]

    with pytest.raises(ValidationError):
        # Omitting it would say *this does not apply*, which is a different and
        # untrue claim about a pair whose grids were both read.
        _EVIDENCE.validate_python({"kind": "availability_overlap", "shared_count": 0})


@pytest.mark.parametrize("variant", EVIDENCE_VARIANTS, ids=lambda v: v.__name__)
def test_no_field_is_both_optional_and_nullable(variant: type[BaseModel]) -> None:
    """The two spellings must not collapse into a third that says neither.

    *Omitted* generates as ``field?: T`` and *null* as ``field: T | null``.
    A field that is both generates as ``field?: T | null``, and a client reading
    it cannot tell *this does not apply* from *we looked and found nothing* —
    which is the distinction ``docs/adr/0106`` §4 exists to keep.
    """

    for name, field in variant.model_fields.items():
        nullable = get_origin(field.annotation) is Union and NoneType in get_args(
            field.annotation
        )
        assert not (nullable and not field.is_required()), (
            f"{variant.__name__}.{name} is both optional and nullable"
        )


# ---------------------------------------------------------------------------
# The ruleset is checked against the union


def test_the_live_ruleset_emits_only_kinds_this_contract_publishes() -> None:
    assert verify_ruleset(LIVE_RULESET) is LIVE_RULESET


def test_a_ruleset_emitting_an_unpublished_kind_refuses_to_load(monkeypatch) -> None:
    """The guard, driven against a contract that has lost a variant.

    Shrinking the union rather than growing the ruleset is the same failure from
    the other side and the one that actually happens: a variant is removed or
    renamed in an API change, and the ruleset that still scores that term goes on
    emitting it.
    """

    monkeypatch.setattr(
        "app.bootstrap.matchmaking.WIRE_EVIDENCE_KINDS",
        WIRE_EVIDENCE_KINDS - {EvidenceKind.SOCIAL_VIBE},
    )
    with pytest.raises(InvariantViolated, match="does not publish"):
        verify_ruleset(LIVE_RULESET)


def test_a_term_weighted_at_nothing_may_lose_its_variant(monkeypatch) -> None:
    """The check reads what the ruleset **can emit**, not what it declares.

    A term nothing weights never scores, so its variant may leave the contract
    without the ruleset becoming malformed — which is what makes this a check on
    behaviour rather than on a list somebody maintains by hand.
    """

    modes = {}
    for mode, rules in LIVE_RULESET.modes.items():
        weights = dict(rules.weights)
        weights[Term.INTENT_ALIGNMENT] += weights[Term.SOCIAL_VIBE]
        weights[Term.SOCIAL_VIBE] = 0
        modes[mode] = dataclasses.replace(rules, weights=MappingProxyType(weights))
    without_vibe = validate_ruleset(
        dataclasses.replace(LIVE_RULESET, modes=MappingProxyType(modes))
    )

    monkeypatch.setattr(
        "app.bootstrap.matchmaking.WIRE_EVIDENCE_KINDS",
        WIRE_EVIDENCE_KINDS - {EvidenceKind.SOCIAL_VIBE},
    )
    assert verify_ruleset(without_vibe) is without_vibe


# ---------------------------------------------------------------------------
# The ruleset is checked against the platform's tag vocabulary


def test_the_matrix_names_only_tags_this_platform_serves() -> None:
    """A typo'd id is a row that can never fire, and a relationship that silently
    never fires is indistinguishable from one product decided against."""

    served = {tag.value for tag in SocialTag}
    named = {
        tag for row in LIVE_RULESET.tags.relationship_matrix for tag in (row.a, row.b)
    }
    assert named <= served


def test_a_ruleset_naming_an_unserved_tag_id_refuses_to_load() -> None:
    unknown = dict(LIVE_RULESET.tags.familiarity_reading_map)
    unknown["HERE_FOR_THE_BEER"] = next(iter(unknown.values()))
    with pytest.raises(InvariantViolated, match="does not serve"):
        verify_ruleset(_reading(unknown))


def test_the_familiarity_map_is_exhaustive_over_why_you_are_here() -> None:
    """An id missing from it falls to the default lean and reads as *this player
    has no preference about repetition* — a claim about them rather than a gap in
    a table."""

    expected = {
        tag.value for tag in SOCIAL_TAG_VOCABULARY[SocialTagGroup.WHY_YOU_ARE_HERE]
    }
    assert set(LIVE_RULESET.tags.familiarity_reading_map) == expected


def test_a_familiarity_map_missing_an_id_refuses_to_load() -> None:
    short = dict(LIVE_RULESET.tags.familiarity_reading_map)
    short.pop(SocialTag.HERE_TO_COMPETE.value)
    with pytest.raises(InvariantViolated, match="not exhaustive"):
        verify_ruleset(_reading(short))


def test_a_familiarity_map_reading_a_tag_from_another_group_refuses_to_load() -> None:
    """Familiarity reads *why you are here*, and a tag about the hour on court is
    not that."""

    wide = dict(LIVE_RULESET.tags.familiarity_reading_map)
    wide[SocialTag.PLAYS_TO_WIN.value] = next(iter(wide.values()))
    with pytest.raises(InvariantViolated, match="not exhaustive"):
        verify_ruleset(_reading(wide))


@pytest.mark.parametrize(
    ("variant", "field"),
    [
        (ReliabilityEvidence, "strands"),
        (PlayingStyleEvidence, "matched"),
        (PlayingStyleEvidence, "complementary"),
        (PlayingStyleEvidence, "clashing"),
        (SocialVibeEvidence, "matched"),
        (SocialVibeEvidence, "complementary"),
        (SocialVibeEvidence, "clashing"),
    ],
    ids=lambda value: value if isinstance(value, str) else value.__name__,
)
def test_an_empty_set_is_a_measurement_and_so_is_required(
    variant: type[BaseModel], field: str
) -> None:
    """These are the fields most likely to drift to the wrong spelling.

    An empty ``matched`` is *we looked at both tag sets and nothing fired* —
    ``different, not incompatible``, which is the term's own measured zero. A
    column that genuinely **does not apply** stands down, and then the whole
    variant is absent rather than present and empty. Defaulted to ``()`` they
    would generate as ``field?: T[]`` and tell the client the opposite.
    """

    assert variant.model_fields[field].is_required()


def _reading(map_: dict[str, object]) -> Ruleset:
    """The live ruleset with a different familiarity reading map.

    Extracted because the nested ``dataclasses.replace`` is three levels deep and
    was repeated at every call site, where the only thing that differed — the map
    — was the least visible part of it.
    """

    return dataclasses.replace(
        LIVE_RULESET,
        tags=dataclasses.replace(
            LIVE_RULESET.tags, familiarity_reading_map=MappingProxyType(map_)
        ),
    )
