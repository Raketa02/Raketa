"""The seeded ranking, read back the way the player app reads it (#768, #770).

``app/seeds/rankings.py`` hands its padel games to the played history — and
``ranking_crowd.py`` the crowd's — so each is a past booked game filled,
played, scored and accepted through the use cases a phone runs; the outbox
drain moves the Levels, and each move folds its row. Each claim is read by
signing in and reading ``GET /rankings/{sport}``, its pages and ``GET /home``;
*a second run changes nothing* compares the stored rows, which is the only
place a write twice would show.

The world is the runner's, cut to what the layer reads: the named accounts,
everybody the games and her evenings seat out of the real cohort, the crowd,
every card, the clubs and their courts.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_clock, build_settle_ratings_on_results
from app.core.config import get_settings
from app.infrastructure.events.event_store_model import EventStoreORM
from app.seeds.booked_history import HER_EVENINGS, write_the_played_history
from app.seeds.catalog import ACCOUNTS, SEED_PASSWORD, THE_POPULATED_PLAYER
from app.modules.rankings.domain.ranking import PAGE_SIZE
from app.seeds.clock import FixedClock
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.cohort import COHORT, PROTAGONIST_HANDLE, Cohort
from app.seeds.payments import write_the_payment_methods
from app.seeds.ranking_crowd import RANKING_CROWD_GAMES, RANKING_CROWD
from app.seeds.rankings import (
    RANKING_GAMES,
    RESULTS,
    THE_BEGINNER,
    THE_RANKED,
    read_the_ranking,
)
from app.seeds.runner import seed, seed_the_cohort
from tests.api.players_world import deliver_the_outbox
from tests.api.rankings_world import stored_rows
from tests.unit.fake_photo_storage import InMemoryPhotoStorage


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def ranked_world(session_factory, now):
    settings = get_settings()
    photos = InMemoryPhotoStorage()
    seated = Cohort(
        seed=COHORT.seed,
        members=tuple(
            COHORT.by_handle(handle)
            for handle in sorted(
                {evening.opponent for evening in HER_EVENINGS}
                | {
                    handle
                    for game in RANKING_GAMES
                    for handle in game.players
                    if handle != PROTAGONIST_HANDLE
                }
            )
        ),
    )
    async with session_factory() as session:
        await seed(session, clock=FixedClock(at=now), settings=settings, photos=photos)
        members = await seed_the_cohort(
            session,
            cohort=seated,
            clock=FixedClock(at=now),
            settings=settings,
            photos=photos,
        )
        crowd = await seed_the_cohort(
            session,
            cohort=RANKING_CROWD,
            clock=FixedClock(at=now),
            settings=settings,
            photos=photos,
            photographs=False,
            clear_the_week=True,
        )
    await write_the_payment_methods(
        session_factory,
        now=now,
        cohort=[
            (member.member.handle, member.player_id) for member in (*members, *crowd)
        ],
    )
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )


async def _the_history(session_factory, now) -> None:
    await write_the_played_history(
        session_factory,
        settings=get_settings(),
        now=now,
        games=(*RANKING_GAMES, *RANKING_CROWD_GAMES),
        named=ACCOUNTS,
        crowd=RANKING_CROWD.members,
    )
    await deliver_the_outbox(session_factory, rounds=200)


async def signed_in(client, email: str) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _read(client, headers: dict, sport: str) -> dict:
    read = await client.get(f"/api/v1/rankings/{sport}", headers=headers)
    assert read.status_code == 200, read.text
    return read.json()


async def test_padel_lists_her_below_page_one_the_beginner_is_short_and_badminton_is_empty(  # noqa: E501
    client, session_factory, ranked_world, now
):
    await _the_history(session_factory, now)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    beginner = await signed_in(client, COHORT.by_handle(THE_BEGINNER).email)

    padel = await _read(client, her, "PADEL")
    short = await _read(client, beginner, "PADEL")
    badminton = await _read(client, her, "BADMINTON")
    home = (await client.get("/api/v1/home", headers=her)).json()

    assert padel["listed"] == len(THE_RANKED) == 14 + len(RANKING_CROWD.members)
    assert padel["card"]["state"] == "LISTED"
    # Below the first page and not last: *You · 56th*.
    place = padel["card"]["place"]
    assert PAGE_SIZE < place < padel["listed"]
    assert len(padel["podium"]) == 3 and len(padel["rows"]) == PAGE_SIZE
    assert not any(row["is_you"] for row in padel["rows"])
    # The jump button's page has her in it, and reading on from the first page
    # reaches her too.
    around = (
        await client.get(
            "/api/v1/rankings/PADEL/general/rows",
            params={"around_me": True},
            headers=her,
        )
    ).json()
    [mine] = [row for row in around["rows"] if row["is_you"]]
    assert mine["place"] == place and len(mine["form"]) == 5
    after = (
        await client.get(
            "/api/v1/rankings/PADEL/general/rows",
            params={"after": padel["next"]},
            headers=her,
        )
    ).json()
    assert [row["place"] for row in after["rows"]][0] == PAGE_SIZE + 1
    assert any(row["is_you"] for row in after["rows"])
    assert (short["card"]["state"], short["card"]["results"]) == (
        "NEEDS_RESULTS",
        RESULTS[THE_BEGINNER],
    )
    assert (badminton["listed"], badminton["rows"], badminton["podium"]) == (0, [], [])
    # Her latest result is her last tennis evening, the day before her week,
    # so the trophy follows tennis — where four agreed results list nobody
    # until the catch-up confirms the fifth (#768; the mechanics §8).
    assert home["ranking"] == {"sport": "TENNIS", "general_place": None}
    seeded = await read_the_ranking(session_factory, settings=get_settings(), now=now)
    assert (seeded.place, seeded.of) == (padel["card"]["place"], padel["listed"])

    # The API's first tick: the catch-up confirms her silent evening, her fifth
    # tennis result, and the trophy has a number — first in tennis, where she
    # is the only one listed in this world.
    async with session_factory() as session:
        await build_settle_ratings_on_results(
            session, clock=FixedClock(at=now)
        ).execute()
    await deliver_the_outbox(session_factory)
    home = (await client.get("/api/v1/home", headers=her)).json()
    assert home["ranking"] == {"sport": "TENNIS", "general_place": 1}


async def test_a_second_run_changes_nothing(client, session_factory, ranked_world, now):
    await _the_history(session_factory, now)
    first = await stored_rows(session_factory)
    async with session_factory() as session:
        events = await session.scalar(select(func.count()).select_from(EventStoreORM))

    # The crowd written again — registered, rated, committed and cleared —
    # and the history after it.
    async with session_factory() as session:
        await seed_the_cohort(
            session,
            cohort=RANKING_CROWD,
            clock=FixedClock(at=now),
            settings=get_settings(),
            photos=InMemoryPhotoStorage(),
            photographs=False,
            clear_the_week=True,
        )
    await _the_history(session_factory, now)

    assert await stored_rows(session_factory) == first
    async with session_factory() as session:
        again = await session.scalar(select(func.count()).select_from(EventStoreORM))
    assert again == events
