"""Kuba's phone never receives Ania's name, only ``ania.k`` (#724).

``docs/adr/0199``: the Name is retired and the **nickname** is what every
sentence, row, card, notice and email says about a player. One court of four —
Ania, who picked ``ania.k``, Kuba, Ewa and Tomek — at Bonarka on Saturday, read
through every player route that names a person: the deck before the game
fills, Members, the payment email it fills with, the booked game's chat, the
notice Ania's departure gives the others, and her record. Each carries
``ania.k`` and nothing called ``name``.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from tests.api.console_world import deck_of
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    makes,
    says_yes,
)
from tests.unit.fake_clock import MovableClock

NOTICES = "/api/v1/players/me/notices"
ANIA = "ania.k"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def court(client, session_factory, payments) -> list[dict]:
    """Kuba, Ewa, Tomek and Ania — who signed up as ``ania.k@example.com`` and
    named herself ``ania.k``."""

    return [
        await a_member(client, session_factory, payments, name)
        for name in ("kuba", "ewa", "tomek", ANIA)
    ]


@pytest.fixture
async def group(client, club, court) -> UUID:
    return await a_group(client, court[0], club, *court[1:])


def nameless(shape: object) -> bool:
    """Whether no dict anywhere in a response carries a ``name`` key beside a
    ``player_id`` — the shape a person is drawn in."""

    if isinstance(shape, dict):
        if "player_id" in shape and "name" in shape:
            return False
        return all(nameless(value) for value in shape.values())
    if isinstance(shape, list):
        return all(nameless(value) for value in shape)
    return True


async def test_the_deck_and_members_say_ania_k(
    client, session_factory, clock, club, court, group
):
    kuba = court[0]
    await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(court),)
    )

    [card] = await deck_of(client, kuba, group)
    members = await client.get(
        f"/api/v1/groups/{group}/members",
        params={"sport": "PADEL"},
        headers=kuba["headers"],
    )

    tiles = card["sides"]["yours"] + card["sides"]["theirs"]
    assert ANIA in {tile["nickname"] for tile in tiles}
    assert nameless(card)
    assert members.status_code == 200, members.text
    rows = members.json()["members"]
    assert ANIA in {row["nickname"] for row in rows}
    assert nameless(rows)


async def test_the_payment_email_greets_ania_k(
    client, session_factory, clock, mailbox, club, court, group
):
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(court),)
    )
    for player in court:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    await mailbox.drain()

    [booked] = await mailbox.to(f"{ANIA}@example.com")

    assert booked.text.startswith(f"It's a game, {ANIA}!")
    assert f"@{ANIA}" not in booked.text


async def test_the_chat_the_notices_and_the_record_say_ania_k(
    client, session_factory, clock, mailbox, club, court, group
):
    kuba, ania = court[0], court[3]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(court),)
    )
    for player in court:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    await mailbox.drain()

    rooms = await client.get("/api/v1/conversations", headers=kuba["headers"])
    assert rooms.status_code == 200, rooms.text
    [room] = rooms.json()["conversations"]
    read = await client.get(
        f"/api/v1/conversations/{room['conversation_id']}", headers=kuba["headers"]
    )
    assert read.status_code == 200, read.text
    chat = read.json()
    assert ANIA in {person["nickname"] for person in chat["people"]}
    assert ANIA in {member["nickname"] for member in chat["members"]}
    assert nameless(chat)

    left = await client.post(
        f"/api/v1/bookings/{proposal}/departure", headers=ania["headers"]
    )
    assert left.status_code == 200, left.text
    await mailbox.drain()
    notices = await client.get(NOTICES, headers=kuba["headers"])
    assert notices.status_code == 200, notices.text
    assert f"{ANIA} left your game" in [
        notice["title"] for notice in notices.json()["notices"]
    ]

    record = await client.get(
        f"/api/v1/players/{ania['id']}/record", headers=kuba["headers"]
    )
    assert record.status_code == 200, record.text
    assert record.json()["nickname"] == ANIA
    assert "name" not in record.json()


async def test_a_new_nickname_reaches_everybody_from_their_next_read(
    client, session_factory, clock, club, court, group
):
    """Changeable at any time, and nothing links the old to the new
    (``docs/adr/0199`` §3)."""

    kuba, ania = court[0], court[3]
    renamed = await client.put(
        "/api/v1/users/me/name", json={"nickname": "ak.padel"}, headers=ania["headers"]
    )
    assert renamed.status_code == 200, renamed.text

    members = await client.get(
        f"/api/v1/groups/{group}/members",
        params={"sport": "PADEL"},
        headers=kuba["headers"],
    )

    nicknames = {row["nickname"] for row in members.json()["members"]}
    assert "ak.padel" in nicknames
    assert ANIA not in nicknames
