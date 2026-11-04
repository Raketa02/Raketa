"""The seeded groups, read back the way the player app reads them.

``app/seeds/groups.py`` creates four player groups at the seeded clubs **through
the use cases a request runs**, so each is asserted by signing in as a named
account and reading its Groups list, a group's page and a home-club search —
never by looking in a table.
"""

from __future__ import annotations

import pytest

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.seeds.catalog import (
    RATED_IN_EVERY_SPORT,
    SEED_PASSWORD,
    THE_NEWCOMER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.clubs import write_the_clubs
from app.seeds.groups import SEED_GROUPS, write_the_groups
from app.seeds.runner import seed


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def seeded(session_factory, now):
    async with session_factory() as session:
        await seed(session)
    await write_the_clubs(session_factory, settings=get_settings(), now=now)
    return await write_the_groups(session_factory, settings=get_settings(), now=now)


async def signed_in(client, account: SeedAccount) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": account.email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def groups_of(client, account: SeedAccount) -> list[dict]:
    listed = await client.get(
        "/api/v1/groups", headers=await signed_in(client, account)
    )
    assert listed.status_code == 200, listed.text
    return listed.json()["groups"]


async def test_the_default_protagonist_owns_two_groups_and_joined_another_later(
    client, seeded
):
    listed = await groups_of(client, THE_POPULATED_PLAYER)

    assert [
        (row["name"], row["home_club"]["name"], row["sports"], row["member_count"])
        for row in listed
    ] == [
        ("Bonarka weekend", "Bonarka Arena", ["PADEL", "TENNIS"], 4),
        ("Czwartkowy padel", "Centrum Ruchu", ["PADEL"], 4),
        ("Ogrody wieczorem", "Ogrody 33", ["PADEL"], 2),
    ]


async def test_one_member_rated_in_a_sport_is_never_its_dot(client, seeded):
    """Only ``rated-in-every-sport`` plays squash and badminton, so no seeded
    group has either dot — and the one nobody joined has none at all."""

    listed = await groups_of(client, RATED_IN_EVERY_SPORT)

    assert [(row["name"], row["sports"]) for row in listed] == [
        ("Squash po pracy", []),
        ("Błonia po pracy", ["PADEL"]),
        ("Bonarka weekend", ["PADEL", "TENNIS"]),
    ]


async def test_the_newcomer_is_in_no_group(client, seeded):
    assert await groups_of(client, THE_NEWCOMER) == []


async def test_a_group_s_first_to_join_are_its_members_in_the_order_they_joined(
    client, seeded
):
    headers = await signed_in(client, THE_POPULATED_PLAYER)
    [mine] = [
        row
        for row in await groups_of(client, THE_POPULATED_PLAYER)
        if row["name"] == "Czwartkowy padel"
    ]

    page = (await client.get(f"/api/v1/groups/{mine['id']}", headers=headers)).json()

    padel = next(row for row in page["rated_by_sport"] if row["sport"] == "PADEL")
    declared = next(group for group in SEED_GROUPS if group.name == "Czwartkowy padel")
    assert page["is_owner"] is True
    assert padel["rated_count"] == 4
    assert [person["nickname"] for person in padel["first_rated"]] == [
        account.nickname for account in (declared.owner, *declared.members)
    ]


async def test_searching_b_shows_the_protagonist_a_group_to_join(client, seeded):
    headers = await signed_in(client, THE_POPULATED_PLAYER)

    found = await client.get("/api/v1/home-clubs", params={"q": "b"}, headers=headers)

    assert found.status_code == 200, found.text
    relations = {
        club["name"]: [(group["name"], group["relation"]) for group in club["groups"]]
        for club in found.json()["clubs"]
    }
    assert relations == {
        "Centrum Ruchu": [("Czwartkowy padel", "MEMBER")],
        "Bonarka Arena": [("Bonarka weekend", "MEMBER")],
        "Zabłocie Sport": [("Squash po pracy", "NONE")],
        "Wisła Park": [("Błonia po pracy", "NONE")],
    }
    assert [club["name"] for club in found.json()["clubs"]] == list(relations)


async def the_approval_group(client) -> tuple[dict, dict]:
    headers = await signed_in(client, THE_POPULATED_PLAYER)
    [group] = [
        row
        for row in await groups_of(client, THE_POPULATED_PLAYER)
        if row["name"] == "Ogrody wieczorem"
    ]
    return headers, group


async def test_the_protagonist_s_approval_group_has_one_request_waiting(client, seeded):
    """The request card, club 20: the one waiting is rated in all four sports,
    the longest line of Levels a card can be asked to draw."""

    headers, group = await the_approval_group(client)

    page = await client.get(f"/api/v1/groups/{group['id']}", headers=headers)
    listed = await client.get(f"/api/v1/groups/{group['id']}/requests", headers=headers)

    assert page.json()["join_policy"] == "PEOPLE_I_APPROVE"
    assert listed.status_code == 200, listed.text
    [request] = listed.json()["requests"]
    assert request["nickname"] == RATED_IN_EVERY_SPORT.nickname
    assert [row["sport"] for row in request["levels"]] == [
        "PADEL",
        "TENNIS",
        "SQUASH",
        "BADMINTON",
    ]


async def test_the_one_waiting_sees_requested_on_the_group(client, seeded):
    _, group = await the_approval_group(client)
    headers = await signed_in(client, RATED_IN_EVERY_SPORT)

    found = await client.get(
        "/api/v1/join-search", params={"q": "ogrody wieczorem"}, headers=headers
    )

    assert found.status_code == 200, found.text
    [card] = found.json()["clubs"]
    [row] = card["groups"]
    assert (row["id"], row["relation"]) == (group["id"], "REQUESTED")
    assert row["owner_nickname"] == THE_POPULATED_PLAYER.nickname


async def test_a_second_run_creates_nothing_and_joins_nobody_twice(
    client, session_factory, seeded, now
):
    before = await groups_of(client, RATED_IN_EVERY_SPORT)
    headers, group = await the_approval_group(client)
    requests = f"/api/v1/groups/{group['id']}/requests"
    waiting = (await client.get(requests, headers=headers)).json()

    again = await write_the_groups(session_factory, settings=get_settings(), now=now)

    assert [entry.created for entry in seeded.groups] == [True] * len(SEED_GROUPS)
    assert [entry.created for entry in again.groups] == [False] * len(SEED_GROUPS)
    assert [entry.group_id for entry in again.groups] == [
        entry.group_id for entry in seeded.groups
    ]
    assert await groups_of(client, RATED_IN_EVERY_SPORT) == before
    assert (await client.get(requests, headers=headers)).json() == waiting
