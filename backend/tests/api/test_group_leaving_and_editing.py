"""Leaving a group, passing it on, editing it and deleting it — over HTTP, as
the player app calls it (#506, ``docs/adr/0183`` §7).

Kuba leaves Kazimierz crew with a confirmation, and could join again. Karol
renames it and switches it to Anyone, and the two people waiting are in at
once. Later Karol leaves, and Ewa — in longest — becomes the Owner and finds
the queue. In his own new group, where he is alone, Tomek deletes it, and its
link reads *nothing at that link*.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.api.test_group_members import a_padel_player, listed
from tests.api.test_join_search import search
from tests.api.test_join_requests import (
    an_approval_group,
    approve,
    requests_of,
    waiting,
)
from tests.api.test_groups import (
    GROUPS,
    a_club,
    a_group,
    a_player,
    join,
    my_groups,
    read,
)


async def leave(client, player: dict, group: dict):
    return await client.delete(
        f"{GROUPS}/{group['id']}/membership", headers=player["headers"]
    )


async def members_of(client, reader: dict, group: dict) -> int:
    opened = await read(client, reader, group)
    assert opened.status_code == 200, opened.text
    return opened.json()["member_count"]


# --------------------------------------------------------------------------- #
# Leaving
# --------------------------------------------------------------------------- #


async def test_a_member_leaves_and_the_group_is_no_longer_theirs(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)

    left = await leave(client, kuba, group)

    assert left.status_code == 204, left.text
    assert await my_groups(client, kuba) == []
    assert (await read(client, kuba, group)).status_code == 404
    assert await members_of(client, karol, group) == 1


async def test_somebody_who_left_may_join_again(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)
    await leave(client, kuba, group)

    again = await join(client, kuba, group)

    assert again.status_code == 200, again.text
    assert again.json()["relation"] == "MEMBER"
    assert await members_of(client, karol, group) == 2


async def test_a_stranger_leaving_meets_the_stranger_s_refusal(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))

    stranger = await leave(client, kuba, group)
    nothing = await leave(client, kuba, {"id": str(uuid4())})

    assert stranger.status_code == nothing.status_code == 404
    assert stranger.json()["code"] == nothing.json()["code"] == "group_not_found"


async def test_an_owner_leaving_passes_the_group_and_its_queue_to_who_is_in_longest(
    client,
):
    karol = await a_player(client, "karol")
    ewa = await a_player(client, "ewa")
    kuba = await a_player(client, "kuba")
    michal = await a_player(client, "michal")
    group = await an_approval_group(client, karol)
    for member in (ewa, kuba):
        await join(client, member, group)
        await approve(client, karol, group, member)
    await join(client, michal, group)

    left = await leave(client, karol, group)

    assert left.status_code == 204, left.text
    assert (await read(client, ewa, group)).json()["is_owner"] is True
    assert (await read(client, kuba, group)).json()["is_owner"] is False
    # The queue passed with the group: Ewa finds Michał waiting, and answers.
    [request] = await waiting(client, ewa, group)
    assert request["player_id"] == str(michal["id"])
    assert (await approve(client, ewa, group, michal)).status_code == 204
    assert (await requests_of(client, kuba, group)).json()["code"] == (
        "not_the_group_owner"
    )
    assert await members_of(client, ewa, group) == 3


async def test_an_owner_alone_cannot_leave(client):
    tomek = await a_player(client, "tomek")
    group = await a_group(client, tomek, await a_club(client))

    refused = await leave(client, tomek, group)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "lone_owner_cannot_leave"
    assert (await read(client, tomek, group)).json()["is_owner"] is True


# --------------------------------------------------------------------------- #
# Deleting
# --------------------------------------------------------------------------- #


async def delete(client, player: dict, group: dict):
    return await client.delete(f"{GROUPS}/{group['id']}", headers=player["headers"])


async def test_an_owner_alone_deletes_the_group_and_its_link_reads_as_dead(client):
    tomek = await a_player(client, "tomek")
    kuba = await a_player(client, "kuba")
    bonarka = await a_club(client)
    group = await a_group(client, tomek, bonarka, join_policy="PEOPLE_I_APPROVE")
    await join(client, kuba, group)

    deleted = await delete(client, tomek, group)

    assert deleted.status_code == 204, deleted.text
    assert await my_groups(client, tomek) == []
    assert (await read(client, tomek, group)).status_code == 404
    # Its link reads *nothing at that link*, and so does its name.
    assert await search(client, kuba, group["link"]) == {
        "clubs": [],
        "next_page": None,
        "read_as": "LINK",
    }
    [card] = (await search(client, kuba, "Bonarka"))["clubs"]
    assert card["groups"] == []
    # The request Kuba left went with it: there is nothing to ask again.
    assert (await join(client, kuba, group)).json()["code"] == "group_not_found"


async def test_a_group_other_people_are_in_cannot_be_deleted(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)

    refused = await delete(client, karol, group)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "group_has_other_members"
    assert await members_of(client, karol, group) == 2


async def test_a_member_who_is_not_the_owner_cannot_delete_it(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)

    refused = await delete(client, kuba, group)

    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "not_the_group_owner"


async def test_a_stranger_deleting_meets_the_stranger_s_refusal(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))

    stranger = await delete(client, kuba, group)
    nothing = await delete(client, kuba, {"id": str(uuid4())})

    assert stranger.status_code == nothing.status_code == 404
    assert stranger.json()["code"] == nothing.json()["code"] == "group_not_found"
    assert await members_of(client, karol, group) == 1


async def test_the_one_who_took_it_over_may_delete_it_once_alone(client):
    karol = await a_player(client, "karol")
    ewa = await a_player(client, "ewa")
    group = await a_group(client, karol, await a_club(client))
    await join(client, ewa, group)
    await leave(client, karol, group)

    deleted = await delete(client, ewa, group)

    assert deleted.status_code == 204, deleted.text
    assert await my_groups(client, ewa) == []


# --------------------------------------------------------------------------- #
# Editing
# --------------------------------------------------------------------------- #


async def edit(client, player: dict, group: dict, **details):
    return await client.put(
        f"{GROUPS}/{group['id']}/details",
        json={
            "name": group["name"],
            "join_policy": group["join_policy"],
            **details,
        },
        headers=player["headers"],
    )


async def test_the_owner_renames_the_group_and_its_link_stays(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client), name="Kazimierz crew")
    await join(client, kuba, group)

    edited = await edit(client, karol, group, name="  Nights   at Kazimierz ")

    assert edited.status_code == 200, edited.text
    body = edited.json()["group"]
    assert body["name"] == "Nights at Kazimierz"
    assert body["link"] == group["link"]
    assert body["monogram"] == {"letters": "Na", "colour": group["monogram"]["colour"]}
    assert edited.json()["admitted"] == []
    [listed] = await my_groups(client, kuba)
    assert listed["name"] == "Nights at Kazimierz"
    # Join search finds it by its new name, folded, and no longer by its old.
    assert [
        row["name"]
        for card in (await search(client, kuba, "nights"))["clubs"]
        for row in card["groups"]
    ] == ["Nights at Kazimierz"]
    assert (await search(client, kuba, "crew"))["clubs"] == []


async def test_switching_to_anyone_admits_everybody_waiting_at_once(client):
    karol = await a_player(client, "karol")
    michal = await a_player(client, "michal")
    tomek = await a_player(client, "tomek")
    group = await an_approval_group(client, karol)
    await join(client, michal, group)
    await join(client, tomek, group)

    edited = await edit(client, karol, group, join_policy="ANYONE")

    assert edited.status_code == 200, edited.text
    assert edited.json()["group"]["join_policy"] == "ANYONE"
    assert edited.json()["group"]["member_count"] == 3
    # Who it let in, in the order they asked — the Edit screen shows them.
    assert edited.json()["admitted"] == [
        {"player_id": str(michal["id"]), "nickname": "michal"},
        {"player_id": str(tomek["id"]), "nickname": "tomek"},
    ]
    assert await waiting(client, karol, group) == []
    assert (await read(client, tomek, group)).status_code == 200


async def test_switching_to_people_i_approve_admits_nobody_and_later_asks_wait(
    client,
):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))

    edited = await edit(client, karol, group, join_policy="PEOPLE_I_APPROVE")
    asked = await join(client, kuba, group)

    assert edited.status_code == 200, edited.text
    assert edited.json()["group"]["join_policy"] == "PEOPLE_I_APPROVE"
    assert edited.json()["admitted"] == []
    assert asked.json()["relation"] == "REQUESTED"


async def test_saving_what_it_already_says_changes_nothing(client):
    karol = await a_player(client, "karol")
    group = await a_group(client, karol, await a_club(client))

    edited = await edit(client, karol, group)

    assert edited.status_code == 200, edited.text
    assert edited.json() == {
        "group": (await read(client, karol, group)).json(),
        "admitted": [],
    }


@pytest.mark.parametrize("name", ["  ", "x" * 41])
async def test_a_name_outside_one_to_forty_is_refused_and_nothing_else_moves(
    client, name
):
    karol = await a_player(client, "karol")
    michal = await a_player(client, "michal")
    group = await an_approval_group(client, karol)
    await join(client, michal, group)

    refused = await edit(client, karol, group, name=name, join_policy="ANYONE")

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "group_name_invalid"
    assert refused.json()["details"] == {"field": "name"}
    # One Save, one answer: the policy did not change without the name.
    assert (await read(client, karol, group)).json()["join_policy"] == (
        "PEOPLE_I_APPROVE"
    )
    assert len(await waiting(client, karol, group)) == 1


async def test_only_the_owner_edits_the_group(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))
    await join(client, kuba, group)

    # Refused as a member before the name is read, so a bad name changes nothing
    # about which refusal a member meets.
    renamed = await edit(client, kuba, group, name="Kuba's now")
    unnamed = await edit(client, kuba, group, name="")

    assert renamed.status_code == unnamed.status_code == 403
    assert renamed.json()["code"] == unnamed.json()["code"] == "not_the_group_owner"
    assert (await read(client, karol, group)).json()["name"] == group["name"]


async def test_a_stranger_editing_meets_the_stranger_s_refusal(client):
    karol = await a_player(client, "karol")
    kuba = await a_player(client, "kuba")
    group = await a_group(client, karol, await a_club(client))

    stranger = await edit(client, kuba, group, name="mine")
    nothing = await edit(client, kuba, {**group, "id": str(uuid4())}, name="mine")

    assert stranger.status_code == nothing.status_code == 404
    assert stranger.json()["code"] == nothing.json()["code"] == "group_not_found"


async def test_the_new_owner_is_who_joined_first_and_members_says_so(client):
    """Kuba asked first and Ewa second, but Karol let Ewa in first: *in
    longest* is who joined earliest, whatever order they asked in — and the
    Members list draws her as the Owner."""

    karol = await a_padel_player(client, "karol")
    ewa = await a_padel_player(client, "ewa")
    kuba = await a_padel_player(client, "kuba")
    group = await an_approval_group(client, karol)
    await join(client, kuba, group)
    await join(client, ewa, group)
    await approve(client, karol, group, ewa)
    await approve(client, karol, group, kuba)

    await leave(client, karol, group)

    rows = await listed(client, kuba, group)
    assert [(row["nickname"], row["is_owner"]) for row in rows] == [
        ("kuba", False),
        ("ewa", True),
    ]
    assert (await read(client, ewa, group)).json()["is_owner"] is True
