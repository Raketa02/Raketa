"""Members, for one sport — over HTTP, as the player app calls it (#506,
``docs/adr/0183`` §10).

Tomek opens Members for padel in Kazimierz crew. He sees himself first, then
Karol, the Owner, then everybody else newest first, each with their padel Level
and Player Score. Zofia blocked Kuba long ago, and **both still see each other**
there: a block keeps two people off one court and hides nobody in a crowd
everybody can see (``docs/adr/0193`` §2, superseding ADR-0183 §10).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.kernel import Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.presentation.dependencies import get_block_query
from tests.api import players_world as players
from tests.api.test_player_record import a_game_not_come_to
from tests.api.test_groups import (
    GROUPS,
    a_club,
    a_group,
    a_player,
    join,
    read,
)


async def a_padel_player(client, name: str, *also: Sport) -> dict:
    """A player rated in padel, and the Level the rating published for them."""

    player_id, token = await players.register(client, name)
    level = await players.rate(client, token, Sport.PADEL)
    for sport in also:
        await players.rate(client, token, sport)
    return {"id": player_id, "headers": players.auth(token), "level": level}


async def members(client, reader: dict, group: dict, sport: str = "PADEL"):
    return await client.get(
        f"{GROUPS}/{group['id']}/members",
        params={"sport": sport},
        headers=reader["headers"],
    )


async def listed(client, reader: dict, group: dict, sport: str = "PADEL") -> list:
    answer = await members(client, reader, group, sport)
    assert answer.status_code == 200, answer.text
    assert answer.json()["sport"] == sport
    return answer.json()["members"]


def names(rows: list[dict]) -> list[str]:
    return [row["nickname"] for row in rows]


async def block(client, blocker: dict, blocked: dict) -> None:
    blocked_ = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"])},
        headers=blocker["headers"],
    )
    assert blocked_.status_code in (200, 201, 204), blocked_.text


# --------------------------------------------------------------------------- #
# Who, and in what order
# --------------------------------------------------------------------------- #


async def test_the_caller_first_then_the_owner_then_everybody_newest_first(client):
    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    ania = await a_padel_player(client, "ania")
    tomek = await a_padel_player(client, "tomek")
    ewa = await a_padel_player(client, "ewa")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, ania, tomek, ewa):
        await join(client, member, group)

    rows = await listed(client, tomek, group)

    assert names(rows) == ["tomek", "karol", "ewa", "ania", "zofia"]
    assert [row["is_owner"] for row in rows] == [False, True, False, False, False]


async def test_the_owner_reading_is_the_caller_and_comes_first_once(client):
    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    ania = await a_padel_player(client, "ania")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, ania):
        await join(client, member, group)

    assert names(await listed(client, karol, group)) == ["karol", "ania", "zofia"]


async def test_only_the_members_rated_in_the_sport_are_listed(client):
    karol = await a_padel_player(client, "karol", Sport.TENNIS)
    zofia = await a_padel_player(client, "zofia")
    fred = await a_player(client, "fred")
    tomasz_id, token = await players.register(client, "tomasz")
    await players.rate(client, token, Sport.TENNIS)
    tomasz = {"id": tomasz_id, "headers": players.auth(token)}
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, fred, tomasz):
        await join(client, member, group)

    assert names(await listed(client, zofia, group)) == ["zofia", "karol"]
    # Somebody not rated in the sport asked is not in its list — themselves
    # included.
    assert names(await listed(client, tomasz, group, "TENNIS")) == [
        "tomasz",
        "karol",
    ]
    assert names(await listed(client, fred, group)) == ["karol", "zofia"]
    assert await listed(client, fred, group, "SQUASH") == []
    # The count is every member, whoever is listed where.
    assert (await read(client, fred, group)).json()["member_count"] == 4


async def test_a_row_is_a_face_the_level_in_that_sport_and_when_they_joined(client):
    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    group = await a_group(client, karol, await a_club(client))
    await join(client, zofia, group)

    owner, member = await listed(client, karol, group)

    # Nothing has happened to anybody here yet, and everyone starts at a
    # hundred (#659): every row carries the figure and its band.
    assert set(owner) == {
        "player_id",
        "nickname",
        "level",
        "player_score",
        "reliability_band",
        "is_owner",
        "is_administrator",
        "joined_at",
        "relation",
    }
    assert (owner["player_score"], owner["reliability_band"]) == (100, "VERY_HIGH")
    # The reader's own row reads nothing; nothing stands between the two yet.
    assert owner["relation"] == member["relation"] == "NONE"
    assert owner["player_id"] == str(karol["id"])
    # A player group is run by its Owner, never by an Administrator.
    assert owner["is_administrator"] is member["is_administrator"] is False
    assert owner["level"] == karol["level"]
    assert member["level"] == zofia["level"]
    assert owner["joined_at"] < member["joined_at"]


async def test_a_member_s_row_carries_their_points_and_band(client, session_factory):
    """The figure and the word their own record prints (``docs/adr/0195`` §6):
    Zofia played one game through and Didn't come to another — 75, High."""

    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    group = await a_group(client, karol, await a_club(client))
    await join(client, zofia, group)
    await players.a_confirmed_game(
        session_factory, UUID(str(zofia["id"])), uuid4(), sport=Sport.PADEL, a_won=True
    )
    await a_game_not_come_to(
        session_factory, UUID(str(zofia["id"])), uuid4(), sport=Sport.PADEL
    )

    rows = await listed(client, karol, group)

    assert (rows[0]["player_score"], rows[0]["reliability_band"]) == (
        100,
        "VERY_HIGH",
    )
    assert (rows[1]["player_score"], rows[1]["reliability_band"]) == (75, "HIGH")


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


