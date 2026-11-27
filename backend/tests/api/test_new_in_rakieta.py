"""Home's *New in Rakieta* row and its See all — over HTTP, as the player app
calls them (#793; the home-rows mechanics §7, ``docs/adr/0204`` §5, §10).

**Tomek** joined long ago and reads his Home. **Bartek** signed up 2 days ago
with padel 2,35 and badminton 2,10; **Ola** yesterday, with no level at all;
both are on Tomek's row, Ola first. **Filip**, a joiner already Tomek's
friend, waits at the back. See all lists every joiner of the month, filtered
by sport. Anyone Tomek adds from the row reads *Found you among new players*.

**Players sign up at moved clocks**: the clock starts weeks back and steps
forward to each sign-up, then to *now*. The directory is fed through the
outbox, so each read follows a delivery, as the worker would have made it.
Levels are filed on the rating's log (``players.rate_in``), the one fact a
questionnaire doesn't take dictation for; the rows read them live.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import delete, select

from app.bootstrap.composition import build_rebuild_the_directory
from app.kernel import Sport
from app.modules.discovery.infrastructure.directory_model import (
    DirectoryPlayerORM,
    DirectoryTagORM,
)
from tests.api import players_world as players
from tests.api.discovery_world import a_crowd

ROW = "/api/v1/new-in-rakieta"
ALL = "/api/v1/new-in-rakieta/all"
REQUESTS = "/api/v1/friends/requests"
NOTICES = "/api/v1/players/me/notices"


async def a_player(client, name: str, **profile) -> dict:
    """Signed up, named and through onboarding — *joined* at the clock's now."""

    player_id, token = await players.register(client, name)
    await players.commit_profile(client, token, **profile)
    return {"id": player_id, "token": token, "headers": players.auth(token)}


async def whole_row(client, mailbox, reader: dict) -> dict:
    await mailbox.drain()
    read = await client.get(ROW, headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def row(client, mailbox, reader: dict) -> list[dict]:
    return (await whole_row(client, mailbox, reader))["players"]


async def total(client, mailbox, reader: dict) -> int:
    return (await whole_row(client, mailbox, reader))["total"]


async def see_all(client, mailbox, reader: dict, **params) -> dict:
    await mailbox.drain()
    read = await client.get(ALL, params=params, headers=reader["headers"])
    assert read.status_code == 200, read.text
    return read.json()


def names(cards: list[dict]) -> list[str]:
    return [card["nickname"] for card in cards]


async def asks(client, requester: dict, addressee: dict, *, made_from="RECORD", **body):
    asked = await client.post(
        REQUESTS,
        json={"player_id": str(addressee["id"]), "made_from": made_from} | body,
        headers=requester["headers"],
    )
    assert asked.status_code == 200, asked.text
    return asked


async def accepts(client, reader: dict, requester: dict) -> None:
    accepted = await client.post(
        f"{REQUESTS}/{requester['id']}/acceptance", headers=reader["headers"]
    )
    assert accepted.status_code == 200, accepted.text


async def blocks(client, blocker: dict, blocked: dict) -> None:
    made = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"])},
        headers=blocker["headers"],
    )
    assert made.status_code == 204, made.text


async def switches(client, player: dict, *, on: bool) -> None:
    turned = await client.put(
        "/api/v1/players/me/show-me-to-new-people",
        json={"on": on},
        headers=player["headers"],
    )
    assert turned.status_code == 204, turned.text


@pytest.fixture
async def tomek(client, clock) -> dict:
    """Joined 60 days ago: on nobody's row, and the reader of every test. The
    clock is left 60 days back, for each test to walk forward."""

    clock.move(-timedelta(days=60))
    return await a_player(client, "tomek")


class Walk:
    """The test's clock, walked forward from 60 days back to *now*."""

    def __init__(self, clock) -> None:
        self._clock = clock
        self._back = timedelta(days=60)

    def to(self, before_now: timedelta) -> None:
        forward = self._back - before_now
        assert forward >= timedelta(0), "the walk only goes forward"
        self._clock.move(forward)
        self._back = before_now

    def to_now(self) -> None:
        self.to(timedelta(0))


@pytest.fixture
def walk(clock, tomek) -> Walk:
    return Walk(clock)


