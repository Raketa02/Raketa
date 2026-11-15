"""The seeded *New in Raketa*, read back the way the player app reads it (#793;
the home-rows mechanics §20).

``app/seeds/new_in_raketa.py`` writes eight joiners outside the cohort across
the 30 days and one past them, and her three relations among them. Each claim
is read by signing in as her and reading ``GET /new-in-raketa`` and its See
all; *a second run changes nothing* counts the stored events, where an account,
a profile or a request written twice would show.

The world is the runner's named accounts alone — she must exist to be asked —
and the layer. The whole row, with the cohort's joiners beside these, is the
runner's own screen assertion (``assert_new_in_raketa``).
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.infrastructure.events.event_store_model import EventStoreORM
from app.seeds.catalog import SEED_PASSWORD, THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.new_in_raketa import (
    ASKED_HER,
    HER_FRIEND,
    JOINED_TODAY,
    JOINERS,
    OUT_OF_THE_MONTH,
    SHE_ASKED,
    assert_new_in_raketa,
    write_new_in_raketa,
)
from app.seeds.runner import seed
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

ROW = "/api/v1/new-in-raketa"
ALL = "/api/v1/new-in-raketa/all"


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
def photos():
    return InMemoryPhotoStorage()


@pytest.fixture
async def named(session_factory, now, photos):
    async with session_factory() as session:
        await seed(
            session, clock=FixedClock(at=now), settings=get_settings(), photos=photos
        )


async def written(session_factory, now, photos):
    return await write_new_in_raketa(
        session_factory,
        settings=get_settings(),
        now=now,
        photos=photos,
        photographs=True,
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


async def test_her_row_holds_the_joiners_in_order_and_the_old_one_stays_out(
    client, session_factory, named, now, photos
):
    seeded = await written(session_factory, now, photos)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)

    row = (await client.get(ROW, headers=her)).json()["players"]
    every = (await client.get(ALL, headers=her)).json()

    by_id = {card["player_id"]: card for card in row}
    relation = {
        index: by_id[str(seeded.ids[index])]["relation"]
        for index in (JOINED_TODAY, SHE_ASKED, ASKED_HER, HER_FRIEND)
    }
    assert relation == {
        JOINED_TODAY: "NONE",
        SHE_ASKED: "SENT",
        ASKED_HER: "ASKED_YOU",
        HER_FRIEND: "FRIEND",
    }
    assert row[-1]["player_id"] == str(seeded.ids[HER_FRIEND])
    assert by_id[str(seeded.ids[JOINED_TODAY])]["sports"] == []
    assert by_id[str(seeded.ids[JOINED_TODAY])]["days_since_joined"] == 0
    listed = {card["player_id"] for card in every["players"]}
    assert str(seeded.ids[OUT_OF_THE_MONTH]) not in listed
    # Every joiner of the month is listed — the catalog's own the-newcomer too.
    assert {
        str(player_id)
        for index, player_id in enumerate(seeded.ids)
        if index != OUT_OF_THE_MONTH
    } < listed
    assert every["sports"] == ["PADEL", "TENNIS", "SQUASH", "BADMINTON"]
    assert seeded.created
    assert (
        await assert_new_in_raketa(
            session_factory, settings=get_settings(), now=now, seeded=seeded
        )
    ).startswith("New in Raketa: ")


async def test_the_one_she_asked_reads_found_you_among_new_players(
    client, session_factory, named, now, photos
):
    await written(session_factory, now, photos)
    asked = JOINERS.members[SHE_ASKED]

    home = await client.get(
        "/api/v1/home", headers=await signed_in(client, asked.email)
    )

    [card] = home.json()["friend_requests"]
    assert card["nickname"] == THE_POPULATED_PLAYER.nickname
    assert card["from_new_players"] is True


async def test_a_second_run_writes_nothing(client, session_factory, named, now, photos):
    first = await written(session_factory, now, photos)
    stored = await stored_events(session_factory)

    again = await written(session_factory, now, photos)

    assert await stored_events(session_factory) == stored
    assert (again.ids, again.created) == (first.ids, False)
