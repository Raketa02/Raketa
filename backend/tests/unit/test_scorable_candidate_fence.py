"""The privacy fence, walked rather than reviewed.

*A term cannot read a protected characteristic because the value is not in the
process.* That sentence is the whole argument for putting the scorer behind a
package boundary, and it is **either literally true or it is decoration** — so it
is checked by walking the source of ``app/engines/matchfit/v1/scorable.py``
rather than by reading it.

**Transitively**, and that is the half a review misses. A ``ScorableCandidate``
with no ``gender`` field but a ``profile: PlayerProfile`` field would satisfy
every eyeball and none of the rule, so the walk follows every annotation into the
type it names and refuses a forbidden word anywhere it can be reached from.

**Parsing rather than importing**, for the reason the kernel's purity walk parses:
a check that has to import the module can only ever see what a runtime type
exposes, where the fence is a claim about what somebody may *write*.

The gate is driven against a deliberately broken source below, because a gate
that has never been observed to fail is indistinguishable from one that does not
work — and this one guards a rule nobody will notice breaking.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.engines.matchfit import scorable

#: The fenced module itself, located **through the module rather than by this
#: file's own depth**. A path counted in ``..``s goes silently wrong the day the
#: tests move or the scorer does, and a walk pointed at nothing reports no breach
#: on any tree at all — which is indistinguishable from a fence that holds.
FENCED = Path(scorable.__file__)

#: The types the fence is a fence around. Both halves of a comparison cross it,
#: so the searcher is walked beside the candidate: a rule that let the searcher
#: carry a birthdate would be a rule about who may be *read*, not about what is
#: in the process.
FENCED_TYPES = ("ScorableCandidate", "Searcher")

#: What may never be reachable from a fenced type, as whole words of an
#: identifier. Words rather than substrings, so ``area_code`` is not read as
#: *code for an area* by accident — and ``nickname`` is caught by ``name`` below
#: because a name is what it is.
FORBIDDEN_WORDS = frozenset(
    {
        "gender",
        "name",
        "nickname",
        "photo",
        "photos",
        "avatar",
        "image",
        "birthdate",
        "birthday",
        "birth",
        "dob",
        "age",
        "email",
        "phone",
        "nationality",
        "latitude",
        "longitude",
        "lat",
        "lng",
        "lon",
        "coordinates",
        "centroid",
        "postcode",
        "address",
        "shard",
        "shard_key",
    }
)


def _classes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }


def _fields(node: ast.ClassDef) -> list[tuple[str, str]]:
    """Every annotated field on a class, as ``(name, the annotation's source)``."""

    return [
        (statement.target.id, ast.unparse(statement.annotation))
        for statement in node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    ]


def _words(text: str) -> set[str]:
    """The identifier words in a fragment of source, lowercased.

    An annotation is unparsed back to source and split the same way a field name
    is, so ``location: PreciseLocation`` is refused on the type's name even
    before the walk reaches inside it.
    """

    word = []
    words = set()
    for character in text:
        if character.isalnum():
            word.append(character.lower())
        else:
            if word:
                words.add("".join(word))
            word = []
        if character.isupper() and word[:-1]:
            words.add("".join(word[:-1]))
            word = [character.lower()]
    if word:
        words.add("".join(word))
    return words


def reachable_fields(source: str, roots: tuple[str, ...]) -> list[tuple[str, str, str]]:
    """Every ``(class, field, annotation)`` reachable from ``roots``.

    A breadth-first walk over the annotations, following any name that is itself
    a class in this module. Anything else — a builtin, a kernel brand, an
    enum from ``core`` — is a leaf, and it is the *word* in its name that the
    check reads.
    """

    classes = _classes(ast.parse(source))
    seen: set[str] = set()
    queue = [name for name in roots if name in classes]
    found: list[tuple[str, str, str]] = []
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for field, annotation in _fields(classes[name]):
            found.append((name, field, annotation))
            queue.extend(
                node.id
                for node in ast.walk(ast.parse(annotation, mode="eval"))
                if isinstance(node, ast.Name) and node.id in classes
            )
    return found


def breaches(source: str, roots: tuple[str, ...] = FENCED_TYPES) -> list[str]:
    """Every field reachable from a fenced type naming something it may not."""

    return [
        f"{owner}.{field}: {annotation} — names {sorted(offending)}"
        for owner, field, annotation in reachable_fields(source, roots)
        if (offending := (_words(field) | _words(annotation)) & FORBIDDEN_WORDS)
    ]


def test_the_fenced_types_carry_no_protected_characteristic() -> None:
    """No gender, no name, no photo, no birthdate, no precise location, no shard key.

    The whole of ``docs/adr/0093``'s privacy claim, and ``docs/adr/0096``'s: gender
    reaches candidate generation and the mutual gate and stops at this line, so a
    term cannot weigh it, and a mutual gate's delta cannot be read off a score.
    """

    assert breaches(FENCED.read_text(encoding="utf-8")) == []


def test_the_walk_reaches_the_fields_it_claims_to_guard() -> None:
    """The check that stops the one above passing for the wrong reason.

    A walk that reached nothing would report no breach on any tree at all — and
    would go on reporting none the day somebody renamed the type. So the real
    source is asserted to reach both roots, the types they hold, and the field
    two hops in that a shallow walk would miss.
    """

    reached = {
        f"{owner}.{field}"
        for owner, field, _ in reachable_fields(
            FENCED.read_text(encoding="utf-8"), FENCED_TYPES
        )
    }
    assert {
        "ScorableCandidate.player_id",
        "ScorableCandidate.area_code",
        "ScorableCandidate.reliability",
        "Searcher.grid",
        # One hop in: the Level is its own type on both sides of the pairing.
        "LevelReading.mu",
        # Two hops in, through `reliability` and into the record's own strands.
        "ReliabilityRecord.published_score",
        "GridCell.part",
    } <= reached


def test_the_walk_reaches_a_forbidden_field_declared_directly() -> None:
    """The obvious break: somebody adds the field to the candidate itself."""

    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class ScorableCandidate:
    player_id: str
    gender: str
"""
    assert breaches(broken) == ["ScorableCandidate.gender: str — names ['gender']"]


def test_the_walk_reaches_a_forbidden_field_through_another_type() -> None:
    """The break a review misses, and the reason the walk is transitive.

    Nothing on ``ScorableCandidate`` names a protected characteristic here. A
    field two hops away does, and it is in the process exactly as completely.
    """

    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class Area:
    code: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Where:
    area: Area


@dataclass(frozen=True)
class ScorableCandidate:
    player_id: str
    where: Where
"""
    assert breaches(broken) == [
        "Area.latitude: float — names ['latitude']",
        "Area.longitude: float — names ['longitude']",
    ]


def test_the_walk_reads_a_type_name_as_well_as_a_field_name() -> None:
    """A field spelled innocently, annotated with what it actually is."""

    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class ScorableCandidate:
    player_id: str
    declared: Gender | None
"""
    assert breaches(broken) == [
        "ScorableCandidate.declared: Gender | None — names ['gender']"
    ]


@pytest.mark.parametrize(
    "field",
    ["area_code", "player_id", "distance_km", "day_parts", "radius_km"],
)
def test_the_walk_does_not_refuse_what_the_scorer_legitimately_reads(
    field: str,
) -> None:
    """A guard that refuses the coarse area would be a guard somebody deletes.

    The area **is** a location fact and it is the coarse one — the finest that
    has ever crossed this line, and what the distance term's evidence is drawn
    from. Naming it here is what stops the forbidden list being read as *no
    location word at all*.
    """

    broken = f"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScorableCandidate:
    {field}: str
"""
    assert breaches(broken) == []
