"""*Show me in General*, and blocks in the lists, read the way the player app
reads them (#772; ``docs/adr/0203`` §7–§8; the rankings mechanics §5, §7.3,
§10, §11; the screens §4.5, §5.1).

Thirteen padel players are listed, a hundredth apart, and Tomek is 7th.
**Tomek turns *Show me in General* off**: his row leaves everybody else's
General, the others read #6 then #8 and *of 13* still counts him; his own card
reads *hidden* with its place and Home still says #7; his friends still see him
among Friends. **Tomek blocks Marek**: neither sees the other's row, in either
view, whoever made the block, and nobody's place moves. **The podium is the
first three rows the reader sees**, each with its true place.

Every claim is read off the player routes — ``PUT
/players/me/ranking-visibility``, ``POST /blocks``, ``GET /rankings/padel``,
``GET /rankings/padel/general/rows`` and ``GET /home`` — the outbox delivered
as the worker delivers it.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete

from app.bootstrap.composition import build_rebuild_the_rankings, build_ranking_rows
from app.kernel import Sport
from app.modules.rankings.domain.ranking import GeneralSwitch
from app.modules.rankings.infrastructure.ranking_model import (
    RankingRowORM,
    RankingVisibilityORM,
)
from tests.api import players_world as players
from tests.api.players_world import deliver_the_outbox
from tests.api.rankings_world import (
    a_listed_crowd,
    general_rows,
    home_ranking,
    places,
    ranking,
    results_at,
)
from tests.api.test_groups import a_club, a_group, join
from tests.api.test_ranking_friends import befriend
from tests.unit.kept_orders import kept_orders_of

VISIBILITY = "/api/v1/players/me/ranking-visibility"
SAME = {"kind": "SAME", "places": None}


def _span(first: int, last: int, *, but: tuple[int, ...] = ()) -> list[int]:
    return [place for place in range(first, last + 1) if place not in but]


def nicknames(read: dict) -> list[str]:
    return [row["nickname"] for row in read["rows"]]


def podium(read: dict) -> list[tuple[int, str]]:
    return [(row["place"], row["nickname"]) for row in read["podium"]]


async def turns(client, session_factory, player: dict, visibility: str) -> None:
    """*Show me in General* switched, and the outbox delivered."""

    switched = await client.put(
        VISIBILITY,
        json={"visibility": visibility},
        headers=players.auth(player["token"]),
    )
    assert switched.status_code == 204, switched.text
    await deliver_the_outbox(session_factory)


async def blocks(client, blocker: dict, blocked: dict) -> None:
    """A block from the blocker's record — **not delivered**: the rows hide
    at once, read live from the blocks."""

    made = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"])},
        headers=players.auth(blocker["token"]),
    )
    assert made.status_code == 204, made.text


async def in_one_group(client, cast: list[dict]) -> None:
    """Everybody in one player group, so any two may be friends."""

    for player in cast:
        player["headers"] = players.auth(player["token"])
    first, *rest = cast
    group = await a_group(client, first, await a_club(client), name="Padel po pracy")
    for player in rest:
        joined = await join(client, player, group)
        assert joined.status_code in (200, 201), joined.text
    for player in cast:
        player["group"] = group["id"]


@pytest.fixture
async def thirteen(client, session_factory, clock) -> list[dict]:
    """Thirteen listed in padel, ``crowd000`` first at 6,00, a hundredth apart,
    none of them *New*."""

    return await a_listed_crowd(client, session_factory, clock, 13)


# --------------------------------------------------------------------------- #
# Show me in General
# --------------------------------------------------------------------------- #


async def test_a_hidden_player_leaves_everybody_elses_general_and_leaves_a_gap(
    client, session_factory, thirteen
):
    tomek = thirteen[6]
    # Read once first, so a kept order is what the switch must forget.
    assert places(await ranking(client, thirteen[0])) == _span(1, 13)

    await turns(client, session_factory, tomek, "HIDDEN")

    for reader in (thirteen[0], thirteen[12]):
        read = await ranking(client, reader)
        # The others see #6, then #8 — and *of 13* still counts him.
        assert places(read) == _span(1, 13, but=(7,))
        assert "crowd006" not in nicknames(read)
        assert (read["listed"], read["card"]["of"]) == (13, 13)
        page = await general_rows(client, reader)
        assert places(page) == _span(1, 13, but=(7,))
        assert page["listed"] == 13
    # Nobody else's place moved.
    assert (await ranking(client, thirteen[12]))["card"]["place"] == 13


async def test_a_hidden_player_still_sees_their_own_place_and_home_keeps_it(
    client, session_factory, thirteen
):
    """The dark card keeps the place, the Level and the chip; *Hidden from
    General* and the switch stand where the gap line was (the screens §4.5)."""

    tomek = thirteen[6]

    await turns(client, session_factory, tomek, "HIDDEN")
    mine = await ranking(client, tomek)

    assert mine["card"] == {
        "state": "HIDDEN",
        "results": 5,
        "results_to_enter": 5,
        "place": 7,
        "of": 13,
        "level": 5.94,
        "chip": SAME,
        "gap_line": None,
    }
    # His own row is his to see, in its place, among everybody's.
    assert places(mine) == _span(1, 13)
    [own] = [row for row in mine["rows"] if row["is_you"]]
    assert own["place"] == 7
    around = await general_rows(client, tomek, around_me=True)
    assert [row["place"] for row in around["rows"] if row["is_you"]] == [7]
    assert (await home_ranking(client, tomek))["general_place"] == 7


async def test_the_gap_line_and_the_podium_skip_a_hidden_row(
    client, session_factory, thirteen
):
    await turns(client, session_factory, thirteen[6], "HIDDEN")
    await turns(client, session_factory, thirteen[1], "HIDDEN")

    eighth = (await ranking(client, thirteen[7]))["card"]["gap_line"]
    sixth = (await ranking(client, thirteen[5]))["card"]["gap_line"]

    # Measured against the nearest row each can see, past the hidden one.
    assert (eighth["above"]["nickname"], eighth["above"]["gap"]) == ("crowd005", 0.02)
    assert (sixth["below"]["nickname"], sixth["below"]["gap"]) == ("crowd007", 0.02)
    # The first three rows the reader sees, each step its true place.
    assert podium(await ranking(client, thirteen[12])) == [
        (1, "crowd000"),
        (3, "crowd002"),
        (4, "crowd003"),
    ]
    # A hidden player's own podium has their own row on it.
    assert [place for place, _ in podium(await ranking(client, thirteen[1]))] == [
        1,
        2,
        3,
    ]


async def test_friends_still_see_a_hidden_player_and_their_friends_card_is_listed(
    client, session_factory, thirteen
):
    tomek, karol = thirteen[6], thirteen[3]
    await in_one_group(client, [tomek, karol])
    await befriend(client, tomek, karol)

    await turns(client, session_factory, tomek, "HIDDEN")
    karols = await ranking(client, karol, view="FRIENDS")
    tomeks = await ranking(client, tomek, view="FRIENDS")

    assert nicknames(karols) == ["crowd003", "crowd006"]
    assert places(karols) == [1, 2]
    # Friends ignores the switch: Tomek's Friends card is an ordinary place.
    assert tomeks["card"]["state"] == "LISTED"
    assert tomeks["card"]["place"] == 2
    assert tomeks["card"]["gap_line"]["above"]["nickname"] == "crowd003"
    assert (await home_ranking(client, tomek))["friends_place"] == 2


async def test_turning_it_back_on_restores_the_row_and_the_gap_line(
    client, session_factory, thirteen
):
    tomek = thirteen[6]
    await turns(client, session_factory, tomek, "HIDDEN")

    await turns(client, session_factory, tomek, "SHOWN")

    assert places(await ranking(client, thirteen[0])) == _span(1, 13)
    mine = (await ranking(client, tomek))["card"]
    assert mine["state"] == "LISTED"
    assert mine["gap_line"]["above"]["nickname"] == "crowd005"
    assert mine["gap_line"]["below"]["nickname"] == "crowd007"


async def test_a_switch_turned_before_the_first_result_holds_when_the_row_is_made(
    client, session_factory, clock, thirteen
):
    """The switch is a fact about the player, not about a row: Ewa hides
    before she has played, and her five results later list her hidden."""

    ewa_id, token = await players.a_player_on_the_log(
        client, session_factory, "ewa", mu=5.5
    )
    ewa = {"id": ewa_id, "token": token}
    await turns(client, session_factory, ewa, "HIDDEN")

    await results_at(session_factory, ewa, [5.5] * 5, clock)

    others = await ranking(client, thirteen[0])
    assert others["listed"] == 14
    assert "ewa" not in nicknames(others)
    assert (await ranking(client, ewa))["card"]["state"] == "HIDDEN"


async def test_a_switch_read_at_an_older_version_never_replaces_a_newer_one(
    client, session_factory, thirteen
):
    """A delivery that read Tomek's profile before he hid, writing after the
    one that read it hidden, takes nothing back."""

    tomek = thirteen[6]
    await turns(client, session_factory, tomek, "HIDDEN")

    async with session_factory() as session:
        await build_ranking_rows(session).follow(
            GeneralSwitch(player_id=tomek["id"], hidden=False, version=1)
        )
        await session.commit()

    assert places(await ranking(client, thirteen[0])) == _span(1, 13, but=(7,))


async def test_the_rebuild_follows_every_switch_and_running_it_twice_changes_nothing(
    client, session_factory, clock, thirteen
):
    """A projection rebuilt from nothing never lists a hidden player: the
    rebuild reads every profile's switch — Tomek's, and Ewa's, who hid before
    she had a level and is listed only after the rebuild."""

    tomek = thirteen[6]
    ewa_id, ewa_token = await players.register(client, "ewa")
    await players.commit_profile(client, ewa_token)
    ewa = {"id": ewa_id, "token": ewa_token}
    await turns(client, session_factory, tomek, "HIDDEN")
    await turns(client, session_factory, ewa, "HIDDEN")
    async with session_factory() as session:
        await session.execute(delete(RankingRowORM))
        await session.execute(delete(RankingVisibilityORM))
        await session.commit()

    for _ in range(2):
        async with session_factory() as session:
            rebuilt = await build_rebuild_the_rankings(
                session, orders=kept_orders_of(session_factory)
            ).execute()
        assert (rebuilt.rows, rebuilt.switches) == (13, 14)
        assert places(await ranking(client, thirteen[0])) == _span(1, 13, but=(7,))
        assert (await ranking(client, tomek))["card"]["state"] == "HIDDEN"

    await players.rate_in(session_factory, ewa_id, Sport.PADEL, mu=5.5)
    await results_at(session_factory, ewa, [5.5] * 5, clock)
    others = await ranking(client, thirteen[0])
    assert others["listed"] == 14 and "ewa" not in nicknames(others)


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


async def test_a_block_hides_both_rows_from_each_other_and_no_place_moves(
    client, session_factory, thirteen
):
    tomek, marek = thirteen[6], thirteen[9]

    await blocks(client, tomek, marek)

    toms, mareks = await ranking(client, tomek), await ranking(client, marek)
    # Neither sees the other, whichever of them made the block.
    assert places(toms) == _span(1, 13, but=(10,))
    assert places(mareks) == _span(1, 13, but=(7,))
    assert (toms["card"]["place"], mareks["card"]["place"]) == (7, 10)
    assert (toms["listed"], mareks["listed"]) == (13, 13)
    # Somebody else sees both.
    assert places(await ranking(client, thirteen[0])) == _span(1, 13)
    # And Home's places are their true ones.
    assert (await home_ranking(client, tomek))["general_place"] == 7
    assert (await home_ranking(client, marek))["general_place"] == 10
    # A page drops them too.
    assert places(await general_rows(client, marek)) == _span(1, 13, but=(7,))


async def test_the_gap_line_skips_a_blocked_neighbour_both_ways(
    client, session_factory, thirteen
):
    tomek, below = thirteen[6], thirteen[7]

    await blocks(client, below, tomek)

    toms = (await ranking(client, tomek))["card"]["gap_line"]
    belows = (await ranking(client, below))["card"]["gap_line"]
    assert (toms["below"]["nickname"], toms["below"]["gap"]) == ("crowd008", 0.02)
    assert (belows["above"]["nickname"], belows["above"]["gap"]) == (
        "crowd005",
        0.02,
    )


async def test_a_block_hides_the_rows_among_friends_at_once_and_places_stay(
    client, session_factory, thirteen
):
    """Tomek, Marek and Karol are friends, all three. Marek blocks Tomek: the
    two rows leave each other's Friends at once, places kept — and once the
    block's delivery ends their friendship, each is out of the other's table."""

    karol, tomek, marek = thirteen[3], thirteen[6], thirteen[9]
    await in_one_group(client, [karol, tomek, marek])
    await befriend(client, tomek, marek)
    await befriend(client, karol, tomek)
    await befriend(client, karol, marek)

    await blocks(client, marek, tomek)

    toms = await ranking(client, tomek, view="FRIENDS")
    mareks = await ranking(client, marek, view="FRIENDS")
    assert (nicknames(toms), places(toms)) == (["crowd003", "crowd006"], [1, 2])
    assert (nicknames(mareks), places(mareks)) == (["crowd003", "crowd009"], [1, 3])
    assert (toms["listed"], mareks["listed"]) == (3, 3)
    assert mareks["card"]["place"] == 3

    await deliver_the_outbox(session_factory)

    after = await ranking(client, tomek, view="FRIENDS")
    assert (nicknames(after), after["listed"]) == (["crowd003", "crowd006"], 2)


async def test_the_podium_is_the_first_three_rows_each_reader_sees(
    client, session_factory, thirteen
):
    first, second = thirteen[0], thirteen[1]

    await blocks(client, first, second)

    assert podium(await ranking(client, first)) == [
        (1, "crowd000"),
        (3, "crowd002"),
        (4, "crowd003"),
    ]
    assert podium(await ranking(client, second)) == [
        (2, "crowd001"),
        (3, "crowd002"),
        (4, "crowd003"),
    ]
    assert [place for place, _ in podium(await ranking(client, thirteen[5]))] == [
        1,
        2,
        3,
    ]


async def test_no_podium_when_the_reader_sees_fewer_than_three_rows(
    client, session_factory, clock
):
    one, two, three = await a_listed_crowd(client, session_factory, clock, 3)

    await blocks(client, one, three)

    ones = await ranking(client, one)
    assert places(ones) == [1, 2]
    assert ones["podium"] == []
    assert len((await ranking(client, two))["podium"]) == 3


# --------------------------------------------------------------------------- #
# Pages of a kept order
# --------------------------------------------------------------------------- #


async def test_a_page_drops_what_the_reader_cant_see_and_keeps_its_cursors(
    client, session_factory, clock
):
    """The kept order holds every row; each reader's slice drops the hidden
    and the blocked. *Around me* centres on the reader's true place, and the
    cursors are the slice's own ends, so the pages either side are whole."""

    crowd = await a_listed_crowd(client, session_factory, clock, 60)
    reader = crowd[29]
    await turns(client, session_factory, crowd[9], "HIDDEN")
    await blocks(client, crowd[40], reader)

    first = await ranking(client, reader)
    assert places(first) == _span(1, 50, but=(10, 41))
    assert places(await general_rows(client, reader, after=first["next"])) == (
        _span(51, 60)
    )

    around = await general_rows(client, reader, around_me=True)
    # 25 places above the 30th and 24 below: 5th to 54th, two left out.
    assert places(around) == _span(5, 54, but=(10, 41))
    assert places(await general_rows(client, reader, before=around["previous"])) == (
        _span(1, 4)
    )
    assert places(await general_rows(client, reader, after=around["next"])) == (
        _span(55, 60)
    )
    # Somebody nobody blocked sees the hidden row's gap alone.
    assert places(await ranking(client, crowd[0])) == _span(1, 50, but=(10,))
