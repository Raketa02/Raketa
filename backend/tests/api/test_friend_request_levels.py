"""**A friend request names every sport the sender holds a level in** (#814;
``docs/adr/0205`` §2 and §10; the friends screens §6.2) — the sport-levels line
on its tile in *Needs your answer*: *Inés wants to be your friend · ● Padel
3,40 · ● Tennis 2,90*.

Ola reads her Home. Inés, Kuba and Zosia are in her padel group and ask her to
be friends from Members, so each card's own ``sport`` is padel. The line is
``levels``: one entry per sport the sender holds a published Level in, in the
app's sport order, each the Level the card's ``level`` shows for its sport —
and every sender's read in one batch, never a read per request per sport.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

import re
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.kernel import Sport
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from tests.api import players_world as players
from tests.api.proposals_world import MONDAY_MORNING, a_club_selling, a_group, a_member
from tests.unit.fake_clock import MovableClock

FRIENDS = "/api/v1/friends"
HOME = "/api/v1/home"


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def ola(client, session_factory, payments) -> dict:
    return await a_member(client, session_factory, payments, "ola")


async def a_sender(
    client, session_factory, payments, name: str, **levels: float
) -> dict:
    """Somebody rated in exactly ``levels`` (``tennis=2.9``), each stream written
    in the order given — never the order the line is read in."""

    sender = await a_member(client, session_factory, payments, name, sports=())
    for sport, mu in levels.items():
        await players.rate_in(
            session_factory, sender["id"], Sport(sport.upper()), mu=mu
        )
    return sender


async def asks(client, group: UUID, sender: dict, ola: dict) -> None:
    asked = await client.post(
        f"{FRIENDS}/requests",
        json={
            "player_id": str(ola["id"]),
            "made_from": "MEMBERS",
            "group_id": str(group),
            "sport": "PADEL",
        },
        headers=sender["headers"],
    )
    assert asked.status_code == 200, asked.text


async def cards(client, ola: dict) -> dict[str, dict]:
    read = await client.get(HOME, headers=ola["headers"])
    assert read.status_code == 200, read.text
    return {card["nickname"]: card for card in read.json()["friend_requests"]}


async def test_a_sender_rated_in_two_sports_is_named_in_both_in_the_apps_order(
    client, session_factory, payments, clock, club, ola
):
    """Her tennis was written first; the line reads padel first, as the app
    orders its sports — and padel's entry is the card's own ``level``."""

    ines = await a_sender(
        client, session_factory, payments, "ines", tennis=2.9, padel=3.4
    )
    group = await a_group(client, ola, club, ines)
    await asks(client, group, ines, ola)

    card = (await cards(client, ola))["ines"]

    assert card["levels"] == [
        {"sport": "PADEL", "level": pytest.approx(3.4)},
        {"sport": "TENNIS", "level": pytest.approx(2.9)},
    ]
    assert card["sport"] == "PADEL"
    assert card["level"] == card["levels"][0]["level"]


async def test_a_sender_rated_in_nothing_has_no_line(
    client, session_factory, payments, clock, club, ola
):
    zosia = await a_sender(client, session_factory, payments, "zosia")
    group = await a_group(client, ola, club, zosia)
    await asks(client, group, zosia, ola)

    card = (await cards(client, ola))["zosia"]

    assert card["levels"] == []
    assert card["sport"] == "PADEL"
    assert card["level"] is None


async def test_a_level_the_sender_gets_is_on_the_next_read(
    client, session_factory, payments, clock, club, ola
):
    """Inés answers the tennis questionnaire after asking: the request is not
    asked again, and the next read names her tennis — read live, recorded
    nowhere."""

    ines = await a_sender(client, session_factory, payments, "ines", padel=3.4)
    group = await a_group(client, ola, club, ines)
    await asks(client, group, ines, ola)
    assert [one["sport"] for one in (await cards(client, ola))["ines"]["levels"]] == [
        "PADEL"
    ]

    tennis = await players.rate(client, ines["token"], Sport.TENNIS)

    card = (await cards(client, ola))["ines"]
    assert card["levels"] == [
        {"sport": "PADEL", "level": pytest.approx(3.4)},
        {"sport": "TENNIS", "level": pytest.approx(tennis)},
    ]


async def test_every_senders_levels_are_one_read_however_many_ask(
    client, session_factory, payments, clock, club, ola, statements
):
    """One request, then three, each sender rated in two sports: the rating
    streams Home reads are read in the same number of statements — never one
    per request, never one per request per sport."""

    ines = await a_sender(
        client, session_factory, payments, "ines", padel=3.4, tennis=2.9
    )
    kuba = await a_sender(
        client, session_factory, payments, "kuba", padel=2.6, squash=3.1
    )
    zosia = await a_sender(
        client, session_factory, payments, "zosia", tennis=4.0, badminton=1.8
    )
    group = await a_group(client, ola, club, ines, kuba, zosia)

    await asks(client, group, ines, ola)
    with statements.counting() as one_request:
        assert len(await cards(client, ola)) == 1

    await asks(client, group, kuba, ola)
    await asks(client, group, zosia, ola)
    with statements.counting() as three_requests:
        read = await cards(client, ola)

    assert [one["sport"] for one in read["kuba"]["levels"]] == ["PADEL", "SQUASH"]
    assert [one["sport"] for one in read["zosia"]["levels"]] == [
        "TENNIS",
        "BADMINTON",
    ]
    # Heard at all: a counter that heard no rating stream read would pass.
    assert one_request.binding(RATING_AGGREGATE)
    assert len(three_requests.binding(RATING_AGGREGATE)) == len(
        one_request.binding(RATING_AGGREGATE)
    )
    # And one batch, never a batch per sport: the only rating read naming
    # many streams at once is the line's.
    assert len(batched(three_requests.binding(RATING_AGGREGATE))) == 1


def batched(statements: list[str]) -> list[str]:
    return [one for one in statements if re.search(r"\baggregate_id IN \(", one)]
