"""A player creates a group at a home club, sees their groups, opens one, and
joins an *Anyone* group — over HTTP, as the player app calls it.

Everything here is asserted the way a player would meet it: the answer to the
request, and what the next read shows. The Group is event-sourced with its
projections written in the act's own transaction (``docs/adr/0183`` §1), so a
read straight after a write already sees it — which is itself one of the claims.
"""

from __future__ import annotations

import re
from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.kernel import Sport
from tests.api import matchmaking_world as world
from tests.api.test_clubs import SIGN_UP, ogrody_33

GROUPS = "/api/v1/groups"

#: The group code's alphabet, spelled out rather than imported: eight characters
#: with no look-alikes — no ``0``/``o``, no ``1``/``l``/``i`` (``docs/adr/0183`` §4).
CODE = r"[abcdefghjkmnpqrstuvwxyz23456789]{8}"


async def a_club(client, name: str = "Bonarka Arena", **overrides) -> dict:
    """A club that signed up on the club website — the only way one exists."""

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    signed_up = await client.post(
        SIGN_UP,
        json=ogrody_33(name=name, email=f"desk.{slug}@clubs.example", **overrides),
    )
    assert signed_up.status_code == 201, signed_up.text
    return signed_up.json()


async def a_player(client, name: str) -> dict:
    player_id, token = await world.register(client, name)
    return {"id": player_id, "headers": world.auth(token)}


async def create(client, player: dict, club: dict, **overrides):
    return await client.post(
        GROUPS,
        json={
            "name": "my raketa group",
            "home_club_id": club["id"],
            "join_policy": "ANYONE",
            **overrides,
        },
        headers=player["headers"],
    )


async def a_group(client, player: dict, club: dict, **overrides) -> dict:
    created = await create(client, player, club, **overrides)
    assert created.status_code == 201, created.text
    return created.json()


async def join(client, player: dict, group: dict):
    return await client.post(
        f"{GROUPS}/{group['id']}/membership", headers=player["headers"]
    )


async def read(client, player: dict, group: dict):
    return await client.get(f"{GROUPS}/{group['id']}", headers=player["headers"])


async def my_groups(client, player: dict) -> list[dict]:
    listed = await client.get(GROUPS, headers=player["headers"])
    assert listed.status_code == 200, listed.text
    return listed.json()["groups"]


# --------------------------------------------------------------------------- #
# Creating a player group
# --------------------------------------------------------------------------- #


async def test_the_creator_owns_the_group_and_is_its_first_member(client):
    tomek = await a_player(client, "tomek")
    bonarka = await a_club(client)

    group = await a_group(client, tomek, bonarka)

    assert group["name"] == "my raketa group"
    assert group["member_count"] == 1
    assert group["is_owner"] is True
    assert group["join_policy"] == "ANYONE"
    assert group["home_club"] == {"id": bonarka["id"], "name": "Bonarka Arena"}
    assert group["monogram"]["letters"] == "mr"
    # A group with one member has no sport dots: a dot needs two rated members.
    assert group["sports"] == []


async def test_the_group_s_link_is_the_public_site_join_and_a_code(client):
    tomek = await a_player(client, "tomek")
    bonarka = await a_club(client)

    first = await a_group(client, tomek, bonarka)
    second = await a_group(client, tomek, bonarka)

    site = re.escape(get_settings().PUBLIC_SITE_URL.rstrip("/"))
    assert re.fullmatch(rf"{site}/join/{CODE}", first["link"]), first["link"]
    assert re.fullmatch(rf"{site}/join/{CODE}", second["link"]), second["link"]
    # Unique, and never changes: the read answers the link the creation did.
    assert first["link"] != second["link"]
    assert (await read(client, tomek, first)).json()["link"] == first["link"]


async def test_the_creator_may_choose_people_i_approve(client):
    tomek = await a_player(client, "tomek")

    group = await a_group(
        client, tomek, await a_club(client), join_policy="PEOPLE_I_APPROVE"
    )

    assert group["join_policy"] == "PEOPLE_I_APPROVE"


