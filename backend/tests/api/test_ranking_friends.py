"""The Friends view, read the way the player app reads it (#771;
``docs/adr/0203`` §3–§6; the rankings mechanics §4.2, §6–§8; the screens §4.6).

Tomek plays padel with Karol, Zofia, Inés and Ewa, and all five are in *Padel
po pracy*, where friend requests are asked and answered through the player
routes. **Friends is the reader and their friends with a result in the last 90
days** — from the first result, places, chips and the gap line counted among
them alone, the whole table at once. Every claim is read off
``GET /rankings/padel?view=FRIENDS`` and ``GET /home``.

Where a test needs an exact Level it is moved through the rating's own
aggregate (``moves_to``), which records the same ``rating.moved_on_result`` a
settled game does, on the same outbox.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from tests.api import players_world as players
from tests.api.rankings_world import (
    chips,
    home_ranking,
    plays,
    ranking,
    results_at,
)
from tests.api.test_groups import a_club, a_group, join

SAME = {"kind": "SAME", "places": None}
NEW = {"kind": "NEW", "places": None}
UP_1 = {"kind": "UP", "places": 1}
DOWN_1 = {"kind": "DOWN", "places": 1}


@pytest.fixture
async def five(client) -> dict[str, dict]:
    """Five padel players, each rated through a real questionnaire, all in one
    group so any two may be friends."""

    cast = {
        name: await players.a_rated_player(client, name)
        for name in ("tomek", "karol", "zofia", "ines", "ewa")
    }
    for player in cast.values():
        player["headers"] = players.auth(player["token"])
    first, *rest = cast.values()
    group = await a_group(client, first, await a_club(client), name="Padel po pracy")
    for player in rest:
        joined = await join(client, player, group)
        assert joined.status_code in (200, 201), joined.text
    for player in cast.values():
        player["group"] = group["id"]
    return cast


async def befriend(client, asker: dict, answerer: dict) -> None:
    """A request from Members, and its acceptance."""

    asked = await client.post(
        "/api/v1/friends/requests",
        json={
            "player_id": str(answerer["id"]),
            "made_from": "MEMBERS",
            "group_id": asker["group"],
            "sport": "PADEL",
        },
        headers=asker["headers"],
    )
    assert asked.status_code == 200, asked.text
    accepted = await client.post(
        f"/api/v1/friends/requests/{asker['id']}/acceptance",
        headers=answerer["headers"],
    )
    assert accepted.status_code == 200, accepted.text


async def friends_view(client, player: dict) -> dict:
    return await ranking(client, player, view="FRIENDS")


def names(read: dict) -> list[str]:
    return [row["nickname"] for row in read["rows"]]


async def a_while_ago(session_factory, clock, *levels: tuple) -> None:
    """One result each at the Level paired with them, then the clock moved
    past the chip's week — so every one of them is listed among friends, and
    none is *New*."""

    for player, level in levels:
        await results_at(session_factory, player, [level], clock)
    clock.move(timedelta(days=8))


NOT_LISTED = {
    "place": None,
    "of": None,
    "level": None,
    "chip": None,
    "gap_line": None,
}


# --------------------------------------------------------------------------- #
# Who is listed
# --------------------------------------------------------------------------- #


async def test_friends_are_listed_from_the_first_result(
    client, session_factory, clock, five
):
    """One game: Tomek and Karol, friends, beat Zofia and Inés. Neither is on
    General, five results short — but both are among Tomek's friends, and only
    they: Zofia and Inés are nobody's friends here."""

    tomek, karol, zofia, ines, _ = five.values()
    await befriend(client, tomek, karol)
    await plays(client, session_factory, clock, (tomek, karol), (zofia, ines))

    general = await ranking(client, tomek)
    friends = await friends_view(client, tomek)

    assert general["card"]["state"] == "NEEDS_RESULTS"
    assert friends["view"] == "FRIENDS"
    assert friends["listed"] == 2
    assert sorted(names(friends)) == ["karol", "tomek"]
    assert [row["place"] for row in friends["rows"]] == [1, 2]
    assert friends["card"]["state"] == "LISTED"
    assert friends["card"]["of"] == 2
    assert friends["card"]["results"] == 1
    assert friends["card"]["results_to_enter"] == 1
    [mine] = [row for row in friends["rows"] if row["is_you"]]
    assert mine["place"] == friends["card"]["place"]
    assert mine["form"] == ["WIN"]
    # Their first result was this week: *New* among friends.
    assert set(map(str, chips(friends).values())) == {str(NEW)}
    assert friends["card"]["chip"] == NEW
    # Fewer than three: no podium. The whole table, never a page.
    assert (friends["podium"], friends["next"]) == ([], None)


