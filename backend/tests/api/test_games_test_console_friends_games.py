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


# --------------------------------------------------------------------------- #
# An empty seat (#752)
# --------------------------------------------------------------------------- #


async def _sent_by_tomek(client, world: dict) -> str:
    tomek = str(world["tomek"]["id"])
    friend_ids = [str(world[name]["id"]) for name in ("ewa", "magda", "kuba")]
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
    return sent.json()["booking_id"]


async def test_the_console_opens_an_empty_seat_and_invites_into_another(
    client, world, session_factory, payments
):
    """Magda says no and Tomek opens her seat to the group; Kuba says no too,
    and Ewa invites Ola, her own friend, into his."""

    ola = await a_member(
        client, session_factory, payments, "ola", week=SATURDAY_MORNINGS, domain=SEED
    )
    from tests.api.test_friends_card import joins

    await joins(client, world["group"], ola)
    await befriend(client, world["group"], world["ewa"], ola)
    booking = await _sent_by_tomek(client, world)
    for name, act in (("ewa", "acceptance"), ("magda", "decline"), ("kuba", "decline")):
        done = await client.post(
            f"/dev/as/{world[name]['id']}/bookings/{booking}/invitation/{act}"
        )
        assert done.status_code in (200, 204), done.text
    [game] = (await board_row(client, world, "tomek"))["friends_games"]
    empty = {seat["person"]["nickname"]: seat for seat in game["seats"]}
    assert empty["magda"]["seat_of"] == str(world["magda"]["id"])

    opened = await client.post(
        f"/dev/as/{world['tomek']['id']}/bookings/{booking}/seats/"
        f"{world['magda']['id']}/opening"
    )
    invited = await client.post(
        f"/dev/as/{world['ewa']['id']}/bookings/{booking}/seats/"
        f"{world['kuba']['id']}/invitations",
        json={"friend_id": str(ola["id"])},
    )

    assert (opened.status_code, invited.status_code) == (204, 204), invited.text
    [game] = (await board_row(client, world, "tomek"))["friends_games"]
    seats = {seat["person"]["nickname"]: seat for seat in game["seats"]}
    assert seats["magda"]["state"] == "SEAT_OPEN"
    assert [one["nickname"] for one in seats["kuba"]["invited"]] == ["ola"]
    # The press is the player's own: Ewa, not the sender, opens nothing.
    refused = await client.post(
        f"/dev/as/{world['ewa']['id']}/bookings/{booking}/seats/"
        f"{world['kuba']['id']}/opening"
    )
    assert refused.json()["code"] == "booking_not_found"


async def test_the_console_runs_the_cover_warning(client, world):
    ran = await client.post("/dev/jobs/cover-warning")

    assert ran.status_code == 200, ran.text
    assert (ran.json()["job"], ran.json()["done"]) == ("cover-warning", 0)
