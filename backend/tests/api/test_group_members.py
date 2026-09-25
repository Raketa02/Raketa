"""Members, for one sport — over HTTP, as the player app calls it (#506,
``docs/adr/0183`` §10).

Tomek opens Members for padel in Kazimierz crew. He sees himself first, then
Karol, the Owner, then everybody else newest first, each with their padel Level
and Player Score. Zofia blocked Kuba long ago, so neither sees the other in the
list — and the group's member count is the same for both of them.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.kernel import Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.groups.presentation.dependencies import get_hidden_members
from tests.api import matchmaking_world as world
from tests.api.test_groups import (
    GROUPS,
    a_club,
    a_group,
    a_player,
    join,
    read,
)
from tests.api.test_join_requests import an_approval_group, approve, waiting
from tests.api.test_join_search import search
from tests.api.test_player_record import a_confirmed_game


async def a_padel_player(client, name: str, *also: Sport) -> dict:
    """A player rated in padel, and the Level the rating published for them."""

    player_id, token = await world.register(client, name)
    level = await world.rate(client, token, Sport.PADEL)
    for sport in also:
        await world.rate(client, token, sport)
    return {"id": player_id, "headers": world.auth(token), "level": level}


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
    return [row["name"] for row in rows]


async def block(client, blocker: dict, blocked: dict) -> None:
    blocked_ = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(blocked["id"]), "surface": "SHORTLIST"},
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
    tomasz_id, token = await world.register(client, "tomasz")
    await world.rate(client, token, Sport.TENNIS)
    tomasz = {"id": tomasz_id, "headers": world.auth(token)}
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

    # Nobody here has a record yet, so there is no Player Score to print — the
    # key is omitted, never a nought.
    assert set(owner) == {"player_id", "name", "level", "is_owner", "joined_at"}
    assert owner["player_id"] == str(karol["id"])
    assert owner["level"] == karol["level"]
    assert member["level"] == zofia["level"]
    assert owner["joined_at"] < member["joined_at"]


async def test_a_member_with_a_record_carries_their_player_score(
    client, session_factory
):
    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    group = await a_group(client, karol, await a_club(client))
    await join(client, zofia, group)
    # One game Zofia turned up to, out of one she was due at: a hundred.
    await a_confirmed_game(
        session_factory, UUID(str(zofia["id"])), uuid4(), sport=Sport.PADEL, a_won=True
    )

    rows = await listed(client, karol, group)

    assert "player_score" not in rows[0]
    assert rows[1]["player_score"] == 100


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


async def test_a_blocked_pair_is_left_out_of_each_other_s_list_either_way(client):
    karol = await a_padel_player(client, "karol")
    zofia = await a_padel_player(client, "zofia")
    kuba = await a_padel_player(client, "kuba")
    tomek = await a_padel_player(client, "tomek")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, kuba, tomek):
        await join(client, member, group)

    await block(client, zofia, kuba)

    assert names(await listed(client, zofia, group)) == ["zofia", "karol", "tomek"]
    assert names(await listed(client, kuba, group)) == ["kuba", "karol", "tomek"]
    # Everybody else still sees both of them.
    assert names(await listed(client, tomek, group)) == [
        "tomek",
        "karol",
        "kuba",
        "zofia",
    ]
    # The count is the group's, the same for every reader.
    assert (await read(client, kuba, group)).json()["member_count"] == 4
    assert (await read(client, zofia, group)).json()["member_count"] == 4


async def test_a_blocked_owner_is_left_out_too(client):
    karol = await a_padel_player(client, "karol")
    kuba = await a_padel_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)

    await block(client, kuba, karol)

    assert names(await listed(client, kuba, group)) == ["kuba"]
    assert names(await listed(client, karol, group)) == ["karol"]


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


async def test_the_members_row_leaves_out_a_blocked_pair_and_keeps_the_count(client):
    karol = await a_player(client, "karol")
    zofia = await a_player(client, "zofia")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    for member in (zofia, kuba):
        await join(client, member, group)

    await block(client, zofia, kuba)

    as_zofia = (await read(client, zofia, group)).json()
    as_kuba = (await read(client, kuba, group)).json()
    assert names(as_zofia["member_faces"]) == ["karol"]
    assert names(as_kuba["member_faces"]) == ["karol"]
    assert as_zofia["member_count"] == as_kuba["member_count"] == 3


async def test_alone_the_members_row_has_nobody_else_to_stack(client):
    tomek = await a_player(client, "tomek")

    group = await a_group(client, tomek, await a_club(client))

    assert group["member_faces"] == []
    assert (await read(client, tomek, group)).json()["member_faces"] == []


async def test_a_block_does_not_reach_the_games_tab_s_seats(client):
    """The line is ADR-0183's: a blocked pair is left out of each other's
    **Members lists** (§10) — the list and the row on Info that opens it — and
    the Games tab's seats are the first rated members **in joining order**
    (§13), whoever reads them (#504)."""

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
    assert names(body["member_faces"]) == ["karol"]


# --------------------------------------------------------------------------- #
# When who is blocked cannot be read
# --------------------------------------------------------------------------- #


class Unreadable:
    """A block state nobody can read — which excludes, never admits
    (``docs/adr/0095`` §5)."""

    async def hidden_from(self, reader_id):
        raise BlockStateUnavailable("the block store is unreachable")


def blocks_unreadable(client) -> None:
    world.override(client, get_hidden_members, Unreadable)


async def test_a_list_nobody_could_check_is_not_served(client):
    karol = await a_padel_player(client, "karol")
    kuba = await a_padel_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)
    blocks_unreadable(client)

    listing = await members(client, kuba, group)
    page = await read(client, kuba, group)

    assert listing.status_code == page.status_code == 503
    assert listing.json()["code"] == page.json()["code"] == "block_state_unavailable"


async def test_a_reader_alone_has_nobody_to_hide_so_blocks_are_not_read(client):
    """Which is what keeps creating a group — whose answer is read straight
    after its commit — from failing over a question with nobody in it."""

    tomek = await a_padel_player(client, "tomek")
    blocks_unreadable(client)

    created = await client.post(
        GROUPS,
        json={
            "name": "my raketa group",
            "home_club_id": (await a_club(client))["id"],
            "join_policy": "ANYONE",
        },
        headers=tomek["headers"],
    )

    assert created.status_code == 201, created.text
    assert names(await listed(client, tomek, created.json())) == ["tomek"]


async def test_an_edit_whose_answer_cannot_be_drawn_records_nothing(client):
    """The answer is drawn before the save commits, so the refusal rolls the
    edit back — and the retry it invites is the whole edit, admissions and all.
    """

    karol = await a_player(client, "karol")
    ewa = await a_player(client, "ewa")
    michal = await a_player(client, "michal")
    group = await an_approval_group(client, karol)
    await join(client, ewa, group)
    await approve(client, karol, group, ewa)
    await join(client, michal, group)
    blocks_unreadable(client)

    refused = await client.put(
        f"{GROUPS}/{group['id']}/details",
        json={"name": "renamed", "join_policy": "ANYONE"},
        headers=karol["headers"],
    )

    assert refused.status_code == 503, refused.text
    assert refused.json()["code"] == "block_state_unavailable"
    # Neither read touches the block state: Michał still waits, and a search
    # still finds the group under its old name and policy.
    assert [row["player_id"] for row in await waiting(client, karol, group)] == [
        str(michal["id"])
    ]
    [card] = (await search(client, michal, group["link"]))["clubs"]
    [row] = card["groups"]
    assert (row["name"], row["join_policy"]) == (group["name"], "PEOPLE_I_APPROVE")