async def test_a_blocked_pair_still_sees_each_other_in_the_list_either_way(client):
    """**Members hides nobody for a block** (``docs/adr/0193`` §2). Hiding a
    member of a crowd everybody can see would itself be the tell."""

    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    kuba = await a_padel_player(client, "kuba")
    tomek = await a_padel_player(client, "tomek")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, kuba, tomek):
        await join(client, member, group)
    before = {
        reader["id"]: (await members(client, reader, group)).text
        for reader in (zofia, kuba, tomek)
    }

    await block(client, zofia, kuba)

    assert names(await listed(client, zofia, group)) == [
        "zofia",
        "karol",
        "tomek",
        "kuba",
    ]
    assert names(await listed(client, kuba, group)) == [
        "kuba",
        "karol",
        "tomek",
        "zofia",
    ]
    # Byte for byte what each read before the block — nobody's list moved.
    for reader in (zofia, kuba, tomek):
        assert (await members(client, reader, group)).text == before[reader["id"]]


async def test_a_blocked_owner_is_listed_too(client):
    karol = await a_padel_player(client, "karol")
    kuba = await a_padel_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)

    await block(client, kuba, karol)

    assert names(await listed(client, kuba, group)) == ["kuba", "karol"]
    assert names(await listed(client, karol, group)) == ["karol", "kuba"]


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


async def test_members_are_for_members(client):
    karol = await a_padel_player(client, "karol")
    kuba = await a_padel_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))

    stranger = await members(client, kuba, group)
    nothing = await members(client, kuba, {"id": str(uuid4())})

    assert stranger.status_code == nothing.status_code == 404
    assert stranger.json()["code"] == nothing.json()["code"] == "group_not_found"


async def test_members_are_asked_for_one_sport(client):
    karol = await a_padel_player(client, "karol")
    group = await a_group(client, karol, await a_club(client))

    unnamed = await client.get(
        f"{GROUPS}/{group['id']}/members", headers=karol["headers"]
    )
    unknown = await members(client, karol, group, "PINGPONG")

    assert unnamed.status_code == unknown.status_code == 422


