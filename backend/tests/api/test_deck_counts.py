"""Your cards per kind, across your groups (#739; ``docs/adr/0201``, Q127; the
You screen §3.3).

On You › *What kind of game* › Padel, the line *"Your 7 competitive cards in
your groups go"* needs the 7: ``GET /players/me/deck-counts?sport=`` answers
how many cards each kind deals the caller now in one sport, **summed over every
group they are in** — each group's number exactly the one its switch shows.

Every card is made the way a seed makes one, through the dealer's own act, and
every claim is read back as the phone reads it.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the tenth is a
Saturday, the eleventh a Sunday.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.engines.matchfit.core import SearchMode
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    changes_intent,
    makes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

DECK_COUNTS = "/api/v1/players/me/deck-counts"


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


async def counts_of(client, player: dict, sport: str = "PADEL") -> dict:
    read = await client.get(
        DECK_COUNTS, params={"sport": sport}, headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    return read.json()


async def switch_of(client, player: dict, group: UUID) -> dict[str, int]:
    """The count each side of the group's switch shows."""

    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return {segment["kind"]: segment["count"] for segment in read.json()["segments"]}


async def anias_two_groups(client, session_factory, payments, clock):
    """Ania and six others, all happy with either kind, in two groups at one
    club. Her first group deals her two competitive cards; her second, one
    competitive and one for fun. Ania, and her two groups."""

    club = await a_club_selling(client)
    ania, ola, kuba, ewa, tomek, zofia, marek = [
        await a_member(client, session_factory, payments, name, intent="NO_PREFERENCE")
        for name in ("ania", "ola", "kuba", "ewa", "tomek", "zofia", "marek")
    ]
    everybody = (ola, kuba, ewa, tomek, zofia, marek)
    first = await a_group(client, ania, club, *everybody)
    second = await a_group(client, ania, club, *everybody)
    for pool, start, kind, four in (
        (first, warsaw(10, 17), SearchMode.COMPETITIVE, (ania, ola, kuba, ewa)),
        (first, warsaw(10, 18), SearchMode.COMPETITIVE, (ania, tomek, zofia, marek)),
        (second, warsaw(11, 10), SearchMode.FOR_FUN, (ania, ola, tomek, zofia)),
        (second, warsaw(11, 12), SearchMode.COMPETITIVE, (ania, kuba, ewa, marek)),
    ):
        await makes(
            session_factory,
            clock,
            pool_id=pool,
            club_id=club,
            start=start,
            kind=kind,
            versions=(four,),
        )
    return ania, first, second


async def test_each_kind_is_her_groups_switch_counts_summed(
    client, session_factory, payments, clock
):
    ania, first, second = await anias_two_groups(
        client, session_factory, payments, clock
    )

    counts = await counts_of(client, ania)

    assert counts == {"sport": "PADEL", "competitive": 3, "for_fun": 1}
    switches = [await switch_of(client, ania, group) for group in (first, second)]
    assert switches == [
        {"COMPETITIVE": 2, "FOR_FUN": 0},
        {"COMPETITIVE": 1, "FOR_FUN": 1},
    ]


async def test_a_kind_her_intent_does_not_show_is_nought(
    client, session_factory, payments, clock
):
    ania, _, _ = await anias_two_groups(client, session_factory, payments, clock)

    await changes_intent(client, ania, "COMPETITIVE")

    assert await counts_of(client, ania) == {
        "sport": "PADEL",
        "competitive": 3,
        "for_fun": 0,
    }


async def test_a_sport_she_has_declared_nothing_in_is_nought_and_nought(
    client, session_factory, payments, clock
):
    ania, _, _ = await anias_two_groups(client, session_factory, payments, clock)

    assert await counts_of(client, ania, "TENNIS") == {
        "sport": "TENNIS",
        "competitive": 0,
        "for_fun": 0,
    }


async def test_the_counts_need_a_player(client):
    read = await client.get(DECK_COUNTS, params={"sport": "PADEL"})

    assert read.status_code == 401
