"""The seeded For-fun deck, read back the way the player app reads it (#832;
``docs/adr/0207`` §2, §8, §11).

``app/seeds/for_fun.py`` writes four tennis players outside the cohort, one
per Social vibe band against her six tags, gathers them into her *Tenis na
luzie* at Prądnik Tennis and runs the proposer over it. Each claim is read by
signing in as her; *a second run changes nothing* counts the stored events.

The world is the runner's named accounts, the four, and the clubs selling
their courts — everything the layer reads.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.infrastructure.events.event_store_model import EventStoreORM
from app.seeds.catalog import SEED_PASSWORD, THE_POPULATED_PLAYER
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.clock import FixedClock
from app.seeds.for_fun import (
    BANDS,
    FOR_FUN_CROWD,
    IN_THE_BAND,
    assert_the_for_fun_deck,
    band_of,
    write_the_for_fun_deck,
)
from app.seeds.runner import seed, seed_the_cohort
from tests.unit.fake_photo_storage import InMemoryPhotoStorage


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
            session,
            cohort=FOR_FUN_CROWD,
            clock=FixedClock(at=now),
            settings=get_settings(),
            photos=photos,
            photographs=False,
        )
    clubs = await write_the_clubs(session_factory, settings=get_settings(), now=now)
    await write_the_club_courts(
        session_factory, settings=get_settings(), now=now, clubs=clubs
    )


async def signed_in(client, email: str = THE_POPULATED_PLAYER.email) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def for_fun_tennis(client, group_id: UUID, headers: dict) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group_id}/deck",
        params={"sport": "TENNIS", "kind": "FOR_FUN"},
        headers=headers,
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


def opposite(card: dict) -> str:
    (them,) = (tile["nickname"] for tile in card["sides"]["theirs"])
    return them


async def stored_events(session_factory) -> int:
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(EventStoreORM))


async def test_her_for_fun_deck_holds_a_card_in_every_band(
    client, session_factory, now, world
):
    seeded = await write_the_for_fun_deck(
        session_factory, settings=get_settings(), now=now
    )

    cards = await for_fun_tennis(client, seeded.group_id, await signed_in(client))

    # One card with each of the four, the best company first, and no forecast
    # on a friendly.
    assert [card["vibe"]["pct"] for card in cards] == [83, 60, 36, 14]
    assert [band_of(card["vibe"]["pct"]).word for card in cards] == [
        band.word for band in BANDS
    ]
    assert all(card["forecast"] is None for card in cards)
    handle = {member.nickname: member.handle for member in FOR_FUN_CROWD.members}
    for card in cards:
        assert IN_THE_BAND[handle[opposite(card)]] == band_of(card["vibe"]["pct"]).word
    line = await assert_the_for_fun_deck(
        session_factory, settings=get_settings(), now=now, seeded=seeded
    )
    assert "Great vibe 83%" in line and "Fresh mix 14%" in line


async def test_the_deal_reads_their_tags(client, session_factory, now, world):
    """Everybody stands level, so only the tags tell two tables apart: at the
    first hour she is seated with the Great vibe player, and the second court
    goes to the best of the rest — Good vibe with Fresh mix, a bite after
    (17%) — never to the next two to have joined (Good and Some, 0%)."""

    seeded = await write_the_for_fun_deck(
        session_factory, settings=get_settings(), now=now
    )
    great, good, _, fresh = FOR_FUN_CROWD.members

    cards = await for_fun_tennis(
        client, seeded.group_id, await signed_in(client, good.email)
    )

    first = min(cards, key=lambda card: card["starts_at"])
    assert opposite(first) == fresh.nickname
    her_deck = await for_fun_tennis(client, seeded.group_id, await signed_in(client))
    (hers,) = (card for card in her_deck if opposite(card) == great.nickname)
    assert hers["starts_at"] == first["starts_at"]


async def test_a_member_holding_other_tags_is_given_their_row_s_again(
    client, session_factory, now, world
):
    """A store seeded before the cohort's last redraw holds the tags the old
    draw gave (#832): the next run gives them their row's through *Edit tags*,
    and the one after records nothing."""

    member = FOR_FUN_CROWD.members[0]
    edited = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": ["QUIET_AND_FOCUSED", "STRAIGHT_HOME_AFTER"]},
        headers=await signed_in(client, member.email),
    )
    assert edited.status_code == 200, edited.text

    async def runs() -> dict[str, bool]:
        async with session_factory() as session:
            written = await seed_the_cohort(
                session,
                cohort=FOR_FUN_CROWD,
                clock=FixedClock(at=now),
                settings=get_settings(),
                photos=InMemoryPhotoStorage(),
                photographs=False,
            )
        return {entry.member.handle: entry.retagged for entry in written}

    assert await runs() == {
        one.handle: one.handle == member.handle for one in FOR_FUN_CROWD.members
    }
    profile = await client.get(
        "/api/v1/players/me/profile", headers=await signed_in(client, member.email)
    )
    assert profile.status_code == 200, profile.text
    assert set(profile.json()["social_tags"]) == set(member.tags)
    events = await stored_events(session_factory)
    assert not any((await runs()).values())
    assert await stored_events(session_factory) == events


async def test_the_group_is_nobody_s_new_one_and_a_second_run_writes_nothing(
    client, session_factory, now, world
):
    """Opened and joined 31 days ago, so Hottest groups counts nobody new in it
    — and a second run at the same instant deals, joins and opens nothing."""

    first = await write_the_for_fun_deck(
        session_factory, settings=get_settings(), now=now
    )
    events = await stored_events(session_factory)

    again = await write_the_for_fun_deck(
        session_factory, settings=get_settings(), now=now
    )

    assert first.created and first.proposed.made >= len(BANDS)
    assert (again.group_id, again.created, again.proposed.made) == (
        first.group_id,
        False,
        0,
    )
    assert await stored_events(session_factory) == events
    her = await signed_in(client)
    hottest = await client.get("/api/v1/hottest-groups", headers=her)
    assert hottest.status_code == 200, hottest.text
    (ours,) = (
        card for card in hottest.json()["groups"] if UUID(card["id"]) == first.group_id
    )
    assert ours["new_this_month"] == 0
