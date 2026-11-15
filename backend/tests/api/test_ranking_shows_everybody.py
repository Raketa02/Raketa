"""The ranking is the real ranking: blocked and switched-off players are on
every list at their true places, read the way the player app reads them (#791;
``docs/adr/0204`` §2; the home-rows mechanics §4.4–§4.5).

Thirteen padel players are listed, a hundredth apart, and Tomek is 7th.
**Tomek blocks Marek**: both still see each other's row, at their true places,
the podium and *of 13* the same for everybody — and a tap on the other reads
the record's one refusal. **Bartek turns *Show me to new people* off**: his row
stays where it was, for everybody, and his own card is listed with its gap
line. The *hidden* card state is gone from the contract.

Every claim is read off the player routes — ``POST /blocks``, ``PUT
/players/me/show-me-to-new-people``, ``GET /rankings/padel``, ``GET
/rankings/padel/general/rows``, ``GET /players/{id}/record`` and ``GET /home``.
"""

from __future__ import annotations

import pytest

from tests.api import players_world as players
from tests.api.players_world import deliver_the_outbox
from tests.api.rankings_world import (
    a_listed_crowd,
    general_rows,
    home_ranking,
    places,
    ranking,
)
from tests.api.test_groups import a_club, a_group, join
from tests.api.test_ranking_friends import befriend

EVERYBODY = list(range(1, 14))


def nicknames(read: dict) -> list[str]:
    return [row["nickname"] for row in read["rows"]]


def podium(read: dict) -> list[tuple[int, str]]:
    return [(row["place"], row["nickname"]) for row in read["podium"]]


async def blocks(client, blocker: dict, blocked: dict) -> None:
    made = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"])},
        headers=blocker["headers"],
    )
    assert made.status_code == 204, made.text


async def switches_off(client, player: dict) -> None:
    turned = await client.put(
        "/api/v1/players/me/show-me-to-new-people",
        json={"on": False},
        headers=player["headers"],
    )
    assert turned.status_code == 204, turned.text


async def in_one_group(client, cast: list[dict]) -> None:
    """Everybody in one player group, so any two may be friends."""

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

    crowd = await a_listed_crowd(client, session_factory, clock, 13)
    for player in crowd:
        player["headers"] = players.auth(player["token"])
    return crowd


# --------------------------------------------------------------------------- #
# A blocked pair
# --------------------------------------------------------------------------- #


async def test_a_blocked_pair_see_each_other_at_their_true_places(
    client, session_factory, thirteen
):
    tomek, marek = thirteen[6], thirteen[9]

    await blocks(client, tomek, marek)
    await deliver_the_outbox(session_factory)

    for reader in (tomek, marek, thirteen[0]):
        read = await ranking(client, reader)
        assert places(read) == EVERYBODY
        assert {"crowd006", "crowd009"} <= set(nicknames(read))
        assert (read["listed"], read["card"]["of"]) == (13, 13)
        assert podium(read) == [(1, "crowd000"), (2, "crowd001"), (3, "crowd002")]
        assert places(await general_rows(client, reader)) == EVERYBODY
    assert (await ranking(client, tomek))["card"]["place"] == 7
    assert (await ranking(client, marek))["card"]["place"] == 10
    assert (await home_ranking(client, tomek))["general_place"] == 7


async def test_the_gap_line_names_the_true_neighbour_whoever_blocked_whom(
    client, thirteen
):
    tomek, below = thirteen[6], thirteen[7]

    await blocks(client, below, tomek)

    toms = (await ranking(client, tomek))["card"]["gap_line"]
    belows = (await ranking(client, below))["card"]["gap_line"]
    assert (toms["below"]["nickname"], toms["below"]["gap"]) == ("crowd007", 0.01)
    assert (belows["above"]["nickname"], belows["above"]["gap"]) == (
        "crowd006",
        0.01,
    )


@pytest.mark.parametrize("blocker", ["tomek", "marek"])
async def test_a_record_opened_from_the_ranking_across_a_block_is_refused(
    client, thirteen, blocker
):
    """The row is there, and a tap on it reads *This record isn't available*
    — both ways round (the mechanics §4.4)."""

    cast = {"tomek": thirteen[6], "marek": thirteen[9]}
    tomek, marek = cast["tomek"], cast["marek"]
    await blocks(client, cast[blocker], marek if blocker == "tomek" else tomek)

    for reader, subject in ((tomek, marek), (marek, tomek)):
        refused = await client.get(
            f"/api/v1/players/{subject['id']}/record",
            params={"sport": "PADEL"},
            headers=reader["headers"],
        )
        assert refused.status_code == 404, refused.text
        assert refused.json()["code"] == "record_unavailable"


async def test_a_blocked_pair_who_were_friends_leave_each_others_friends_table(
    client, session_factory, thirteen
):
    """A block ends a friendship, as ever (ADR-0202 §2): once its delivery
    lands, each is out of the other's table — the true places of who is left."""

    karol, tomek, marek = thirteen[3], thirteen[6], thirteen[9]
    await in_one_group(client, [karol, tomek, marek])
    await befriend(client, tomek, marek)
    await befriend(client, karol, tomek)
    await befriend(client, karol, marek)

    await blocks(client, marek, tomek)
    await deliver_the_outbox(session_factory)

    toms = await ranking(client, tomek, view="FRIENDS")
    assert (nicknames(toms), places(toms), toms["listed"]) == (
        ["crowd003", "crowd006"],
        [1, 2],
        2,
    )


# --------------------------------------------------------------------------- #
# Show me to new people, off
# --------------------------------------------------------------------------- #


async def test_a_switched_off_player_keeps_their_true_place_for_everybody(
    client, session_factory, thirteen
):
    bartek = thirteen[6]
    # Read once first, so a kept order is in hand when the switch turns.
    assert places(await ranking(client, thirteen[0])) == EVERYBODY

    await switches_off(client, bartek)
    await deliver_the_outbox(session_factory)

    for reader in (thirteen[0], thirteen[12]):
        read = await ranking(client, reader)
        assert places(read) == EVERYBODY
        assert "crowd006" in nicknames(read)
        assert (read["listed"], read["card"]["of"]) == (13, 13)
    mine = await ranking(client, bartek)
    assert mine["card"]["state"] == "LISTED"
    assert (mine["card"]["place"], mine["card"]["of"]) == (7, 13)
    assert mine["card"]["gap_line"]["above"]["nickname"] == "crowd005"
    assert (await home_ranking(client, bartek))["general_place"] == 7


async def test_a_page_around_a_reader_holds_every_place(client, session_factory, clock):
    """Nothing is dropped from a slice: *around me* is 25 places above and 24
    below, whole, and the pages either side meet it."""

    crowd = await a_listed_crowd(client, session_factory, clock, 60)
    for player in crowd:
        player["headers"] = players.auth(player["token"])
    reader = crowd[29]
    await switches_off(client, crowd[9])
    await blocks(client, crowd[40], reader)

    first = await ranking(client, reader)
    assert places(first) == list(range(1, 51))
    assert places(await general_rows(client, reader, after=first["next"])) == list(
        range(51, 61)
    )
    around = await general_rows(client, reader, around_me=True)
    assert places(around) == list(range(5, 55))
    assert places(await general_rows(client, reader, before=around["previous"])) == [
        1,
        2,
        3,
        4,
    ]