async def joins(client, walk: Walk, name: str, *, days: float, **profile) -> dict:
    walk.to(timedelta(days=days))
    return await a_player(client, name, **profile)


# --------------------------------------------------------------------------- #
# Who: the last 30 days, strictly
# --------------------------------------------------------------------------- #


async def test_bartek_and_ola_are_on_tomeks_row_ola_first(
    client, mailbox, session_factory, walk, tomek
):
    bartek = await joins(client, walk, "bartek", days=2)
    ola = await joins(client, walk, "ola", days=1)
    walk.to_now()
    await players.rate_in(session_factory, bartek["id"], Sport.PADEL, mu=2.35)
    await players.rate_in(session_factory, bartek["id"], Sport.BADMINTON, mu=2.10)

    read = await whole_row(client, mailbox, tomek)
    cards = read["players"]

    assert names(cards) == ["ola", "bartek"]
    # Bartek holds two sports, and is counted once.
    assert read["total"] == 2
    ola_card, bartek_card = cards
    assert ola_card["player_id"] == str(ola["id"])
    assert ola_card["days_since_joined"] == 1
    assert ola_card["sports"] == []
    assert ola_card["relation"] == "NONE"
    assert ola_card["photo_id"] is None and ola_card["photo_url"] is None
    assert bartek_card["days_since_joined"] == 2
    assert bartek_card["sports"] == [
        {"sport": "PADEL", "level": 2.35},
        {"sport": "BADMINTON", "level": 2.10},
    ]


async def test_new_is_strictly_the_last_30_days(client, mailbox, clock, walk, tomek):
    walk.to(timedelta(days=35))
    await a_player(client, "old")
    walk.to(timedelta(days=30))
    await a_player(client, "edge")
    walk.to(timedelta(days=30) - timedelta(minutes=1))
    await a_player(client, "inside")
    walk.to_now()

    assert names(await row(client, mailbox, tomek)) == ["inside"]

    clock.move(timedelta(minutes=1))
    assert await row(client, mailbox, tomek) == []
    assert (await see_all(client, mailbox, tomek))["players"] == []


async def test_joined_counts_warsaw_days(client, mailbox, clock, walk, tomek):
    """*Joined today* is the Warsaw day of the commit, whatever the hours since
    (the words §31.7)."""

    await joins(client, walk, "ania", days=0)
    walk.to_now()
    [card] = await row(client, mailbox, tomek)
    assert card["days_since_joined"] == 0

    clock.move(timedelta(days=13))
    [card] = await row(client, mailbox, tomek)
    assert card["days_since_joined"] == 13


async def test_a_player_who_never_finished_sign_up_is_on_no_row(
    client, mailbox, walk, tomek
):
    """Signed up and named, no profile: an account that doesn't play — as an
    administrator-only account is."""

    walk.to(timedelta(days=3))
    await players.register(client, "halfway")
    await a_player(client, "kasia")
    walk.to_now()

    assert names(await row(client, mailbox, tomek)) == ["kasia"]


# --------------------------------------------------------------------------- #
# The row of 10, and See all
# --------------------------------------------------------------------------- #


async def test_ten_newest_on_the_row_and_every_joiner_in_pages_of_twenty(
    client, mailbox, walk, tomek
):
    for n in range(25):
        await joins(client, walk, f"new{n:02d}", days=25 - n)
    walk.to_now()
    newest_first = [f"new{n:02d}" for n in reversed(range(25))]

    assert names(await row(client, mailbox, tomek)) == newest_first[:10]

    first = await see_all(client, mailbox, tomek)
    assert names(first["players"]) == newest_first[:20]
    assert first["next"] is not None
    second = await see_all(client, mailbox, tomek, after=first["next"])
    assert names(second["players"]) == newest_first[20:]
    assert second["next"] is None


async def test_an_eleventh_sign_up_pushes_the_oldest_off_the_row(
    client, mailbox, walk, tomek
):
    for n in range(10):
        await joins(client, walk, f"new{n:02d}", days=20 - n)
    assert "new00" in names(await row(client, mailbox, tomek))

    await joins(client, walk, "eleventh", days=1)
    walk.to_now()
    cards = names(await row(client, mailbox, tomek))

    assert cards[0] == "eleventh" and "new00" not in cards and len(cards) == 10
    assert "new00" in names((await see_all(client, mailbox, tomek))["players"])


