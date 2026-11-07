"""**A friend's ask for a level waits on their Home** — over HTTP as the player
app calls it (#764; ``docs/adr/0202`` §4's 2026-11-07 amendment; the friends
mechanics §5.1, §12; Q129).

The cast, all in **Ogrody open play**, a padel group:

- **Zofia** is rated in tennis and holds **no padel level**. Tomek, Kuba and Ania
  are her friends, each rated in padel.
- **Tomek** and then **Kuba** ask her for a padel level: her Home lists padel,
  naming kuba then tomek. She says **Not now**: padel leaves her Home and both
  *level asked* rows leave her bell. Nobody is told.
- **Ania** then asks her for padel: padel is back, naming only ania.
- Zofia finishes the padel questionnaire: padel leaves her Home at once, and
  Tomek, Kuba and Ania are all told *level got*.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.kernel import Sport
from tests.api import players_world as players
from tests.api.test_friends import accepts, asked, bell_of, blocks, friends_of
from tests.api.test_group_members import a_padel_player
from tests.api.test_groups import a_club, a_group, join
from tests.api.test_level_asks import asked_for_a_level, row_of

FRIENDS = "/api/v1/friends"
HOME = "/api/v1/home"
NOTICES = "/api/v1/players/me/notices"


@pytest.fixture
async def ogrody(client, clock) -> dict[str, dict]:
    """Ogrody open play: Zofia, rated in tennis alone, a friend of Tomek's,
    Kuba's and Ania's."""

    tomek = await a_padel_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client), name="Ogrody open play")
    zofia_id, token = await players.register(client, "zofia")
    await players.rate(client, token, Sport.TENNIS)
    zofia = {"id": zofia_id, "headers": players.auth(token), "token": token}
    cast = {"tomek": tomek, "zofia": zofia, "group": group}
    for name in ("kuba", "ania"):
        cast[name] = await a_padel_player(client, name)
    for player in (zofia, cast["kuba"], cast["ania"]):
        joined = await join(client, player, group)
        assert joined.status_code in (200, 201), joined.text
    for friend in (tomek, cast["kuba"], cast["ania"]):
        await asked(client, friend, zofia, group)
        accepted = await accepts(client, zofia, friend)
        assert accepted.status_code == 200, accepted.text
    return cast


async def asks_her(client, clock, ogrody, *askers: str, sport: str = "PADEL"):
    """Each asks Zofia in turn, a minute apart, so newest first has an order."""

    for asker in askers:
        clock.move(timedelta(minutes=1))
        await asked_for_a_level(
            client, ogrody[asker], ogrody["zofia"], ogrody["group"], sport
        )


async def home_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def cards_of(client, player: dict) -> list[tuple[str, list[str]]]:
    """Home's ASKED FOR A LEVEL, as each card names its askers."""

    return [
        (card["sport"], [asker["nickname"] for asker in card["askers"]])
        for card in (await home_of(client, player))["level_asks"]
    ]


async def not_now(client, player: dict, sport: str = "PADEL"):
    return await client.post(
        f"{FRIENDS}/level-asks/{sport}/set-aside", headers=player["headers"]
    )


async def says_not_now(client, player: dict, sport: str = "PADEL") -> None:
    answer = await not_now(client, player, sport)
    assert answer.status_code == 204, answer.text


async def bell_unread(client, player: dict) -> dict:
    """The bell as it reads **now** — nothing delivered first."""

    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


def level_asked_rows(bell: dict) -> list[tuple[str, str]]:
    return [
        (notice["player_id"], notice["sport"])
        for notice in bell["notices"]
        if notice["kind"] == "LEVEL_ASKED"
    ]


def told_level_got(bell: dict) -> list[dict]:
    return [notice for notice in bell["notices"] if notice["kind"] == "LEVEL_GOT"]


# --------------------------------------------------------------------------- #
# The card: one per sport, its askers newest first
# --------------------------------------------------------------------------- #


async def test_one_ask_is_one_card_on_the_friends_home(client, clock, ogrody):
    tomek, zofia = ogrody["tomek"], ogrody["zofia"]

    await asks_her(client, clock, ogrody, "tomek")

    [card] = (await home_of(client, zofia))["level_asks"]
    assert card == {
        "sport": "PADEL",
        "askers": [
            {
                "player_id": str(tomek["id"]),
                "nickname": "tomek",
                "photo_id": None,
                "photo_url": None,
            }
        ],
    }
    # The asker's own Home draws nothing of it.
    assert (await home_of(client, tomek))["level_asks"] == []


