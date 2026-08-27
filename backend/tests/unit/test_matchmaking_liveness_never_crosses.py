"""No Liveness number crosses the wire, asserted **centrally** and not per route.

``docs/adr/0106`` §5 makes it a schema fact rather than a rule about how a route
is written: *a candidate carries ``fit`` and a list of liveness reason codes, and
there is no field a Liveness offset could be written to.* A rule stated per route
is a rule the next route can be written without, so this walks the emitted
contract — every schema on the surface, however it got there — and refuses a
property that names one.

**It is deliberately green today, and that is the point.** No route reads the
matcher yet, so today it asserts the shape of the surface a future route will be
added to. It is written now because the field it guards against is one somebody
will add with a good reason: ranking is genuinely easier to debug when the number
is in the payload, and the ordering will be genuinely mysterious without it.

**What it does not forbid is as load-bearing as what it does.** ``liveness_reasons``
is exactly what the contract *will* carry. So the refusal is not the word
*liveness* — it is the word beside a **number**, and the two lists below are the
whole of the judgement. ``rank_key`` is refused outright, because the printed Fit
is the only number a player is asked to trust and ``rank_key`` is not it.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.api.contract import SURFACES, build_surface_spec

#: What a Liveness quantity would be called. Whole words of a property name, so
#: ``offset`` is caught beside ``points`` and neither is caught inside another
#: word by accident.
QUANTITIES = frozenset(
    {
        "offset",
        "points",
        "score",
        "value",
        "number",
        "delta",
        "adjustment",
        "weight",
        "boost",
        "lift",
        "dock",
    }
)

#: The names that carry a Liveness reading whatever they are paired with.
NEVER = frozenset({"rank_key", "rankkey", "livenessoffset", "ranking_key"})


def words(name: str) -> set[str]:
    """The identifier words in a property name, lowercased.

    Both spellings the contract could arrive in — a generated document may carry
    ``liveness_offset`` or ``livenessOffset`` depending on how somebody declares
    an alias — so camelCase is split as well as snake_case.
    """

    found: list[str] = []
    word: list[str] = []
    for character in name:
        if character.isalnum():
            if character.isupper() and word:
                found.append("".join(word))
                word = []
            word.append(character.lower())
        elif word:
            found.append("".join(word))
            word = []
    if word:
        found.append("".join(word))
    return set(found)


def properties(spec: dict[str, Any]) -> list[tuple[str, str]]:
    """Every ``(schema, property)`` the document declares, however nested.

    A walk over the whole document rather than over ``components.schemas``:
    FastAPI inlines some shapes, and a walk that read only the named components
    would report no breach on a surface whose offending field was inline.
    """

    found: list[tuple[str, str]] = []

    def walk(node: Any, owner: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    found.extend((owner, name) for name in value)
                walk(value, key if key not in {"properties", "items"} else owner)
        elif isinstance(node, list):
            for item in node:
                walk(item, owner)

    walk(spec, "")
    return found


def breaches(spec: dict[str, Any]) -> list[str]:
    """Every property on this surface that would carry a Liveness number."""

    offending = []
    for owner, name in properties(spec):
        parts = words(name)
        if (
            name.lower().replace("-", "_") in NEVER
            or "rank" in parts
            and "key" in parts
        ):
            offending.append(f"{owner}.{name} — a rank key never crosses")
        elif "liveness" in parts and parts & QUANTITIES:
            offending.append(f"{owner}.{name} — a Liveness number never crosses")
    return offending


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_no_response_type_on_any_surface_carries_a_liveness_number(
    surface: str,
) -> None:
    """The whole of ``docs/adr/0106`` §5, over the document the client generates
    from rather than over the routes somebody remembered to check."""

    assert breaches(build_surface_spec(surface, SURFACES[surface])) == []


def test_the_walk_reaches_the_properties_it_claims_to_guard() -> None:
    """The check that stops the one above passing for the wrong reason.

    A walk that reached nothing would report no breach on any document at all —
    and would go on reporting none the day the surface grew the field this
    guards against.
    """

    reached = properties(build_surface_spec("player", SURFACES["player"]))
    assert len(reached) > 50, "the walk found almost no properties: it is pointed wrong"
    assert any(name == "code" for _, name in reached), "the error envelope is missing"


@pytest.mark.parametrize(
    "field",
    ["rank_key", "rankKey", "liveness_offset", "livenessOffset", "liveness_points"],
)
def test_the_walk_refuses_the_field_it_exists_to_refuse(field: str) -> None:
    """Driven against a deliberately broken document, because a gate that has
    never been observed to fail is indistinguishable from one that does not
    work — and this one guards a field nobody will notice arriving."""

    broken = {"components": {"schemas": {"Candidate": {"properties": {field: {}}}}}}
    assert breaches(broken) != []


@pytest.mark.parametrize("field", ["liveness_reasons", "fit", "offset", "position"])
def test_the_walk_admits_what_the_contract_will_actually_carry(field: str) -> None:
    """The other half of the judgement, and the one a blunter check would fail.

    A candidate **does** carry liveness reason codes, and refusing the word
    *liveness* outright would refuse the contract this rule exists to protect.
    """

    fine = {"components": {"schemas": {"Candidate": {"properties": {field: {}}}}}}
    assert breaches(fine) == []
