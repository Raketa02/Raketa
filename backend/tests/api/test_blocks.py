"""The two block routes, over HTTP, and the silence around them.

What is asserted here is mostly *what does not happen*: the same 204 for a block
and for a repeat of it, the same 204 for a lift and for a lift of nothing, and no
body anywhere. Those sameness claims are the promise — *no response reveals a
block to the blocked party* (``docs/adr/0095`` §8) — and each of them is one
status code away from being broken by somebody making the API "more helpful".
"""

from __future__ import annotations

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
        json={"player_id": bob_id, "surface": "SHORTLIST"},
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
    body = {"player_id": bob_id, "surface": "DECK"}

    first = await client.post("/api/v1/blocks", json=body, headers=_auth(alice_token))
    second = await client.post("/api/v1/blocks", json=body, headers=_auth(alice_token))

    assert (first.status_code, first.content) == (second.status_code, second.content)


async def test_unblocking_somebody_never_blocked_is_not_a_404(client, two_players):
    """A 404 here would be the API reporting on state to the caller, and the
    first crack in *a block is unrepresentable in a response*."""

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
        json={"player_id": str(uuid4()), "surface": "SHORTLIST"},
        headers=_auth(alice_token),
    )

    assert response.status_code == 204


async def test_blocking_yourself_is_refused_with_a_code(client, two_players):
    alice_id, alice_token = two_players["alice"]

    response = await client.post(
        "/api/v1/blocks",
        json={"player_id": alice_id, "surface": "SHORTLIST"},
        headers=_auth(alice_token),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "cannot_block_yourself"


async def test_an_unknown_surface_is_refused(client, two_players):
    """The four surfaces are a closed set the client already holds."""

    _, alice_token = two_players["alice"]
    bob_id, _ = two_players["bob"]

    response = await client.post(
        "/api/v1/blocks",
        json={"player_id": bob_id, "surface": "SETTINGS"},
        headers=_auth(alice_token),
    )

    assert response.status_code == 422


async def test_neither_route_can_be_reached_without_a_token(client, two_players):
    bob_id, _ = two_players["bob"]

    blocked = await client.post(
        "/api/v1/blocks", json={"player_id": bob_id, "surface": "SHORTLIST"}
    )
    lifted = await client.delete(f"/api/v1/blocks/{bob_id}")

    assert blocked.status_code == 401
    assert lifted.status_code == 401


async def test_being_blocked_changes_nothing_the_blocked_player_can_see(
    client, two_players
):
    """The blocked party is not notified, and nothing they can ask about
    themselves moves. ``/users/me`` is every response the platform serves them
    today, which is what makes this assertion the whole of the claim for now."""

    _, alice_token = two_players["alice"]
    bob_id, bob_token = two_players["bob"]

    before = await client.get("/api/v1/users/me", headers=_auth(bob_token))
    await client.post(
        "/api/v1/blocks",
        json={"player_id": bob_id, "surface": "SHORTLIST"},
        headers=_auth(alice_token),
    )
    after = await client.get("/api/v1/users/me", headers=_auth(bob_token))

    assert before.json() == after.json()