async def test_two_askers_are_named_newest_first(client, clock, ogrody):
    await asks_her(client, clock, ogrody, "tomek", "kuba")

    assert await cards_of(client, ogrody["zofia"]) == [("PADEL", ["kuba", "tomek"])]


async def test_two_sports_are_two_cards_the_newest_ask_first(client, clock, ogrody):
    await asks_her(client, clock, ogrody, "tomek")
    await asks_her(client, clock, ogrody, "kuba", sport="SQUASH")

    assert await cards_of(client, ogrody["zofia"]) == [
        ("SQUASH", ["kuba"]),
        ("PADEL", ["tomek"]),
    ]

    await asks_her(client, clock, ogrody, "ania")

    assert await cards_of(client, ogrody["zofia"]) == [
        ("PADEL", ["ania", "tomek"]),
        ("SQUASH", ["kuba"]),
    ]


async def test_an_ask_is_not_counted_among_the_games_that_need_you(
    client, clock, ogrody
):
    before = (await home_of(client, ogrody["zofia"]))["needing_you"]

    await asks_her(client, clock, ogrody, "tomek", "kuba")
    await asks_her(client, clock, ogrody, "ania", sport="SQUASH")

    assert (await home_of(client, ogrody["zofia"]))["needing_you"] == before == 0


# --------------------------------------------------------------------------- #
# Not now
# --------------------------------------------------------------------------- #


async def test_not_now_takes_the_sport_off_home_and_the_bell_and_tells_nobody(
    client, clock, mailbox, ogrody
):
    tomek, kuba, zofia = ogrody["tomek"], ogrody["kuba"], ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek", "kuba")
    bell = await bell_of(client, mailbox, zofia)
    assert sorted(level_asked_rows(bell)) == sorted(
        [(str(tomek["id"]), "PADEL"), (str(kuba["id"]), "PADEL")]
    )
    count = bell["new_count"]
    theirs = {
        name: len((await bell_of(client, mailbox, ogrody[name]))["notices"])
        for name in ("tomek", "kuba")
    }

    await says_not_now(client, zofia)

    assert await cards_of(client, zofia) == []
    bell = await bell_of(client, mailbox, zofia)
    assert level_asked_rows(bell) == []
    assert bell["new_count"] == count - 2
    # Nobody is told, and each asker's picker still reads *Asked*.
    for name in ("tomek", "kuba"):
        bell = await bell_of(client, mailbox, ogrody[name])
        assert len(bell["notices"]) == theirs[name]
        picker = row_of(await friends_of(client, ogrody[name], sport="PADEL"), zofia)
        assert picker["level_asked_in"] == ["PADEL"]


async def test_not_now_sets_aside_one_sport_alone(client, clock, ogrody):
    await asks_her(client, clock, ogrody, "tomek")
    await asks_her(client, clock, ogrody, "kuba", sport="SQUASH")

    await says_not_now(client, ogrody["zofia"], "SQUASH")

    assert await cards_of(client, ogrody["zofia"]) == [("PADEL", ["tomek"])]


async def test_a_new_ask_brings_the_sport_back_naming_only_the_new_asker(
    client, clock, mailbox, ogrody
):
    ania, zofia = ogrody["ania"], ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek", "kuba")
    await says_not_now(client, zofia)

    await asks_her(client, clock, ogrody, "ania")

    assert await cards_of(client, zofia) == [("PADEL", ["ania"])]
    assert level_asked_rows(await bell_of(client, mailbox, zofia)) == [
        (str(ania["id"]), "PADEL")
    ]


async def test_a_level_after_not_now_is_told_to_every_asker(
    client, clock, mailbox, ogrody
):
    zofia = ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek", "kuba")
    await says_not_now(client, zofia)
    await asks_her(client, clock, ogrody, "ania")

    await players.rate(client, zofia["token"], Sport.PADEL)

    assert await cards_of(client, zofia) == []
    for name in ("tomek", "kuba", "ania"):
        [told] = told_level_got(await bell_of(client, mailbox, ogrody[name]))
        assert told["player_id"] == str(zofia["id"])
        assert told["sport"] == "PADEL"


