"""Asking to join a *People I approve* group, and its Owner answering — over
HTTP, as the player app calls it.

Kasia taps *Ask to join* and her request waits. Karol, the Owner, sees it and
approves her, and she's in. Had he declined, her row would quietly go back to
*Ask to join*, and she could ask again (#505, ``docs/adr/0183`` §7). The
requests are a projection written in the act's own transaction, so a read
straight after an answer already sees it.
"""

from __future__ import annotations

from uuid import uuid4

from app.kernel import Sport
from tests.api import players_world as players
from tests.api.test_groups import (
    GROUPS,
    a_club,
    a_group,
    a_player,
    a_rated_player,
    join,
    my_groups,
    read,
)


async def an_approval_group(client, owner: dict, **overrides) -> dict:
    return await a_group(
        client,
        owner,
        await a_club(client),
        join_policy="PEOPLE_I_APPROVE",
        **overrides,
    )


async def requests_of(client, player: dict, group: dict):
    return await client.get(
        f"{GROUPS}/{group['id']}/requests", headers=player["headers"]
    )


async def waiting(client, owner: dict, group: dict) -> list[dict]:
    listed = await requests_of(client, owner, group)
    assert listed.status_code == 200, listed.text
    return listed.json()["requests"]


async def approve(client, player: dict, group: dict, asker: dict):
    return await client.post(
        f"{GROUPS}/{group['id']}/requests/{asker['id']}/approve",
        headers=player["headers"],
    )


async def decline(client, player: dict, group: dict, asker: dict):
    return await client.post(
        f"{GROUPS}/{group['id']}/requests/{asker['id']}/decline",
        headers=player["headers"],
    )


# --------------------------------------------------------------------------- #
# Asking
# --------------------------------------------------------------------------- #


async def test_asking_to_join_a_people_i_approve_group_leaves_a_request_waiting(
    client,
):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)

    asked = await join(client, kasia, group)

    assert asked.status_code == 200, asked.text
    assert asked.json()["relation"] == "REQUESTED"
    # Asking admits nobody.
    assert asked.json()["member_count"] == 1
    assert (await read(client, kasia, group)).status_code == 404
    assert await my_groups(client, kasia) == []
    [request] = await waiting(client, karol, group)
    assert request["player_id"] == str(kasia["id"])


async def test_asking_again_while_waiting_changes_nothing(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)

    first = await join(client, kasia, group)
    second = await join(client, kasia, group)

    assert second.status_code == 200, second.text
    assert second.json() == first.json()
    assert len(await waiting(client, karol, group)) == 1


async def test_the_owner_asking_to_join_their_own_group_changes_nothing(client):
    karol = await a_player(client, "karol")
    group = await an_approval_group(client, karol)

    joined = await join(client, karol, group)

    assert joined.status_code == 200, joined.text
    assert joined.json()["relation"] == "MEMBER"
    assert await waiting(client, karol, group) == []


# --------------------------------------------------------------------------- #
# What the Owner sees
# --------------------------------------------------------------------------- #


async def test_a_request_shows_the_person_s_name_face_and_every_level(client):
    karol = await a_player(client, "karol")
    kasia = await a_rated_player(client, "kasia", Sport.TENNIS, Sport.PADEL)
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)

    [request] = await waiting(client, karol, group)

    # No photograph: the client draws her initials.
    assert set(request) == {"player_id", "name", "levels"}
    assert request["name"] == "kasia"
    # Every sport she is rated in, in the registry's order, each with its Level
    # as RacketSkill published it.
    assert [row["sport"] for row in request["levels"]] == ["PADEL", "TENNIS"]
    assert all(isinstance(row["level"], float) for row in request["levels"])


async def test_somebody_rated_in_nothing_asks_with_no_levels(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)

    [request] = await waiting(client, karol, group)

    assert request["levels"] == []


async def test_requests_wait_in_the_order_they_were_asked(client):
    karol = await a_player(client, "karol")
    askers = [await a_player(client, name) for name in ("kasia", "ola", "jan")]
    group = await an_approval_group(client, karol)
    for asker in askers:
        await join(client, asker, group)

    listed = await waiting(client, karol, group)

    assert [row["name"] for row in listed] == ["kasia", "ola", "jan"]


async def test_a_group_nobody_has_asked_has_no_requests(client):
    karol = await a_player(client, "karol")

    assert await waiting(client, karol, await an_approval_group(client, karol)) == []


# --------------------------------------------------------------------------- #
# Approving
# --------------------------------------------------------------------------- #


async def test_approving_makes_the_person_a_member_at_once(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)

    approved = await approve(client, karol, group, kasia)

    assert approved.status_code == 204, approved.text
    assert await waiting(client, karol, group) == []
    opened = await read(client, kasia, group)
    assert opened.status_code == 200, opened.text
    assert opened.json()["member_count"] == 2
    [listed] = await my_groups(client, kasia)
    assert listed["id"] == group["id"]
    # Her tap answers *you're in* from now on.
    assert (await join(client, kasia, group)).json()["relation"] == "MEMBER"


async def test_approving_twice_changes_nothing(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)
    await approve(client, karol, group, kasia)

    again = await approve(client, karol, group, kasia)

    assert again.status_code == 204, again.text
    assert (await read(client, karol, group)).json()["member_count"] == 2


