"""A location moves on a cold start, and everything that reads it follows.

``docs/adr/0174`` §6, end to end: Filip moves; the next time his app launches it
puts his phone's position; his Location area moves to the new cell; his new
neighbour's next deal finds him there, and the neighbour he left behind no
longer does. Nothing else moves. The issue's Filip crossed Kraków; this one goes
from the fixture's London to Warsaw, so that no reach a profile can hold keeps
him in both cities and the assertion is about the cell and never the radius.

**Two facts are asserted and they live in two places.** The *searcher's* own
area is read live off the aggregate at request time, so Filip's own deal draws
its box around the new cell the instant the write commits. Everybody *else*
reads him off the candidate index, which tails the log — so what the index
holds after the fold is one row, in the new cell, and the old cell's row is
gone. The fold is run in-process here exactly as ``matchmaking_world`` runs it
for every other test.

**Why the reads before the move are shortlists and not deals.** A deal remembers
whom it dealt for a day (``docs/adr/0131``), so a neighbour who had already been
dealt Filip would be shown him again by nothing — and the assertion would pass
for the wrong reason. The shortlist has no dealt memory; the deal after the
move is the first either neighbour makes.
"""

from __future__ import annotations

from tests.api import matchmaking_world as world

LOCATION_URL = "/api/v1/players/me/location"
#: Another city entirely — far outside any reach a profile can hold.
WARSAW = (52.23, 21.01)
#: A fix inside that cell, as a phone would read one.
WARSAW_FIX = {"latitude": 52.2297, "longitude": 21.0122}


def ids_on(response) -> set[str]:
    assert response.status_code == 200, response.text
    return {row["player_id"] for row in response.json()["candidates"]}


async def test_a_neighbour_in_the_new_cell_deals_the_player_who_moved_there(
    client, session_factory, candidate_source
):
    filip = await world.a_searcher(client, "filip")
    basia = await world.a_searcher(client, "basia", location=WARSAW)
    await world.fold_the_log(session_factory, candidate_source)
    assert str(filip["id"]) not in ids_on(await world.search(client, basia["token"]))

    moved = await client.put(
        LOCATION_URL, json=WARSAW_FIX, headers=world.auth(filip["token"])
    )
    assert moved.status_code == 204, moved.text
    await world.fold_the_log(session_factory, candidate_source)

    assert str(filip["id"]) in ids_on(await world.deck(client, basia["token"]))


async def test_the_old_cells_row_is_gone(client, session_factory, candidate_source):
    """One row per player per sport: a move is an update and never a second
    row, so the neighbour Filip left behind stops finding him."""

    filip = await world.a_searcher(client, "filip")
    ania = await world.a_searcher(client, "ania")
    await world.fold_the_log(session_factory, candidate_source)
    assert str(filip["id"]) in ids_on(await world.search(client, ania["token"]))

    await client.put(LOCATION_URL, json=WARSAW_FIX, headers=world.auth(filip["token"]))
    await world.fold_the_log(session_factory, candidate_source)

    assert str(filip["id"]) not in ids_on(await world.search(client, ania["token"]))


async def test_the_deal_after_the_move_draws_the_box_around_the_new_cell(
    client, session_factory, candidate_source
):
    """Filip's own deal: the searcher is read live, so the box moves with the
    write and the hand is dealt from the new city with nothing reset."""

    filip = await world.a_searcher(client, "filip")
    ania = await world.a_searcher(client, "ania")
    basia = await world.a_searcher(client, "basia", location=WARSAW)
    await world.fold_the_log(session_factory, candidate_source)

    await client.put(LOCATION_URL, json=WARSAW_FIX, headers=world.auth(filip["token"]))

    dealt = ids_on(await world.deck(client, filip["token"]))
    assert str(basia["id"]) in dealt
    assert str(ania["id"]) not in dealt
