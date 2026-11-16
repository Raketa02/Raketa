"""The seeded *Same vibe players*, read back the way the player app reads it
(#795; the home-rows mechanics §8, §20).

``app/seeds/same_vibe.py`` writes no player: her six tags meet the cohort's at
every count from one to six. It writes a request each way from the row, and on
a store seeded before her six it gives her them through *Edit tags*' own use
case. Each claim is read by signing in as her, or as the player she asked;
*a second run changes nothing* counts the stored events.

The world is the runner's named accounts and the real cohort, as ``make seed``
writes them; one friendship stands in for the friends layer, which
``assert_same_vibe`` asks for among her good matches.
"""

from __future__ import annotations

import re

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.infrastructure.events.event_store_model import EventStoreORM
from app.seeds.catalog import (
    HER_TAGS,
    PROTAGONIST_TAGS,
    SEED_PASSWORD,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
)
from app.seeds.clock import FixedClock
from app.seeds.cohort import COHORT
from app.seeds.runner import seed, seed_the_cohort
from app.seeds.same_vibe import (
    ASKS_HER,
    SHE_ASKS,
    assert_same_vibe,
    write_same_vibe,
)
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

ROW = "/api/v1/same-vibe"
ALL = "/api/v1/same-vibe/all"


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def world(session_factory, now):
    photos = InMemoryPhotoStorage()
    async with session_factory() as session:
        await seed(
            session, clock=FixedClock(at=now), settings=get_settings(), photos=photos
        )
        await seed_the_cohort(
            session, clock=FixedClock(at=now), settings=get_settings(), photos=photos
        )


async def signed_in(client, email: str) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def stored_events(session_factory) -> int:
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(EventStoreORM))


async def everyone(client, her: dict) -> list[dict]:
    cards: list[dict] = []
    after = None
    while True:
        page = (
            await client.get(
                ALL, params={} if after is None else {"after": after}, headers=her
            )
        ).json()
        cards += page["players"]
        if (after := page["next"]) is None:
            return cards


async def her_friend(client) -> None:
    """One friend, as the friends layer makes several: she shares three tags
    with every other protagonist."""

    friend = await signed_in(client, THE_ONE_SPORT_PLAYER.email)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    me = (await client.get("/api/v1/users/me", headers=her)).json()["id"]
    them = (await client.get("/api/v1/users/me", headers=friend)).json()["id"]
    asked = await client.post(
        "/api/v1/friends/requests",
        json={"player_id": them, "made_from": "RECORD"},
        headers=her,
    )
    assert asked.status_code == 200, asked.text
    accepted = await client.post(
        f"/api/v1/friends/requests/{me}/acceptance", headers=friend
    )
    assert accepted.status_code == 200, accepted.text


async def test_her_six_tags_meet_somebody_at_every_count(
    client, session_factory, now, world
):
    await write_same_vibe(session_factory, now=now)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)

    cards = await everyone(client, her)
    row = (await client.get(ROW, headers=her)).json()["players"]

    assert {card["in_common"] for card in cards} == {1, 2, 3, 4, 5, 6}
    assert len(row) == 10
    assert {card["player_id"] for card in row} <= {card["player_id"] for card in cards}


async def test_a_request_each_way_from_the_row(client, session_factory, now, world):
    seeded = await write_same_vibe(session_factory, now=now)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    asked = await signed_in(client, COHORT.by_handle(SHE_ASKS).email)

    relations = {
        card["player_id"]: card["relation"] for card in await everyone(client, her)
    }
    [theirs] = (await client.get("/api/v1/home", headers=asked)).json()[
        "friend_requests"
    ]
    mine = {
        request["player_id"]: request
        for request in (await client.get("/api/v1/home", headers=her)).json()[
            "friend_requests"
        ]
    }

    assert seeded.created
    assert relations[str(seeded.she_asked)] == "SENT"
    assert relations[str(seeded.asked_her)] == "ASKED_YOU"
    assert (theirs["from_same_vibe"], theirs["in_common"]) == (True, 5)
    assert mine[str(seeded.asked_her)]["from_same_vibe"] is True
    assert mine[str(seeded.asked_her)]["in_common"] == 6
    assert COHORT.by_handle(ASKS_HER).email != COHORT.by_handle(SHE_ASKS).email


async def test_the_screen_holds_and_a_second_run_changes_nothing(
    client, session_factory, now, world
):
    await her_friend(client)
    first = await write_same_vibe(session_factory, now=now)
    screen, read = await assert_same_vibe(
        session_factory, settings=get_settings(), seeded=first
    )
    before = await stored_events(session_factory)

    again = await write_same_vibe(session_factory, now=now)

    assert await stored_events(session_factory) == before
    assert not again.created and not again.retagged
    assert read.fresh == 10
    # Her line counts everybody in See all, fewer than a hundred here (#812).
    assert re.match(
        r"Same vibe: 10 on her row of (\d+) \(10 fresh\), \1 in See all", screen
    )


async def test_a_store_from_before_her_six_tags_is_given_them(
    client, session_factory, now, world
):
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    three = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": list(PROTAGONIST_TAGS)},
        headers=her,
    )
    assert three.status_code == 200, three.text

    seeded = await write_same_vibe(session_factory, now=now)

    profile = (await client.get("/api/v1/players/me/profile", headers=her)).json()
    assert seeded.retagged
    assert set(profile["social_tags"]) == set(HER_TAGS)