async def test_ninety_days_on_a_friend_is_off_and_the_next_result_brings_them_back(
    client, session_factory, clock, five
):
    tomek, karol, zofia, ines, _ = five.values()
    await befriend(client, tomek, karol)
    await befriend(client, tomek, zofia)
    await a_while_ago(
        session_factory, clock, (tomek, 2.71), (karol, 2.75), (zofia, 2.69)
    )
    clock.move(timedelta(days=60))
    await results_at(session_factory, zofia, [2.69], clock)
    clock.move(timedelta(days=31))

    # Tomek's and Karol's last results are 99 days old, Zofia's 31.
    off = await friends_view(client, tomek)

    assert names(off) == ["zofia"]
    assert off["card"] == {
        "state": "OFF_THE_LIST",
        "results": 1,
        "results_to_enter": 1,
        **NOT_LISTED,
    }
    # A friend is listed and Tomek isn't: no Friends place on Home.
    assert await home_ranking(client, tomek) == {
        "sport": "PADEL",
        "general_place": None,
        "friends_place": None,
    }

    await results_at(session_factory, tomek, [2.71], clock)
    back = await friends_view(client, tomek)

    assert names(back) == ["tomek", "zofia"]
    assert back["card"]["state"] == "LISTED"
    assert (back["card"]["place"], back["card"]["of"]) == (1, 2)


# --------------------------------------------------------------------------- #
# The chip among friends
# --------------------------------------------------------------------------- #


async def test_adding_a_friend_moves_nobodys_chip(client, session_factory, clock, five):
    """Tomek adds Inés, the best padel player Tomek knows: Inés tops the table
    and Tomek is second now — and nobody's chip moves for it, Tomek's
    included. **Both played this week**, so each is placed a week back from
    their level history, and Inés stood above Tomek then too."""

    tomek, karol, zofia, ines, _ = five.values()
    await befriend(client, tomek, karol)
    await befriend(client, tomek, zofia)
    await a_while_ago(
        session_factory,
        clock,
        (ines, 3.40),
        (tomek, 2.71),
        (karol, 2.70),
        (zofia, 2.69),
    )
    await results_at(session_factory, ines, [3.42], clock)
    await results_at(session_factory, tomek, [2.72], clock)
    before = await friends_view(client, tomek)

    await befriend(client, ines, tomek)
    after = await friends_view(client, tomek)

    assert (before["card"]["place"], before["card"]["of"]) == (1, 3)
    assert (after["card"]["place"], after["card"]["of"]) == (2, 4)
    assert names(after) == ["ines", "tomek", "karol", "zofia"]
    assert chips(after) == {name: SAME for name in names(after)}
    assert after["card"]["chip"] == SAME


async def test_an_overtake_among_friends_moves_both_and_a_stranger_moves_nobody(
    client, session_factory, clock, five
):
    """Karol, Tomek's friend, passes Tomek: ▼ 1 for Tomek among friends and ▲ 1
    for Karol. Ewa, a stranger, passes Tomek too — on General that is ▼ 2,
    among Tomek's friends still ▼ 1."""

    tomek, karol, zofia, _, ewa = five.values()
    await befriend(client, tomek, karol)
    await befriend(client, tomek, zofia)
    for player, level in ((tomek, 2.71), (karol, 2.70), (zofia, 2.69), (ewa, 2.68)):
        await results_at(session_factory, player, [level] * 5, clock)
    clock.move(timedelta(days=8))

    await results_at(session_factory, karol, [2.73], clock)
    await results_at(session_factory, ewa, [2.75], clock)
    friends = await friends_view(client, tomek)
    general = await ranking(client, tomek)

    assert names(friends) == ["karol", "tomek", "zofia"]
    assert chips(friends) == {"karol": UP_1, "tomek": DOWN_1, "zofia": SAME}
    assert friends["card"]["chip"] == DOWN_1
    assert general["card"]["chip"] == {"kind": "DOWN", "places": 2}
    # Karol's own table is Karol and Karol's friend Tomek.
    assert (await friends_view(client, karol))["card"]["chip"] == UP_1


# --------------------------------------------------------------------------- #
# The gap line and the podium among friends
# --------------------------------------------------------------------------- #


async def test_the_gap_line_names_friends_and_is_priced_as_in_general(
    client, session_factory, clock, five
):
    """Zofia, a stranger, stands between Tomek and Karol on General. Among his
    friends, the line skips her: *0,04 behind Karol · about 4 wins close it ·
    Ewa is 0,03 behind you*."""

    tomek, karol, zofia, ines, ewa = five.values()
    for friend in (karol, ines, ewa):
        await befriend(client, tomek, friend)
    await a_while_ago(
        session_factory,
        clock,
        (ines, 3.40),
        (karol, 2.75),
        (zofia, 2.73),
        (tomek, 2.71),
        (ewa, 2.68),
    )

    read = await friends_view(client, tomek)

    assert names(read) == ["ines", "karol", "tomek", "ewa"]
    assert read["card"]["gap_line"] == {
        "above": {"nickname": "karol", "gap": 0.04, "wins": 4, "tied": False},
        "below": {"nickname": "ewa", "gap": 0.03},
        "top_of_the_list": False,
    }
    assert [row["nickname"] for row in read["podium"]] == ["ines", "karol", "tomek"]
    assert [row["place"] for row in read["podium"]] == [1, 2, 3]
    top = (await friends_view(client, ines))["card"]["gap_line"]
    assert top == {"above": None, "below": None, "top_of_the_list": True}


