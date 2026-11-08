"""General in pages of 50, read the way the player app reads them (#770;
``docs/adr/0203`` §10; the screens §5.3).

**Every page is a slice of one order**, worked out in one pass and kept for at
most a minute: after a cursor, before one, or around the reader, each page
with the cursors either side, and the main read's first page the same as the
rows read with no cursor. **A ranking write forgets the kept order**, so a
result settling is seen on the next read; **the minute is the read's own
clock**, so a player crossing 90 days drops off within it — every claim here
is read off the player routes, the clock moved.
"""

from __future__ import annotations

import base64
from datetime import timedelta

from sqlalchemy import delete

from app.kernel import instant
from app.modules.rankings.domain.general_order import ORDER_KEPT_FOR
from app.modules.rankings.domain.ranking import LISTED_FOR, PAGE_SIZE
from app.modules.rankings.infrastructure.ranking_model import RankingRowORM
from tests.api import players_world as players
from tests.api.rankings_world import (
    a_listed_crowd,
    general_rows,
    moves_to,
    places,
    ranking,
)

LISTED = 120


def _span(first: int, last: int) -> list[int]:
    return list(range(first, last + 1))


async def test_pages_of_fifty_either_way_and_around_the_reader(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, LISTED)
    tomek = crowd[74]

    main = await ranking(client, tomek)
    first = await general_rows(client, tomek)
    # The first page is the main read's, row for row, chips and all.
    assert first["rows"] == main["rows"]
    assert places(first) == _span(1, PAGE_SIZE)
    assert (first["listed"], main["listed"]) == (LISTED, LISTED)
    assert first["previous"] is None
    assert first["next"] == main["next"] is not None
    assert {row["chip"]["kind"] for row in first["rows"]} == {"SAME"}

    second = await general_rows(client, tomek, after=first["next"])
    third = await general_rows(client, tomek, after=second["next"])
    assert places(second) == _span(51, 100)
    assert places(third) == _span(101, LISTED)
    assert third["next"] is None
    assert [row["nickname"] for row in second["rows"]] == [
        player["nickname"] for player in crowd[50:100]
    ]

    # And back up, from the bottom.
    back = await general_rows(client, tomek, before=third["previous"])
    top = await general_rows(client, tomek, before=back["previous"])
    assert back["rows"] == second["rows"]
    assert places(top) == _span(1, PAGE_SIZE) and top["previous"] is None

    # Around the reader: 75th has 25 rows above and 24 below...
    around = await general_rows(client, tomek, around_me=True)
    assert places(around) == _span(50, 99)
    assert [row["is_you"] for row in around["rows"]].index(True) == PAGE_SIZE // 2
    # ...and the reads go either way from there.
    assert places(await general_rows(client, tomek, after=around["next"])) == (
        _span(100, LISTED)
    )
    assert places(await general_rows(client, tomek, before=around["previous"])) == (
        _span(1, 49)
    )
    # At the top and the bottom, the page is held to the list's ends.
    assert places(await general_rows(client, crowd[9], around_me=True)) == _span(
        1, PAGE_SIZE
    )
    bottom = await general_rows(client, crowd[109], around_me=True)
    assert places(bottom) == _span(71, LISTED) and bottom["next"] is None


async def test_around_a_reader_who_is_not_listed_is_the_first_page(
    client, session_factory, clock
):
    await a_listed_crowd(client, session_factory, clock, 3)
    stranger = await players.a_rated_player(client, "stranger")

    read = await general_rows(client, stranger, around_me=True)

    assert places(read) == [1, 2, 3]
    assert (read["previous"], read["next"]) == (None, None)
    assert not any(row["is_you"] for row in read["rows"])
    assert read["rows"] == (await ranking(client, stranger))["rows"] != []


async def test_a_page_is_not_asked_for_in_two_places_or_with_a_made_up_cursor(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, 2)
    cursor = (await general_rows(client, crowd[0]))["rows"] and (
        await ranking(client, crowd[0])
    )["next"]
    assert cursor is None  # two rows are one page

    def forged(written: str) -> str:
        return base64.urlsafe_b64encode(written.encode()).decode().rstrip("=")

    player = crowd[0]["id"].hex
    for params in (
        {"after": "bm90LWEtY3Vyc29y"},
        {"before": "!!"},
        {"after": "MS4yLjM", "around_me": True},
        # Past every instant there is, a Level below nought, more results than
        # a key holds, and before the epoch: no row stands at any of them.
        {"after": forged(f"300.5.{10**18}.{player}")},
        {"after": forged(f"-1.5.0.{player}")},
        {"before": forged(f"300.{10**10}.0.{player}")},
        {"before": forged(f"300.5.-1.{player}")},
    ):
        refused = await client.get(
            "/api/v1/rankings/PADEL/general/rows",
            params=params,
            headers=players.auth(crowd[0]["token"]),
        )
        assert refused.status_code == 400, params
        assert refused.json()["code"] == "not_a_ranking_page"


async def test_a_result_settling_is_seen_on_the_next_read(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, 4)
    last = crowd[3]
    assert places(await general_rows(client, last)) == [1, 2, 3, 4]

    # The last one wins up past everybody, this instant: the kept order is
    # forgotten by the write, so the next read — inside the minute — has it.
    await moves_to(session_factory, last, 6.5, at=instant(clock.now()))

    read = await general_rows(client, last)
    assert [row["nickname"] for row in read["rows"]][0] == last["nickname"]
    assert (await ranking(client, crowd[0]))["card"]["place"] == 2


async def test_an_order_is_kept_for_a_minute(client, session_factory, clock):
    crowd = await a_listed_crowd(client, session_factory, clock, 3)
    assert (await ranking(client, crowd[0]))["listed"] == 3

    # Rows gone behind the write path's back: the kept order is still read...
    async with session_factory() as session:
        await session.execute(
            delete(RankingRowORM).where(RankingRowORM.player_id == crowd[2]["id"])
        )
        await session.commit()
    clock.move(ORDER_KEPT_FOR - timedelta(seconds=1))
    assert (await ranking(client, crowd[0]))["listed"] == 3

    # ...and a minute after it was worked out it is worked out again.
    clock.move(timedelta(seconds=1))
    assert (await ranking(client, crowd[0]))["listed"] == 2


async def test_a_player_crossing_ninety_days_drops_off_within_a_minute(
    client, session_factory, clock
):
    crowd = await a_listed_crowd(client, session_factory, clock, 3)
    reader, leaving = crowd[0], crowd[2]
    # Everybody but the one leaving plays again today.
    for player in crowd[:2]:
        await moves_to(session_factory, player, 6.0, at=instant(clock.now()))
    # Their last result settled eight days ago, at the fourth minute.
    crosses = instant(clock.now() - timedelta(days=8) + timedelta(minutes=4))
    crosses = instant(crosses + LISTED_FOR)

    clock.move(crosses - timedelta(seconds=30) - clock.now())
    assert (await ranking(client, reader))["listed"] == 3

    # Crossed twenty seconds ago, and the order read was worked out fifty
    # seconds ago: still listed, for the rest of that minute.
    clock.move(timedelta(seconds=50))
    assert (await ranking(client, reader))["listed"] == 3
    # A minute after it was worked out, the next read drops them.
    clock.move(timedelta(seconds=10))
    read = await ranking(client, reader)
    assert read["listed"] == 2
    assert leaving["nickname"] not in [row["nickname"] for row in read["rows"]]
    assert (await ranking(client, leaving))["card"]["state"] == "OFF_THE_LIST"
