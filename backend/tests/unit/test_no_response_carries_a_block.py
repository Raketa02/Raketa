"""A block crosses the wire in exactly one place, and only as the reader's own.

``docs/adr/0193`` §3 narrowed ADR-0095 §8's *a block is unrepresentable in a
response* to **a response may carry the reader's own blocks, never anyone's block
of the reader**. Since ``docs/adr/0203`` §8 (#773) **one read carries them**:

- **Blocked players** — ``GET /blocks``, the caller's own blocks.

The player record carried the other — ``blocked_by_you`` — until a block made
by either side became one of its gates: a blocked pair's record never opens, so
there is no sheet for the reader's own block to be drawn on, and the field left
the contract.

A rule like that is broken by addition, months later, by somebody adding a
helpful field to a card, and nothing about the diff would look wrong. So the
check walks the **emitted contract**, not the source: every schema reachable
from a *response* on the player surface, transitively. **The one allowed place
is named here, and every other one is forbidden** — a second is a red build,
not a review question. The request shape is outside the walk:
``BlockPlayerRequest`` is what a player *sends*.
"""

from __future__ import annotations

import re

from app.api.contract import build_surface_spec
from app.api.v1.player import player_api_router

#: Anything a client could read as *this person is blocked, or blocked you*.
FORBIDDEN = re.compile(r"block", re.IGNORECASE)

#: The *Blocked players* read's schemas, whole: everything on them is the
#: reader's own blocks.
BLOCKED_PLAYERS = frozenset({"BlockedPlayersResponse", "BlockedPlayerSchema"})


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


def _reachable(spec: dict, frontier: set[str]) -> dict[str, dict]:
    components = spec.get("components", {}).get("schemas", {})
    reached: dict[str, dict] = {}
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        schema = components.get(name, {})
        reached[name] = schema
        frontier |= _refs(schema) - set(reached)
    return reached


def _operations(spec: dict):
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            yield f"{method.upper()} {path}", operation


def _schemas_reachable_from_responses(spec: dict) -> dict[str, dict]:
    frontier: set[str] = set()
    for _, operation in _operations(spec):
        frontier |= _refs(operation.get("responses", {}))
    return _reachable(spec, frontier)


def _operations_reaching(spec: dict, schema: str) -> set[str]:
    return {
        name
        for name, operation in _operations(spec)
        if schema in _reachable(spec, _refs(operation.get("responses", {})))
    }


def _spec() -> dict:
    return build_surface_spec("Rakieta Player API", player_api_router)


def test_the_walk_reaches_the_response_schemas_it_is_meant_to_check():
    """The guard on the guard: a walk that reached nothing would pass forever,
    and one that no longer reached the allowed place, or the record, would be
    guarding a rule about nothing."""

    reached = _schemas_reachable_from_responses(_spec())

    assert "ErrorResponse" in reached
    assert len(reached) > 5
    assert BLOCKED_PLAYERS <= set(reached)
    assert "PlayerRecordResponse" in reached


def test_no_response_names_a_block_but_blocked_players():
    offenders = {
        f"{name}.{field}"
        for name, schema in _schemas_reachable_from_responses(_spec()).items()
        if name not in BLOCKED_PLAYERS
        for field in schema.get("properties", {})
        if FORBIDDEN.search(field)
    }
    named = {
        name
        for name in _schemas_reachable_from_responses(_spec())
        if FORBIDDEN.search(name) and name not in BLOCKED_PLAYERS
    }

    assert offenders == set(), sorted(offenders)
    assert named == set(), sorted(named)


def test_blocked_players_is_served_by_its_own_read_and_no_other():
    """The list is the caller's own, so it may hang off nothing but the route
    that reads it — a card or a row embedding it would be one more place a
    block crosses."""

    spec = _spec()

    for schema in BLOCKED_PLAYERS:
        assert _operations_reaching(spec, schema) == {"GET /api/v1/blocks"}


def test_the_record_carries_no_block_either_way():
    """``docs/adr/0203`` §8: a blocked pair's record never opens, so the sheet
    has nothing to say about a block — the reader's own included."""

    record = _schemas_reachable_from_responses(_spec())["PlayerRecordResponse"]

    assert not [field for field in record["properties"] if FORBIDDEN.search(field)]


def test_neither_block_write_returns_a_body():
    """204 and nothing else on making and lifting a block — which is what makes
    *the same answer either way* a property of the contract rather than of one
    handler."""

    paths = _spec()["paths"]

    post = paths["/api/v1/blocks"]["post"]["responses"]
    delete = paths["/api/v1/blocks/{player_id}"]["delete"]["responses"]

    assert set(post) == {"204", "400", "409", "422"}
    assert set(delete) == {"204", "422"}
    assert "content" not in post["204"]
    assert "content" not in delete["204"]
