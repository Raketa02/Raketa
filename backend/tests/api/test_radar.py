"""The reading — the radar's fifth surface, over HTTP.

``docs/adr/0174`` §1, §3, §4 and §5, asserted on the real route through the
async client fixture: ASGI transport over in-memory SQLite, **no MinIO, no
sidecar and no Redis**.

What is asserted is the product's promises. That a reading draws **everyone**
inside the reach — the cooling-off, the passed, the matched and the level-far
included — each with a Fit, a one-decimal distance, a bearing and their sport
chips, ordered by distance and then id. That the **five** gates the radar asks
still hold, that a gate that cannot be evaluated refuses the reading, and that
the four it does not ask exclude nobody. That the chip on the envelope is **the
deck's number**, equal to the deal's on the same fixture and omitted at zero.
That a reading is a recorded search and a prior disclosure, and **never a deal**:
the dealt memory after a reading is empty. And that an answer given on the
radar names the reading as its origin and writes the ledgers the deck writes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select

from app.kernel import Sport
from app.modules.matchmaking.domain.geography import (
    Point,
    bearing_deg,
    drawn_spot,
)
from app.modules.matchmaking.domain.searches import SearchSurface
from app.modules.matchmaking.infrastructure.interest_model import InterestORM
from app.modules.matchmaking.infrastructure.search_model import SearchORM
from tests.api import matchmaking_world as world
from tests.api.test_deck import _a_game_between
from tests.api.test_player_record import record_of

RADAR_URL = "/api/v1/radar"

#: One cell north-east of the searcher's — a bearing between north and east.
NEARBY = (51.53, -0.10)


async def read_the_radar(client, token: str, sport: Sport = world.SPORT):
    """One reading. **The sport is the whole ask** — no radius, no mode, no
    position: the server holds the viewer's cell and their reach."""

    return await client.post(
        RADAR_URL, json={"sport": sport.value}, headers=world.auth(token)
    )


def rows_by_id(body: dict) -> dict[str, dict]:
    return {row["player_id"]: row for row in body["candidates"]}


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


# ---------------------------------------------------------------------------
# Who is drawn
# ---------------------------------------------------------------------------


async def test_a_reading_draws_the_cooling_off_the_passed_the_matched_and_the_level_far(
    client, session_factory, candidate_source, searcher
):
    """Karol (played ten days ago), Magda (passed yesterday), Marek (matched)
    and a player whose Level the deck would never deal: all drawn, each with a
    Fit — and the deal beside it draws none of the four."""

    karol = await world.a_candidate(client, session_factory, "karol", mu=searcher["mu"])
    magda = await world.a_candidate(client, session_factory, "magda", mu=searcher["mu"])
    marek = await world.a_searcher(client, "marek")
    level_far = await world.a_candidate(
        client, session_factory, "far", mu=searcher["mu"] + 2.0
    )
    await world.fold_the_log(session_factory, candidate_source)
    now = datetime.now(timezone.utc)
    await _a_game_between(
        session_factory,
        searcher["id"],
        karol,
        planned_at=now - timedelta(days=10, hours=2),
        played_at=now - timedelta(days=10),
    )
    dealt = (await world.deck(client, searcher["token"])).json()
    passed = await world.pass_on(
        client,
        searcher["token"],
        player_id=magda,
        search_id=dealt["search"]["search_id"],
    )
    assert passed.status_code == 204, passed.text
    # A mutual: marek says yes to the searcher, and the searcher says yes back.
    await world.a_yes(
        client, session_factory, candidate_source, sender=marek, towards=searcher["id"]
    )
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=marek["id"]
    )

    reading = await read_the_radar(client, searcher["token"])
    deal = (await world.deck(client, searcher["token"])).json()

    assert reading.status_code == 200, reading.text
    drawn = rows_by_id(reading.json())
    assert {str(karol), str(magda), str(marek["id"]), str(level_far)} <= set(drawn)
    for row in drawn.values():
        assert 0 <= row["fit"] <= 100
    assert not {str(karol), str(magda), str(marek["id"]), str(level_far)} & set(
        rows_by_id(deal)
    )


