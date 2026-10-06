"""The block routes, over HTTP, and the silence around them.

Most of what is asserted here is *what does not happen*: the same 204 for a
block and for a repeat of it, the same 204 for a lift and for a lift of nothing,
and no body on either. Those sameness claims are the promise — *nobody is shown
that they were blocked* (``docs/adr/0193`` §3) — and each of them is one status
code away from being broken by somebody making the API "more helpful".

The one thing that *is* shown is **your own** blocks: ``GET /blocks`` lists whom
the caller blocked, and nobody else's block of them.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest


async def _player(client, name: str) -> tuple[str, str]:
    """Register, sign in and name one player. Returns their id and a bearer token."""

    signup = await client.post(
        "/api/v1/users",
        json={
            "email": f"{name}@example.com",
            "password1": "hunter22!",
            "password2": "hunter22!",
            "adult_attested": True,
        },
    )
    assert signup.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": "hunter22!"},
    )
    token = login.json()["access_token"]
    named = await client.put(
        "/api/v1/users/me/name",
        json={"name": name, "nickname": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert named.status_code == 200, named.text
    return signup.json()["id"], token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def two_players(client):
    alice_id, alice_token = await _player(client, "alice")
    bob_id, bob_token = await _player(client, "bob")
    return {
        "alice": (alice_id, alice_token),
        "bob": (bob_id, bob_token),
    }


async def test_a_player_can_block_and_unblock(client, two_players):
    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]

    blocked = await client.post(
        "/api/v1/blocks",
        json={"player_id": bob_id},
        headers=_auth(alice_token),
    )
    assert blocked.status_code == 204
    assert blocked.content == b""

    lifted = await client.delete(
        f"/api/v1/blocks/{bob_id}", headers=_auth(alice_token)
    )
    assert lifted.status_code == 204
    assert lifted.content == b""


async def test_blocking_twice_answers_exactly_the_same(client, two_players):
    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]
    body = {"player_id": bob_id}

    first = await client.post("/api/v1/blocks", json=body, headers=_auth(alice_token))
    second = await client.post("/api/v1/blocks", json=body, headers=_auth(alice_token))

    assert (first.status_code, first.content) == (second.status_code, second.content)


async def test_unblocking_somebody_never_blocked_is_not_a_404(client, two_players):
    """A 404 here would be the API reporting on state to the caller — and, were
    they blocked back, on the other person's block."""

    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]

    response = await client.delete(
        f"/api/v1/blocks/{bob_id}", headers=_auth(alice_token)
    )

    assert response.status_code == 204


async def test_blocking_a_player_who_does_not_exist_answers_the_same(
    client, two_players
):
    """Deliberately not a 404: answering *no such player* would make this
    endpoint an oracle for which ids exist."""

    _, alice_token = two_players["alice"]

    response = await client.post(
        "/api/v1/blocks",
        json={"player_id": str(uuid4())},
        headers=_auth(alice_token),
    )

    assert response.status_code == 204


async def test_blocking_yourself_is_refused_with_a_code(client, two_players):
    alice_id, alice_token = two_players["alice"]

    response = await client.post(
        "/api/v1/blocks",
        json={"player_id": alice_id},
        headers=_auth(alice_token),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "cannot_block_yourself"


async def test_a_request_still_naming_a_screen_blocks_and_the_screen_is_dropped(
    client, two_players
):
    """A shipped client sends ``surface`` until it updates. The field is gone
    from the contract (``docs/adr/0193`` §5), and a body still carrying it blocks
    exactly as one without it — nothing is refused for a screen."""

    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]

    response = await client.post(
        "/api/v1/blocks",
        json={"player_id": bob_id, "surface": "SHORTLIST"},
        headers=_auth(alice_token),
    )

    assert response.status_code == 204
    listed = await client.get("/api/v1/blocks", headers=_auth(alice_token))
    assert [one["player_id"] for one in listed.json()["players"]] == [bob_id]


async def test_neither_route_can_be_reached_without_a_token(client, two_players):
    bob_id, _ = two_players["bob"]

    blocked = await client.post("/api/v1/blocks", json={"player_id": bob_id})
    lifted = await client.delete(f"/api/v1/blocks/{bob_id}")
    listed = await client.get("/api/v1/blocks")

    assert blocked.status_code == 401
    assert lifted.status_code == 401
    assert listed.status_code == 401