async def test_the_name_is_trimmed_and_two_groups_at_one_club_may_share_it(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    bonarka = await a_club(client)

    mine = await a_group(client, tomek, bonarka, name="  Padel   Kraków \n")
    theirs = await a_group(client, kuba, bonarka, name="Padel Kraków")

    assert mine["name"] == theirs["name"] == "Padel Kraków"
    assert mine["id"] != theirs["id"]


@pytest.mark.parametrize("name", ["", "   ", "x" * 41, " " + "y" * 41 + " "])
async def test_a_name_outside_one_to_forty_is_refused_under_the_name(client, name):
    tomek = await a_player(client, "tomek")
    bonarka = await a_club(client)

    refused = await create(client, tomek, bonarka, name=name)

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "group_name_invalid"
    assert refused.json()["details"] == {"field": "name"}
    assert await my_groups(client, tomek) == []


async def test_forty_characters_is_a_name_once_trimmed(client):
    tomek = await a_player(client, "tomek")

    group = await a_group(client, tomek, await a_club(client), name=f"  {'z' * 40} ")

    assert group["name"] == "z" * 40


async def test_a_home_club_that_is_not_in_raketa_is_refused_under_its_field(client):
    tomek = await a_player(client, "tomek")

    refused = await create(client, tomek, {"id": str(uuid4())})

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "home_club_unknown"
    assert refused.json()["details"] == {"field": "home_club_id"}
    assert await my_groups(client, tomek) == []


@pytest.mark.parametrize(
    "overrides",
    [{"join_policy": "EVERYBODY"}, {"join_policy": None}, {"home_club_id": None}],
)
async def test_a_join_policy_or_club_that_is_not_one_is_not_read(client, overrides):
    tomek = await a_player(client, "tomek")

    refused = await create(client, tomek, await a_club(client), **overrides)

    assert refused.status_code == 422
    assert refused.json()["code"] == "validation_error"


async def test_creating_a_group_needs_a_player(client):
    bonarka = await a_club(client)

    refused = await client.post(
        GROUPS,
        json={"name": "x", "home_club_id": bonarka["id"], "join_policy": "ANYONE"},
    )

    assert refused.status_code == 401


# --------------------------------------------------------------------------- #
# The monogram
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("name", "letters"),
    [
        ("my raketa group", "mr"),
        ("Ogrody 33 Club", "O3"),
        ("Ogrody open play", "Oo"),
        ("Padel", "Pa"),
        ("X", "X"),
        ("Łódź squash", "Łs"),
    ],
)
async def test_the_monogram_is_cut_from_the_name_as_typed(client, name, letters):
    tomek = await a_player(client, "tomek")

    group = await a_group(client, tomek, await a_club(client), name=name)

    assert group["monogram"]["letters"] == letters
    [listed] = await my_groups(client, tomek)
    assert listed["monogram"] == group["monogram"]


async def test_the_monogram_colour_is_a_key_fixed_for_the_group(client):
    tomek = await a_player(client, "tomek")
    bonarka = await a_club(client)

    groups = [await a_group(client, tomek, bonarka) for _ in range(12)]

    colours = [group["monogram"]["colour"] for group in groups]
    assert all(isinstance(colour, int) and 0 <= colour < 8 for colour in colours)
    # Derived from the id, so twelve groups of one name do not all share one.
    assert len(set(colours)) > 1
    for group in groups:
        again = (await read(client, tomek, group)).json()
        assert again["monogram"] == group["monogram"]


# --------------------------------------------------------------------------- #
# Joining an Anyone group
# --------------------------------------------------------------------------- #