async def test_unconnected_first_then_sent_then_friends_newest_first_in_each(
    client, mailbox, walk, tomek
):
    filip = await joins(client, walk, "filip", days=9)
    asked_him = await joins(client, walk, "magda", days=8)
    sent = await joins(client, walk, "piotr", days=7)
    await joins(client, walk, "zosia", days=6)
    friend = await joins(client, walk, "karol", days=5)
    await joins(client, walk, "ewa", days=4)
    walk.to_now()
    await asks(client, filip, tomek)
    await accepts(client, tomek, filip)
    await asks(client, friend, tomek)
    await accepts(client, tomek, friend)
    await asks(client, tomek, sent, made_from="NEW_PLAYERS")
    await asks(client, asked_him, tomek)

    cards = await row(client, mailbox, tomek)

    assert names(cards) == ["ewa", "zosia", "magda", "piotr", "karol", "filip"]
    assert [card["relation"] for card in cards] == [
        "NONE",
        "NONE",
        "ASKED_YOU",
        "SENT",
        "FRIEND",
        "FRIEND",
    ]
    # See all: plain newest first, friends where they fall.
    assert names((await see_all(client, mailbox, tomek))["players"]) == [
        "ewa",
        "karol",
        "zosia",
        "piotr",
        "magda",
        "filip",
    ]


async def test_a_cursor_this_server_never_wrote_is_refused(client, tomek):
    refused = await client.get(
        ALL, params={"after": "not-a-cursor"}, headers=tomek["headers"]
    )

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "not_a_new_in_rakieta_page"


# --------------------------------------------------------------------------- #
# The sport pill
# --------------------------------------------------------------------------- #


async def test_a_sport_keeps_only_joiners_rated_in_it_and_the_pill_offers_theirs(
    client, mailbox, session_factory, walk, tomek
):
    bartek = await joins(client, walk, "bartek", days=3)
    await joins(client, walk, "ola", days=2)
    kasia = await joins(client, walk, "kasia", days=1)
    walk.to_now()
    await players.rate_in(session_factory, bartek["id"], Sport.BADMINTON, mu=2.10)
    await players.rate_in(session_factory, bartek["id"], Sport.PADEL, mu=2.35)
    await players.rate_in(session_factory, kasia["id"], Sport.TENNIS, mu=3.10)

    everyone = await see_all(client, mailbox, tomek)
    tennis = await see_all(client, mailbox, tomek, sport="TENNIS")
    squash = await see_all(client, mailbox, tomek, sport="SQUASH")

    assert names(everyone["players"]) == ["kasia", "ola", "bartek"]
    assert everyone["sports"] == ["PADEL", "TENNIS", "BADMINTON"]
    assert names(tennis["players"]) == ["kasia"]
    assert tennis["sports"] == everyone["sports"]
    assert squash["players"] == [] and squash["next"] is None


# --------------------------------------------------------------------------- #
# Who is never on it
# --------------------------------------------------------------------------- #


async def test_never_the_reader_a_block_either_way_or_a_switched_off_player(
    client, mailbox, walk, tomek
):
    blocked = await joins(client, walk, "blocked", days=5)
    blocker = await joins(client, walk, "blocker", days=4)
    hidden = await joins(client, walk, "hidden", days=3)
    await joins(client, walk, "seen", days=2)
    reader = await joins(client, walk, "reader", days=1)
    walk.to_now()
    await blocks(client, reader, blocked)
    await blocks(client, blocker, reader)
    await switches(client, hidden, on=False)

    assert names(await row(client, mailbox, reader)) == ["seen"]
    assert names((await see_all(client, mailbox, reader))["players"]) == ["seen"]
    # Tomek is in no block: he sees all but the switched-off player.
    assert names(await row(client, mailbox, tomek)) == [
        "reader",
        "seen",
        "blocker",
        "blocked",
    ]

    await switches(client, hidden, on=True)
    assert "hidden" in names(await row(client, mailbox, tomek))