# --------------------------------------------------------------------------- #
# The Info tab's members row, and the Games tab's faces
# --------------------------------------------------------------------------- #


async def test_the_members_row_stacks_five_faces_in_the_members_order(client):
    """Play 58–59: the Owner, then the newest — everybody but the reader, whose
    own row it is — and the count is every member."""

    karol = await a_player(client, "karol")
    joiners = {
        name: await a_player(client, name)
        for name in ("zofia", "ania", "tomek", "ewa", "marek", "ola")
    }
    group = await a_group(client, karol, await a_club(client))
    for member in joiners.values():
        await join(client, member, group)

    body = (await read(client, joiners["tomek"], group)).json()

    assert body["member_count"] == 7
    assert names(body["member_faces"]) == ["karol", "ola", "marek", "ewa", "ania"]


async def test_the_members_row_keeps_a_blocked_pair(client):
    karol = await a_player(client, "karol")
    zofia = await a_player(client, "zofia")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, kuba):
        await join(client, member, group)

    await block(client, zofia, kuba)

    as_zofia = (await read(client, zofia, group)).json()
    as_kuba = (await read(client, kuba, group)).json()
    assert names(as_zofia["member_faces"]) == ["karol", "kuba"]
    assert names(as_kuba["member_faces"]) == ["karol", "zofia"]
    assert as_zofia["member_count"] == as_kuba["member_count"] == 3


async def test_alone_the_members_row_has_nobody_else_to_stack(client):
    tomek = await a_player(client, "tomek")

    group = await a_group(client, tomek, await a_club(client))

    assert group["member_faces"] == []
    assert (await read(client, tomek, group)).json()["member_faces"] == []


async def test_a_block_does_not_reach_the_games_tab_s_seats(client):
    """The Games tab's seats are the first rated members **in joining order**
    (ADR-0183 §13), whoever reads them (#504) — and a block hides nobody there
    either (``docs/adr/0193`` §2)."""

    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    kuba = await a_padel_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, kuba):
        await join(client, member, group)

    await block(client, zofia, kuba)

    body = (await read(client, zofia, group)).json()
    padel = next(row for row in body["rated_by_sport"] if row["sport"] == "PADEL")
    assert names(padel["first_rated"]) == ["karol", "zofia", "kuba"]


# --------------------------------------------------------------------------- #
# When who is blocked cannot be read
# --------------------------------------------------------------------------- #


class Unreadable:
    """A block state nobody can read. Every route onto a court refuses on it
    (``docs/adr/0095`` §5); a group's pages never ask it."""

    async def exclusions_for(self, player_id):
        raise BlockStateUnavailable("the block store is unreachable")

    async def blocked_between(self, first, second):
        raise BlockStateUnavailable("the block store is unreachable")

    async def blocked_pairs_among(self, player_ids):
        raise BlockStateUnavailable("the block store is unreachable")

    async def blocks_made_by(self, blocker_id):
        raise BlockStateUnavailable("the block store is unreachable")


def blocks_unreadable(client) -> None:
    players.override(client, get_block_query, Unreadable)


async def test_an_unreadable_block_state_takes_no_members_list_down(client):
    """**Fewer things fail** (``docs/adr/0193``, Consequences): under the old
    rule an unreadable block state was an outage of Members and the group's
    page. Neither reads it now."""

    karol = await a_padel_player(client, "karol")
    kuba = await a_padel_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)
    blocks_unreadable(client)

    listing = await members(client, kuba, group)
    page = await read(client, kuba, group)
    edited = await client.put(
        f"{GROUPS}/{group['id']}/details",
        json={"name": "renamed", "join_policy": "ANYONE"},
        headers=karol["headers"],
    )

    assert listing.status_code == page.status_code == 200, listing.text
    assert names(listing.json()["members"]) == ["kuba", "karol"]
    assert edited.status_code == 200, edited.text