async def test_being_blocked_changes_nothing_the_blocked_player_can_see(
    client, two_players
):
    """The blocked party is not notified, and nothing they can ask about
    themselves moves — their own account, and their own list of blocks."""

    _, alice_token = two_players["alice"]
    bob_id, bob_token = two_players["bob"]

    me_before = await client.get("/api/v1/users/me", headers=_auth(bob_token))
    list_before = await client.get("/api/v1/blocks", headers=_auth(bob_token))
    await client.post(
        "/api/v1/blocks", json={"player_id": bob_id}, headers=_auth(alice_token)
    )
    me_after = await client.get("/api/v1/users/me", headers=_auth(bob_token))
    list_after = await client.get("/api/v1/blocks", headers=_auth(bob_token))

    assert me_before.json() == me_after.json()
    assert list_before.content == list_after.content
    assert list_after.json() == {"players": []}


# --------------------------------------------------------------------------- #
# Blocked players — your own blocks, and nobody else's
# --------------------------------------------------------------------------- #


async def _blocked_players(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/blocks", headers=_auth(token))
    assert response.status_code == 200, response.text
    return response.json()["players"]


async def _ids_blocked_by(client, token: str) -> list[str]:
    return [one["player_id"] for one in await _blocked_players(client, token)]


async def test_nobody_blocked_is_an_empty_list(client, two_players):
    _, alice_token = two_players["alice"]

    assert await _blocked_players(client, alice_token) == []


async def test_the_list_names_whom_you_blocked_and_when_newest_first(
    client, clock, two_players
):
    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]
    carol_id, _ = await _player(client, "carol")

    await client.post(
        "/api/v1/blocks", json={"player_id": bob_id}, headers=_auth(alice_token)
    )
    bob_blocked_at = clock.now()
    clock.move(timedelta(hours=2))
    await client.post(
        "/api/v1/blocks", json={"player_id": carol_id}, headers=_auth(alice_token)
    )

    listed = await _blocked_players(client, alice_token)

    assert [(one["player_id"], one["name"]) for one in listed] == [
        (carol_id, "carol"),
        (bob_id, "bob"),
    ]
    assert datetime.fromisoformat(listed[1]["blocked_at"]) == bob_blocked_at
    # Nobody here has a photograph, so neither half of one is on the row.
    assert "photo_id" not in listed[0] and "photo_url" not in listed[0]


async def test_blocking_again_leaves_the_list_and_its_time_as_they_were(
    client, clock, two_players
):
    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]
    body = {"player_id": bob_id}

    await client.post("/api/v1/blocks", json=body, headers=_auth(alice_token))
    first = await _blocked_players(client, alice_token)
    clock.move(timedelta(hours=1))
    await client.post("/api/v1/blocks", json=body, headers=_auth(alice_token))

    assert await _blocked_players(client, alice_token) == first


async def test_unblocking_takes_them_off_the_list_at_once(client, two_players):
    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]

    await client.post(
        "/api/v1/blocks", json={"player_id": bob_id}, headers=_auth(alice_token)
    )
    await client.delete(f"/api/v1/blocks/{bob_id}", headers=_auth(alice_token))

    assert await _blocked_players(client, alice_token) == []


async def test_both_having_blocked_each_lists_only_their_own_and_one_lift_is_one(
    client, two_players
):
    """The record is directed, so the list is per person (``docs/adr/0193``
    §3): Alice unblocking Bob lifts Alice's block and says nothing about Bob's,
    which still stands and is still on Bob's list alone."""

    alice_id, alice_token = two_players["alice"]
    bob_id, bob_token = two_players["bob"]

    await client.post(
        "/api/v1/blocks", json={"player_id": bob_id}, headers=_auth(alice_token)
    )
    await client.post(
        "/api/v1/blocks", json={"player_id": alice_id}, headers=_auth(bob_token)
    )
    assert await _ids_blocked_by(client, alice_token) == [bob_id]
    assert await _ids_blocked_by(client, bob_token) == [alice_id]

    await client.delete(f"/api/v1/blocks/{bob_id}", headers=_auth(alice_token))

    assert await _ids_blocked_by(client, alice_token) == []
    assert await _ids_blocked_by(client, bob_token) == [alice_id]


async def test_a_block_of_an_id_nobody_holds_is_not_listed(client, two_players):
    """It answered 204 like any block, so the block route is no oracle for which
    ids exist — and there is nobody to draw for it."""

    _, alice_token = two_players["alice"]

    await client.post(
        "/api/v1/blocks", json={"player_id": str(uuid4())}, headers=_auth(alice_token)
    )

    assert await _blocked_players(client, alice_token) == []
