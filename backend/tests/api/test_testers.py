"""The tester mark, from the admin command's use case to ``GET /users/me``.

A **Tester** is a player whose account carries the tester mark
(``docs/adr/0180`` §9). Nothing on the player surface sets it — the admin
command does, through ``SetTesterMark`` — and the player app reads it back as
``is_tester`` on its own account and hands it to flag evaluation, so that no
datafile ever has to name a tester.

The use case is driven here the way the command drives it: built by the
composition root over a session of its own, committed, and then read back over
HTTP by the player it marked. The ``client`` fixture overrides ``get_db`` with
the same factory, so what the command wrote is what the request sees.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.bootstrap.composition import build_set_tester_mark
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.users.application.commands import SetTesterMarkCommand
from app.modules.users.application.set_tester_mark import TesterMark
from app.modules.users.domain.errors import UnknownPlayer


async def _signed_in(client, payload) -> dict[str, str]:
    assert (await client.post("/api/v1/users", json=payload)).status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _is_tester(client, headers) -> bool:
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200, me.text
    return me.json()["is_tester"]


async def _set(session_factory, player: str, *, tester: bool) -> TesterMark:
    async with session_factory() as session:
        return await build_set_tester_mark(session).execute(
            SetTesterMarkCommand(player=player, tester=tester)
        )


async def _marks_on_the_stream(session_factory) -> list[str]:
    async with session_factory() as session:
        return list(
            (
                await session.execute(
                    select(EventStoreORM.event_type)
                    .where(
                        EventStoreORM.event_type.in_(
                            (
                                "users.user_marked_as_tester",
                                "users.user_unmarked_as_tester",
                            )
                        )
                    )
                    .order_by(EventStoreORM.sequence_no)
                )
            )
            .scalars()
            .all()
        )


async def test_a_new_account_is_not_a_tester(client, valid_signup_payload):
    headers = await _signed_in(client, valid_signup_payload)

    assert await _is_tester(client, headers) is False


async def test_the_registration_answers_is_tester_false(client, valid_signup_payload):
    """The shape ``/me`` shares, and ``false`` is the honest answer about an
    account created one line ago."""

    created = await client.post("/api/v1/users", json=valid_signup_payload)

    assert created.status_code == 201, created.text
    assert created.json()["is_tester"] is False


async def test_me_reads_the_mark_once_the_command_sets_it_by_email(
    client, valid_signup_payload, session_factory
):
    headers = await _signed_in(client, valid_signup_payload)

    marked = await _set(
        session_factory, valid_signup_payload["email"].upper(), tester=True
    )

    assert marked.is_tester is True and marked.changed is True
    assert marked.email == valid_signup_payload["email"]
    assert await _is_tester(client, headers) is True


async def test_the_command_finds_a_player_by_id_and_clears_the_mark(
    client, valid_signup_payload, session_factory
):
    headers = await _signed_in(client, valid_signup_payload)
    player_id = (await client.get("/api/v1/users/me", headers=headers)).json()["id"]
    await _set(session_factory, player_id, tester=True)

    cleared = await _set(session_factory, player_id, tester=False)

    assert str(cleared.player_id) == player_id
    assert cleared.is_tester is False and cleared.changed is True
    assert await _is_tester(client, headers) is False


async def test_each_act_is_one_event_and_a_repeat_is_none(
    client, valid_signup_payload, session_factory
):
    """Marking a Tester again, or unmarking a player who is not one, records
    nothing — and says so, so the command can tell the operator."""

    email = valid_signup_payload["email"]
    await _signed_in(client, valid_signup_payload)

    first = await _set(session_factory, email, tester=True)
    again = await _set(session_factory, email, tester=True)
    cleared = await _set(session_factory, email, tester=False)
    cleared_again = await _set(session_factory, email, tester=False)

    assert [first.changed, again.changed, cleared.changed, cleared_again.changed] == [
        True,
        False,
        True,
        False,
    ]
    assert await _marks_on_the_stream(session_factory) == [
        "users.user_marked_as_tester",
        "users.user_unmarked_as_tester",
    ]


async def test_marking_one_player_marks_nobody_else(
    client, valid_signup_payload, session_factory
):
    alice = await _signed_in(client, valid_signup_payload)
    bob = await _signed_in(client, {**valid_signup_payload, "email": "bob@example.com"})

    await _set(session_factory, valid_signup_payload["email"], tester=True)

    assert await _is_tester(client, alice) is True
    assert await _is_tester(client, bob) is False


@pytest.mark.parametrize(
    "player",
    [
        "nobody@example.com",
        "00000000-0000-4000-8000-000000000000",
        "neither-an-id-nor-an-address",
        "",
    ],
)
async def test_a_player_nobody_answers_to_is_refused(session_factory, player):
    with pytest.raises(UnknownPlayer) as refused:
        await _set(session_factory, player, tester=True)

    assert refused.value.code == "unknown_player"
    assert await _marks_on_the_stream(session_factory) == []
