"""``GET /api/v1/player-profile/options`` — the facts a client must not hold.

The vocabulary's own invariants are unit-tested; this file is about the wire:
what a client actually receives, that it needs nothing to ask for it, and that
the contract document the client generates from carries the shapes.

The ids are written out here as well as in the unit test, deliberately. That
test guards the constant; this one guards the *response*, and a mapper that
dropped a group or re-sorted the tags would leave the constant untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]

OPTIONS_PATH = "/api/v1/player-profile/options"

EXPECTED_GROUPS: list[tuple[str, list[str]]] = [
    (
        "AFTER_THE_MATCH",
        [
            "STAYS_FOR_A_DRINK",
            "STRAIGHT_HOME_AFTER",
            "TALKS_THROUGH_THE_MATCH",
            "SETTLES_UP_ON_THE_SPOT",
            "BOOKS_THE_NEXT_ONE",
            "SHARES_A_LIFT",
        ],
    ),
    (
        "ON_THE_COURT",
        [
            "PLAYS_TO_WIN",
            "LAUGHS_OFF_MISTAKES",
            "ENCOURAGES_A_PARTNER",
            "GENEROUS_ON_LINE_CALLS",
            "QUIET_AND_FOCUSED",
            "WARMS_UP_PROPERLY",
        ],
    ),
    (
        "WHY_YOU_ARE_HERE",
        [
            "HERE_TO_IMPROVE",
            "HERE_TO_COMPETE",
            "HERE_FOR_THE_EXERCISE",
            "HERE_TO_MEET_PLAYERS",
            "HERE_FOR_A_REGULAR_GAME",
            "HERE_TO_GET_BACK_INTO_IT",
            "OPEN_TO_MEET_SOMEONE",
        ],
    ),
]


@pytest.mark.asyncio
async def test_the_vocabulary_is_served_grouped_and_in_order(client):
    resp = await client.get(OPTIONS_PATH)
    assert resp.status_code == 200, resp.text

    served = [
        (group["group"], [tag["id"] for tag in group["tags"]])
        for group in resp.json()["social_tag_groups"]
    ]
    assert served == EXPECTED_GROUPS


@pytest.mark.asyncio
async def test_nineteen_tags_are_served(client):
    resp = await client.get(OPTIONS_PATH)
    tags = [
        tag["id"] for group in resp.json()["social_tag_groups"] for tag in group["tags"]
    ]

    assert len(tags) == 19
    assert len(set(tags)) == 19


@pytest.mark.asyncio
async def test_the_search_radius_bounds_are_served_with_their_default(client):
    resp = await client.get(OPTIONS_PATH)
    assert resp.status_code == 200, resp.text

    assert resp.json()["search_radius"] == {
        "minimum_km": 1,
        "maximum_km": 50,
        "step_km": 1,
        "default_km": 10,
    }


@pytest.mark.asyncio
async def test_the_social_tag_floor_and_ceiling_are_served(client):
    # Written out rather than read from the constant: this guards the *wire*,
    # and a mapper that swapped the two would leave the constant untouched.
    resp = await client.get(OPTIONS_PATH)
    assert resp.status_code == 200, resp.text

    assert resp.json()["social_tag_selection"] == {
        "minimum_tags": 2,
        "maximum_tags": 6,
    }


@pytest.mark.asyncio
async def test_the_ceiling_is_reachable_from_what_is_served(client):
    # A ceiling above the vocabulary would be a counter that never fills.
    body = (await client.get(OPTIONS_PATH)).json()
    tags = [tag["id"] for group in body["social_tag_groups"] for tag in group["tags"]]

    assert body["social_tag_selection"]["maximum_tags"] <= len(tags)


@pytest.mark.asyncio
async def test_the_answer_needs_no_token_and_no_body(client):
    # Nothing here belongs to anybody, and the first step of the social part
    # renders from it — asking for a token would be asking for one twice.
    resp = await client.get(OPTIONS_PATH, headers={})

    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_the_answer_says_it_is_cacheable(client):
    # Left to a proxy's guess, a response with no freshness information is
    # revalidated on every launch — for a document that changes on a release.
    resp = await client.get(OPTIONS_PATH)

    cache_control = resp.headers["cache-control"]
    assert "public" in cache_control
    assert "max-age=" in cache_control


@pytest.mark.asyncio
async def test_two_reads_return_the_same_document(client):
    first = await client.get(OPTIONS_PATH)
    second = await client.get(OPTIONS_PATH)

    assert first.json() == second.json()


def test_the_committed_contract_carries_the_route_and_its_schemas():
    # The client generates its wire types from this file (docs/adr/0006), so a
    # route added without regenerating it is a route the client cannot call.
    committed = json.loads((BACKEND_ROOT / "openapi.player.json").read_text())

    operation = committed["paths"][OPTIONS_PATH]["get"]
    assert operation["responses"]["200"]

    schemas = committed["components"]["schemas"]
    for name in (
        "PlayerProfileOptionsResponse",
        "SocialTagGroupResource",
        "SocialTagResource",
        "SearchRadiusBoundsResource",
        "SocialTagSelectionBoundsResource",
        "SocialTag",
        "SocialTagGroup",
    ):
        assert name in schemas, f"{name} missing from the committed contract"

    assert set(schemas["SocialTag"]["enum"]) == {
        tag for _, tags in EXPECTED_GROUPS for tag in tags
    }