# --------------------------------------------------------------------------- #
# The total: everybody new, counted up to 100 (#812)
# --------------------------------------------------------------------------- #


async def test_the_total_counts_the_month_under_the_rows_own_exclusions(
    client, mailbox, walk, tomek
):
    walk.to(timedelta(days=35))
    await a_player(client, "old")
    walk.to(timedelta(days=30))
    await a_player(client, "edge")
    blocked = await joins(client, walk, "blocked", days=5)
    blocker = await joins(client, walk, "blocker", days=4)
    hidden = await joins(client, walk, "hidden", days=3)
    await joins(client, walk, "seen", days=2)
    walk.to(timedelta(days=1))
    await players.register(client, "halfway")
    reader = await a_player(client, "reader")
    walk.to_now()
    await blocks(client, reader, blocked)
    await blocks(client, blocker, reader)
    await switches(client, hidden, on=False)

    # Neither the reader, a block either way, the switched off, the one who
    # never finished sign-up, nor anybody 30 days in.
    assert await total(client, mailbox, reader) == 1
    assert await total(client, mailbox, tomek) == 4

    await switches(client, hidden, on=True)
    assert await total(client, mailbox, tomek) == 5


async def test_an_empty_month_totals_nought(client, mailbox, tomek):
    assert await whole_row(client, mailbox, tomek) == {"players": [], "total": 0}


async def test_the_total_stops_at_100_and_the_row_and_see_all_stand(
    client, mailbox, session_factory, clock, walk, tomek
):
    walk.to_now()
    yesterday = clock.now() - timedelta(days=1)
    await a_crowd(session_factory, 99, joined_at=yesterday)
    assert await total(client, mailbox, tomek) == 99

    await a_crowd(session_factory, 1, joined_at=yesterday, named="hundredth")
    assert await total(client, mailbox, tomek) == 100

    await a_crowd(session_factory, 5, joined_at=yesterday, named="more")
    read = await whole_row(client, mailbox, tomek)
    assert read["total"] == 100
    assert len(read["players"]) == 10
    assert len((await see_all(client, mailbox, tomek))["players"]) == 20


async def test_the_count_from_ten_leaves_out_who_the_row_leaves_out(
    client, mailbox, session_factory, clock, walk, tomek
):
    """Ten new yesterday fill the row, so the month is counted — and the count
    holds the row's own exclusions, which the row's ten never test."""

    walk.to(timedelta(days=35))
    await a_player(client, "old")
    walk.to(timedelta(days=30))
    await a_player(client, "edge")
    blocked = await joins(client, walk, "blocked", days=5)
    blocker = await joins(client, walk, "blocker", days=4)
    hidden = await joins(client, walk, "hidden", days=3)
    await joins(client, walk, "seen", days=2)
    await players.register(client, "halfway")
    walk.to_now()
    await blocks(client, tomek, blocked)
    await blocks(client, blocker, tomek)
    await switches(client, hidden, on=False)
    await a_crowd(session_factory, 6, joined_at=clock.now() - timedelta(days=40))
    await a_crowd(
        session_factory, 10, joined_at=clock.now() - timedelta(days=1), named="new"
    )

    read = await whole_row(client, mailbox, tomek)

    assert len(read["players"]) == 10
    assert "seen" not in names(read["players"])
    # The ten and Seen: nobody blocked either way, switched off, half signed
    # up, 30 days in or older.
    assert read["total"] == 11


async def test_the_total_is_free_below_ten_and_one_count_from_ten(
    client, mailbox, session_factory, clock, statements, walk, tomek
):
    """**At most one statement more** than the row read before its total.
    Every statement a total could cost is the directory's — the neighbours'
    (the session, the blocks, Friends, the rating) are the cards', and move
    with their owners — and the row read the directory once: ``who_joined``."""

    walk.to_now()
    yesterday = clock.now() - timedelta(days=1)
    await a_crowd(session_factory, 9, joined_at=yesterday)
    await mailbox.drain()
    with statements.counting() as nine:
        assert (await client.get(ROW, headers=tomek["headers"])).json()["total"] == 9

    await a_crowd(session_factory, 3, joined_at=yesterday, named="later")
    with statements.counting() as twelve:
        assert (await client.get(ROW, headers=tomek["headers"])).json()["total"] == 12

    assert len(nine.naming("discovery_players")) == 1
    the_row, the_count = twelve.naming("discovery_players")
    assert the_row == nine.naming("discovery_players")[0]
    assert "count(" in the_count.lower() and "joined_at" in the_count


