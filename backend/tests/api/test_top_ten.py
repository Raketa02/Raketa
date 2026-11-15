"""Top 10 on Home, read the way the player app reads it (#797;
``docs/adr/0204`` §8; the home-rows mechanics §10).

**Places 1 to 10 of General in one sport**: the first ten rows of the Rankings
page's own list, everybody counted — a blocked pair included — read off the
sport's kept General order. **Which sport**: one
asked exactly (the pill), or one preferred (the trophy's, on opening) that
falls through to the next sport in the app's order where anybody is listed,
going round. **Whether anybody is listed anywhere** says whether the row shows
at all.

Every Level is moved through the rating's own aggregate (``moves_to``), which
records the same ``rating.moved_on_result`` a settled game does, on the same
outbox; every claim is read off ``GET /top-10``.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.kernel import Sport, instant
from tests.api import players_world as players
from tests.api.players_world import deliver_the_outbox
from tests.api.rankings_world import (
    a_listed_crowd,
    move_on,
    moves_to,
    ranking,
    results_at,
)
from tests.api.test_ranking_shows_everybody import blocks
from tests.unit.kept_orders import kept_orders_of

UP_1 = {"kind": "UP", "places": 1}
DOWN_1 = {"kind": "DOWN", "places": 1}


async def top_ten(client, reader: dict, **params) -> dict:
    read = await client.get(
        "/api/v1/top-10", params=params, headers=players.auth(reader["token"])
    )
    assert read.status_code == 200, read.text
    return read.json()


def nicknames(read: dict) -> list[str]:
    return [player["nickname"] for player in read["players"]]


def places(read: dict) -> list[int]:
    return [player["place"] for player in read["players"]]


async def listed_in(
    client, session_factory, clock, sport: Sport, *levels: tuple[str, float]
) -> list[dict]:
    """Players listed in ``sport`` alone, each at the Level paired with their
    name: a Level filed in the sport, then five results there settled eight
    days ago — so nobody is *New* — and the outbox delivered. Their ids, tokens
    and nicknames, in the order given."""

    cast = []
    for name, level in levels:
        # The log files a Level in the players' own sport, padel, as it is.
        player_id, token = await players.a_player_on_the_log(
            client, session_factory, name, mu=level, intent=None
        )
        if sport is not players.SPORT:
            await players.rate_in(session_factory, player_id, sport, mu=level)
        cast.append({"id": player_id, "token": token, "nickname": name})
    settled = instant(clock.now() - timedelta(days=8))
    async with session_factory() as session:
        for (_, level), player in zip(levels, cast, strict=True):
            for result in range(5):
                await move_on(
                    session,
                    player["id"],
                    level,
                    at=instant(settled + timedelta(minutes=result)),
                    sport=sport,
                )
    await deliver_the_outbox(session_factory, rounds=len(cast))
    return cast


@pytest.fixture
async def stranger(client) -> dict:
    """A rated padel player with no result anywhere — listed nowhere."""

    return await players.a_rated_player(client, "tomek")


# --------------------------------------------------------------------------- #
# The first ten of General
# --------------------------------------------------------------------------- #


async def test_the_row_is_the_first_ten_of_general_in_place_order(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, 12)
    reader = crowd[11]

    read = await top_ten(client, reader, sport="PADEL")
    general = await ranking(client, reader)

    assert (read["sport"], read["anyone_listed"]) == ("PADEL", True)
    assert places(read) == list(range(1, 11))
    assert nicknames(read) == [f"crowd{n:03d}" for n in range(10)]
    assert read["players"][0] == {
        "place": 1,
        "player_id": str(crowd[0]["id"]),
        "nickname": "crowd000",
        "photo_id": None,
        "photo_url": None,
        "level": 6.0,
        "chip": None,
        "is_you": False,
    }
    assert [
        (one["place"], one["player_id"], one["nickname"], one["level"])
        for one in read["players"]
    ] == [
        (row["place"], row["player_id"], row["nickname"], row["level"])
        for row in general["rows"][:10]
    ]


async def test_the_readers_own_card_is_marked_among_the_ten(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, 12)

    read = await top_ten(client, crowd[3], sport="PADEL")

    assert [one["is_you"] for one in read["players"]] == [n == 3 for n in range(10)]
    assert read["players"][3]["nickname"] == "crowd003"


async def test_a_sport_with_one_or_two_listed_shows_those_cards(
    client, session_factory, clock, stranger
):
    await listed_in(client, session_factory, clock, Sport.SQUASH, ("kuba", 3.2))

    one = await top_ten(client, stranger, sport="SQUASH")

    assert (one["sport"], nicknames(one), places(one)) == ("SQUASH", ["kuba"], [1])

    await listed_in(client, session_factory, clock, Sport.SQUASH, ("zofia", 3.5))
    two = await top_ten(client, stranger, sport="SQUASH")

    assert (nicknames(two), places(two)) == (["zofia", "kuba"], [1, 2])
    assert [one["level"] for one in two["players"]] == [3.5, 3.2]


async def test_an_asked_sport_with_nobody_listed_is_empty_and_somebody_is_listed_elsewhere(  # noqa: E501
    client, session_factory, clock, stranger
):
    await listed_in(client, session_factory, clock, Sport.SQUASH, ("kuba", 3.2))

    read = await top_ten(client, stranger, sport="BADMINTON")

    assert read == {"sport": "BADMINTON", "anyone_listed": True, "players": []}


async def test_nobody_listed_anywhere_says_so_and_names_the_sport_it_was_asked_for(
    client, session_factory, clock, stranger
):
    # Four results in squash: one short of General.
    await players.rate_in(session_factory, stranger["id"], Sport.SQUASH, mu=3.0)
    async with session_factory() as session:
        for result in range(4):
            await move_on(
                session,
                stranger["id"],
                3.0,
                at=instant(clock.now() - timedelta(hours=result + 1)),
                sport=Sport.SQUASH,
            )
    await deliver_the_outbox(session_factory)

    preferred = await top_ten(client, stranger, prefer="PADEL")
    asked = await top_ten(client, stranger, sport="SQUASH")

    assert preferred == {"sport": "PADEL", "anyone_listed": False, "players": []}
    assert asked == {"sport": "SQUASH", "anyone_listed": False, "players": []}


# --------------------------------------------------------------------------- #
# Which sport, when one is preferred
# --------------------------------------------------------------------------- #


async def test_a_preferred_sport_with_somebody_listed_is_the_one_shown(
    client, session_factory, clock, stranger
):
    await listed_in(client, session_factory, clock, Sport.PADEL, ("ines", 3.4))
    await listed_in(client, session_factory, clock, Sport.SQUASH, ("kuba", 3.2))

    read = await top_ten(client, stranger, prefer="SQUASH")

    assert (read["sport"], nicknames(read)) == ("SQUASH", ["kuba"])


@pytest.mark.parametrize(
    ("preferred", "shown"),
    [
        # Forward to the next sport with anybody — never back to padel.
        ("TENNIS", "SQUASH"),
        # Past the last sport, round to the first.
        ("BADMINTON", "PADEL"),
    ],
)
async def test_a_preferred_sport_with_nobody_listed_falls_through_in_the_apps_order(
    client, session_factory, clock, stranger, preferred, shown
):
    await listed_in(client, session_factory, clock, Sport.PADEL, ("ines", 3.4))
    await listed_in(client, session_factory, clock, Sport.SQUASH, ("kuba", 3.2))

    read = await top_ten(client, stranger, prefer=preferred)

    assert (read["sport"], read["anyone_listed"]) == (shown, True)
    assert nicknames(read) == {"PADEL": ["ines"], "SQUASH": ["kuba"]}[shown]


# --------------------------------------------------------------------------- #
# The chip
# --------------------------------------------------------------------------- #


async def test_a_card_draws_the_weeks_move_and_no_chip_for_no_change_or_new(
    client, session_factory, clock
):
    """Karol overtakes Tomek this week — ▲1 and ▼1. Ines and Zofia didn't
    move, and Ewa's fifth result has just listed her: the Rankings page reads
    them *—* and *New*, and their cards draw no chip."""

    tomek, karol, zofia, ines, ewa = [
        await players.a_rated_player(client, name)
        for name in ("tomek", "karol", "zofia", "ines", "ewa")
    ]
    for player, level in ((ines, 3.40), (tomek, 2.71), (karol, 2.70), (zofia, 2.69)):
        await results_at(session_factory, player, [level] * 5, clock)
    await results_at(session_factory, ewa, [2.60] * 4, clock)
    clock.move(timedelta(days=8))
    await moves_to(session_factory, karol, 2.75, at=instant(clock.now()))
    await moves_to(session_factory, ewa, 2.61, at=instant(clock.now()))

    read = await top_ten(client, tomek, sport="PADEL")
    page = await ranking(client, tomek)

    assert {one["nickname"]: one["chip"] for one in read["players"]} == {
        "ines": None,
        "karol": UP_1,
        "tomek": DOWN_1,
        "zofia": None,
        "ewa": None,
    }
    assert {row["nickname"]: row["chip"]["kind"] for row in page["rows"]} == {
        "ines": "SAME",
        "karol": "UP",
        "tomek": "DOWN",
        "zofia": "SAME",
        "ewa": "NEW",
    }


# --------------------------------------------------------------------------- #
# The real ranking, off the kept order
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("blocker", ["reader", "leader"])
async def test_a_blocked_pair_see_each_other_in_top_ten(
    client, session_factory, clock, blocker
):
    crowd = await a_listed_crowd(client, session_factory, clock, 12)
    for player in crowd:
        player["headers"] = players.auth(player["token"])
    reader, leader = crowd[5], crowd[0]
    if blocker == "reader":
        await blocks(client, reader, leader)
    else:
        await blocks(client, leader, reader)
    await deliver_the_outbox(session_factory)

    for one in (reader, leader):
        read = await top_ten(client, one, sport="PADEL")
        assert places(read) == list(range(1, 11))
        assert {"crowd000", "crowd005"} <= set(nicknames(read))


async def test_the_row_reads_the_kept_order_and_sees_a_result_on_the_next_read(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, 12)
    reader = crowd[11]

    first = await top_ten(client, reader, sport="PADEL")
    kept = await kept_orders_of(session_factory).held(Sport.PADEL)

    assert kept is not None
    assert [str(row.player_id) for row in await kept.rows(0, 10)] == [
        one["player_id"] for one in first["players"]
    ]

    # Twelfth to first: the write forgets the kept order, and the next read
    # works it out again.
    await moves_to(session_factory, reader, 7.0, at=instant(clock.now()))
    again = await top_ten(client, reader, sport="PADEL")

    assert again["players"][0]["nickname"] == "crowd011"
    assert again["players"][0]["is_you"] is True
    assert nicknames(again)[1:] == [f"crowd{n:03d}" for n in range(9)]


# --------------------------------------------------------------------------- #
# What is refused
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "params", [{}, {"sport": "PADEL", "prefer": "TENNIS"}], ids=["neither", "both"]
)
async def test_one_sport_is_asked_for_or_preferred_and_never_both_or_neither(
    client, stranger, params
):
    read = await client.get(
        "/api/v1/top-10", params=params, headers=players.auth(stranger["token"])
    )

    assert read.status_code == 400, read.text
    assert read.json()["code"] == "not_one_sport"


async def test_an_unknown_sport_is_refused(client, stranger):
    read = await client.get(
        "/api/v1/top-10",
        params={"sport": "CURLING"},
        headers=players.auth(stranger["token"]),
    )

    assert read.status_code == 422, read.text


async def test_the_row_is_read_signed_in(client):
    read = await client.get("/api/v1/top-10", params={"prefer": "PADEL"})

    assert read.status_code == 401
