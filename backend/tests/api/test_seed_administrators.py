"""The seeded administrators, read back the way the club website and the player
app read them.

``app/seeds/administrators.py`` names three people at Ogrody 33 **through the use
cases a request runs**, so each is asserted by signing in — as the desk on the
club surface, and as each person on the player surface — and never by looking
in a table.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.kernel import instant
from app.seeds.administrators import (
    ADMINISTRATOR_ONLY_EMAIL,
    PENDING,
    PLAYER_AND_ADMINISTRATOR,
    THE_CLUB,
    write_the_administrators,
)
from app.seeds.catalog import SEED_PASSWORD
from app.seeds.clubs import desk_email, write_the_clubs
from app.seeds.runner import seed


@pytest.fixture
def now():
    return build_clock().now()


async def _seeded(session_factory, now):
    return await write_the_administrators(
        session_factory, settings=get_settings(), now=now
    )


@pytest.fixture
async def seeded(session_factory, now):
    async with session_factory() as session:
        await seed(session)
    await write_the_clubs(session_factory, settings=get_settings(), now=now)
    return await _seeded(session_factory, now)


async def signed_in(client, path: str, email: str) -> dict:
    login = await client.post(path, json={"email": email, "password": SEED_PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def the_desk(client) -> dict:
    return await signed_in(client, "/api/v1/club/auth/login", desk_email(THE_CLUB))


async def a_player(client, email: str) -> dict:
    return await signed_in(client, "/api/v1/auth/login", email)


async def test_the_desk_sees_two_active_administrators_and_one_invited(client, seeded):
    rows = (
        await client.get("/api/v1/club/administrators", headers=await the_desk(client))
    ).json()["administrators"]

    assert {
        row["email"]: (row["status"], row["can_reset_password"]) for row in rows
    } == {
        ADMINISTRATOR_ONLY_EMAIL: ("ACTIVE", True),
        PLAYER_AND_ADMINISTRATOR.email: ("ACTIVE", False),
        PENDING.email: ("INVITED", False),
    }


async def test_the_administrator_only_account_holds_nothing_but_the_club(
    client, seeded
):
    marta = await a_player(client, ADMINISTRATOR_ONLY_EMAIL)

    me = (await client.get("/api/v1/users/me", headers=marta)).json()

    assert "name" not in me
    assert me["nickname"] is None
    assert me["adult_attested"] is False
    assert me["profiles"]["acts_as_player"] is False
    assert [club["club_name"] for club in me["profiles"]["administers"]] == [
        THE_CLUB.name
    ]


async def test_the_player_also_runs_the_club_s_groups(client, seeded):
    tomek = await a_player(client, PLAYER_AND_ADMINISTRATOR.email)

    profiles = (await client.get("/api/v1/users/me", headers=tomek)).json()["profiles"]
    (club,) = profiles["administers"]
    profile = await client.get(
        f"/api/v1/administrator/clubs/{club['club_id']}", headers=tomek
    )

    assert profiles["acts_as_player"] is True
    assert profile.status_code == 200
    assert profile.json()["club_name"] == THE_CLUB.name


async def test_the_pending_invitation_waits_on_launch(client, seeded):
    player = await a_player(client, PENDING.email)

    profiles = (await client.get("/api/v1/users/me", headers=player)).json()["profiles"]

    assert profiles["administers"] == []
    (pending,) = profiles["pending_invitations"]
    assert pending["club_name"] == THE_CLUB.name


async def test_a_second_run_invites_nobody_twice(client, seeded, session_factory, now):
    again = await _seeded(session_factory, now)

    assert [entry.action for entry in again.administrators] == [
        "already there",
        "already there",
        "already there",
    ]
    rows = (
        await client.get("/api/v1/club/administrators", headers=await the_desk(client))
    ).json()["administrators"]
    assert len(rows) == 3


async def test_a_run_after_the_pending_invitation_expired_resends_it(
    client, seeded, session_factory, now
):
    later = await _seeded(session_factory, instant(now + timedelta(days=4)))

    assert [entry.action for entry in later.administrators][-1] == "resent"
