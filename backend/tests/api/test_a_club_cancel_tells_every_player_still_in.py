"""**A club's cancel tells every player still in the game it called off** (#711;
the mechanics §13, §16.9, Q113; ADR-0196 §2).

A game that fills a week ahead is checked, not held: Ivan's Visa hold would not
last until the cut-off, so his share is only **checked** and nothing is held on
his card. Oscar, Marta and Paula's Mastercard holds reach the cut-off and stand.
The club cancels before the cut-off — nothing is taken, nobody is refunded — and
each of the four must be told the game was called off, whichever way their share
was held. The bell reads that notice off the list, and the phone is pushed it.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.api.dependencies import get_clock
from app.modules.payments.domain.entered_cards import A_CARD
from tests.api.proposals_world import (
    a_club_and_its_desk,
    a_group,
    a_member,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

NOTICES = "/api/v1/players/me/notices"

#: Thursday 8 October, 19:00 in Kraków: the last yes, a week ahead.
THE_FILL = warsaw(8, 19)
#: Thursday 15 October, 19:00: the game.
THE_GAME = warsaw(15, 19)
#: Friday 9 October, 19:00: the club cancels it, well before the cut-off.
THE_CANCEL = warsaw(9, 19)

A_MASTERCARD = replace(A_CARD, brand="mastercard", last_four="4444")


@pytest.fixture
def clock(app, payments):
    fixed = MovableClock(THE_FILL)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


@pytest.fixture
async def club(client) -> tuple[str, dict]:
    return await a_club_and_its_desk(client, padel_grosze=160_00)


@pytest.fixture
async def four(client, session_factory, payments) -> dict[str, dict]:
    people = {
        "ivan": await a_member(client, session_factory, payments, "ivan"),
        **{
            name: await a_member(
                client, session_factory, payments, name, entered=A_MASTERCARD
            )
            for name in ("oscar", "marta", "paula")
        },
    }
    people["diego"] = await a_member(client, session_factory, payments, "diego")
    return people


async def fills(client, session_factory, clock, club: str, people: dict) -> str:
    four = [people[name] for name in ("oscar", "marta", "paula", "ivan")]
    group = await a_group(client, four[0], club, *four[1:], people["diego"])
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=THE_GAME,
        versions=(tuple(four),),
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    assert last.json()["booked"] is not None, last.text
    return last.json()["booked"]["booking_id"]


async def told(client, mailbox, player: dict) -> list[dict]:
    await mailbox.drain()
    read = await client.get(NOTICES, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["notices"]


async def test_every_player_still_in_is_told_the_game_was_called_off(
    client, session_factory, clock, payments, mailbox, club, four
):
    booking = await fills(client, session_factory, clock, club[0], four)
    await mailbox.drain()
    clock.move(THE_CANCEL - THE_FILL)

    # Ivan's share is only checked: nothing is held on his card for it.
    read = await client.get("/api/v1/home", headers=four["ivan"]["headers"])
    [card] = read.json()["games"]
    assert card["money"]["share_state"] == "CHECKED"

    cancelled = await client.post(
        f"/api/v1/club/bookings/{booking}/cancellation",
        json={"reason": "WEATHER"},
        headers=club[1],
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["outcome"] == "CALLED_OFF"

    # The checked share is told as the three held ones are: called off, with the
    # club's reason, and nothing taken.
    for name in ("ivan", "oscar", "marta", "paula"):
        notices = await told(client, mailbox, four[name])
        called_off = [n for n in notices if n["kind"] == "GAME_CALLED_OFF"]
        assert [n["title"] for n in called_off] == [
            "Game called off · nothing was taken"
        ], (name, notices)
        assert "weather" in called_off[0]["body"], (name, called_off)