async def test_joining_an_anyone_group_makes_the_caller_a_member_at_once(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, tomek, await a_club(client))

    joined = await join(client, kuba, group)

    assert joined.status_code == 200, joined.text
    assert joined.json()["relation"] == "MEMBER"
    assert joined.json()["member_count"] == 2
    assert joined.json()["id"] == group["id"]
    opened = await read(client, kuba, group)
    assert opened.status_code == 200
    assert opened.json()["member_count"] == 2
    assert opened.json()["is_owner"] is False


async def test_joining_twice_changes_nothing(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, tomek, await a_club(client))

    first = await join(client, kuba, group)
    second = await join(client, kuba, group)

    assert second.status_code == 200, second.text
    assert second.json() == first.json()
    assert (await read(client, tomek, group)).json()["member_count"] == 2


async def test_the_owner_joining_their_own_group_changes_nothing(client):
    tomek = await a_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client))

    joined = await join(client, tomek, group)

    assert joined.status_code == 200, joined.text
    assert joined.json()["member_count"] == 1


async def test_a_people_i_approve_group_is_not_joined_by_tapping_join(client):
    """Until join requests exist (#505), a group that needs approval admits
    nobody by a tap — and says why, rather than admitting them."""

    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    group = await a_group(
        client, tomek, await a_club(client), join_policy="PEOPLE_I_APPROVE"
    )

    refused = await join(client, kuba, group)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "group_needs_approval"
    assert (await read(client, tomek, group)).json()["member_count"] == 1
    assert await my_groups(client, kuba) == []


async def test_joining_a_group_that_does_not_exist_is_not_found(client):
    kuba = await a_player(client, "kuba")

    refused = await join(client, kuba, {"id": str(uuid4())})

    assert refused.status_code == 404
    assert refused.json()["code"] == "group_not_found"


# --------------------------------------------------------------------------- #
# My groups
# --------------------------------------------------------------------------- #


async def test_my_groups_lists_the_groups_i_belong_to_newest_joined_first(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    bonarka = await a_club(client)
    centrum = await a_club(client, "Centrum Ruchu", district="Dębniki")

    mine = await a_group(client, tomek, bonarka, name="Tomek's own")
    theirs = await a_group(client, kuba, centrum, name="Kuba's crew")
    await a_group(client, kuba, centrum, name="Not joined")
    await join(client, tomek, theirs)

    listed = await my_groups(client, tomek)

    assert [row["name"] for row in listed] == ["Kuba's crew", "Tomek's own"]
    newest = listed[0]
    assert newest["id"] == theirs["id"]
    assert newest["member_count"] == 2
    assert newest["home_club"] == {"id": centrum["id"], "name": "Centrum Ruchu"}
    assert newest["monogram"] == theirs["monogram"]
    assert newest["sports"] == []
    assert listed[1]["id"] == mine["id"]


async def test_a_player_with_no_groups_has_an_empty_list(client):
    assert await my_groups(client, await a_player(client, "tomek")) == []


# --------------------------------------------------------------------------- #
# Sport dots
# --------------------------------------------------------------------------- #


async def a_rated_player(client, name: str, *sports: Sport) -> dict:
    player_id, token = await world.register(client, name)
    for sport in sports:
        await world.rate(client, token, sport)
    return {"id": player_id, "headers": world.auth(token)}


async def test_a_dot_is_a_sport_at_least_two_members_are_rated_in(client):
    tomek = await a_rated_player(client, "tomek", Sport.PADEL, Sport.TENNIS)
    kuba = await a_rated_player(client, "kuba", Sport.PADEL)
    zofia = await a_rated_player(client, "zofia", Sport.SQUASH)
    group = await a_group(client, tomek, await a_club(client))

    alone = (await read(client, tomek, group)).json()
    await join(client, kuba, group)
    with_kuba = (await read(client, tomek, group)).json()
    await join(client, zofia, group)
    with_zofia = (await read(client, tomek, group)).json()

    assert alone["sports"] == []
    assert with_kuba["sports"] == ["PADEL"]
    # One squash player is not a squash dot, and a third member moves nothing.
    assert with_zofia["sports"] == ["PADEL"]
    [listed] = await my_groups(client, kuba)
    assert listed["sports"] == ["PADEL"]


async def test_dots_are_read_so_a_rating_earned_later_adds_one(client):
    tomek = await a_rated_player(client, "tomek", Sport.PADEL, Sport.TENNIS)
    kuba = await a_rated_player(client, "kuba", Sport.PADEL)
    group = await a_group(client, tomek, await a_club(client))
    await join(client, kuba, group)

    await world.rate(client, kuba["headers"]["Authorization"].split()[1], Sport.TENNIS)

    [listed] = await my_groups(client, tomek)
    assert listed["sports"] == ["PADEL", "TENNIS"]


# --------------------------------------------------------------------------- #
# Reading a group
# --------------------------------------------------------------------------- #


async def test_a_group_is_read_by_its_members_only(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, tomek, await a_club(client))

    stranger = await read(client, kuba, group)
    nothing = await read(client, kuba, {"id": str(uuid4())})

    # One refusal for two cases: not a member, and no such group — the same
    # body but for the trace id every error carries.
    assert stranger.status_code == nothing.status_code == 404
    assert {**stranger.json(), "trace_id": None} == {**nothing.json(), "trace_id": None}
    assert stranger.json()["code"] == "group_not_found"


async def test_reading_a_group_needs_a_player(client):
    tomek = await a_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client))

    assert (await client.get(f"{GROUPS}/{group['id']}")).status_code == 401


