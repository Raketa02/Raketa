"""**Ask for a level** — over HTTP as the player app calls it (``docs/adr/0202``
§4; the mechanics §5, §12; the words §29.5; #749).

The cast:

- **Tomek** plays padel in **Ogrody open play**. **Zofia** joined it, is his
  friend, and has **no padel level**, so his picker greys her. He asks her from
  Ogrody's picker; she is told *"tomek wants to play padel with you."*, which
  opens the padel questionnaire. She finishes it, and he is told *"zofia has a
  padel level — you can seat zofia now."*, which opens Ogrody's picker.
- **Ewa** is Zofia's friend from **Kazimierz crew**, and asks her too: both are
  told, each naming the group they asked from.
- **Kuba** is in Ogrody and is nobody's friend.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.kernel import Sport
from tests.api import players_world as players
from tests.api.test_friends import (
    accepts,
    asked,
    bell_of,
    blocks,
    friends_of,
    has_a_phone,
)
from tests.api.test_group_members import a_padel_player
from tests.api.test_groups import a_club, a_group, a_player, join

FRIENDS = "/api/v1/friends"


@pytest.fixture
async def ogrody(client) -> dict[str, dict]:
    """Ogrody open play, with Zofia a friend of Tomek's and of Ewa's — Ewa's
    from Kazimierz crew, a group Tomek is not in."""

    tomek = await a_padel_player(client, "tomek")
    ogrody = await a_group(client, tomek, await a_club(client), name="Ogrody open play")
    ewa = await a_padel_player(client, "ewa")
    kazimierz = await a_group(
        client, ewa, await a_club(client, "Wisła Park"), name="Kazimierz crew"
    )
    # Rated in nothing: no padel level.
    zofia_id, token = await players.register(client, "zofia")
    zofia = {"id": zofia_id, "headers": players.auth(token), "token": token}
    kuba = await a_padel_player(client, "kuba")
    for player, group in ((zofia, ogrody), (kuba, ogrody), (zofia, kazimierz)):
        joined = await join(client, player, group)
        assert joined.status_code in (200, 201), joined.text
    for friend, group in ((tomek, ogrody), (ewa, kazimierz)):
        await asked(client, friend, zofia, group)
        accepted = await accepts(client, zofia, friend)
        assert accepted.status_code == 200, accepted.text
    return {
        "tomek": tomek,
        "ewa": ewa,
        "zofia": zofia,
        "kuba": kuba,
        "ogrody": ogrody,
        "kazimierz": kazimierz,
    }


async def asks_for_a_level(
    client, asker: dict, friend_id, group: dict, sport: str = "PADEL"
):
    return await client.post(
        f"{FRIENDS}/{friend_id}/level-asks",
        json={"sport": sport, "group_id": group["id"]},
        headers=asker["headers"],
    )


async def asked_for_a_level(
    client, asker: dict, friend: dict, group: dict, sport: str = "PADEL"
) -> None:
    answer = await asks_for_a_level(client, asker, friend["id"], group, sport)
    assert answer.status_code == 204, answer.text


def row_of(rows: list[dict], player: dict) -> dict:
    [row] = [row for row in rows if row["player_id"] == str(player["id"])]
    return row


def refused(answer, status: int, code: str) -> None:
    assert answer.status_code == status, answer.text
    assert answer.json()["code"] == code


# --------------------------------------------------------------------------- #
# The ask, and the picker reading *Asked*
# --------------------------------------------------------------------------- #


async def test_a_friend_with_no_level_is_asked_and_the_picker_reads_asked(
    client, ogrody
):
    tomek, zofia, group = ogrody["tomek"], ogrody["zofia"], ogrody["ogrody"]
    before = row_of(await friends_of(client, tomek, sport="PADEL"), zofia)
    assert (before["sports"], before["level_asked_in"]) == ([], [])

    await asked_for_a_level(client, tomek, zofia, group)

    picker = row_of(await friends_of(client, tomek, sport="PADEL"), zofia)
    assert (picker["sports"], picker["level_asked_in"]) == ([], ["PADEL"])
    # Without a sport, every sport asked; with another, none.
    assert row_of(await friends_of(client, tomek), zofia)["level_asked_in"] == ["PADEL"]
    tennis = row_of(await friends_of(client, tomek, sport="TENNIS"), zofia)
    assert tennis["level_asked_in"] == []
    # Only the asker reads it: Zofia's own list says nothing about Tomek.
    assert row_of(await friends_of(client, zofia), tomek)["level_asked_in"] == []


async def test_asking_is_once_per_sport_ever(client, ogrody):
    tomek, zofia, group = ogrody["tomek"], ogrody["zofia"], ogrody["ogrody"]
    await asked_for_a_level(client, tomek, zofia, group)

    refused(
        await asks_for_a_level(client, tomek, zofia["id"], group),
        409,
        "level_already_asked",
    )
    # Another sport is another ask.
    await asked_for_a_level(client, tomek, zofia, group, sport="TENNIS")
    # A friendship removed and made again asks nobody twice.
    removed = await client.delete(f"{FRIENDS}/{tomek['id']}", headers=zofia["headers"])
    assert removed.status_code == 204, removed.text
    await asked(client, zofia, tomek, group)
    await accepts(client, tomek, zofia)
    refused(
        await asks_for_a_level(client, tomek, zofia["id"], group),
        409,
        "level_already_asked",
    )


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


async def test_only_a_friend_is_asked(client, ogrody):
    tomek, zofia, kuba, group = (
        ogrody["tomek"],
        ogrody["zofia"],
        ogrody["kuba"],
        ogrody["ogrody"],
    )
    newcomer = await a_player(client, "newcomer")
    joined = await join(client, newcomer, group)
    assert joined.status_code in (200, 201), joined.text

    # A group-mate who is no friend, rated or not; an id nobody holds; oneself.
    for not_a_friend in (kuba["id"], newcomer["id"], uuid4(), tomek["id"]):
        refused(
            await asks_for_a_level(client, tomek, not_a_friend, group),
            404,
            "friend_not_found",
        )
    # A friend removed is a friend no longer.
    await client.delete(f"{FRIENDS}/{zofia['id']}", headers=tomek["headers"])
    refused(
        await asks_for_a_level(client, tomek, zofia["id"], group),
        404,
        "friend_not_found",
    )


async def test_a_friendship_a_block_ended_asks_nothing_either_way(
    client, session_factory, ogrody
):
    tomek, zofia, group = ogrody["tomek"], ogrody["zofia"], ogrody["ogrody"]

    await blocks(client, session_factory, zofia, tomek)

    refused(
        await asks_for_a_level(client, tomek, zofia["id"], group),
        404,
        "friend_not_found",
    )


async def test_a_friend_with_a_level_in_the_sport_is_not_asked(client, ogrody):
    tomek, group = ogrody["tomek"], ogrody["ogrody"]
    magda = await a_padel_player(client, "magda")
    await join(client, magda, group)
    await asked(client, tomek, magda, group)
    await accepts(client, magda, tomek)

    refused(
        await asks_for_a_level(client, tomek, magda["id"], group),
        409,
        "already_has_a_level",
    )
    # The sport she has no level in is askable.
    await asked_for_a_level(client, tomek, magda, group, sport="SQUASH")


async def test_the_ask_is_made_from_one_of_the_askers_groups(client, ogrody):
    tomek, zofia = ogrody["tomek"], ogrody["zofia"]

    for not_his in (ogrody["kazimierz"], {"id": str(uuid4())}):
        refused(
            await asks_for_a_level(client, tomek, zofia["id"], not_his),
            404,
            "not_one_of_your_groups",
        )
    # Nothing was asked.
    picker = row_of(await friends_of(client, tomek, sport="PADEL"), zofia)
    assert picker["level_asked_in"] == []


# --------------------------------------------------------------------------- #
# Level asked — to the friend
# --------------------------------------------------------------------------- #


async def test_the_friend_is_told_and_it_opens_the_sports_questionnaire(
    client, mailbox, pushes, ogrody
):
    tomek, zofia, group = ogrody["tomek"], ogrody["zofia"], ogrody["ogrody"]
    await bell_of(client, mailbox, zofia)
    phone = await has_a_phone(client, zofia, "zofia")
    before = len((await bell_of(client, mailbox, zofia))["notices"])

    await asked_for_a_level(client, tomek, zofia, group)

    bell = await bell_of(client, mailbox, zofia)
    [notice] = [n for n in bell["notices"] if n["kind"] == "LEVEL_ASKED"]
    assert len(bell["notices"]) == before + 1
    assert notice["title"] == "tomek wants to play padel with you."
    assert notice["body"] == "Get your padel level so tomek can add you."
    assert notice["opens"] == "QUESTIONNAIRE"
    assert notice["sport"] == "PADEL"
    assert notice["player_id"] == str(tomek["id"])
    assert notice["game_id"] is None
    assert notice["new"] is True
    [push] = [p for p in pushes.to(phone) if p.data["kind"] == "LEVEL_ASKED"]
    assert (push.title, push.body) == (notice["title"], notice["body"])
    assert push.data == {
        "notice_id": notice["notice_id"],
        "kind": "LEVEL_ASKED",
        "opens": "QUESTIONNAIRE",
        "player_id": str(tomek["id"]),
        "sport": "PADEL",
    }
    # The asker is told nothing of his own ask.
    assert not [
        n
        for n in (await bell_of(client, mailbox, tomek))["notices"]
        if n["kind"].startswith("LEVEL_")
    ]


async def test_an_ask_is_told_nobody_once_they_are_no_longer_friends(
    client, mailbox, ogrody
):
    tomek, zofia, group = ogrody["tomek"], ogrody["zofia"], ogrody["ogrody"]
    await asked_for_a_level(client, tomek, zofia, group)
    await client.delete(f"{FRIENDS}/{tomek['id']}", headers=zofia["headers"])

    bell = await bell_of(client, mailbox, zofia)

    assert not [n for n in bell["notices"] if n["kind"] == "LEVEL_ASKED"]


# --------------------------------------------------------------------------- #
# Level got — to whoever asked
# --------------------------------------------------------------------------- #


async def test_the_asker_is_told_when_the_friend_gets_the_level(
    client, mailbox, pushes, ogrody
):
    tomek, zofia, group = ogrody["tomek"], ogrody["zofia"], ogrody["ogrody"]
    phone = await has_a_phone(client, tomek, "tomek")
    await asked_for_a_level(client, tomek, zofia, group)
    await bell_of(client, mailbox, tomek)

    await players.rate(client, zofia["token"], Sport.PADEL)

    [told] = [
        n
        for n in (await bell_of(client, mailbox, tomek))["notices"]
        if n["kind"] == "LEVEL_GOT"
    ]
    assert told["title"] == "zofia has a padel level — you can seat zofia now."
    assert told["body"] == "In Ogrody open play, on the Friends tab."
    assert told["opens"] == "PICKER"
    assert told["pool_id"] == group["id"]
    assert told["sport"] == "PADEL"
    assert told["player_id"] == str(zofia["id"])
    [push] = [p for p in pushes.to(phone) if p.data["kind"] == "LEVEL_GOT"]
    assert push.data == {
        "notice_id": told["notice_id"],
        "kind": "LEVEL_GOT",
        "opens": "PICKER",
        "player_id": str(zofia["id"]),
        "pool_id": group["id"],
        "sport": "PADEL",
    }
    # And she is on his picker now, with her level.
    picker = row_of(await friends_of(client, tomek, sport="PADEL"), zofia)
    assert [sport["sport"] for sport in picker["sports"]] == ["PADEL"]


async def test_two_friends_who_asked_are_both_told_each_naming_their_group(
    client, mailbox, ogrody
):
    tomek, ewa, zofia = ogrody["tomek"], ogrody["ewa"], ogrody["zofia"]
    await asked_for_a_level(client, tomek, zofia, ogrody["ogrody"])
    await asked_for_a_level(client, ewa, zofia, ogrody["kazimierz"])

    await players.rate(client, zofia["token"], Sport.PADEL)

    for asker, group in ((tomek, ogrody["ogrody"]), (ewa, ogrody["kazimierz"])):
        [told] = [
            n
            for n in (await bell_of(client, mailbox, asker))["notices"]
            if n["kind"] == "LEVEL_GOT"
        ]
        assert told["pool_id"] == group["id"]
        assert told["body"] == f"In {group['name']}, on the Friends tab."
    # Kuba asked nothing, and is told nothing.
    assert not [
        n
        for n in (await bell_of(client, mailbox, ogrody["kuba"]))["notices"]
        if n["kind"] == "LEVEL_GOT"
    ]


async def test_a_level_in_another_sport_answers_nothing(client, mailbox, ogrody):
    tomek, zofia = ogrody["tomek"], ogrody["zofia"]
    await asked_for_a_level(client, tomek, zofia, ogrody["ogrody"])

    await players.rate(client, zofia["token"], Sport.TENNIS)

    assert not [
        n
        for n in (await bell_of(client, mailbox, tomek))["notices"]
        if n["kind"] == "LEVEL_GOT"
    ]


async def test_nobody_is_told_the_level_once_they_are_no_longer_friends(
    client, mailbox, ogrody
):
    tomek, zofia = ogrody["tomek"], ogrody["zofia"]
    await asked_for_a_level(client, tomek, zofia, ogrody["ogrody"])
    await bell_of(client, mailbox, tomek)
    await client.delete(f"{FRIENDS}/{tomek['id']}", headers=zofia["headers"])

    await players.rate(client, zofia["token"], Sport.PADEL)

    assert not [
        n
        for n in (await bell_of(client, mailbox, tomek))["notices"]
        if n["kind"] == "LEVEL_GOT"
    ]