async def test_not_now_with_nothing_waiting_answers_the_same(client, clock, ogrody):
    zofia = ogrody["zofia"]

    await says_not_now(client, zofia)
    await asks_her(client, clock, ogrody, "tomek")
    # Another sport, nothing asked in it; and the sport again, already aside.
    await says_not_now(client, zofia, "SQUASH")
    assert await cards_of(client, zofia) == [("PADEL", ["tomek"])]
    await says_not_now(client, zofia)
    await says_not_now(client, zofia)

    assert await cards_of(client, zofia) == []
    # The asker's own press sets aside nothing of his.
    await says_not_now(client, ogrody["tomek"])
    assert (await home_of(client, ogrody["tomek"]))["level_asks"] == []


# --------------------------------------------------------------------------- #
# The card ends by itself
# --------------------------------------------------------------------------- #


async def test_a_level_by_another_route_takes_the_card_off_before_level_got_is_told(
    client, clock, mailbox, ogrody
):
    tomek, zofia = ogrody["tomek"], ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek")
    assert level_asked_rows(await bell_of(client, mailbox, zofia)) == [
        (str(tomek["id"]), "PADEL")
    ]
    count = (await bell_unread(client, zofia))["new_count"]
    await bell_of(client, mailbox, tomek)

    # The passport's questionnaire — nothing delivered since.
    await players.rate(client, zofia["token"], Sport.PADEL)

    assert await cards_of(client, zofia) == []
    bell = await bell_unread(client, zofia)
    assert level_asked_rows(bell) == []
    assert bell["new_count"] == count - 1
    assert told_level_got(await bell_unread(client, tomek)) == []
    # Then the answer is delivered, as it always was.
    assert len(told_level_got(await bell_of(client, mailbox, tomek))) == 1


async def test_a_removal_and_a_block_take_the_asker_off_and_the_last_the_sport(
    client, clock, mailbox, ogrody
):
    tomek, kuba, zofia = ogrody["tomek"], ogrody["kuba"], ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek", "kuba")
    await bell_of(client, mailbox, zofia)

    removed = await client.delete(f"{FRIENDS}/{tomek['id']}", headers=zofia["headers"])
    assert removed.status_code == 204, removed.text

    assert await cards_of(client, zofia) == [("PADEL", ["kuba"])]
    assert level_asked_rows(await bell_unread(client, zofia)) == [
        (str(kuba["id"]), "PADEL")
    ]

    # Her own block takes him off at once — before its delivery ends anything.
    made = await players.block_between(client, zofia["token"], kuba["id"])
    assert made.status_code == 204, made.text

    assert await cards_of(client, zofia) == []
    assert level_asked_rows(await bell_unread(client, zofia)) == []


async def test_an_askers_block_takes_them_off_once_its_delivery_has_run(
    client, clock, session_factory, ogrody
):
    await asks_her(client, clock, ogrody, "ania")

    await blocks(client, session_factory, ogrody["ania"], ogrody["zofia"])

    assert await cards_of(client, ogrody["zofia"]) == []


async def test_a_friend_removed_and_made_again_is_back_unless_set_aside(
    client, clock, ogrody
):
    """A call #763 recorded (the friends mechanics §15): the card reads
    friendship live, so an ask still waiting comes back with the friend — and
    one set aside stays aside."""

    tomek, kuba, zofia, group = (
        ogrody["tomek"],
        ogrody["kuba"],
        ogrody["zofia"],
        ogrody["group"],
    )
    await asks_her(client, clock, ogrody, "tomek", "kuba")
    for friend in (tomek, kuba):
        await client.delete(f"{FRIENDS}/{friend['id']}", headers=zofia["headers"])
    assert await cards_of(client, zofia) == []
    # Not now while neither is a friend sets aside nothing Home did not list.
    await says_not_now(client, zofia)

    await asked(client, zofia, tomek, group)
    await accepts(client, tomek, zofia)

    assert await cards_of(client, zofia) == [("PADEL", ["tomek"])]
    await says_not_now(client, zofia)
    # Kuba's was never set aside: Home did not list it then.
    await asked(client, zofia, kuba, group)
    await accepts(client, kuba, zofia)
    assert await cards_of(client, zofia) == [("PADEL", ["kuba"])]
    await says_not_now(client, zofia)

    for friend in (tomek, kuba):
        await client.delete(f"{FRIENDS}/{friend['id']}", headers=zofia["headers"])
        await asked(client, zofia, friend, group)
        await accepts(client, friend, zofia)

    assert await cards_of(client, zofia) == []
