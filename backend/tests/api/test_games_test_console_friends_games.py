"""**The games test console sends, accepts, declines and calls off a friends
game as seed accounts** (#751; ``docs/adr/0194``): each press the player's own
use case, refusals included, and the board's row listing what it acts on.

Ogrody 33 sells one padel court on Saturdays at 10:00, 100 zł; **Tomek**,
**Ewa**, **Magda** and **Kuba** are seed accounts in its group, the three
Tomek's friends. The clock stands on **Monday 5 October 2026, 08:00**.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from tests.api.console_world import SEED
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_and_its_desk,
    a_group,
    a_member,
)
from tests.api.test_friends_on_every_face import befriend
from tests.unit.fake_clock import MovableClock

SATURDAY_MORNINGS = [{"day": 6, "hour": 10}]


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def world(client, session_factory, payments, clock) -> dict:
    club, _ = await a_club_and_its_desk(
        client, name="Ogrody 33", hours=[(6, 10)], padel_grosze=100_00
    )
    people = {
        name: await a_member(
            client,
            session_factory,
            payments,
            name,
            week=SATURDAY_MORNINGS,
            domain=SEED,
        )
        for name in ("tomek", "ewa", "magda", "kuba")
    }
    group = await a_group(
        client, people["tomek"], club, people["ewa"], people["magda"], people["kuba"]
    )
    for friend in ("ewa", "magda", "kuba"):
        await befriend(client, group, people["tomek"], people[friend])
    return {"group": group, **people}


async def board_row(client, world: dict, name: str) -> dict:
    read = await client.get(f"/dev/groups/{world['group']}", params={"sport": "PADEL"})
    assert read.status_code == 200, read.text
    [row] = [
        row
        for row in read.json()["people"]
        if row["player_id"] == str(world[name]["id"])
    ]
    return row


async def test_the_console_sends_and_its_friends_answer_as_each_of_them(client, world):
    tomek = str(world["tomek"]["id"])
    row = await board_row(client, world, "tomek")
    assert {friend["nickname"] for friend in row["friends"]} == {"ewa", "magda", "kuba"}
    friend_ids = [friend["player_id"] for friend in row["friends"]]

    card = await client.get(
        f"/dev/as/{tomek}/pools/{world['group']}/friends-card",
        params={"sport": "PADEL", "kind": "COMPETITIVE", "friend_ids": friend_ids},
    )
    assert card.status_code == 200, card.text
    sent = await client.post(
        f"/dev/as/{tomek}/pools/{world['group']}/friends-games",
        json={
            "sport": "PADEL",
            "kind": "COMPETITIVE",
            "friend_ids": friend_ids,
            "court_id": card.json()["court"]["court_id"],
            "starts_at": card.json()["court"]["starts_at"],
            "pay_mode": "SPLIT_THE_COST",
        },
    )
    assert sent.status_code == 200, sent.text
    booking = sent.json()["booking_id"]

    [invited] = (await board_row(client, world, "ewa"))["friends_games"]
    assert invited["booking_id"] == booking
    assert invited["invited_until"] is not None
    ewa = str(world["ewa"]["id"])
    accepted = await client.post(
        f"/dev/as/{ewa}/bookings/{booking}/invitation/acceptance"
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted"] is True
    magda = str(world["magda"]["id"])
    declined = await client.post(
        f"/dev/as/{magda}/bookings/{booking}/invitation/decline"
    )
    assert declined.status_code == 204, declined.text

    [game] = (await board_row(client, world, "tomek"))["friends_games"]
    assert game["you_are_the_sender"] is True
    assert {seat["person"]["nickname"]: seat["state"] for seat in game["seats"]} == {
        "tomek": "IN",
        "ewa": "IN",
        "magda": "DECLINED",
        "kuba": "WAITING",
    }

    called = await client.post(f"/dev/as/{tomek}/bookings/{booking}/call-off")
    assert called.status_code == 204, called.text
    [game] = (await board_row(client, world, "tomek"))["friends_games"]
    assert game["state"] == "CALLED_OFF"


async def test_a_press_is_refused_as_the_players_own_route_refuses_it(client, world):
    tomek = str(world["tomek"]["id"])

    refused = await client.post(f"/dev/as/{tomek}/bookings/{UUID(int=1)}/call-off")

    assert refused.status_code == 404
    assert refused.json()["code"] == "booking_not_found"
