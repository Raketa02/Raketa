"""``distance_km`` is one decimal on every candidate, spot to spot — over HTTP.

``docs/adr/0174`` §2: the deck and the radar print the same number for the same
person, so *every* surface that carries a candidate prints the one-decimal
distance between two **drawn spots**, never below ``0.1``, and still omits it
when the distance term stood down. Asserted here against the number the domain
derives for the same two people, so a surface that quietly kept the whole
kilometre — or measured from the cell rather than the spot — goes red by value
and not by type alone.

The five surfaces: the shortlist, the deck, the line-up, completing a
half-built court, and the challenge card an invitee reads. The read-back is the
sixth reader and prints what was recorded.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.modules.matchmaking.domain.geography import (
    Point,
    distance_km,
    drawn_spot,
    shown_kilometres,
)
from tests.api import matchmaking_world as world

#: One cell north-east of the searcher's — near enough for every gate, far
#: enough that the print is a distance and not the floor.
NEARBY = (51.53, -0.10)


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


def expected_print(viewer_id: UUID, player_id: UUID, cell: tuple[float, float]):
    """What the card should say, derived the way the domain derives it."""

    viewer = drawn_spot(viewer_id, Point(*world.CENTRE))
    theirs = drawn_spot(player_id, Point(*cell))
    return shown_kilometres(distance_km(viewer, theirs))


def _by_id(candidates: list[dict]) -> dict[str, dict]:
    return {row["player_id"]: row for row in candidates}


def assert_one_decimal(printed) -> None:
    assert isinstance(printed, float), f"{printed!r} is not a number with a decimal"
    assert printed == round(printed, 1)
    assert printed >= 0.1


async def test_the_shortlist_prints_the_spot_distance_to_one_decimal(
    client, session_factory, candidate_source, searcher
):
    """*1,9 km* where the card said *2 km* — and *0,x km* for somebody in the
    searcher's own cell, where it used to say *0 km*."""

    same_cell = await world.a_candidate(
        client, session_factory, "same-cell", mu=searcher["mu"]
    )
    nearby = await world.a_candidate(
        client,
        session_factory,
        "nearby",
        mu=searcher["mu"],
        latitude=NEARBY[0],
        longitude=NEARBY[1],
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await world.search(client, searcher["token"])).json()

    rows = _by_id(body["candidates"])
    assert set(rows) == {str(same_cell), str(nearby)}
    for player_id, cell in ((same_cell, world.CENTRE), (nearby, NEARBY)):
        printed = rows[str(player_id)]["distance_km"]
        assert_one_decimal(printed)
        assert printed == expected_print(searcher["id"], player_id, cell)


async def test_the_read_back_prints_what_the_search_printed(
    client, session_factory, candidate_source, searcher
):
    nearby = await world.a_candidate(
        client,
        session_factory,
        "nearby",
        mu=searcher["mu"],
        latitude=NEARBY[0],
        longitude=NEARBY[1],
    )
    await world.fold_the_log(session_factory, candidate_source)
    searched = (await world.search(client, searcher["token"])).json()

    read = (
        await world.read_back(
            client, searcher["token"], searched["search"]["search_id"]
        )
    ).json()

    printed = _by_id(read["candidates"])[str(nearby)]["distance_km"]
    assert printed == _by_id(searched["candidates"])[str(nearby)]["distance_km"]
    assert_one_decimal(printed)


async def test_the_deck_prints_the_same_number_the_shortlist_does(
    client, session_factory, candidate_source, searcher
):
    """The author's rule: one number for one person, whichever surface."""

    nearby = await world.a_candidate(
        client,
        session_factory,
        "nearby",
        mu=searcher["mu"],
        latitude=NEARBY[0],
        longitude=NEARBY[1],
    )
    await world.fold_the_log(session_factory, candidate_source)

    dealt = (await world.deck(client, searcher["token"])).json()
    listed = (await world.search(client, searcher["token"])).json()

    on_the_deck = _by_id(dealt["candidates"])[str(nearby)]["distance_km"]
    assert_one_decimal(on_the_deck)
    assert on_the_deck == _by_id(listed["candidates"])[str(nearby)]["distance_km"]
    assert on_the_deck == expected_print(searcher["id"], nearby, NEARBY)


async def test_the_line_up_and_its_fill_print_it_on_every_seated_row(
    client, session_factory, candidate_source, searcher
):
    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05), ("dee", 0.10)):
        player_id, token = await world.a_signed_in_candidate(
            client,
            session_factory,
            name,
            mu=searcher["mu"] + delta,
            latitude=NEARBY[0],
            longitude=NEARBY[1],
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)

    seated = (await world.lineup(client, searcher["token"])).json()
    rows = _by_id(seated["candidates"])
    assert len(rows) >= 3
    for player_id, row in rows.items():
        assert_one_decimal(row["distance_km"])
        assert row["distance_km"] == expected_print(
            searcher["id"], UUID(player_id), NEARBY
        )

    # The fill: a padel four sent to one person who accepts, then ⚡ naming it.
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(people["ana"]["id"])},
        {"side": "B"},
        {"side": "B"},
    ]
    sent = await client.post(
        "/api/v1/challenges",
        json={"search_id": seated["search"]["search_id"], "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert sent.status_code == 201, sent.text
    challenge_id = sent.json()["challenge_id"]
    accepted = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(people["ana"]["token"]),
    )
    assert accepted.status_code == 200, accepted.text

    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )

    assert filled.status_code == 200, filled.text
    body = filled.json()
    assert body["search"]["surface"] == "FILL_SEATS"
    for player_id, row in _by_id(body["candidates"]).items():
        assert_one_decimal(row["distance_km"])
        assert row["distance_km"] == expected_print(
            searcher["id"], UUID(player_id), NEARBY
        )


async def test_the_challenge_card_an_invitee_reads_prints_it_in_their_direction(
    client, session_factory, candidate_source, exposure_ledger, searcher
):
    """The card is recomputed for the reader (``docs/adr/0143``), and the spot
    is fixed per player, so the invitee's print is spot to spot the other way
    round — the same two spots, the same number."""

    world.draw_real_cards(client, candidate_source, exposure_ledger)
    ana = await world.a_searcher(client, "ana")
    await world.fold_the_log(session_factory, candidate_source)
    listed = (await world.search(client, searcher["token"])).json()
    sent = await client.post(
        "/api/v1/challenges",
        json={
            "search_id": listed["search"]["search_id"],
            # A padel court is a four; the two empty seats are nobody's yet.
            "court": [
                {"side": "A", "player_id": str(searcher["id"])},
                {"side": "A"},
                {"side": "B", "player_id": str(ana["id"])},
                {"side": "B"},
            ],
        },
        headers=world.auth(searcher["token"]),
    )
    assert sent.status_code == 201, sent.text

    detail = await client.get(
        f"/api/v1/challenges/{sent.json()['challenge_id']}",
        headers=world.auth(ana["token"]),
    )

    assert detail.status_code == 200, detail.text
    organiser = next(
        seat
        for seat in detail.json()["seats"]
        if seat.get("player_id") == str(searcher["id"])
    )
    printed = organiser["card"]["pairing"]["distance_km"]
    assert_one_decimal(printed)
    assert printed == expected_print(ana["id"], searcher["id"], world.CENTRE)
