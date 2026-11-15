"""The seeded ranking, read back the way the player app reads it (#768, #770,
#771), and Home's Top 10 over it (#797).

``app/seeds/rankings.py`` hands its padel games to the played history — and
``ranking_crowd.py`` the crowd's — so each is a past booked game filled,
played, scored and accepted through the use cases a phone runs; the outbox
drain moves the Levels, and each move folds its row. Each claim is read by
signing in and reading ``GET /rankings/{sport}``, its pages and ``GET /home``;
*a second run changes nothing* compares the stored rows, which is the only
place a write twice would show, and counts the stored events, where a friend
asked twice would.

The world is the runner's, cut to what the layer reads: the named accounts,
everybody the games and her evenings seat out of the real cohort, the crowd,
Top 10's squash pair, every card, the clubs and their courts.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import (
    build_clock,
    build_settle_ratings_on_results,
    build_user_repository,
)
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
    FRIENDS_PROMISED,
    HER_FRIENDS,
    RANKING_GAMES,
    RESULTS,
    THE_BEGINNER,
    THE_RANKED,
    read_the_ranking,
    write_her_ranked_friends,
)
from app.seeds.runner import seed, seed_the_cohort
from app.seeds.top_ten import SQUASH_PAIR, assert_the_top_ten, write_the_squash_pair
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
        pair = await seed_the_cohort(
            session,
            cohort=SQUASH_PAIR,
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
            (member.member.handle, member.player_id)
            for member in (*members, *crowd, *pair)
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
    await write_the_squash_pair(session_factory, settings=get_settings(), now=now)
    await deliver_the_outbox(session_factory, rounds=200)
    await write_her_ranked_friends(session_factory, now=now)


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
    # Among her friends one result lists a player, and the beginner, a friend
    # of hers, played her one tennis evening and lost it: she is first of the
    # two (#771).
    assert home["ranking"] == {
        "sport": "TENNIS",
        "general_place": None,
        "friends_place": 1,
    }
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
    assert home["ranking"] == {
        "sport": "TENNIS",
        "general_place": 1,
        "friends_place": 1,
    }


async def test_her_friends_table_lists_four_of_her_padel_group(
    client, session_factory, ranked_world, now
):
    await _the_history(session_factory, now)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    nicknames = {
        handle: await _nickname(session_factory, COHORT.by_handle(handle).email)
        for handle in HER_FRIENDS
    }

    friends = (
        await client.get(
            "/api/v1/rankings/PADEL", params={"view": "FRIENDS"}, headers=her
        )
    ).json()

    listed = [row["nickname"] for row in friends["rows"] if not row["is_you"]]
    assert sorted(listed) == sorted(nicknames.values())
    assert len(listed) >= FRIENDS_PROMISED
    # Two above her, and two below with the beginner: Friends lists from the
    # first result, General from the fifth.
    assert (friends["card"]["state"], friends["card"]["place"]) == ("LISTED", 3)
    assert friends["listed"] == len(HER_FRIENDS) + 1
    assert nicknames[THE_BEGINNER] in listed
    assert len(friends["podium"]) == 3 and friends["next"] is None
    line = friends["card"]["gap_line"]
    assert line["above"]["nickname"] == nicknames["cohort-a-08"]
    assert line["below"]["nickname"] == nicknames["cohort-b-04"]
    seeded = await read_the_ranking(session_factory, settings=get_settings(), now=now)
    assert (seeded.friends_place, seeded.friends_of) == (3, len(HER_FRIENDS) + 1)


async def _nickname(session_factory, email: str) -> str:
    async with session_factory() as session:
        users = build_user_repository(session)
        user = await users.get_by_email(email)
        assert user is not None
        return (await users.find_nicknames_of([user.id]))[user.id]


async def test_a_second_run_changes_nothing(client, session_factory, ranked_world, now):
    await _the_history(session_factory, now)
    first = await stored_rows(session_factory)
    async with session_factory() as session:
        events = await session.scalar(select(func.count()).select_from(EventStoreORM))

    # The crowd and the squash pair written again — registered, rated,
    # committed and cleared — and the history after them.
    async with session_factory() as session:
        for cohort in (RANKING_CROWD, SQUASH_PAIR):
            await seed_the_cohort(
                session,
                cohort=cohort,
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


async def _top_ten(client, headers: dict, **params) -> dict:
    read = await client.get("/api/v1/top-10", params=params, headers=headers)
    assert read.status_code == 200, read.text
    return read.json()


async def test_top_ten_reads_ten_in_padel_the_pair_in_squash_and_nobody_in_badminton(  # noqa: E501
    client, session_factory, ranked_world, now
):
    await _the_history(session_factory, now)
    her = await signed_in(client, THE_POPULATED_PLAYER.email)
    pair = sorted(
        [await _nickname(session_factory, one.email) for one in SQUASH_PAIR.members]
    )

    padel = await _top_ten(client, her, sport="PADEL")
    squash = await _top_ten(client, her, sport="SQUASH")
    badminton = await _top_ten(client, her, sport="BADMINTON")

    assert [one["place"] for one in padel["players"]] == list(range(1, 11))
    assert not any(one["is_you"] for one in padel["players"])
    assert sorted(one["nickname"] for one in squash["players"]) == pair
    assert [one["place"] for one in squash["players"]] == [1, 2]
    assert badminton == {"sport": "BADMINTON", "anyone_listed": True, "players": []}
    # Nobody else plays squash, and the pair hold none of her tags: no row of
    # hers reads them, and their group of two is left off Hottest groups.
    for row in ("/api/v1/same-level", "/api/v1/same-vibe", "/api/v1/new-in-raketa"):
        read = (await client.get(row, headers=her)).json()
        assert not set(pair) & {one["nickname"] for one in read["players"]}, row
    assert await assert_the_top_ten(session_factory, settings=get_settings(), now=now)

    # Her four agreed tennis results list nobody in this world, so preferring
    # her trophy's sport falls through to the next with anybody listed...
    assert (await _top_ten(client, her, prefer="TENNIS"))["sport"] == "SQUASH"
    # ...until the API's first tick confirms her silent evening, her fifth:
    # then it opens on tennis, with her own card.
    async with session_factory() as session:
        await build_settle_ratings_on_results(
            session, clock=FixedClock(at=now)
        ).execute()
    await deliver_the_outbox(session_factory)
    opening = await _top_ten(client, her, prefer="TENNIS")

    assert opening["sport"] == "TENNIS"
    assert [(one["place"], one["is_you"]) for one in opening["players"]] == [(1, True)]
    assert await assert_the_top_ten(session_factory, settings=get_settings(), now=now)
