"""*Groups heating up*: Hottest groups' total, and every group in the row's
order, page by page — over HTTP, as the player app calls them (#813;
``docs/adr/0205`` §6, §7; the Home rows mechanics §5.10).

Tomek's FOR YOU line reads *Groups heating up · 8*; **All groups ›** opens the
page, which lists every group of three or more — his own among them — in the
row's one order, twenty at a time, the row being its first six.

The order's tie-breaks are walked on groups made, joined and played over HTTP,
as ``test_hottest_groups`` makes them. Paging and the cap need dozens of
groups, so those are written straight into the projections
(``groups_world``), where nobody is new and nobody played: each group's heat is
its players.
"""

from __future__ import annotations

import base64
from datetime import timedelta
from uuid import uuid4

import pytest

from tests.api.groups_world import groups_at, resize
from tests.api.test_groups import a_club, a_group, a_player, join
from tests.api.test_hottest_groups import (
    HOTTEST,
    a_group_of,
    games_in,
    joins,
    people,
)

PAGE = f"{HOTTEST}/all"


async def row_of(client, player: dict) -> dict:
    read = await client.get(HOTTEST, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def page_of(client, player: dict, after: str | None = None) -> dict:
    read = await client.get(
        PAGE,
        params={} if after is None else {"after": after},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def every_page(client, player: dict) -> list[dict]:
    pages = [await page_of(client, player)]
    while pages[-1]["next"] is not None:
        pages.append(await page_of(client, player, pages[-1]["next"]))
    return pages


def ids(cards: list[dict]) -> list[str]:
    return [card["id"] for card in cards]


@pytest.fixture
async def club(client):
    return await a_club(client, "Ogrody 33")


@pytest.fixture
async def tomek(client):
    return await a_player(client, "tomek")


# --------------------------------------------------------------------------- #
# The order
# --------------------------------------------------------------------------- #


async def test_every_group_of_three_in_the_row_s_order_and_its_tie_breaks(
    client, session_factory, clock, club, tomek
):
    """Hot (4 new, 2 games) = 4 + 12 + 4 = 20, HOTTEST; two GROWING at 16, tied
    in heat and games, by id; untagged: *Old 4 played* (4 players, a game) and
    *Old 6* tie at 6, the game first; *Old 5*; two *Old 3* by id; and a group of
    two left out."""

    old = await people(client, *(f"old{n}" for n in range(6)))
    new = await people(client, *(f"new{n}" for n in range(4)))
    old_6 = await a_group_of(client, old[0], club, *old[1:6], name="Old 6")
    old_5 = await a_group_of(client, old[0], club, *old[1:5], name="Old 5")
    old_4_played = await a_group_of(client, old[0], club, *old[1:4], name="Old 4")
    old_3 = [
        await a_group_of(client, old[0], club, *old[1:3], name=f"Old 3{letter}")
        for letter in "ab"
    ]
    await a_group_of(client, old[0], club, old[1], name="Two of us")
    clock.move(timedelta(days=31))
    growing = [
        await a_group_of(client, new[0], club, *new[1:], name=f"Growing {n}")
        for n in (1, 2)
    ]
    hot = await a_group_of(client, new[0], club, *new[1:], name="Hot")
    now = clock.now()
    await games_in(
        session_factory, hot, now - timedelta(days=1), now - timedelta(days=2)
    )
    await games_in(session_factory, old_4_played, now - timedelta(days=3))

    page = await page_of(client, tomek)

    assert ids(page["groups"]) == [
        hot["id"],
        *sorted(group["id"] for group in growing),
        old_4_played["id"],
        old_6["id"],
        old_5["id"],
        *sorted(group["id"] for group in old_3),
    ]
    assert [card["tag"] for card in page["groups"]] == [
        "HOTTEST",
        "GROWING",
        "GROWING",
        None,
        None,
        None,
        None,
        None,
    ]
    assert (page["total"], page["next"]) == (8, None)


async def test_the_row_is_exactly_the_page_s_first_six(
    client, session_factory, clock, club, tomek
):
    """Card for card: the same groups, places, tags, bars, faces and relation."""

    crowd = await people(client, *(f"p{n}" for n in range(8)))
    for size in range(3, 9):
        await a_group_of(client, crowd[0], club, *crowd[1:size], name=f"Old {size}")
    clock.move(timedelta(days=31))
    played = await a_group_of(client, crowd[0], club, *crowd[1:4], name="Played")
    await a_group_of(client, crowd[4], club, *crowd[5:8], tomek, name="Tomek's")
    now = clock.now()
    await games_in(
        session_factory, played, *(now - timedelta(days=d) for d in (1, 2, 3))
    )

    row = await row_of(client, tomek)
    page = await page_of(client, tomek)

    assert len(page["groups"]) == 8
    assert row["groups"] == page["groups"][:6]
    assert row["total"] == page["total"] == 8


# --------------------------------------------------------------------------- #
# Whose groups
# --------------------------------------------------------------------------- #


async def test_the_reader_s_own_groups_are_on_it_marked_as_his(client, club, tomek):
    owner, ania, bartek = await people(client, "owner", "ania", "bartek")
    his = await a_group(client, tomek, club, name="His")
    for member in (ania, bartek):
        await joins(client, member, his, owner=tomek)
    member_of = await a_group_of(client, owner, club, ania, tomek, name="Member of")
    asked = await a_group_of(
        client, owner, club, ania, bartek, name="Asked", join_policy="PEOPLE_I_APPROVE"
    )
    assert (await join(client, tomek, asked)).json()["relation"] == "REQUESTED"
    other = await a_group_of(client, owner, club, ania, bartek, name="Other")

    page = await page_of(client, tomek)

    assert {card["id"]: card["relation"] for card in page["groups"]} == {
        his["id"]: "MEMBER",
        member_of["id"]: "MEMBER",
        asked["id"]: "REQUESTED",
        other["id"]: "NONE",
    }
    assert page["total"] == 4
    # Never his own face, on his own group or any other.
    assert str(tomek["id"]) not in {
        face["player_id"] for card in page["groups"] for face in card["faces"]
    }


async def test_groups_under_three_players_are_left_out_and_none_is_an_empty_page(
    client, club, tomek
):
    owner, ania, bartek = await people(client, "owner", "ania", "bartek")
    group = await a_group_of(client, owner, club, ania, name="Two of us")

    assert await page_of(client, tomek) == {"groups": [], "next": None, "total": 0}
    assert await row_of(client, tomek) == {"groups": [], "total": 0}

    await joins(client, bartek, group, owner=owner)
    page = await page_of(client, tomek)
    assert (ids(page["groups"]), page["total"]) == ([group["id"]], 1)


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #


async def test_twenty_a_page_by_cursor_and_the_last_names_no_next(
    client, session_factory, club, tomek
):
    sizes = [3 + n % 21 for n in range(45)]
    made = await groups_at(session_factory, club["id"], sizes)
    expected = [
        str(group_id)
        for group_id, _ in sorted(
            zip(made, sizes, strict=True),
            key=lambda pair: (-min(pair[1], 20), pair[0]),
        )
    ]

    pages = await every_page(client, tomek)

    assert [len(page["groups"]) for page in pages] == [20, 20, 5]
    assert [ids(page["groups"]) for page in pages] == [
        expected[:20],
        expected[20:40],
        expected[40:],
    ]
    # The first page carries the total; the later pages leave the first's.
    assert [page["total"] for page in pages] == [45, None, None]
    assert pages[-1]["next"] is None
    # Every card is read whole, on every page.
    last = pages[-1]["groups"][-1]
    assert (last["member_count"], len(last["faces"]), last["club"]["name"]) == (
        3,
        3,
        "Ogrody 33",
    )


async def test_a_page_exactly_full_at_the_end_names_no_next(
    client, session_factory, club, tomek
):
    await groups_at(session_factory, club["id"], [3] * 40)

    pages = await every_page(client, tomek)

    assert [len(page["groups"]) for page in pages] == [20, 20]


async def test_heat_is_worked_out_on_every_read_so_a_group_can_shift_pages(
    client, session_factory, club, tomek
):
    """**Accepted drift**: the cursor is a place in the order, never a count.
    A group behind it that heats past it is missed by the next page; one on the
    first page that cools behind it is read again; everybody else stays where
    they were."""

    await groups_at(session_factory, club["id"], [3 + n for n in range(25)])
    first = await page_of(client, tomek)
    rest = (await page_of(client, tomek, first["next"]))["groups"]
    heating, cooling = rest[-1], first["groups"][0]
    await resize(session_factory, heating["id"], 20)
    await resize(session_factory, cooling["id"], 3)

    second = await page_of(client, tomek, first["next"])

    assert heating["id"] not in ids(second["groups"])
    assert ids(second["groups"]) == [*ids(rest[:-1]), cooling["id"]]
    assert heating["id"] in ids((await page_of(client, tomek))["groups"])


def a_cursor(written: str) -> str:
    return base64.urlsafe_b64encode(written.encode()).decode().rstrip("=")


async def test_a_cursor_this_server_never_wrote_is_refused(client, tomek):
    some_group = uuid4().hex
    for after in (
        "nonsense",
        "",
        a_cursor(f"3:10:0:{some_group}"),  # no fourth rank
        a_cursor(f"0:-1:0:{some_group}"),  # no heat below nought
        a_cursor(f"0:10:-1:{some_group}"),  # nor games
        a_cursor("0:10:0:not-an-id"),
        a_cursor(f"0:10:{some_group}"),
        # Another spelling of a place this server could have written.
        a_cursor(f"+0:10:0:{some_group}"),
        a_cursor(f"0: 10:0:{some_group}"),
        a_cursor(f"0:10:0:{{{some_group}}}"),
        a_cursor(f"0:10:0:{some_group.upper()}"),
        a_cursor(f"0:10:0:{some_group}") + "==",
    ):
        read = await client.get(PAGE, params={"after": after}, headers=tomek["headers"])
        assert read.status_code == 400, (after, read.text)
        assert read.json()["code"] == "not_a_hottest_groups_page"


async def test_a_cursor_from_a_page_reads_on_after_a_group_gone_meanwhile(
    client, session_factory, club, tomek
):
    """The place a cursor names needs no group there now: a page is read on
    from a group deleted, or left below three, since."""

    await groups_at(session_factory, club["id"], [3 + n for n in range(22)])
    first = await page_of(client, tomek)
    await resize(session_factory, first["groups"][-1]["id"], 2)

    second = await page_of(client, tomek, first["next"])

    assert len(second["groups"]) == 2
    assert second["next"] is None


async def test_the_page_needs_a_player(client):
    assert (await client.get(PAGE)).status_code == 401


# --------------------------------------------------------------------------- #
# The total
# --------------------------------------------------------------------------- #


async def test_the_row_s_total_counts_every_group_of_three_in_them_or_not(
    client, session_factory, club, tomek
):
    owner, ania = await people(client, "owner", "ania")
    await a_group_of(client, owner, club, ania, tomek, name="His")
    await groups_at(session_factory, club["id"], [3, 7, 2, 1, 25])

    row = await row_of(client, tomek)

    assert row["total"] == 4
    assert len(row["groups"]) == 4


async def test_the_total_stops_at_a_hundred(client, session_factory, club, tomek):
    await groups_at(session_factory, club["id"], [3] * 100)
    assert (await row_of(client, tomek))["total"] == 100

    await groups_at(session_factory, club["id"], [3] * 7, named="More")

    row = await row_of(client, tomek)
    page = await page_of(client, tomek)
    assert (row["total"], page["total"]) == (100, 100)
    assert len(row["groups"]) == 6
    assert len(page["groups"]) == 20


def profile_folds(sent) -> list[str]:
    """The statements that fold one stream — a face's profile, one per face
    drawn, the faces' own cost (``ProfileGroupFaces``)."""

    return [
        statement
        for statement in sent.naming("event_store")
        if "event_store.aggregate_id = ?" in " ".join(statement.split())
    ]


async def test_the_row_s_total_adds_no_statement(
    client, session_factory, club, tomek, statements
):
    """**Not one statement**: the total is the number of groups the heat
    already counted the members of. Six groups or thirty-six, the row sends the
    same statements, and the groups projections are asked four questions — the
    members counted, one group-by over ``group_members``; then the six shown,
    their members and who waits on them."""

    await groups_at(session_factory, club["id"], [3] * 6)
    with statements.counting() as six:
        assert (await row_of(client, tomek))["total"] == 6

    await groups_at(session_factory, club["id"], [3] * 30, named="More")
    with statements.counting() as thirty_six:
        assert (await row_of(client, tomek))["total"] == 36

    assert len(thirty_six) == len(six)
    counted, listed = thirty_six.naming("group_members")
    assert "count(" in counted.lower() and "group by" in counted.lower()
    assert "count(" not in listed.lower()
    assert len(thirty_six.naming("groups")) == 1
    assert len(thirty_six.naming("group_join_requests")) == 1


async def test_a_page_asks_the_row_s_questions_and_folds_a_profile_per_face(
    client, session_factory, club, tomek, statements
):
    """A page of twenty is read whole as the row's six are: the same questions,
    about twenty groups instead of six, and one profile per face it draws."""

    await groups_at(session_factory, club["id"], [3] * 30)
    with statements.counting() as a_row:
        row = await row_of(client, tomek)
    with statements.counting() as a_page:
        page = await page_of(client, tomek)

    def questions(sent) -> list[str]:
        folds = profile_folds(sent)
        return [statement for statement in sent if statement not in folds]

    def faces(cards: list[dict]) -> int:
        return sum(len(card["faces"]) for card in cards)

    assert len(questions(a_page)) == len(questions(a_row))
    assert (
        (len(profile_folds(a_row)), len(profile_folds(a_page)))
        == (
            faces(row["groups"]),
            faces(page["groups"]),
        )
        == (18, 60)
    )