# --------------------------------------------------------------------------- #
# A request from the row
# --------------------------------------------------------------------------- #


async def test_a_request_from_the_row_reads_found_you_among_new_players(
    client, mailbox, walk, tomek
):
    bartek = await joins(client, walk, "bartek", days=2)
    walk.to_now()

    # A group and a sport sent with it are dropped: the line names neither.
    asked = await asks(
        client,
        tomek,
        bartek,
        made_from="NEW_PLAYERS",
        group_id=str(bartek["id"]),
        sport="PADEL",
    )
    [card] = await row(client, mailbox, tomek)
    [request] = (await client.get("/api/v1/home", headers=bartek["headers"])).json()[
        "friend_requests"
    ]
    [notice] = (await client.get(NOTICES, headers=bartek["headers"])).json()["notices"]

    assert asked.json()["relation"] == "SENT"
    assert card["relation"] == "SENT"
    assert request["player_id"] == str(tomek["id"])
    assert request["from_new_players"] is True
    assert request["from_ranking"] is False
    assert request["group"] is None
    assert request["sport"] is None
    assert notice["kind"] == "FRIEND_REQUEST"
    assert notice["body"] == "Found you among new players"


async def test_a_request_from_anywhere_else_is_not_from_new_players(
    client, mailbox, walk, tomek
):
    bartek = await joins(client, walk, "bartek", days=2)
    walk.to_now()

    await asks(client, tomek, bartek)
    await mailbox.drain()
    [request] = (await client.get("/api/v1/home", headers=bartek["headers"])).json()[
        "friend_requests"
    ]

    assert request["from_new_players"] is False


# --------------------------------------------------------------------------- #
# The directory
# --------------------------------------------------------------------------- #


async def stored_directory(session_factory) -> tuple[list, list]:
    async with session_factory() as session:
        entries = (
            await session.execute(
                select(DirectoryPlayerORM).order_by(DirectoryPlayerORM.player_id)
            )
        ).scalars()
        rows = [
            (
                entry.player_id,
                entry.nickname,
                entry.plays,
                entry.joined_at,
                entry.photo_id,
                entry.area_latitude,
                entry.area_longitude,
                entry.open_to_new_people,
            )
            for entry in entries
        ]
        tags = (
            await session.execute(
                select(DirectoryTagORM.player_id, DirectoryTagORM.tag).order_by(
                    DirectoryTagORM.player_id, DirectoryTagORM.tag
                )
            )
        ).all()
    return rows, [tuple(tag) for tag in tags]


async def test_the_rebuild_writes_what_live_delivery_wrote_and_twice_changes_nothing(
    client, mailbox, session_factory, walk, tomek
):
    bartek = await joins(client, walk, "bartek", days=3)
    ola = await joins(
        client,
        walk,
        "ola",
        days=2,
        location={"latitude": 50.06, "longitude": 19.94},
    )
    await players.register(client, "halfway")
    walk.to_now()
    changed = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": ["PLAYS_TO_WIN", "OPEN_TO_MEET_SOMEONE"]},
        headers=bartek["headers"],
    )
    assert changed.status_code == 200, changed.text
    await switches(client, ola, on=False)
    await mailbox.drain()
    live = await stored_directory(session_factory)
    live_row = await row(client, mailbox, tomek)
    assert len(live[0]) == 4  # tomek, bartek, ola, and halfway who doesn't play

    # Today's players, before the directory shipped: nobody on any row.
    async with session_factory() as session:
        await session.execute(delete(DirectoryTagORM))
        await session.execute(delete(DirectoryPlayerORM))
        await session.commit()
    assert await row(client, mailbox, tomek) == []

    for _ in range(2):
        async with session_factory() as session:
            rebuilt = await build_rebuild_the_directory(session).execute()
        assert (rebuilt.accounts, rebuilt.entries) == (4, 4)
        assert await stored_directory(session_factory) == live

    assert await row(client, mailbox, tomek) == live_row