async def test_approving_somebody_who_is_not_waiting_is_not_found(client):
    """Nobody is admitted who did not ask — a request that was declined, or
    never made, has to be asked again."""

    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)

    refused = await approve(client, karol, group, kasia)

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "join_request_not_found"
    assert (await read(client, karol, group)).json()["member_count"] == 1


# --------------------------------------------------------------------------- #
# Declining, and asking again
# --------------------------------------------------------------------------- #


async def test_declining_removes_the_request_silently(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)

    declined = await decline(client, karol, group, kasia)

    assert declined.status_code == 204, declined.text
    assert await waiting(client, karol, group) == []
    assert await my_groups(client, kasia) == []
    assert (await read(client, karol, group)).json()["member_count"] == 1


async def test_after_a_decline_the_person_may_ask_again(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)
    await decline(client, karol, group, kasia)

    again = await join(client, kasia, group)

    assert again.status_code == 200, again.text
    assert again.json()["relation"] == "REQUESTED"
    [request] = await waiting(client, karol, group)
    assert request["player_id"] == str(kasia["id"])


async def test_declining_a_request_that_is_not_waiting_changes_nothing(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)
    await decline(client, karol, group, kasia)

    again = await decline(client, karol, group, kasia)

    assert again.status_code == 204, again.text
    assert await waiting(client, karol, group) == []


async def test_declining_a_member_removes_nobody(client):
    """Nobody removes a Group member (``docs/adr/0183`` §7) — a decline that
    arrives after an approval finds nothing waiting."""

    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, kasia, group)
    await approve(client, karol, group, kasia)

    declined = await decline(client, karol, group, kasia)

    assert declined.status_code == 204, declined.text
    assert (await read(client, kasia, group)).json()["member_count"] == 2


# --------------------------------------------------------------------------- #
# Nobody but the Owner
# --------------------------------------------------------------------------- #


async def a_group_with_a_member_and_a_request(client) -> tuple[dict, ...]:
    karol = await a_player(client, "karol")
    ola = await a_player(client, "ola")
    kasia = await a_player(client, "kasia")
    group = await an_approval_group(client, karol)
    await join(client, ola, group)
    await approve(client, karol, group, ola)
    await join(client, kasia, group)
    return karol, ola, kasia, group


async def test_a_member_who_is_not_the_owner_cannot_see_or_answer_requests(client):
    karol, ola, kasia, group = await a_group_with_a_member_and_a_request(client)

    listed = await requests_of(client, ola, group)
    approved = await approve(client, ola, group, kasia)
    declined = await decline(client, ola, group, kasia)

    for refused in (listed, approved, declined):
        assert refused.status_code == 403, refused.text
        assert refused.json()["code"] == "not_the_group_owner"
    [still] = await waiting(client, karol, group)
    assert still["player_id"] == str(kasia["id"])


async def test_a_stranger_meets_the_group_as_not_found(client):
    """A stranger — the person asking included — is refused as a group's page
    refuses them: one code for *no such group* and *not yours*."""

    karol, _ola, kasia, group = await a_group_with_a_member_and_a_request(client)
    stranger = await a_player(client, "obcy")

    for player in (stranger, kasia):
        for refused in (
            await requests_of(client, player, group),
            await approve(client, player, group, kasia),
            await decline(client, player, group, kasia),
        ):
            assert refused.status_code == 404, refused.text
            assert refused.json()["code"] == "group_not_found"
    assert len(await waiting(client, karol, group)) == 1


async def test_requests_of_a_group_that_does_not_exist_are_not_found(client):
    karol = await a_player(client, "karol")

    refused = await requests_of(client, karol, {"id": str(uuid4())})

    assert refused.status_code == 404
    assert refused.json()["code"] == "group_not_found"


async def test_requests_need_a_player(client):
    karol = await a_player(client, "karol")
    group = await an_approval_group(client, karol)

    assert (await client.get(f"{GROUPS}/{group['id']}/requests")).status_code == 401
    assert (
        await client.post(f"{GROUPS}/{group['id']}/requests/{karol['id']}/approve")
    ).status_code == 401


# --------------------------------------------------------------------------- #
# An Anyone group
# --------------------------------------------------------------------------- #


async def test_an_anyone_group_admits_at_once_and_never_has_a_request(client):
    karol = await a_player(client, "karol")
    kasia = await a_player(client, "kasia")
    group = await a_group(client, karol, await a_club(client))

    joined = await join(client, kasia, group)

    assert joined.json()["relation"] == "MEMBER"
    assert await waiting(client, karol, group) == []


async def test_a_request_names_nobody_s_nickname(client):
    """The Name and never the handle (``docs/adr/0171`` §4)."""

    karol = await a_player(client, "karol")
    kasia_id, token = await players.register(client, "kasia")
    renamed = await client.put(
        "/api/v1/users/me/name",
        json={"name": "Kasia Nowak", "nickname": "kasia_n"},
        headers=players.auth(token),
    )
    assert renamed.status_code == 200, renamed.text
    group = await an_approval_group(client, karol)
    await join(client, {"id": kasia_id, "headers": players.auth(token)}, group)

    [request] = await waiting(client, karol, group)

    assert request["name"] == "Kasia Nowak"
