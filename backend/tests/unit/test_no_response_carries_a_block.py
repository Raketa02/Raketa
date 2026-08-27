"""No response shape on this API can carry a block. Asserted, not reviewed.

``docs/adr/0095`` §8 extends the existing rule — *a test asserts no response
shape can carry a decline* — to blocks: neither party is notified and the other
side sees no trace anywhere in any response. A rule like that is broken by
addition, months later, by somebody adding a helpful field to a candidate row,
and nothing about the diff would look wrong.

So the check walks the **emitted contract**, not the source: every schema
reachable from a *response* on the player surface, transitively, and no property
on any of them may name a block. The request shape is deliberately outside the
walk — ``BlockPlayerRequest`` is what a player *sends*, and it is reachable only
from a request body.
"""

from __future__ import annotations

import re

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router

#: Anything a client could read as *this person is blocked, or blocked you*.
FORBIDDEN = re.compile(r"block", re.IGNORECASE)


def _refs(node: object) -> set[str]:
    """Every ``$ref`` name anywhere under `node`."""

    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.add(value.rsplit("/", 1)[-1])
            else:
                found |= _refs(value)
    elif isinstance(node, list):
        for item in node:
            found |= _refs(item)
    return found


def _schemas_reachable_from_responses(spec: dict) -> dict[str, dict]:
    components = spec.get("components", {}).get("schemas", {})
    frontier = set()
    for path in spec["paths"].values():
        for operation in path.values():
            frontier |= _refs(operation.get("responses", {}))

    reached: dict[str, dict] = {}
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        schema = components.get(name, {})
        reached[name] = schema
        frontier |= _refs(schema) - set(reached)
    return reached


def _spec() -> dict:
    return build_surface_spec("Raketa Player API", player_api_router)


def test_the_walk_reaches_the_response_schemas_it_is_meant_to_check():
    """The guard on the guard: a walk that reached nothing would pass forever."""

    reached = _schemas_reachable_from_responses(_spec())

    assert "ErrorResponse" in reached
    assert len(reached) > 5


def test_no_response_schema_has_a_property_naming_a_block():
    offenders = {
        f"{name}.{field}"
        for name, schema in _schemas_reachable_from_responses(_spec()).items()
        for field in schema.get("properties", {})
        if FORBIDDEN.search(field)
    }

    assert offenders == set(), sorted(offenders)


def test_neither_block_route_returns_a_body():
    """204 and nothing else, on both — which is what makes *the same answer
    either way* a property of the contract rather than of one handler."""

    paths = _spec()["paths"]

    post = paths["/api/v1/blocks"]["post"]["responses"]
    delete = paths["/api/v1/blocks/{player_id}"]["delete"]["responses"]

    assert set(post) == {"204", "400", "409", "422"}
    assert set(delete) == {"204", "422"}
    assert "content" not in post["204"]
    assert "content" not in delete["204"]