async def test_every_row_carries_a_bearing_a_one_decimal_distance_and_its_sport_chips(
    client, session_factory, candidate_source, searcher
):
    """Position is the pair's and never the card's: ``bearing_deg`` sits beside
    ``distance_km`` on the row, spot to spot, and ``ratings[]`` names every
    sport the player is rated in with the Level held there."""

    two_sports = await world.a_candidate(
        client,
        session_factory,
        "two-sports",
        mu=searcher["mu"],
        latitude=NEARBY[0],
        longitude=NEARBY[1],
    )
    await world.rate_in(session_factory, two_sports, Sport.TENNIS, mu=3.4)
    await world.fold_the_log(session_factory, candidate_source)

    body = (await read_the_radar(client, searcher["token"])).json()

    row = rows_by_id(body)[str(two_sports)]
    viewer = drawn_spot(searcher["id"], Point(*world.CENTRE))
    theirs = drawn_spot(two_sports, Point(*NEARBY))
    assert row["bearing_deg"] == bearing_deg(viewer, theirs)
    assert 0 <= row["bearing_deg"] <= 359
    assert "bearing_deg" not in row["player_card"]
    assert row["distance_km"] == round(row["distance_km"], 1) >= 0.1
    assert row["ratings"] == [
        {"sport": "PADEL", "level": row["player_card"]["level"]},
        {"sport": "TENNIS", "level": 3.4},
    ]
    assert row["player_card"]["level"] == searcher["mu"]


async def test_the_order_is_the_distance_then_the_id(
    client, session_factory, candidate_source, searcher
):
    near = await world.a_candidate(client, session_factory, "near", mu=searcher["mu"])
    further = await world.a_candidate(
        client,
        session_factory,
        "further",
        mu=searcher["mu"],
        latitude=world.CENTRE[0] + 0.03,
    )
    furthest = await world.a_candidate(
        client,
        session_factory,
        "furthest",
        mu=searcher["mu"],
        latitude=world.CENTRE[0] + 0.06,
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await read_the_radar(client, searcher["token"])).json()

    assert [row["player_id"] for row in body["candidates"]] == [
        str(near),
        str(further),
        str(furthest),
    ]
    distances = [row["distance_km"] for row in body["candidates"]]
    assert distances == sorted(distances)


# ---------------------------------------------------------------------------
# The five gates
# ---------------------------------------------------------------------------


async def test_the_five_gates_hold_and_the_four_not_asked_exclude_nobody(
    client, session_factory, candidate_source, searcher
):
    """Blocked either way, held, disabled and gender-excluded are absent; an
    open court with the viewer and a far Level are drawn."""

    blocked_by_me = await world.a_candidate(
        client, session_factory, "blocked-by-me", mu=searcher["mu"]
    )
    blocker, their_token = await world.a_signed_in_candidate(
        client, session_factory, "blocker", mu=searcher["mu"]
    )
    held = await world.a_candidate(client, session_factory, "held", mu=searcher["mu"])
    disabled = await world.a_candidate(
        client, session_factory, "disabled", mu=searcher["mu"]
    )
    men_only = await world.a_candidate(
        client,
        session_factory,
        "men-only",
        mu=searcher["mu"],
        gender="MAN",
        gender_preference="SAME_GENDER_ONLY",
    )
    drawn_anyway = await world.a_candidate(
        client, session_factory, "drawn", mu=searcher["mu"] + 2.0
    )
    await world.fold_the_log(session_factory, candidate_source)
    assert (
        await world.block_between(client, searcher["token"], blocked_by_me)
    ).status_code in (200, 201, 204)
    assert (
        await world.block_between(client, their_token, searcher["id"])
    ).status_code in (
        200,
        201,
        204,
    )
    world.hold_only(client, held)
    world.may_not_show(client, disabled)

    body = (await read_the_radar(client, searcher["token"])).json()

    drawn = set(rows_by_id(body))
    assert str(drawn_anyway) in drawn
    assert (
        not {str(blocked_by_me), str(blocker), str(held), str(disabled), str(men_only)}
        & drawn
    )
    assert body["search"]["pool"]["players_in_range"] == 1