async def test_each_sport_says_how_many_are_rated_and_who_joined_first(client):
    """The Games tab's *N of M*: the members rated in the sport, and the faces of
    the first to join who are — as many as the sport seats."""

    owner = await a_rated_player(client, "owner", Sport.PADEL, Sport.TENNIS)
    names = ["ala", "bea", "cyryl", "dora", "emil"]
    joiners = [await a_rated_player(client, name, Sport.PADEL) for name in names]
    unrated = await a_player(client, "fred")
    group = await a_group(client, owner, await a_club(client))
    for player in [joiners[0], unrated, *joiners[1:]]:
        assert (await join(client, player, group)).status_code == 200

    opened = await read(client, joiners[2], group)

    assert opened.status_code == 200, opened.text
    body = opened.json()
    assert body["member_count"] == 7
    by_sport = {row["sport"]: row for row in body["rated_by_sport"]}
    assert [row["sport"] for row in body["rated_by_sport"]] == [s.value for s in Sport]
    padel = by_sport["PADEL"]
    assert padel["rated_count"] == 6
    # Padel seats four: the owner first, then the first three rated joiners.
    assert [person["player_id"] for person in padel["first_rated"]] == [
        str(owner["id"]),
        *(str(player["id"]) for player in joiners[:3]),
    ]
    assert [person["name"] for person in padel["first_rated"]] == [
        "owner",
        "ala",
        "bea",
        "cyryl",
    ]
    tennis = by_sport["TENNIS"]
    assert tennis["rated_count"] == 1
    assert [person["player_id"] for person in tennis["first_rated"]] == [
        str(owner["id"])
    ]
    assert by_sport["SQUASH"] == {
        "sport": "SQUASH",
        "rated_count": 0,
        "first_rated": [],
    }
    assert body["sports"] == ["PADEL"]


async def test_a_face_without_a_photograph_carries_no_photograph(client):
    tomek = await a_rated_player(client, "tomek", Sport.PADEL)
    group = await a_group(client, tomek, await a_club(client))

    body = (await read(client, tomek, group)).json()

    [face] = next(
        row["first_rated"] for row in body["rated_by_sport"] if row["sport"] == "PADEL"
    )
    assert face == {"player_id": str(tomek["id"]), "name": "tomek"}


async def test_the_owner_is_the_owner_and_a_member_is_not(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, tomek, await a_club(client))
    await join(client, kuba, group)

    assert (await read(client, tomek, group)).json()["is_owner"] is True
    assert (await read(client, kuba, group)).json()["is_owner"] is False
