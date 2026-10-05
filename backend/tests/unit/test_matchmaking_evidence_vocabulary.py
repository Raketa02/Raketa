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
import json
from pathlib import Path
from types import MappingProxyType, NoneType
from typing import Union, get_args, get_origin

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router
from app.bootstrap.matchmaking import verify_ruleset
from app.engines.matchfit.core import EvidenceKind, SearchMode, Term
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
from app.modules.player_profile.domain.play_intent import PlayIntent
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
            "next_slot": {"day": 2, "hour": 19},
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


def test_the_intent_table_prices_every_declaration_this_platform_serves() -> None:
    """Exhaustive in both directions, because the two failures differ.

    A cell keyed on a string nobody declares can never be read; a declaration
    with no cell stands the term down and renormalises it away — for a player who
    answered the question, which is the one case a stand-down must never mean.
    """

    declared = {intent.value for intent in PlayIntent}
    for row in LIVE_RULESET.intent.alignment.values():
        assert set(row) == declared


def test_a_ruleset_missing_a_declaration_refuses_to_load() -> None:
    thinned = dict(LIVE_RULESET.intent.alignment[SearchMode.FOR_FUN])
    thinned.pop(PlayIntent.NO_PREFERENCE.value)
    with pytest.raises(InvariantViolated, match="does not price every Play intent"):
        verify_ruleset(_intent_row(SearchMode.FOR_FUN, thinned))


def test_a_ruleset_pricing_a_declaration_nobody_can_make_refuses_to_load() -> None:
    invented = dict(LIVE_RULESET.intent.alignment[SearchMode.COMPETITIVE])
    invented["HERE_FOR_THE_BEER"] = 0.5
    with pytest.raises(InvariantViolated, match="does not price every Play intent"):
        verify_ruleset(_intent_row(SearchMode.COMPETITIVE, invented))


def _intent_row(mode: SearchMode, row: dict[str, float]) -> Ruleset:
    alignment = dict(LIVE_RULESET.intent.alignment)
    alignment[mode] = MappingProxyType(row)
    return dataclasses.replace(
        LIVE_RULESET,
        intent=dataclasses.replace(
            LIVE_RULESET.intent, alignment=MappingProxyType(alignment)
        ),
    )


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


# ---------------------------------------------------------------------------
# The third roster: the union against the contract document
#
# `docs/adr/0106`'s friction only exists if it is felt. **Adding or reshaping a
# variant is an API release**, and the release is three artifacts deep: the
# enum, this union, and `openapi.player.json` — from which the client generates
# an exhaustive renderer per variant (`.github/scripts/check-contract-drift.sh`).
#
# Nothing regenerates the contract document from the code, so without this the
# middle link is missing: a reshaped variant leaves a stale document, the drift
# check compares that stale document against types generated from it, and the
# build stays green with the client drawing the old shape. This is the link, and
# it is a roster test because a table titled *every constant* has already quietly
# gained and lost a row on this map.
# ---------------------------------------------------------------------------

CONTRACT = (
    Path(__file__).resolve().parents[2] / "openapi.player.json"
)


VARIANT_NAMES = frozenset(variant.__name__ for variant in EVIDENCE_VARIANTS)


def _closure(schemas: dict, roots: frozenset[str]) -> dict[str, object]:
    """The variants **and everything they are made of**, by following ``$ref``.

    Scoped to the eight and their closure rather than to the whole document, so
    an unrelated schema moving is not reported as evidence drift — and *not* to
    the eight alone, because ``TagPair`` and ``SharedSlot`` are referenced
    shapes: comparing only the top-level variants would call a reshaped
    ``TagPair`` no change at all, which is exactly the silent failure this
    exists to refuse.
    """

    wanted: dict[str, object] = {}
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in wanted or name not in schemas:
            continue
        schema = schemas[name]
        wanted[name] = schema
        pending.extend(_refs(schema))
    return wanted


def _refs(node: object) -> list[str]:
    """Every ``#/components/schemas/X`` this subtree names."""

    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.append(value.rsplit("/", 1)[-1])
            else:
                found.extend(_refs(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_refs(item))
    return found


def _published_schemas() -> dict[str, object]:
    """Every evidence variant as the **committed contract** publishes it."""

    document = json.loads(CONTRACT.read_text())
    return _closure(document["components"]["schemas"], VARIANT_NAMES)


def _live_schemas() -> dict[str, object]:
    """The same variants as the **code** would emit them, right now."""

    built = build_surface_spec("Raketa Player API", player_api_router)
    return _closure(built["components"]["schemas"], VARIANT_NAMES)


def test_the_contract_document_publishes_every_kind_the_union_holds() -> None:
    """One schema per variant, in the document the client reads.

    A variant that reaches no route publishes no schema, and the client then
    generates a union it can never be handed — which is the failure this asserts
    against in the direction nobody watches.
    """

    published = _published_schemas()
    assert VARIANT_NAMES <= set(published)
    assert len(VARIANT_NAMES) == len(EvidenceKind)


def test_a_reshaped_variant_leaves_the_contract_document_stale() -> None:
    """The committed contract reproduces from the code, variant for variant.

    This is the link that makes the drift check cover the evidence union.
    Regenerating is ``make gen-api`` at the repository root, and committing the
    document without the client types is what the drift check then refuses.
    """

    assert _published_schemas() == _live_schemas(), (
        "openapi.player.json no longer matches the evidence union this code "
        "emits. Run 'make gen-api' at the repository root and commit both the "
        "contract and the regenerated client types."
    )