async def test_a_gate_that_cannot_be_evaluated_refuses_the_reading(
    client, session_factory, candidate_source, searcher
):
    from app.modules.blocks.domain.errors import BlockStateUnavailable
    from app.modules.blocks.presentation.dependencies import get_block_query

    class Unreachable:
        async def exclusions_for(self, player_id):
            raise BlockStateUnavailable("the block store is unreachable")

        async def blocked_between(self, first, second):
            raise BlockStateUnavailable("the block store is unreachable")

    await world.a_candidate(client, session_factory, "somebody", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    world.override(client, get_block_query, Unreachable)

    response = await read_the_radar(client, searcher["token"])

    assert response.status_code == 503, response.text
    assert response.json()["code"] == "gate_data_unavailable"


# ---------------------------------------------------------------------------
# The chip
# ---------------------------------------------------------------------------


async def test_the_chip_is_the_decks_number_and_is_omitted_at_zero(
    client, session_factory, candidate_source, searcher
):
    """``pool.want_to_play_you`` is computed by the deck's own rule over the
    deck's own gates (``docs/adr/0174`` §5): it equals the deal's on the same
    fixture, and the named edge holds — a liker whose Level is too far for the
    deck to deal is drawn, carries ``INTEREST_LIFT``, and is not counted."""

    quiet = (await read_the_radar(client, searcher["token"])).json()
    assert "want_to_play_you" not in quiet["search"]["pool"]
    assert "remaining" not in quiet["search"]["pool"]

    bea = await world.a_searcher(client, "bea")
    far = await world.a_signed_in_candidate(
        client, session_factory, "far", mu=searcher["mu"] + 2.0
    )
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client, session_factory, candidate_source, sender=bea, towards=searcher["id"]
    )
    # The far liker's yes has to come off a search of theirs that showed the
    # searcher — and the deck's level gate refuses the pair in both directions,
    # so it is given off *their* radar, which asks no level.
    their_reading = (await read_the_radar(client, far[1])).json()
    said = await world.express_interest(
        client,
        far[1],
        player_id=searcher["id"],
        search_id=their_reading["search"]["search_id"],
    )
    assert said.status_code in (200, 201), said.text

    reading = (await read_the_radar(client, searcher["token"])).json()
    deal = (await world.deck(client, searcher["token"])).json()

    assert reading["search"]["pool"]["want_to_play_you"] == 1
    assert (
        reading["search"]["pool"]["want_to_play_you"]
        == deal["search"]["pool"]["want_to_play_you"]
    )
    drawn = rows_by_id(reading)
    assert drawn[str(far[0])]["inclusion_reason"] == "INTEREST_LIFT"
    assert drawn[str(bea["id"])]["inclusion_reason"] == "INTEREST_LIFT"
    assert str(far[0]) not in rows_by_id(deal)


# ---------------------------------------------------------------------------
# A recorded search, a disclosure, and never a deal
# ---------------------------------------------------------------------------


async def test_a_reading_is_recorded_under_its_own_surface_and_reads_back_whole(
    client, session_factory, candidate_source, searcher
):
    somebody = await world.a_candidate(
        client, session_factory, "somebody", mu=searcher["mu"]
    )
    await world.fold_the_log(session_factory, candidate_source)

    body = (await read_the_radar(client, searcher["token"])).json()
    read = (
        await world.read_back(client, searcher["token"], body["search"]["search_id"])
    ).json()

    assert body["search"]["surface"] == "RADAR"
    assert body["search"]["mode"] is None
    assert body["search"]["rung_offers"] is None
    assert body["search"]["sorts_available"] == []
    assert read["search"]["surface"] == "RADAR"
    live, kept = rows_by_id(body)[str(somebody)], rows_by_id(read)[str(somebody)]
    assert kept["bearing_deg"] == live["bearing_deg"]
    assert kept["ratings"] == live["ratings"]
    assert kept["distance_km"] == live["distance_km"]
    async with session_factory() as session:
        recorded = (
            await session.execute(
                select(SearchORM).where(
                    SearchORM.id == UUID(body["search"]["search_id"])
                )
            )
        ).scalar_one()
    assert recorded.surface == SearchSurface.RADAR.value
    assert recorded.mode is None
    assert recorded.n_excluded_by_suppression is None


async def test_the_record_opens_from_a_card_the_reading_drew(
    client, session_factory, candidate_source, searcher
):
    """ADR-0159 §3's second strand: *a search of the reader's returned them*.
    A reading is one, so the sheet opens from every card it drew — and not
    from a face nothing of the reader's has ever shown."""

    drawn = await world.a_candidate(client, session_factory, "drawn", mu=searcher["mu"])
    never_shown = await world.a_candidate(
        client,
        session_factory,
        "never-shown",
        mu=searcher["mu"],
        latitude=world.CENTRE[0] + 0.5,
    )
    await world.fold_the_log(session_factory, candidate_source)

    await read_the_radar(client, searcher["token"])

    assert (await record_of(client, searcher["token"], drawn)).status_code == 200
    assert (await record_of(client, searcher["token"], never_shown)).status_code == 404


