"""The seeded official groups, read back the way the administrator profile and
the player app read them.

``app/seeds/official_groups.py`` creates Ogrody 33's two official groups
**through the use cases a request runs**, so each is asserted by signing in — as
the administrator who runs it, and as a player — and never by looking in a
table.
"""

from __future__ import annotations

import pytest

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.seeds.administrators import (
    ADMINISTRATOR_ONLY_EMAIL,
    PLAYER_AND_ADMINISTRATOR,
    write_the_administrators,
)
from app.seeds.catalog import (
    ASSESSMENT_COMPLETED,
    SEED_PASSWORD,
    THE_POPULATED_PLAYER,
)
from app.seeds.clubs import write_the_clubs
from app.seeds.groups import write_the_groups
from app.seeds.official_groups import write_the_official_groups
from app.seeds.runner import seed


@pytest.fixture
def now():
    return build_clock().now()


async def _official(session_factory, now):
    return await write_the_official_groups(
        session_factory, settings=get_settings(), now=now
    )


@pytest.fixture
async def seeded(session_factory, now):
    async with session_factory() as session:
        await seed(session)
    settings = get_settings()
    await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_groups(session_factory, settings=settings, now=now)
    await write_the_administrators(session_factory, settings=settings, now=now)
    return await _official(session_factory, now)


async def signed_in(client, email: str) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def administered(client, email: str) -> tuple[str, dict, list[dict]]:
    """The club this administrator runs groups at, their session, and their
    Groups tab."""

    session = await signed_in(client, email)
    me = (await client.get("/api/v1/users/me", headers=session)).json()
    (club,) = me["profiles"]["administers"]
    listed = await client.get(
        f"/api/v1/administrator/clubs/{club['club_id']}/groups", headers=session
    )
    assert listed.status_code == 200, listed.text
    return club["club_id"], session, listed.json()["groups"]


async def test_marta_runs_ogrody_33_club_with_three_players_and_one_waiting(
    client, seeded
):
    club_id, marta, groups = await administered(client, ADMINISTRATOR_ONLY_EMAIL)

    (card,) = groups
    page = (
        await client.get(
            f"/api/v1/administrator/clubs/{club_id}/groups/{card['id']}",
            headers=marta,
        )
    ).json()
    assert (
        card["name"],
        card["sports"],
        card["member_count"],
        card["waiting_count"],
    ) == (
        "Ogrody 33 Club",
        ["PADEL"],
        3,
        1,
    )
    assert page["whatsapp_size"] == 48
    assert page["join_policy"] == "PEOPLE_I_APPROVE"
    # Newest first: the protagonist joined first, eleven days and more ago.
    assert page["players"][-1]["player_id"] == str(
        (
            await client.get(
                "/api/v1/users/me",
                headers=await signed_in(client, THE_POPULATED_PLAYER.email),
            )
        ).json()["id"]
    )
    (waiting,) = page["requests"]
    assert waiting["levels"] != []
    asker = await signed_in(client, ASSESSMENT_COMPLETED.email)
    asker_id = (await client.get("/api/v1/users/me", headers=asker)).json()["id"]
    assert waiting["player_id"] == asker_id


async def test_the_administrator_who_plays_is_a_member_of_his_own_group(client, seeded):
    club_id, tomek, groups = await administered(client, PLAYER_AND_ADMINISTRATOR.email)

    (card,) = groups
    rows = (
        await client.get(
            f"/api/v1/groups/{card['id']}/members",
            params={"sport": "PADEL"},
            headers=tomek,
        )
    ).json()["members"]
    assert (card["name"], card["sports"], card["member_count"]) == (
        "Ogrody open play",
        ["PADEL", "TENNIS"],
        3,
    )
    # He reads himself first, carrying the admin tag.
    assert rows[0]["is_administrator"] is True


async def test_the_protagonist_finds_an_official_group_on_her_list(client, seeded):
    session = await signed_in(client, THE_POPULATED_PLAYER.email)

    listed = (await client.get("/api/v1/groups", headers=session)).json()["groups"]
    found = (
        await client.get("/api/v1/join-search", params={"q": "ogrody"}, headers=session)
    ).json()

    assert ("OFFICIAL", "Ogrody 33 Club") in {
        (row["kind"], row["name"]) for row in listed
    }
    rows = {row["name"]: row for card in found["clubs"] for row in card["groups"]}
    assert rows["Ogrody 33 Club"]["administrator_name"] == "Marta Wójcik"
    assert rows["Ogrody 33 Club"]["relation"] == "MEMBER"
    assert (
        rows["Ogrody open play"]["administrator_name"] == PLAYER_AND_ADMINISTRATOR.name
    )


async def test_running_it_again_creates_nothing_twice(
    client, seeded, session_factory, now
):
    again = await _official(session_factory, now)

    assert [entry.action for entry in again.groups] == ["already there"] * 2
    _, _, groups = await administered(client, ADMINISTRATOR_ONLY_EMAIL)
    (card,) = groups
    assert (card["member_count"], card["waiting_count"]) == (3, 1)