# --------------------------------------------------------------------------- #
# The card's states
# --------------------------------------------------------------------------- #


async def test_a_listed_reader_with_no_friend_listed_is_just_you(
    client, session_factory, clock, five
):
    """Tomek has a result; Tomek's friend Karol has none, and Zofia, who has,
    is no friend of Tomek's."""

    tomek, karol, zofia, _, _ = five.values()
    await befriend(client, tomek, karol)
    await a_while_ago(session_factory, clock, (tomek, 2.71), (zofia, 2.75))

    read = await friends_view(client, tomek)

    assert read["card"] == {
        "state": "JUST_YOU",
        "results": 1,
        "results_to_enter": 1,
        **NOT_LISTED,
    }
    assert (read["listed"], read["rows"], read["podium"]) == (1, [], [])
    assert await home_ranking(client, tomek) == {
        "sport": "PADEL",
        "general_place": None,
        "friends_place": None,
    }


@pytest.mark.parametrize("has_friends", [True, False], ids=["a friend", "none"])
async def test_nobody_listed_is_no_friend_listed(
    client, session_factory, clock, five, has_friends
):
    """Neither Tomek nor any friend of Tomek's has a result: *None of your
    friends is ranked in padel yet* — with a friend or with none at all."""

    tomek, karol, zofia, _, _ = five.values()
    if has_friends:
        await befriend(client, tomek, karol)
    await a_while_ago(session_factory, clock, (zofia, 2.75))

    read = await friends_view(client, tomek)

    assert read["card"] == {
        "state": "NO_FRIEND_LISTED",
        "results": 0,
        "results_to_enter": 1,
        **NOT_LISTED,
    }
    assert (read["listed"], read["rows"], read["podium"]) == (0, [], [])


async def test_a_reader_with_no_result_reads_the_friends_table_under_their_own_card(
    client, session_factory, clock, five
):
    """*Not ranked in padel yet — your first confirmed competitive game puts
    you on the list*, above Karol and Zofia's table (Q7)."""

    tomek, karol, zofia, _, _ = five.values()
    await befriend(client, karol, tomek)
    await befriend(client, zofia, tomek)
    await a_while_ago(session_factory, clock, (karol, 2.75), (zofia, 2.69))

    read = await friends_view(client, tomek)

    assert read["card"] == {
        "state": "NEEDS_RESULTS",
        "results": 0,
        "results_to_enter": 1,
        **NOT_LISTED,
    }
    assert names(read) == ["karol", "zofia"]
    assert not any(row["is_you"] for row in read["rows"])
    assert (read["listed"], read["podium"]) == (2, [])


async def test_a_reader_with_no_level_reads_the_friends_table_under_get_your_level(
    client, session_factory, clock, five
):
    """Ola browses with no padel level: Ola's friend Karol's table is under *No
    padel level yet — get one, then one competitive game puts you on the
    list*."""

    karol = five["karol"]
    ola_id, token = await players.register(client, "ola")
    ola = {"id": ola_id, "token": token, "headers": players.auth(token)}
    joined = await join(client, ola, {"id": karol["group"]})
    assert joined.status_code in (200, 201), joined.text
    await befriend(client, {**ola, "group": karol["group"]}, karol)
    await a_while_ago(session_factory, clock, (karol, 2.75))

    read = await friends_view(client, ola)

    assert read["card"]["state"] == "NO_LEVEL"
    assert names(read) == ["karol"]


# --------------------------------------------------------------------------- #
# Home's Friends place
# --------------------------------------------------------------------------- #


async def test_home_carries_the_friends_place_beside_the_general_one(
    client, session_factory, clock, five
):
    tomek, karol, zofia, ines, ewa = five.values()
    for friend in (karol, ewa):
        await befriend(client, tomek, friend)
    for player, level in (
        (ines, 3.40),
        (karol, 2.75),
        (zofia, 2.73),
        (tomek, 2.71),
        (ewa, 2.68),
    ):
        await results_at(session_factory, player, [level] * 5, clock)

    assert await home_ranking(client, tomek) == {
        "sport": "PADEL",
        "general_place": 4,
        "friends_place": 2,
    }
    assert (await friends_view(client, tomek))["card"]["place"] == 2
