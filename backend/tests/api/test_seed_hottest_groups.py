"""The seeded *Hottest groups*, read back the way the player app reads them
(#792; the Home rows mechanics §20).

``app/seeds/hottest_groups.py`` writes one group the row cannot do without —
the ranking's crowd's *Wieczorny Kazimierz*, three games in it this week — and
her Join request waiting on it. Each claim is read by signing in as her and
reading ``GET /hottest-groups``; *a second run changes nothing* counts the
stored events, where a member let in twice or a game booked twice would show.

The world is the runner's, cut to what the layer reads — the named accounts,
the ranking's crowd with a card each, the clubs and their courts — and the
groups layer, whose two four-player groups are GROWING and whose two-player
group stays out. The whole row, with every layer's groups, is the runner's own
screen assertion (``assert_the_hottest_groups``).
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.seeds.catalog import SEED_PASSWORD, THE_POPULATED_PLAYER
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.clock import FixedClock
from app.seeds.groups import write_the_groups
from app.seeds.hottest_groups import (
    HOTTEST_GROUP,
    MEMBERS,
    TOO_SMALL,
    write_the_hottest_groups,
)
from app.seeds.payments import write_the_payment_methods
from app.seeds.ranking_crowd import RANKING_CROWD
from app.seeds.runner import seed, seed_the_cohort
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

HOTTEST = "/api/v1/hottest-groups"


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def crowd(session_factory, now) -> list[tuple[str, object]]:
    settings = get_settings()
    photos = InMemoryPhotoStorage()
    async with session_factory() as session:
        await seed(session, clock=FixedClock(at=now), settings=settings, photos=photos)
        members = await seed_the_cohort(
            session,
            cohort=RANKING_CROWD,
            clock=FixedClock(at=now),
            settings=settings,
            photos=photos,
            photographs=False,
            clear_the_week=True,
        )
    crowd = [(member.member.handle, member.player_id) for member in members]
    await write_the_payment_methods(session_factory, now=now, cohort=crowd)
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )
    await write_the_groups(session_factory, settings=settings, now=now)
    return crowd


async def signed_in(client, email: str) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def her_row(client) -> list[dict]:
    read = await client.get(
        HOTTEST, headers=await signed_in(client, THE_POPULATED_PLAYER.email)
    )
    assert read.status_code == 200, read.text
    return read.json()["groups"]


async def stored_events(session_factory) -> int:
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(EventStoreORM))


async def test_her_row_opens_on_the_hottest_group_with_her_request_waiting(
    client, session_factory, crowd, now
):
    seeded = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=now, crowd=crowd
    )

    row = await her_row(client)

    first = row[0]
    assert (first["id"], first["name"], first["tag"]) == (
        str(seeded.group_id),
        HOTTEST_GROUP,
        "HOTTEST",
    )
    assert (first["relation"], first["join_policy"]) == (
        "REQUESTED",
        "PEOPLE_I_APPROVE",
    )
    assert (
        first["games_this_week"],
        first["member_count"],
        first["new_this_month"],
    ) == (3, MEMBERS, MEMBERS)
    assert first["club"]["name"] == "Kazimierz Padel"
    assert [made for _, made in seeded.games] == [True, True, True]
    # The groups layer's four-player groups are GROWING, its two-player one out.
    tags = {card["name"]: card["tag"] for card in row}
    assert tags["Czwartkowy padel"] == tags["Bonarka weekend"] == "GROWING"
    assert TOO_SMALL not in tags


async def test_a_second_run_writes_nothing(client, session_factory, crowd, now):
    first = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=now, crowd=crowd
    )
    stored = await stored_events(session_factory)

    again = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=now, crowd=crowd
    )

    assert await stored_events(session_factory) == stored
    assert (again.group_id, again.created) == (first.group_id, False)
    assert [start for start, _ in again.games] == [start for start, _ in first.games]
    assert [made for _, made in again.games] == [False, False, False]


async def test_a_request_she_withdrew_is_put_back_on_the_next_run(
    client, session_factory, crowd, now
):
    seeded = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=now, crowd=crowd
    )
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    withdrawn = await client.delete(
        f"/api/v1/groups/{seeded.group_id}/join-request", headers=her
    )
    assert withdrawn.status_code == 204, withdrawn.text
    assert (await her_row(client))[0]["relation"] == "NONE"

    await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=now, crowd=crowd
    )

    assert (await her_row(client))[0]["relation"] == "REQUESTED"


async def test_a_run_days_later_books_this_week_s_games_again(
    client, session_factory, crowd, now
):
    """Seeded six days ago, its games are eight to ten days old today: a run
    now books the same fours where they fall this week, and the group is
    HOTTEST again."""

    earlier = instant(now - timedelta(days=6))
    first = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=earlier, crowd=crowd
    )

    later = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=now, crowd=crowd
    )

    assert later.group_id == first.group_id
    assert [made for _, made in later.games] == [True, True, True]
    assert all(start > now - timedelta(days=7) for start, _ in later.games)
    first_card = (await her_row(client))[0]
    assert (first_card["id"], first_card["tag"]) == (str(first.group_id), "HOTTEST")
    assert (first_card["games_this_week"], first_card["relation"]) == (3, "REQUESTED")


async def test_a_day_the_club_sells_nothing_is_stepped_over(
    client, session_factory, crowd, now
):
    """Kazimierz Padel sells no Monday (``club_courts.py``), so a run on a
    Friday, whose two, three and four days ago end on one, books its third game
    on the Sunday before it — still three games, inside the seven days. Seeded
    on the last Friday, so it holds on any day the suite runs."""

    friday = instant(
        now - timedelta(days=(now.astimezone(CLUB_ZONE).isoweekday() - 5) % 7)
    )

    seeded = await write_the_hottest_groups(
        session_factory, settings=get_settings(), now=friday, crowd=crowd
    )

    assert [made for _, made in seeded.games] == [True, True, True]
    assert [f"{start.astimezone(CLUB_ZONE):%a}" for start, _ in seeded.games] == [
        "Sun",
        "Tue",
        "Wed",
    ]
    assert all(friday - timedelta(days=7) < start < friday for start, _ in seeded.games)
