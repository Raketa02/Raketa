"""The protagonist's played history, as past booked games (#573).

``app/seeds/booked_history.py`` writes her evenings the way the Games deck makes
a game — a proposal filled by its last yes, booked, played, scored — and her
opponents rate her. Each claim here is read back the way she would read it:
signed in, through her record and each game's details — every evening ended
days ago, so none is on her Home any more (#613) — and through the rating
catch-up's own use case for the Level.

The world under it is the runner's, cut to what the layer reads: the named
accounts, her three opponents out of the real cohort, every card, the clubs and
their courts.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.bootstrap.composition import (
    build_booked_games,
    build_clock,
    build_player_bookings,
    build_settle_ratings_on_results,
)
from app.core.config import get_settings
from app.modules.proposals.domain.deck import GAME_LENGTH, week_of
from app.seeds.booked_history import (
    HER_EVENINGS,
    HistoryIsEmpty,
    assert_her_history,
    latest_evening_ends_by,
    write_the_played_history,
)
from app.seeds.catalog import SEED_PASSWORD, THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.cohort import COHORT, Cohort, PlayedGame
from app.seeds.payments import write_the_payment_methods
from app.seeds.runner import seed, seed_the_cohort
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

RECORD = "/api/v1/players/me/record"
HOME = "/api/v1/home"


@pytest.fixture
def now():
    return build_clock().now()


#: Three of the pool's padel games, none naming somebody who committed inside a
#: week: a score accepted, the one nobody agreed, and one nobody answered.
DECLARED = (
    PlayedGame(
        sport="PADEL",
        played_days_ago=11,
        side_a=("cohort-a-16", "cohort-a-07"),
        side_b=("cohort-a-05", "cohort-a-13"),
        won_by=None,
    ),
    PlayedGame(
        sport="PADEL",
        played_days_ago=10,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-12", "cohort-a-05"),
        won_by="A",
        answered=False,
    ),
    PlayedGame(
        sport="PADEL",
        played_days_ago=8,
        side_a=("cohort-a-16", "cohort-a-08"),
        side_b=("cohort-a-13", "cohort-a-12"),
        won_by="A",
    ),
)


@pytest.fixture
async def her_world(session_factory, now):
    """The named accounts, her three opponents and everybody the declared games
    seat, every card, the clubs and their courts."""

    settings = get_settings()
    photos = InMemoryPhotoStorage()
    opponents = Cohort(
        seed=COHORT.seed,
        members=tuple(
            COHORT.by_handle(handle)
            for handle in sorted(
                {evening.opponent for evening in HER_EVENINGS}
                | {handle for game in DECLARED for handle in game.players}
            )
        ),
    )
    async with session_factory() as session:
        await seed(session, clock=FixedClock(at=now), settings=settings, photos=photos)
        members = await seed_the_cohort(
            session,
            cohort=opponents,
            clock=FixedClock(at=now),
            settings=settings,
            photos=photos,
        )
    await write_the_payment_methods(
        session_factory,
        now=now,
        cohort=[(member.member.handle, member.player_id) for member in members],
    )
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )


async def signed_in_as_her(client) -> dict:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": THE_POPULATED_PLAYER.email, "password": SEED_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def statuses_on_the_details(client, session_factory, headers: dict) -> list:
    """Each booked game of the signed-in player, as its details screen says it
    ended — every one of them, whenever it was."""

    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200, me.text
    async with session_factory() as session:
        games = await build_player_bookings(session, settings=get_settings()).of_player(
            UUID(me.json()["id"]), since=None
        )
    statuses = []
    for game in games:
        read = await client.get(f"/api/v1/bookings/{game.booking_id}", headers=headers)
        assert read.status_code == 200, read.text
        statuses.append(read.json()["status"])
    return sorted(statuses)


async def test_her_evenings_are_on_her_record_with_a_mixed_run_and_her_stars(
    client, session_factory, now, her_world
):
    await write_the_played_history(session_factory, settings=get_settings(), now=now)
    headers = await signed_in_as_her(client)

    record = await client.get(RECORD, params={"sport": "TENNIS"}, headers=headers)

    assert record.status_code == 200, record.text
    body = record.json()
    assert body["skill"]["sport"] == "TENNIS"
    assert sorted(set(body["skill"]["last_five"])) == ["LOSS", "WIN"]
    assert body["variety"] == {"distinct_opponents": 3, "times_on_court": 5}
    assert body["sportsmanship"] == {"average": 4.5, "raters": 2}
    strands = {row["strand"]: row for row in body["reliability"]["strands"]}
    assert (strands["SHOWS_UP"]["good"], strands["SHOWS_UP"]["opportunities"]) == (5, 6)


async def test_every_evening_is_over_before_her_week_began(
    client, session_factory, now, her_world
):
    """A booked game counts toward its week's *games per week*, so an evening in
    this week would shrink the week every later layer seats her in."""

    seeded = await write_the_played_history(
        session_factory, settings=get_settings(), now=now
    )

    assert [written.game for written in seeded.evenings] == [
        evening.as_a_game() for evening in HER_EVENINGS
    ]
    assert all(
        written.start + GAME_LENGTH <= latest_evening_ends_by(now)
        for written in seeded.evenings
    )
    async with session_factory() as session:
        her = UUID(
            (
                await client.get(
                    "/api/v1/users/me", headers=await signed_in_as_her(client)
                )
            ).json()["id"]
        )
        this_week = await build_booked_games(session).starts_of(
            her, start=latest_evening_ends_by(now), end=now + timedelta(days=14)
        )
    assert this_week == []
    assert all(week_of(written.start) < week_of(now) for written in seeded.evenings)


async def test_her_evenings_have_ended_and_left_her_home(
    client, session_factory, now, her_world
):
    """Each ended as declared, and none needs her — so none is on her Home,
    which sends only what it draws (#613)."""

    await write_the_played_history(session_factory, settings=get_settings(), now=now)
    headers = await signed_in_as_her(client)

    home = await client.get(HOME, headers=headers)
    statuses = await statuses_on_the_details(client, session_factory, headers)

    assert statuses == sorted(["COUNTED"] * 5 + ["NEVER_PLAYED"]), statuses
    assert home.status_code == 200, home.text
    assert home.json()["games"] == []
    assert home.json()["needing_you"] == 0


async def test_the_rating_catch_up_moves_her_tennis_level(
    client, session_factory, now, her_world
):
    await write_the_played_history(session_factory, settings=get_settings(), now=now)
    headers = await signed_in_as_her(client)
    before = (
        await client.get(RECORD, params={"sport": "TENNIS"}, headers=headers)
    ).json()

    async with session_factory() as session:
        settled = await build_settle_ratings_on_results(session).execute()
    after = (
        await client.get(RECORD, params={"sport": "TENNIS"}, headers=headers)
    ).json()

    assert settled.games == 5
    assert before["skill"]["counted_games"] == 0
    assert after["skill"]["counted_games"] == 5
    assert after["skill"]["level"] != before["skill"]["level"]


async def test_the_check_reads_her_evenings_and_passes(session_factory, now, her_world):
    await write_the_played_history(session_factory, settings=get_settings(), now=now)

    line = await assert_her_history(session_factory, settings=get_settings(), now=now)

    assert "5 of 6 game(s) counted" in line
    assert "5 result(s) for the rating catch-up" in line
    assert "2 rater(s)" in line


async def test_a_record_with_no_evenings_fails_the_run_by_name(
    session_factory, now, her_world
):
    with pytest.raises(HistoryIsEmpty, match="no evening was written"):
        await assert_her_history(session_factory, settings=get_settings(), now=now)


async def test_a_second_run_writes_nothing_twice(
    client, session_factory, now, her_world
):
    first = await write_the_played_history(
        session_factory, settings=get_settings(), now=now
    )

    again = await write_the_played_history(
        session_factory, settings=get_settings(), now=now
    )

    assert all(written.made for written in first.evenings)
    assert not any(created for _, _, created in again.groups)
    assert [written.start for written in again.evenings] == [
        written.start for written in first.evenings
    ]
    assert not any(written.made or written.acts for written in again.evenings)
    assert all("already answered" in line for line in again.cards)
    headers = await signed_in_as_her(client)
    statuses = await statuses_on_the_details(client, session_factory, headers)
    assert len(statuses) == len(HER_EVENINGS)


async def signed_in_as(client, email: str) -> dict:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_declared_games_are_booked_before_her_week_and_read_as_declared(
    client, session_factory, now, her_world
):
    """**The cohort's and the pool's games are booked games too**: each played
    before her week began, with the ending it was declared with — read on the
    details of somebody who played all three."""

    seeded = await write_the_played_history(
        session_factory, settings=get_settings(), now=now, games=DECLARED
    )

    assert [written.game for written in seeded.played] == list(DECLARED)
    assert not seeded.this_week
    assert all(
        written.start + GAME_LENGTH <= latest_evening_ends_by(now)
        for written in seeded.played
    )
    headers = await signed_in_as(client, COHORT.by_handle("cohort-a-16").email)
    statuses = await statuses_on_the_details(client, session_factory, headers)
    assert statuses == ["COUNTED", "COUNTED", "UNCOUNTED"], statuses


async def test_a_second_run_writes_no_declared_game_twice(
    session_factory, now, her_world
):
    await write_the_played_history(
        session_factory, settings=get_settings(), now=now, games=DECLARED
    )

    again = await write_the_played_history(
        session_factory, settings=get_settings(), now=now, games=DECLARED
    )

    assert not any(written.made or written.acts for written in again.played)