async def test_a_reading_never_enters_the_dealt_memory(
    client, session_factory, candidate_source, searcher
):
    """Ania browses the radar on Monday and does nothing; Tuesday's deck deals
    Filip (``docs/adr/0174`` §4, ADR-0131 bounded). The memory reads ``DECK``
    rows and nothing else."""

    from app.bootstrap.composition import build_search_store
    from app.modules.matchmaking.domain.deck import DEALT_MEMORY

    filip = await world.a_candidate(client, session_factory, "filip", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)

    body = (await read_the_radar(client, searcher["token"])).json()
    assert str(filip) in rows_by_id(body)

    async with session_factory() as session:
        remembered = await build_search_store(session).dealt_since(
            searcher_id=searcher["id"],
            sport=world.SPORT,
            since=datetime.now(timezone.utc) - DEALT_MEMORY,
        )
    assert remembered == frozenset()
    deal = (await world.deck(client, searcher["token"])).json()
    assert str(filip) in rows_by_id(deal)


# ---------------------------------------------------------------------------
# Answers from a reading
# ---------------------------------------------------------------------------


async def test_a_yes_and_a_not_today_name_the_reading_and_write_the_decks_ledgers(
    client, session_factory, candidate_source, searcher
):
    """One answer, two windows (``docs/adr/0174`` §4): the same routes, the
    same ledgers. The passed player leaves the deck and **stays on the radar**."""

    filip = await world.a_candidate(client, session_factory, "filip", mu=searcher["mu"])
    magda = await world.a_candidate(client, session_factory, "magda", mu=searcher["mu"])
    await world.fold_the_log(session_factory, candidate_source)
    reading = (await read_the_radar(client, searcher["token"])).json()
    origin = reading["search"]["search_id"]

    said = await world.express_interest(
        client, searcher["token"], player_id=filip, search_id=origin
    )
    passed = await world.pass_on(
        client, searcher["token"], player_id=magda, search_id=origin
    )

    assert said.status_code == 201, said.text
    assert passed.status_code == 204, passed.text
    outgoing = (await world.read_interest(client, searcher["token"])).json()
    assert [row["player_id"] for row in outgoing["outgoing"]] == [str(filip)]
    # The origin is read off the record and never served back, so it is
    # asserted where it lives: on the two ledgers' rows.
    async with session_factory() as session:
        yeses = (await session.execute(select(InterestORM))).scalars().all()
    assert [(row.to_player_id, row.origin_search_id) for row in yeses] == [
        (filip, UUID(origin))
    ]
    passes = await world.recorded_passes(session_factory)
    assert [(row.passed_id, row.origin_search_id) for row in passes] == [
        (magda, UUID(origin))
    ]
    deal = (await world.deck(client, searcher["token"])).json()
    again = (await read_the_radar(client, searcher["token"])).json()
    assert str(magda) not in rows_by_id(deal)
    assert str(magda) in rows_by_id(again)
    assert str(filip) in rows_by_id(again)


# ---------------------------------------------------------------------------
# The route
# ---------------------------------------------------------------------------


async def test_a_reading_needs_a_token_a_profile_and_a_rating(client):
    assert (await client.post(RADAR_URL, json={"sport": "PADEL"})).status_code == 401
    _, token = await world.register(client, "unplaced")
    unplaced = await read_the_radar(client, token)
    assert unplaced.status_code == 409, unplaced.text
    assert unplaced.json()["code"] == "player_profile_not_committed"
    await world.commit_profile(client, token)
    unrated = await read_the_radar(client, token)
    assert unrated.status_code == 409, unrated.text
    assert unrated.json()["code"] == "sport_not_rated"


async def test_a_reading_is_refused_under_a_hold(client, searcher):
    world.hold_everybody(client)
    response = await read_the_radar(client, searcher["token"])
    assert response.status_code == 403, response.text
    assert response.json()["code"] == "account_held"


async def test_a_reading_takes_no_mode_no_radius_and_no_position(client, searcher):
    """**The sport is the whole ask.** There is no field for a mode, a radius or
    a position to arrive through, so a client that sends one is answered on
    the profile's own reach with no mode — exactly as the deck answers."""

    from app.modules.matchmaking.presentation.schemas import ReadRadarRequest

    assert set(ReadRadarRequest.model_fields) == {"sport"}
    response = await client.post(
        RADAR_URL,
        json={"sport": "PADEL", "mode": "COMPETITIVE", "radius_km": 1, "latitude": 0.0},
        headers=world.auth(searcher["token"]),
    )
    assert response.status_code == 200, response.text
    assert response.json()["search"]["mode"] is None
    assert response.json()["search"]["pool"]["radius_km_used"] == 10
