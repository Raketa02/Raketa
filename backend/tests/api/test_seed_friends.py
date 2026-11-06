"""The seeded friends, read back the way the player app reads them (#745).

``app/seeds/friends.py`` makes friends, open requests both ways, a request set
aside, a block case and every named account's Friend link (#748) **through the
use cases a request runs**, so each is asserted by signing in as a named account
and reading the friend routes and Home — never a table. A second run asks nobody twice.
"""

from __future__ import annotations

import pytest

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.seeds.catalog import (
    ACCOUNTS,
    ASSESSMENT_COMPLETED,
    RATED_IN_EVERY_SPORT,
    RATING_BARELY_ESTABLISHED,
    THE_BLANK_WEEK_PLAYER,
    THE_POPULATED_PLAYER,
)
from app.seeds.clubs import write_the_clubs
from app.seeds.friends import write_the_friends
from app.seeds.groups import write_the_groups
from app.seeds.runner import seed
from tests.api.test_seed_groups import signed_in


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def seeded(session_factory, now):
    async with session_factory() as session:
        await seed(session)
    settings = get_settings()
    await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_groups(session_factory, settings=settings, now=now)
    return await write_the_friends(session_factory, settings=settings, now=now)


async def test_she_has_friends_requests_both_ways_and_one_set_aside(client, seeded):
    her = await signed_in(client, THE_POPULATED_PLAYER)

    friends = (await client.get("/api/v1/friends", headers=her)).json()["friends"]
    asked_her = (
        await client.get(
            "/api/v1/friends/requests", params={"direction": "ASKED_YOU"}, headers=her
        )
    ).json()["requests"]
    she_asked = (
        await client.get(
            "/api/v1/friends/requests", params={"direction": "YOU_ASKED"}, headers=her
        )
    ).json()["requests"]
    home = (await client.get("/api/v1/home", headers=her)).json()

    assert len(friends) == 2
    assert {(row["set_aside"]) for row in asked_her} == {True, False}
    assert len(she_asked) == 1
    [card] = home["friend_requests"]
    assert card["group"]["name"] == "Czwartkowy padel"
    assert card["sport"] == "PADEL"
    assert seeded.on_her_home == (RATING_BARELY_ESTABLISHED.slug,)
    assert seeded.set_aside == (ASSESSMENT_COMPLETED.slug,)


async def test_the_blocked_players_request_reads_sent_and_the_blocker_sees_nothing(
    client, seeded
):
    blocked = await signed_in(client, RATED_IN_EVERY_SPORT)
    blocker = await signed_in(client, THE_BLANK_WEEK_PLAYER)

    sent = (
        await client.get(
            "/api/v1/friends/requests",
            params={"direction": "YOU_ASKED"},
            headers=blocked,
        )
    ).json()["requests"]
    asked = (
        await client.get(
            "/api/v1/friends/requests",
            params={"direction": "ASKED_YOU"},
            headers=blocker,
        )
    ).json()["requests"]

    assert [row["nickname"] for row in sent] != []
    assert asked == []
    assert (await client.get("/api/v1/friends", headers=blocker)).json()[
        "friends"
    ] == []
    assert seeded.block_case is True


async def test_a_second_run_asks_nobody_twice(session_factory, now, seeded):
    """Nor makes anybody a second link: the same codes, read again."""

    again = await write_the_friends(session_factory, settings=get_settings(), now=now)

    assert again == seeded


async def test_every_named_account_has_the_link_its_sheet_reads(client, seeded):
    assert set(seeded.links) == {account.slug for account in ACCOUNTS}
    her = await signed_in(client, THE_POPULATED_PLAYER)

    read = await client.get("/api/v1/friends/link", headers=her)

    assert read.status_code == 200, read.text
    assert read.json()["link"] == seeded.links[THE_POPULATED_PLAYER.slug]
    page = await client.get(f"/api/v1/public/friend-links/{read.json()['code']}")
    assert page.json()["nickname"] == THE_POPULATED_PLAYER.nickname
